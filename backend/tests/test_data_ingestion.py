"""
Tests for the data ingestion service and API endpoint using pytest.
"""

import json
from unittest.mock import MagicMock

import pytest
from app.main import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app("testing")
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_data_ingestion_service(monkeypatch):
    """Mock the DataIngestionService."""
    mock_service = MagicMock()
    monkeypatch.setattr("app.api.routes.data_ingestion_service", mock_service)
    return mock_service


def test_ingest_data_success(client, mock_data_ingestion_service):
    """Test successful data ingestion via the API."""
    mock_data_ingestion_service.process_source.return_value = True
    payload = {
        "source_type": "text",
        "data": "This is a test document.",
        "metadata": {"source": "test"},
    }
    response = client.post(
        "/api/ingest",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json["message"] == "Data ingested successfully"
    mock_data_ingestion_service.process_source.assert_called_once_with(
        "This is a test document.", "text", {"source": "test"}
    )


def test_ingest_data_failure(client, mock_data_ingestion_service):
    """Test failed data ingestion via the API."""
    mock_data_ingestion_service.process_source.return_value = False
    payload = {
        "source_type": "text",
        "data": "This is another test document.",
    }
    response = client.post(
        "/api/ingest",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 500
    assert response.json["error"] == "Failed to ingest data"


def test_ingest_data_unsupported_type(client, mock_data_ingestion_service):
    """Test data ingestion with an unsupported source type."""
    mock_data_ingestion_service.process_source.side_effect = ValueError(
        "Unsupported data source type: invalid_type"
    )
    payload = {
        "source_type": "invalid_type",
        "data": "This is a test document.",
    }
    response = client.post(
        "/api/ingest",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Unsupported data source type: invalid_type"


def test_ingest_data_bad_request(client):
    """Test the /api/ingest endpoint with a bad request."""
    payload = {"data": "This is a test document."}  # Missing source_type
    response = client.post(
        "/api/ingest",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json["error"] == "Missing source_type or data in request"
