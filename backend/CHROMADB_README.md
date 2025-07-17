# ChromaDB Integration Documentation

This document describes the ChromaDB integration implemented for the RAG chatbot backend.

## Overview

ChromaDB has been integrated as a vector database with local persistence support. The integration provides:

- Local file system persistence for vector data
- Configurable storage path via environment variables
- Clean service interface for collection management
- Integration with the existing Flask application structure

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# ChromaDB Configuration
CHROMADB_PERSIST_PATH=db/chroma
```

The `CHROMADB_PERSIST_PATH` variable controls where ChromaDB stores its persistent data. 
Default: `db/chroma` (relative to the backend directory)

### Dependencies

ChromaDB has been added to `pyproject.toml`:

```toml
dependencies = [
    # ... other dependencies
    "chromadb>=0.4.15",
]
```

## Usage

### Basic Service Usage

```python
from chromadb_service import chromadb_service

# The service is automatically configured when imported
# in a Flask application context

# Create or get a collection
collection = chromadb_service.get_or_create_collection("my_documents")

# Add documents
success = chromadb_service.add_documents(
    collection_name="my_documents",
    documents=["This is a sample document about AI.", "Another document about ML."],
    metadatas=[{"topic": "AI"}, {"topic": "ML"}],
    ids=["doc1", "doc2"]
)

# Search documents
results = chromadb_service.query_documents(
    collection_name="my_documents",
    query_texts="artificial intelligence",
    n_results=5
)

# Get collection statistics
count = chromadb_service.get_collection_count("my_documents")
```

### Flask Integration

The service can be used in Flask routes:

```python
from flask import Flask, jsonify, request
from chromadb_service import chromadb_service

app = Flask(__name__)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    
    results = chromadb_service.query_documents(
        collection_name="documents",
        query_texts=query,
        n_results=10
    )
    
    return jsonify(results)
```

## API Reference

### ChromaDBService Methods

#### `get_or_create_collection(name, metadata=None, embedding_function=None)`
Creates a new collection or retrieves an existing one.

**Parameters:**
- `name` (str): Collection name
- `metadata` (dict, optional): Collection metadata
- `embedding_function` (optional): Custom embedding function

**Returns:** ChromaDB Collection instance

#### `add_documents(collection_name, documents, metadatas=None, ids=None, embeddings=None)`
Adds documents to a collection.

**Parameters:**
- `collection_name` (str): Target collection name
- `documents` (List[str]): List of document texts
- `metadatas` (List[dict], optional): Document metadata
- `ids` (List[str], optional): Document IDs (auto-generated if not provided)
- `embeddings` (List[List[float]], optional): Pre-computed embeddings

**Returns:** bool (success status)

#### `query_documents(collection_name, query_texts, n_results=10, where=None, where_document=None, include=None)`
Searches for similar documents in a collection.

**Parameters:**
- `collection_name` (str): Collection to search
- `query_texts` (str or List[str]): Search query/queries
- `n_results` (int): Number of results to return
- `where` (dict, optional): Metadata filter conditions
- `where_document` (dict, optional): Document content filter conditions
- `include` (List[str], optional): What to include in results

**Returns:** dict (query results) or None

#### `list_collections()`
Lists all collections in the ChromaDB instance.

**Returns:** List[str] (collection names)

#### `delete_collection(name)`
Deletes a collection by name.

**Parameters:**
- `name` (str): Collection name to delete

**Returns:** bool (success status)

#### `get_collection_count(collection_name)`
Gets the number of documents in a collection.

**Parameters:**
- `collection_name` (str): Collection name

**Returns:** int (document count, -1 if error)

## Data Persistence

ChromaDB data is persisted to the local file system in the directory specified by `CHROMADB_PERSIST_PATH`. 

**Important Notes:**
- The persistence directory is automatically created if it doesn't exist
- Data persists across application restarts
- The `db/` directory is excluded from version control via `.gitignore`
- For production deployments, consider using absolute paths for the persist directory

## Error Handling

The service includes comprehensive error handling:
- All methods return appropriate error indicators (None, False, -1)
- Errors are logged using Python's logging module
- Exceptions are caught and logged with detailed messages

## Example Integration

See `chromadb_example.py` for a complete example showing how to integrate ChromaDB with Flask routes, including:
- Collection management endpoints
- Document addition endpoints
- Search endpoints
- Status and health check endpoints

## Testing

Two test files are provided:
- `test_chromadb_basic.py`: Basic syntax and structure tests (doesn't require ChromaDB installation)
- `test_chromadb.py`: Comprehensive functionality tests (requires ChromaDB installation)

Run tests with:
```bash
python test_chromadb_basic.py  # Basic tests
python test_chromadb.py        # Full tests (requires ChromaDB)
```