import os
import json
import re
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env (local dev only; ignored in Docker)
load_dotenv()

app = Flask(__name__)

# Validate and configure Gemini API key at startup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "Set it in your .env file locally or as a Cloud Run secret."
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/shopping-list', methods=['POST'])
def generate_shopping_list():
    data = request.get_json()

    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400

    query = data['query'].strip()
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400

    prompt = f"""
    You are an expert in-store shopping assistant for a supermarket/grocery store.
    The user wants: "{query}"

    Return a JSON object with exactly two keys:
    1. "items": A list of required grocery items to fulfill this request. Each item is an object with:
       - "name": string (the item name)
       - "aisle": string (e.g., "Aisle 4", "Produce", "Dairy", "Bakery")
    2. "cross_sell": One highly relevant complementary item. An object with:
       - "name": string
       - "aisle": string
       - "reason": string (short reason why it pairs well)

    Respond ONLY with valid JSON. Do not include any markdown code fences, backticks, or extra text.
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Robustly strip markdown code fences if Gemini adds them
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\s*```$', '', response_text, flags=re.MULTILINE)
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Basic schema validation
        if 'items' not in result:
            result['items'] = []
        if 'cross_sell' not in result:
            result['cross_sell'] = None

        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}. Raw response: {response_text}")
        return jsonify({'error': 'Failed to parse AI response. Please try again.'}), 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


if __name__ == '__main__':
    # debug=False is essential; use Gunicorn in production (Cloud Run)
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
