# Audio Transcription Web App

A Flask-based web application that converts M4A and MP3 audio files to text transcripts using OpenAI's Whisper API. Deployable to Azure App Service.

## Features

- **Easy Upload Interface** - Drag-and-drop or click to upload audio files
- **Multiple Format Support** - MP3, M4A, WAV, WebM
- **Large File Handling** - Automatically chunks files >25MB
- **Language Detection** - Auto-detects language or specify manually
- **AI-Powered Analysis** - Analyze transcripts using OpenAI's GPT-5.4 model
  - Ask questions about the transcript
  - Generate summaries and insights
  - Multi-prompt support for the same transcript
- **One-Click Download** - Download transcripts as text files
- **Production Ready** - Error handling, validation, security

## Tech Stack

- **Frontend:** HTML5, Tailwind CSS, JavaScript
- **Backend:** Flask, Python 3.11
- **Audio Processing:** pydub, OpenAI Whisper API
- **Deployment:** Azure App Service, Gunicorn

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys)

### Setup

1. **Clone/Download this project**

```bash
cd azure-transcription-app
```

2. **Create virtual environment**

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Run the application**

```bash
export FLASK_ENV=development
python app.py
```

6. **Open in browser**

```
http://localhost:5000
```

## Testing

### With Sample Audio Files

The application includes test audio files:
- `/Users/miklostoth/develop/workspaces/cikkiro/data/260323_152947.mp3` (5.1 MB)
- `/Users/miklostoth/develop/workspaces/cikkiro/data/Hang_260323_152947.m4a` (9.6 MB)

Test with:
1. Open http://localhost:5000
2. Upload a test file
3. Choose language (or leave as auto-detect)
4. Click "Transcribe"
5. View results, copy, or download

### Run Unit Tests

```bash
pytest tests/
```

### Test Large Files

Create a test file >25MB to test chunking:

```bash
# Create 30MB test file
dd if=/dev/zero bs=1M count=30 of=test-30mb.mp3
```

The app will automatically split it into 20MB chunks and transcribe.

## Project Structure

```
azure-transcription-app/
├── app/                      # Flask application
│   ├── __init__.py          # App factory
│   ├── routes.py            # Web routes
│   ├── forms.py             # WTForms
│   ├── utils.py             # Helpers
│   ├── templates/           # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── result.html
│   │   └── analysis.html    # LLM analysis results
│   └── static/              # CSS, JS
│
├── src/                      # Reused from cikkiro
│   ├── core/
│   │   ├── constants.py
│   │   └── exceptions.py
│   ├── processors/
│   │   └── audio_processor.py
│   ├── services/
│   │   └── openai_service.py
│   └── utils/
│       ├── validators.py
│       └── logger.py
│
├── config/
│   └── settings.py          # Configuration
│
├── tests/                   # Test files
├── app.py                   # Entry point
├── requirements.txt         # Dependencies
├── runtime.txt              # Python version
├── DEPLOYMENT.md            # Azure deployment guide
└── README.md                # This file
```

## API Endpoints

### GET /

Upload page with form.

### POST /upload

Process uploaded audio file.

**Form Data:**
- `audio_file` (required) - Audio file (MP3, M4A, WAV, WebM)
- `language` (optional) - Language code (en, hu, es, etc.)

**Response:**
- Success: Returns HTML page with transcript
- Error: Returns error message and form

### GET /result/<transcript_id>

Display transcript with analysis form.

**Parameters:**
- `transcript_id` (URL param) - UUID of the transcript

**Response:**
- Returns HTML page with transcript and analysis prompt form

### POST /analyze

Submit transcript for LLM analysis with user prompt.

**Form Data:**
- `prompt` (required) - Analysis prompt (10-2000 characters)

**Response:**
- Success: Redirects to `/analysis/<analysis_id>` with results
- Error: Returns error message and redirects to result page

### GET /analysis/<analysis_id>

Display LLM analysis results.

**Parameters:**
- `analysis_id` (URL param) - UUID of the analysis

**Response:**
- Returns HTML page with:
  - User's prompt
  - AI-generated response
  - Collapsible original transcript
  - Links to try another prompt or upload new file

### GET /health

Health check endpoint (used by Azure).

**Response:**
```json
{"status": "healthy"}
```

## Configuration

Environment variables (set in `.env` or Azure App Settings):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | `production` | Flask environment |
| `SECRET_KEY` | Yes | None | Flask secret key (set random value in production) |
| `OPENAI_API_KEY` | Yes | None | OpenAI API key |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MAX_CONTENT_LENGTH` | No | 200MB | Max file size |

## Deployment

### Azure App Service

Full deployment guide: See [DEPLOYMENT.md](./DEPLOYMENT.md)

Quick deployment:

```bash
# Prerequisites: Azure CLI installed and logged in
az login

# Create resource group
az group create --name rg-transcription-app --location eastus

# Create app service plan
az appservice plan create \
  --name plan-transcription-app \
  --resource-group rg-transcription-app \
  --sku B1 --is-linux

# Create web app
az webapp create \
  --name transcription-app-unique-name \
  --resource-group rg-transcription-app \
  --plan plan-transcription-app \
  --runtime "PYTHON:3.11"

# Configure settings
az webapp config appsettings set \
  --name transcription-app-unique-name \
  --resource-group rg-transcription-app \
  --settings OPENAI_API_KEY="sk-your-key" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)"

# Set startup command
az webapp config set \
  --name transcription-app-unique-name \
  --resource-group rg-transcription-app \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 300 --workers 2 app:app"

# Deploy
az webapp up --name transcription-app-unique-name \
  --resource-group rg-transcription-app
```

## Cost

### Local Development
- Free

### Azure Deployment
- **App Service:** $13.14/month (B1 plan)
- **OpenAI Whisper:** $0.006/minute of audio
  - 10 hours/month = $3.60
  - 100 hours/month = $36
- **Total:** ~$50-100/month (depending on usage)

## Security

✅ **Implemented:**
- CSRF protection (Flask-WTF)
- Secure filename handling
- File extension validation
- File size limits (200MB max)
- API key encryption (Azure App Settings)
- Temporary file cleanup

⚠️ **Production Recommendations:**
- Use Azure Key Vault for secrets
- Enable Application Insights for monitoring
- Add rate limiting (Flask-Limiter)
- Enable HTTPS (default on Azure)
- Regular security updates

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"

**Solution:** Set environment variable:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or in `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Audio validation failed: Unsupported audio format"

**Solution:** Ensure file is MP3, M4A, WAV, or WebM format.

### Issue: Request Timeout

**Cause:** Large file or slow connection

**Solution:**
- Split file into smaller chunks
- Increase timeout in Gunicorn startup command (see DEPLOYMENT.md)

### Issue: 502 Bad Gateway (Azure)

**Solution:**
1. Check logs: `az webapp log tail ...`
2. Verify OPENAI_API_KEY is set
3. Ensure startup command is correct
4. Restart app: `az webapp restart ...`

## Development

### Adding New Languages

Edit `app/forms.py`:

```python
language = SelectField(
    "Language (Optional)",
    choices=[
        ("", "Auto-detect"),
        ("en", "English"),
        ("hu", "Hungarian"),
        # Add more here:
        ("ja", "Japanese"),
    ],
)
```

### Modifying Styling

Edit Tailwind CSS in templates:
- `app/templates/base.html` - Main styles
- `app/templates/index.html` - Upload form
- `app/templates/result.html` - Results

### Adding Features

Key components to modify:
- `app/routes.py` - Add routes here
- `app/templates/` - Add HTML templates
- `app/forms.py` - Add form fields
- `requirements.txt` - Add dependencies

## Future Enhancements

### Completed Features
- [x] AI-Powered Analysis (GPT-5.4 integration)
- [x] Version management system

### Planned Features
- [ ] User authentication and transcript history
- [ ] Database integration (PostgreSQL) to replace in-memory storage
- [ ] User-specific transcript management
- [ ] Translation to other languages
- [ ] Speaker diarization
- [ ] Export to PDF/DOCX
- [ ] Batch upload
- [ ] Real-time progress updates (WebSocket)
- [ ] Transcript search and filtering
- [ ] Rate limiting per user
- [ ] Analytics dashboard

## License

This project reuses components from the [cikkiro](https://github.com/miklos-toth/cikkiro) project.

## Support

For issues, feature requests, or improvements:

1. Check [DEPLOYMENT.md](./DEPLOYMENT.md) for Azure-specific issues
2. Review logs: `az webapp log tail ...` (Azure)
3. Check [OpenAI Status](https://status.openai.com)
4. Test with sample files first

---

**Created:** 2026-04-04
**Last Updated:** 2026-04-09
**Current Version:** 1.0.7
**Status:** Production Ready
**Python Version:** 3.11+
**Framework:** Flask 3.0.2

See [CHANGELOG.md](./CHANGELOG.md) for version history and detailed changes.
