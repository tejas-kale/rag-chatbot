"""
Embedding model factory for the RAG chatbot application.
Provides configurable embedding models for different providers.
"""

import os
import logging
from typing import Optional, Union, Any
from flask import current_app

# Configure logger
logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """
    Factory class for creating embedding models from different providers.
    
    Supports HuggingFace and OpenAI embedding models with configuration
    via environment variables.
    """
    
    SUPPORTED_PROVIDERS = ['huggingface', 'openai']
    
    @staticmethod
    def create_embedding_model(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Any:
        """
        Create an embedding model based on the specified provider.
        
        Args:
            provider: Embedding provider ('huggingface' or 'openai')
            model_name: Name of the model to use
            api_key: API key for the provider (if required)
            
        Returns:
            LangChain embedding model instance
            
        Raises:
            ValueError: If provider is not supported
            ImportError: If required dependencies are not installed
            RuntimeError: If configuration is invalid
        """
        # Get configuration from Flask app config or use provided values
        if hasattr(current_app, 'config'):
            provider = provider or current_app.config.get('EMBEDDING_PROVIDER', 'huggingface')
            model_name = model_name or current_app.config.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        else:
            # Fallback to environment variables if not in Flask context
            provider = provider or os.environ.get('EMBEDDING_PROVIDER', 'huggingface')
            model_name = model_name or os.environ.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        
        provider = provider.lower()
        
        if provider not in EmbeddingFactory.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported embedding provider: {provider}. Supported providers: {EmbeddingFactory.SUPPORTED_PROVIDERS}")
        
        logger.info(f"Creating {provider} embedding model: {model_name}")
        
        if provider == 'huggingface':
            return EmbeddingFactory._create_huggingface_embedding(model_name, api_key)
        elif provider == 'openai':
            return EmbeddingFactory._create_openai_embedding(model_name, api_key)
    
    @staticmethod
    def _create_huggingface_embedding(model_name: str, api_key: Optional[str] = None) -> Any:
        """
        Create a HuggingFace embedding model.
        
        Args:
            model_name: HuggingFace model name
            api_key: Optional HuggingFace API token
            
        Returns:
            HuggingFaceEmbeddings instance
        """
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-huggingface is required for HuggingFace embeddings. "
                "Install it with: pip install langchain-huggingface"
            )
        
        # Get API token from parameter, Flask config, or environment
        if api_key is None:
            if hasattr(current_app, 'config'):
                api_key = current_app.config.get('HUGGINGFACE_API_TOKEN')
            else:
                api_key = os.environ.get('HUGGINGFACE_API_TOKEN')
        
        # Configure model parameters
        model_kwargs = {}
        if api_key:
            model_kwargs['use_auth_token'] = api_key
        
        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs
            )
            logger.info(f"Successfully created HuggingFace embedding model: {model_name}")
            return embedding_model
        except Exception as e:
            logger.error(f"Failed to create HuggingFace embedding model '{model_name}': {e}")
            raise RuntimeError(f"Failed to initialize HuggingFace embedding model: {e}")
    
    @staticmethod
    def _create_openai_embedding(model_name: str, api_key: Optional[str] = None) -> Any:
        """
        Create an OpenAI embedding model.
        
        Args:
            model_name: OpenAI model name (e.g., 'text-embedding-ada-002')
            api_key: OpenAI API key
            
        Returns:
            OpenAIEmbeddings instance
        """
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI embeddings. "
                "Install it with: pip install langchain-openai"
            )
        
        # Get API key from parameter, Flask config, or environment
        if api_key is None:
            if hasattr(current_app, 'config'):
                api_key = current_app.config.get('OPENAI_API_KEY')
            else:
                api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            raise RuntimeError(
                "OpenAI API key is required for OpenAI embeddings. "
                "Set OPENAI_API_KEY environment variable or provide api_key parameter."
            )
        
        try:
            embedding_model = OpenAIEmbeddings(
                model=model_name,
                openai_api_key=api_key
            )
            logger.info(f"Successfully created OpenAI embedding model: {model_name}")
            return embedding_model
        except Exception as e:
            logger.error(f"Failed to create OpenAI embedding model '{model_name}': {e}")
            raise RuntimeError(f"Failed to initialize OpenAI embedding model: {e}")


def get_default_embedding_model() -> Any:
    """
    Get the default embedding model based on current configuration.
    
    This is a convenience function that creates an embedding model
    using the default configuration from environment variables or Flask config.
    
    Returns:
        LangChain embedding model instance
    """
    return EmbeddingFactory.create_embedding_model()


def create_embedding_function() -> Any:
    """
    Create an embedding function compatible with ChromaDB.
    
    This function creates a LangChain embedding model and returns it
    in a format that can be used with ChromaDB's embedding_function parameter.
    
    Returns:
        Embedding function compatible with ChromaDB
    """
    embedding_model = get_default_embedding_model()
    
    # ChromaDB expects an embedding function that can handle lists of texts
    # LangChain embeddings have an embed_documents method for this purpose
    return embedding_model