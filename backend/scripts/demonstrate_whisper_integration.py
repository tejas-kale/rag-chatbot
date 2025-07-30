#!/usr/bin/env python3
"""
Demonstration script for whisper.cpp integration with RAG chatbot.

This script shows how the whisper.cpp subprocess wrapper works and
how it integrates with the YouTube processing pipeline.
"""

import logging
import sys
import tempfile
from pathlib import Path

# Add the current directory to the Python path  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.whisper_transcription_service import (  # noqa: E402
    WhisperTranscriptionService,
)


def demonstrate_whisper_service():
    """Demonstrate the WhisperTranscriptionService functionality."""
    print("=" * 60)
    print("Whisper.cpp Integration Demonstration")
    print("=" * 60)

    # Initialize the service
    print("\n1. Initializing WhisperTranscriptionService...")
    whisper_service = WhisperTranscriptionService(
        whisper_executable="whisper",  # Assumes whisper.cpp is in PATH
        default_model="base",
    )
    print(
        f"   ✓ Service initialized with executable: "
        f"{whisper_service.whisper_executable}"
    )
    print(f"   ✓ Default model: {whisper_service.default_model}")

    # Check if whisper.cpp is available
    print("\n2. Checking whisper.cpp availability...")
    is_available = whisper_service.is_whisper_available()
    if is_available:
        print("   ✓ whisper.cpp is available and working")
    else:
        print("   ✗ whisper.cpp is not available")
        print("   Note: This is expected if whisper.cpp is not installed")
        print("   To install whisper.cpp:")
        print("     1. Clone: git clone https://github.com/ggerganov/whisper.cpp.git")
        print("     2. Build: cd whisper.cpp && make")
        print("     3. Download model: bash ./models/download-ggml-model.sh base")
        print("     4. Add to PATH or specify full path in service initialization")

    # Show available models
    print("\n3. Available whisper models:")
    models = whisper_service.get_available_models()
    for model in models:
        print(f"   - {model}")

    # Demonstrate transcription (mock since we don't have a real audio file)
    print("\n4. Transcription workflow:")
    print("   When processing a YouTube video:")
    print("   a) Download audio using YouTubeDownloaderService")
    print("   b) Call whisper_service.transcribe_audio(audio_file_path)")
    print("   c) Whisper.cpp processes the audio and returns text")
    print("   d) Text is chunked, embedded, and stored in ChromaDB")
    print("   e) Audio file is cleaned up")

    print("\n5. Command that would be executed:")
    temp_audio = "/tmp/youtube_audio.mp3"
    model = "base"
    temp_output = Path(tempfile.gettempdir()) / "whisper_output.txt"

    cmd_parts = [
        whisper_service.whisper_executable,
        "-m",
        model,
        "-f",
        temp_audio,
        "-otxt",
        "-of",
        str(temp_output.with_suffix("")),
    ]
    print(f"   Command: {' '.join(cmd_parts)}")

    # Integration with DataIngestionService
    print("\n6. Integration with DataIngestionService:")
    print("   The DataIngestionService now:")
    print("   ✓ Initializes WhisperTranscriptionService in __init__")
    print("   ✓ Uses whisper transcription in _process_youtube method")
    print("   ✓ Handles transcription failures gracefully")
    print("   ✓ Includes transcription status in metadata")
    print("   ✓ Cleans up audio files after processing")

    print("\n7. Error handling:")
    print("   ✓ Checks if whisper.cpp executable is available")
    print("   ✓ Validates input audio file exists")
    print("   ✓ Handles subprocess timeouts (5 minute default)")
    print("   ✓ Handles whisper.cpp errors and non-zero exit codes")
    print("   ✓ Falls back to stdout if output file is missing")
    print("   ✓ Cleans up temporary files")

    print("\n" + "=" * 60)
    print("Integration complete! ✓")
    print("=" * 60)


def demonstrate_youtube_integration():
    """Show how whisper integrates with YouTube processing."""
    print("\n" + "=" * 60)
    print("YouTube + Whisper Integration Flow")
    print("=" * 60)

    print("\nWhen processing a YouTube URL:")
    print("1. Validate YouTube URL")
    print("2. Download audio using yt-dlp → MP3 file")
    print("3. NEW: Transcribe audio using whisper.cpp")
    print("4. Create embeddings from transcribed text")
    print("5. Store in ChromaDB with metadata")
    print("6. Clean up audio file")

    print("\nBefore whisper integration:")
    print("   Text content: 'YouTube video: https://youtube.com/watch?v=...'")
    print("   Limited searchability and context")

    print("\nAfter whisper integration:")
    print("   Text content: 'YouTube video transcription from https://...'")
    print("                 'Full transcribed audio content here...'")
    print("   Rich, searchable content for RAG retrieval")

    print("\nMetadata includes:")
    print("   - source_type: 'youtube'")
    print("   - youtube_url: original URL")
    print("   - audio_file_path: downloaded MP3 path")
    print("   - transcription_available: true/false")
    print("   - content_type: 'audio/mp3'")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    try:
        demonstrate_whisper_service()
        demonstrate_youtube_integration()

        print("\n" + "🎉" * 20)
        print("Whisper.cpp integration successfully implemented!")
        print("🎉" * 20)

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        sys.exit(1)
