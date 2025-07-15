# Backend

This directory contains the backend code for the RAG chatbot, built with Flask.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Create a `.env` file for environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://127.0.0.1:5000`

## API Endpoints

- `GET /` - Health check endpoint
- `GET /api/health` - API health check with environment info

## Configuration

The application uses environment variables for configuration:

- `FLASK_ENV` - Environment (development/production/testing)
- `FLASK_DEBUG` - Debug mode (True/False)
- `FLASK_HOST` - Host to bind to (default: 127.0.0.1)
- `FLASK_PORT` - Port to bind to (default: 5000)
- `SECRET_KEY` - Flask secret key
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins