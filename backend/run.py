#!/usr/bin/env python3
"""
Entry point for the RAG Chatbot application.
This script runs the Flask development server.
"""

import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app

if __name__ == '__main__':
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create the Flask app
    app = create_app(config_name)
    
    # Run the development server
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=config_name == 'development'
    )