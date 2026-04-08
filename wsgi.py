"""WSGI entry point for Gunicorn."""
import os
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def application(environ, start_response):
    """WSGI application entry point."""
    # Import here to debug
    try:
        from app import create_app
        config_name = os.environ.get("FLASK_ENV", "production")
        app = create_app(config_name)
        return app(environ, start_response)
    except Exception as e:
        print(f"WSGI Error: {e}")
        import traceback
        traceback.print_exc()
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [b'App failed to load. Check logs.']

# For direct imports by gunicorn
if __name__ != '__main__':
    try:
        from app import create_app
        config_name = os.environ.get("FLASK_ENV", "production")
        app = create_app(config_name)
    except Exception as e:
        print(f"Import Error: {e}")
        import traceback
        traceback.print_exc()
