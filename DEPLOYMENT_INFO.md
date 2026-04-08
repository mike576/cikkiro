# Azure Audio Transcription App - Deployment Information

## 🌐 Application URL

```
http://transcription-app-prod.eastus.azurecontainer.io:8000/
```

**Important:** Port `:8000` is required in the URL

---

## 🔐 Login Credentials

| Field | Value |
|-------|-------|
| **Email** | borbala.veres@gmail.com |
| **Password** | feketemacska |

---

## 📋 Application Overview

**Audio Transcription Web Application**
- Convert M4A and MP3 audio files to text transcripts
- Powered by OpenAI Whisper API
- Automatic M4A to MP3 conversion
- User authentication system
- Cost-optimized Azure Container Instances deployment

---

## 🎯 Features

✅ Audio file upload (M4A, MP3, WAV, WebM)
✅ Real-time transcription via OpenAI Whisper
✅ Automatic format conversion (M4A → MP3)
✅ Maximum file size: 200MB
✅ Multiple language support
✅ Secure user authentication
✅ Copy transcript to clipboard
✅ Download transcript as text file
✅ Character and word count statistics

---

## 💻 How to Use

1. **Access the Application**
   - Go to: `http://transcription-app-prod.eastus.azurecontainer.io:8000/`

2. **Login**
   - Email: `borbala.veres@gmail.com`
   - Password: `feketemacska`

3. **Upload Audio**
   - Click "Choose File" and select your audio file
   - Select language (optional, auto-detects by default)
   - Click "Transcribe"

4. **Get Results**
   - Transcript appears on results page
   - Copy to clipboard or download as text file
   - Upload another file to continue

---

## ☁️ Azure Deployment Details

| Property | Value |
|----------|-------|
| **Resource Group** | rg-transcription-aci |
| **Container Registry** | transcriptionacr5102.azurecr.io |
| **Container Name** | transcription-app |
| **Region** | eastus |
| **CPU** | 1 core |
| **Memory** | 2 GB |
| **Container Runtime** | Azure Container Instances (ACI) |
| **DNS Label** | transcription-app-prod (fixed) |

---

## 💰 Cost Information

| Usage | Monthly Cost |
|-------|--------------|
| 1 hour/day | ~$0.15 |
| 8 hours/day | ~$1.20 |
| 24 hours/day | ~$3.60 |
| **Idle (stopped)** | **$0.00** |

**Hourly Rate:** $0.002/hour
**Always-on Alternative:** App Service costs $13.14/month minimum

---

## ⏸️ Container Management

### Stop Container (Frees Resources)
```bash
az container stop -g rg-transcription-aci -n transcription-app
```
**Cost:** $0 while stopped

### Start Container
```bash
az container start -g rg-transcription-aci -n transcription-app
```

### View Live Logs
```bash
az container logs -g rg-transcription-aci -n transcription-app --follow
```

### Check Status
```bash
az container show \
  -g rg-transcription-aci \
  -n transcription-app \
  --query "{State:instanceView.state, IP:ipAddress.ip, FQDN:ipAddress.fqdn}" \
  --output table
```

### Delete Everything
```bash
az group delete -g rg-transcription-aci --yes
```

---

## 🏗️ Technical Stack

| Component | Technology |
|-----------|------------|
| **Web Framework** | Flask 3.0.2 |
| **Authentication** | Flask-Login 0.6.3 |
| **Audio Processing** | pydub, ffmpeg |
| **AI Service** | OpenAI Whisper API |
| **Form Validation** | Flask-WTF |
| **Security** | Werkzeug (password hashing) |
| **Frontend** | HTML + Tailwind CSS |
| **Server** | Gunicorn 21.2.0 |
| **Container** | Docker (Multi-stage build) |
| **Python Version** | 3.11 |

---

## 📦 Supported Audio Formats

- MP3 (.mp3)
- M4A (.m4a) - Auto-converts to MP3
- WAV (.wav)
- WebM (.webm)
- MP4 (.mp4)
- MPEG (.mpeg)
- MPGA (.mpga)
- OGA (.oga)
- OGG (.ogg)

**Maximum File Size:** 200MB

---

## 🔑 Environment Variables

The container is configured with:
- `OPENAI_API_KEY` - OpenAI API key for Whisper API
- `FLASK_ENV` - Set to "production"
- `SECRET_KEY` - Randomly generated for session security

---

## 📝 Project Files

| File | Purpose |
|------|---------|
| `app.py` | Flask entry point |
| `wsgi.py` | WSGI entry for Gunicorn |
| `Dockerfile` | Multi-stage Docker build |
| `requirements.txt` | Python dependencies |
| `config/settings.py` | Application configuration |
| `app/__init__.py` | Flask app factory |
| `app/routes.py` | Main application routes |
| `app/auth.py` | User authentication |
| `app/auth_routes.py` | Login/logout routes |
| `app/forms.py` | WTForms for input validation |
| `app/utils.py` | File handling utilities |
| `app/templates/` | HTML templates |
| `src/` | Reused code from cikkiro project |

---

## 🚀 Deployment URL (Always Use :8000)

### ✅ Correct
```
http://transcription-app-prod.eastus.azurecontainer.io:8000/
```

### ❌ Incorrect (without port)
```
http://transcription-app-prod.eastus.azurecontainer.io/
```

---

## 📊 Performance Notes

- **Startup Time:** ~5-10 seconds after container starts
- **Transcription Speed:** Depends on audio file size and OpenAI API response time
- **Large Files:** Files >25MB are automatically chunked by OpenAI
- **M4A Conversion:** Takes 2-10 seconds depending on file size

---

## 🛠️ Troubleshooting

### Container Won't Start
```bash
az container logs -g rg-transcription-aci -n transcription-app
```

### Access Denied
- Verify credentials are correct
- Check that port `:8000` is included in URL

### Upload Fails
- Check file format is supported
- Verify file size is under 200MB
- Ensure OpenAI API key is valid

### Transcription Errors
- Check OpenAI API key is active
- Verify audio file quality
- Try converting M4A to MP3 locally first

---

## 📅 Last Updated

- **Deployment Date:** April 5, 2026
- **Status:** ✅ Production Ready
- **URL Status:** ✅ Fixed (no longer changes on redeploy)
- **Credentials:** ✅ Updated and hidden from UI

---

## 📞 Quick Reference

| Need | Command |
|------|---------|
| View logs | `az container logs -g rg-transcription-aci -n transcription-app --follow` |
| Stop app | `az container stop -g rg-transcription-aci -n transcription-app` |
| Start app | `az container start -g rg-transcription-aci -n transcription-app` |
| Check status | `az container show -g rg-transcription-aci -n transcription-app` |

---

**🎉 Your audio transcription application is ready to use!**

Access it at: `http://transcription-app-prod.eastus.azurecontainer.io:8000/`
