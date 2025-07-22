"""
Test file for encryption/decryption functionality.
"""

import os
import tempfile

import pytest
from cryptography.fernet import Fernet
from flask import Flask

from app.models.models import db, init_db
from app.services.persistence_service import PersistenceManager


class TestConfig:
    """Test configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY = Fernet.generate_key()


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config.from_object(TestConfig)

    with app.app_context():
        init_db(app)
        yield app


@pytest.fixture
def persistence_manager(app):
    """Create PersistenceManager instance for testing."""
    with app.app_context():
        return PersistenceManager()


def test_encrypt_decrypt_key(persistence_manager):
    """Test encryption and decryption of API keys."""
    # Test data
    api_keys = {
        "openai": "sk-test-openai-key-123",
        "anthropic": "sk-ant-test-key-456",
        "google": "test-google-key-789",
    }

    # Test encryption
    encrypted_data = persistence_manager.encrypt_key(api_keys)
    assert encrypted_data is not None
    assert isinstance(encrypted_data, bytes)
    assert len(encrypted_data) > 0

    # Test decryption
    decrypted_data = persistence_manager.decrypt_key(encrypted_data)
    assert decrypted_data is not None
    assert isinstance(decrypted_data, dict)
    assert decrypted_data == api_keys


def test_encrypt_empty_data(persistence_manager):
    """Test encryption with empty data."""
    # Test with None
    encrypted_data = persistence_manager.encrypt_key(None)
    assert encrypted_data is None

    # Test with empty dict
    encrypted_data = persistence_manager.encrypt_key({})
    assert encrypted_data is None


def test_decrypt_empty_data(persistence_manager):
    """Test decryption with empty data."""
    # Test with None
    decrypted_data = persistence_manager.decrypt_key(None)
    assert decrypted_data is None


def test_decrypt_invalid_data(persistence_manager):
    """Test decryption with invalid data."""
    # Test with invalid encrypted data
    decrypted_data = persistence_manager.decrypt_key(b"invalid_data")
    assert decrypted_data is None


def test_create_user_settings_with_api_keys(persistence_manager):
    """Test creating user settings with encrypted API keys."""
    api_keys = {"openai": "sk-test-key-123", "anthropic": "sk-ant-key-456"}

    # Create user settings
    user_settings = persistence_manager.create_user_settings(
        user_id="test_user",
        api_keys=api_keys,
        custom_prompts='{"system": "You are a helpful assistant"}',
    )

    assert user_settings is not None
    assert user_settings.user_id == "test_user"
    assert user_settings.api_keys is not None
    assert isinstance(user_settings.api_keys, bytes)


def test_get_set_api_keys(persistence_manager):
    """Test getting and setting API keys for a user."""
    user_id = "test_user_2"
    api_keys = {"openai": "sk-test-key-999", "cohere": "test-cohere-key"}

    # Set API keys
    success = persistence_manager.set_api_keys(user_id, api_keys)
    assert success is True

    # Get API keys
    retrieved_keys = persistence_manager.get_api_keys(user_id)
    assert retrieved_keys is not None
    assert retrieved_keys == api_keys


def test_update_user_settings_with_api_keys(persistence_manager):
    """Test updating user settings with new encrypted API keys."""
    # Create initial user settings
    initial_keys = {"openai": "initial-key"}
    user_settings = persistence_manager.create_user_settings(
        user_id="test_update_user", api_keys=initial_keys
    )
    assert user_settings is not None

    # Update with new API keys
    new_keys = {"openai": "updated-key", "anthropic": "new-anthropic-key"}
    updated_settings = persistence_manager.update_user_settings(
        user_settings.id, api_keys=new_keys
    )

    assert updated_settings is not None
    assert updated_settings.id == user_settings.id

    # Verify the keys were updated
    retrieved_keys = persistence_manager.get_api_keys("test_update_user")
    assert retrieved_keys == new_keys


def test_no_encryption_key_app():
    """Test behavior when no encryption key is provided."""
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            # Note: No ENCRYPTION_KEY provided
        }
    )

    with app.app_context():
        init_db(app)
        pm = PersistenceManager()

        # Should return None when no encryption key
        api_keys = {"test": "key"}
        encrypted = pm.encrypt_key(api_keys)
        assert encrypted is None

        decrypted = pm.decrypt_key(b"some_data")
        assert decrypted is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
