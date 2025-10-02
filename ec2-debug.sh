#!/bin/bash

echo "=== EC2 Debug Script ==="
echo "Collecting debug information for troubleshooting deployment issues"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging helpers
print_header() {
    echo -e "\n${BLUE}===== $1 =====${NC}"
}
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# System Information
show_system_info() {
    print_header "SYSTEM INFORMATION"
    echo "Operating System: $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
    echo "Kernel Version: $(uname -r)"
    echo "Architecture: $(uname -m)"
    echo "Uptime: $(uptime)"
    echo "Memory Usage: $(free -h | grep Mem)"
    echo "Disk Usage: $(df -h / | tail -1)"
}

# Docker Information
show_docker_info() {
    print_header "DOCKER INFORMATION"
    if command -v docker &> /dev/null; then
        print_status "Docker installed: $(docker --version)"
        echo "Docker Status: $(systemctl is-active docker 2>/dev/null || echo 'Service not found')"
        echo "Docker user groups: $(groups $USER | grep -o docker || echo 'User not in docker group')"
        
        print_status "Docker Images:"
        docker images || print_error "Failed to list Docker images"

        print_status "Running Containers:"
        docker ps || print_error "Failed to list running containers"

        print_status "All Containers:"
        docker ps -a || print_error "Failed to list all containers"

        print_status "Docker Networks:"
        docker network ls || print_error "Failed to list Docker networks"

        print_status "Docker Volumes:"
        docker volume ls || print_error "Failed to list Docker volumes"

        print_status "Docker System Info:"
        docker system df || print_error "Failed to get Docker system info"
    else
        print_error "Docker is not installed or not in PATH"
    fi

    print_header "DOCKER COMPOSE INFORMATION"
    if command -v docker-compose &> /dev/null; then
        print_status "Docker Compose v1: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        print_status "Docker Compose v2: $(docker compose version)"
    else
        print_error "Docker Compose not installed"
    fi
}

# Firefly Application Info
show_firefly_info() {
    print_header "APPLICATION DIRECTORY INFORMATION"
    APP_DIR="/home/ec2-user/firefly-ai"
    if [ -d "$APP_DIR" ]; then
        print_status "Application directory exists: $APP_DIR"
        ls -la "$APP_DIR" || print_error "Failed to list directory contents"

        if [ -f "$APP_DIR/docker-compose.yaml" ] || [ -f "$APP_DIR/docker-compose.yml" ]; then
            print_status "Docker Compose file found"
        else
            print_warning "No Docker Compose file found in application directory"
        fi

        if [ -f "$APP_DIR/.env" ]; then
            print_status ".env file exists"
            echo ".env file size: $(stat -c%s "$APP_DIR/.env" 2>/dev/null || echo "Unknown")"
        else
            print_warning "No .env file found"
        fi
    else
        print_error "Application directory does not exist: $APP_DIR"
    fi
}

# Service Logs
show_service_logs() {
    print_header "SERVICE LOGS"
    if [ -d ~/firefly ] && [ -f ~/firefly/docker-compose.yaml ]; then
        cd ~/firefly || return
        docker-compose ps 2>/dev/null || echo "Failed to get compose status"
        for container in firefly_iii_core firefly_iii_db firefly_iii_ai_service firefly_iii_webhook_service; do
            if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
                echo "--- $container (last 10 lines) ---"
                docker logs "$container" --tail=10 2>&1 | head -10
                echo ""
            fi
        done
    else
        log_warn "No docker-compose.yaml found, skipping service logs"
    fi
}

# Connectivity
test_connectivity() {
    print_header "NETWORK CONNECTIVITY"
    echo "Google DNS: $(ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"
    echo "Docker Hub: $(curl -s --max-time 5 https://index.docker.io/v1/ >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"
    echo "Port 8080 (Firefly): $(curl -s --max-time 5 http://localhost:8080 >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"
    echo "Port 8001 (Webhook): $(curl -s --max-time 5 http://localhost:8001/health >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"
    echo "Port 8082 (AI Service): $(curl -s --max-time 5 http://localhost:8082/health >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"
}

# Resource Usage
show_resource_usage() {
    print_header "RESOURCE USAGE"
    echo "CPU Usage:"
    top -bn1 | head -10 || echo "Failed to get CPU info"
    echo ""
    echo "Memory Usage:"
    free -h || echo "Failed to get memory info"
    echo ""
    echo "Disk Usage:"
    df -h || echo "Failed to get disk info"
    echo ""
    echo "Docker System Usage:"
    docker system df 2>/dev/null || echo "Failed to get Docker system usage"
}

# Main
main() {
    log_info "Starting debug information collection..."
    show_system_info
    show_docker_info
    show_firefly_info
    show_service_logs
    test_connectivity
    show_resource_usage
    log_info "Debug collection completed!"
}

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
