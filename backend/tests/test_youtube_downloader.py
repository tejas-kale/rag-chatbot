"""
Test module for YouTube downloader service.
"""

import shutil
import tempfile
import time
import unittest.mock
from pathlib import Path

import pytest
import yt_dlp

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

    @unittest.mock.patch("yt_dlp.YoutubeDL")
    def test_download_audio_success(self, mock_ydl_class):
        """Test successful audio download via yt-dlp Python API."""
        # Setup mock
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.download.return_value = None

        # Create a mock downloaded file
        test_file = self.service.download_directory / "test_audio.mp3"
        test_file.touch()

        # Mock the postprocessor hook to simulate file creation
        def mock_download(urls):
            self.service.downloaded_file_path = test_file

        mock_ydl.download.side_effect = mock_download

        # Test
        result = self.service.download_audio("https://youtube.com/watch?v=test")

        # Verify yt-dlp was called
        mock_ydl_class.assert_called_once()
        mock_ydl.download.assert_called_once_with(["https://youtube.com/watch?v=test"])

        # Verify result
        assert result == str(test_file)

    @unittest.mock.patch("yt_dlp.YoutubeDL")
    def test_download_audio_yt_dlp_error(self, mock_ydl_class):
        """Test yt-dlp download error handling."""
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError(
            "Error downloading video"
        )

        with pytest.raises(RuntimeError, match="yt-dlp download failed"):
            self.service.download_audio("https://youtube.com/watch?v=test")

    @unittest.mock.patch("yt_dlp.YoutubeDL")
    def test_download_audio_no_file_created(self, mock_ydl_class):
        """Test handling when download succeeds but no file is created."""
        mock_ydl = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl.download.return_value = None

        result = self.service.download_audio("https://youtube.com/watch?v=test")
        assert result is None

    def test_postprocessor_hook(self):
        """Test the postprocessor hook functionality."""
        test_file = self.service.download_directory / "test_audio.mp3"
        test_file.touch()

        # Test hook with finished status
        hook_data = {"status": "finished", "filepath": str(test_file)}
        self.service._postprocessor_hook(hook_data)

        assert self.service.downloaded_file_path == test_file

    def test_find_newest_mp3_file(self):
        """Test finding the newest MP3 file in download directory."""
        # Create test files with different timestamps
        old_file = self.service.download_directory / "old_audio.mp3"
        new_file = self.service.download_directory / "new_audio.mp3"

        old_file.touch()
        time.sleep(0.01)  # Ensure different timestamps
        new_file.touch()

        result = self.service._find_newest_mp3_file()
        assert result == new_file

    def test_find_newest_mp3_file_no_files(self):
        """Test finding newest MP3 file when no files exist."""
        result = self.service._find_newest_mp3_file()
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
