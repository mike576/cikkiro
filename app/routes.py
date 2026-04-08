"""Flask routes for audio transcription."""
import logging
import subprocess
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import RequestEntityTooLarge

from app.forms import AudioUploadForm
from app.utils import cleanup_file, save_upload
from src.core.exceptions import (
    AudioProcessingError,
    AudioValidationError,
    OpenAIAPIError,
    TranscriptionError,
)
from src.processors.audio_processor import AudioProcessor

bp = Blueprint("main", __name__)


def convert_m4a_to_mp3(m4a_path):
    """Convert M4A file to MP3 using ffmpeg.

    Args:
        m4a_path: Path to M4A file

    Returns:
        Path to converted MP3 file

    Raises:
        Exception: If conversion fails
    """
    m4a_file = Path(m4a_path)
    mp3_file = m4a_file.with_suffix('.mp3')

    try:
        current_app.logger.info(f"Converting M4A to MP3: {m4a_file.name}")

        # Use ffmpeg to convert
        cmd = [
            'ffmpeg',
            '-i', str(m4a_file),
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-v', '0',  # Suppress output
            str(mp3_file)
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=300, text=True)

        if result.returncode != 0:
            raise Exception(f"ffmpeg conversion failed: {result.stderr}")

        if not mp3_file.exists():
            raise Exception("Converted MP3 file was not created")

        current_app.logger.info(f"Conversion successful: {m4a_file.name} → {mp3_file.name}")
        return mp3_file

    except subprocess.TimeoutExpired:
        raise Exception("M4A conversion timed out (file too large)")
    except FileNotFoundError:
        raise Exception(
            "ffmpeg not found. Install it with: brew install ffmpeg (macOS) "
            "or apt-get install ffmpeg (Linux)"
        )
    except Exception as e:
        current_app.logger.error(f"M4A conversion error: {e}")
        raise


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Main upload page.

    Returns:
        Rendered template for upload form
    """
    form = AudioUploadForm()

    if form.validate_on_submit():
        return redirect(url_for("main.upload"))

    return render_template("index.html", form=form)


@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Handle file upload and transcription.

    Automatically converts M4A files to MP3 for compatibility with OpenAI API.

    Returns:
        Rendered result page with transcript or error page
    """
    form = AudioUploadForm()

    if not form.validate_on_submit():
        return (
            render_template("index.html", form=form, error="Invalid file or form submission"),
            400,
        )

    temp_file = None
    converted_file = None

    try:
        # Save uploaded file
        file = form.audio_file.data
        temp_file = save_upload(file)

        current_app.logger.info(f"Processing upload: {file.filename} ({temp_file})")

        # Convert M4A to MP3 if necessary (OpenAI API compatibility)
        processing_file = temp_file
        original_filename = file.filename

        if file.filename.lower().endswith('.m4a'):
            try:
                current_app.logger.info(f"M4A file detected, converting to MP3...")
                converted_file = convert_m4a_to_mp3(temp_file)
                processing_file = converted_file

                # Show user that conversion happened
                flash(
                    "✓ M4A file automatically converted to MP3 for optimal compatibility",
                    "info"
                )
            except Exception as conversion_error:
                current_app.logger.error(f"M4A conversion failed: {conversion_error}")
                flash(
                    f"M4A conversion failed: {str(conversion_error)}. "
                    f"Please try uploading as MP3 instead.",
                    "error"
                )
                return render_template("index.html", form=form), 500

        # Get language if specified
        language = form.language.data if form.language.data else None

        # Process audio
        processor = AudioProcessor()
        transcript = processor.process(str(processing_file), language=language)

        # Calculate file size for display (use original file size)
        file_size_mb = temp_file.stat().st_size / (1024 * 1024)

        return render_template(
            "result.html",
            transcript=transcript,
            filename=original_filename,
            file_size_mb=f"{file_size_mb:.2f}",
            language=language or "Auto-detected",
        )

    except AudioValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        flash(f"Validation error: {str(e)}", "error")
        return render_template("index.html", form=form), 400

    except OpenAIAPIError as e:
        current_app.logger.error(f"OpenAI API error: {e}")
        flash(f"Transcription service error: {str(e)}", "error")
        return render_template("index.html", form=form), 500

    except TranscriptionError as e:
        current_app.logger.error(f"Transcription error: {e}")
        flash(f"Transcription failed: {str(e)}", "error")
        return render_template("index.html", form=form), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return render_template("index.html", form=form), 500

    finally:
        # Always cleanup temp files
        if temp_file:
            cleanup_file(temp_file)
        if converted_file:
            cleanup_file(converted_file)


@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Azure.

    Returns:
        JSON response with health status
    """
    return jsonify({"status": "healthy"}), 200


@bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size limit errors.

    Args:
        e: The exception

    Returns:
        Rendered index page with error message
    """
    flash("File too large. Maximum size is 200MB.", "error")
    return render_template("index.html", form=AudioUploadForm()), 413
