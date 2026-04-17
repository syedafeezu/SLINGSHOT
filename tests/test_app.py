"""
tests/test_app.py — Comprehensive test suite for RetailVibe Flask API.

Covers:
  - Homepage renders correctly
  - Health endpoint
  - Valid shopping-list query → correct JSON structure
  - Missing / empty query → 400 errors
  - Markdown fence cleanup regex
  - History endpoint
  - Security headers present
  - Response contains required keys
"""

import json
import re
import pytest
import unittest.mock as mock


# ===========================================================================
# 1. Homepage
# ===========================================================================

class TestHomepage:
    def test_homepage_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_homepage_content_type_is_html(self, client):
        response = client.get("/")
        assert "text/html" in response.content_type

    def test_homepage_contains_brand_name(self, client):
        response = client.get("/")
        assert b"RetailVibe" in response.data


# ===========================================================================
# 2. Health Check
# ===========================================================================

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        response = client.get("/api/health")
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_returns_model_name(self, client):
        response = client.get("/api/health")
        data = response.get_json()
        assert "model" in data
        assert "gemini" in data["model"]


# ===========================================================================
# 3. Shopping List — Valid Requests
# ===========================================================================

class TestShoppingListValid:
    def _post(self, client, query, session_id="test-session"):
        return client.post(
            "/api/shopping-list",
            data=json.dumps({"query": query, "session_id": session_id}),
            content_type="application/json",
        )

    def test_valid_query_returns_200(self, client):
        response = self._post(client, "i wanna make pasta")
        assert response.status_code == 200

    def test_response_has_items_key(self, client):
        response = self._post(client, "make a salad")
        data = response.get_json()
        assert "items" in data

    def test_response_items_is_list(self, client):
        response = self._post(client, "make a salad")
        data = response.get_json()
        assert isinstance(data["items"], list)

    def test_each_item_has_name_and_aisle(self, client):
        response = self._post(client, "make pasta")
        data = response.get_json()
        for item in data["items"]:
            assert "name" in item, f"Missing 'name' in item: {item}"
            assert "aisle" in item, f"Missing 'aisle' in item: {item}"

    def test_response_has_cross_sell_key(self, client):
        response = self._post(client, "make pasta")
        data = response.get_json()
        assert "cross_sell" in data

    def test_cross_sell_has_required_fields(self, client):
        response = self._post(client, "make pasta")
        cs = response.get_json()["cross_sell"]
        assert cs is not None
        for field in ("name", "aisle", "reason"):
            assert field in cs, f"cross_sell missing field: {field}"

    def test_query_is_trimmed(self, client):
        """Whitespace-padded query should still succeed."""
        response = self._post(client, "   make pasta   ")
        assert response.status_code == 200

    def test_long_query_is_truncated_not_errored(self, client):
        """Queries longer than 500 chars should be truncated, not raise 500."""
        long_query = "make pasta " * 60  # >500 chars
        response = self._post(client, long_query)
        assert response.status_code == 200


# ===========================================================================
# 4. Shopping List — Invalid Requests
# ===========================================================================

class TestShoppingListInvalid:
    def test_missing_query_key_returns_400(self, client):
        response = client.post(
            "/api/shopping-list",
            data=json.dumps({"wrong_key": "value"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_query_returns_400(self, client):
        response = client.post(
            "/api/shopping-list",
            data=json.dumps({"query": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_no_body_returns_400(self, client):
        response = client.post(
            "/api/shopping-list",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_error_response_has_error_key(self, client):
        response = client.post(
            "/api/shopping-list",
            data=json.dumps({}),
            content_type="application/json",
        )
        data = response.get_json()
        assert "error" in data


# ===========================================================================
# 5. JSON Cleanup Utility (unit test — no HTTP)
# ===========================================================================

class TestJsonCleanup:
    """Tests the markdown-fence stripping logic used in app.py."""

    def _strip(self, text: str) -> str:
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        return text.strip()

    def test_strips_json_code_fence(self):
        raw = "```json\n{\"key\": \"value\"}\n```"
        assert self._strip(raw) == '{"key": "value"}'

    def test_strips_plain_code_fence(self):
        raw = "```\n{\"key\": \"value\"}\n```"
        assert self._strip(raw) == '{"key": "value"}'

    def test_no_fence_unchanged(self):
        raw = '{"key": "value"}'
        assert self._strip(raw) == raw

    def test_result_is_valid_json(self):
        raw = '```json\n{"items": [], "cross_sell": null}\n```'
        result = json.loads(self._strip(raw))
        assert result["items"] == []


# ===========================================================================
# 6. History Endpoint
# ===========================================================================

class TestHistoryEndpoint:
    def test_history_returns_200(self, client):
        response = client.get("/api/history")
        assert response.status_code == 200

    def test_history_returns_list(self, client):
        response = client.get("/api/history")
        data = response.get_json()
        assert "history" in data
        assert isinstance(data["history"], list)


# ===========================================================================
# 7. Security Headers
# ===========================================================================

class TestSecurityHeaders:
    def test_x_content_type_options_header(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_header(self, client):
        response = client.get("/")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy_header(self, client):
        response = client.get("/")
        assert "Referrer-Policy" in response.headers
