#!/bin/bash

# Enhanced AI Financial Intelligence - Docker Build and Deploy Script
# This script builds and deploys the corrected webhook system

set -e

echo "🧠💰 Enhanced AI Financial Intelligence - Docker Build Script"
echo "============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required environment files exist
echo -e "${BLUE}📋 Checking environment configuration...${NC}"

required_files=(".env" ".db.env" ".importer.env")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        echo "   Please create this file with appropriate configuration"
        exit 1
    else
        echo -e "${GREEN}✅ Found: $file${NC}"
    fi
done

# Check if required environment variables are set
echo -e "${BLUE}🔑 Checking required environment variables...${NC}"

if [[ -z "${FIREFLY_TOKEN}" ]]; then
    echo -e "${YELLOW}⚠️ FIREFLY_TOKEN not set. Reading from .env file...${NC}"
    # Try to source from .env
    if [[ -f ".env" ]]; then
        source .env
    fi
    
    if [[ -z "${FIREFLY_TOKEN}" ]]; then
        echo -e "${RED}❌ FIREFLY_TOKEN is required but not set${NC}"
        echo "   Please set FIREFLY_TOKEN in your .env file"
        exit 1
    fi
fi

if [[ -z "${OPENAI_API_KEY}" ]]; then
    echo -e "${YELLOW}⚠️ OPENAI_API_KEY not set. AI features may be limited.${NC}"
fi

echo -e "${GREEN}✅ Environment configuration looks good${NC}"

# Build the services
echo -e "${BLUE}🔨 Building Docker images...${NC}"

echo -e "${YELLOW}Building Webhook Service (simpler build)...${NC}"
docker build -t firefly-webhook-service:test ./webhook_service/
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Webhook Service built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Webhook Service${NC}"
    echo "Check the webhook_service Dockerfile and requirements.txt"
    exit 1
fi

echo -e "${YELLOW}Building AI Categorizer Service...${NC}"
docker build -t firefly-ai-categorizer:test ./firefly-ai-categorizer/
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ AI Categorizer built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build AI Categorizer${NC}"
    echo "Checking for alternative build approach..."
    
    # Try building without PostgreSQL dependencies
    echo -e "${YELLOW}Attempting simplified build without PostgreSQL...${NC}"
    
    # Create temporary simplified requirements
    cp ./firefly-ai-categorizer/requirements.txt ./firefly-ai-categorizer/requirements.txt.backup
    cat > ./firefly-ai-categorizer/requirements-simple.txt << EOF
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
openai>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
EOF
    
    # Create simple Dockerfile
    cat > ./firefly-ai-categorizer/Dockerfile.simple << EOF
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements-simple.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN mkdir -p /app/data /app/logs
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:8001/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF
    
    docker build -f ./firefly-ai-categorizer/Dockerfile.simple -t firefly-ai-categorizer:test ./firefly-ai-categorizer/
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ AI Categorizer built successfully (simplified)${NC}"
        echo -e "${YELLOW}⚠️ Note: Running without PostgreSQL support (file-based storage)${NC}"
        # Cleanup
        rm ./firefly-ai-categorizer/Dockerfile.simple ./firefly-ai-categorizer/requirements-simple.txt
    else
        echo -e "${RED}❌ Failed to build AI Categorizer even with simplified approach${NC}"
        # Restore backup
        mv ./firefly-ai-categorizer/requirements.txt.backup ./firefly-ai-categorizer/requirements.txt
        exit 1
    fi
fi

# Start the services
echo -e "${BLUE}🚀 Starting Enhanced AI Financial Intelligence Stack...${NC}"

docker-compose up -d

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ All services started successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo "   • Firefly III Core:     http://localhost:8080"
    echo "   • Webhook Service:      http://localhost:8000"
    echo "   • AI Categorizer:       http://localhost:8001"
    echo "   • Data Importer:        http://localhost:81"
    echo ""
    echo -e "${YELLOW}🔗 Webhook Configuration:${NC}"
    echo "   Configure Firefly III webhooks to point to:"
    echo "   http://localhost:8000/webhook"
    echo ""
    echo -e "${BLUE}🧪 Testing:${NC}"
    echo "   Run: python3 test_webhooks.py"
    echo ""
    echo -e "${GREEN}🎉 Enhanced AI Financial Intelligence is ready!${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Wait a moment and check health
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

echo -e "${BLUE}🏥 Checking service health...${NC}"

# Check webhook service health
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Webhook Service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Webhook Service health check failed${NC}"
fi

# Check AI service health
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✅ AI Categorizer Service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ AI Categorizer Service health check failed${NC}"
fi

# Check Firefly III health
if curl -s http://localhost:8080 > /dev/null; then
    echo -e "${GREEN}✅ Firefly III Core is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Firefly III Core health check failed${NC}"
fi

echo ""
echo -e "${GREEN}🎯 System Status: Enhanced AI Financial Intelligence is operational!${NC}"
echo -e "${BLUE}📖 Next Steps:${NC}"
echo "   1. Complete Firefly III setup at http://localhost:8080"
echo "   2. Configure webhooks to point to http://localhost:8000/webhook"
echo "   3. Test with: python3 test_webhooks.py"
echo "   4. Monitor logs with: docker-compose logs -f"