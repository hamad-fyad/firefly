#!/bin/bash

echo "=== Firefly III Docker Setup Validation ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check 1: Docker is installed and running
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_status 0 "Docker is installed and running"
        echo "   Version: $(docker --version)"
    else
        print_status 1 "Docker is installed but not running"
        print_info "Try: sudo systemctl start docker"
    fi
else
    print_status 1 "Docker is not installed"
    print_info "Run: ./ec2-setup.sh"
fi

echo ""

# Check 2: Docker Compose is available
echo "2. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    print_status 0 "Docker Compose is available"
    echo "   Version: $(docker compose version --short)"
else
    print_status 1 "Docker Compose is not available"
fi

echo ""

# Check 3: Required files exist
echo "3. Checking required files..."
files=(
    "docker-compose.yaml"
    ".env"
    "configure-firefly.sh"
    "ec2-setup.sh"
    "firefly-ai-categorizer/Dockerfile"
    "webhook_service/Dockerfile"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "$file exists"
    else
        print_status 1 "$file is missing"
        all_files_exist=false
    fi
done

echo ""

# Check 4: Environment variables in .env
echo "4. Checking environment variables..."
if [ -f ".env" ]; then
    required_vars=(
        "DOCKER_USERNAME"
        "AI_SERVICE_TAG"
        "WEBHOOK_SERVICE_TAG"
        "OPENAI_API_KEY"
        "FIREFLY_TOKEN"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            value=$(grep "^$var=" .env | cut -d'=' -f2 | sed 's/^["'\'']*//;s/["'\'']*$//')
            if [ -n "$value" ] && [ "$value" != "\${$var}" ]; then
                print_status 0 "$var is set"
            else
                print_status 1 "$var is empty or not properly set"
            fi
        else
            print_status 1 "$var is missing from .env"
        fi
    done
else
    print_status 1 ".env file is missing"
fi

echo ""

# Check 5: Docker images availability
echo "5. Checking Docker images..."
if [ -f ".env" ]; then
    # Source environment variables
    set -a
    source .env
    set +a
    
    # Check if custom images exist locally or can be pulled
    images=(
        "${DOCKER_USERNAME:-hamad}/firefly-ai-categorizer:${AI_SERVICE_TAG:-latest}"
        "${DOCKER_USERNAME:-hamad}/firefly-webhook-service:${WEBHOOK_SERVICE_TAG:-latest}"
    )
    
    for image in "${images[@]}"; do
        if docker image inspect "$image" &> /dev/null; then
            print_status 0 "$image exists locally"
        else
            print_warning "$image not found locally"
            echo "   Attempting to pull..."
            if docker pull "$image" &> /dev/null; then
                print_status 0 "$image pulled successfully"
            else
                print_status 1 "$image could not be pulled"
                print_info "Will attempt local build during compose up"
            fi
        fi
    done
fi

echo ""

# Check 6: Docker Compose validation
echo "6. Validating Docker Compose configuration..."
if docker compose config &> /dev/null; then
    print_status 0 "Docker Compose configuration is valid"
else
    print_status 1 "Docker Compose configuration has errors"
    print_info "Run: docker compose config"
fi

echo ""

# Check 7: Port availability
echo "7. Checking port availability..."
ports=(8080 8082 8001 81 3306 5432)
for port in "${ports[@]}"; do
    if ! ss -tuln | grep -q ":$port "; then
        print_status 0 "Port $port is available"
    else
        print_warning "Port $port is in use"
        print_info "Service using port $port: $(ss -tulnp | grep ":$port " | awk '{print $7}' | cut -d'"' -f2)"
    fi
done

echo ""

# Summary and recommendations
echo "=== SUMMARY AND RECOMMENDATIONS ==="
echo ""

if $all_files_exist && [ -f ".env" ]; then
    echo "🎯 Quick test commands:"
    echo "   docker compose pull          # Pull latest images"
    echo "   docker compose up -d         # Start all services"
    echo "   docker compose ps            # Check service status"
    echo "   docker compose logs ai-service    # Check AI service logs"
    echo "   docker compose logs webhook-service # Check webhook service logs"
    echo ""
fi

echo "📋 Manual checks to perform:"
echo "   1. Verify GitHub secrets are set correctly"
echo "   2. Check that Docker Hub repositories exist"
echo "   3. Test GitHub Actions workflow"
echo "   4. Verify EC2 security groups allow required ports"
echo ""

echo "🔧 If issues persist:"
echo "   1. Check Docker Hub for your images: https://hub.docker.com/u/$(grep '^DOCKER_USERNAME=' .env 2>/dev/null | cut -d'=' -f2 || echo 'your-username')"
echo "   2. Review GitHub Actions logs"
echo "   3. Check EC2 instance logs: journalctl -u docker"
echo "   4. Verify .env file contains all required variables"
echo ""

echo "=== Validation Complete ==="