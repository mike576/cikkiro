"""Input validation utilities for the Cikkiro application."""

import re
from typing import Optional

from src.core.constants import (
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_DOCUMENT_FORMATS,
    MAX_AUDIO_SIZE_MB,
    MAX_DOCUMENT_SIZE_MB,
)
from src.core.exceptions import ValidationError


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid

    Raises:
        ValidationError: If email format is invalid
    """
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")

    return True


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate file extension against allowed list.

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed file extensions (without dots)

    Returns:
        True if file extension is allowed

    Raises:
        ValidationError: If file extension is not allowed
    """
    if "." not in filename:
        raise ValidationError(f"File has no extension: {filename}")

    extension = filename.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise ValidationError(
            f"File extension '{extension}' not in allowed list: {allowed_extensions}"
        )

    return True


def validate_audio_file(filename: str, file_size_bytes: int) -> bool:
    """
    Validate audio file format and size.

    Args:
        filename: Audio filename
        file_size_bytes: File size in bytes

    Returns:
        True if file is valid

    Raises:
        ValidationError: If file is invalid
    """
    # Check extension
    validate_file_extension(filename, SUPPORTED_AUDIO_FORMATS)

    # Check size
    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > MAX_AUDIO_SIZE_MB:
        raise ValidationError(
            f"Audio file exceeds maximum size of {MAX_AUDIO_SIZE_MB}MB. "
            f"Current size: {file_size_mb:.2f}MB"
        )

    return True


def validate_document_file(filename: str, file_size_bytes: int) -> bool:
    """
    Validate document file format and size.

    Args:
        filename: Document filename
        file_size_bytes: File size in bytes

    Returns:
        True if file is valid

    Raises:
        ValidationError: If file is invalid
    """
    # Check extension
    validate_file_extension(filename, SUPPORTED_DOCUMENT_FORMATS)

    # Check size
    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > MAX_DOCUMENT_SIZE_MB:
        raise ValidationError(
            f"Document file exceeds maximum size of {MAX_DOCUMENT_SIZE_MB}MB. "
            f"Current size: {file_size_mb:.2f}MB"
        )

    return True


def validate_non_empty_string(value: str, field_name: str = "value") -> bool:
    """
    Validate that a string is non-empty.

    Args:
        value: String to validate
        field_name: Name of the field for error messages

    Returns:
        True if string is non-empty

    Raises:
        ValidationError: If string is empty
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")

    return True


def validate_positive_integer(
    value: int,
    field_name: str = "value",
    min_value: Optional[int] = None,
) -> bool:
    """
    Validate that a value is a positive integer.

    Args:
        value: Integer to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (optional)

    Returns:
        True if value is valid

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer")

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{field_name} must be at least {min_value}, got {value}"
        )

    return True


def validate_model_name(model_name: str) -> bool:
    """
    Validate Claude model name format.

    Args:
        model_name: Model name to validate

    Returns:
        True if model name is valid

    Raises:
        ValidationError: If model name is invalid
    """
    # Check for common Claude model patterns
    valid_patterns = [
        r"^claude-3-[a-z]+-\d{8}$",  # claude-3-sonnet-20240229
        r"^claude-\d+(\.\d+)?$",  # claude-2, claude-2.1
    ]

    if not any(re.match(pattern, model_name) for pattern in valid_patterns):
        raise ValidationError(f"Invalid Claude model name: {model_name}")

    return True
