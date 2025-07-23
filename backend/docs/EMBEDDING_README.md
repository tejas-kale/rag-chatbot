# LangChain Embedding Configuration

This document describes the implementation of configurable LangChain embeddings for the RAG chatbot backend.

## Overview

The embedding configuration system provides a factory pattern for creating different embedding models that can be used with the ChromaDB vector database. It supports both HuggingFace and OpenAI embedding providers with configuration via environment variables.

## Features

- ✅ **Multiple Providers**: Support for HuggingFace and OpenAI embeddings
- ✅ **Environment Configuration**: Configurable via environment variables
- ✅ **Flask Integration**: Works seamlessly with Flask app context
- ✅ **ChromaDB Compatible**: Direct integration with existing ChromaDB service
- ✅ **Error Handling**: Comprehensive error handling and validation
- ✅ **Extensible Design**: Easy to add new embedding providers
- ✅ **API Key Management**: Secure handling of API keys
- ✅ **Default Fallbacks**: Sensible defaults for quick setup

## Files

| File | Description |
|------|-------------|
| `embeddings.py` | Main embedding factory implementation |
| `config.py` | Updated with embedding configuration options |
| `test_embeddings.py` | Comprehensive unit tests |
| `validate_embeddings.py` | Validation script (no dependencies) |
| `embedding_integration_example.py` | Usage examples |
| `complete_integration_demo.py` | Complete demo with all features |
| `.env.example` | Updated with embedding environment variables |
| `pyproject.toml` | Updated with LangChain dependencies |

## Installation

Add the required dependencies to your environment:

```bash
pip install langchain langchain-community langchain-openai langchain-huggingface
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Embedding Configuration
EMBEDDING_PROVIDER=huggingface  # or 'openai'
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_API_KEY=your-openai-api-key-here
HUGGINGFACE_API_TOKEN=your-hf-token-here  # optional
```

### HuggingFace Models

```bash
# Fast, lightweight model (default)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# High quality model
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Paraphrase detection
EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L6-v2
```

### OpenAI Models

```bash
# Legacy model
EMBEDDING_MODEL=text-embedding-ada-002

# Recommended models
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_MODEL=text-embedding-3-large
```

## Usage

### Basic Usage

```python
from embeddings import get_default_embedding_model
from chromadb_service import chromadb_service

# Get default embedding model (uses environment configuration)
embedding_model = get_default_embedding_model()

# Create ChromaDB collection with embeddings
collection = chromadb_service.get_or_create_collection(
    name="my_documents",
    embedding_function=embedding_model
)

# Add documents (embeddings computed automatically)
success = chromadb_service.add_documents(
    collection_name="my_documents",
    documents=["Document text here"],
    metadatas=[{"source": "file.txt"}]
)
```

### Custom Configuration

```python
from embeddings import EmbeddingFactory

# Create specific embedding model
embedding_model = EmbeddingFactory.create_embedding_model(
    provider='openai',
    model_name='text-embedding-3-small',
    api_key='your-api-key'
)

# Use with ChromaDB
collection = chromadb_service.get_or_create_collection(
    name="openai_documents",
    embedding_function=embedding_model
)
```

### Flask App Integration

```python
from flask import Flask
from config import config
from embeddings import create_embedding_function

app = Flask(__name__)
app.config.from_object(config['development'])

with app.app_context():
    # Create embedding function using app configuration
    embedding_function = create_embedding_function()
    
    # Use in your application
    @app.route('/embed')
    def embed_text():
        text = request.json.get('text')
        embeddings = embedding_function.embed_documents([text])
        return {'embeddings': embeddings}
```

## API Reference

### EmbeddingFactory

Main factory class for creating embedding models.

#### Methods

- `create_embedding_model(provider=None, model_name=None, api_key=None)`: Create embedding model
- `_create_huggingface_embedding(model_name, api_key=None)`: Create HuggingFace embedding
- `_create_openai_embedding(model_name, api_key=None)`: Create OpenAI embedding

#### Class Attributes

- `SUPPORTED_PROVIDERS`: List of supported providers (`['huggingface', 'openai']`)

### Convenience Functions

- `get_default_embedding_model()`: Get embedding model using default configuration
- `create_embedding_function()`: Create ChromaDB-compatible embedding function

## Error Handling

The implementation includes comprehensive error handling:

```python
# Unsupported provider
try:
    embedding = EmbeddingFactory.create_embedding_model(provider='unknown')
except ValueError as e:
    print(f"Provider error: {e}")

# Missing API key
try:
    embedding = EmbeddingFactory.create_embedding_model(provider='openai')
except RuntimeError as e:
    print(f"Configuration error: {e}")

# Missing dependencies
try:
    embedding = EmbeddingFactory.create_embedding_model()
except ImportError as e:
    print(f"Dependency error: {e}")
```

## Testing

### Run Unit Tests

```bash
python test_embeddings.py
```

### Run Validation (No Dependencies)

```bash
python validate_embeddings.py
```

### Run Examples

```bash
python embedding_integration_example.py
python complete_integration_demo.py
```

## ChromaDB Integration

The embedding factory integrates seamlessly with the existing ChromaDB service:

```python
from embeddings import create_embedding_function
from chromadb_service import chromadb_service

# Create embedding function
embedding_function = create_embedding_function()

# Use with ChromaDB service methods
collection = chromadb_service.get_or_create_collection(
    name="documents", 
    embedding_function=embedding_function
)

# Add documents with automatic embedding
chromadb_service.add_documents(
    collection_name="documents",
    documents=["Text to embed"],
    metadatas=[{"source": "file.txt"}]
)

# Query with semantic search
results = chromadb_service.query_documents(
    collection_name="documents",
    query_texts=["What is this about?"],
    n_results=5
)
```

## Performance Considerations

### Model Selection

- **HuggingFace**: Local inference, no API costs, good for development
- **OpenAI**: API-based, usage costs, high quality embeddings

### Recommended Models

| Use Case | Provider | Model | Notes |
|----------|----------|--------|-------|
| Development | HuggingFace | `all-MiniLM-L6-v2` | Fast, small |
| Production | HuggingFace | `all-mpnet-base-v2` | High quality |
| Commercial | OpenAI | `text-embedding-3-small` | Balanced cost/quality |
| High-end | OpenAI | `text-embedding-3-large` | Best quality |

## Security

- API keys are loaded from environment variables
- No hardcoded credentials in source code
- Support for optional HuggingFace tokens
- Validation of required API keys

## Extensibility

To add a new embedding provider:

1. Add provider to `SUPPORTED_PROVIDERS`
2. Implement `_create_<provider>_embedding()` method
3. Add configuration variables to `config.py`
4. Update `.env.example` with new variables
5. Add tests for the new provider

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install LangChain packages
2. **API Key Issues**: Check environment variable configuration
3. **Model Not Found**: Verify model name spelling
4. **Network Issues**: Check internet connection for API-based models

### Debug Mode

Enable logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Create embedding model (will show detailed logs)
embedding = get_default_embedding_model()
```

## Support

For issues or questions:

1. Check the error message and logs
2. Verify configuration in `.env` file
3. Run validation script: `python validate_embeddings.py`
4. Review the integration examples
5. Check ChromaDB service compatibility

---

*This implementation provides a robust, configurable foundation for embedding models in the RAG chatbot application.*