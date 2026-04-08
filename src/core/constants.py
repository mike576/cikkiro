"""Application constants and configuration defaults."""

# Supported file formats
SUPPORTED_AUDIO_FORMATS = ["mp3", "wav", "m4a", "webm"]
SUPPORTED_DOCUMENT_FORMATS = ["pdf", "docx"]

# File size limits (in MB)
# Note: OpenAI Whisper API has a 25MB limit, but our service will
# automatically split larger files into chunks for processing
MAX_AUDIO_SIZE_MB = 200
MAX_DOCUMENT_SIZE_MB = 10

# Storage bucket names (can be overridden by config)
CONFIG_BUCKET = "cikkiro-config"
ARTICLE_BANK_BUCKET = "cikkiro-article-banks"
TEMP_BUCKET = "cikkiro-temp"
PROCESSED_BUCKET = "cikkiro-processed"

# Default configuration file name
DEFAULT_CONFIG_FILE = "config.json"

# Article bank settings
DEFAULT_ARTICLE_BANK_SIZE = 5
MIN_ARTICLES_FOR_STYLE = 3

# Processing settings
DEFAULT_CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.7

# Gmail settings
DEFAULT_PROCESSED_LABEL = "cikkiro/processed"
DEFAULT_ERROR_LABEL = "cikkiro/error"

# Email checking settings
DEFAULT_EMAIL_CHECK_INTERVAL_MINUTES = 5
DEFAULT_MAX_EMAILS_PER_CHECK = 10

# Timeout settings (in seconds)
EMAIL_CHECKER_TIMEOUT = 60
ARTICLE_GENERATOR_TIMEOUT = 540

# Logging settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
