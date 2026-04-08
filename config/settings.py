"""Application configuration."""
import os
from pathlib import Path


class Config:
    """Base configuration."""

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max file size
    UPLOAD_FOLDER = Path("/tmp/audio_uploads")

    # OpenAI API
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # Audio processing
    ALLOWED_EXTENSIONS = {"mp3", "m4a", "wav", "webm"}
    DEFAULT_LANGUAGE = None  # Auto-detect

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration."""
        # Create upload folder if it doesn't exist
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration (Azure)."""

    DEBUG = False

    @staticmethod
    def init_app(app):
        Config.init_app(app)

        # Azure-specific logging setup
        import logging

        app.logger.setLevel(logging.INFO)


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
