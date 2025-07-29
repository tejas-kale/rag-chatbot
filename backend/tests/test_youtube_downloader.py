"""
Test module for YouTube downloader service.
"""

import tempfile
import unittest.mock
from pathlib import Path

import pytest

from app.services.youtube_downloader_service import YouTubeDownloaderService


class TestYouTubeDownloaderService:
    """Test cases for YouTubeDownloaderService."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = YouTubeDownloaderService(download_directory=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_download_directory(self):
        """Test that initialization creates the download directory."""
        assert self.service.download_directory.exists()
        assert self.service.download_directory.is_dir()

    def test_is_youtube_url_valid_urls(self):
        """Test YouTube URL validation with valid URLs."""
        valid_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

        for url in valid_urls:
            assert self.service.is_youtube_url(url), f"URL should be valid: {url}"

    def test_is_youtube_url_invalid_urls(self):
        """Test YouTube URL validation with invalid URLs."""
        invalid_urls = [
            "https://example.com",
            "https://vimeo.com/123456",
            "not-a-url",
            "",
            "https://youtubee.com/watch?v=123",
        ]

        for url in invalid_urls:
            assert not self.service.is_youtube_url(url), f"URL should be invalid: {url}"

    def test_download_audio_invalid_url_raises_error(self):
        """Test that download_audio raises ValueError for invalid URLs."""
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            self.service.download_audio("https://example.com")

    @unittest.mock.patch("subprocess.run")
    def test_download_audio_subprocess_success(self, mock_run):
        """Test successful audio download via subprocess."""
        # Setup mock
        mock_run.return_value.stdout = "[download] Destination: test_audio.mp3"
        mock_run.return_value.returncode = 0

        # Create a mock downloaded file
        test_file = self.service.download_directory / "test_audio.mp3"
        test_file.touch()

        # Test
        result = self.service.download_audio("https://youtube.com/watch?v=test")

        # Verify subprocess was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "yt-dlp" in call_args
        assert "--extract-audio" in call_args
        assert "--audio-format" in call_args
        assert "mp3" in call_args
        assert "https://youtube.com/watch?v=test" in call_args

        # Verify result
        assert result == str(test_file)

    @unittest.mock.patch("subprocess.run")
    def test_download_audio_subprocess_timeout(self, mock_run):
        """Test subprocess timeout handling."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("yt-dlp", 300)

        with pytest.raises(RuntimeError, match="Download timed out"):
            self.service.download_audio("https://youtube.com/watch?v=test")

    @unittest.mock.patch("subprocess.run")
    def test_download_audio_subprocess_error(self, mock_run):
        """Test subprocess error handling."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(
            1, "yt-dlp", stderr="Error downloading video"
        )

        with pytest.raises(RuntimeError, match="yt-dlp failed"):
            self.service.download_audio("https://youtube.com/watch?v=test")

    @unittest.mock.patch("subprocess.run")
    def test_download_audio_file_not_found_error(self, mock_run):
        """Test handling when yt-dlp is not installed."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(RuntimeError, match="yt-dlp not found"):
            self.service.download_audio("https://youtube.com/watch?v=test")

    @unittest.mock.patch("subprocess.run")
    def test_download_audio_no_file_created(self, mock_run):
        """Test handling when subprocess succeeds but no file is created."""
        mock_run.return_value.stdout = "[download] Some output without file info"
        mock_run.return_value.returncode = 0

        result = self.service.download_audio("https://youtube.com/watch?v=test")
        assert result is None

    def test_find_downloaded_file_with_destination_output(self):
        """Test finding downloaded file from yt-dlp output with Destination."""
        # Create test file
        test_file = self.service.download_directory / "test_audio.mp3"
        test_file.touch()

        output = f"[download] Destination: {test_file}"
        result = self.service._find_downloaded_file(output)

        assert result == test_file

    def test_find_downloaded_file_fallback_to_newest(self):
        """Test fallback to finding newest mp3 file."""
        # Create test files with different timestamps
        old_file = self.service.download_directory / "old_audio.mp3"
        new_file = self.service.download_directory / "new_audio.mp3"

        old_file.touch()
        # Ensure different timestamps
        import time

        time.sleep(0.01)
        new_file.touch()

        output = "[download] Some output without file info"
        result = self.service._find_downloaded_file(output)

        assert result == new_file

    def test_find_downloaded_file_no_files(self):
        """Test finding downloaded file when no files exist."""
        output = "[download] Some output without file info"
        result = self.service._find_downloaded_file(output)

        assert result is None

    def test_cleanup_file_success(self):
        """Test successful file cleanup."""
        # Create test file
        test_file = self.service.download_directory / "test_cleanup.mp3"
        test_file.touch()

        result = self.service.cleanup_file(str(test_file))

        assert result is True
        assert not test_file.exists()

    def test_cleanup_file_not_exists(self):
        """Test cleanup of non-existent file."""
        non_existent = self.service.download_directory / "non_existent.mp3"

        result = self.service.cleanup_file(str(non_existent))

        assert result is False

    def test_cleanup_file_permission_error(self):
        """Test cleanup with permission error."""
        # Create test file
        test_file = self.service.download_directory / "test_permission.mp3"
        test_file.touch()

        # Mock unlink to raise PermissionError
        with unittest.mock.patch.object(Path, "unlink", side_effect=PermissionError()):
            result = self.service.cleanup_file(str(test_file))
            assert result is False
