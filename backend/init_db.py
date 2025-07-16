#!/usr/bin/env python3
"""
Database initialization script for the RAG chatbot.
Creates all tables and sets up initial data.
"""

from app import create_app
from models import init_db


def init_database():
    """Initialize the database with tables and default data."""
    app = create_app()
    
    # Use the init_db function from models.py to avoid code duplication
    init_db(app)


if __name__ == '__main__':
    init_database()