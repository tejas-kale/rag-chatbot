"""
Database models for the RAG chatbot application.
Defines SQLAlchemy models for persistent data storage.
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import LargeBinary, Text

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class UserSettings(db.Model):
    """
    Model for storing user settings including API keys and custom prompts.

    Covers requirements FR4.2 (API keys) and FR4.4 (custom prompts).
    """

    __tablename__ = "user_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(100), nullable=True, default="default_user"
    )  # For future multi-user support

    # Encrypted API keys storage (JSON format)
    api_keys = db.Column(LargeBinary, nullable=True)  # Will store encrypted JSON

    # Custom prompts storage (JSON format)
    custom_prompts = db.Column(Text, nullable=True)  # JSON string of custom prompts

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    chat_sessions = db.relationship("ChatHistory", backref=__tablename__, lazy=True)
    data_sources = db.relationship("DataSource", backref=__tablename__, lazy=True)
    transcriptions = db.relationship("Transcription", backref=__tablename__, lazy=True)

    def __repr__(self):
        return f"<UserSettings {self.user_id}>"


class ChatHistory(db.Model):
    """
    Model for storing chat conversation history.

    Covers requirement FR4.1 (chat conversation history).

    Sample row:
    {
        "id": 1,
        "session_id": "session_123",
        "user_message": "What is machine learning?",
        "bot_response": "Machine learning is a subset of AI...",
        "timestamp": "2024-01-15 10:30:00",
        "context_sources": "[{'source': 'ml_basics.pdf', 'score': 0.95}]"
    }
    """

    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(100), nullable=False
    )  # To group messages in conversations

    # Message content
    user_message = db.Column(Text, nullable=False)
    bot_response = db.Column(Text, nullable=True)

    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_settings_id = db.Column(
        db.Integer, db.ForeignKey("user_settings.id"), nullable=True
    )

    # Additional context information
    context_sources = db.Column(
        Text, nullable=True
    )  # JSON string of sources used for RAG

    # Relationship to transcriptions (if transcription is used in chat)
    transcription = db.relationship(
        "Transcription", backref=__tablename__, uselist=False, lazy=True
    )

    def __repr__(self):
        return f"<ChatHistory {self.session_id}: {self.user_message[:50]}...>"


class DataSource(db.Model):
    """
    Model for storing references to data sources.

    Covers requirement FR4.3 (data sources persistence).
    """

    __tablename__ = "data_sources"

    id = db.Column(db.Integer, primary_key=True)

    # Source information
    source_type = db.Column(
        db.String(20), nullable=False
    )  # 'url', 'pdf', 'markdown', etc.
    source_path = db.Column(db.String(500), nullable=False)  # URL or file path
    display_name = db.Column(db.String(200), nullable=True)  # User-friendly name

    # Metadata
    file_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    content_hash = db.Column(db.String(64), nullable=True)  # SHA256 hash of content

    # Status and processing info
    status = db.Column(
        db.String(20), default="pending"
    )  # 'pending', 'processed', 'error'
    error_message = db.Column(Text, nullable=True)

    # Timestamps
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime, nullable=True)

    # Foreign key to user settings
    user_settings_id = db.Column(
        db.Integer, db.ForeignKey("user_settings.id"), nullable=True
    )

    def __repr__(self):
        return (
            f"<DataSource {self.source_type}: {self.display_name or self.source_path}>"
        )


class Transcription(db.Model):
    """
    Model for storing audio transcription data.

    Supports audio input functionality for the chatbot.
    """

    __tablename__ = "transcriptions"

    id = db.Column(db.Integer, primary_key=True)

    # YouTube URL (instead of persisting MP3 files)
    youtube_url = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(200), nullable=True)
    video_duration = db.Column(db.Float, nullable=True)  # Duration in seconds

    # Transcription content
    transcription_text = db.Column(Text, nullable=True)
    confidence_score = db.Column(
        db.Float, nullable=True
    )  # Transcription confidence (0-1)

    # Processing info
    transcription_engine = db.Column(
        db.String(50), nullable=True
    )  # 'whisper', 'google', etc.
    processing_duration = db.Column(
        db.Float, nullable=True
    )  # Time taken to process (seconds)

    # Status
    status = db.Column(
        db.String(20), default="pending"
    )  # 'pending', 'completed', 'error'
    error_message = db.Column(Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    # Foreign key to user settings
    user_settings_id = db.Column(
        db.Integer, db.ForeignKey("user_settings.id"), nullable=True
    )

    # Foreign key to chat history (if transcription is used in chat)
    chat_history_id = db.Column(
        db.Integer, db.ForeignKey("chat_history.id"), nullable=True
    )

    def __repr__(self):
        return f"<Transcription {self.original_filename}: {self.status}>"


def init_db(app):
    """
    Initialize the database with the Flask application.

    Args:
        app: Flask application instance
    """
    db.init_app(app)

    with app.app_context():
        print("Initializing database...")

        # Create all tables
        db.create_all()
        print("✅ Database tables created")

        # Create default user settings if not exists
        default_user = UserSettings.query.filter_by(user_id="default_user").first()
        if not default_user:
            default_user = UserSettings(user_id="default_user")
            db.session.add(default_user)
            db.session.commit()
            print("✅ Default user settings created")
        else:
            print("✅ Default user settings already exist")

        # Print summary
        print("\nDatabase initialization complete!")
        print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Tables created: {len(db.metadata.tables)} tables")
        for table_name in db.metadata.tables.keys():
            print(f"  - {table_name}")
