"""
Test for the backend directory structure organization.
Validates that the new app/api/ structure works correctly.
"""

import pytest
from app.main import create_app


class TestBackendStructure:
    """Test the backend directory structure."""

    @pytest.fixture
    def app(self):
        """Create and configure a test application."""
        app = create_app("testing")
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the Flask application."""
        return app.test_client()

    def test_api_blueprint_registration(self, app):
        """Test that the API blueprint is properly registered."""
        # Check that the app has the expected blueprints
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert "api" in blueprint_names, "API blueprint should be registered"

    def test_api_routes_accessible(self, client):
        """Test that routes moved to app/api/ are still accessible."""
        # Test health check endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert b"RAG Chatbot API is running" in response.data

        # Test API health endpoint
        response = client.get("/api/health")
        assert response.status_code == 200
        assert b"ok" in response.data

        # Test settings endpoint
        response = client.get("/api/settings")
        assert response.status_code == 200

        # Test history endpoint
        response = client.get("/api/history")
        assert response.status_code == 200

    def test_api_module_structure(self):
        """Test that the API module can be imported correctly."""
        # Test that we can import the API routes
        from app.api.routes import api_bp

        assert api_bp is not None
        assert api_bp.name == "api"

        # Test that we can import the helper function as well
        from app.api.routes import _sanitize_settings_response

        assert _sanitize_settings_response is not None
