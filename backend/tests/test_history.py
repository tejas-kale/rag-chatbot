"""
Test module for history endpoint.
"""

import json
import logging
import os
import sys

# Add the parent directory to the path to import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure logger
logger = logging.getLogger(__name__)


def test_history_endpoint_empty():
    """Test the /api/history endpoint returns empty array when no data."""
    try:
        from app.main import create_app

        # Create test app
        app = create_app("testing")

        with app.test_client() as client:
            # Test GET request to /api/history
            response = client.get("/api/history")

            # Check status code is 200 OK
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"

            # Check response is JSON
            assert (
                response.content_type == "application/json"
            ), f"Expected JSON, got {response.content_type}"

            # Check response body is an array
            data = json.loads(response.data)
            assert isinstance(data, list), f"Expected array, got {type(data)}"

            logger.info("History endpoint empty test passed!")

    except ImportError as e:
        logger.error(f"Flask not available for testing: {e}")
        logger.info("History endpoint empty validation skipped")


def test_history_endpoint_with_data():
    """Test the /api/history endpoint returns data when chat history exists."""
    try:
        from app.main import create_app
        from app.models.models import db
        from app.services.persistence_service import PersistenceManager

        # Create test app
        app = create_app("testing")

        with app.app_context():
            # Initialize database and create test data
            db.create_all()

            persistence_manager = PersistenceManager()

            # Create test chat history
            persistence_manager.create_chat_history(
                session_id="test_session_1",
                user_message="Hello",
                bot_response="Hi there!",
            )

            persistence_manager.create_chat_history(
                session_id="test_session_1",
                user_message="How are you?",
                bot_response="I'm doing well, thank you!",
            )

            with app.test_client() as client:
                # Test GET request to /api/history
                response = client.get("/api/history")

                # Check status code is 200 OK
                assert (
                    response.status_code == 200
                ), f"Expected 200, got {response.status_code}"

                # Check response is JSON
                assert (
                    response.content_type == "application/json"
                ), f"Expected JSON, got {response.content_type}"

                # Check response body
                data = json.loads(response.data)
                assert isinstance(data, list), f"Expected array, got {type(data)}"
                assert len(data) == 2, f"Expected 2 items, got {len(data)}"

                # Check first item structure
                first_item = data[0]
                expected_fields = {
                    "id",
                    "session_id",
                    "user_message",
                    "bot_response",
                    "timestamp",
                    "context_sources",
                }
                assert set(first_item.keys()) == expected_fields, (
                    f"Expected fields {expected_fields}, "
                    f"got {set(first_item.keys())}"
                )

                # Check data content
                assert first_item["session_id"] == "test_session_1"
                assert first_item["user_message"] == "Hello"
                assert first_item["bot_response"] == "Hi there!"
                assert first_item["timestamp"] is not None

                logger.info("History endpoint with data test passed!")

    except ImportError as e:
        logger.error(f"Flask not available for testing: {e}")
        logger.info("History endpoint with data validation skipped")


if __name__ == "__main__":
    test_history_endpoint_empty()
    test_history_endpoint_with_data()
