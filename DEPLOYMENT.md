# Azure Deployment Guide

## Overview

This guide provides step-by-step instructions to deploy the Audio Transcription Web App to Azure App Service.

## Prerequisites

1. **Azure CLI** - [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Azure Subscription** - Active Azure account
3. **OpenAI API Key** - Get one from [OpenAI API Keys](https://platform.openai.com/api-keys)
4. **Git** (optional but recommended for source control)

## Azure Resources

The deployment will create these resources:

- **Resource Group:** `rg-transcription-app`
- **App Service Plan:** B1 (Basic) - ~$13.14/month, 1.75GB RAM
- **Web App:** Python 3.11 runtime
- **Total Monthly Cost:** ~$50-100/month (including OpenAI Whisper API usage)

## Deployment Steps

### Step 1: Login to Azure

```bash
az login
```

This opens your browser for authentication. After login, you'll see your subscriptions listed.

### Step 2: Create a Resource Group

Choose your region (e.g., `eastus`, `westus2`, `northeurope`):

```bash
az group create \
  --name rg-transcription-app \
  --location eastus
```

**Note:** Replace `eastus` with your preferred region.

### Step 3: Create an App Service Plan

```bash
az appservice plan create \
  --name plan-transcription-app \
  --resource-group rg-transcription-app \
  --sku B1 \
  --is-linux
```

### Step 4: Create the Web App

Choose a globally unique name for your app (e.g., `transcription-app-12345`):

```bash
az webapp create \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --plan plan-transcription-app \
  --runtime "PYTHON:3.11"
```

**Important:** Replace `transcription-app-12345` with your unique app name. This will be part of your public URL.

### Step 5: Configure Application Settings

```bash
# Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)

# Set environment variables
az webapp config appsettings set \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --settings \
    OPENAI_API_KEY="sk-your-openai-api-key-here" \
    FLASK_ENV="production" \
    SECRET_KEY="$SECRET_KEY" \
    LOG_LEVEL="INFO"
```

**Important:** Replace `sk-your-openai-api-key-here` with your actual OpenAI API key.

### Step 6: Configure the Startup Command

```bash
az webapp config set \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 300 --workers 2 app:app"
```

**Explanation:**
- `--timeout 300` - 5 minutes timeout for large file processing
- `--workers 2` - 2 worker processes (suitable for B1 plan)
- `--bind 0.0.0.0:8000` - Azure requires port 8000
- `app:app` - Flask app instance (app.py, create_app())

### Step 7: Deploy the Application

Navigate to the project root directory and run:

```bash
cd /path/to/azure-transcription-app

az webapp up \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --runtime "PYTHON:3.11"
```

This command:
1. Detects the runtime and creates a `.deployment` file
2. Builds the Python environment
3. Installs dependencies from `requirements.txt`
4. Deploys to Azure

**Note:** This may take 5-10 minutes.

### Step 8: Verify Deployment

Get your app URL:

```bash
az webapp show \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --query defaultHostName \
  --output tsv
```

This returns: `transcription-app-12345.azurewebsites.net`

Test the health endpoint:

```bash
curl https://transcription-app-12345.azurewebsites.net/health
```

Expected response:
```json
{"status": "healthy"}
```

### Step 9: Access Your Application

Open your browser and go to:
```
https://transcription-app-12345.azurewebsites.net
```

You should see the audio transcription upload page!

## Monitoring and Logs

### View Real-time Logs

```bash
az webapp log tail \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --lines 50
```

### View Deployment Logs

```bash
az webapp log deployment show \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app
```

### Configure Log Level

```bash
az webapp config appsettings set \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --settings LOG_LEVEL="DEBUG"
```

## Updating the Application

After making changes to your code:

```bash
# Navigate to project directory
cd /path/to/azure-transcription-app

# Deploy updated code
az webapp up \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app
```

## Scaling Up (If Needed)

If you encounter performance issues, scale to S1 plan:

```bash
# Scale the App Service Plan
az appservice plan update \
  --name plan-transcription-app \
  --resource-group rg-transcription-app \
  --sku S1
```

**S1 Benefits:**
- 1.75 GB → 1.75 GB RAM (same)
- Better CPU performance
- Autoscaling available
- Cost: ~$75/month

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause:** Application crash or startup failure

**Solution:**
```bash
# Check logs
az webapp log tail --name transcription-app-12345 \
  --resource-group rg-transcription-app

# Check startup file is correct
az webapp config show --name transcription-app-12345 \
  --resource-group rg-transcription-app
```

### Issue: OPENAI_API_KEY Not Found

**Solution:**
```bash
# Verify setting is set
az webapp config appsettings list \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app | grep OPENAI_API_KEY

# Re-set the key if missing
az webapp config appsettings set \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --settings OPENAI_API_KEY="sk-your-key-here"
```

### Issue: Request Timeout (Large Files)

The startup command has a 300-second (5-minute) timeout, which should handle files up to 1-2 hours of audio.

If needed, increase timeout:

```bash
az webapp config set \
  --name transcription-app-12345 \
  --resource-group rg-transcription-app \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 app:app"
```

### Issue: File Upload Fails

Check:
1. File size is < 200MB
2. File format is MP3, M4A, WAV, or WebM
3. OPENAI_API_KEY is set correctly
4. Check logs: `az webapp log tail --name transcription-app-12345 ...`

## Cleaning Up (Delete Resources)

To remove all Azure resources and avoid charges:

```bash
# Delete the entire resource group
az group delete \
  --name rg-transcription-app \
  --yes --no-wait
```

## Cost Management

### Monitor Costs

```bash
# View resource costs (if Cost Management is enabled)
az costmanagement query --name "rg-transcription-app"
```

### Set Budget Alerts

1. Go to [Azure Portal](https://portal.azure.com)
2. Search "Budgets"
3. Create a budget for `rg-transcription-app`
4. Set alert threshold (e.g., $50/month)

### Cost Breakdown

- **Azure App Service B1:** $13.14/month
- **OpenAI Whisper API:** $0.006/minute of audio
  - Example: 100 hours/month = $36
  - **Total:** ~$50/month

## Next Steps

### For Production:

1. **Enable HTTPS:** Already enabled by default on azurewebsites.net
2. **Custom Domain:** Add your own domain (optional)
3. **Application Insights:** Enable monitoring and diagnostics
4. **Azure Key Vault:** Store secrets more securely
5. **CI/CD Pipeline:** Set up GitHub Actions for automatic deployments

### Feature Enhancements:

1. **Azure Blob Storage** - Persist transcripts and files
2. **Azure Functions** - Async background processing
3. **User Authentication** - Azure AD B2C
4. **Database** - Azure SQL for user accounts and history
5. **API Analytics** - Track usage patterns

## Support

For issues:

1. Check Azure Portal → App Service → Logs
2. Review troubleshooting section above
3. Check OpenAI API status: https://status.openai.com
4. Review Flask/Gunicorn logs

---

**Deployment Version:** 1.0
**Last Updated:** 2026-04-04
**Azure CLI Version Required:** 2.50.0+
