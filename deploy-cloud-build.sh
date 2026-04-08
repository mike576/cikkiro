#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Configuration
RESOURCE_GROUP="rg-transcription-aci"
ACR_NAME="transcriptionacr$(date +%s | tail -c 5)"
CONTAINER_NAME="transcription-app"
LOCATION="eastus"
IMAGE_NAME="audio-transcription"
CONTAINER_PORT=8000
CPU=1
MEMORY=2

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Azure Cloud Build Deployment (No Local Docker Needed)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    print_error "Azure CLI not found. Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi
print_success "Azure CLI found"

# Check Azure login
if ! az account show &> /dev/null; then
    print_warning "Not logged into Azure. Running 'az login'..."
    az login
fi
print_success "Azure authenticated"

# Get or prompt for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY not set"
    read -sp "Enter your OpenAI API key: " OPENAI_API_KEY
    echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OpenAI API key is required"
    exit 1
fi
print_success "OpenAI API key provided"

echo ""
print_status "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Container Registry: $ACR_NAME.azurecr.io"
echo "  Container Name: $CONTAINER_NAME"
echo "  Location: $LOCATION"
echo "  CPU: $CPU"
echo "  Memory: ${MEMORY}GB"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 1: Creating Azure Resources${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

print_status "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
print_success "Resource group created"

print_status "Creating container registry: $ACR_NAME"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --output none
print_success "Container registry created"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 2: Building Docker Image in Azure Cloud${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

print_status "Building Docker image in Azure (this may take 2-3 minutes)..."
az acr build \
    --registry $ACR_NAME \
    --image ${IMAGE_NAME}:latest \
    . || {
    print_error "Docker build failed"
    exit 1
}
print_success "Docker image built in Azure"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 3: Deploying Container Instance${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

print_status "Getting registry credentials..."
REGISTRY_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
SECRET_KEY=$(openssl rand -hex 32)
print_success "Credentials obtained"

print_status "Deploying container instance..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest \
    --cpu $CPU \
    --memory $MEMORY \
    --ports $CONTAINER_PORT \
    --dns-name-label $CONTAINER_NAME-$(date +%s | tail -c 6) \
    --environment-variables \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        FLASK_ENV="production" \
        SECRET_KEY="$SECRET_KEY" \
    --registry-login-server ${ACR_NAME}.azurecr.io \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --restart-policy OnFailure \
    --output none || {
    print_error "Container creation failed"
    exit 1
}
print_success "Container deployed"

echo ""
print_status "Waiting for container to start (this may take 30-60 seconds)..."
sleep 30

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Get the FQDN
FQDN=$(az container show \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --query ipAddress.fqdn \
    --output tsv)

print_success "Your app is now running!"
echo ""
echo -e "${GREEN}Access your app at:${NC}"
echo -e "${YELLOW}http://${FQDN}${NC}"
echo ""
echo -e "${GREEN}Login credentials:${NC}"
echo "  Email: borbala.veres@gmail.com"
echo "  Password: BakKecske5."
echo ""

# Cost information
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}COST INFORMATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Pricing: \$0.002/hour when running (~\$1.50/month if 24/7)"
echo ""
echo -e "${YELLOW}To minimize costs:${NC}"
echo "  • Stop when not in use: az container stop -g $RESOURCE_GROUP -n $CONTAINER_NAME"
echo "  • Restart when needed:  az container start -g $RESOURCE_GROUP -n $CONTAINER_NAME"
echo "  • Delete to stop charges: az group delete -n $RESOURCE_GROUP --yes"
echo ""

# Useful commands
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}USEFUL COMMANDS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "View logs:"
echo "  az container logs -g $RESOURCE_GROUP -n $CONTAINER_NAME --follow"
echo ""
echo "Check status:"
echo "  az container show -g $RESOURCE_GROUP -n $CONTAINER_NAME"
echo ""
echo "Stop container (free up resources):"
echo "  az container stop -g $RESOURCE_GROUP -n $CONTAINER_NAME"
echo ""
echo "Start container again:"
echo "  az container start -g $RESOURCE_GROUP -n $CONTAINER_NAME"
echo ""
echo "Delete everything:"
echo "  az group delete -n $RESOURCE_GROUP --yes"
echo ""

print_success "Deployment script completed successfully!"
