"""Utility functions for file handling."""
import os
import secrets
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """Check if file extension is allowed.

    Args:
        filename: File name to check

    Returns:
        True if extension is allowed
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_upload(file):
    """Save uploaded file to temp directory.

    Args:
        file: Flask FileStorage object from request.files

    Returns:
        Path: Path to saved file
    """
    # Generate secure filename
    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)

    # Add random string to prevent collisions
    random_str = secrets.token_hex(8)
    filename = f"{name}_{random_str}{ext}"

    # Save file
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = upload_folder / filename

    file.save(str(filepath))

    return filepath


def cleanup_file(filepath):
    """Delete temporary file.

    Args:
        filepath: Path to file to delete
    """
    try:
        if filepath and Path(filepath).exists():
            Path(filepath).unlink()
            current_app.logger.info(f"Cleaned up temp file: {filepath}")
    except Exception as e:
        current_app.logger.warning(f"Failed to cleanup file {filepath}: {e}")
