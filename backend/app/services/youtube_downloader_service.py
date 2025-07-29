"""
YouTube audio downloader service using yt-dlp Python interface.

This service provides functionality to download audio tracks from YouTube URLs
as MP3 files using yt-dlp's Python API.
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yt_dlp

# Configure logger
logger = logging.getLogger(__name__)


class YouTubeDownloaderService:
    """
    Service for downloading audio from YouTube URLs using yt-dlp Python API.
    """

    def __init__(self, download_directory: str = "downloads/audio"):
        """
        Initialize the YouTubeDownloaderService.

        Args:
            download_directory: Directory where audio files will be saved.
        """
        self.download_directory = Path(download_directory)
        self.download_directory.mkdir(parents=True, exist_ok=True)
        self.downloaded_file_path = None  # Track the last downloaded file

    def is_youtube_url(self, url: str) -> bool:
        """
        Check if the given URL is a valid YouTube URL.

        Args:
            url: URL to validate.

        Returns:
            True if the URL is a YouTube URL, False otherwise.
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() in [
                "youtube.com",
                "www.youtube.com",
                "youtu.be",
                "music.youtube.com",
            ]
        except Exception:
            return False

    def download_audio(self, youtube_url: str) -> Optional[str]:
        """
        Download audio from a YouTube URL as MP3 using yt-dlp Python API.

        Args:
            youtube_url: The YouTube URL to download audio from.

        Returns:
            Path to the downloaded MP3 file if successful, None otherwise.

        Raises:
            ValueError: If the URL is not a valid YouTube URL.
            RuntimeError: If yt-dlp download fails.
        """
        if not self.is_youtube_url(youtube_url):
            raise ValueError(f"Invalid YouTube URL: {youtube_url}")

        logger.info(f"Starting audio download from: {youtube_url}")

        # Reset the downloaded file tracker
        self.downloaded_file_path = None

        # Configure yt-dlp options
        output_template = str(self.download_directory / "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": output_template,
            "noplaylist": True,
            "restrictfilenames": True,
            "quiet": True,  # Reduce verbose output
            "no_warnings": False,
        }

        try:
            # Add progress hook to track downloaded file
            ydl_opts["postprocessor_hooks"] = [self._postprocessor_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download the audio
                ydl.download([youtube_url])

                # Return the downloaded file path if available
                if self.downloaded_file_path and self.downloaded_file_path.exists():
                    logger.info(
                        f"Audio downloaded successfully: {self.downloaded_file_path}"
                    )
                    return str(self.downloaded_file_path)
                else:
                    # Fallback: find the most recently created MP3 file
                    downloaded_file = self._find_newest_mp3_file()
                    if downloaded_file:
                        logger.info(f"Audio downloaded successfully: {downloaded_file}")
                        return str(downloaded_file)
                    else:
                        logger.error("Downloaded file not found after yt-dlp execution")
                        return None

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download failed: {e}")
            raise RuntimeError(f"yt-dlp download failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during download: {e}")

    def _postprocessor_hook(self, d):
        """
        Hook called by yt-dlp after post-processing (audio extraction).

        Args:
            d: Dictionary containing post-processor information.
        """
        if d["status"] == "finished":
            self.downloaded_file_path = Path(d["filepath"])
            logger.debug(f"Post-processing finished: {self.downloaded_file_path}")

    def _find_newest_mp3_file(self) -> Optional[Path]:
        """
        Find the most recently created MP3 file in the download directory.

        Returns:
            Path to the newest MP3 file if found, None otherwise.
        """
        mp3_files = list(self.download_directory.glob("*.mp3"))
        if mp3_files:
            return max(mp3_files, key=lambda f: f.stat().st_mtime)
        return None

    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a downloaded file.

        Args:
            file_path: Path to the file to delete.

        Returns:
            True if cleanup was successful, False otherwise.
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for cleanup: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}", exc_info=True)
            return False
