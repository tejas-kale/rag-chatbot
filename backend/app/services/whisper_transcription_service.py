"""
Whisper.cpp transcription service for audio-to-text conversion.

This service provides functionality to transcribe audio files using the
whisper.cpp executable as a subprocess.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# Configure logger
logger = logging.getLogger(__name__)


class WhisperTranscriptionService:
    """
    Service for transcribing audio files using whisper.cpp executable.
    """

    def __init__(
        self,
        whisper_executable: str = "whisper",
        default_model: str = "base",
        temp_dir: Optional[str] = None,
    ):
        """
        Initialize the WhisperTranscriptionService.

        Args:
            whisper_executable: Path to the whisper.cpp executable.
            default_model: Default whisper model to use for transcription.
            temp_dir: Directory for temporary files (uses system temp if None).
        """
        self.whisper_executable = whisper_executable
        self.default_model = default_model
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())

    def is_whisper_available(self) -> bool:
        """
        Check if whisper.cpp executable is available.

        Returns:
            True if whisper.cpp is available, False otherwise.
        """
        try:
            result = subprocess.run(
                [self.whisper_executable, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def transcribe_audio(
        self, audio_file_path: str, model: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe an audio file using whisper.cpp.

        Args:
            audio_file_path: Path to the audio file to transcribe.
            model: Whisper model to use (defaults to default_model).

        Returns:
            Transcribed text if successful, None otherwise.

        Raises:
            FileNotFoundError: If the audio file doesn't exist.
            RuntimeError: If whisper.cpp is not available or transcription fails.
        """
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        if not self.is_whisper_available():
            executable = self.whisper_executable
            raise RuntimeError(
                f"whisper.cpp executable not found or not working: {executable}"
            )

        model_to_use = model or self.default_model
        logger.info(
            f"Starting transcription of {audio_file_path} using model {model_to_use}"
        )

        # Create temporary output file for whisper.cpp
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", dir=self.temp_dir, delete=False
        ) as temp_output:
            temp_output_path = Path(temp_output.name)

        try:
            # Build whisper.cpp command
            cmd = [
                self.whisper_executable,
                "-m",
                model_to_use,
                "-f",
                str(audio_path),
                "-otxt",  # Output as text format
                "-of",
                str(temp_output_path.with_suffix("")),  # Output file prefix
            ]

            logger.debug(f"Running whisper.cpp command: {' '.join(cmd)}")

            # Run whisper.cpp subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"whisper.cpp failed with return code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"whisper.cpp transcription failed: {result.stderr}")

            # Read transcription result
            transcription_file = temp_output_path
            if transcription_file.exists() and transcription_file.stat().st_size > 0:
                transcribed_text = transcription_file.read_text(
                    encoding="utf-8"
                ).strip()
                logger.info(
                    f"Successfully transcribed {audio_file_path} "
                    f"({len(transcribed_text)} characters)"
                )
                return transcribed_text
            else:
                logger.warning(
                    f"Transcription completed but no output file found: "
                    f"{transcription_file}"
                )
                # Try to get text from stdout as fallback
                if result.stdout.strip():
                    return result.stdout.strip()
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"whisper.cpp transcription timed out for {audio_file_path}")
            raise RuntimeError("whisper.cpp transcription timed out")
        except Exception as e:
            logger.error(
                f"Unexpected error during transcription of {audio_file_path}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Transcription failed: {e}")
        finally:
            # Clean up temporary files
            self._cleanup_temp_file(temp_output_path)

    def _cleanup_temp_file(self, file_path: Path) -> None:
        """
        Clean up a temporary file.

        Args:
            file_path: Path to the temporary file to clean up.
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {e}")

    def get_available_models(self) -> list[str]:
        """
        Get list of available whisper models.

        Note: This is a static list of common whisper models.
        whisper.cpp doesn't provide a command to list available models.

        Returns:
            List of available model names.
        """
        return [
            "tiny",
            "tiny.en",
            "base",
            "base.en",
            "small",
            "small.en",
            "medium",
            "medium.en",
            "large-v1",
            "large-v2",
            "large-v3",
        ]
