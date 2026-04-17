"""
google_services.py — Centralized Google Cloud service integrations for RetailVibe.

Services:
  - Google Cloud Secret Manager : secure API key retrieval in production
  - Google Cloud Firestore       : persistent shopping history per session
"""

import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Cloud Secret Manager
# ---------------------------------------------------------------------------

def get_secret(secret_id: str, project_id: str | None = None) -> str | None:
    """
    Fetch a secret value from Google Cloud Secret Manager.
    Returns None (with a warning) if the client is unavailable or the secret
    is not found — callers should fall back to environment variables.
    """
    try:
        from google.cloud import secretmanager  # noqa: PLC0415
        project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT not set; skipping Secret Manager.")
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8").strip()
    except ImportError:
        logger.warning("google-cloud-secret-manager not installed; skipping.")
        return None
    except Exception as exc:
        logger.warning("Secret Manager unavailable (%s); falling back to env var.", exc)
        return None


def get_gemini_api_key() -> str:
    """
    Return the Gemini API key, preferring Secret Manager in production.
    Falls back gracefully to the GEMINI_API_KEY environment variable.
    """
    # Try Secret Manager first (Cloud Run / production)
    secret_value = get_secret("GEMINI_API_KEY")
    if secret_value:
        logger.info("Gemini API key loaded from Secret Manager.")
        return secret_value

    # Local development fallback
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        logger.info("Gemini API key loaded from environment variable.")
    return key


# ---------------------------------------------------------------------------
# Google Cloud Firestore — Shopping History
# ---------------------------------------------------------------------------

_firestore_client = None
_firestore_available = False


def _get_firestore_client():
    """Lazy-initialise the Firestore client; returns None if unavailable."""
    global _firestore_client, _firestore_available
    if _firestore_client is not None:
        return _firestore_client
    if _firestore_available is False and _firestore_client is None:
        # Already tried and failed — avoid repeated init
        pass

    try:
        from google.cloud import firestore  # noqa: PLC0415
        _firestore_client = firestore.Client()
        _firestore_available = True
        logger.info("Firestore client initialised successfully.")
    except ImportError:
        logger.warning("google-cloud-firestore not installed; history disabled.")
        _firestore_available = False
    except Exception as exc:
        logger.warning("Firestore unavailable (%s); using in-memory fallback.", exc)
        _firestore_available = False

    return _firestore_client


# In-memory fallback store when Firestore is not available
_memory_history: list[str] = []
_HISTORY_LIMIT = 10


def save_query(query: str, session_id: str = "global") -> None:
    """Persist a successfully resolved query to Firestore (or memory)."""
    query = query.strip()
    if not query:
        return

    client = _get_firestore_client()
    if client:
        try:
            from google.cloud import firestore as _fs  # noqa: PLC0415
            doc_ref = client.collection("shopping_history").document(session_id)
            doc = doc_ref.get()
            history: list[str] = doc.to_dict().get("queries", []) if doc.exists else []
            # Deduplicate and keep latest at front
            if query in history:
                history.remove(query)
            history.insert(0, query)
            history = history[:_HISTORY_LIMIT]
            doc_ref.set({"queries": history}, merge=True)
        except Exception as exc:
            logger.warning("Failed to save query to Firestore: %s", exc)
    else:
        # Memory fallback
        if query in _memory_history:
            _memory_history.remove(query)
        _memory_history.insert(0, query)
        del _memory_history[_HISTORY_LIMIT:]


def get_history(session_id: str = "global") -> list[str]:
    """Return up to 10 recent unique queries for the given session."""
    client = _get_firestore_client()
    if client:
        try:
            doc_ref = client.collection("shopping_history").document(session_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("queries", [])[:_HISTORY_LIMIT]
        except Exception as exc:
            logger.warning("Failed to fetch history from Firestore: %s", exc)
    return list(_memory_history[:_HISTORY_LIMIT])
