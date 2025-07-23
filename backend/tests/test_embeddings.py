"""
Test script for embedding functionality.
This script tests the embedding factory and model creation.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.config.config import config
from app.services.embedding_service import (EmbeddingFactory,
                                            create_embedding_function,
                                            get_default_embedding_model)

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestEmbeddingFactory:
    """Test cases for the EmbeddingFactory class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config.from_object(config["testing"])

        # Set test embedding configuration
        self.app.config["EMBEDDING_PROVIDER"] = "huggingface"
        self.app.config["EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
        self.app.config["OPENAI_API_KEY"] = "test-openai-key"
        self.app.config["HUGGINGFACE_API_TOKEN"] = "test-hf-token"

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any test artifacts if needed
        pass

    def test_supported_providers(self):
        """Test that supported providers are correctly defined."""
        expected_providers = ["huggingface", "openai"]
        assert EmbeddingFactory.SUPPORTED_PROVIDERS == expected_providers

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        with self.app.app_context():
            with pytest.raises(ValueError) as exc_info:
                EmbeddingFactory.create_embedding_model(provider="unsupported")

            assert "Unsupported embedding provider" in str(exc_info.value)

    @patch("app.services.embedding_service.HuggingFaceEmbeddings")
    def test_create_huggingface_embedding_success(self, mock_hf_embeddings):
        """Test successful creation of HuggingFace embedding model."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance

            # Create embedding model
            result = EmbeddingFactory.create_embedding_model(
                provider="huggingface", model_name="test-model"
            )

            # Verify the result
            assert result == mock_embedding_instance
            mock_hf_embeddings.assert_called_once_with(
                model_name="test-model",
                model_kwargs={"use_auth_token": "test-hf-token"},
            )

    @patch("app.services.embedding_service.OpenAIEmbeddings")
    def test_create_openai_embedding_success(self, mock_openai_embeddings):
        """Test successful creation of OpenAI embedding model."""
        with self.app.app_context():
            # Mock the OpenAI embeddings class
            mock_embedding_instance = MagicMock()
            mock_openai_embeddings.return_value = mock_embedding_instance

            # Create embedding model
            result = EmbeddingFactory.create_embedding_model(
                provider="openai", model_name="text-embedding-ada-002"
            )

            # Verify the result
            assert result == mock_embedding_instance
            mock_openai_embeddings.assert_called_once_with(
                model="text-embedding-ada-002", openai_api_key="test-openai-key"
            )

    def test_openai_embedding_without_api_key_raises_error(self):
        """Test that OpenAI embedding without API key raises RuntimeError."""
        # Create app without OpenAI API key
        app = Flask(__name__)
        app.config.from_object(config["testing"])
        app.config["EMBEDDING_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = None

        with app.app_context():
            # Patch OpenAIEmbeddings to be available (simulate dependency installed)
            with patch(
                "app.services.embedding_service.OpenAIEmbeddings", new=MagicMock()
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    EmbeddingFactory.create_embedding_model(provider="openai")

                assert "OpenAI API key is required" in str(exc_info.value)

    @patch("app.services.embedding_service.HuggingFaceEmbeddings")
    def test_default_embedding_model_uses_config(self, mock_hf_embeddings):
        """Test that default embedding model uses Flask app configuration."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance

            # Create default embedding model
            result = get_default_embedding_model()

            # Verify it uses the config values
            assert result == mock_embedding_instance
            mock_hf_embeddings.assert_called_once_with(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"use_auth_token": "test-hf-token"},
            )

    @patch("app.services.embedding_service.HuggingFaceEmbeddings")
    def test_create_embedding_function(self, mock_hf_embeddings):
        """Test creation of embedding function for ChromaDB."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance

            # Create embedding function
            result = create_embedding_function()

            # Verify it returns the embedding model instance
            assert result == mock_embedding_instance

    @patch.dict(
        os.environ,
        {
            "EMBEDDING_PROVIDER": "openai",
            "EMBEDDING_MODEL": "text-embedding-ada-002",
            "OPENAI_API_KEY": "env-openai-key",
        },
    )
    @patch("app.services.embedding_service.OpenAIEmbeddings")
    @patch("app.services.embedding_service.hasattr")
    def test_fallback_to_environment_variables(
        self, mock_hasattr, mock_openai_embeddings
    ):
        """
        Test that factory falls back to environment variables when
        not in Flask context.
        """
        # Mock the OpenAI embeddings class
        mock_embedding_instance = MagicMock()
        mock_openai_embeddings.return_value = mock_embedding_instance

        # Mock hasattr to return False (simulate no Flask context)
        mock_hasattr.return_value = False

        # Create embedding model outside Flask context
        result = EmbeddingFactory.create_embedding_model()

        # Verify it uses environment variables
        assert result == mock_embedding_instance
        mock_openai_embeddings.assert_called_once_with(
            model="text-embedding-ada-002", openai_api_key="env-openai-key"
        )


if __name__ == "__main__":
    # Run tests with pytest when executed directly
    import subprocess

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"], capture_output=False
    )
    sys.exit(result.returncode)
