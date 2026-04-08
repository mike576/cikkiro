"""Audio file processing for transcription."""

import logging
from pathlib import Path
from typing import Optional

from src.core.constants import SUPPORTED_AUDIO_FORMATS, MAX_AUDIO_SIZE_MB
from src.core.exceptions import AudioProcessingError, AudioValidationError
from src.services.openai_service import OpenAIService
from src.utils.logger import get_logger, log_with_context
from src.utils.validators import validate_audio_file

logger = get_logger(__name__)


class AudioProcessor:
    """Processor for audio files (transcription)."""

    def __init__(self, openai_service: Optional[OpenAIService] = None):
        """
        Initialize audio processor.

        Args:
            openai_service: OpenAI service for transcription
                           If None, will be created with default API key
        """
        if openai_service:
            self.openai_service = openai_service
        else:
            self.openai_service = OpenAIService()

        logger.info("Audio processor initialized")

    def process(
        self,
        file_path: str,
        language: Optional[str] = None,
    ) -> str:
        """
        Process audio file and return transcript.

        Args:
            file_path: Path to audio file
            language: Language code (e.g., 'hu' for Hungarian)

        Returns:
            Transcribed text

        Raises:
            AudioProcessingError: If processing fails
        """
        try:
            audio_path = Path(file_path)

            log_with_context(
                logger,
                logging.INFO,
                "Processing audio file",
                file=audio_path.name,
                language=language,
            )

            # Validate audio file
            self.validate_audio_file(file_path)

            # Get file size for reference
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)

            # Transcribe audio
            transcript = self.openai_service.transcribe_audio(
                file_path,
                language=language,
            )

            if not transcript or not transcript.strip():
                raise AudioProcessingError("Transcription resulted in empty text")

            log_with_context(
                logger,
                logging.INFO,
                "Audio processing completed",
                file=audio_path.name,
                size_mb=file_size_mb,
                transcript_length=len(transcript),
            )

            return transcript

        except AudioValidationError:
            raise

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise AudioProcessingError(f"Audio processing failed: {e}")

    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate audio file format and size.

        Args:
            file_path: Path to audio file

        Returns:
            True if valid

        Raises:
            AudioValidationError: If validation fails
        """
        try:
            audio_path = Path(file_path)

            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Check file extension
            validate_audio_file(
                audio_path.name,
                audio_path.stat().st_size,
            )

            logger.debug(f"Audio file validation passed: {audio_path.name}")
            return True

        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            raise AudioValidationError(f"Audio validation failed: {e}")

    def get_supported_formats(self) -> list:
        """
        Get list of supported audio formats.

        Returns:
            List of supported formats
        """
        return SUPPORTED_AUDIO_FORMATS

    def get_max_file_size_mb(self) -> int:
        """
        Get maximum allowed file size in MB.

        Returns:
            Maximum file size
        """
        return MAX_AUDIO_SIZE_MB
