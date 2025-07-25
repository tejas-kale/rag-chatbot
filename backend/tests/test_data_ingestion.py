"""
Tests for the data ingestion service and API endpoint.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from app.main import create_app


class DataIngestionTestCase(unittest.TestCase):
    """Test case for data ingestion functionalities."""

    def setUp(self):
        """Set up the test environment."""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        # Mock the services that are used by the API
        self.mock_chromadb_service = MagicMock()
        self.mock_embedding_factory = MagicMock()
        self.mock_data_ingestion_service = MagicMock()

        self.service_patch = patch.dict(
            "app.api.routes.__dict__",
            {
                "chromadb_service": self.mock_chromadb_service,
                "embedding_factory": self.mock_embedding_factory,
                "data_ingestion_service": self.mock_data_ingestion_service,
            },
        )
        self.service_patch.start()

    def tearDown(self):
        """Tear down the test environment."""
        self.service_patch.stop()

    def test_ingest_data_success(self):
        """Test successful data ingestion via the API."""
        # Configure the mock to return True for successful processing
        self.mock_data_ingestion_service.process_source.return_value = True

        # Prepare the request payload
        payload = {
            "source_type": "text",
            "data": "This is a test document.",
            "metadata": {"source": "test"},
        }

        # Send a POST request to the /api/ingest endpoint
        response = self.client.post(
            "/api/ingest", data=json.dumps(payload), content_type="application/json"
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "Data ingested successfully")

        # Verify that the process_source method was called with the correct arguments
        self.mock_data_ingestion_service.process_source.assert_called_once_with(
            "This is a test document.", "text", {"source": "test"}
        )

    def test_ingest_data_failure(self):
        """Test failed data ingestion via the API."""
        # Configure the mock to return False for failed processing
        self.mock_data_ingestion_service.process_source.return_value = False

        # Prepare the request payload
        payload = {
            "source_type": "text",
            "data": "This is another test document.",
        }

        # Send a POST request to the /api/ingest endpoint
        response = self.client.post(
            "/api/ingest", data=json.dumps(payload), content_type="application/json"
        )

        # Check the response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json["error"], "Failed to ingest data")

    def test_ingest_data_unsupported_type(self):
        """Test data ingestion with an unsupported source type."""
        # Configure the mock to raise a ValueError
        self.mock_data_ingestion_service.process_source.side_effect = ValueError(
            "Unsupported data source type: invalid_type"
        )

        # Prepare the request payload
        payload = {
            "source_type": "invalid_type",
            "data": "This is a test document.",
        }

        # Send a POST request to the /api/ingest endpoint
        response = self.client.post(
            "/api/ingest", data=json.dumps(payload), content_type="application/json"
        )

        # Check the response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"], "Unsupported data source type: invalid_type"
        )


if __name__ == "__main__":
    unittest.main()
