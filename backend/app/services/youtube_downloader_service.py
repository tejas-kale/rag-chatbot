"""
YouTube audio downloader service using yt-dlp subprocess.

This service provides functionality to download audio tracks from YouTube URLs
as MP3 files using yt-dlp as a subprocess.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Configure logger
logger = logging.getLogger(__name__)


class YouTubeDownloaderService:
    """
    Service for downloading audio from YouTube URLs using yt-dlp.
    """

    def __init__(self, download_directory: str = "downloads/audio"):
        """
        Initialize the YouTubeDownloaderService.

        Args:
            download_directory: Directory where audio files will be saved.
        """
        self.download_directory = Path(download_directory)
        self.download_directory.mkdir(parents=True, exist_ok=True)

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
        Download audio from a YouTube URL as MP3.

        Args:
            youtube_url: The YouTube URL to download audio from.

        Returns:
            Path to the downloaded MP3 file if successful, None otherwise.

        Raises:
            ValueError: If the URL is not a valid YouTube URL.
            RuntimeError: If yt-dlp subprocess fails.
        """
        if not self.is_youtube_url(youtube_url):
            raise ValueError(f"Invalid YouTube URL: {youtube_url}")

        logger.info(f"Starting audio download from: {youtube_url}")

        # Construct yt-dlp command
        output_template = str(self.download_directory / "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "192K",
            "--output",
            output_template,
            "--no-playlist",
            "--restrict-filenames",
            youtube_url,
        ]

        try:
            # Run yt-dlp subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                check=True,
            )

            logger.info("yt-dlp subprocess completed successfully")
            logger.debug(f"yt-dlp stdout: {result.stdout}")

            # Find the downloaded file
            downloaded_file = self._find_downloaded_file(result.stdout)
            if downloaded_file and downloaded_file.exists():
                logger.info(f"Audio downloaded successfully: {downloaded_file}")
                return str(downloaded_file)
            else:
                logger.error("Downloaded file not found after yt-dlp execution")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"yt-dlp subprocess timed out for URL: {youtube_url}")
            raise RuntimeError(f"Download timed out for URL: {youtube_url}")
        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp subprocess failed: {e.stderr}")
            raise RuntimeError(f"yt-dlp failed: {e.stderr}")
        except FileNotFoundError:
            logger.error("yt-dlp not found. Please install yt-dlp.")
            raise RuntimeError("yt-dlp not found. Please install yt-dlp.")
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during download: {e}")

    def _find_downloaded_file(self, yt_dlp_output: str) -> Optional[Path]:
        """
        Parse yt-dlp output to find the downloaded file path.

        Args:
            yt_dlp_output: stdout from yt-dlp command.

        Returns:
            Path to the downloaded file if found, None otherwise.
        """
        for line in yt_dlp_output.split("\n"):
            if "has already been downloaded" in line or "Destination:" in line:
                # Extract filename from various yt-dlp output formats
                if "]" in line and self.download_directory.name in line:
                    filename_part = line.split("]")[-1].strip()
                    # Remove "Destination: " prefix if present
                    if filename_part.startswith("Destination: "):
                        filename_part = filename_part[len("Destination: ") :].strip()

                    # Handle case where full path is in output
                    if str(self.download_directory) in filename_part:
                        return Path(filename_part)
                    else:
                        return self.download_directory / filename_part

        # Fallback: look for .mp3 files in download directory
        mp3_files = list(self.download_directory.glob("*.mp3"))
        if mp3_files:
            # Return the most recently modified file
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
