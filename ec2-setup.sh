#!/bin/bash

echo "=== EC2 Firefly Setup Script ==="
echo "This script will set up Docker and dependencies for Firefly III on EC2"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. This is generally not recommended."
    echo "Consider running as a regular user with sudo privileges."
fi

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    echo "Detected OS: $OS $VER"
}

# Install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo "Installing Docker on Ubuntu/Debian..."
    
    # Update package index
    sudo apt-get update
    
    # Install packages to allow apt to use a repository over HTTPS
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Set up the stable repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Update package index again
    sudo apt-get update

    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker

    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo "✅ Docker installed successfully"
}

# Install Docker on Amazon Linux 2
install_docker_amazon_linux() {
    echo "Installing Docker on Amazon Linux..."
    
    # Update packages
    sudo yum update -y
    
    # Install Docker
    sudo yum install -y docker
    
    # Start Docker service
    sudo service docker start
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo "✅ Docker installed successfully"
}

# Main installation logic
main() {
    detect_os
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        echo "✅ Docker is already installed: $(docker --version)"
        
        # Check if Docker is running
        if ! docker info &> /dev/null; then
            echo "🔄 Starting Docker service..."
            sudo systemctl start docker
        fi
    else
        echo "📦 Installing Docker..."
        
        case "$OS" in
            *"Ubuntu"*|*"Debian"*)
                install_docker_ubuntu
                ;;
            *"Amazon Linux"*)
                install_docker_amazon_linux
                ;;
            *)
                echo "❌ Unsupported OS: $OS"
                echo "Please install Docker manually: https://docs.docker.com/engine/install/"
                exit 1
                ;;
        esac
    fi
    
    # Configure firewall for required ports
    echo "🔧 Configuring firewall..."
    
    # For Ubuntu with UFW
    if command -v ufw &> /dev/null; then
        sudo ufw allow 8080/tcp  # Firefly III
        sudo ufw allow 8082/tcp  # AI Service
        sudo ufw allow 8001/tcp  # Webhook Service
        sudo ufw allow 81/tcp    # Data Importer
        echo "✅ UFW rules added"
    fi
    
    # For Amazon Linux with firewalld
    if command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=8080/tcp
        sudo firewall-cmd --permanent --add-port=8082/tcp
        sudo firewall-cmd --permanent --add-port=8001/tcp
        sudo firewall-cmd --permanent --add-port=81/tcp
        sudo firewall-cmd --reload
        echo "✅ Firewalld rules added"
    fi
    
    # Install additional useful tools
    echo "🛠️  Installing additional tools..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y curl wget git htop net-tools
    elif command -v yum &> /dev/null; then
        sudo yum install -y curl wget git htop net-tools
    fi
    
    echo ""
    echo "=== SETUP COMPLETE ==="
    echo "✅ Docker and dependencies installed"
    echo "✅ Firewall configured for Firefly III ports"
    echo "✅ Additional tools installed"
    echo ""
    echo "⚠️  IMPORTANT: You need to log out and log back in for Docker group changes to take effect"
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