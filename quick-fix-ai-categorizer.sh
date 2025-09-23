#!/bin/bash

echo "🔧 Quick Fix: Updating AI Categorizer Service"
echo "============================================="

# Set colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EC2_HOST="52.212.42.101"
EC2_USER="ubuntu"
DOCKER_IMAGE="hamadfyad/firefly-ai-categorizer:latest"

echo -e "${YELLOW}📋 Step 1: Build and push updated AI categorizer image${NC}"

# Build the image locally with a fix tag
docker build -t "$DOCKER_IMAGE" ./firefly-ai-categorizer/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push to Docker Hub
echo -e "${YELLOW}📤 Pushing to Docker Hub...${NC}"
docker push "$DOCKER_IMAGE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image pushed to Docker Hub${NC}"
else
    echo -e "${RED}❌ Docker push failed${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Step 2: Update service on EC2${NC}"

# Create the update script
cat > update_ai_service.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Updating AI Categorizer service..."

# Navigate to the firefly directory
cd ~/firefly

# Pull the latest image
echo "📥 Pulling latest AI categorizer image..."
docker compose pull ai-categorizer

# Stop and restart the AI categorizer service
echo "⏹️ Stopping AI categorizer..."
docker compose stop ai-categorizer

echo "🗑️ Removing old container..."
docker compose rm -f ai-categorizer

echo "🚀 Starting updated AI categorizer..."
docker compose up -d ai-categorizer

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 10

# Test the service
echo "🧪 Testing AI categorizer health..."
curl -s http://localhost:8082/health | jq '.' || echo "Health check response (no jq):" && curl -s http://localhost:8082/health

echo "✅ AI Categorizer update completed!"
EOF

# Make the script executable
chmod +x update_ai_service.sh

echo -e "${YELLOW}📋 Step 3: Execute update on EC2${NC}"
echo "Please run this command manually with your SSH key:"
echo ""
echo -e "${GREEN}scp -i your-key.pem update_ai_service.sh $EC2_USER@$EC2_HOST:~/update_ai_service.sh${NC}"
echo -e "${GREEN}ssh -i your-key.pem $EC2_USER@$EC2_HOST 'chmod +x ~/update_ai_service.sh && ~/update_ai_service.sh'${NC}"
echo ""
echo "OR if you have SSH keys configured:"
echo -e "${GREEN}scp update_ai_service.sh $EC2_USER@$EC2_HOST:~/update_ai_service.sh${NC}"
echo -e "${GREEN}ssh $EC2_USER@$EC2_HOST 'chmod +x ~/update_ai_service.sh && ~/update_ai_service.sh'${NC}"

echo ""
echo -e "${YELLOW}📋 Step 4: Test the fix${NC}"
echo "After running the above commands, test with:"
echo -e "${GREEN}curl http://$EC2_HOST:8082/health${NC}"
echo ""
echo "Expected response:"
echo '{"status":"healthy","model_status":"available","model_type":"openai"}'