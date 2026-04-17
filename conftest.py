"""
conftest.py — Shared pytest fixtures for RetailVibe test suite.
Gemini and Google Cloud services are mocked so tests run fully offline.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Patch heavy Google services BEFORE the app module is imported
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def mock_google_services(session_mocker=None):
    """
    Ensure tests never hit real Google Cloud APIs.
    We patch at the module level so the app initialises cleanly.
    """
    import unittest.mock as mock

    # ---- Patch Secret Manager so get_gemini_api_key() returns a fake key --
    with mock.patch(
        "google_services.get_secret", return_value=None
    ):
        # ---- Provide a dummy key via env so the RuntimeError isn't raised --
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "test-fake-key-12345"}):
            yield


@pytest.fixture(scope="session")
def app(mock_google_services):
    """Create the Flask application configured for testing."""
    import unittest.mock as mock

    # Patch Gemini *before* importing app so genai.configure() uses the fake key
    with mock.patch("google.generativeai.configure"):
        with mock.patch("google.generativeai.GenerativeModel") as MockModel:
            # Default mock response: valid JSON shopping list
            mock_instance = MockModel.return_value
            mock_instance.generate_content.return_value = mock.Mock(
                text=json.dumps({
                    "items": [
                        {"name": "Spaghetti", "aisle": "Aisle 3"},
                        {"name": "Tomato Sauce", "aisle": "Aisle 5"},
                        {"name": "Ground Beef", "aisle": "Meat"},
                    ],
                    "cross_sell": {
                        "name": "Parmesan Cheese",
                        "aisle": "Dairy",
                        "reason": "Perfect topping for pasta dishes.",
                    },
                })
            )

            import app as flask_app
            flask_app.app.config["TESTING"] = True
            flask_app.app.config["WTF_CSRF_ENABLED"] = False
            # Disable rate limiting in tests
            flask_app.limiter.enabled = False
            yield flask_app.app


@pytest.fixture()
def client(app):
    """A test client for the Flask app."""
    return app.test_client()
