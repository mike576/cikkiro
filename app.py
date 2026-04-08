"""Application entry point."""
import os

from app import create_app

# Determine environment
config_name = os.environ.get("FLASK_ENV", "production")

# Create app
app = create_app(config_name)

if __name__ == "__main__":
    # For local development only
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
