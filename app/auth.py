"""User authentication module."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# Hardcoded users (for simple authentication)
# In production, use a database
USERS = {
    "borbala.veres@gmail.com": {
        "password_hash": generate_password_hash("feketemacska"),
        "name": "Borbála Veres"
    },
    "miklos.toth83@gmail.com": {
        "password_hash": generate_password_hash("feketemacska"),
        "name": "Miklos Toth"
    }
}


class User(UserMixin):
    """User model for Flask-Login."""

    def __init__(self, email):
        """Initialize user.

        Args:
            email: User email address
        """
        self.id = email
        self.email = email
        if email in USERS:
            self.name = USERS[email].get("name", email)
        else:
            self.name = email

    @staticmethod
    def get(email):
        """Get user by email.

        Args:
            email: User email

        Returns:
            User object if exists, None otherwise
        """
        if email in USERS:
            return User(email)
        return None

    @staticmethod
    def authenticate(email, password):
        """Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            User object if authentication successful, None otherwise
        """
        user_data = USERS.get(email)
        if user_data and check_password_hash(user_data["password_hash"], password):
            return User(email)
        return None
