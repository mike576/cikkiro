# Azure Deployment - Quick Start (5 minutes)

## Cost-Optimized: Pay Only When Running!

Estimated cost: **$0-5/month** (vs $13+/month for always-on App Service)

---

## Option 1: Automated Deployment (Recommended)

### Prerequisites
- Azure CLI: `az --version`
- Docker: `docker --version`
- Azure account: `az login`
- OpenAI API key ready

### Deploy in One Command

```bash
# Make script executable
chmod +x /Users/miklostoth/develop/workspaces/azure-transcription-app/deploy-aci.sh

# Run deployment script
cd /Users/miklostoth/develop/workspaces/azure-transcription-app
./deploy-aci.sh
```

The script will:
1. ✅ Create resource group & container registry
2. ✅ Build Docker image
3. ✅ Push to Azure
4. ✅ Deploy container instance
5. ✅ Give you the public URL

**That's it!** Your app is live in ~5 minutes.

---

## Option 2: Manual Step-by-Step

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name rg-transcription-aci --location eastus

# 3. Create container registry
az acr create --resource-group rg-transcription-aci --name transcriptionacr --sku Basic

# 4. Build Docker image
docker build -t audio-transcription .

# 5. Tag for registry
docker tag audio-transcription:latest transcriptionacr.azurecr.io/audio-transcription:latest

# 6. Push to Azure
az acr login --name transcriptionacr
docker push transcriptionacr.azurecr.io/audio-transcription:latest

# 7. Get credentials
REGISTRY_USERNAME=$(az acr credential show --name transcriptionacr --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name transcriptionacr --query passwords[0].value -o tsv)

# 8. Deploy container
az container create \
  --resource-group rg-transcription-aci \
  --name transcription-app \
  --image transcriptionacr.azurecr.io/audio-transcription:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY="sk-your-api-key" \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)" \
  --registry-login-server transcriptionacr.azurecr.io \
  --registry-username $REGISTRY_USERNAME \
  --registry-password $REGISTRY_PASSWORD \
  --restart-policy OnFailure \
  --dns-name-label transcription-app-$(date +%s | tail -c 6)

# 9. Get URL
az container show \
  --resource-group rg-transcription-aci \
  --name transcription-app \
  --query ipAddress.fqdn \
  --output tsv
```

---

## Access Your App

```
http://<FQDN-from-deployment>

Login:
  Email: borbala.veres@gmail.com
  Password: BakKecske5.
```

---

## Minimize Costs - Stop When Not Using

### Stop Container (Free Up Resources)
```bash
az container stop \
  --resource-group rg-transcription-aci \
  --name transcription-app
```

**When stopped:** No charges

### Restart When Needed
```bash
az container start \
  --resource-group rg-transcription-aci \
  --name transcription-app
```

### Delete Everything (If No Longer Needed)
```bash
az group delete --name rg-transcription-aci --yes
```

---

## Useful Commands

### View Logs
```bash
az container logs \
  --resource-group rg-transcription-aci \
  --name transcription-app \
  --follow
```

### Check Status
```bash
az container show \
  --resource-group rg-transcription-aci \
  --name transcription-app \
  --query "{State:instanceView.state, IP:ipAddress.ip, FQDN:ipAddress.fqdn}" \
  --output table
```

### Update Configuration
Delete and redeploy with `az container create` (from Step 8 above)

---

## Cost Breakdown

| Usage | Cost/Month |
|-------|-----------|
| 1 hour/day | ~$0.15 |
| 8 hours/day | ~$1.20 |
| 24 hours/day | ~$3.60 |
| **Always stopped** | **$0** |

---

## Pricing vs Alternatives

| Service | Cost/Month | Notes |
|---------|-----------|-------|
| Container Instances (on-demand) | $0-5 | Pay only when running |
| App Service (B1, always-on) | $13.14 | Always running |
| App Service (Free tier) | $0 | Limited (50MB, 1GB RAM) |
| Azure Functions | $0-2 | True serverless, best for APIs |

---

## Scheduled Stop/Start (Advanced)

To automatically stop/start at specific times, use Azure Logic Apps:

```bash
# View current container usage
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/rg-transcription-aci/providers/Microsoft.ContainerInstance/containerGroups/transcription-app \
  --metric CPUUsage \
  --start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)Z" \
  --interval PT1H
```

---

## Troubleshooting

### Container won't start
```bash
az container logs \
  --resource-group rg-transcription-aci \
  --name transcription-app
```

### Image push fails
```bash
az acr login --name transcriptionacr
docker push transcriptionacr.azurecr.io/audio-transcription:latest
```

### Access denied
- Verify OpenAI API key is correct
- Check container logs for detailed errors

---

## Next Steps

1. **Deploy:** Run `./deploy-aci.sh`
2. **Test:** Visit the URL and login
3. **Monitor:** Check logs with `az container logs ...`
4. **Cost:** Stop when not in use with `az container stop ...`
5. **Delete:** Clean up with `az group delete ...` when done

---

## Support

- Detailed guide: See `AZURE_DEPLOYMENT.md`
- View logs: `az container logs --follow ...`
- Check status: `az container show ...`
- Monitor costs: Azure Portal → Subscriptions → Cost Analysis

---

**Estimated deployment time:** 5 minutes
**Monthly cost (with good scheduling):** $0-5
**Status:** Production-ready
