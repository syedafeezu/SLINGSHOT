import os
import json
import re
import logging
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv
from cachetools import TTLCache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from google_services import get_gemini_api_key, save_query, get_history

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()  # No-op in Docker (no .env present); works locally

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32))

# ---------------------------------------------------------------------------
# Rate Limiting — Security layer (10 req/min per IP on AI endpoint)
# ---------------------------------------------------------------------------

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

# ---------------------------------------------------------------------------
# Security Headers
# ---------------------------------------------------------------------------

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ---------------------------------------------------------------------------
# Gemini Setup — via Google Secret Manager (prod) or env var (local)
# ---------------------------------------------------------------------------

GEMINI_API_KEY = get_gemini_api_key()
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Provide it via Secret Manager or a .env file."
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------------------------------------------------------------------
# In-memory query cache — 5-minute TTL, max 128 entries
# ---------------------------------------------------------------------------

_query_cache: TTLCache = TTLCache(maxsize=128, ttl=300)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Health check endpoint for Cloud Run and uptime monitoring."""
    return jsonify({"status": "ok", "model": "gemini-2.5-flash"}), 200


@app.route("/api/history", methods=["GET"])
def shopping_history():
    """Return the user's recent query history (from Firestore or memory)."""
    session_id = request.args.get("session_id", "global")
    return jsonify({"history": get_history(session_id)}), 200


@app.route("/api/shopping-list", methods=["POST"])
@limiter.limit("10 per minute")
def generate_shopping_list():
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Missing query parameter"}), 400

    query = data["query"].strip()[:500]  # Sanitize: cap at 500 chars
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    session_id = data.get("session_id", "global")

    # ---- Cache check -------------------------------------------------------
    cache_key = query.lower()
    if cache_key in _query_cache:
        logger.info("CACHE HIT for query: %s", query[:60])
        cached = _query_cache[cache_key]
        # Still persist history even for cached results
        save_query(query, session_id)
        return jsonify(cached), 200

    # ---- Gemini API call ---------------------------------------------------
    prompt = (
        f'You are an expert in-store shopping assistant for a supermarket/grocery store.\n'
        f'The user wants: "{query}"\n\n'
        'Return a JSON object with exactly two keys:\n'
        '1. "items": A list of required grocery items. Each item is an object with:\n'
        '   - "name": string\n'
        '   - "aisle": string (e.g., "Aisle 4", "Produce", "Dairy", "Bakery")\n'
        '2. "cross_sell": One complementary item with:\n'
        '   - "name": string\n'
        '   - "aisle": string\n'
        '   - "reason": string (brief reason for the pairing)\n\n'
        'Respond ONLY with valid JSON. No markdown code fences, no extra text.'
    )

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Robustly strip markdown code fences
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text, flags=re.MULTILINE)
        response_text = re.sub(r"\s*```$", "", response_text, flags=re.MULTILINE)
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Schema normalisation
        if "items" not in result or not isinstance(result["items"], list):
            result["items"] = []
        if "cross_sell" not in result:
            result["cross_sell"] = None

        # Cache and persist
        _query_cache[cache_key] = result
        save_query(query, session_id)

        return jsonify(result), 200

    except json.JSONDecodeError as exc:
        logger.error("JSON parse error: %s | raw: %s", exc, response_text[:200])
        return jsonify({"error": "Failed to parse AI response. Please try again."}), 500
    except Exception as exc:
        logger.error("Gemini error: %s", exc)
        return jsonify({"error": "An error occurred while processing your request."}), 500


# ---------------------------------------------------------------------------
# Entry point (local dev only — use Gunicorn in prod)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
