"""Test language parameter handling in audio transcription."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.openai_service import OpenAIService
from src.processors.audio_processor import AudioProcessor


class TestLanguageParameterHandling:
    """Test that language=None is never passed to OpenAI API."""

    def test_transcribe_audio_with_none_language(self):
        """Test that None language is not passed to OpenAI API."""
        # Create a mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Test transcript"
        mock_client.audio.transcriptions.create.return_value = mock_response

        # Create service with mock client - patch OpenAI() initialization
        with patch("src.services.openai_service.OpenAI", return_value=mock_client):
            service = OpenAIService(api_key="test-key")

            # Mock file operations
            with patch("builtins.open", create=True):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat_result = Mock()
                        mock_stat_result.st_size = 1000000  # 1MB
                        mock_stat.return_value = mock_stat_result

                        # Call with language=None
                        transcript = service.transcribe_audio(
                            "/tmp/test.mp3",
                            language=None,
                        )

                        # Assert that the API was called WITHOUT language parameter
                        call_args = mock_client.audio.transcriptions.create.call_args

                        # Check that language was not in the call
                        assert "language" not in call_args.kwargs, (
                            "language=None should not be passed to OpenAI API. "
                            f"Got call with kwargs: {call_args.kwargs}"
                        )

                        # Also verify temperature is NOT passed (not valid for Whisper API)
                        assert "temperature" not in call_args.kwargs, (
                            "temperature should not be passed to Whisper API. "
                            f"Got call with kwargs: {call_args.kwargs}"
                        )

    def test_transcribe_audio_with_language_specified(self):
        """Test that language is passed when specified."""
        # Create a mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Test transcript"
        mock_client.audio.transcriptions.create.return_value = mock_response

        # Create service with mock client - patch OpenAI() initialization
        with patch("src.services.openai_service.OpenAI", return_value=mock_client):
            service = OpenAIService(api_key="test-key")

            # Mock file operations
            with patch("builtins.open", create=True):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat_result = Mock()
                        mock_stat_result.st_size = 1000000  # 1MB
                        mock_stat.return_value = mock_stat_result

                        # Call with language="hu"
                        transcript = service.transcribe_audio(
                            "/tmp/test.mp3",
                            language="hu",
                        )

                        # Assert that the API was called WITH language parameter
                        call_args = mock_client.audio.transcriptions.create.call_args

                        # Check that language was in the call
                        assert "language" in call_args.kwargs, (
                            "language should be passed to OpenAI API when specified"
                        )
                        assert call_args.kwargs["language"] == "hu"

    def test_audio_processor_with_none_language(self):
        """Test that AudioProcessor doesn't pass None language to service."""
        # Create a mock OpenAI service
        mock_service = Mock(spec=OpenAIService)
        mock_service.transcribe_audio.return_value = "Test transcript"

        # Create processor with mock service
        processor = AudioProcessor(openai_service=mock_service)

        # Mock file operations
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat_result = Mock()
                mock_stat_result.st_size = 1000000  # 1MB
                mock_stat.return_value = mock_stat_result

                # Call with language=None
                transcript = processor.process(
                    "/tmp/test.mp3",
                    language=None,
                )

                # Assert that transcribe_audio was called with only file_path
                # (no language keyword argument)
                mock_service.transcribe_audio.assert_called_once()
                call_args = mock_service.transcribe_audio.call_args

                # Check that language was not in the call
                assert "language" not in call_args.kwargs, (
                    "AudioProcessor should not pass language=None to service. "
                    f"Got call with kwargs: {call_args.kwargs}"
                )

    def test_audio_processor_with_language_specified(self):
        """Test that AudioProcessor passes language when specified."""
        # Create a mock OpenAI service
        mock_service = Mock(spec=OpenAIService)
        mock_service.transcribe_audio.return_value = "Test transcript"

        # Create processor with mock service
        processor = AudioProcessor(openai_service=mock_service)

        # Mock file operations
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat_result = Mock()
                mock_stat_result.st_size = 1000000  # 1MB
                mock_stat.return_value = mock_stat_result

                # Call with language="hu"
                transcript = processor.process(
                    "/tmp/test.mp3",
                    language="hu",
                )

                # Assert that transcribe_audio was called WITH language
                call_args = mock_service.transcribe_audio.call_args

                # Check that language was in the call
                assert "language" in call_args.kwargs, (
                    "AudioProcessor should pass language when specified"
                )
                assert call_args.kwargs["language"] == "hu"
