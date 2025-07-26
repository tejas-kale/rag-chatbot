"""
Tests for PDF upload endpoint functionality.
"""

import io
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


@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    # Create a simple PDF-like content for testing
    pdf_content = (
        b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
        b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n"
        b">>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n"
        b"/Root 1 0 R\n>>\nstartxref\n198\n%%EOF"
    )
    return pdf_content


class TestUploadEndpoint:
    """Test cases for the PDF upload endpoint."""

    def test_upload_endpoint_no_file(self, client):
        """Test upload endpoint with no file provided."""
        response = client.post("/api/data_source/upload")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"] == "No file provided"

    def test_upload_endpoint_empty_filename(self, client):
        """Test upload endpoint with empty filename."""
        data = {"file": (io.BytesIO(b"test"), "")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"] == "No file selected"

    def test_upload_endpoint_invalid_file_type(self, client):
        """Test upload endpoint with non-PDF file."""
        data = {"file": (io.BytesIO(b"test content"), "test.txt")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid file type" in data["error"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_upload_endpoint_success(self, mock_process, client, sample_pdf):
        """Test successful PDF upload."""
        mock_process.return_value = True

        data = {"file": (io.BytesIO(sample_pdf), "test.pdf")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        assert "task_id" in response_data
        assert response_data["status"] == "processing"
        assert response_data["filename"] == "test.pdf"
        assert "processing started" in response_data["message"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_upload_endpoint_processing_success(self, mock_process, client, sample_pdf):
        """Test upload endpoint with successful processing."""
        mock_process.return_value = True

        data = {"file": (io.BytesIO(sample_pdf), "test.pdf")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        task_id = response_data["task_id"]

        # Wait a bit for background processing
        time.sleep(0.1)

        # Check task status
        status_response = client.get(f"/api/data_source/upload/status/{task_id}")
        assert status_response.status_code == 200
        status_data = json.loads(status_response.data)
        assert status_data["task_id"] == task_id
        # Status might be "processing" or "completed" depending on timing
        assert status_data["status"] in ["processing", "completed"]

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_upload_endpoint_processing_failure(self, mock_process, client, sample_pdf):
        """Test upload endpoint with processing failure."""
        mock_process.return_value = False

        data = {"file": (io.BytesIO(sample_pdf), "test.pdf")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        task_id = response_data["task_id"]

        # Wait for background processing to complete
        time.sleep(0.2)

        # Check task status
        status_response = client.get(f"/api/data_source/upload/status/{task_id}")
        assert status_response.status_code == 200
        status_data = json.loads(status_response.data)
        assert status_data["task_id"] == task_id
        # Should be failed since mock returns False
        assert status_data["status"] in ["processing", "failed"]

    def test_upload_status_endpoint_not_found(self, client):
        """Test status endpoint with non-existent task ID."""
        response = client.get("/api/data_source/upload/status/nonexistent")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["error"] == "Task not found"

    def test_is_allowed_file_function(self):
        """Test the file extension validation function."""
        from app.api.routes import _is_allowed_file

        assert _is_allowed_file("test.pdf") is True
        assert _is_allowed_file("TEST.PDF") is True
        assert _is_allowed_file("document.txt") is False
        assert _is_allowed_file("image.jpg") is False
        assert _is_allowed_file("noextension") is False
        assert _is_allowed_file("") is False

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_upload_with_special_characters_filename(
        self, mock_process, client, sample_pdf
    ):
        """Test upload with filename containing special characters."""
        mock_process.return_value = True

        # Filename with special characters
        filename = "test file with spaces & symbols!.pdf"
        data = {"file": (io.BytesIO(sample_pdf), filename)}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        # Should have a sanitized filename
        assert "task_id" in response_data
        assert response_data["status"] == "processing"

    @patch("app.api.routes.data_ingestion_service.process_source")
    @patch("app.api.routes.secure_filename")
    def test_upload_with_malicious_filename(
        self, mock_secure, mock_process, client, sample_pdf
    ):
        """Test upload with potentially malicious filename."""
        mock_process.return_value = True
        mock_secure.return_value = ""  # Simulate secure_filename returning empty

        filename = (
            "../../../etc/passwd.pdf"  # Need .pdf extension to pass file type check
        )
        data = {"file": (io.BytesIO(sample_pdf), filename)}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        # Should generate a safe filename when secure_filename returns empty
        assert response_data["filename"].startswith("upload_")
        assert response_data["filename"].endswith(".pdf")

    @patch("app.api.routes.data_ingestion_service.process_source")
    def test_upload_large_file_simulation(self, mock_process, client):
        """Test upload with larger file content."""
        mock_process.return_value = True

        # Create larger content to simulate a real PDF
        large_content = b"Large PDF content " * 1000
        data = {"file": (io.BytesIO(large_content), "large_test.pdf")}
        response = client.post(
            "/api/data_source/upload", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 202
        response_data = json.loads(response.data)
        assert "task_id" in response_data
        assert response_data["status"] == "processing"
        assert response_data["filename"] == "large_test.pdf"
