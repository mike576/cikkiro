"""Flask-WTF forms for file upload and authentication."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import EmailField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional, Length


class LoginForm(FlaskForm):
    """User login form."""

    email = EmailField(
        "Email",
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Invalid email address"),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required")],
    )

    submit = SubmitField("Login")


class AudioUploadForm(FlaskForm):
    """Audio file upload form."""

    audio_file = FileField(
        "Audio File",
        validators=[
            FileRequired(message="Please select an audio file"),
            FileAllowed(
                ["mp3", "m4a", "wav", "webm"],
                message="Only MP3, M4A, WAV, and WebM files are allowed",
            ),
        ],
    )

    language = SelectField(
        "Language (Optional)",
        choices=[
            ("", "Auto-detect"),
            ("en", "English"),
            ("hu", "Hungarian"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("pl", "Polish"),
            ("tr", "Turkish"),
        ],
        validators=[Optional()],
        default="",
    )

    submit = SubmitField("Transcribe")


class AnalysisPromptForm(FlaskForm):
    """Form for LLM analysis with user prompt."""

    prompt = TextAreaField(
        "Analysis Prompt",
        validators=[
            DataRequired(message="Please enter a prompt"),
            Length(
                min=10,
                max=2000,
                message="Prompt must be 10-2000 characters",
            ),
        ],
        render_kw={
            "placeholder": "E.g., Summarize this transcript in 3 bullet points...",
            "rows": 4,
        },
    )

    submit = SubmitField("Analyze with AI")
