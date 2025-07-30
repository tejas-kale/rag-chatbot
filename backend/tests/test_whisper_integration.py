"""
Integration test for whisper transcription with data ingestion service.
"""

import shutil
import tempfile
import unittest.mock
from pathlib import Path

from app.services.chromadb_service import ChromaDBService
from app.services.data_ingestion_service import DataIngestionService
from app.services.embedding_service import EmbeddingFactory


class TestWhisperDataIngestionIntegration:
    """Integration tests for whisper transcription with data ingestion."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Mock services
        self.mock_chromadb = unittest.mock.MagicMock(spec=ChromaDBService)
        self.mock_embedding_factory = unittest.mock.MagicMock(spec=EmbeddingFactory)

        # Set up mock embedding model
        mock_embedding_model = unittest.mock.MagicMock()
        mock_embedding_model.embed_documents.return_value = [
            [0.1, 0.2, 0.3],  # Mock embedding
        ]
        self.mock_embedding_factory.create_embedding_model.return_value = (
            mock_embedding_model
        )

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.mock.patch("app.services.data_ingestion_service.YouTubeDownloaderService")
    @unittest.mock.patch(
        "app.services.data_ingestion_service.WhisperTranscriptionService"
    )
    def test_youtube_processing_with_transcription_success(
        self, mock_whisper_service_class, mock_youtube_service_class
    ):
        """Test successful YouTube processing with whisper transcription."""
        # Setup mocks
        mock_youtube_service = unittest.mock.MagicMock()
        mock_whisper_service = unittest.mock.MagicMock()

        mock_youtube_service_class.return_value = mock_youtube_service
        mock_whisper_service_class.return_value = mock_whisper_service

        # Configure YouTube downloader mock
        mock_youtube_service.is_youtube_url.return_value = True
        mock_youtube_service.download_audio.return_value = str(
            Path(self.temp_dir) / "test_audio.mp3"
        )
        mock_youtube_service.cleanup_file.return_value = True

        # Configure whisper transcription mock
        mock_whisper_service.transcribe_audio.return_value = (
            "This is a test transcription of the YouTube video content."
        )

        # Create data ingestion service
        service = DataIngestionService(
            chromadb_service=self.mock_chromadb,
            embedding_factory=self.mock_embedding_factory,
            youtube_download_dir=self.temp_dir,
        )

        # Test YouTube processing
        result = service.process_source(
            "https://youtube.com/watch?v=test123",
            "youtube",
            {"test_metadata": "value"},
        )

        # Verify the process succeeded
        assert result is True

        # Verify YouTube downloader was called correctly
        mock_youtube_service.is_youtube_url.assert_called_once_with(
            "https://youtube.com/watch?v=test123"
        )
        mock_youtube_service.download_audio.assert_called_once_with(
            "https://youtube.com/watch?v=test123"
        )

        # Verify whisper transcription was called
        mock_whisper_service.transcribe_audio.assert_called_once()

        # Verify ChromaDB storage was called with transcribed content
        self.mock_chromadb.add_documents.assert_called_once()
        call_args = self.mock_chromadb.add_documents.call_args

        # Check that the transcribed text was included in the documents
        documents = call_args.kwargs["documents"]
        assert len(documents) > 0
        assert "This is a test transcription" in documents[0]
        # URL should not be in document content, only in metadata

        # Check metadata includes transcription info
        metadatas = call_args.kwargs["metadatas"]
        assert len(metadatas) > 0
        assert metadatas[0]["source_type"] == "youtube"
        assert metadatas[0]["transcription_available"] is True

        # Verify cleanup was called
        mock_youtube_service.cleanup_file.assert_called_once()

    @unittest.mock.patch("app.services.data_ingestion_service.YouTubeDownloaderService")
    @unittest.mock.patch(
        "app.services.data_ingestion_service.WhisperTranscriptionService"
    )
    def test_youtube_processing_with_transcription_failure(
        self, mock_whisper_service_class, mock_youtube_service_class
    ):
        """Test YouTube processing when whisper transcription fails."""
        # Setup mocks
        mock_youtube_service = unittest.mock.MagicMock()
        mock_whisper_service = unittest.mock.MagicMock()

        mock_youtube_service_class.return_value = mock_youtube_service
        mock_whisper_service_class.return_value = mock_whisper_service

        # Configure YouTube downloader mock
        mock_youtube_service.is_youtube_url.return_value = True
        mock_youtube_service.download_audio.return_value = str(
            Path(self.temp_dir) / "test_audio.mp3"
        )
        mock_youtube_service.cleanup_file.return_value = True

        # Configure whisper transcription to fail
        mock_whisper_service.transcribe_audio.side_effect = RuntimeError(
            "Whisper transcription failed"
        )

        # Create data ingestion service
        service = DataIngestionService(
            chromadb_service=self.mock_chromadb,
            embedding_factory=self.mock_embedding_factory,
            youtube_download_dir=self.temp_dir,
        )

        # Test YouTube processing (should still succeed with fallback)
        result = service.process_source(
            "https://youtube.com/watch?v=test123",
            "youtube",
            {"test_metadata": "value"},
        )

        # Verify the process succeeded despite transcription failure
        assert result is True

        # Verify whisper transcription was attempted
        mock_whisper_service.transcribe_audio.assert_called_once()

        # Verify ChromaDB storage was called with fallback content
        self.mock_chromadb.add_documents.assert_called_once()
        call_args = self.mock_chromadb.add_documents.call_args

        # Check that fallback content was used (URL only)
        documents = call_args.kwargs["documents"]
        assert len(documents) > 0
        assert "YouTube video: https://youtube.com/watch?v=test123" in documents[0]

        # Check metadata indicates no transcription available
        metadatas = call_args.kwargs["metadatas"]
        assert len(metadatas) > 0
        assert metadatas[0]["source_type"] == "youtube"
        assert metadatas[0]["transcription_available"] is False

    @unittest.mock.patch("app.services.data_ingestion_service.YouTubeDownloaderService")
    @unittest.mock.patch(
        "app.services.data_ingestion_service.WhisperTranscriptionService"
    )
    def test_data_ingestion_service_initialization_with_whisper_params(
        self, mock_whisper_service_class, mock_youtube_service_class
    ):
        """Test DataIngestionService initializes WhisperTranscriptionService."""
        # Create data ingestion service with custom whisper parameters
        service = DataIngestionService(
            chromadb_service=self.mock_chromadb,
            embedding_factory=self.mock_embedding_factory,
            whisper_executable="/custom/path/whisper",
            whisper_model="large-v3",
        )

        # Verify WhisperTranscriptionService was initialized with correct parameters
        mock_whisper_service_class.assert_called_once_with(
            whisper_executable="/custom/path/whisper",
            default_model="large-v3",
        )

        # Verify the service has the whisper service
        assert hasattr(service, "whisper_service")
        assert service.whisper_service is not None
