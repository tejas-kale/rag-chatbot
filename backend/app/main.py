"""
Main Flask application for the RAG chatbot.
"""

import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from app.config.config import config
from app.models.models import init_db
from app.services.persistence_service import PersistenceManager


def create_app(config_name=None):
    """
    Create and configure the Flask application.

    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Determine configuration
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config[config_name])

    # Configure CORS
    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Initialize database
    init_db(app)

    # Initialize persistence manager
    persistence_manager = PersistenceManager()

    def _sanitize_settings_response(user_settings):
        """
        Sanitize user settings for API response by removing sensitive data.

        Args:
            user_settings: UserSettings object

        Returns:
            dict: Sanitized settings dictionary
        """
        if not user_settings:
            return {
                "user_id": "default_user",
                "api_keys": {},
                "custom_prompts": None,
                "created_at": None,
                "updated_at": None,
            }

        # Get API keys to check what keys exist (but don't expose values)
        api_keys_data = persistence_manager.get_api_keys(user_settings.user_id)
        api_keys_status = {}

        if api_keys_data:
            # Only indicate which API keys are configured, not their values
            for key in api_keys_data.keys():
                api_keys_status[key] = "configured"

        return {
            "user_id": user_settings.user_id,
            "api_keys": api_keys_status,
            "custom_prompts": user_settings.custom_prompts,
            "created_at": (
                user_settings.created_at.isoformat()
                if user_settings.created_at
                else None
            ),
            "updated_at": (
                user_settings.updated_at.isoformat()
                if user_settings.updated_at
                else None
            ),
        }

    # Register routes
    @app.route("/")
    def health_check():
        """Basic health check endpoint."""
        return jsonify(
            {
                "message": "RAG Chatbot API is running",
                "status": "healthy",
                "version": "1.0.0",
            }
        )

    @app.route("/api/health")
    def api_health():
        """API health check endpoint."""
        return jsonify({"status": "ok"})

    @app.route("/api/chat", methods=["POST"])
    def chat():
        """Chat endpoint for processing user messages."""
        try:
            # Get JSON data from request
            data = request.get_json()

            # Validate that message field exists
            if not data or "message" not in data:
                return jsonify({"error": "Message field is required"}), 400

            # For now, return a placeholder response
            return jsonify({"response": "I am a bot."})

        except Exception as e:
            return jsonify({"error": f"Invalid request: {e}"}), 400

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        """Get current user settings."""
        try:
            # For now, use default_user as user_id
            user_id = "default_user"

            # Get user settings from database
            user_settings = persistence_manager.get_user_settings_by_user_id(user_id)

            # Sanitize response to remove sensitive data
            settings_data = _sanitize_settings_response(user_settings)

            return jsonify(settings_data)

        except Exception as e:
            return jsonify({"error": f"Failed to retrieve settings: {str(e)}"}), 500

    @app.route("/api/settings", methods=["POST"])
    def update_settings():
        """Update user settings."""
        try:
            # Get JSON data from request
            data = request.get_json()

            if not data:
                return jsonify({"error": "Request body is required"}), 400

            # For now, use default_user as user_id
            user_id = "default_user"

            # Get existing user settings or create new ones
            user_settings = persistence_manager.get_user_settings_by_user_id(user_id)

            # Extract API keys and custom prompts from request
            api_keys = data.get("api_keys")
            custom_prompts = data.get("custom_prompts")

            # Validate custom_prompts is a valid JSON string if provided
            if custom_prompts is not None:
                try:
                    json.loads(custom_prompts)
                except (json.JSONDecodeError, TypeError):
                    return jsonify({"error": "custom_prompts must be a valid JSON string"}), 400

            if user_settings:
                # Update existing settings
                update_data = {}

                if api_keys is not None:
                    # Merge existing API keys with new ones
                    existing_api_keys = persistence_manager.get_api_keys(user_id) or {}
                    merged_api_keys = existing_api_keys.copy()
                    merged_api_keys.update(api_keys)
                    update_data["api_keys"] = merged_api_keys

                if custom_prompts is not None:
                    update_data["custom_prompts"] = custom_prompts

                if update_data:
                    updated_settings = persistence_manager.update_user_settings(
                        user_settings.id, **update_data
                    )
                    if not updated_settings:
                        return jsonify({"error": "Failed to update settings"}), 500
                else:
                    updated_settings = user_settings
            else:
                # Create new user settings
                updated_settings = persistence_manager.create_user_settings(
                    user_id=user_id, api_keys=api_keys, custom_prompts=custom_prompts
                )
                if not updated_settings:
                    return jsonify({"error": "Failed to create settings"}), 500

            # Return sanitized response
            settings_data = _sanitize_settings_response(updated_settings)
            return jsonify(settings_data)

        except Exception as e:
            return jsonify({"error": f"Failed to update settings: {str(e)}"}), 500

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    # Run the application
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
