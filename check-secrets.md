# 🔑 GitHub Secrets Checklist

## Required Secrets for CI/CD

Go to: `https://github.com/hamad-fyad/firefly/settings/secrets/actions`

### ✅ Check these secrets exist:

1. **DOCKER_USERNAME**
   - Your Docker Hub username
   - Example: `hamad-fyad`

2. **DOCKER_PASSWORD** 
   - Your Docker Hub password or access token
   - Get from: https://hub.docker.com/settings/security

3. **AWS_EC2_HOST**
   - Your EC2 instance public IP or hostname
   - Example: `3.15.123.45` or `ec2-3-15-123-45.us-east-2.compute.amazonaws.com`

4. **AWS_EC2_USER**
   - SSH username for your EC2 instance
   - Usually: `ubuntu` (for Ubuntu) or `ec2-user` (for Amazon Linux)

5. **AWS_EC2_PRIVATE_KEY**
   - Your EC2 private key file content
   - Should start with `-----BEGIN RSA PRIVATE KEY-----` or similar
   - Copy entire content including headers/footers

6. **FIREFLY_BASE_URL**
   - Your Firefly III application URL
   - Example: `http://3.15.123.45:8080`

7. **OPENAI_API_KEY**
   - Your OpenAI API key
   - Should start with `sk-`

## 🐛 Common Issues:

- **Missing Secrets**: Deployment job gets skipped
- **Wrong EC2 Key**: SSH connection fails  
- **Wrong Host/User**: SSH connection fails
- **Wrong Docker Credentials**: Image push fails
- **Missing OpenAI Key**: AI service fails

## 🧪 Test Commands:

Run the "Test Deploy - Manual EC2 Deployment" workflow to debug conditions without running full build.