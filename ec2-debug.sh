#!/bin/bash

echo "=== EC2 Firefly Deployment Debugging Script ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo ""

# System Information
echo "=== SYSTEM INFORMATION ==="
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo ""

# Docker Installation Check
echo "=== DOCKER ENVIRONMENT ==="
if command -v docker &> /dev/null; then
    echo "✅ Docker installed: $(docker --version)"
    echo "Docker status: $(systemctl is-active docker 2>/dev/null || echo 'Service not found')"
    echo "Docker user groups: $(groups $USER | grep -o docker || echo 'User not in docker group')"
else
    echo "❌ Docker not installed"
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose v1: $(docker-compose --version)"
else
    echo "❌ Docker Compose v1 not found"
fi

if docker compose version &> /dev/null; then
    echo "✅ Docker Compose v2: $(docker compose version)"
else
    echo "❌ Docker Compose v2 not found"
fi
echo ""

# Network and Ports
echo "=== NETWORK AND PORTS ==="
echo "Public IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Unable to fetch')"
echo "Private IP: $(hostname -I | awk '{print $1}')"
echo "Listening ports:"
netstat -tlnp 2>/dev/null | grep -E ':(8080|8082|8001|81|3306)' || echo "No target ports listening"
echo ""

# Security Groups / Firewall
echo "=== FIREWALL STATUS ==="
if command -v ufw &> /dev/null; then
    echo "UFW Status: $(ufw status)"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld zones: $(firewall-cmd --get-active-zones 2>/dev/null)"
elif command -v iptables &> /dev/null; then
    echo "Iptables rules: $(iptables -L INPUT | grep -E '8080|8082|8001|81' | wc -l) rules found"
else
    echo "No standard firewall detected"
fi
echo ""

# File System Check
echo "=== PROJECT FILES ==="
pwd
echo "Current directory contents:"
ls -la
echo ""
echo "Docker Compose file exists: $(test -f docker-compose.yaml && echo 'YES' || echo 'NO')"
echo "Environment files:"
for env_file in .env .db.env .importer.env; do
    if [ -f "$env_file" ]; then
        echo "  ✅ $env_file ($(wc -l < $env_file) lines)"
    else
        echo "  ❌ $env_file missing"
    fi
done
echo ""

# Docker Status
echo "=== DOCKER CONTAINERS ==="
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers or permission denied"
    echo ""
    echo "All containers (including stopped):"
    docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No containers or permission denied"
else
    echo "❌ Cannot access Docker daemon"
fi
echo ""

# Docker Compose Status
echo "=== DOCKER COMPOSE STATUS ==="
if [ -f docker-compose.yaml ]; then
    if docker compose ps &> /dev/null; then
        docker compose ps
    elif docker-compose ps &> /dev/null; then
        docker-compose ps
    else
        echo "❌ Cannot run docker compose ps"
    fi
else
    echo "❌ No docker-compose.yaml file found"
fi
echo ""

# Recent Logs Check
echo "=== RECENT CONTAINER LOGS ==="
if command -v docker &> /dev/null && docker info &> /dev/null; then
    for container in firefly_iii_core firefly_iii_db firefly_iii_ai_service firefly_iii_webhook_service; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            echo "--- $container (last 10 lines) ---"
            docker logs "$container" --tail 10 2>&1 | head -10
            echo ""
        fi
    done
else
    echo "❌ Cannot access Docker logs"
fi

# Environment Variables Check
echo "=== ENVIRONMENT VARIABLES ==="
if [ -f .env ]; then
    echo ".env file critical variables:"
    grep -E '^(APP_KEY|DB_|SITE_OWNER|APP_URL)' .env 2>/dev/null | sed 's/=.*/=***/' || echo "Cannot read .env"
fi
if [ -f .db.env ]; then
    echo ".db.env file variables:"
    grep -E '^MARIADB_' .db.env 2>/dev/null | sed 's/=.*/=***/' || echo "Cannot read .db.env"
fi
echo ""

echo "=== DEBUG COMPLETE ==="
echo "Save this output and share it for troubleshooting assistance."