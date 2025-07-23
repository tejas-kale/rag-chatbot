# RAG Chatbot Backend

A Flask-based backend service for a Retrieval-Augmented Generation (RAG) chatbot application with configurable embedding providers and vector database integration.

## 🚀 Features

- **Configurable Embedding Providers**: Support for HuggingFace and OpenAI embeddings
- **Vector Database Integration**: ChromaDB with persistent storage
- **Data Persistence**: SQLAlchemy with SQLite for chat history and user settings
- **Encryption Support**: Configurable encryption for sensitive data
- **RESTful API**: Clean Flask API with CORS support
- **Comprehensive Testing**: Unit tests with pytest and validation scripts
- **CI/CD Ready**: GitHub Actions workflow for automated testing

## 📁 Project Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # Flask app factory
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── models.py            # SQLAlchemy models
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── chromadb_service.py  # ChromaDB operations
│   │   ├── embedding_service.py # Embedding factory
│   │   └── persistence_service.py # Database operations
│   ├── config/                  # Configuration
│   │   ├── __init__.py
│   │   └── config.py           # Flask configuration
│   └── utils/                   # Utility functions
│       └── __init__.py
├── tests/                       # All tests
│   ├── __init__.py
│   ├── test_embeddings.py       # Embedding tests
│   ├── test_chromadb.py         # ChromaDB tests
│   ├── test_chromadb_basic.py   # Basic ChromaDB tests
│   └── test_encryption.py       # Encryption tests
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── init_db.py              # Database initialization
│   ├── generate_encryption_key.py # Key generation
│   ├── validate_embeddings.py  # Embedding validation
│   ├── verify_chromadb.py      # ChromaDB verification
│   └── chromadb_example.py     # Usage examples
├── docs/                        # Documentation
│   ├── CHROMADB_README.md
│   ├── EMBEDDING_README.md
│   ├── ENCRYPTION_README.md
│   └── COMPLETE_INTEGRATION_DEMO.md
├── .env.example                 # Environment template
├── README.md                    # This file
├── pyproject.toml              # Project configuration
├── uv.lock                     # Lock file
└── run.py                      # Application entry point
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///rag_chatbot.db

# ChromaDB Configuration
CHROMADB_PERSIST_PATH=./chroma_data

# Embedding Configuration
EMBEDDING_PROVIDER=huggingface        # or 'openai'
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_API_TOKEN=your_token_here # Optional
OPENAI_API_KEY=your_openai_key        # Required for OpenAI

# Encryption (Optional)
ENCRYPTION_KEY=your-encryption-key    # Generate with scripts/generate_encryption_key.py
```

### Supported Embedding Providers

#### HuggingFace (Default)
```bash
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Fast, good quality
# or
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # High quality
```

#### OpenAI
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small    # Recommended
OPENAI_API_KEY=your-api-key-here          # Required
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+ 
- pip or uv package manager

### Quick Start

1. **Clone and navigate to backend**
   ```bash
   git clone <repository-url>
   cd rag-chatbot/backend
   ```

2. **Install dependencies**
   ```bash
   # Using pip
   pip install flask python-dotenv flask-cors flask-sqlalchemy cryptography
   pip install chromadb langchain langchain-huggingface langchain-openai
   
   # Or using uv (recommended)
   uv sync
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5000`

## 🧪 Testing

### Run All Tests
```bash
# Run unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run validation scripts
python scripts/validate_embeddings.py
python scripts/verify_chromadb.py
```

### Run Specific Tests
```bash
# Test embeddings only
python -m pytest tests/test_embeddings.py -v

# Test ChromaDB only
python -m pytest tests/test_chromadb.py -v
```

## 📚 API Usage

### Basic Embedding Usage

```python
from app.services.embedding_service import create_embedding_function
from app.services.chromadb_service import chromadb_service

# Create embedding function
embedding_function = create_embedding_function()

# Create ChromaDB collection
collection = chromadb_service.get_or_create_collection(
    name="my_documents",
    embedding_function=embedding_function
)

# Add documents
success = chromadb_service.add_documents(
    collection_name="my_documents",
    documents=["Sample document text"],
    metadatas=[{"source": "file.txt"}]
)
```

### Flask App Usage

```python
from app.main import create_app

# Create app
app = create_app('development')

# Use in Flask context
with app.app_context():
    from app.services.embedding_service import get_default_embedding_model
    embedding_model = get_default_embedding_model()
```

## 🔧 Development

### Code Style
- **Black** for code formatting
- **isort** for import sorting  
- **Flake8** for linting
- **pytest** for testing

### Pre-commit Hooks
```bash
# Install development dependencies
pip install black isort flake8 pytest pytest-cov

# Format code
black app/ tests/ scripts/

# Sort imports
isort app/ tests/ scripts/

# Run linter
flake8 app/ tests/ scripts/
```

### Adding New Embedding Providers

1. Update `app/services/embedding_service.py`
2. Add provider to `SUPPORTED_PROVIDERS`
3. Implement `_create_provider_embedding()` method
4. Add configuration documentation
5. Add unit tests in `tests/test_embeddings.py`

## 📖 Documentation

- **[Embedding Configuration](docs/EMBEDDING_README.md)** - Detailed embedding setup
- **[ChromaDB Integration](docs/CHROMADB_README.md)** - Vector database usage
- **[Encryption Guide](docs/ENCRYPTION_README.md)** - Data encryption setup
- **[Integration Examples](docs/COMPLETE_INTEGRATION_DEMO.md)** - Complete usage examples

## 🚦 CI/CD

GitHub Actions workflow automatically:
- ✅ Runs tests on Python 3.9-3.12
- ✅ Performs code linting and formatting checks
- ✅ Validates embedding configuration
- ✅ Tests application startup
- ✅ Generates coverage reports

## 🛡️ Security

- Environment variables for sensitive configuration
- Optional encryption for stored data
- API key management for external services
- Input validation and error handling

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the backend directory
   cd backend
   python -c "from app.main import create_app; print('✅ Imports working')"
   ```

2. **Missing Dependencies**
   ```bash
   # Install missing packages
   pip install langchain langchain-huggingface langchain-openai
   ```

3. **Database Issues**
   ```bash
   # Reinitialize database
   python scripts/init_db.py
   ```

4. **Embedding Provider Issues**
   ```bash
   # Test embedding configuration
   python scripts/validate_embeddings.py
   ```

## 📄 License

This project is part of the RAG Chatbot application. See the main repository for license information.

## 🤝 Contributing

1. Follow the established project structure
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure CI/CD pipeline passes
5. Use conventional commit messages