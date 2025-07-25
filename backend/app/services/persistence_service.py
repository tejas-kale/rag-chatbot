"""
Persistence service for the RAG chatbot application.
Provides a clean interface for all database operations (CRUD) for all models.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import ChatHistory, DataSource, Transcription, UserSettings, db

# Configure logger
logger = logging.getLogger(__name__)


class PersistenceManager:
    """
    Service class that encapsulates all database interactions.

    Provides CRUD operations for all models with proper session management.
    """

    def __init__(self):
        """Initialize the PersistenceManager."""
        self._fernet = None

    def _get_fernet(self) -> Optional[Fernet]:
        """
        Get or create Fernet instance for encryption/decryption.

        Returns:
            Fernet instance if encryption key is available, None otherwise
        """
        if self._fernet is None:
            encryption_key = current_app.config.get("ENCRYPTION_KEY")
            if encryption_key:
                try:
                    # If the key is a string, encode it to bytes
                    if isinstance(encryption_key, str):
                        encryption_key = encryption_key.encode()
                    self._fernet = Fernet(encryption_key)
                except Exception as e:
                    logger.error(f"Failed to initialize Fernet with provided key: {e}")
                    return None
            else:
                logger.warning(
                    "No encryption key provided in ENCRYPTION_KEY environment variable"
                )
                return None
        return self._fernet

    def encrypt_key(self, data: Dict[str, Any]) -> Optional[bytes]:
        """
        Encrypt API keys data for secure storage.

        Args:
            data: Dictionary containing API keys to encrypt

        Returns:
            Encrypted bytes if successful, None if encryption fails
        """
        if not data:
            return None

        fernet = self._get_fernet()
        if not fernet:
            logger.error("Cannot encrypt data: Fernet instance not available")
            return None

        try:
            # Convert dict to JSON string, then to bytes
            json_data = json.dumps(data).encode("utf-8")
            encrypted_data = fernet.encrypt(json_data)
            logger.debug("API keys encrypted successfully")
            return encrypted_data
        except Exception as e:
            logger.error(f"Failed to encrypt API keys: {e}")
            return None

    def decrypt_key(self, encrypted_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Decrypt API keys data from storage.

        Args:
            encrypted_data: Encrypted bytes to decrypt

        Returns:
            Decrypted dictionary if successful, None if decryption fails
        """
        if not encrypted_data:
            return None

        fernet = self._get_fernet()
        if not fernet:
            logger.error("Cannot decrypt data: Fernet instance not available")
            return None

        try:
            # Decrypt bytes to JSON string, then parse to dict
            decrypted_bytes = fernet.decrypt(encrypted_data)
            json_data = decrypted_bytes.decode("utf-8")
            data = json.loads(json_data)
            logger.debug("API keys decrypted successfully")
            return data
        except Exception as e:
            logger.error(f"Failed to decrypt API keys: {e}")
            return None

    # UserSettings CRUD operations
    def create_user_settings(
        self,
        user_id: str = "default_user",
        api_keys: Dict[str, Any] = None,
        custom_prompts: str = None,
    ) -> Optional[UserSettings]:
        """
        Create a new user settings record.

        Args:
            user_id: User identifier
            api_keys: Dictionary of API keys to encrypt and store
            custom_prompts: JSON string of custom prompts

        Returns:
            UserSettings object if successful, None if failed
        """
        try:
            # Encrypt API keys if provided
            encrypted_api_keys = None
            if api_keys:
                encrypted_api_keys = self.encrypt_key(api_keys)
                if encrypted_api_keys is None:
                    logger.error(
                        "Failed to encrypt API keys during user settings creation"
                    )
                    return None

            user_settings = UserSettings(
                user_id=user_id,
                api_keys=encrypted_api_keys,
                custom_prompts=custom_prompts,
            )
            db.session.add(user_settings)
            db.session.commit()
            return user_settings
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating user settings: {e}")
            return None

    def get_user_settings_by_id(self, settings_id: int) -> Optional[UserSettings]:
        """Get user settings by ID."""
        try:
            return UserSettings.query.get(settings_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user settings by ID: {e}")
            return None

    def get_user_settings_by_user_id(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings by user ID."""
        try:
            return UserSettings.query.filter_by(user_id=user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user settings by user ID: {e}")
            return None

    def get_api_keys(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get decrypted API keys for a user.

        Args:
            user_id: User identifier

        Returns:
            Decrypted API keys dictionary if successful, None if failed
        """
        try:
            user_settings = self.get_user_settings_by_user_id(user_id)
            if not user_settings or not user_settings.api_keys:
                return None

            return self.decrypt_key(user_settings.api_keys)
        except Exception as e:
            logger.error(f"Error getting API keys for user {user_id}: {e}")
            return None

    def set_api_keys(self, user_id: str, api_keys: Dict[str, Any]) -> bool:
        """
        Set encrypted API keys for a user.

        Args:
            user_id: User identifier
            api_keys: Dictionary of API keys to encrypt and store

        Returns:
            True if successful, False if failed
        """
        try:
            user_settings = self.get_user_settings_by_user_id(user_id)
            if not user_settings:
                # Create new user settings if doesn't exist
                user_settings = self.create_user_settings(
                    user_id=user_id, api_keys=None
                )
                if user_settings is None:
                    return False

                # Now encrypt and add the API keys
                encrypted_api_keys = self.encrypt_key(api_keys)
                if encrypted_api_keys is None:
                    logger.error("Failed to encrypt API keys during user creation")
                    return False

                user_settings.api_keys = encrypted_api_keys
                user_settings.updated_at = datetime.utcnow()
                db.session.commit()
                return True

            # Encrypt the new API keys
            encrypted_api_keys = self.encrypt_key(api_keys)
            if encrypted_api_keys is None:
                logger.error("Failed to encrypt API keys during update")
                return False

            # Update existing user settings
            user_settings.api_keys = encrypted_api_keys
            user_settings.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error setting API keys for user {user_id}: {e}")
            return False

    def update_user_settings(
        self, settings_id: int, **kwargs
    ) -> Optional[UserSettings]:
        """
        Update user settings.

        Args:
            settings_id: ID of the user settings to update
            **kwargs: Fields to update (api_keys, custom_prompts, etc.)
                     Note: api_keys should be provided as a dict,
                     will be encrypted automatically

        Returns:
            Updated UserSettings object if successful, None if failed
        """
        try:
            user_settings = UserSettings.query.get(settings_id)
            if not user_settings:
                return None

            # Validate kwargs - only allow valid model attributes
            valid_attributes = {"user_id", "api_keys", "custom_prompts"}
            for key, value in kwargs.items():
                if key not in valid_attributes:
                    logger.warning(f"Invalid attribute '{key}' in kwargs, skipping")
                    continue

                if key == "api_keys" and value is not None:
                    # Encrypt API keys if provided
                    encrypted_value = self.encrypt_key(value)
                    if encrypted_value is None:
                        logger.error("Failed to encrypt API keys during update")
                        return None
                    value = encrypted_value

                if hasattr(user_settings, key):
                    setattr(user_settings, key, value)

            user_settings.updated_at = datetime.utcnow()
            db.session.commit()
            return user_settings
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating user settings: {e}")
            return None

    def delete_user_settings(self, settings_id: int) -> bool:
        """Delete user settings by ID."""
        try:
            user_settings = UserSettings.query.get(settings_id)
            if not user_settings:
                return False

            db.session.delete(user_settings)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting user settings: {e}")
            return False

    # ChatHistory CRUD operations
    def create_chat_history(
        self,
        session_id: str,
        user_message: str,
        bot_response: str = None,
        user_settings_id: int = None,
        context_sources: str = None,
    ) -> Optional[ChatHistory]:
        """
        Create a new chat history record.

        Args:
            session_id: Session identifier for grouping messages
            user_message: User's message
            bot_response: Bot's response (optional)
            user_settings_id: Associated user settings ID
            context_sources: JSON string of sources used for RAG

        Returns:
            ChatHistory object if successful, None if failed
        """
        try:
            chat_history = ChatHistory(
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                user_settings_id=user_settings_id,
                context_sources=context_sources,
            )
            db.session.add(chat_history)
            db.session.commit()
            return chat_history
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating chat history: {e}")
            return None

    def get_chat_history_by_id(self, chat_id: int) -> Optional[ChatHistory]:
        """Get chat history by ID."""
        try:
            return ChatHistory.query.get(chat_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving chat history by ID: {e}")
            return None

    def get_chat_history_by_session(
        self, session_id: str, limit: int = 100
    ) -> List[ChatHistory]:
        """Get chat history for a specific session."""
        try:
            return (
                ChatHistory.query.filter_by(session_id=session_id)
                .order_by(ChatHistory.timestamp)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving chat history by session: {e}")
            return []

    def update_chat_history(self, chat_id: int, **kwargs) -> Optional[ChatHistory]:
        """
        Update chat history record.

        Args:
            chat_id: ID of the chat history to update
            **kwargs: Fields to update

        Returns:
            Updated ChatHistory object if successful, None if failed
        """
        try:
            chat_history = ChatHistory.query.get(chat_id)
            if not chat_history:
                return None

            # Validate kwargs - only allow valid model attributes (excluding timestamp)
            valid_attributes = {
                "session_id",
                "user_message",
                "bot_response",
                "user_settings_id",
                "context_sources",
            }
            for key, value in kwargs.items():
                if key not in valid_attributes:
                    logger.warning(f"Invalid attribute '{key}' in kwargs, skipping")
                    continue
                if hasattr(chat_history, key):
                    setattr(chat_history, key, value)

            db.session.commit()
            return chat_history
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating chat history: {e}")
            return None

    def delete_chat_history(self, chat_id: int) -> bool:
        """Delete chat history by ID."""
        try:
            chat_history = ChatHistory.query.get(chat_id)
            if not chat_history:
                return False

            db.session.delete(chat_history)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting chat history: {e}")
            return False

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete all chat history for a specific session."""
        try:
            # Use bulk delete for better performance
            deleted_count = ChatHistory.query.filter_by(session_id=session_id).delete()
            db.session.commit()
            logger.info(
                f"Deleted {deleted_count} chat records for session {session_id}"
            )
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting chat session: {e}")
            return False

    # DataSource CRUD operations
    def create_data_source(
        self,
        source_type: str,
        source_path: str,
        display_name: str = None,
        file_size: int = None,
        content_hash: str = None,
        user_settings_id: int = None,
    ) -> Optional[DataSource]:
        """
        Create a new data source record.

        Args:
            source_type: Type of source ('url', 'pdf', 'markdown', etc.)
            source_path: URL or file path
            display_name: User-friendly name
            file_size: File size in bytes
            content_hash: SHA256 hash of content
            user_settings_id: Associated user settings ID

        Returns:
            DataSource object if successful, None if failed
        """
        try:
            data_source = DataSource(
                source_type=source_type,
                source_path=source_path,
                display_name=display_name,
                file_size=file_size,
                content_hash=content_hash,
                user_settings_id=user_settings_id,
            )
            db.session.add(data_source)
            db.session.commit()
            return data_source
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating data source: {e}")
            return None

    def get_data_source_by_id(self, source_id: int) -> Optional[DataSource]:
        """Get data source by ID."""
        try:
            return DataSource.query.get(source_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving data source by ID: {e}")
            return None

    def get_data_sources_by_type(self, source_type: str) -> List[DataSource]:
        """Get all data sources of a specific type."""
        try:
            return DataSource.query.filter_by(source_type=source_type).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving data sources by type: {e}")
            return []

    def get_data_sources_by_status(self, status: str) -> List[DataSource]:
        """Get all data sources with a specific status."""
        try:
            return DataSource.query.filter_by(status=status).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving data sources by status: {e}")
            return []

    def update_data_source(self, source_id: int, **kwargs) -> Optional[DataSource]:
        """
        Update data source record.

        Args:
            source_id: ID of the data source to update
            **kwargs: Fields to update

        Returns:
            Updated DataSource object if successful, None if failed
        """
        try:
            data_source = DataSource.query.get(source_id)
            if not data_source:
                return None

            # Validate kwargs - only allow valid model attributes
            # (excluding auto-managed fields)
            valid_attributes = {
                "source_type",
                "source_path",
                "display_name",
                "file_size",
                "content_hash",
                "status",
                "error_message",
                "user_settings_id",
            }
            for key, value in kwargs.items():
                if key not in valid_attributes:
                    logger.warning(f"Invalid attribute '{key}' in kwargs, skipping")
                    continue
                if hasattr(data_source, key):
                    setattr(data_source, key, value)

            # Update processed_date if status is being set to 'processed'
            if kwargs.get("status") == "processed":
                data_source.processed_date = datetime.utcnow()

            db.session.commit()
            return data_source
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating data source: {e}")
            return None

    def delete_data_source(self, source_id: int) -> bool:
        """Delete data source by ID."""
        try:
            data_source = DataSource.query.get(source_id)
            if not data_source:
                return False

            db.session.delete(data_source)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting data source: {e}")
            return False

    # Transcription CRUD operations
    def create_transcription(
        self,
        youtube_url: str,
        original_filename: str = None,
        video_duration: float = None,
        user_settings_id: int = None,
        chat_history_id: int = None,
    ) -> Optional[Transcription]:
        """
        Create a new transcription record.

        Args:
            youtube_url: YouTube URL for the video
            original_filename: Original filename
            video_duration: Duration in seconds
            user_settings_id: Associated user settings ID
            chat_history_id: Associated chat history ID

        Returns:
            Transcription object if successful, None if failed
        """
        try:
            transcription = Transcription(
                youtube_url=youtube_url,
                original_filename=original_filename,
                video_duration=video_duration,
                user_settings_id=user_settings_id,
                chat_history_id=chat_history_id,
            )
            db.session.add(transcription)
            db.session.commit()
            return transcription
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating transcription: {e}")
            return None

    def get_transcription_by_id(self, transcription_id: int) -> Optional[Transcription]:
        """Get transcription by ID."""
        try:
            return Transcription.query.get(transcription_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving transcription by ID: {e}")
            return None

    def get_transcriptions_by_status(self, status: str) -> List[Transcription]:
        """Get all transcriptions with a specific status."""
        try:
            return Transcription.query.filter_by(status=status).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving transcriptions by status: {e}")
            return []

    def update_transcription(
        self, transcription_id: int, **kwargs
    ) -> Optional[Transcription]:
        """
        Update transcription record.

        Args:
            transcription_id: ID of the transcription to update
            **kwargs: Fields to update

        Returns:
            Updated Transcription object if successful, None if failed
        """
        try:
            transcription = Transcription.query.get(transcription_id)
            if not transcription:
                return None

            # Validate kwargs - only allow valid model attributes
            # (excluding auto-managed fields)
            valid_attributes = {
                "youtube_url",
                "original_filename",
                "video_duration",
                "transcription_text",
                "confidence_score",
                "transcription_engine",
                "processing_duration",
                "status",
                "error_message",
                "user_settings_id",
                "chat_history_id",
            }
            for key, value in kwargs.items():
                if key not in valid_attributes:
                    logger.warning(f"Invalid attribute '{key}' in kwargs, skipping")
                    continue
                if hasattr(transcription, key):
                    setattr(transcription, key, value)

            # Update processed_at if status is being set to 'completed'
            if kwargs.get("status") == "completed":
                transcription.processed_at = datetime.utcnow()

            db.session.commit()
            return transcription
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating transcription: {e}")
            return None

    def delete_transcription(self, transcription_id: int) -> bool:
        """Delete transcription by ID."""
        try:
            transcription = Transcription.query.get(transcription_id)
            if not transcription:
                return False

            db.session.delete(transcription)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting transcription: {e}")
            return False

    # Utility methods
    def get_all_user_settings(self) -> List[UserSettings]:
        """Get all user settings records."""
        try:
            return UserSettings.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all user settings: {e}")
            return []

    def get_recent_chat_history(self, limit: int = 50) -> List[ChatHistory]:
        """Get recent chat history across all sessions."""
        try:
            return (
                ChatHistory.query.order_by(ChatHistory.timestamp.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving recent chat history: {e}")
            return []

    def get_all_data_sources(self) -> List[DataSource]:
        """Get all data source records."""
        try:
            return DataSource.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all data sources: {e}")
            return []

    def get_all_transcriptions(self) -> List[Transcription]:
        """Get all transcription records."""
        try:
            return Transcription.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all transcriptions: {e}")
            return []
