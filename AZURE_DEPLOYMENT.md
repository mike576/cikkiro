# Azure Deployment Guide - Cost-Optimized with Container Instances

## Overview

This guide deploys the Audio Transcription app to **Azure Container Instances (ACI)**, which offers true pay-per-use pricing:

- **No idle charges** - You only pay when the container is running
- **Auto-scaling** - Scale down to 0 when not in use
- **Start on demand** - Containers start when needed
- **Estimated cost:** $0-5/month (with light usage) vs $13+/month for App Service

---

## Architecture

```
Your Computer
    ↓
Docker Container (locally built)
    ↓
Azure Container Registry (image storage)
    ↓
Azure Container Instances (run containers on demand)
    ↓
Public IP (accessible via HTTPS)
```

---

## Prerequisites

1. **Azure CLI** - [Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Docker Desktop** - [Install](https://www.docker.com/products/docker-desktop)
3. **Azure Subscription** - Active account with credits
4. Logged into Azure: `az login`

---

## Step 1: Create Azure Resources (One-time)

```bash
# Set variables
RESOURCE_GROUP="rg-transcription-aci"
ACR_NAME="transcriptionacr$(date +%s | tail -c 6)"  # Unique name
LOCATION="eastus"

# 1. Create Resource Group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# 2. Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic

# 3. Get registry credentials
az acr credential show \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME

# Save the username and password from output!
```

**Save the credentials:**
- Registry name: `$ACR_NAME.azurecr.io`
- Username: `(from credential output)`
- Password: `(from credential output)`

---

## Step 2: Build and Push Docker Image

```bash
# Set your ACR name
ACR_NAME="yourregistryname"
ACR_URL="${ACR_NAME}.azurecr.io"
IMAGE_NAME="audio-transcription"
IMAGE_TAG="latest"

# Navigate to project directory
cd /Users/miklostoth/develop/workspaces/azure-transcription-app

# 1. Build Docker image locally
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# 2. Tag for Azure Container Registry
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ACR_URL}/${IMAGE_NAME}:${IMAGE_TAG}

# 3. Login to ACR (use credentials from Step 1)
az acr login --name $ACR_NAME

# 4. Push image to registry
docker push ${ACR_URL}/${IMAGE_NAME}:${IMAGE_TAG}

# Verify push
az acr repository list --name $ACR_NAME
```

---

## Step 3: Deploy Container Instance

```bash
# Set variables
RESOURCE_GROUP="rg-transcription-aci"
ACR_NAME="yourregistryname"
ACR_URL="${ACR_NAME}.azurecr.io"
IMAGE_NAME="audio-transcription:latest"
CONTAINER_NAME="transcription-app"
CONTAINER_PORT=8000

# Get ACR credentials
REGISTRY_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Deploy Container Instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image ${ACR_URL}/${IMAGE_NAME} \
  --cpu 1 \
  --memory 2 \
  --ports $CONTAINER_PORT \
  --environment-variables \
    OPENAI_API_KEY="sk-your-openai-api-key-here" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)" \
  --registry-login-server $ACR_URL \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --restart-policy OnFailure \
  --dns-name-label transcription-app-$(date +%s | tail -c 6)

# Get public IP and URL
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query ipAddress.fqdn \
  --output tsv
```

Your app is now accessible at the FQDN returned above!

---

## Step 4: Minimize Costs - Auto-Stop on Idle

### Option A: Manual Start/Stop (Cheapest)

Stop when not using:
```bash
az container stop \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME

# Restart when needed
az container start \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME
```

**Cost:** Only when running (~$0.002/hour = ~$1.50/month if 24/7)

### Option B: Scheduled Stop/Start

```bash
# Create automation account for scheduling
az automation account create \
  --resource-group $RESOURCE_GROUP \
  --name "transcription-automation"

# Create runbook to stop container at specific times
# Example: Stop at 6 PM, Start at 9 AM on weekdays
```

### Option C: Azure Logic App (Event-Based)

Create a Logic App that:
1. Starts container on HTTP request
2. Stops container after 30 minutes of inactivity

---

## Step 5: Monitor and Manage

### View Logs
```bash
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --follow
```

### Check Status
```bash
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query "{
    State:instanceView.state,
    IP:ipAddress.ip,
    FQDN:ipAddress.fqdn,
    CPUUsage:instanceView.events[0].description
  }" \
  --output table
```

### Update Environment Variables
```bash
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image ${ACR_URL}/${IMAGE_NAME} \
  # ... (repeat all options from Step 3)
```

---

## Cost Breakdown

### Azure Container Instances Pricing

| Usage | Cost |
|-------|------|
| 1 hour/day | ~$0.15/month |
| 8 hours/day | ~$1.20/month |
| 24 hours/day | ~$3.60/month |
| CPU & Memory | Included above |
| Data transfer | Minimal (included in free tier) |

### vs App Service Always-On

| Service | Cost |
|---------|------|
| App Service (B1) | $13.14/month (always running) |
| Container Instances | $0-5/month (pay-per-use) |
| **Monthly Savings** | **$8-13/month** |

---

## Deployment Script (Automated)

Save as `deploy-to-aci.sh`:

```bash
#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="rg-transcription-aci"
ACR_NAME="transcriptionacr"
IMAGE_NAME="audio-transcription"
CONTAINER_NAME="transcription-app"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Validate
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable not set"
    exit 1
fi

# Build
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# Tag
echo "🏷️  Tagging image..."
docker tag ${IMAGE_NAME}:latest ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

# Push
echo "📤 Pushing to Azure Container Registry..."
az acr login --name $ACR_NAME
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

# Deploy
echo "🚀 Deploying to Azure Container Instances..."
REGISTRY_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)" \
  --registry-login-server ${ACR_NAME}.azurecr.io \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --restart-policy OnFailure

# Get URL
echo "✅ Deployment complete!"
echo "Your app is accessible at:"
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query ipAddress.fqdn \
  --output tsv
```

Usage:
```bash
chmod +x deploy-to-aci.sh
export OPENAI_API_KEY="sk-your-key"
./deploy-to-aci.sh
```

---

## Cost Optimization Tips

### 1. **Use Spot Instances** (if available)
```bash
az container create \
  --priority Spot \
  # ... rest of options
```

Saves up to 70% but can be interrupted.

### 2. **Schedule Start/Stop**
- Stop container at end of day
- Start in morning
- Saves 16+ hours/day = 66% cost reduction

### 3. **Reduce Idle Time**
- Set shorter timeout (default 300s)
- Use Logic Apps to auto-stop after inactivity

### 4. **Monitor Usage**
```bash
# Check how long container runs
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerInstance/containerGroups/$CONTAINER_NAME \
  --metric CPUUsage \
  --start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)Z" \
  --interval PT1H
```

---

## Cleanup (Delete Resources)

If you no longer need the app:

```bash
# Delete Container Instance
az container delete \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --yes

# Delete Container Registry
az acr delete \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --yes

# Delete Resource Group (deletes everything)
az group delete \
  --name $RESOURCE_GROUP \
  --yes
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME

# Restart
az container restart \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME
```

### API Key Not Working

Verify environment variable is set:
```bash
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query containers[0].environmentVariables \
  --output table
```

Update if needed:
```bash
az container delete \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --yes

# Redeploy with correct key (see Step 3)
```

### Image Push Fails

Ensure you're logged into ACR:
```bash
az acr login --name $ACR_NAME
```

---

## Alternative: Azure App Service with Auto-Scale to 0

If you prefer App Service (simpler UI):

```bash
# Create Free tier App Service Plan (doesn't scale to 0, but cheapest fixed cost)
az appservice plan create \
  --name plan-free \
  --resource-group $RESOURCE_GROUP \
  --sku F1

# Or use B1 with manual scale-down at night
```

**Note:** App Service doesn't truly scale to 0 in Standard plans, so ACI is better for cost.

---

## Next Steps

1. **Build Docker image:** `docker build -t audio-transcription .`
2. **Create ACR:** Follow Step 1
3. **Push image:** Follow Step 2
4. **Deploy ACI:** Follow Step 3
5. **Optimize costs:** Follow Step 4
6. **Monitor:** Check logs and usage regularly

---

## Support

For issues:
- Check container logs: `az container logs --follow ...`
- View Azure portal: https://portal.azure.com
- Monitor costs: Home → Subscriptions → Cost Analysis

---

**Cost:** $0-5/month with proper scheduling
**Status:** Production-ready for low-traffic usage
**Ideal for:** Demo, testing, or light production use

