# 🤖 ChatGPT Integration Troubleshooting Guide

## 🚨 Quick Diagnosis

If you feel the ChatGPT integration is not working, here's how to diagnose and fix it:

### 1. 🧪 Run the Diagnostic Tool

```bash
cd /Users/hamadfyad/Desktop/firefly
python3 test_chatgpt_integration.py
```

This will test:
- ✅ Environment variables
- 🏥 Service health
- 🤖 AI categorization
- 📡 Webhook simulation

### 2. 🔍 Check Service Logs

```bash
# Real-time logs
docker logs -f firefly_iii_ai_service

# Recent logs
docker logs --tail=50 firefly_iii_ai_service
```

Look for these log patterns:
- `🔑 Found OpenAI API key: sk-****` - API key detected
- `✅ OpenAI client initialized successfully` - Client working  
- `🎯 OpenAI prediction: '...' -> '...'` - Successful categorization
- `❌ OpenAI API call failed` - API issues

### 3. 📊 Check Service Status

```bash
curl http://localhost:8082/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_status": "available",
  "model_type": "openai",
  "database_status": "available"
}
```

### 4. 🧪 Test AI Endpoint Directly

```bash
curl -X POST http://localhost:8082/test-ai \
  -H "Content-Type: application/json" \
  -d '{"description": "Coffee from Starbucks"}'
```

### 5. 🔧 Debug Environment

```bash
curl http://localhost:8082/debug-env
```

## 🔧 Common Issues & Solutions

### Issue 1: "OpenAI client not available"

**Symptoms:**
```
❌ OPENAI_API_KEY not found in environment variables
⚠️ OpenAI client not available, using fallback categorization
```

**Solutions:**
1. Check if API key is set:
   ```bash
   docker exec firefly_iii_ai_service env | grep OPENAI_API_KEY
   ```

2. Set the API key in `.env` file:
   ```bash
   echo "OPENAI_API_KEY=sk-your-actual-key-here" >> .env
   ```

3. Restart the container:
   ```bash
   docker-compose restart ai-service
   ```

### Issue 2: "OpenAI API call failed"

**Symptoms:**
```
❌ OpenAI API call failed after 30s: timeout
🚫 Rate limit exceeded
💳 Quota exceeded - check OpenAI billing
```

**Solutions:**
1. **Timeout**: Check internet connection
2. **Rate Limit**: Wait and retry, implement rate limiting
3. **Quota**: Check OpenAI billing dashboard
4. **Invalid Key**: Generate new API key

### Issue 3: Categorization Returns "Uncategorized"

**Symptoms:**
```
✅ Transaction categorized: 'description' -> 'Uncategorized'
⚠️ Using fallback category: 'Uncategorized'
```

**Causes & Solutions:**
1. **OpenAI unavailable**: Check API key and quota
2. **Low confidence**: AI is unsure, this is normal behavior
3. **Parsing error**: Check logs for JSON parsing issues

### Issue 4: Categories Not Applied to Firefly

**Symptoms:**
- AI predicts category correctly
- Category not showing in Firefly III transactions

**Solutions:**
1. Check Firefly token:
   ```bash
   docker exec firefly_iii_ai_service env | grep FIREFLY_TOKEN
   ```

2. Test Firefly API:
   ```bash
   curl -H "Authorization: Bearer your-token" \
        http://localhost:8080/api/v1/about
   ```

3. Check webhook service logs:
   ```bash
   docker logs firefly_iii_webhook_service
   ```

## 📈 Enhanced Logging Levels

The service now includes detailed logging with emojis:

- `🔑` API key operations
- `🤖` AI processing
- `📡` API calls  
- `⚡` Performance metrics
- `✅` Success operations
- `❌` Errors
- `⚠️` Warnings

### Change Log Level

Set environment variable in docker-compose.yaml:
```yaml
ai-service:
  environment:
    LOG_LEVEL: DEBUG  # INFO, DEBUG, WARNING, ERROR
```

## 🧪 Testing Scenarios

### Test 1: Simple Categorization
```bash
python3 test_chatgpt_integration.py --description "McDonald's lunch"
```

### Test 2: Complex Transaction
```bash
python3 test_chatgpt_integration.py --description "AMAZON MKTP US*M45N67890 AMZN.COM/BILL WA"
```

### Test 3: Edge Case
```bash
python3 test_chatgpt_integration.py --description "ATM WITHDRAWAL"
```

## 🔄 Manual Test via Firefly III

1. Create a new transaction in Firefly III
2. Check AI service logs for categorization
3. Verify category appears in transaction
4. Check webhook service logs for any issues

## 📞 Still Not Working?

1. **Restart everything**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Check all logs**:
   ```bash
   docker-compose logs ai-service
   docker-compose logs webhook-service
   ```

3. **Verify network connectivity**:
   ```bash
   docker exec firefly_iii_ai_service ping -c 3 api.openai.com
   ```

4. **Test OpenAI directly**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer your-api-key"
   ```

The enhanced logging should now give you much better visibility into exactly where the ChatGPT integration might be failing!