# Complete LangChain Embedding Integration Demo

This document provides comprehensive examples of integrating the LangChain embedding configuration with ChromaDB service for the RAG chatbot.

## Table of Contents

1. [Quick Start Example](#quick-start-example)
2. [Configuration Options](#configuration-options)
3. [Integration Examples](#integration-examples)
4. [Multi-Model Usage](#multi-model-usage)
5. [Error Handling](#error-handling)
6. [Testing Approach](#testing-approach)
7. [Flask App Integration](#flask-app-integration)

## Quick Start Example

### Basic HuggingFace Setup

```python
# Example 1: Basic setup with default HuggingFace embeddings
import os
from flask import Flask
from config import config
from embeddings import create_embedding_function
from chromadb_service import chromadb_service

# Create Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

with app.app_context():
    # Create embedding function using default configuration
    embedding_function = create_embedding_function()
    
    # Create ChromaDB collection with custom embeddings
    collection = chromadb_service.get_or_create_collection(
        name="my_rag_documents",
        embedding_function=embedding_function
    )
    
    # Add documents with automatic embedding generation
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "ChromaDB is a vector database for embedding storage."
    ]
    
    success = chromadb_service.add_documents(
        collection_name="my_rag_documents",
        documents=documents,
        metadatas=[
            {"source": "example1.txt", "type": "sentence"},
            {"source": "ml_intro.txt", "type": "definition"},
            {"source": "chromadb_info.txt", "type": "description"}
        ]
    )
    
    if success:
        print("Documents added successfully with embeddings!")
    
    # Query the collection
    results = chromadb_service.query_documents(
        collection_name="my_rag_documents",
        query_texts=["What is machine learning?"],
        n_results=2
    )
    
    print("Query results:", results)
```

## Configuration Options

### Environment Variables

Set the following environment variables to configure your embedding provider:

```bash
# HuggingFace Configuration (Default)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_API_TOKEN=your_token_here  # Optional

# OpenAI Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_openai_api_key     # Required for OpenAI
```

### Supported Models

#### HuggingFace Models
- `sentence-transformers/all-MiniLM-L6-v2` (default, fast)
- `sentence-transformers/all-mpnet-base-v2` (high quality)
- `sentence-transformers/paraphrase-MiniLM-L6-v2`
- `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`
- `sentence-transformers/all-distilroberta-v1`

#### OpenAI Models
- `text-embedding-ada-002` (legacy)
- `text-embedding-3-small` (recommended)
- `text-embedding-3-large` (highest quality)

## Integration Examples

### Example 1: HuggingFace Integration

```python
from embeddings import create_embedding_function
from chromadb_service import chromadb_service

# Configuration
# EMBEDDING_PROVIDER=huggingface
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# HUGGINGFACE_API_TOKEN=your_token_here

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
```

### Example 2: OpenAI Integration

```python
# Set OpenAI configuration
os.environ['EMBEDDING_PROVIDER'] = 'openai'
os.environ['EMBEDDING_MODEL'] = 'text-embedding-3-small'
os.environ['OPENAI_API_KEY'] = 'your_openai_api_key'

from embeddings import EmbeddingFactory

# Create OpenAI embedding model
embedding_model = EmbeddingFactory.create_embedding_model(
    provider='openai',
    model_name='text-embedding-3-small'
)

# Use with ChromaDB
collection = chromadb_service.get_or_create_collection(
    name="openai_documents",
    embedding_function=embedding_model
)

# Add documents with OpenAI embeddings
success = chromadb_service.add_documents(
    collection_name="openai_documents",
    documents=["Advanced RAG with OpenAI embeddings"],
    metadatas=[{"source": "advanced_rag.txt"}]
)
```

## Multi-Model Usage

### Using Different Models for Different Use Cases

```python
# Use different embedding models for different use cases
with app.app_context():
    # Fast embeddings for development
    fast_embeddings = EmbeddingFactory.create_embedding_model(
        provider='huggingface',
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )
    
    # High-quality embeddings for production
    quality_embeddings = EmbeddingFactory.create_embedding_model(
        provider='huggingface', 
        model_name='sentence-transformers/all-mpnet-base-v2'
    )
    
    # Create separate collections
    dev_collection = chromadb_service.get_or_create_collection(
        name="dev_documents",
        embedding_function=fast_embeddings
    )
    
    prod_collection = chromadb_service.get_or_create_collection(
        name="prod_documents", 
        embedding_function=quality_embeddings
    )
```

### Context-Specific Models

```python
# Create context-specific embedding models
qa_embeddings = EmbeddingFactory.create_embedding_model(
    provider='huggingface',
    model_name='sentence-transformers/multi-qa-MiniLM-L6-cos-v1'
)

paraphrase_embeddings = EmbeddingFactory.create_embedding_model(
    provider='huggingface',
    model_name='sentence-transformers/paraphrase-MiniLM-L6-v2'
)

# Use for specific document types
qa_collection = chromadb_service.get_or_create_collection(
    name="qa_documents",
    embedding_function=qa_embeddings
)

paraphrase_collection = chromadb_service.get_or_create_collection(
    name="paraphrase_documents",
    embedding_function=paraphrase_embeddings
)
```

## Error Handling

### Common Error Scenarios and Solutions

```python
# Handle unsupported provider
try:
    bad_embedding = EmbeddingFactory.create_embedding_model(
        provider='unsupported_provider'
    )
except ValueError as e:
    print(f"Provider error: {e}")
    # Solution: Use 'huggingface' or 'openai'

# Handle missing OpenAI API key
try:
    openai_embedding = EmbeddingFactory.create_embedding_model(
        provider='openai'
    )
except RuntimeError as e:
    print(f"Configuration error: {e}")
    # Solution: Set OPENAI_API_KEY environment variable

# Handle import errors (missing dependencies)
try:
    embedding = EmbeddingFactory.create_embedding_model()
except ImportError as e:
    print(f"Dependency error: {e}")
    print("Install missing dependencies with:")
    print("pip install langchain langchain-huggingface langchain-openai")
```

### Graceful Fallbacks

```python
def get_embedding_with_fallback():
    """Get embedding model with graceful fallback."""
    try:
        # Try OpenAI first (if configured)
        if os.environ.get('OPENAI_API_KEY'):
            return EmbeddingFactory.create_embedding_model(provider='openai')
    except Exception as e:
        print(f"OpenAI embedding failed: {e}")
    
    try:
        # Fallback to HuggingFace
        return EmbeddingFactory.create_embedding_model(provider='huggingface')
    except Exception as e:
        print(f"HuggingFace embedding failed: {e}")
        raise RuntimeError("No embedding provider available")
```

## Testing Approach

### Unit Tests

```bash
# Run unit tests with pytest
python -m pytest test_embeddings.py -v

# Run with coverage
python -m pytest test_embeddings.py --cov=embeddings --cov-report=html
```

### Validation Script

```bash
# Run validation script (no dependencies required)
python validate_embeddings.py
```

### Integration Testing

```python
# Test with actual ChromaDB
from embeddings import create_embedding_function
from chromadb_service import chromadb_service

# Test embedding creation
embedding_fn = create_embedding_function()
print('Embedding function created successfully!')

# Test ChromaDB integration
collection = chromadb_service.get_or_create_collection(
    name='test_embeddings',
    embedding_function=embedding_fn
)
print('ChromaDB collection created with embeddings!')
```

### Performance Testing

```python
import time
from embeddings import EmbeddingFactory

# Compare different models
models = [
    ('huggingface', 'sentence-transformers/all-MiniLM-L6-v2'),
    ('huggingface', 'sentence-transformers/all-mpnet-base-v2'),
]

test_docs = ["Sample document for testing"] * 100

for provider, model_name in models:
    embedding_model = EmbeddingFactory.create_embedding_model(
        provider=provider,
        model_name=model_name
    )
    
    start_time = time.time()
    embeddings = embedding_model.embed_documents(test_docs)
    end_time = time.time()
    
    print(f"{model_name}: {end_time - start_time:.2f}s for {len(test_docs)} docs")
```

## Flask App Integration

### Basic Flask Integration

```python
from flask import Flask, request, jsonify
from config import config
from embeddings import get_default_embedding_model

app = Flask(__name__)
app.config.from_object(config['development'])

with app.app_context():
    # Get embedding model using app configuration
    embedding_model = get_default_embedding_model()

@app.route('/embed', methods=['POST'])
def embed_text():
    """Endpoint to generate embeddings for text."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        text = data['text']
        embeddings = embedding_model.embed_documents([text])
        return jsonify({'embeddings': embeddings[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/embed/batch', methods=['POST'])
def embed_batch():
    """Endpoint to generate embeddings for multiple texts."""
    data = request.get_json()
    if not data or 'texts' not in data:
        return jsonify({'error': 'Texts array is required'}), 400
    
    try:
        texts = data['texts']
        embeddings = embedding_model.embed_documents(texts)
        return jsonify({'embeddings': embeddings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Advanced Flask Integration with ChromaDB

```python
@app.route('/documents', methods=['POST'])
def add_documents():
    """Add documents to ChromaDB with embeddings."""
    data = request.get_json()
    
    try:
        # Create collection with configured embeddings
        embedding_function = create_embedding_function()
        collection = chromadb_service.get_or_create_collection(
            name=data.get('collection_name', 'default'),
            embedding_function=embedding_function
        )
        
        # Add documents
        success = chromadb_service.add_documents(
            collection_name=data.get('collection_name', 'default'),
            documents=data['documents'],
            metadatas=data.get('metadatas', [])
        )
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_documents():
    """Search documents using semantic similarity."""
    data = request.get_json()
    
    try:
        results = chromadb_service.query_documents(
            collection_name=data.get('collection_name', 'default'),
            query_texts=data['query_texts'],
            n_results=data.get('n_results', 5)
        )
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Next Steps

After setting up the embedding configuration:

1. **Install Dependencies**
   ```bash
   pip install langchain langchain-community langchain-openai langchain-huggingface
   ```

2. **Configure Environment Variables**
   Copy `.env.example` to `.env` and set your provider configuration.

3. **Test Integration**
   ```bash
   python test_embeddings.py
   python validate_embeddings.py
   ```

4. **Use in RAG Pipeline**
   Integrate with your existing ChromaDB service for semantic search and retrieval.

## Features Summary

✅ **Configurable embedding providers** (HuggingFace, OpenAI)  
✅ **Environment variable configuration**  
✅ **ChromaDB service integration**  
✅ **Error handling and validation**  
✅ **Flask app context support**  
✅ **Comprehensive testing**  
✅ **Performance optimization options**  
✅ **Multiple model support**  
✅ **Graceful fallback mechanisms**  

This implementation provides a robust, configurable embedding system that seamlessly integrates with your existing RAG chatbot infrastructure while maintaining flexibility for future enhancements.