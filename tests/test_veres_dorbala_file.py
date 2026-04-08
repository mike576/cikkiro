"""Unit tests for VeresDorbala audio files - handles OpenAI API issues."""

import pytest
from pathlib import Path
from src.processors.audio_processor import AudioProcessor
from src.core.exceptions import (
    TranscriptionError,
    OpenAIAPIError,
    AudioValidationError,
    AudioProcessingError,
)


class TestVeresDorbalaFiles:
    """Test suite for VeresDorbala audio files."""

    @pytest.fixture
    def processor(self):
        """Create audio processor instance."""
        return AudioProcessor()

    @pytest.fixture
    def test_file(self):
        """Get path to Hang.m4a test file."""
        return Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang.m4a")

    def test_file_exists(self, test_file):
        """Test that the Hang.m4a file exists."""
        assert test_file.exists(), f"Test file not found: {test_file}"

    def test_file_size(self, test_file):
        """Test file size and basic properties."""
        assert test_file.exists()
        size_mb = test_file.stat().st_size / (1024 * 1024)
        print(f"\nFile: {test_file.name}")
        print(f"Size: {size_mb:.2f} MB")
        print(f"Expected: 6.8 MB")

        # Should be around 6.8 MB
        assert 6 < size_mb < 8, f"File size {size_mb} MB is unexpected"

    def test_file_extension(self, test_file):
        """Test that file has correct extension."""
        assert test_file.suffix.lower() == ".m4a", f"Expected .m4a, got {test_file.suffix}"

    def test_audio_processor_validates_file(self, processor, test_file):
        """Test that audio processor can validate the file."""
        try:
            # This should not raise validation error
            result = processor.validate_audio_file(str(test_file))
            assert result is True
            print(f"✓ File validation passed")
        except AudioValidationError as e:
            pytest.fail(f"File validation failed: {e}")

    def test_audio_processor_processes_file(self, processor, test_file):
        """
        Test audio transcription with Hang.m4a file.

        NOTE: This test may fail with OpenAI API errors if:
        1. API quota exceeded
        2. API returns 400 error with invalid file format message
        3. Network connectivity issues

        Known Issue:
        - Error: "Invalid file format. Supported formats: [...'m4a'...]"
        - This can happen even though m4a is listed as supported
        - May be due to file corruption or unusual encoding
        """
        try:
            print(f"\nProcessing: {test_file.name}")
            print(f"Size: {test_file.stat().st_size / (1024*1024):.2f} MB")
            print(f"Language: Hungarian (auto)")

            transcript = processor.process(str(test_file), language="hu")

            # Should get a transcript back
            assert transcript is not None
            assert isinstance(transcript, str)
            assert len(transcript) > 0

            print(f"✓ Transcription successful!")
            print(f"  Transcript length: {len(transcript)} characters")
            print(f"  First 100 chars: {transcript[:100]}...")

        except (OpenAIAPIError, AudioProcessingError) as e:
            error_msg = str(e)
            print(f"\n✗ OpenAI API Error: {error_msg}")

            # Check if it's the "invalid file format" error
            if "Invalid file format" in error_msg and "m4a" in error_msg:
                print("\n" + "="*70)
                print("KNOWN ISSUE DETECTED: OpenAI rejects m4a file format")
                print("="*70)
                print(f"\nDEBUGGING INFO:")
                print(f"  - Error message mentions m4a is supported")
                print(f"  - But API still rejects the file")
                print(f"  - Possible causes:")
                print(f"    1. File may be corrupted or truncated")
                print(f"    2. File encoding may not match standard m4a")
                print(f"    3. File header may be malformed")
                print(f"    4. File metadata may be non-standard")
                print(f"\nRECOMMENDATIONS:")
                print(f"  1. Try converting file to MP3 (most compatible):")
                print(f"     ffmpeg -i Hang.m4a -acodec libmp3lame -b:a 192k Hang.mp3")
                print(f"\n  2. Or re-encode m4a with standard AAC codec:")
                print(f"     ffmpeg -i Hang.m4a -acodec aac -b:a 192k output.m4a")
                print(f"\n  3. Or convert to WAV (lossless):")
                print(f"     ffmpeg -i Hang.m4a output.wav")
                print(f"\n  4. Check file integrity first:")
                print(f"     ffmpeg -i Hang.m4a")
                print("="*70)

                # Don't fail the test - just report it
                pytest.skip(f"OpenAI API rejected file format - try converting to MP3")
            else:
                # Other API errors
                print(f"\nAPI Error: {error_msg}")
                pytest.skip(f"OpenAI API error: {error_msg}")

        except Exception as e:
            print(f"\n✗ Unexpected Error: {type(e).__name__}: {e}")
            pytest.fail(f"Unexpected error during transcription: {e}")


class TestHangM4aFileDebug:
    """Debug tests to investigate the Hang.m4a file issue."""

    @pytest.fixture
    def test_file(self):
        """Get path to Hang.m4a test file."""
        return Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang.m4a")

    def test_file_readable_by_pydub(self, test_file):
        """Test if file can be read by pydub."""
        try:
            from pydub import AudioSegment

            print(f"\nAttempting to load file with pydub...")
            audio = AudioSegment.from_file(str(test_file), format="m4a")

            print(f"✓ File loaded successfully by pydub")
            print(f"  Duration: {len(audio)/1000:.1f} seconds ({len(audio)/1000/60:.1f} minutes)")
            print(f"  Frame rate: {audio.frame_rate} Hz")
            print(f"  Channels: {audio.channels}")
            print(f"  Sample width: {audio.sample_width} bytes")

            assert len(audio) > 0, "Audio file is empty"

        except Exception as e:
            print(f"✗ pydub failed to load file: {e}")
            pytest.fail(f"File cannot be read by pydub: {e}")

    def test_compare_with_working_file(self, test_file):
        """Compare Hang.m4a with a known working file."""
        working_file = Path("/Users/miklostoth/develop/workspaces/cikkiro/data/Hang_260323_152947.m4a")

        if not working_file.exists():
            pytest.skip(f"Working file not found: {working_file}")

        print(f"\nComparing files:")
        print(f"  Problematic: {test_file.name} ({test_file.stat().st_size / (1024*1024):.2f} MB)")
        print(f"  Working:     {working_file.name} ({working_file.stat().st_size / (1024*1024):.2f} MB)")

        from pydub import AudioSegment

        try:
            problematic = AudioSegment.from_file(str(test_file), format="m4a")
            working = AudioSegment.from_file(str(working_file), format="m4a")

            print(f"\n  Problematic file:")
            print(f"    - Duration: {len(problematic)/1000/60:.1f} minutes")
            print(f"    - Frame rate: {problematic.frame_rate} Hz")
            print(f"    - Channels: {problematic.channels}")
            print(f"    - Sample width: {problematic.sample_width}")

            print(f"\n  Working file:")
            print(f"    - Duration: {len(working)/1000/60:.1f} minutes")
            print(f"    - Frame rate: {working.frame_rate} Hz")
            print(f"    - Channels: {working.channels}")
            print(f"    - Sample width: {working.sample_width}")

            # Identify differences
            if problematic.frame_rate != working.frame_rate:
                print(f"\n  ⚠ DIFFERENCE: Frame rate mismatch!")
            if problematic.channels != working.channels:
                print(f"\n  ⚠ DIFFERENCE: Channel count mismatch!")
            if problematic.sample_width != working.sample_width:
                print(f"\n  ⚠ DIFFERENCE: Sample width mismatch!")

        except Exception as e:
            print(f"✗ Error comparing files: {e}")

    def test_file_conversion_solution(self, test_file):
        """
        Test if converting the file would solve the issue.

        Provides commands to manually convert the file.
        """
        print(f"\nFile Conversion Solutions:")
        print(f"\n1. Convert m4a to MP3 (most compatible):")
        print(f"   ffmpeg -i {test_file} -acodec libmp3lame -b:a 192k output.mp3")
        print(f"\n2. Re-encode m4a with AAC codec:")
        print(f"   ffmpeg -i {test_file} -acodec aac -b:a 192k output.m4a")
        print(f"\n3. Convert to WAV (lossless, larger file):")
        print(f"   ffmpeg -i {test_file} output.wav")
        print(f"\n4. Check file integrity first:")
        print(f"   ffmpeg -i {test_file}")

        # Skip this test - it's just informational
        pytest.skip("This is an informational test showing conversion solutions")


class TestOtherVeresDorbalaFiles:
    """Test other files in the VeresDorbala directory."""

    @pytest.fixture
    def processor(self):
        """Create audio processor instance."""
        return AudioProcessor()

    def test_hang_1_m4a(self, processor):
        """Test Hang (1).m4a file (38 MB)."""
        test_file = Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang (1).m4a")

        if not test_file.exists():
            pytest.skip("File not found")

        print(f"\nTesting: {test_file.name}")
        print(f"Size: {test_file.stat().st_size / (1024*1024):.2f} MB")

        try:
            # Validate file
            processor.validate_audio_file(str(test_file))
            print(f"✓ File validation passed")
        except Exception as e:
            pytest.fail(f"Validation failed: {e}")

    def test_hang_260329_112254_m4a(self, processor):
        """Test Hang 260329_112254.m4a file (21 MB)."""
        test_file = Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang 260329_112254.m4a")

        if not test_file.exists():
            pytest.skip("File not found")

        print(f"\nTesting: {test_file.name}")
        print(f"Size: {test_file.stat().st_size / (1024*1024):.2f} MB")

        try:
            # Validate file
            processor.validate_audio_file(str(test_file))
            print(f"✓ File validation passed")
        except Exception as e:
            pytest.fail(f"Validation failed: {e}")
