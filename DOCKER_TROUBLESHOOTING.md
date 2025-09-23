# Docker Image Pull/Build Troubleshooting Guide

## Issues Identified and Fixed

### 1. Missing Environment Variables on EC2
**Problem**: The `DOCKER_USERNAME`, `AI_SERVICE_TAG`, and `WEBHOOK_SERVICE_TAG` environment variables were not being passed to the EC2 instance.

**Solution**: Updated the CI/CD workflow to include these variables in the `.env` file that gets deployed to EC2:

```bash
# Docker Configuration
DOCKER_USERNAME=${{ env.DOCKER_USERNAME }}
AI_SERVICE_TAG=${{ needs.build-and-push.outputs.version }}
WEBHOOK_SERVICE_TAG=${{ needs.build-and-push.outputs.version }}
```

### 2. Incorrect sed Commands
**Problem**: The workflow was trying to update image names using sed commands that didn't match the actual image names in docker-compose.yaml:

- Looking for: `fireflyiii/ai-categorizer:.*`
- Actual: `${DOCKER_USERNAME:-hamad}/firefly-ai-categorizer:${AI_SERVICE_TAG:-latest}`

**Solution**: Removed the sed commands since the docker-compose.yaml already uses environment variables properly.

### 3. Docker Compose Configuration
**Current Setup**: The docker-compose.yaml is properly configured with:

```yaml
ai-service:
  image: ${DOCKER_USERNAME:-hamad}/firefly-ai-categorizer:${AI_SERVICE_TAG:-latest}
  build:
    context: ./firefly-ai-categorizer

webhook-service:
  image: ${DOCKER_USERNAME:-hamad}/firefly-webhook-service:${WEBHOOK_SERVICE_TAG:-latest}
  build:
    context: ./webhook_service
```

This configuration:
- ✅ Pulls from Docker Hub when environment variables are set (production)
- ✅ Falls back to local build if images aren't found
- ✅ Uses default values for local development

## How the Fixed Flow Works

### CI/CD Pipeline:
1. **Build Stage**: Builds Docker images and pushes them to Docker Hub
2. **Deploy Stage**: 
   - Creates deployment files with correct environment variables
   - Copies files to EC2
   - Sets `DOCKER_USERNAME`, `AI_SERVICE_TAG`, `WEBHOOK_SERVICE_TAG` in `.env`
   - Runs `docker compose pull` (will pull from Docker Hub)
   - Runs `docker compose up -d`

### Local Development:
1. Environment variables default to `hamad` and `latest`
2. If images don't exist, Docker Compose builds them locally
3. Perfect for testing and development

## Testing the Setup

### Test 1: Verify Environment Variables
```bash
# On EC2, check if variables are set:
cd ~/firefly
grep -E "(DOCKER_USERNAME|AI_SERVICE_TAG|WEBHOOK_SERVICE_TAG)" .env
```

### Test 2: Test Image Pull
```bash
# Test pulling specific images:
docker pull hamad/firefly-ai-categorizer:latest
docker pull hamad/firefly-webhook-service:latest
```

### Test 3: Test Docker Compose
```bash
# Test compose pull and up:
cd ~/firefly
docker compose pull
docker compose up -d
```

## GitHub Secrets Required

Make sure these secrets are set in your GitHub repository:

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password/token
- `AWS_EC2_KEY`: Your EC2 private key
- `AWS_EC2_HOST`: Your EC2 instance IP/hostname
- `AWS_EC2_USER`: Your EC2 username (usually `ubuntu` or `ec2-user`)
- `OPENAI_API_KEY`: Your OpenAI API key
- `FIREFLY_BASE_URL`: Your Firefly III base URL (e.g., `http://your-ec2-ip:8080`)

## Common Issues and Solutions

### Issue: "Image not found" errors
**Cause**: Docker Hub images don't exist or wrong username
**Solution**: Check that images were built and pushed successfully in CI/CD

### Issue: "Permission denied" on EC2
**Cause**: User not in docker group
**Solution**: Run `sudo usermod -aG docker $USER` and restart session

### Issue: Services fail to start
**Cause**: Environment variables not set correctly
**Solution**: Check `.env` file on EC2 and verify all required variables are present

### Issue: Local development builds fail
**Cause**: Missing build context or Dockerfile
**Solution**: Ensure `firefly-ai-categorizer/Dockerfile` and `webhook_service/Dockerfile` exist