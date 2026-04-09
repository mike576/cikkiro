"""Flask application factory."""
import sys
import logging
from pathlib import Path

from flask import Flask
from flask_login import LoginManager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for startup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from config.settings import config
    logger.info("✓ config.settings imported")
except Exception as e:
    logger.error(f"✗ Failed to import config.settings: {e}")
    raise


def create_app(config_name="default"):
    """Create Flask application.

    Args:
        config_name: Configuration name ('development', 'production', or 'default')

    Returns:
        Flask application instance
    """
    logger.info(f"Creating app with config: {config_name}")

    app = Flask(__name__)

    # Load configuration
    try:
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        logger.info("✓ Configuration loaded")
    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        raise

    # Initialize Flask-Login
    try:
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = "auth.login"
        login_manager.login_message = "Please log in to access this page."
        login_manager.login_message_category = "info"

        @login_manager.user_loader
        def load_user(user_id):
            """Load user by ID."""
            from app.auth import User
            return User.get(user_id)

        logger.info("✓ Flask-Login initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Flask-Login: {e}")
        raise

    # Register blueprints
    try:
        from app import routes
        logger.info("✓ routes imported")
        app.register_blueprint(routes.bp)
        logger.info("✓ routes blueprint registered")
    except Exception as e:
        logger.error(f"✗ Failed to import/register routes: {e}", exc_info=True)
        raise

    try:
        from app import auth_routes
        logger.info("✓ auth_routes imported")
        app.register_blueprint(auth_routes.bp)
        logger.info("✓ auth_routes blueprint registered")
    except Exception as e:
        logger.error(f"✗ Failed to import/register auth_routes: {e}", exc_info=True)
        raise

    # Load application version
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            app.version = version_file.read_text().strip()
        else:
            app.version = "1.0.0"
        logger.info(f"✓ Application version: {app.version}")
    except Exception as e:
        logger.error(f"✗ Failed to load version: {e}")
        app.version = "unknown"

    # Make version available to templates
    @app.context_processor
    def inject_version():
        return {"app_version": app.version}

    logger.info("✓ App created successfully")
    return app
