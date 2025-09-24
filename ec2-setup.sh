#!/bin/bash#!/bin/bash#!/bin/bash



echo "=== EC2 System Setup Script ==="

echo "Installing and configuring required dependencies on EC2"

echo ""echo "=== EC2 System Setup Script ==="echo "=== EC2 System Setup Script ==="



# Colors for outputecho "Installing and configuring required dependencies on EC2"echo "Installing and configuring required dependencies on EC2"

RED='\033[0;31m'

GREEN='\033[0;32m'echo ""echo ""

YELLOW='\033[1;33m'

BLUE='\033[0;34m'

NC='\033[0m' # No Color

# Colors for output# Colors for output

# Function to print status messages

print_status() {RED='\033[0;31m'

    echo -e "${BLUE}[INFO]${NC} $1"

}GREEN='\033[0;32m'RED='\033[0;31m'# Check if running as root



print_success() {YELLOW='\033[1;33m'

    echo -e "${GREEN}[SUCCESS]${NC} $1"

}BLUE='\033[0;34m'GREEN='\033[0;32m'if [ "$EUID" -eq 0 ]; then



print_warning() {NC='\033[0m' # No Color

    echo -e "${YELLOW}[WARNING]${NC} $1"

}YELLOW='\033[1;33m'    echo "⚠️  Running as root. This is generally not recommended."



print_error() {# Function to print status messages

    echo -e "${RED}[ERROR]${NC} $1"

}print_status() {NC='\033[0m' # No Color    echo "Consider running as a regular user with sudo privileges."



# Function to check if command succeeded    echo -e "${BLUE}[INFO]${NC} $1"

check_command() {

    if [ $? -eq 0 ]; then}fi

        print_success "$1"

    else

        print_error "$2"

        exit 1print_success() {log_info() {

    fi

}    echo -e "${GREEN}[SUCCESS]${NC} $1"



print_status "Starting EC2 system setup..."}    echo -e "${GREEN}[INFO]${NC} $1"# Function to detect OS



# Update system packages

print_status "Updating system packages..."

sudo yum update -yprint_warning() {}detect_os() {

check_command "System packages updated successfully" "Failed to update system packages"

    echo -e "${YELLOW}[WARNING]${NC} $1"

# Install Docker

print_status "Installing Docker..."}    if [ -f /etc/os-release ]; then

sudo yum install -y docker

check_command "Docker installed successfully" "Failed to install Docker"



# Start and enable Docker serviceprint_error() {log_warn() {        . /etc/os-release

print_status "Starting Docker service..."

sudo systemctl start docker    echo -e "${RED}[ERROR]${NC} $1"

check_command "Docker service started" "Failed to start Docker service"

}    echo -e "${YELLOW}[WARN]${NC} $1"        OS=$NAME

sudo systemctl enable docker

check_command "Docker service enabled for auto-start" "Failed to enable Docker service"



# Add ec2-user to docker group# Function to check if command succeeded}        VER=$VERSION_ID

print_status "Adding ec2-user to docker group..."

sudo usermod -a -G docker ec2-usercheck_command() {

check_command "User added to docker group" "Failed to add user to docker group"

    if [ $? -eq 0 ]; then    elif type lsb_release >/dev/null 2>&1; then

# Install Docker Compose

print_status "Installing Docker Compose..."        print_success "$1"

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

check_command "Docker Compose downloaded" "Failed to download Docker Compose"    elselog_error() {        OS=$(lsb_release -si)



sudo chmod +x /usr/local/bin/docker-compose        print_error "$2"

check_command "Docker Compose made executable" "Failed to make Docker Compose executable"

        exit 1    echo -e "${RED}[ERROR]${NC} $1"        VER=$(lsb_release -sr)

# Verify installations

print_status "Verifying installations..."    fi

docker --version

check_command "Docker version check passed" "Docker installation verification failed"}}    elif [ -f /etc/lsb-release ]; then



docker-compose --version

check_command "Docker Compose version check passed" "Docker Compose installation verification failed"

print_status "Starting EC2 system setup..."        . /etc/lsb-release

# Install git (if not already installed)

print_status "Installing Git..."

sudo yum install -y git

check_command "Git installed successfully" "Failed to install Git"# Update system packages# Update system packages        OS=$DISTRIB_ID



# Install unzip (useful for extracting files)print_status "Updating system packages..."

print_status "Installing unzip utility..."

sudo yum install -y unzipsudo yum update -yupdate_system() {        VER=$DISTRIB_RELEASE

check_command "Unzip installed successfully" "Failed to install unzip"

check_command "System packages updated successfully" "Failed to update system packages"

# Create necessary directories

print_status "Creating application directories..."    log_info "Updating system packages..."    else

mkdir -p /home/ec2-user/firefly-ai

check_command "Application directory created" "Failed to create application directory"# Install Docker



# Set proper permissionsprint_status "Installing Docker..."            OS=$(uname -s)

print_status "Setting directory permissions..."

sudo chown -R ec2-user:ec2-user /home/ec2-user/firefly-aisudo yum install -y docker

check_command "Directory permissions set" "Failed to set directory permissions"

check_command "Docker installed successfully" "Failed to install Docker"    # Detect OS        VER=$(uname -r)

print_success "EC2 system setup completed successfully!"

print_status "System is ready for Firefly III deployment"

print_warning "Remember to:"

print_warning "1. Update OPENAI_API_KEY in .env file"# Start and enable Docker service    if command -v apt-get &> /dev/null; then    fi

print_warning "2. Update APP_URL with your actual domain/IP"

print_warning "3. Generate a new APP_KEY for security"print_status "Starting Docker service..."

print_warning "4. Log out and back in for docker group changes to take effect"

sudo systemctl start docker        # Ubuntu/Debian    echo "Detected OS: $OS $VER"

echo ""

print_status "Setup Summary:"check_command "Docker service started" "Failed to start Docker service"

echo "  ✓ System packages updated"

echo "  ✓ Docker installed and configured"        sudo apt-get update -y}

echo "  ✓ Docker Compose installed"

echo "  ✓ Git installed"sudo systemctl enable docker

echo "  ✓ Application directories created"

echo ""check_command "Docker service enabled for auto-start" "Failed to enable Docker service"        sudo apt-get upgrade -y

print_success "EC2 setup complete! Ready for application deployment."


# Add ec2-user to docker group        sudo apt-get install -y curl wget git unzip# Install Docker on Ubuntu/Debian

print_status "Adding ec2-user to docker group..."

sudo usermod -a -G docker ec2-user    elif command -v yum &> /dev/null; theninstall_docker_ubuntu() {

check_command "User added to docker group" "Failed to add user to docker group"

        # Amazon Linux/CentOS    echo "Installing Docker on Ubuntu/Debian..."

# Install Docker Compose

print_status "Installing Docker Compose..."        sudo yum update -y    

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

check_command "Docker Compose downloaded" "Failed to download Docker Compose"        sudo yum install -y curl wget git unzip    # Update package index



sudo chmod +x /usr/local/bin/docker-compose    else    sudo apt-get update

check_command "Docker Compose made executable" "Failed to make Docker Compose executable"

        log_warn "Unknown package manager, skipping system update"    

# Verify installations

print_status "Verifying installations..."    fi    # Install packages to allow apt to use a repository over HTTPS

docker --version

check_command "Docker version check passed" "Docker installation verification failed"}    sudo apt-get install -y \



docker-compose --version        apt-transport-https \

check_command "Docker Compose version check passed" "Docker Compose installation verification failed"

# Install Docker if not present        ca-certificates \

# Install git (if not already installed)

print_status "Installing Git..."install_docker() {        curl \

sudo yum install -y git

check_command "Git installed successfully" "Failed to install Git"    if command -v docker &> /dev/null; then        gnupg \



# Install unzip (useful for extracting files)        log_info "Docker already installed: $(docker --version)"        lsb-release

print_status "Installing unzip utility..."

sudo yum install -y unzip        return 0

check_command "Unzip installed successfully" "Failed to install unzip"

    fi    # Add Docker's official GPG key

# Create necessary directories

print_status "Creating application directories..."        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

mkdir -p /home/ec2-user/firefly-ai

check_command "Application directory created" "Failed to create application directory"    log_info "Installing Docker..."



# Set proper permissions        # Set up the stable repository

print_status "Setting directory permissions..."

sudo chown -R ec2-user:ec2-user /home/ec2-user/firefly-ai    # Install Docker using the official script    echo \

check_command "Directory permissions set" "Failed to set directory permissions"

    curl -fsSL https://get.docker.com -o get-docker.sh        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \

# Create .env file with default values

print_status "Creating default .env file..."    sudo sh get-docker.sh        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

cat > /home/ec2-user/firefly-ai/.env << 'EOF'

# Database Configuration    

POSTGRES_DB=firefly

POSTGRES_USER=firefly    # Add current user to docker group    # Update package index again

POSTGRES_PASSWORD=firefly123

DB_CONNECTION=pgsql    sudo usermod -aG docker $USER    sudo apt-get update

DB_HOST=db

DB_PORT=5432    

DB_DATABASE=firefly

DB_USERNAME=firefly    # Start Docker service    # Install Docker Engine

DB_PASSWORD=firefly123

    sudo systemctl start docker    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Firefly III Configuration

APP_KEY=SomeRandomStringOf32CharsExactly    sudo systemctl enable docker

SITE_OWNER=admin@example.com

APP_URL=http://localhost        # Start and enable Docker

TRUSTED_PROXIES=**

    log_info "Docker installed successfully"    sudo systemctl start docker

# AI Service Configuration

OPENAI_API_KEY=your-openai-api-key-here}    sudo systemctl enable docker

AI_SERVICE_URL=http://firefly-ai-categorizer:8000



# Webhook Configuration

WEBHOOK_URL=http://webhook_service:5000/webhook# Install Docker Compose if not present    # Add current user to docker group

EOF

check_command "Default .env file created" "Failed to create .env file"install_docker_compose() {    sudo usermod -aG docker $USER



print_success "EC2 system setup completed successfully!"    if command -v docker-compose &> /dev/null; then    

print_status "System is ready for Firefly III deployment"

print_warning "Remember to:"        log_info "Docker Compose already installed: $(docker-compose --version)"    echo "✅ Docker installed successfully"

print_warning "1. Update OPENAI_API_KEY in .env file"

print_warning "2. Update APP_URL with your actual domain/IP"        return 0}

print_warning "3. Generate a new APP_KEY for security"

print_warning "4. Log out and back in for docker group changes to take effect"    fi



echo ""    # Install Docker on Amazon Linux 2

print_status "Setup Summary:"

echo "  ✓ System packages updated"    log_info "Installing Docker Compose..."install_docker_amazon_linux() {

echo "  ✓ Docker installed and configured"

echo "  ✓ Docker Compose installed"        echo "Installing Docker on Amazon Linux..."

echo "  ✓ Git installed"

echo "  ✓ Application directories created"    # Get latest version    

echo "  ✓ Default .env file created"

echo ""    local latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)    # Update packages

print_success "EC2 setup complete! Ready for application deployment."
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