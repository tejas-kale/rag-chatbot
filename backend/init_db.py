#!/usr/bin/env python3
"""
Database initialization script for the RAG chatbot.
Creates all tables and sets up initial data.
"""

from app import create_app
from models import db, UserSettings


def init_database():
    """Initialize the database with tables and default data."""
    app = create_app()
    
    with app.app_context():
        print("Initializing database...")
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Create default user settings if not exists
        default_user = UserSettings.query.filter_by(user_id='default_user').first()
        if not default_user:
            default_user = UserSettings(user_id='default_user')
            db.session.add(default_user)
            db.session.commit()
            print("✅ Default user settings created")
        else:
            print("✅ Default user settings already exist")
        
        # Print summary
        print(f"\nDatabase initialization complete!")
        print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Tables created: {len(db.metadata.tables)} tables")
        for table_name in db.metadata.tables.keys():
            print(f"  - {table_name}")


if __name__ == '__main__':
    init_database()