"""
Test module for Whisper transcription service.
"""

import shutil
import subprocess
import tempfile
import unittest.mock
from pathlib import Path

import pytest

from app.services.whisper_transcription_service import WhisperTranscriptionService


class TestWhisperTranscriptionService:
    """Test cases for WhisperTranscriptionService."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = WhisperTranscriptionService(
            whisper_executable="whisper",
            default_model="base",
            temp_dir=self.temp_dir,
        )

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_sets_properties(self):
        """Test that initialization sets the correct properties."""
        assert self.service.whisper_executable == "whisper"
        assert self.service.default_model == "base"
        assert self.service.temp_dir == Path(self.temp_dir)

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        service = WhisperTranscriptionService()
        assert service.whisper_executable == "whisper"
        assert service.default_model == "base"
        assert service.temp_dir == Path(tempfile.gettempdir())

    @unittest.mock.patch("subprocess.run")
    def test_is_whisper_available_success(self, mock_run):
        """Test whisper availability check when executable is available."""
        mock_run.return_value.returncode = 0

        assert self.service.is_whisper_available() is True
        mock_run.assert_called_once_with(
            ["whisper", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

    @unittest.mock.patch("subprocess.run")
    def test_is_whisper_available_not_found(self, mock_run):
        """Test whisper availability check when executable is not found."""
        mock_run.side_effect = FileNotFoundError()

        assert self.service.is_whisper_available() is False

    @unittest.mock.patch("subprocess.run")
    def test_is_whisper_available_fails(self, mock_run):
        """Test whisper availability check when executable fails."""
        mock_run.return_value.returncode = 1

        assert self.service.is_whisper_available() is False

    @unittest.mock.patch("subprocess.run")
    def test_is_whisper_available_timeout(self, mock_run):
        """Test whisper availability check when command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("whisper", 10)

        assert self.service.is_whisper_available() is False

    def test_transcribe_audio_file_not_found(self):
        """Test transcription with non-existent audio file."""
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            self.service.transcribe_audio("nonexistent_file.mp3")

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=False
    )
    def test_transcribe_audio_whisper_not_available(self, mock_available):
        """Test transcription when whisper.cpp is not available."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        with pytest.raises(RuntimeError, match="whisper.cpp executable not found"):
            self.service.transcribe_audio(str(temp_audio))

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_success(self, mock_run, mock_available):
        """Test successful audio transcription."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock successful subprocess execution
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = ""

        # Create a real temporary output file for testing
        temp_output_path = Path(self.temp_dir) / "temp_output.txt"

        # Mock tempfile.NamedTemporaryFile to return our controlled file
        with unittest.mock.patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            # Create a context manager that returns a file-like object with our path
            mock_file = unittest.mock.MagicMock()
            mock_file.name = str(temp_output_path)
            mock_tempfile.return_value.__enter__.return_value = mock_file

            # Create the actual output file with transcription content
            temp_output_path.write_text("This is a test transcription.")

            result = self.service.transcribe_audio(str(temp_audio))

            assert result == "This is a test transcription."
            mock_run.assert_called_once()

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_with_custom_model(self, mock_run, mock_available):
        """Test transcription with custom model."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock successful subprocess execution
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = ""

        temp_output_path = Path(self.temp_dir) / "temp_output.txt"

        # Mock tempfile.NamedTemporaryFile to return our controlled file
        with unittest.mock.patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            # Create a context manager that returns a file-like object with our path
            mock_file = unittest.mock.MagicMock()
            mock_file.name = str(temp_output_path)
            mock_tempfile.return_value.__enter__.return_value = mock_file

            # Create the actual output file with transcription
            temp_output_path.write_text("Custom model transcription.")

            result = self.service.transcribe_audio(str(temp_audio), model="large")

            assert result == "Custom model transcription."
            # Verify the model parameter was passed correctly
            call_args = mock_run.call_args[0][0]  # Get the command list
            assert "-m" in call_args
            model_index = call_args.index("-m")
            assert call_args[model_index + 1] == "large"

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_subprocess_failure(self, mock_run, mock_available):
        """Test transcription when subprocess fails."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock failed subprocess execution
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "whisper.cpp error: invalid file"

        with pytest.raises(RuntimeError, match="whisper.cpp transcription failed"):
            self.service.transcribe_audio(str(temp_audio))

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_timeout(self, mock_run, mock_available):
        """Test transcription when subprocess times out."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock subprocess timeout
        mock_run.side_effect = subprocess.TimeoutExpired("whisper", 300)

        with pytest.raises(RuntimeError, match="whisper.cpp transcription timed out"):
            self.service.transcribe_audio(str(temp_audio))

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_no_output_file_with_stdout(
        self, mock_run, mock_available
    ):
        """Test transcription when no output file is created but stdout has content."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock successful subprocess execution with stdout content
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = "Transcription from stdout"

        with unittest.mock.patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp_file = unittest.mock.MagicMock()
            mock_temp_file.name = str(Path(self.temp_dir) / "temp_output.txt")
            mock_temp.__enter__.return_value = mock_temp_file

            # Don't create the output file to simulate missing file scenario

            result = self.service.transcribe_audio(str(temp_audio))

            assert result == "Transcription from stdout"

    @unittest.mock.patch.object(
        WhisperTranscriptionService, "is_whisper_available", return_value=True
    )
    @unittest.mock.patch("subprocess.run")
    def test_transcribe_audio_no_output(self, mock_run, mock_available):
        """Test transcription when no output is produced."""
        # Create a temporary audio file
        temp_audio = Path(self.temp_dir) / "test.mp3"
        temp_audio.touch()

        # Mock successful subprocess execution but no output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = ""

        with unittest.mock.patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp_file = unittest.mock.MagicMock()
            mock_temp_file.name = str(Path(self.temp_dir) / "temp_output.txt")
            mock_temp.__enter__.return_value = mock_temp_file

            # Don't create the output file

            result = self.service.transcribe_audio(str(temp_audio))

            assert result is None

    def test_get_available_models(self):
        """Test getting list of available models."""
        models = self.service.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "base" in models
        assert "large-v3" in models
        assert "tiny" in models

    def test_cleanup_temp_file(self):
        """Test temporary file cleanup."""
        # Create a temporary file
        temp_file = Path(self.temp_dir) / "test_cleanup.txt"
        temp_file.write_text("test content")
        assert temp_file.exists()

        # Test cleanup
        self.service._cleanup_temp_file(temp_file)
        assert not temp_file.exists()

    def test_cleanup_temp_file_not_exists(self):
        """Test cleanup of non-existent file doesn't raise error."""
        temp_file = Path(self.temp_dir) / "nonexistent.txt"

        # Should not raise an exception
        self.service._cleanup_temp_file(temp_file)
