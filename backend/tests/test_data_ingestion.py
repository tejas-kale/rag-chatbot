"""
Tests for the data ingestion service and API endpoint using pytest.
"""

import json
import tempfile
import os
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
    assert response.json["error"] == (
        "Unsupported data source type: invalid_type"
    )


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


def _create_test_pdf(content="Test PDF content for ingestion testing."):
    """Create a temporary PDF file for testing."""
    # Create a minimal valid PDF
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(content) + 20}
>>
stream
BT
/F1 12 Tf
100 700 Td
({content}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_file.write(pdf_content.encode())
    temp_file.close()
    return temp_file.name


def test_ingest_pdf_success(client, mock_data_ingestion_service):
    """Test successful PDF ingestion via the API."""
    mock_data_ingestion_service.process_source.return_value = True

    # Create a temporary test PDF
    pdf_path = _create_test_pdf(
        "Test PDF document for RAG chatbot processing."
    )

    try:
        payload = {
            "source_type": "pdf",
            "data": pdf_path,
            "metadata": {"source": "test_pdf"},
        }
        response = client.post(
            "/api/ingest",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json["message"] == "Data ingested successfully"
        mock_data_ingestion_service.process_source.assert_called_once_with(
            pdf_path, "pdf", {"source": "test_pdf"}
        )
    finally:
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_ingest_pdf_failure(client, mock_data_ingestion_service):
    """Test failed PDF ingestion via the API."""
    mock_data_ingestion_service.process_source.return_value = False

    # Use a non-existent PDF path for testing failure
    pdf_path = "/nonexistent/test.pdf"

    payload = {
        "source_type": "pdf",
        "data": pdf_path,
    }
    response = client.post(
        "/api/ingest",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 500
    assert response.json["error"] == "Failed to ingest data"
