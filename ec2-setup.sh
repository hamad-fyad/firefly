#!/bin/bash#!/bin/bash



echo "=== EC2 System Setup Script ==="echo "=== EC2 Firefly Setup Script ==="

echo "Installing and configuring required dependencies on EC2"echo "This script will set up Docker and dependencies for Firefly III on EC2"

echo ""

# Colors for output

RED='\033[0;31m'# Check if running as root

GREEN='\033[0;32m'if [ "$EUID" -eq 0 ]; then

YELLOW='\033[1;33m'    echo "⚠️  Running as root. This is generally not recommended."

NC='\033[0m' # No Color    echo "Consider running as a regular user with sudo privileges."

fi

log_info() {

    echo -e "${GREEN}[INFO]${NC} $1"# Function to detect OS

}detect_os() {

    if [ -f /etc/os-release ]; then

log_warn() {        . /etc/os-release

    echo -e "${YELLOW}[WARN]${NC} $1"        OS=$NAME

}        VER=$VERSION_ID

    elif type lsb_release >/dev/null 2>&1; then

log_error() {        OS=$(lsb_release -si)

    echo -e "${RED}[ERROR]${NC} $1"        VER=$(lsb_release -sr)

}    elif [ -f /etc/lsb-release ]; then

        . /etc/lsb-release

# Update system packages        OS=$DISTRIB_ID

update_system() {        VER=$DISTRIB_RELEASE

    log_info "Updating system packages..."    else

            OS=$(uname -s)

    # Detect OS        VER=$(uname -r)

    if command -v apt-get &> /dev/null; then    fi

        # Ubuntu/Debian    echo "Detected OS: $OS $VER"

        sudo apt-get update -y}

        sudo apt-get upgrade -y

        sudo apt-get install -y curl wget git unzip# Install Docker on Ubuntu/Debian

    elif command -v yum &> /dev/null; theninstall_docker_ubuntu() {

        # Amazon Linux/CentOS    echo "Installing Docker on Ubuntu/Debian..."

        sudo yum update -y    

        sudo yum install -y curl wget git unzip    # Update package index

    else    sudo apt-get update

        log_warn "Unknown package manager, skipping system update"    

    fi    # Install packages to allow apt to use a repository over HTTPS

}    sudo apt-get install -y \

        apt-transport-https \

# Install Docker if not present        ca-certificates \

install_docker() {        curl \

    if command -v docker &> /dev/null; then        gnupg \

        log_info "Docker already installed: $(docker --version)"        lsb-release

        return 0

    fi    # Add Docker's official GPG key

        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    log_info "Installing Docker..."

        # Set up the stable repository

    # Install Docker using the official script    echo \

    curl -fsSL https://get.docker.com -o get-docker.sh        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \

    sudo sh get-docker.sh        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    

    # Add current user to docker group    # Update package index again

    sudo usermod -aG docker $USER    sudo apt-get update

    

    # Start Docker service    # Install Docker Engine

    sudo systemctl start docker    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    sudo systemctl enable docker

        # Start and enable Docker

    log_info "Docker installed successfully"    sudo systemctl start docker

}    sudo systemctl enable docker



# Install Docker Compose if not present    # Add current user to docker group

install_docker_compose() {    sudo usermod -aG docker $USER

    if command -v docker-compose &> /dev/null; then    

        log_info "Docker Compose already installed: $(docker-compose --version)"    echo "✅ Docker installed successfully"

        return 0}

    fi

    # Install Docker on Amazon Linux 2

    log_info "Installing Docker Compose..."install_docker_amazon_linux() {

        echo "Installing Docker on Amazon Linux..."

    # Get latest version    

    local latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)    # Update packages

        sudo yum update -y

    # Install Docker Compose    

    sudo curl -L "https://github.com/docker/compose/releases/download/${latest_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose    # Install Docker

    sudo chmod +x /usr/local/bin/docker-compose    sudo yum install -y docker

        

    # Create symlink if needed    # Start Docker service

    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose    sudo service docker start

        sudo systemctl enable docker

    log_info "Docker Compose installed successfully"    

}    # Add current user to docker group

    sudo usermod -aG docker $USER

# Setup firefly directory    

setup_firefly_directory() {    # Install Docker Compose

    log_info "Setting up Firefly III directory..."    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

        sudo chmod +x /usr/local/bin/docker-compose

    # Create directory if it doesn't exist    

    mkdir -p ~/firefly    echo "✅ Docker installed successfully"

    cd ~/firefly}

    

    # Set proper permissions# Main installation logic

    chmod 755 ~/fireflymain() {

        detect_os

    log_info "Firefly III directory ready"    

}    # Check if Docker is already installed

    if command -v docker &> /dev/null; then

# Configure system limits for Docker        echo "✅ Docker is already installed: $(docker --version)"

configure_system_limits() {        

    log_info "Configuring system limits for Docker..."        # Check if Docker is running

            if ! docker info &> /dev/null; then

    # Increase file limits            echo "🔄 Starting Docker service..."

    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf            sudo systemctl start docker

    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf        fi

        else

    # Configure Docker daemon        echo "📦 Installing Docker..."

    sudo mkdir -p /etc/docker        

    cat << EOF | sudo tee /etc/docker/daemon.json        case "$OS" in

{            *"Ubuntu"*|*"Debian"*)

    "log-driver": "json-file",                install_docker_ubuntu

    "log-opts": {                ;;

        "max-size": "10m",            *"Amazon Linux"*)

        "max-file": "3"                install_docker_amazon_linux

    },                ;;

    "storage-driver": "overlay2"            *)

}                echo "❌ Unsupported OS: $OS"

EOF                echo "Please install Docker manually: https://docs.docker.com/engine/install/"

                    exit 1

    # Restart Docker with new configuration                ;;

    sudo systemctl restart docker        esac

        fi

    log_info "System limits configured"    

}    # Configure firewall for required ports

    echo "🔧 Configuring firewall..."

# Main execution    

main() {    # For Ubuntu with UFW

    log_info "Starting EC2 system setup..."    if command -v ufw &> /dev/null; then

            sudo ufw allow 8080/tcp  # Firefly III

    # Update system        sudo ufw allow 8082/tcp  # AI Service

    update_system        sudo ufw allow 8001/tcp  # Webhook Service

            sudo ufw allow 81/tcp    # Data Importer

    # Install Docker        echo "✅ UFW rules added"

    install_docker    fi

        

    # Install Docker Compose    # For Amazon Linux with firewalld

    install_docker_compose    if command -v firewall-cmd &> /dev/null; then

            sudo firewall-cmd --permanent --add-port=8080/tcp

    # Setup directory        sudo firewall-cmd --permanent --add-port=8082/tcp

    setup_firefly_directory        sudo firewall-cmd --permanent --add-port=8001/tcp

            sudo firewall-cmd --permanent --add-port=81/tcp

    # Configure system        sudo firewall-cmd --reload

    configure_system_limits        echo "✅ Firewalld rules added"

        fi

    log_info "EC2 system setup completed successfully!"    

        # Install additional useful tools

    # Show versions    echo "🛠️  Installing additional tools..."

    echo ""    if command -v apt-get &> /dev/null; then

    echo "=== Installed Versions ==="        sudo apt-get install -y curl wget git htop net-tools

    echo "Docker: $(docker --version 2>/dev/null || echo 'Not available')"    elif command -v yum &> /dev/null; then

    echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not available')"        sudo yum install -y curl wget git htop net-tools

    echo "Current directory: $(pwd)"    fi

    echo "User: $(whoami)"    

    echo "Groups: $(groups)"    echo ""

}    echo "=== SETUP COMPLETE ==="

    echo "✅ Docker and dependencies installed"

# Run if executed directly    echo "✅ Firewall configured for Firefly III ports"

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then    echo "✅ Additional tools installed"

    main "$@"    echo ""

fi    echo "⚠️  IMPORTANT: You need to log out and log back in for Docker group changes to take effect"
    echo "    Or run: newgrp docker"
    echo ""
    echo "Next steps:"
    echo "1. Clone your Firefly repository"
    echo "2. Copy your environment files (.env, .db.env, .importer.env)"
    echo "3. Run: docker compose up -d"
    echo ""
}

# Run main function
main