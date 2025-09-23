# 🚀 Complete CI/CD Setup Guide for Firefly III AI Stack

This guide will help you set up a complete CI/CD pipeline that automatically builds, tests, and deploys your Firefly III AI categorizer and webhook services to AWS EC2.

## 📋 Prerequisites

### 1. GitHub Repository Setup
- ✅ Fork or clone this repository
- ✅ Ensure you have admin access to set up secrets

### 2. Docker Hub Account
- ✅ Create account at [Docker Hub](https://hub.docker.com)
- ✅ Create repositories:
  - `your-username/firefly-ai-categorizer`
  - `your-username/firefly-webhook-service`

### 3. AWS EC2 Instance
- ✅ Launch EC2 instance (recommended: t3.medium or larger)
- ✅ Configure Security Groups (see below)
- ✅ Generate SSH key pair

### 4. OpenAI API Key
- ✅ Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## 🔧 Step-by-Step Setup

### Step 1: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
AWS_EC2_HOST=your-ec2-public-ip
AWS_EC2_USER=ubuntu (or ec2-user for Amazon Linux)
AWS_EC2_PRIVATE_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
...your-private-key-content...
-----END OPENSSH PRIVATE KEY-----
FIREFLY_BASE_URL=http://your-ec2-ip:8080
OPENAI_API_KEY=sk-your-openai-api-key
```

### Step 2: Configure EC2 Security Groups

Your EC2 security group should allow inbound traffic on:

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Your IP | SSH access |
| 8080 | TCP | 0.0.0.0/0 | Firefly III |
| 8082 | TCP | 0.0.0.0/0 | AI Categorizer |
| 8001 | TCP | 0.0.0.0/0 | Webhook Service |
| 81 | TCP | 0.0.0.0/0 | Data Importer |

### Step 3: Update Environment Files

#### Update `.env` file:
```bash
# Replace with your values
DOCKER_USERNAME=your-dockerhub-username
AI_SERVICE_TAG=latest
WEBHOOK_SERVICE_TAG=latest

# Update these for EC2 deployment
APP_URL=http://your-ec2-ip:8080
FIREFLY_URL=http://your-ec2-ip:8080
```

#### Update `config.py`:
```python
# Your current config.py already handles environment switching correctly!
# It will automatically use FIREFLY_TOKEN2 for EC2 and FIREFLY_TOKEN for local
```

### Step 4: Build and Test Locally (Optional)

```bash
# Test locally first
docker compose up -d

# Wait for services to start
sleep 30

# Configure Firefly III
./configure-firefly.sh

# Validate deployment
./validate-deployment.sh
```

### Step 5: Deploy via CI/CD

#### Option A: Automatic Deployment (Recommended)
```bash
# Simply push to main branch
git add .
git commit -m "feat: setup complete CI/CD pipeline"
git push origin main
```

#### Option B: Manual Deployment Trigger
Go to GitHub → Actions → "🚀 CI/CD - Build, Deploy & Test Firefly AI Stack" → "Run workflow"

## 🎯 What the CI/CD Pipeline Does

### 🔨 Build Phase
1. **Docker Images**: Builds AI categorizer and webhook service images
2. **Multi-Platform**: Builds for both AMD64 and ARM64 architectures
3. **Security Scanning**: Scans images for vulnerabilities with Trivy
4. **Push to Registry**: Pushes images to Docker Hub with version tags

### 🚀 Deploy Phase
1. **Environment Setup**: Ensures Docker and dependencies are installed on EC2
2. **File Transfer**: Copies configuration files and scripts to EC2
3. **Service Update**: Pulls latest images and restarts services
4. **Auto-Configuration**: Automatically configures Firefly III settings:
   - ✅ Enables user registration for testing
   - ✅ Creates admin account
   - ✅ Generates API tokens
   - ✅ Configures database connections

### 🧪 Validation Phase
1. **Health Checks**: Validates all services are running
2. **API Testing**: Tests API endpoints with authentication
3. **Network Testing**: Verifies port accessibility
4. **Integration Testing**: Ensures services communicate correctly

## 🎉 Post-Deployment

### Accessing Your Services

After successful deployment, you can access:

- **Firefly III**: `http://your-ec2-ip:8080`
- **AI Categorizer**: `http://your-ec2-ip:8082/health`
- **Webhook Service**: `http://your-ec2-ip:8001/health`
- **Data Importer**: `http://your-ec2-ip:81`

### Default Admin Credentials
- **Email**: `admin@firefly.ec2`
- **Password**: `admin123456`

### API Tokens
The pipeline automatically generates and configures API tokens. Check your EC2 `.env` file for the generated tokens.

## 🔧 Troubleshooting

### Debug Scripts Available

1. **EC2 Environment Debug**:
   ```bash
   ssh ubuntu@your-ec2-ip
   cd ~/firefly
   ./ec2-debug.sh
   ```

2. **Validate Deployment**:
   ```bash
   ./validate-deployment.sh
   ```

3. **Manual Configuration**:
   ```bash
   ./configure-firefly.sh
   ```

### Common Issues

#### 1. Docker Permission Issues
```bash
# On EC2, if you get permission denied:
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. Services Not Starting
```bash
# Check logs
docker compose logs

# Restart services
docker compose down
docker compose up -d
```

#### 3. API Token Issues
```bash
# Regenerate tokens
./configure-firefly.sh
```

#### 4. Network Issues
```bash
# Check EC2 security groups
# Ensure ports 8080, 8082, 8001, 81 are open
```

## 📊 Monitoring and Maintenance

### View Deployment Status
- Check GitHub Actions for build/deploy status
- Monitor EC2 CloudWatch metrics
- Use the validation script for health checks

### Update Services
Simply push code changes to trigger automatic rebuilding and deployment:

```bash
git add .
git commit -m "feat: update AI categorizer logic"
git push origin main
```

### Manual Updates
If you need to update only specific services:

```bash
# SSH to EC2
ssh ubuntu@your-ec2-ip
cd ~/firefly

# Pull latest images
docker compose pull

# Restart specific service
docker compose up -d ai-service
```

## 🎯 Testing Your Setup

### Run Full Integration Test
```bash
# This tests everything end-to-end
curl -X POST http://your-ec2-ip:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "transaction categorization"}'
```

### Check AI Service Health
```bash
curl http://your-ec2-ip:8082/health
```

### Validate Firefly API
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://your-ec2-ip:8080/api/v1/about
```

## 🔒 Security Notes

1. **Environment Variables**: Never commit real API keys to repository
2. **SSH Keys**: Store private keys only in GitHub Secrets
3. **Firewall**: Configure EC2 security groups properly
4. **Passwords**: Change default admin password after first login
5. **Tokens**: Rotate API tokens regularly

## 📚 Additional Resources

- [Firefly III Documentation](https://docs.firefly-iii.org/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

🎉 **Congratulations!** You now have a complete CI/CD pipeline that automatically handles building, testing, and deploying your Firefly III AI stack with zero-downtime updates!