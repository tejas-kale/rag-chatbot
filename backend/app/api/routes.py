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


def _determine_file_type(filename):
    """
    Determine the source type based on file extension.

    Args:
        filename: Name of the file to analyze

    Returns:
        str: Source type ('pdf', 'markdown')

    Raises:
        ValueError: If file type is unsupported
    """
    file_extension = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if file_extension == "pdf":
        return "pdf"
    elif file_extension == "md":
        return "markdown"
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


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
        source_type = _determine_file_type(original_filename)

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


def _process_data_source_async(task_id, source_type, source_value):
    """
    Process data source asynchronously in background thread.

    Args:
        task_id: Unique task identifier
        source_type: Type of data source (url, markdown, etc.)
        source_value: The actual data source (URL string, markdown content, etc.)
    """
    try:
        # Update task status to processing
        upload_tasks[task_id]["status"] = "processing"

        # Add metadata about the data source
        metadata = {
            "source_type": source_type,
            "task_id": task_id,
        }

        # Determine the actual processing type based on source_type and source_value
        processing_type = source_type
        processing_value = source_value

        # For URL type, detect if it's a YouTube URL
        if source_type == "url":
            if data_ingestion_service.youtube_downloader.is_youtube_url(source_value):
                processing_type = "youtube"
            # else: keep as "url" for general web article processing
        elif source_type == "markdown":
            # For markdown content via API, treat as text instead of file
            processing_type = "text"

        # Process the data source using data ingestion service
        success = data_ingestion_service.process_source(
            processing_value, processing_type, metadata
        )

        # Update task status based on result
        if success:
            upload_tasks[task_id]["status"] = "completed"
            upload_tasks[task_id]["message"] = "Data source processed successfully"
        else:
            upload_tasks[task_id]["status"] = "failed"
            upload_tasks[task_id]["message"] = "Failed to process data source"

    except Exception as e:
        upload_tasks[task_id]["status"] = "failed"
        upload_tasks[task_id]["message"] = f"Processing error: {str(e)}"


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


@api_bp.route("/api/data_source/add", methods=["POST"])
def add_data_source():
    """
    Add data source endpoint for URLs and Markdown content.

    Accepts JSON payload with data source information and processes it
    asynchronously for ingestion into the RAG system.

    Expected JSON format:
        {"type": "url", "value": "http://example.com"}
        {"type": "markdown", "value": "# Markdown content..."}

    Returns:
        JSON response with task_id and processing status
    """
    try:
        # Get JSON data from request
        try:
            data = request.get_json(force=True)
        except Exception as e:
            # Handle both malformed JSON and missing content-type
            if "Content-Type" in str(e):
                return jsonify({"error": "No JSON data provided"}), 400
            else:
                return jsonify({"error": "Invalid JSON format"}), 400

        # Validate request format
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        if "type" not in data or "value" not in data:
            return jsonify({"error": "Missing 'type' or 'value' field in request"}), 400

        source_type = data["type"]
        source_value = data["value"]

        # Validate source type
        allowed_types = {"url", "markdown"}
        if source_type not in allowed_types:
            allowed_types_str = ", ".join(allowed_types)
            error_msg = f"Invalid source type. Allowed types: {allowed_types_str}"
            return jsonify({"error": error_msg}), 400

        # Validate source value
        if (
            not source_value
            or not isinstance(source_value, str)
            or not source_value.strip()
        ):
            return jsonify({"error": "Source value must be a non-empty string"}), 400

        # Additional validation for URL type
        if source_type == "url":
            if not (
                source_value.startswith("http://")
                or source_value.startswith("https://")
            ):
                return (
                    jsonify({"error": "URL must start with http:// or https://"}),
                    400,
                )

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Initialize task tracking
        upload_tasks[task_id] = {
            "status": "queued",
            "source_type": source_type,
            "source_value": source_value,
            "task_id": task_id,
            "message": "Data source queued for processing",
        }

        # Start async processing in background thread
        processing_thread = threading.Thread(
            target=_process_data_source_async, args=(task_id, source_type, source_value)
        )
        processing_thread.daemon = True
        processing_thread.start()

        # Return immediate response with task ID
        return (
            jsonify(
                {
                    "task_id": task_id,
                    "status": "processing",
                    "message": "Data source added successfully, processing started",
                    "source_type": source_type,
                }
            ),
            202,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to add data source: {str(e)}"}), 500


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


@api_bp.route("/api/data_source/status/<task_id>", methods=["GET"])
def get_data_source_status(task_id):
    """
    Get the status of a data source processing task.

    Args:
        task_id: The unique task identifier

    Returns:
        JSON response with task status and details
    """
    if task_id not in upload_tasks:
        return jsonify({"error": "Task not found"}), 404

    task_info = upload_tasks[task_id]
    return jsonify(task_info)
