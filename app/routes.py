"""Flask routes for audio transcription."""
import logging
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import RequestEntityTooLarge

from app.forms import AudioUploadForm, AnalysisPromptForm
from app.utils import cleanup_file, save_upload
from src.core.exceptions import (
    AudioProcessingError,
    AudioValidationError,
    OpenAIAPIError,
    TranscriptionError,
)
from src.processors.audio_processor import AudioProcessor
from src.services.openai_service import OpenAIService

bp = Blueprint("main", __name__)

# In-memory storage (replace with Redis/DB in production)
TRANSCRIPTS = {}  # {transcript_id: {transcript, filename, file_size_mb, language, char_count, word_count, created_at}}
ANALYSES = {}     # {analysis_id: {prompt, response, transcript_id, model, created_at}}


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

        # Get language if specified (only pass if non-empty)
        language = form.language.data or None

        # Process audio
        processor = AudioProcessor()

        # Only pass language if specified
        if language:
            transcript = processor.process(str(processing_file), language=language)
        else:
            transcript = processor.process(str(processing_file))

        # Calculate file size for display (use original file size)
        file_size_mb = temp_file.stat().st_size / (1024 * 1024)

        # Generate UUID for transcript
        transcript_id = str(uuid.uuid4())

        # Store transcript data in memory
        TRANSCRIPTS[transcript_id] = {
            'transcript': transcript,
            'filename': original_filename,
            'file_size_mb': f"{file_size_mb:.2f}",
            'language': language or "Auto-detected",
            'char_count': len(transcript),
            'word_count': len(transcript.split()),
            'created_at': datetime.utcnow()
        }

        # Store in session for easy access
        session['current_transcript_id'] = transcript_id
        session.permanent = True

        flash("Transcription completed successfully!", "success")
        return redirect(url_for("main.result", transcript_id=transcript_id))

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


@bp.route("/result/<transcript_id>", methods=["GET"])
@login_required
def result(transcript_id):
    """Display transcript and analysis form.

    Args:
        transcript_id: UUID of the transcript

    Returns:
        Rendered result page with transcript and analysis form
    """
    if transcript_id not in TRANSCRIPTS:
        flash("Transcript not found. Please upload a new file.", "error")
        return redirect(url_for("main.index"))

    transcript_data = TRANSCRIPTS[transcript_id]
    form = AnalysisPromptForm()

    return render_template(
        "result.html",
        transcript=transcript_data['transcript'],
        filename=transcript_data['filename'],
        file_size_mb=transcript_data['file_size_mb'],
        language=transcript_data['language'],
        char_count=transcript_data['char_count'],
        word_count=transcript_data['word_count'],
        transcript_id=transcript_id,
        form=form
    )


@bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """Process transcript analysis with LLM.

    Returns:
        Redirect to analysis page or error
    """
    form = AnalysisPromptForm()

    if not form.validate_on_submit():
        flash("Invalid prompt submission", "error")
        return redirect(url_for("main.index"))

    # Get transcript from form data
    transcript_id = request.form.get('transcript_id')
    if not transcript_id or transcript_id not in TRANSCRIPTS:
        flash("Transcript not found. Please upload a new file.", "error")
        return redirect(url_for("main.index"))

    transcript_data = TRANSCRIPTS[transcript_id]
    user_prompt = form.prompt.data

    try:
        # Call OpenAI Chat Completion API
        openai_service = OpenAIService()
        llm_response = openai_service.generate_chat_completion(
            transcript=transcript_data['transcript'],
            user_prompt=user_prompt,
            model='gpt-5.4'
        )

        # Store analysis
        analysis_id = str(uuid.uuid4())
        ANALYSES[analysis_id] = {
            'prompt': user_prompt,
            'response': llm_response,
            'transcript_id': transcript_id,
            'model': 'gpt-5.4',
            'created_at': datetime.utcnow()
        }

        flash("Analysis completed!", "success")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    except OpenAIAPIError as e:
        current_app.logger.error(f"OpenAI API error: {e}")
        flash(f"OpenAI API error: {str(e)}", "error")
        return redirect(url_for("main.result", transcript_id=transcript_id))
    except Exception as e:
        current_app.logger.error(f"Analysis error: {e}")
        flash(f"Analysis error: {str(e)}", "error")
        return redirect(url_for("main.result", transcript_id=transcript_id))


@bp.route("/analysis/<analysis_id>", methods=["GET"])
@login_required
def analysis(analysis_id):
    """Display analysis result.

    Args:
        analysis_id: UUID of the analysis

    Returns:
        Rendered analysis page
    """
    if analysis_id not in ANALYSES:
        flash("Analysis not found", "error")
        return redirect(url_for("main.index"))

    analysis_data = ANALYSES[analysis_id]
    transcript_id = analysis_data['transcript_id']
    transcript_data = TRANSCRIPTS.get(transcript_id, {})

    return render_template(
        "analysis.html",
        prompt=analysis_data['prompt'],
        response=analysis_data['response'],
        model=analysis_data['model'],
        transcript=transcript_data.get('transcript', ''),
        filename=transcript_data.get('filename', ''),
        transcript_id=transcript_id
    )


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
