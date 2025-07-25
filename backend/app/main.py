"""
Main Flask application for the RAG chatbot.
"""

import os

from flask import Flask
from flask_cors import CORS

from app.api.routes import api_bp
from app.config.config import config
from app.models.models import init_db


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

    # Register API blueprint
    app.register_blueprint(api_bp)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    # Run the application
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
