#!/bin/bash

echo "=== EC2 System Setup Script ==="
echo "Installing and configuring required dependencies on EC2"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging helpers
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Exit on error
set -e

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    log_info "Detected OS: $OS $VER"
}

# Install Docker + Compose on Ubuntu/Debian
install_docker_ubuntu() {
    log_info "Installing Docker on Ubuntu/Debian..."
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Try to add Docker GPG key with proper flags for non-interactive environment
    if ! curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null; then
        log_warn "GPG method failed, trying alternative Docker installation..."
        # Fallback: use snap or direct package installation
        if command -v snap >/dev/null 2>&1; then
            log_info "Installing Docker via snap..."
            sudo snap install docker
        else
            log_info "Installing Docker via default repository..."
            sudo apt-get install -y docker.io docker-compose
        fi
    else
        # Continue with official Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
            https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
            | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        sudo apt-get update -y
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    log_success "Docker installed successfully"

    # Docker Compose
    local latest_version
    latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${latest_version}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    log_success "Docker Compose installed successfully"
}

# Install Docker + Compose on Amazon Linux/CentOS
install_docker_amazon() {
    log_info "Installing Docker on Amazon Linux/CentOS..."
    sudo yum update -y
    sudo yum install -y docker curl wget git unzip
    sudo systemctl start docker
    sudo systemctl enable docker
    log_success "Docker installed successfully"

    local latest_version
    latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${latest_version}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    log_success "Docker Compose installed successfully"
}

# Setup application directory
setup_firefly_directory() {
    log_info "Setting up Firefly directory..."
    mkdir -p ~/firefly-ai
    sudo chown -R $USER:$USER ~/firefly-ai

    cat > ~/firefly-ai/.env <<EOF
# Database Configuration
POSTGRES_DB=firefly
POSTGRES_USER=firefly
POSTGRES_PASSWORD=firefly123
DB_CONNECTION=pgsql
DB_HOST=db
DB_PORT=5432
DB_DATABASE=firefly
DB_USERNAME=firefly
DB_PASSWORD=firefly123

# Firefly III Configuration
APP_KEY=SomeRandomStringOf32CharsExactly
SITE_OWNER=admin@example.com
APP_URL=http://localhost
TRUSTED_PROXIES=**

# AI Service Configuration
OPENAI_API_KEY=your-openai-api-key-here
AI_SERVICE_URL=http://firefly-ai-categorizer:8000

# Webhook Configuration
WEBHOOK_URL=http://webhook_service:5000/webhook
EOF

    log_success "Firefly directory and .env created"
}

# Main
main() {
    detect_os
    case "$OS" in
        *"Ubuntu"*|*"Debian"*) install_docker_ubuntu ;;
        *"Amazon Linux"*|*"CentOS"*) install_docker_amazon ;;
        *) log_error "Unsupported OS: $OS. Install Docker manually."; exit 1 ;;
    esac
    setup_firefly_directory
    log_success "EC2 setup complete! Ready for application deployment."
}

main "$@"
