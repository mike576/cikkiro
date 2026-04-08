# Quick Start Guide

## Local Testing (5 minutes)

### 1. Start the App

```bash
cd /Users/miklostoth/develop/workspaces/azure-transcription-app
source venv/bin/activate
export FLASK_ENV=development
python app.py
```

You'll see:
```
* Running on http://127.0.0.1:5000
```

### 2. Open in Browser

Visit: **http://localhost:5000**

You should see:
- Audio upload form with drag-and-drop
- Language selector (Hungarian, English, Spanish, etc.)
- "Transcribe" button
- Info about supported formats

### 3. Test Upload

Upload one of the sample files from cikkiro:
- `/Users/miklostoth/develop/workspaces/cikkiro/data/260323_152947.mp3` (5.14 MB)
- `/Users/miklostoth/develop/workspaces/cikkiro/data/Hang_260323_152947.m4a` (9.6 MB)

**Result:** You'll see the transcript on the result page with:
- Copy to clipboard button
- Download as text file button
- Word/character count
- Language detected

---

## Azure Deployment (10-15 minutes)

### Prerequisites

1. Azure account with subscription
2. Azure CLI installed: `az --version`
3. OpenAI API key with active billing

### Deploy Steps

```bash
# 1. Login
az login

# 2. Create resource group
az group create --name rg-transcription-app --location eastus

# 3. Create app service plan
az appservice plan create \
  --name plan-transcription-app \
  --resource-group rg-transcription-app \
  --sku B1 --is-linux

# 4. Create web app (replace with unique name)
APP_NAME="transcription-app-$(date +%s)"
az webapp create \
  --name $APP_NAME \
  --resource-group rg-transcription-app \
  --plan plan-transcription-app \
  --runtime "PYTHON:3.11"

# 5. Configure settings
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group rg-transcription-app \
  --settings \
    OPENAI_API_KEY="sk-your-openai-api-key" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)" \
    LOG_LEVEL="INFO"

# 6. Set startup command
az webapp config set \
  --name $APP_NAME \
  --resource-group rg-transcription-app \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 300 --workers 2 app:app"

# 7. Deploy (from project directory)
cd /Users/miklostoth/develop/workspaces/azure-transcription-app
az webapp up --name $APP_NAME --resource-group rg-transcription-app

# 8. Get your public URL
az webapp show --name $APP_NAME --resource-group rg-transcription-app --query defaultHostName -o tsv
```

After ~5-10 minutes, you'll get a URL like:
```
transcription-app-1712282400.azurewebsites.net
```

Visit in browser: `https://transcription-app-1712282400.azurewebsites.net`

---

## File Structure

```
azure-transcription-app/
├── app/                    # Flask application
│   ├── routes.py          # Upload/health endpoints
│   ├── forms.py           # File upload form
│   ├── utils.py           # File handling
│   ├── templates/         # HTML pages
│   │   ├── index.html     # Upload form
│   │   ├── result.html    # Transcript display
│   │   └── base.html      # Layout
│   └── __init__.py        # Flask app factory
│
├── src/                   # Reused from cikkiro
│   ├── processors/audio_processor.py
│   ├── services/openai_service.py
│   ├── core/exceptions.py
│   └── utils/validators.py
│
├── .env                   # Environment variables (with your API key)
├── app.py                 # Entry point
├── requirements.txt       # Dependencies
├── DEPLOYMENT.md          # Full Azure guide
└── README.md              # Full documentation
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:** Activate virtual environment first
```bash
source venv/bin/activate
```

### Issue: Port 5000 already in use

**Solution:** Use different port
```bash
python app.py --port 5001
# Then visit http://localhost:5001
```

### Issue: "OPENAI_API_KEY not found" error

**Solution:** Make sure `.env` is in project root
```bash
# Verify it exists
ls -la /Users/miklostoth/develop/workspaces/azure-transcription-app/.env
```

### Issue: Transcription fails on Azure

**Solution:** Check logs
```bash
az webapp log tail --name your-app-name --resource-group rg-transcription-app
```

Common causes:
1. Wrong OpenAI API key
2. OpenAI quota exceeded (check https://platform.openai.com/account/billing/overview)
3. File too large (>200MB)
4. Unsupported format (use MP3, M4A, WAV, or WebM)

---

## Key Features Tested

✅ Flask app starts without errors
✅ All routes load (/, /upload, /health)
✅ HTML templates render correctly
✅ Tailwind CSS loads via CDN
✅ Upload form with drag-and-drop
✅ Language selector works
✅ Audio processor initializes
✅ OpenAI Whisper API integration ready

---

## Next Steps

1. **Test Locally** - Follow the "Local Testing" section above
2. **Deploy to Azure** - Follow the "Azure Deployment" section
3. **Test in Production** - Upload a file to your Azure URL
4. **Monitor** - Check logs: `az webapp log tail ...`
5. **Scale** - Upgrade to S1 plan if needed for more users

---

## Support

For detailed information, see:
- `DEPLOYMENT.md` - Complete Azure deployment guide
- `README.md` - Features, structure, development
- `app.py` - Flask entry point
- `app/routes.py` - Web request handling

Happy transcribing! 🎉
