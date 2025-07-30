"""
Text correction service for improving transcription quality.

This service provides basic text correction functionality for transcribed text.
Future enhancements could include AI-powered grammar correction,
spell checking, and context-aware improvements.
"""

import logging
import re

# Configure logger
logger = logging.getLogger(__name__)


class TextCorrectionService:
    """
    Service for applying basic text corrections to transcriptions.
    """

    def __init__(self):
        """Initialize the TextCorrectionService."""
        pass

    def correct_transcription(self, raw_text: str) -> str:
        """
        Apply basic corrections to raw transcription text.

        This method performs simple text cleaning and normalization.
        Future versions could integrate with AI services for advanced correction.

        Args:
            raw_text: The raw transcription text to correct

        Returns:
            Corrected text string

        Raises:
            ValueError: If raw_text is None or empty
        """
        if not raw_text or not isinstance(raw_text, str):
            raise ValueError("Raw text must be a non-empty string")

        try:
            logger.debug(f"Starting text correction for {len(raw_text)} characters")

            corrected_text = raw_text

            # Apply basic corrections
            corrected_text = self._normalize_whitespace(corrected_text)
            corrected_text = self._fix_common_transcription_errors(corrected_text)
            corrected_text = self._improve_punctuation(corrected_text)
            corrected_text = self._capitalize_sentences(corrected_text)

            logger.debug("Text correction completed")
            return corrected_text.strip()

        except Exception as e:
            logger.error(f"Error during text correction: {e}", exc_info=True)
            # Return original text if correction fails
            return raw_text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in the text.

        Args:
            text: Input text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace from lines
        text = "\n".join(line.strip() for line in text.split("\n"))
        return text

    def _fix_common_transcription_errors(self, text: str) -> str:
        """
        Fix common transcription errors.

        Args:
            text: Input text

        Returns:
            Text with common errors fixed
        """
        # Common transcription error corrections
        corrections = {
            # Common speech-to-text mistakes
            r"\bi\b": "I",  # lowercase 'i' to uppercase 'I'
            r"\byou\s+know\b": "you know",  # normalize filler words
            r"\buh\b": "",  # remove filler sounds
            r"\bum\b": "",  # remove filler sounds
            r"\ber\b": "",  # remove filler sounds
        }

        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _improve_punctuation(self, text: str) -> str:
        """
        Improve punctuation in the text.

        Args:
            text: Input text

        Returns:
            Text with improved punctuation
        """
        # Add periods at the end of sentences that don't have punctuation
        # Simple heuristic: if a line ends without punctuation, add a period
        lines = text.split("\n")
        improved_lines = []

        for line in lines:
            line = line.strip()
            if line and not re.search(r"[.!?]$", line):
                # Check if it looks like a complete sentence (has some length)
                if len(line) > 10:
                    line += "."
            improved_lines.append(line)

        return "\n".join(improved_lines)

    def _capitalize_sentences(self, text: str) -> str:
        """
        Capitalize the first letter of sentences.

        Args:
            text: Input text

        Returns:
            Text with properly capitalized sentences
        """
        # Capitalize first letter after sentence-ending punctuation
        text = re.sub(
            r"(^|[.!?]\s+)([a-z])",
            lambda m: m.group(1) + m.group(2).upper(),
            text,
            flags=re.MULTILINE,
        )

        # Capitalize the very first letter of the text
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return text

    def get_correction_stats(self, original_text: str, corrected_text: str) -> dict:
        """
        Get statistics about the corrections applied.

        Args:
            original_text: The original text
            corrected_text: The corrected text

        Returns:
            Dictionary with correction statistics
        """
        try:
            original_words = len(original_text.split())
            corrected_words = len(corrected_text.split())

            # Simple character-level difference count
            char_changes = sum(
                1 for a, b in zip(original_text, corrected_text) if a != b
            )
            if len(original_text) != len(corrected_text):
                char_changes += abs(len(original_text) - len(corrected_text))

            return {
                "original_length": len(original_text),
                "corrected_length": len(corrected_text),
                "original_word_count": original_words,
                "corrected_word_count": corrected_words,
                "character_changes": char_changes,
                "change_percentage": (
                    (char_changes / len(original_text) * 100) if original_text else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating correction stats: {e}")
            return {
                "original_length": len(original_text) if original_text else 0,
                "corrected_length": len(corrected_text) if corrected_text else 0,
                "original_word_count": 0,
                "corrected_word_count": 0,
                "character_changes": 0,
                "change_percentage": 0,
            }
