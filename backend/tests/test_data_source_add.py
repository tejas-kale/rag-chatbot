"""
Tests for /api/data_source/add endpoint functionality.
"""

import json
import time
from unittest.mock import patch

import pytest

from app.main import create_app


@pytest.fixture
def app():
    """Create test Flask application."""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestDataSourceAddEndpoint:
    """Test cases for the /api/data_source/add endpoint."""

    def test_add_data_source_no_json(self, client):
        """Test endpoint with no JSON data provided."""
        response = client.post("/api/data_source/add")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        # Accept either error message depending on how Flask handles the request
        assert (
            "No JSON data provided" in data["error"]
            or "Invalid JSON format" in data["error"]
        )

    def test_add_data_source_missing_fields(self, client):
        """Test endpoint with missing required fields."""
        # Missing both type and value
        response = client.post(
            "/api/data_source/add", data=json.dumps({}), content_type="application/json"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing 'type' or 'value' field" in data["error"]

        # Missing value field
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing 'type' or 'value' field" in data["error"]

        # Missing type field
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"value": "http://example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing 'type' or 'value' field" in data["error"]

    def test_add_data_source_invalid_type(self, client):
        """Test endpoint with invalid source type."""
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "invalid", "value": "some value"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Invalid source type" in data["error"]
        # Check that both allowed types are mentioned (order doesn't matter)
        assert "url" in data["error"]
        assert "markdown" in data["error"]

    def test_add_data_source_empty_value(self, client):
        """Test endpoint with empty or invalid values."""
        # Empty string
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Source value must be a non-empty string" in data["error"]

        # Whitespace only
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Source value must be a non-empty string" in data["error"]

        # Non-string value
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": 123}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Source value must be a non-empty string" in data["error"]

    def test_add_data_source_invalid_url(self, client):
        """Test endpoint with invalid URL format."""
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": "not-a-valid-url"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "URL must start with http:// or https://" in data["error"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_add_data_source_valid_url(self, mock_process_source, client):
        """Test endpoint with valid URL."""
        mock_process_source.return_value = True

        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": "https://example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 202
        data = json.loads(response.data)

        # Check response structure
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert "source_type" in data

        # Check response values
        assert data["status"] == "processing"
        assert data["source_type"] == "url"
        assert "processing started" in data["message"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_add_data_source_valid_markdown(self, mock_process_source, client):
        """Test endpoint with valid markdown content."""
        mock_process_source.return_value = True

        markdown_content = "# Test Markdown\n\nThis is a test."
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "markdown", "value": markdown_content}),
            content_type="application/json",
        )
        assert response.status_code == 202
        data = json.loads(response.data)

        # Check response structure
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert "source_type" in data

        # Check response values
        assert data["status"] == "processing"
        assert data["source_type"] == "markdown"
        assert "processing started" in data["message"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_add_data_source_youtube_url_detection(self, mock_process_source, client):
        """Test that YouTube URLs are properly detected."""
        mock_process_source.return_value = True

        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.post(
            "/api/data_source/add",
            data=json.dumps({"type": "url", "value": youtube_url}),
            content_type="application/json",
        )
        assert response.status_code == 202

        # Give a moment for the async processing to start
        time.sleep(0.1)

        # Verify that process_source was called with 'youtube' type
        mock_process_source.assert_called_once()
        args, kwargs = mock_process_source.call_args
        assert args[0] == youtube_url  # source_value
        assert args[1] == "youtube"  # processing_type (should be detected as youtube)

    def test_add_data_source_error_handling(self, client):
        """Test error handling in the endpoint."""
        # Test with malformed JSON
        response = client.post(
            "/api/data_source/add",
            data="malformed json",
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Invalid JSON format" in data["error"]

    def test_get_data_source_status_endpoint(self, client):
        """Test the status endpoint for data source tasks."""
        # Test with non-existent task ID
        response = client.get("/api/data_source/status/non-existent-task")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "Task not found" in data["error"]
