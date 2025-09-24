#!/bin/bash#!/bin/bash



echo "=== EC2 Debug Script ==="echo "=== EC2 Firefly Deployment Debugging Script ==="

echo "Collecting debug information for troubleshooting deployment issues"echo "Date: $(date)"

echo "Hostname: $(hostname)"

# Colors for outputecho ""

RED='\033[0;31m'

GREEN='\033[0;32m'# System Information

YELLOW='\033[1;33m'echo "=== SYSTEM INFORMATION ==="

NC='\033[0m' # No Colorecho "OS: $(cat /etc/os-release | grep PRETTY_NAME)"

echo "Architecture: $(uname -m)"

log_info() {echo "Kernel: $(uname -r)"

    echo -e "${GREEN}[INFO]${NC} $1"echo "Memory: $(free -h | grep Mem)"

}echo "Disk: $(df -h / | tail -1)"

echo ""

log_warn() {

    echo -e "${YELLOW}[WARN]${NC} $1"# Docker Installation Check

}echo "=== DOCKER ENVIRONMENT ==="

if command -v docker &> /dev/null; then

log_error() {    echo "✅ Docker installed: $(docker --version)"

    echo -e "${RED}[ERROR]${NC} $1"    echo "Docker status: $(systemctl is-active docker 2>/dev/null || echo 'Service not found')"

}    echo "Docker user groups: $(groups $USER | grep -o docker || echo 'User not in docker group')"

else

# System Information    echo "❌ Docker not installed"

show_system_info() {fi

    log_info "=== System Information ==="

    echo "OS: $(uname -a)"if command -v docker-compose &> /dev/null; then

    echo "Date: $(date)"    echo "✅ Docker Compose v1: $(docker-compose --version)"

    echo "Uptime: $(uptime)"else

    echo "Disk Usage: $(df -h / | tail -1)"    echo "❌ Docker Compose v1 not found"

    echo "Memory: $(free -h | grep Mem)"fi

    echo "User: $(whoami)"

    echo "Groups: $(groups)"if docker compose version &> /dev/null; then

    echo ""    echo "✅ Docker Compose v2: $(docker compose version)"

}else

    echo "❌ Docker Compose v2 not found"

# Docker Informationfi

show_docker_info() {echo ""

    log_info "=== Docker Information ==="

    # Network and Ports

    if command -v docker &> /dev/null; thenecho "=== NETWORK AND PORTS ==="

        echo "Docker Version: $(docker --version)"echo "Public IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Unable to fetch')"

        echo "Docker Status: $(sudo systemctl is-active docker || echo 'Not running')"echo "Private IP: $(hostname -I | awk '{print $1}')"

        echo "Listening ports:"

        echo ""netstat -tlnp 2>/dev/null | grep -E ':(8080|8082|8001|81|3306)' || echo "No target ports listening"

        echo "Docker Images:"echo ""

        docker images || echo "Failed to list images"

        # Security Groups / Firewall

        echo ""echo "=== FIREWALL STATUS ==="

        echo "Docker Containers:"if command -v ufw &> /dev/null; then

        docker ps -a || echo "Failed to list containers"    echo "UFW Status: $(ufw status)"

        elif command -v firewall-cmd &> /dev/null; then

        echo ""    echo "Firewalld zones: $(firewall-cmd --get-active-zones 2>/dev/null)"

        echo "Docker Networks:"elif command -v iptables &> /dev/null; then

        docker network ls || echo "Failed to list networks"    echo "Iptables rules: $(iptables -L INPUT | grep -E '8080|8082|8001|81' | wc -l) rules found"

        else

        echo ""    echo "No standard firewall detected"

        echo "Docker Volumes:"fi

        docker volume ls || echo "Failed to list volumes"echo ""

        

    else# File System Check

        log_error "Docker not installed"echo "=== PROJECT FILES ==="

    fipwd

    echo "Current directory contents:"

    if command -v docker-compose &> /dev/null; thenls -la

        echo ""echo ""

        echo "Docker Compose Version: $(docker-compose --version)"echo "Docker Compose file exists: $(test -f docker-compose.yaml && echo 'YES' || echo 'NO')"

    elseecho "Environment files:"

        log_error "Docker Compose not installed"for env_file in .env .db.env .importer.env; do

    fi    if [ -f "$env_file" ]; then

    echo ""        echo "  ✅ $env_file ($(wc -l < $env_file) lines)"

}    else

        echo "  ❌ $env_file missing"

# Firefly Directory Information    fi

show_firefly_info() {done

    log_info "=== Firefly Directory Information ==="echo ""

    

    if [ -d ~/firefly ]; then# Docker Status

        echo "Firefly Directory: ~/firefly"echo "=== DOCKER CONTAINERS ==="

        echo "Directory Size: $(du -sh ~/firefly 2>/dev/null || echo 'Unknown')"if command -v docker &> /dev/null && docker info &> /dev/null; then

        echo ""    echo "Running containers:"

        echo "Files in firefly directory:"    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers or permission denied"

        ls -la ~/firefly/ || echo "Failed to list files"    echo ""

            echo "All containers (including stopped):"

        echo ""    docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No containers or permission denied"

        echo "Docker Compose file exists: $([ -f ~/firefly/docker-compose.yaml ] && echo 'Yes' || echo 'No')"else

        echo "Configure script exists: $([ -f ~/firefly/configure-firefly.sh ] && echo 'Yes' || echo 'No')"    echo "❌ Cannot access Docker daemon"

        echo "Environment file exists: $([ -f ~/firefly/.env ] && echo 'Yes' || echo 'No')"fi

        echo ""

        if [ -f ~/firefly/.env ]; then

            echo ""# Docker Compose Status

            echo "Environment file contents (secrets hidden):"echo "=== DOCKER COMPOSE STATUS ==="

            cat ~/firefly/.env | sed 's/=.*/=***/' || echo "Failed to read .env"if [ -f docker-compose.yaml ]; then

        fi    if docker compose ps &> /dev/null; then

    else        docker compose ps

        log_error "Firefly directory not found at ~/firefly"    elif docker-compose ps &> /dev/null; then

    fi        docker-compose ps

    echo ""    else

}        echo "❌ Cannot run docker compose ps"

    fi

# Service Logselse

show_service_logs() {    echo "❌ No docker-compose.yaml file found"

    log_info "=== Service Logs ==="fi

    echo ""

    if [ -d ~/firefly ] && [ -f ~/firefly/docker-compose.yaml ]; then

        cd ~/firefly# Recent Logs Check

        echo "=== RECENT CONTAINER LOGS ==="

        echo "Docker Compose Services Status:"if command -v docker &> /dev/null && docker info &> /dev/null; then

        docker-compose ps 2>/dev/null || echo "Failed to get compose status"    for container in firefly_iii_core firefly_iii_db firefly_iii_ai_service firefly_iii_webhook_service; do

                if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then

        echo ""            echo "--- $container (last 10 lines) ---"

        echo "Recent logs from all services:"            docker logs "$container" --tail 10 2>&1 | head -10

        docker-compose logs --tail=20 2>/dev/null || echo "Failed to get compose logs"            echo ""

                fi

    else    done

        log_warn "No docker-compose.yaml found, skipping service logs"else

    fi    echo "❌ Cannot access Docker logs"

    echo ""fi

}

# Environment Variables Check

# Network Connectivityecho "=== ENVIRONMENT VARIABLES ==="

test_connectivity() {if [ -f .env ]; then

    log_info "=== Network Connectivity Tests ==="    echo ".env file critical variables:"

        grep -E '^(APP_KEY|DB_|SITE_OWNER|APP_URL)' .env 2>/dev/null | sed 's/=.*/=***/' || echo "Cannot read .env"

    echo "Testing external connectivity:"fi

    echo "Google DNS: $(ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"if [ -f .db.env ]; then

    echo "Docker Hub: $(curl -s --max-time 5 https://index.docker.io/v1/ >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"    echo ".db.env file variables:"

        grep -E '^MARIADB_' .db.env 2>/dev/null | sed 's/=.*/=***/' || echo "Cannot read .db.env"

    echo ""fi

    echo "Testing local services:"echo ""

    echo "Port 8080 (Firefly): $(curl -s --max-time 5 http://localhost:8080 >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"

    echo "Port 8001 (Webhook): $(curl -s --max-time 5 http://localhost:8001/health >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"echo "=== DEBUG COMPLETE ==="

    echo "Port 8082 (AI Service): $(curl -s --max-time 5 http://localhost:8082/health >/dev/null 2>&1 && echo 'OK' || echo 'FAIL')"echo "Save this output and share it for troubleshooting assistance."
    echo ""
}

# Resource Usage
show_resource_usage() {
    log_info "=== Resource Usage ==="
    
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
    echo ""
}

# Generate Report
generate_report() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="/tmp/firefly_debug_report_$timestamp.txt"
    
    log_info "Generating comprehensive debug report..."
    
    {
        echo "=== FIREFLY III DEBUG REPORT ==="
        echo "Generated: $(date)"
        echo "Hostname: $(hostname)"
        echo ""
        
        show_system_info
        show_docker_info
        show_firefly_info
        show_service_logs
        test_connectivity
        show_resource_usage
        
    } > "$report_file"
    
    log_info "Debug report saved to: $report_file"
    log_info "Report size: $(du -h $report_file | cut -f1)"
    
    echo ""
    echo "=== REPORT PREVIEW (Last 50 lines) ==="
    tail -50 "$report_file"
}

# Main execution
main() {
    log_info "Starting debug information collection..."
    
    show_system_info
    show_docker_info
    show_firefly_info
    show_service_logs
    test_connectivity
    show_resource_usage
    
    generate_report
    
    log_info "Debug collection completed!"
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi