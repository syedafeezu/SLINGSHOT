"""
conftest.py — Shared pytest fixtures for RetailVibe test suite.
All Google Cloud and Gemini calls are mocked — tests run fully offline.
"""

import json
import sys
import os
import unittest.mock as mock
import pytest


# ---------------------------------------------------------------------------
# Pre-patch environment before any app imports
# ---------------------------------------------------------------------------
os.environ.setdefault("GEMINI_API_KEY", "test-fake-key-12345")


@pytest.fixture(scope="session")
def app():
    """
    Create the Flask app for testing.
    Patches Gemini and Google Cloud at the google_services module level
    so no real HTTP calls are made.
    """
    fake_response_json = json.dumps({
        "items": [
            {"name": "Spaghetti",     "aisle": "Aisle 3"},
            {"name": "Tomato Sauce",  "aisle": "Aisle 5"},
            {"name": "Ground Beef",   "aisle": "Meat"},
        ],
        "cross_sell": {
            "name": "Parmesan Cheese",
            "aisle": "Dairy",
            "reason": "Perfect topping for pasta dishes.",
        },
    })

    mock_response = mock.Mock()
    mock_response.text = fake_response_json

    mock_model = mock.Mock()
    mock_model.generate_content.return_value = mock_response

    # Patch google_services helpers so Secret Manager / Firestore never hit
    with mock.patch("google_services.get_secret", return_value=None), \
         mock.patch("google_services._get_firestore_client", return_value=None), \
         mock.patch("google_services.save_query", return_value=None), \
         mock.patch("google_services.get_history", return_value=[]):

        # Patch genai at the module attribute level — avoids importing the
        # full google.generativeai package inside mock.patch()
        import google_services  # noqa: ensure module is loaded first

        import importlib
        import app as flask_app_module

        # Replace the model object the app already constructed
        flask_app_module.model = mock_model

        flask_app_module.app.config["TESTING"] = True
        flask_app_module.limiter.enabled = False

        yield flask_app_module.app


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()
