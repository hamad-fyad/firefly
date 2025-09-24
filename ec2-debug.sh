#!/bin/bash#!/bin/bash#!/bin/bash



echo "=== EC2 Debug Script ==="

echo "Collecting debug information for troubleshooting deployment issues"

echo "Date: $(date)"echo "=== EC2 Debug Script ==="echo "=== EC2 Firefly Deployment Debugging Script ==="

echo "Hostname: $(hostname)"

echo ""echo "Collecting debug information for troubleshooting deployment issues"echo "Date: $(date)"



# Colors for outputecho "Hostname: $(hostname)"

RED='\033[0;31m'

GREEN='\033[0;32m'# Colors for outputecho ""

YELLOW='\033[1;33m'

BLUE='\033[0;34m'RED='\033[0;31m'

NC='\033[0m' # No Color

GREEN='\033[0;32m'# System Information

print_header() {

    echo -e "\n${BLUE}===== $1 =====${NC}"YELLOW='\033[1;33m'echo "=== SYSTEM INFORMATION ==="

}

NC='\033[0m' # No Colorecho "OS: $(cat /etc/os-release | grep PRETTY_NAME)"

print_status() {

    echo -e "${GREEN}[INFO]${NC} $1"echo "Architecture: $(uname -m)"

}

log_info() {echo "Kernel: $(uname -r)"

print_warning() {

    echo -e "${YELLOW}[WARNING]${NC} $1"    echo -e "${GREEN}[INFO]${NC} $1"echo "Memory: $(free -h | grep Mem)"

}

}echo "Disk: $(df -h / | tail -1)"

print_error() {

    echo -e "${RED}[ERROR]${NC} $1"echo ""

}

log_warn() {

# System Information

print_header "SYSTEM INFORMATION"    echo -e "${YELLOW}[WARN]${NC} $1"# Docker Installation Check

echo "Operating System: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"

echo "Kernel Version: $(uname -r)"}echo "=== DOCKER ENVIRONMENT ==="

echo "Architecture: $(uname -m)"

echo "Uptime: $(uptime)"if command -v docker &> /dev/null; then

echo "Memory Usage: $(free -h | grep Mem)"

echo "Disk Usage: $(df -h / | tail -1)"log_error() {    echo "✅ Docker installed: $(docker --version)"



# Docker Information    echo -e "${RED}[ERROR]${NC} $1"    echo "Docker status: $(systemctl is-active docker 2>/dev/null || echo 'Service not found')"

print_header "DOCKER INFORMATION"

if command -v docker &> /dev/null; then}    echo "Docker user groups: $(groups $USER | grep -o docker || echo 'User not in docker group')"

    print_status "Docker is installed"

    echo "Docker Version: $(docker --version)"else

    echo "Docker Status: $(systemctl is-active docker)"

    # System Information    echo "❌ Docker not installed"

    print_status "Docker Images:"

    docker images || print_error "Failed to list Docker images"show_system_info() {fi

    

    print_status "Running Containers:"    log_info "=== System Information ==="

    docker ps || print_error "Failed to list running containers"

        echo "OS: $(uname -a)"if command -v docker-compose &> /dev/null; then

    print_status "All Containers:"

    docker ps -a || print_error "Failed to list all containers"    echo "Date: $(date)"    echo "✅ Docker Compose v1: $(docker-compose --version)"

    

    print_status "Docker Networks:"    echo "Uptime: $(uptime)"else

    docker network ls || print_error "Failed to list Docker networks"

        echo "Disk Usage: $(df -h / | tail -1)"    echo "❌ Docker Compose v1 not found"

    print_status "Docker Volumes:"

    docker volume ls || print_error "Failed to list Docker volumes"    echo "Memory: $(free -h | grep Mem)"fi

    

    print_status "Docker System Info:"    echo "User: $(whoami)"

    docker system df || print_error "Failed to get Docker system info"

else    echo "Groups: $(groups)"if docker compose version &> /dev/null; then

    print_error "Docker is not installed or not in PATH"

fi    echo ""    echo "✅ Docker Compose v2: $(docker compose version)"



# Docker Compose Information}else

print_header "DOCKER COMPOSE INFORMATION"

if command -v docker-compose &> /dev/null; then    echo "❌ Docker Compose v2 not found"

    print_status "Docker Compose is installed"

    echo "Docker Compose Version: $(docker-compose --version)"# Docker Informationfi

else

    print_error "Docker Compose is not installed or not in PATH"show_docker_info() {echo ""

fi

    log_info "=== Docker Information ==="

# Application Directory Information

print_header "APPLICATION DIRECTORY INFORMATION"    # Network and Ports

APP_DIR="/home/ec2-user/firefly-ai"

if [ -d "$APP_DIR" ]; then    if command -v docker &> /dev/null; thenecho "=== NETWORK AND PORTS ==="

    print_status "Application directory exists: $APP_DIR"

    echo "Directory contents:"        echo "Docker Version: $(docker --version)"echo "Public IP: $(curl -s ifconfig.me 2>/dev/null || echo 'Unable to fetch')"

    ls -la "$APP_DIR" || print_error "Failed to list directory contents"

            echo "Docker Status: $(sudo systemctl is-active docker || echo 'Not running')"echo "Private IP: $(hostname -I | awk '{print $1}')"

    if [ -f "$APP_DIR/docker-compose.yaml" ] || [ -f "$APP_DIR/docker-compose.yml" ]; then

        print_status "Docker Compose file found"        echo "Listening ports:"

    else

        print_warning "No Docker Compose file found in application directory"        echo ""netstat -tlnp 2>/dev/null | grep -E ':(8080|8082|8001|81|3306)' || echo "No target ports listening"

    fi

            echo "Docker Images:"echo ""

    if [ -f "$APP_DIR/.env" ]; then

        print_status ".env file exists"        docker images || echo "Failed to list images"

        echo ".env file size: $(stat -c%s "$APP_DIR/.env" 2>/dev/null || echo "Unknown")"

    else        # Security Groups / Firewall

        print_warning "No .env file found"

    fi        echo ""echo "=== FIREWALL STATUS ==="

else

    print_error "Application directory does not exist: $APP_DIR"        echo "Docker Containers:"if command -v ufw &> /dev/null; then

fi

        docker ps -a || echo "Failed to list containers"    echo "UFW Status: $(ufw status)"

# Network Information

print_header "NETWORK INFORMATION"        elif command -v firewall-cmd &> /dev/null; then

echo "Network Interfaces:"

ip addr show || ifconfig || print_error "Failed to show network interfaces"        echo ""    echo "Firewalld zones: $(firewall-cmd --get-active-zones 2>/dev/null)"



echo -e "\nListening Ports:"        echo "Docker Networks:"elif command -v iptables &> /dev/null; then

netstat -tlnp 2>/dev/null || ss -tlnp || print_error "Failed to show listening ports"

        docker network ls || echo "Failed to list networks"    echo "Iptables rules: $(iptables -L INPUT | grep -E '8080|8082|8001|81' | wc -l) rules found"

echo -e "\nDNS Configuration:"

cat /etc/resolv.conf || print_error "Failed to show DNS configuration"        else



# Process Information        echo ""    echo "No standard firewall detected"

print_header "PROCESS INFORMATION"

echo "Running processes (related to Docker/Firefly):"        echo "Docker Volumes:"fi

ps aux | grep -E "(docker|firefly|postgres)" | grep -v grep || echo "No relevant processes found"

        docker volume ls || echo "Failed to list volumes"echo ""

# Log Information

print_header "LOG INFORMATION"        

echo "Recent system logs (last 20 lines):"

journalctl --no-pager -n 20 || print_error "Failed to retrieve system logs"    else# File System Check



if command -v docker &> /dev/null; then        log_error "Docker not installed"echo "=== PROJECT FILES ==="

    echo -e "\nRecent Docker logs:"

    docker logs $(docker ps -q) --tail=10 2>/dev/null || echo "No containers running or failed to get logs"    fipwd

fi

    echo "Current directory contents:"

# File System Permissions

print_header "FILE SYSTEM PERMISSIONS"    if command -v docker-compose &> /dev/null; thenls -la

if [ -d "$APP_DIR" ]; then

    echo "Application directory permissions:"        echo ""echo ""

    ls -ld "$APP_DIR"

            echo "Docker Compose Version: $(docker-compose --version)"echo "Docker Compose file exists: $(test -f docker-compose.yaml && echo 'YES' || echo 'NO')"

    echo -e "\nKey files permissions:"

    for file in "$APP_DIR/docker-compose.yaml" "$APP_DIR/docker-compose.yml" "$APP_DIR/.env"; do    elseecho "Environment files:"

        if [ -f "$file" ]; then

            ls -l "$file"        log_error "Docker Compose not installed"for env_file in .env .db.env .importer.env; do

        fi

    done    fi    if [ -f "$env_file" ]; then

fi

    echo ""        echo "  ✅ $env_file ($(wc -l < $env_file) lines)"

# Environment Variables

print_header "ENVIRONMENT VARIABLES"}    else

echo "Docker-related environment variables:"

env | grep -i docker || echo "No Docker environment variables found"        echo "  ❌ $env_file missing"



echo -e "\nUser and group information:"# Firefly Directory Information    fi

echo "Current user: $(whoami)"

echo "User groups: $(groups)"show_firefly_info() {done

echo "Docker group members:"

getent group docker || echo "Docker group not found"    log_info "=== Firefly Directory Information ==="echo ""



# Resource Usage    

print_header "RESOURCE USAGE"

echo "CPU Usage:"    if [ -d ~/firefly ]; then# Docker Status

top -bn1 | head -10

        echo "Firefly Directory: ~/firefly"echo "=== DOCKER CONTAINERS ==="

echo -e "\nMemory Usage:"

free -h        echo "Directory Size: $(du -sh ~/firefly 2>/dev/null || echo 'Unknown')"if command -v docker &> /dev/null && docker info &> /dev/null; then



echo -e "\nDisk Usage:"        echo ""    echo "Running containers:"

df -h

        echo "Files in firefly directory:"    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers or permission denied"

# Firefly-specific checks

print_header "FIREFLY-SPECIFIC CHECKS"        ls -la ~/firefly/ || echo "Failed to list files"    echo ""

if [ -f "$APP_DIR/.env" ]; then

    echo "Checking .env file for required variables:"            echo "All containers (including stopped):"

    for var in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DB_HOST APP_KEY OPENAI_API_KEY; do

        if grep -q "^$var=" "$APP_DIR/.env"; then        echo ""    docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No containers or permission denied"

            print_status "$var is set"

        else        echo "Docker Compose file exists: $([ -f ~/firefly/docker-compose.yaml ] && echo 'Yes' || echo 'No')"else

            print_warning "$var is not set or commented out"

        fi        echo "Configure script exists: $([ -f ~/firefly/configure-firefly.sh ] && echo 'Yes' || echo 'No')"    echo "❌ Cannot access Docker daemon"

    done

else        echo "Environment file exists: $([ -f ~/firefly/.env ] && echo 'Yes' || echo 'No')"fi

    print_error ".env file not found"

fi        echo ""



# Final Status        if [ -f ~/firefly/.env ]; then

print_header "DEBUG SUMMARY"

print_status "Debug information collection completed"            echo ""# Docker Compose Status

echo "Timestamp: $(date)"

echo ""            echo "Environment file contents (secrets hidden):"echo "=== DOCKER COMPOSE STATUS ==="

print_status "Key areas to check based on above output:"

echo "1. Ensure Docker is running and accessible"            cat ~/firefly/.env | sed 's/=.*/=***/' || echo "Failed to read .env"if [ -f docker-compose.yaml ]; then

echo "2. Verify application directory and files exist"

echo "3. Check .env file has all required variables"        fi    if docker compose ps &> /dev/null; then

echo "4. Ensure proper file permissions"

echo "5. Review any error messages in logs"    else        docker compose ps

echo ""

print_status "Debug script completed successfully"        log_error "Firefly directory not found at ~/firefly"    elif docker-compose ps &> /dev/null; then

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