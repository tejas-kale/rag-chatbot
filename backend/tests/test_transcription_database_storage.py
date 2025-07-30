"""
Tests for transcription database storage functionality.

Tests the integration between YouTube processing, transcription,
text correction, and database persistence.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.data_ingestion_service import DataIngestionService
from app.services.text_correction_service import TextCorrectionService
from app.models.models import Transcription


class TestTranscriptionDatabaseStorage:
    """Test class for transcription database storage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_chromadb_service = Mock()
        self.mock_embedding_factory = Mock()

        # Create a mock embedding model
        mock_embedding_model = Mock()
        mock_embedding_model.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        self.mock_embedding_factory.create_embedding_model.return_value = (
            mock_embedding_model
        )

        self.data_ingestion_service = DataIngestionService(
            chromadb_service=self.mock_chromadb_service,
            embedding_factory=self.mock_embedding_factory,
        )

    def test_text_correction_service_basic_functionality(self):
        """Test that text correction service performs basic corrections."""
        correction_service = TextCorrectionService()

        # Test basic text correction
        raw_text = "hello world this is a test"
        corrected_text = correction_service.correct_transcription(raw_text)

        # Should capitalize first letter and add period
        assert corrected_text.startswith("Hello")
        assert corrected_text.endswith(".")

    def test_text_correction_service_with_filler_words(self):
        """Test text correction removes common filler words."""
        correction_service = TextCorrectionService()

        raw_text = "well um this is er a test you know"
        corrected_text = correction_service.correct_transcription(raw_text)

        # Should remove filler words
        assert "um" not in corrected_text
        assert "er" not in corrected_text

    def test_text_correction_service_error_handling(self):
        """Test text correction service handles errors gracefully."""
        correction_service = TextCorrectionService()

        # Test with None input
        with pytest.raises(ValueError):
            correction_service.correct_transcription(None)

        # Test with empty string
        with pytest.raises(ValueError):
            correction_service.correct_transcription("")

    def test_correction_stats(self):
        """Test correction statistics calculation."""
        correction_service = TextCorrectionService()

        original = "hello world"
        corrected = "Hello world."

        stats = correction_service.get_correction_stats(original, corrected)

        assert "original_length" in stats
        assert "corrected_length" in stats
        assert "character_changes" in stats
        assert stats["original_length"] == len(original)
        assert stats["corrected_length"] == len(corrected)

    @patch("app.services.data_ingestion_service.time")
    def test_youtube_processing_with_database_storage(self, mock_time):
        """Test that YouTube processing creates and updates transcription records."""
        mock_time.time.side_effect = [1000.0, 1010.0]  # 10 second processing time

        youtube_url = "https://www.youtube.com/watch?v=test123"
        raw_transcription = "this is a test transcription"

        # Mock the persistence manager
        mock_transcription_record = Mock()
        mock_transcription_record.id = 123

        with patch.object(
            self.data_ingestion_service.persistence_manager, "create_transcription"
        ) as mock_create, patch.object(
            self.data_ingestion_service.persistence_manager, "update_transcription"
        ) as mock_update, patch.object(
            self.data_ingestion_service.youtube_downloader, "is_youtube_url"
        ) as mock_is_youtube, patch.object(
            self.data_ingestion_service.youtube_downloader, "download_audio"
        ) as mock_download, patch.object(
            self.data_ingestion_service.whisper_service, "transcribe_audio"
        ) as mock_transcribe, patch.object(
            self.data_ingestion_service.youtube_downloader, "cleanup_file"
        ) as mock_cleanup, patch(
            "os.stat"
        ) as mock_stat, patch(
            "os.path.basename"
        ) as mock_basename:

            # Set up mocks
            mock_create.return_value = mock_transcription_record
            mock_is_youtube.return_value = True
            mock_download.return_value = "/tmp/test_audio.mp3"
            mock_transcribe.return_value = raw_transcription
            mock_cleanup.return_value = True
            mock_stat.return_value = Mock(st_size=1024)
            mock_basename.return_value = "test_audio.mp3"

            # Execute the test
            result = self.data_ingestion_service._process_youtube(youtube_url)

            # Verify results
            assert result is True

            # Verify transcription record was created
            mock_create.assert_called_once_with(
                youtube_url=youtube_url, user_settings_id=1
            )

            # Verify transcription record was updated multiple times
            assert mock_update.call_count >= 2

            # Check the final update call contains the transcription data
            final_call = mock_update.call_args_list[-1]
            final_kwargs = final_call[1]

            assert final_kwargs["transcription_text"] == raw_transcription
            assert "corrected_text" in final_kwargs
            assert final_kwargs["status"] == "completed"
            assert final_kwargs["transcription_engine"] == "whisper"
            assert final_kwargs["processing_duration"] == 10.0

    def test_youtube_processing_transcription_failure(self):
        """Test YouTube processing handles transcription failure gracefully."""
        youtube_url = "https://www.youtube.com/watch?v=test123"

        # Mock the persistence manager
        mock_transcription_record = Mock()
        mock_transcription_record.id = 123

        with patch.object(
            self.data_ingestion_service.persistence_manager, "create_transcription"
        ) as mock_create, patch.object(
            self.data_ingestion_service.persistence_manager, "update_transcription"
        ) as mock_update, patch.object(
            self.data_ingestion_service.youtube_downloader, "is_youtube_url"
        ) as mock_is_youtube, patch.object(
            self.data_ingestion_service.youtube_downloader, "download_audio"
        ) as mock_download, patch.object(
            self.data_ingestion_service.whisper_service, "transcribe_audio"
        ) as mock_transcribe, patch.object(
            self.data_ingestion_service.youtube_downloader, "cleanup_file"
        ) as mock_cleanup, patch(
            "os.stat"
        ) as mock_stat, patch(
            "os.path.basename"
        ) as mock_basename:

            # Set up mocks - transcription fails
            mock_create.return_value = mock_transcription_record
            mock_is_youtube.return_value = True
            mock_download.return_value = "/tmp/test_audio.mp3"
            mock_transcribe.side_effect = Exception("Transcription failed")
            mock_cleanup.return_value = True
            mock_stat.return_value = Mock(st_size=1024)
            mock_basename.return_value = "test_audio.mp3"

            # Execute the test
            result = self.data_ingestion_service._process_youtube(youtube_url)

            # Should still succeed overall (fallback to URL)
            assert result is True

            # Verify error was recorded in database
            error_calls = [
                call
                for call in mock_update.call_args_list
                if "status" in call[1] and call[1]["status"] == "error"
            ]
            assert len(error_calls) > 0

            error_call_kwargs = error_calls[0][1]
            assert "error_message" in error_call_kwargs
            assert "Transcription failed" in error_call_kwargs["error_message"]

    def test_youtube_processing_download_failure(self):
        """Test YouTube processing handles download failure gracefully."""
        youtube_url = "https://www.youtube.com/watch?v=test123"

        # Mock the persistence manager
        mock_transcription_record = Mock()
        mock_transcription_record.id = 123

        with patch.object(
            self.data_ingestion_service.persistence_manager, "create_transcription"
        ) as mock_create, patch.object(
            self.data_ingestion_service.persistence_manager, "update_transcription"
        ) as mock_update, patch.object(
            self.data_ingestion_service.youtube_downloader, "is_youtube_url"
        ) as mock_is_youtube, patch.object(
            self.data_ingestion_service.youtube_downloader, "download_audio"
        ) as mock_download:

            # Set up mocks - download fails
            mock_create.return_value = mock_transcription_record
            mock_is_youtube.return_value = True
            mock_download.return_value = None  # Download failure

            # Execute the test
            result = self.data_ingestion_service._process_youtube(youtube_url)

            # Should fail
            assert result is False

            # Verify transcription record was created
            mock_create.assert_called_once()

            # Verify error was recorded in database
            mock_update.assert_called_once_with(
                mock_transcription_record.id,
                status="error",
                error_message="Failed to download audio from YouTube",
            )

    def test_youtube_processing_database_creation_failure(self):
        """Test YouTube processing handles database creation failure gracefully."""
        youtube_url = "https://www.youtube.com/watch?v=test123"

        with patch.object(
            self.data_ingestion_service.persistence_manager, "create_transcription"
        ) as mock_create, patch.object(
            self.data_ingestion_service.youtube_downloader, "is_youtube_url"
        ) as mock_is_youtube:

            # Set up mocks - database creation fails
            mock_create.return_value = None  # Creation failure
            mock_is_youtube.return_value = True

            # Execute the test
            result = self.data_ingestion_service._process_youtube(youtube_url)

            # Should fail
            assert result is False

            # Verify transcription record creation was attempted
            mock_create.assert_called_once()

    def test_transcription_model_has_corrected_text_field(self):
        """Test that Transcription model has the new corrected_text field."""
        # This test verifies the model structure
        transcription = Transcription()

        # Check that the corrected_text attribute exists
        assert hasattr(transcription, "corrected_text")

        # Check that we can set the corrected_text field
        transcription.corrected_text = "This is corrected text."
        assert transcription.corrected_text == "This is corrected text."
