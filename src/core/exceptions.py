"""Custom exceptions for the Cikkiro application."""


class CikkiroException(Exception):
    """Base exception for all Cikkiro errors."""
    pass


# Configuration Exceptions
class ConfigurationError(CikkiroException):
    """Raised when configuration loading or validation fails."""
    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration doesn't match the schema."""
    pass


# Gmail Exceptions
class GmailError(CikkiroException):
    """Base exception for Gmail API errors."""
    pass


class GmailAuthenticationError(GmailError):
    """Raised when Gmail authentication fails."""
    pass


class GmailFetchError(GmailError):
    """Raised when fetching emails from Gmail fails."""
    pass


class GmailSendError(GmailError):
    """Raised when sending emails via Gmail fails."""
    pass


class UnauthorizedSenderError(CikkiroException):
    """Raised when email sender is not in whitelist."""
    pass


# Storage Exceptions
class StorageError(CikkiroException):
    """Base exception for Cloud Storage errors."""
    pass


class StorageUploadError(StorageError):
    """Raised when file upload fails."""
    pass


class StorageDownloadError(StorageError):
    """Raised when file download fails."""
    pass


# File Processing Exceptions
class FileProcessingError(CikkiroException):
    """Base exception for file processing errors."""
    pass


class AudioProcessingError(FileProcessingError):
    """Raised when audio processing fails."""
    pass


class AudioValidationError(AudioProcessingError):
    """Raised when audio file validation fails."""
    pass


class TranscriptionError(AudioProcessingError):
    """Raised when audio transcription fails."""
    pass


class DocumentProcessingError(FileProcessingError):
    """Raised when document processing fails."""
    pass


class DocumentValidationError(DocumentProcessingError):
    """Raised when document validation fails."""
    pass


class TextExtractionError(DocumentProcessingError):
    """Raised when text extraction from document fails."""
    pass


class ArticleBankError(FileProcessingError):
    """Raised when article bank operations fail."""
    pass


# API Exceptions
class APIError(CikkiroException):
    """Base exception for API errors."""
    pass


class OpenAIAPIError(APIError):
    """Raised when OpenAI API calls fail."""
    pass


class AnthropicAPIError(APIError):
    """Raised when Anthropic/Claude API calls fail."""
    pass


# Article Generation Exceptions
class ArticleGenerationError(CikkiroException):
    """Raised when article generation fails."""
    pass


class PromptBuildingError(ArticleGenerationError):
    """Raised when prompt building fails."""
    pass


# Rate Limiting Exceptions
class RateLimitError(CikkiroException):
    """Raised when rate limit is exceeded."""
    pass


# Validation Exceptions
class ValidationError(CikkiroException):
    """Raised when input validation fails."""
    pass
