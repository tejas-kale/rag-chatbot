"""
Example integration of embedding factory with ChromaDB service.
This shows how the embedding configuration would be used in practice.
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_chromadb_collection_with_embeddings():
    """
    Example showing how to create a ChromaDB collection with custom embeddings.
    
    This example demonstrates the integration between the embedding factory
    and the existing ChromaDB service.
    """
    print("Example: ChromaDB collection with custom embeddings")
    print("="*60)
    
    # Example configuration
    print("1. Configuration example:")
    print("   EMBEDDING_PROVIDER=huggingface")
    print("   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2")
    print("   HUGGINGFACE_API_TOKEN=your_token_here")
    print()
    
    # Example usage with HuggingFace
    print("2. HuggingFace embedding example:")
    print("""
    from embeddings import create_embedding_function
    from chromadb_service import chromadb_service
    
    # Create embedding function
    embedding_function = create_embedding_function()
    
    # Create collection with custom embeddings
    collection = chromadb_service.get_or_create_collection(
        name="my_documents",
        embedding_function=embedding_function
    )
    
    # Add documents (embeddings will be computed automatically)
    success = chromadb_service.add_documents(
        collection_name="my_documents",
        documents=["This is a sample document", "Another document"],
        metadatas=[{"source": "file1.txt"}, {"source": "file2.txt"}]
    )
    """)
    
    # Example usage with OpenAI
    print("3. OpenAI embedding example:")
    print("""
    # Set OpenAI configuration
    os.environ['EMBEDDING_PROVIDER'] = 'openai'
    os.environ['EMBEDDING_MODEL'] = 'text-embedding-ada-002'
    os.environ['OPENAI_API_KEY'] = 'your_openai_api_key'
    
    from embeddings import EmbeddingFactory
    
    # Create OpenAI embedding model
    embedding_model = EmbeddingFactory.create_embedding_model(
        provider='openai',
        model_name='text-embedding-ada-002'
    )
    
    # Use with ChromaDB
    collection = chromadb_service.get_or_create_collection(
        name="openai_documents",
        embedding_function=embedding_model
    )
    """)
    
    # Configuration options
    print("4. Supported configurations:")
    print("""
    HuggingFace options:
    - EMBEDDING_PROVIDER=huggingface
    - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    - EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
    - EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L6-v2
    - HUGGINGFACE_API_TOKEN=optional_token
    
    OpenAI options:
    - EMBEDDING_PROVIDER=openai
    - EMBEDDING_MODEL=text-embedding-ada-002
    - EMBEDDING_MODEL=text-embedding-3-small
    - EMBEDDING_MODEL=text-embedding-3-large
    - OPENAI_API_KEY=required_api_key
    """)
    
    # Flask app integration
    print("5. Flask app integration:")
    print("""
    from flask import Flask
    from config import config
    from embeddings import get_default_embedding_model
    
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    with app.app_context():
        # Get embedding model using app configuration
        embedding_model = get_default_embedding_model()
        
        # Use in your routes or services
        @app.route('/embed')
        def embed_text():
            text = request.json.get('text')
            embeddings = embedding_model.embed_documents([text])
            return {'embeddings': embeddings}
    """)
    
    print("\n✓ Integration example complete!")


def show_factory_features():
    """Show the key features of the embedding factory."""
    print("\nEmbedding Factory Features:")
    print("="*40)
    
    features = [
        "✓ Configurable embedding providers (HuggingFace, OpenAI)",
        "✓ Environment variable configuration",
        "✓ Flask app context integration", 
        "✓ Error handling and validation",
        "✓ ChromaDB compatibility",
        "✓ Extensible design for new providers",
        "✓ API key management",
        "✓ Default model fallbacks",
        "✓ Logging and debugging support"
    ]
    
    for feature in features:
        print(f"  {feature}")


def show_usage_patterns():
    """Show common usage patterns."""
    print("\nCommon Usage Patterns:")
    print("="*30)
    
    patterns = [
        ("Quick Start", "Use get_default_embedding_model() with environment variables"),
        ("Custom Config", "Use EmbeddingFactory.create_embedding_model() with parameters"),
        ("ChromaDB Integration", "Use create_embedding_function() for collections"),
        ("Multiple Models", "Create different embedding models for different use cases"),
        ("Development vs Production", "Switch providers easily via environment variables")
    ]
    
    for i, (pattern, description) in enumerate(patterns, 1):
        print(f"  {i}. {pattern}: {description}")


if __name__ == '__main__':
    create_chromadb_collection_with_embeddings()
    show_factory_features()
    show_usage_patterns()
    print("\n" + "="*60)
    print("Embedding configuration implementation complete!")
    print("Install dependencies: pip install langchain langchain-community langchain-openai langchain-huggingface")
    print("="*60)