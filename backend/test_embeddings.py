"""
Test script for embedding functionality.
This script tests the embedding factory and model creation.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import config
from embeddings import EmbeddingFactory, get_default_embedding_model, create_embedding_function


class TestEmbeddingFactory(unittest.TestCase):
    """Test cases for the EmbeddingFactory class."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.app.config.from_object(config['testing'])
        
        # Set test embedding configuration
        self.app.config['EMBEDDING_PROVIDER'] = 'huggingface'
        self.app.config['EMBEDDING_MODEL'] = 'sentence-transformers/all-MiniLM-L6-v2'
        self.app.config['OPENAI_API_KEY'] = 'test-openai-key'
        self.app.config['HUGGINGFACE_API_TOKEN'] = 'test-hf-token'
    
    def test_supported_providers(self):
        """Test that supported providers are correctly defined."""
        expected_providers = ['huggingface', 'openai']
        self.assertEqual(EmbeddingFactory.SUPPORTED_PROVIDERS, expected_providers)
    
    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        with self.app.app_context():
            with self.assertRaises(ValueError) as context:
                EmbeddingFactory.create_embedding_model(provider='unsupported')
            
            self.assertIn("Unsupported embedding provider", str(context.exception))
    
    @patch('embeddings.HuggingFaceEmbeddings')
    def test_create_huggingface_embedding_success(self, mock_hf_embeddings):
        """Test successful creation of HuggingFace embedding model."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance
            
            # Create embedding model
            result = EmbeddingFactory.create_embedding_model(
                provider='huggingface',
                model_name='test-model'
            )
            
            # Verify the result
            self.assertEqual(result, mock_embedding_instance)
            mock_hf_embeddings.assert_called_once_with(
                model_name='test-model',
                model_kwargs={'use_auth_token': 'test-hf-token'}
            )
    
    @patch('embeddings.OpenAIEmbeddings')
    def test_create_openai_embedding_success(self, mock_openai_embeddings):
        """Test successful creation of OpenAI embedding model."""
        with self.app.app_context():
            # Mock the OpenAI embeddings class
            mock_embedding_instance = MagicMock()
            mock_openai_embeddings.return_value = mock_embedding_instance
            
            # Create embedding model
            result = EmbeddingFactory.create_embedding_model(
                provider='openai',
                model_name='text-embedding-ada-002'
            )
            
            # Verify the result
            self.assertEqual(result, mock_embedding_instance)
            mock_openai_embeddings.assert_called_once_with(
                model='text-embedding-ada-002',
                openai_api_key='test-openai-key'
            )
    
    def test_openai_embedding_without_api_key_raises_error(self):
        """Test that OpenAI embedding without API key raises RuntimeError."""
        # Create app without OpenAI API key
        app = Flask(__name__)
        app.config.from_object(config['testing'])
        app.config['EMBEDDING_PROVIDER'] = 'openai'
        app.config['OPENAI_API_KEY'] = None
        
        with app.app_context():
            with self.assertRaises(RuntimeError) as context:
                EmbeddingFactory.create_embedding_model(provider='openai')
            
            self.assertIn("OpenAI API key is required", str(context.exception))
    
    @patch('embeddings.HuggingFaceEmbeddings')
    def test_default_embedding_model_uses_config(self, mock_hf_embeddings):
        """Test that default embedding model uses Flask app configuration."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance
            
            # Create default embedding model
            result = get_default_embedding_model()
            
            # Verify it uses the config values
            self.assertEqual(result, mock_embedding_instance)
            mock_hf_embeddings.assert_called_once_with(
                model_name='sentence-transformers/all-MiniLM-L6-v2',
                model_kwargs={'use_auth_token': 'test-hf-token'}
            )
    
    @patch('embeddings.HuggingFaceEmbeddings')
    def test_create_embedding_function(self, mock_hf_embeddings):
        """Test creation of embedding function for ChromaDB."""
        with self.app.app_context():
            # Mock the HuggingFace embeddings class
            mock_embedding_instance = MagicMock()
            mock_hf_embeddings.return_value = mock_embedding_instance
            
            # Create embedding function
            result = create_embedding_function()
            
            # Verify it returns the embedding model instance
            self.assertEqual(result, mock_embedding_instance)
    
    @patch.dict(os.environ, {
        'EMBEDDING_PROVIDER': 'openai',
        'EMBEDDING_MODEL': 'text-embedding-ada-002',
        'OPENAI_API_KEY': 'env-openai-key'
    })
    @patch('embeddings.OpenAIEmbeddings')
    def test_fallback_to_environment_variables(self, mock_openai_embeddings):
        """Test that factory falls back to environment variables when not in Flask context."""
        # Mock the OpenAI embeddings class
        mock_embedding_instance = MagicMock()
        mock_openai_embeddings.return_value = mock_embedding_instance
        
        # Create embedding model outside Flask context
        result = EmbeddingFactory.create_embedding_model()
        
        # Verify it uses environment variables
        self.assertEqual(result, mock_embedding_instance)
        mock_openai_embeddings.assert_called_once_with(
            model='text-embedding-ada-002',
            openai_api_key='env-openai-key'
        )


def run_embedding_tests():
    """Run the embedding tests."""
    print("Testing Embedding Factory...")
    
    try:
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestEmbeddingFactory)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print results
        if result.wasSuccessful():
            print("\n✓ All embedding tests passed!")
            return True
        else:
            print(f"\n✗ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
            return False
    
    except Exception as e:
        print(f"Error running embedding tests: {e}")
        return False


if __name__ == '__main__':
    run_embedding_tests()