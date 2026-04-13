"""OpenAI API service for audio transcription."""

import logging
import os
import tempfile
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional

from openai import OpenAI, APIError
from pydub import AudioSegment

from src.core.exceptions import OpenAIAPIError, TranscriptionError
from src.utils.logger import get_logger, log_with_context

# Azure Key Vault support (optional)
try:
    from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_KEYVAULT_AVAILABLE = True
except ImportError:
    AZURE_KEYVAULT_AVAILABLE = False

logger = get_logger(__name__)

# OpenAI Whisper API has a 25MB file size limit
WHISPER_MAX_FILE_SIZE_MB = 25


class OpenAIService:
    """Service for interacting with OpenAI API (Whisper transcription)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var or Key Vault)

        Raises:
            OpenAIAPIError: If authentication fails
        """
        try:
            # Try to get API key from various sources
            api_key_to_use = api_key or self._get_api_key()

            if not api_key_to_use:
                raise ValueError("No API key provided or found in environment/Key Vault")

            self.client = OpenAI(api_key=api_key_to_use)
            logger.info("OpenAI service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise OpenAIAPIError(f"OpenAI initialization failed: {e}")

    @staticmethod
    def _get_api_key() -> Optional[str]:
        """
        Get API key from environment variable or Azure Key Vault.

        Returns:
            API key or None if not found
        """
        # Try environment variable first
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            logger.info("Using OPENAI_API_KEY from environment")
            return api_key

        # Try Azure Key Vault if configured and available
        if not AZURE_KEYVAULT_AVAILABLE:
            return None

        keyvault_name = os.environ.get("KEYVAULT_NAME")
        secret_name = os.environ.get("KEYVAULT_SECRET_NAME", "openai-api-key")

        if not keyvault_name:
            return None

        try:
            logger.info(f"Attempting to read API key from Key Vault: {keyvault_name}")

            # Try Managed Identity first (for Azure services)
            try:
                credential = ManagedIdentityCredential()
                logger.info("Using Managed Identity to access Key Vault")
            except Exception:
                # Fall back to DefaultAzureCredential (for local dev)
                logger.info("Managed Identity not available, using DefaultAzureCredential")
                credential = DefaultAzureCredential()

            keyvault_url = f"https://{keyvault_name}.vault.azure.net/"
            client = SecretClient(vault_url=keyvault_url, credential=credential)
            secret = client.get_secret(secret_name)

            logger.info(f"Successfully retrieved API key from Key Vault: {keyvault_name}")
            return secret.value

        except Exception as e:
            logger.warning(f"Failed to retrieve API key from Key Vault: {e}")
            return None

    def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio file using Whisper API.

        Handles large files by splitting them into chunks (OpenAI limit is 25MB).

        Args:
            audio_file_path: Path to audio file (MP3, WAV, M4A, WebM)
            language: Language code (e.g., 'hu' for Hungarian, 'en' for English)
                     If None, Whisper will auto-detect
            prompt: Optional prompt to guide transcription (for better accuracy)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            audio_path = Path(audio_file_path)

            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            file_size_mb = audio_path.stat().st_size / (1024 * 1024)

            log_with_context(
                logger,
                logging.INFO,
                "Starting audio transcription",
                file=audio_path.name,
                size_mb=file_size_mb,
                language=language,
            )

            # Check if file needs to be split
            if file_size_mb > WHISPER_MAX_FILE_SIZE_MB:
                logger.info(
                    f"Audio file ({file_size_mb:.2f}MB) exceeds Whisper limit "
                    f"({WHISPER_MAX_FILE_SIZE_MB}MB), splitting into chunks..."
                )
                transcript_text = self._transcribe_large_audio(
                    audio_path, language, prompt
                )
            else:
                # File is small enough, transcribe directly
                # Open file handle directly for Whisper API
                audio_file = open(audio_path, "rb")

                try:
                    # Build parameters, only include optional ones if provided
                    # Note: Whisper API does NOT support temperature parameter
                    transcribe_params = {
                        "model": "whisper-1",
                        "file": audio_file,
                    }
                    if language:
                        transcribe_params["language"] = language
                    if prompt:
                        transcribe_params["prompt"] = prompt

                    # Log parameters being sent (excluding file object)
                    log_params = {k: v for k, v in transcribe_params.items() if k != "file"}
                    logger.info(f"Sending to Whisper API: {log_params}")

                    transcript_response = self.client.audio.transcriptions.create(**transcribe_params)
                    transcript_text = transcript_response.text
                finally:
                    audio_file.close()

            log_with_context(
                logger,
                logging.INFO,
                "Audio transcription completed",
                file=audio_path.name,
                transcript_length=len(transcript_text),
            )

            return transcript_text

        except FileNotFoundError as e:
            logger.error(f"Audio file not found: {e}")
            raise TranscriptionError(f"Audio file not found: {e}")

        except APIError as e:
            logger.error(f"OpenAI API error during transcription: {e}")
            raise TranscriptionError(f"OpenAI API error: {e}")

        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise TranscriptionError(f"Transcription failed: {e}")

    def _transcribe_large_audio(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """
        Transcribe a large audio file by splitting it into chunks.

        Args:
            audio_path: Path to audio file
            language: Language code
            prompt: Optional transcription prompt

        Returns:
            Concatenated transcriptions of all chunks
        """
        temp_dir = None
        try:
            # Create temporary directory for chunks
            temp_dir = tempfile.mkdtemp()

            # Load audio file
            logger.info(f"Loading audio file: {audio_path.name}")
            audio = AudioSegment.from_file(str(audio_path))

            # Calculate chunk duration (target 20MB chunks to be safe)
            total_duration_ms = len(audio)
            file_size_bytes = audio_path.stat().st_size
            bytes_per_ms = file_size_bytes / total_duration_ms

            # Calculate how many ms we can fit in 20MB to be safe
            target_chunk_size_bytes = 20 * 1024 * 1024
            chunk_duration_ms = int(target_chunk_size_bytes / bytes_per_ms)

            # Split audio into chunks
            num_chunks = (total_duration_ms + chunk_duration_ms - 1) // chunk_duration_ms
            logger.info(
                f"Splitting audio into {num_chunks} chunks "
                f"({chunk_duration_ms}ms per chunk)"
            )

            transcriptions = []

            for i in range(num_chunks):
                start_ms = i * chunk_duration_ms
                end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)

                chunk = audio[start_ms:end_ms]
                chunk_path = Path(temp_dir) / f"chunk_{i:03d}.mp3"

                # Export chunk
                chunk.export(str(chunk_path), format="mp3")
                chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)

                logger.info(
                    f"Transcribing chunk {i + 1}/{num_chunks} "
                    f"({chunk_size_mb:.2f}MB, {(end_ms - start_ms) / 1000:.1f}s)"
                )

                # Transcribe chunk
                # Open file handle directly for Whisper API
                chunk_file = open(chunk_path, "rb")

                try:
                    # Build parameters, only include optional ones if provided
                    # Note: Whisper API does NOT support temperature parameter
                    transcribe_params = {
                        "model": "whisper-1",
                        "file": chunk_file,
                    }
                    if language:
                        transcribe_params["language"] = language
                    if prompt:
                        transcribe_params["prompt"] = prompt

                    # Log parameters being sent (excluding file object)
                    log_params = {k: v for k, v in transcribe_params.items() if k != "file"}
                    logger.info(f"Sending chunk {i + 1}/{num_chunks} to Whisper API: {log_params}")

                    response = self.client.audio.transcriptions.create(**transcribe_params)
                    transcriptions.append(response.text)
                finally:
                    chunk_file.close()

                chunk_path.unlink()  # Delete chunk file

            # Concatenate transcriptions
            return " ".join(transcriptions)

        finally:
            # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")

    def estimate_transcription_cost(
        self,
        duration_minutes: float,
    ) -> float:
        """
        Estimate cost of audio transcription.

        OpenAI charges $0.006 per minute of audio for Whisper API.

        Args:
            duration_minutes: Duration of audio in minutes

        Returns:
            Estimated cost in USD
        """
        cost_per_minute = 0.006
        estimated_cost = duration_minutes * cost_per_minute

        logger.debug(
            f"Estimated transcription cost: ${estimated_cost:.4f} "
            f"({duration_minutes} minutes)"
        )

        return estimated_cost

    def generate_chat_completion(
        self,
        transcript: str,
        user_prompt: str,
        model: str = "gpt-4o",
        max_tokens: int = 10000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate LLM analysis of transcript using Chat Completion API.

        Args:
            transcript: The transcript text to analyze
            user_prompt: User's analysis instruction/question
            model: OpenAI model to use (gpt-4o, gpt-5.4, etc.)
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0-1)

        Returns:
            LLM response text

        Raises:
            OpenAIAPIError: If chat completion fails
        """
        try:
            log_with_context(
                logger,
                logging.INFO,
                "Starting chat completion",
                model=model,
                transcript_length=len(transcript),
                prompt_length=len(user_prompt),
            )

            # Build messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI assistant analyzing transcripts. "
                        "Provide clear, accurate, and insightful analysis based on "
                        "the transcript and user's request."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Transcript:\n\n{transcript}\n\n---\n\n{user_prompt}",
                },
            ]

            # Call OpenAI Chat Completion API
            # Note: Newer OpenAI models use max_completion_tokens instead of max_tokens
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract response text
            logger.info(f"Full response object: {response}")
            logger.info(f"Response choices: {response.choices}")

            if not response.choices or not response.choices[0].message.content:
                logger.warning("Response is empty! Full response: " + str(response))
                raise OpenAIAPIError("Chat completion returned empty response")

            response_text = response.choices[0].message.content

            if not response_text or response_text.strip() == "":
                logger.warning("Response text is empty after extraction")
                raise OpenAIAPIError("Chat completion returned empty response text")

            log_with_context(
                logger,
                logging.INFO,
                "Chat completion completed",
                model=model,
                response_length=len(response_text),
                tokens_used=response.usage.total_tokens if response.usage else 0,
            )

            return response_text

        except APIError as e:
            logger.error(f"OpenAI API error during chat completion: {e}")
            raise OpenAIAPIError(f"Chat completion failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error during chat completion: {e}")
            raise OpenAIAPIError(f"Chat completion error: {e}")
