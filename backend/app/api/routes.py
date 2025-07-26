"""
API routes for the RAG chatbot application.
Contains all route definitions organized as Flask blueprints.
"""

import json
import os
import tempfile
import threading
import uuid
from werkzeug.utils import secure_filename

from flask import Blueprint, jsonify, request

from app.services.persistence_service import PersistenceManager
from app.services.chromadb_service import ChromaDBService
from app.services.embedding_service import EmbeddingFactory
from app.services.data_ingestion_service import DataIngestionService

# Create blueprint for API routes
api_bp = Blueprint("api", __name__)

# Initialize persistence manager
persistence_manager = PersistenceManager()

# Initialize services
chromadb_service = ChromaDBService()
embedding_factory = EmbeddingFactory()
data_ingestion_service = DataIngestionService(chromadb_service, embedding_factory)

# Track upload tasks - in production, use Redis or database
upload_tasks = {}


def _sanitize_settings_response(user_settings):
    """
    Sanitize user settings for API response by removing sensitive data.

    Args:
        user_settings: UserSettings object

    Returns:
        dict: Sanitized settings dictionary
    """
    if not user_settings:
        return {
            "user_id": "default_user",
            "api_keys": {},
            "custom_prompts": None,
            "created_at": None,
            "updated_at": None,
        }

    # Get API keys to check what keys exist (but don't expose values)
    api_keys_data = persistence_manager.get_api_keys(user_settings.user_id)
    api_keys_status = {}

    if api_keys_data:
        # Only indicate which API keys are configured, not their values
        for key in api_keys_data.keys():
            api_keys_status[key] = "configured"

    return {
        "user_id": user_settings.user_id,
        "api_keys": api_keys_status,
        "custom_prompts": user_settings.custom_prompts,
        "created_at": (
            user_settings.created_at.isoformat() if user_settings.created_at else None
        ),
        "updated_at": (
            user_settings.updated_at.isoformat() if user_settings.updated_at else None
        ),
    }


@api_bp.route("/")
def health_check():
    """Basic health check endpoint."""
    return jsonify(
        {
            "message": "RAG Chatbot API is running",
            "status": "healthy",
            "version": "1.0.0",
        }
    )


@api_bp.route("/api/health")
def api_health():
    """API health check endpoint."""
    return jsonify({"status": "ok"})


@api_bp.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint for processing user messages."""
    try:
        # Get JSON data from request
        data = request.get_json()

        # Validate that message field exists
        if not data or "message" not in data:
            return jsonify({"error": "Message field is required"}), 400

        # For now, return a placeholder response
        return jsonify({"response": "I am a bot."})

    except Exception as e:
        return jsonify({"error": f"Invalid request: {e}"}), 400


@api_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current user settings."""
    try:
        # For now, use default_user as user_id
        user_id = "default_user"

        # Get user settings from database
        user_settings = persistence_manager.get_user_settings_by_user_id(user_id)

        # Sanitize response to remove sensitive data
        settings_data = _sanitize_settings_response(user_settings)

        return jsonify(settings_data)

    except Exception as e:
        return (
            jsonify({"error": f"Failed to retrieve settings: {str(e)}"}),
            400,
        )


@api_bp.route("/api/settings", methods=["POST"])
def update_settings():
    """Update user settings."""
    try:
        # Get JSON data from request
        data = request.get_json()

        if not data or len(data) == 0:
            return jsonify({"error": "Request body is required"}), 400

        # For now, use default_user as user_id
        user_id = "default_user"

        # Get existing user settings or create new ones
        user_settings = persistence_manager.get_user_settings_by_user_id(user_id)

        # Extract API keys and custom prompts from request
        api_keys = data.get("api_keys")
        custom_prompts = data.get("custom_prompts")

        # Validate custom_prompts is a valid JSON string if provided
        if custom_prompts is not None:
            try:
                json.loads(custom_prompts)
            except (json.JSONDecodeError, TypeError):
                return (
                    jsonify({"error": "custom_prompts must be a valid JSON string"}),
                    400,
                )

        if user_settings:
            # Update existing settings
            update_data = {}

            if api_keys is not None:
                # Merge existing API keys with new ones
                existing_api_keys = persistence_manager.get_api_keys(user_id) or {}
                merged_api_keys = existing_api_keys.copy()
                merged_api_keys.update(api_keys)
                update_data["api_keys"] = merged_api_keys

            if custom_prompts is not None:
                update_data["custom_prompts"] = custom_prompts

            if update_data:
                updated_settings = persistence_manager.update_user_settings(
                    user_settings.id, **update_data
                )
                if not updated_settings:
                    return (
                        jsonify({"error": "Failed to update settings"}),
                        500,
                    )
            else:
                updated_settings = user_settings
        else:
            # Create new user settings
            updated_settings = persistence_manager.create_user_settings(
                user_id=user_id,
                api_keys=api_keys,
                custom_prompts=custom_prompts,
            )
            if not updated_settings:
                return jsonify({"error": "Failed to create settings"}), 500

        # Return sanitized response
        settings_data = _sanitize_settings_response(updated_settings)
        return jsonify(settings_data)

    except Exception as e:
        return (
            jsonify({"error": f"Failed to update settings: {str(e)}"}),
            400,
        )


@api_bp.route("/api/history", methods=["GET"])
def get_history():
    """Get chat conversation history."""
    try:
        # Get all chat history ordered by timestamp
        chat_history = persistence_manager.get_recent_chat_history(limit=1000)

        # Convert to JSON serializable format
        history_data = []
        for chat in chat_history:
            history_data.append(
                {
                    "id": chat.id,
                    "session_id": chat.session_id,
                    "user_message": chat.user_message,
                    "bot_response": chat.bot_response,
                    "timestamp": (
                        chat.timestamp.isoformat() if chat.timestamp else None
                    ),
                    "context_sources": chat.context_sources,
                }
            )

        # Reverse to get chronological order (oldest first)
        history_data.reverse()

        return jsonify(history_data)

    except Exception as e:
        return (
            jsonify({"error": f"Failed to retrieve chat history: {str(e)}"}),
            500,
        )


@api_bp.route("/api/ingest", methods=["POST"])
def ingest_data():
    """Endpoint for ingesting data into the RAG system."""
    try:
        data = request.get_json()
        if not data or "source_type" not in data or "data" not in data:
            return (
                jsonify({"error": "Missing source_type or data in request"}),
                400,
            )

        source_type = data["source_type"]
        source_data = data["data"]
        metadata = data.get("metadata", {})

        success = data_ingestion_service.process_source(
            source_data, source_type, metadata
        )

        if success:
            return jsonify({"message": "Data ingested successfully"}), 200
        else:
            return jsonify({"error": "Failed to ingest data"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def _is_allowed_file(filename, allowed_extensions=None):
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename: Name of the uploaded file
        allowed_extensions: Set of allowed extensions (default: {'pdf', 'md'})

    Returns:
        bool: True if file extension is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = {"pdf", "md"}

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def _process_upload_async(task_id, file_path, original_filename):
    """
    Process uploaded file asynchronously in background thread.

    Args:
        task_id: Unique task identifier
        file_path: Path to the temporary uploaded file
        original_filename: Original name of uploaded file
    """
    try:
        # Update task status to processing
        upload_tasks[task_id]["status"] = "processing"

        # Add metadata about the uploaded file
        metadata = {
            "source_type": "upload",
            "original_filename": original_filename,
            "task_id": task_id,
        }

        # Determine file type based on extension
        file_extension = (
            original_filename.rsplit(".", 1)[1].lower()
            if "." in original_filename
            else ""
        )
        if file_extension == "pdf":
            source_type = "pdf"
        elif file_extension == "md":
            source_type = "markdown"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Process the file using data ingestion service
        success = data_ingestion_service.process_source(
            file_path, source_type, metadata
        )

        # Update task status based on result
        if success:
            upload_tasks[task_id]["status"] = "completed"
            upload_tasks[task_id]["message"] = "File processed successfully"
        else:
            upload_tasks[task_id]["status"] = "failed"
            upload_tasks[task_id]["message"] = "Failed to process file"

    except Exception as e:
        upload_tasks[task_id]["status"] = "failed"
        upload_tasks[task_id]["message"] = f"Processing error: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {file_path}: {e}")


@api_bp.route("/api/data_source/upload", methods=["POST"])
def upload_file():
    """
    Upload endpoint for PDF and Markdown files.

    Accepts multipart/form-data with a PDF or Markdown file and processes it
    asynchronously for ingestion into the RAG system.

    Returns:
        JSON response with task_id and processing status
    """
    try:
        # Check if file is present in request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        # Check if file was actually selected
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Validate file type
        if not _is_allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "error": (
                            "Invalid file type. Only PDF and Markdown files are allowed"
                        )
                    }
                ),
                400,
            )

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"upload_{task_id}.pdf"

        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{task_id}_{filename}")

        # Save uploaded file to temporary location
        file.save(temp_file_path)

        # Initialize task tracking
        upload_tasks[task_id] = {
            "status": "queued",
            "filename": filename,
            "task_id": task_id,
            "message": "File uploaded, processing queued",
        }

        # Start async processing in background thread
        processing_thread = threading.Thread(
            target=_process_upload_async, args=(task_id, temp_file_path, filename)
        )
        processing_thread.daemon = True
        processing_thread.start()

        # Return immediate response with task ID
        return (
            jsonify(
                {
                    "task_id": task_id,
                    "status": "processing",
                    "message": "File uploaded successfully, processing started",
                    "filename": filename,
                }
            ),
            202,
        )

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@api_bp.route("/api/data_source/upload/status/<task_id>", methods=["GET"])
def get_upload_status(task_id):
    """
    Get the status of an upload task.

    Args:
        task_id: The unique task identifier

    Returns:
        JSON response with task status and details
    """
    if task_id not in upload_tasks:
        return jsonify({"error": "Task not found"}), 404

    task_info = upload_tasks[task_id]
    return jsonify(task_info)
