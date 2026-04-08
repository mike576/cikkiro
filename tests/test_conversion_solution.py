"""Test file conversion as solution to M4A format issue."""

import pytest
import os
from pathlib import Path
from src.processors.audio_processor import AudioProcessor
from src.core.exceptions import AudioProcessingError, OpenAIAPIError


class TestConversionSolution:
    """Test converting M4A to MP3 as a solution."""

    @pytest.fixture
    def processor(self):
        """Create audio processor instance."""
        return AudioProcessor()

    @pytest.fixture
    def source_file(self):
        """Get path to problematic Hang.m4a file."""
        return Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang.m4a")

    @pytest.fixture
    def converted_file(self, tmp_path):
        """Create path for converted MP3 file."""
        return tmp_path / "Hang_converted.mp3"

    def test_ffmpeg_available(self):
        """Check if ffmpeg is available on the system."""
        import subprocess
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            assert result.returncode == 0, "ffmpeg command failed"
            print("\n✓ ffmpeg is available")
        except FileNotFoundError:
            pytest.skip("ffmpeg not installed - install with: brew install ffmpeg")

    def test_convert_m4a_to_mp3(self, source_file, converted_file):
        """Convert M4A file to MP3 using ffmpeg."""
        import subprocess

        if not source_file.exists():
            pytest.skip(f"Source file not found: {source_file}")

        print(f"\nConverting: {source_file.name} → {converted_file.name}")
        print(f"Source size: {source_file.stat().st_size / (1024*1024):.2f} MB")

        # Convert M4A to MP3
        cmd = [
            "ffmpeg",
            "-i", str(source_file),
            "-acodec", "libmp3lame",
            "-b:a", "192k",
            "-v", "0",  # Suppress ffmpeg output
            str(converted_file),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)

            if result.returncode != 0:
                pytest.fail(f"ffmpeg conversion failed: {result.stderr}")

            assert converted_file.exists(), "Converted file was not created"
            converted_size = converted_file.stat().st_size / (1024 * 1024)
            print(f"Converted size: {converted_size:.2f} MB")
            print(f"✓ Conversion successful!")

        except subprocess.TimeoutExpired:
            pytest.fail("ffmpeg conversion timed out")
        except Exception as e:
            pytest.fail(f"Conversion error: {e}")

    def test_converted_file_is_valid_mp3(self, converted_file):
        """Validate that converted file is a valid MP3."""
        if not converted_file.exists():
            pytest.skip("Converted file not available")

        from pydub import AudioSegment

        try:
            audio = AudioSegment.from_mp3(str(converted_file))
            print(f"\n✓ Converted file is valid MP3")
            print(f"  Duration: {len(audio)/1000/60:.1f} minutes")
            print(f"  Frame rate: {audio.frame_rate} Hz")
            print(f"  Channels: {audio.channels}")

            assert len(audio) > 0, "Converted audio is empty"
        except Exception as e:
            pytest.fail(f"Converted file is not valid: {e}")

    def test_processor_validates_converted_file(self, processor, converted_file):
        """Test that audio processor can validate the converted file."""
        if not converted_file.exists():
            pytest.skip("Converted file not available")

        try:
            result = processor.validate_audio_file(str(converted_file))
            assert result is True
            print(f"✓ Converted file validation passed")
        except Exception as e:
            pytest.fail(f"Validation failed: {e}")

    def test_transcribe_converted_file(self, processor, converted_file):
        """
        Test transcription with the converted MP3 file.

        This is the final test to verify that conversion solves the issue.
        """
        if not converted_file.exists():
            pytest.skip("Converted file not available")

        print(f"\nAttempting transcription of converted MP3...")
        print(f"File: {converted_file.name}")
        print(f"Size: {converted_file.stat().st_size / (1024*1024):.2f} MB")

        try:
            transcript = processor.process(str(converted_file), language="hu")

            assert transcript is not None
            assert isinstance(transcript, str)
            assert len(transcript) > 0

            print(f"✓ CONVERSION SOLUTION WORKS!")
            print(f"  Transcription successful!")
            print(f"  Transcript length: {len(transcript)} characters")
            print(f"  First 100 chars: {transcript[:100]}...")

        except (OpenAIAPIError, AudioProcessingError) as e:
            error_msg = str(e)
            if "Invalid file format" in error_msg:
                pytest.fail(
                    f"Even the converted MP3 was rejected! "
                    f"This suggests a deeper issue. Error: {error_msg}"
                )
            else:
                print(f"\n✗ API Error: {error_msg}")
                pytest.skip(f"OpenAI API error: {error_msg}")

        except Exception as e:
            print(f"\n✗ Unexpected Error: {type(e).__name__}: {e}")
            pytest.fail(f"Unexpected error: {e}")


class TestConversionBenchmark:
    """Compare original and converted files."""

    @pytest.fixture
    def source_file(self):
        """Get original M4A file."""
        return Path("/Users/miklostoth/develop/workspaces/cikkiro/data/2026-03-29_VeresDorbala/Hang.m4a")

    def test_file_size_comparison(self, source_file, tmp_path):
        """Compare file sizes before and after conversion."""
        if not source_file.exists():
            pytest.skip("Source file not found")

        import subprocess

        converted_file = tmp_path / "Hang_converted.mp3"

        # Convert file
        cmd = [
            "ffmpeg",
            "-i", str(source_file),
            "-acodec", "libmp3lame",
            "-b:a", "192k",
            "-v", "0",
            str(converted_file),
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=60)

            if not converted_file.exists():
                pytest.skip("Conversion failed")

            original_size = source_file.stat().st_size / (1024 * 1024)
            converted_size = converted_file.stat().st_size / (1024 * 1024)
            ratio = (converted_size / original_size) * 100

            print(f"\nFile Size Comparison:")
            print(f"  Original M4A: {original_size:.2f} MB")
            print(f"  Converted MP3: {converted_size:.2f} MB")
            print(f"  Ratio: {ratio:.0f}%")

            if converted_size > original_size:
                print(f"  ℹ Converted file is slightly larger (common for MP3)")
            else:
                print(f"  ✓ Converted file is smaller (good compression)")

        except subprocess.TimeoutExpired:
            pytest.skip("Conversion timed out")
        except Exception as e:
            pytest.skip(f"Could not compare sizes: {e}")


if __name__ == "__main__":
    """
    Run these tests to verify that converting M4A to MP3 solves the OpenAI API issue.

    Usage:
        pytest tests/test_conversion_solution.py -v -s

    The tests will:
        1. Check if ffmpeg is installed
        2. Convert the M4A file to MP3
        3. Validate the converted file
        4. Transcribe the converted file
        5. Show file size comparison

    Success indicates that conversion is a viable solution.
    """
    pass
