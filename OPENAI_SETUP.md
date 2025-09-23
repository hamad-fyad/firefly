# OpenAI Integration Setup

This project now uses OpenAI's GPT models for intelligent transaction categorization instead of traditional machine learning.

## Setup Instructions

### 1. Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account if you don't have one
3. Generate a new API key
4. Copy the key (it starts with `sk-`)

### 2. Configure API Key
1. Open `.env` file in the project root
2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

### 3. Rebuild and Start Services
```bash
# Rebuild the AI service with OpenAI integration
docker-compose build ai-service

# Start all services
docker-compose up -d

# Check if AI service is healthy
docker logs firefly_iii_ai_service
```

## Features

### Intelligent Categorization
- Uses GPT-3.5-turbo for context-aware categorization
- Understands natural language transaction descriptions
- Learns from user feedback via few-shot learning
- Fallback to keyword-based categorization if API unavailable

### Available Categories
- Food & Drink
- Transportation
- Shopping
- Health & Fitness
- Entertainment
- Bills & Utilities
- Income
- Investment
- Education
- Travel
- Insurance
- Charity
- Other

### Benefits over Traditional ML
- **No training data required**: Works immediately with any transaction
- **Better accuracy**: Understands context and nuance
- **Multilingual support**: Can categorize transactions in any language
- **Self-improving**: Gets better with feedback examples
- **Robust**: Handles edge cases and new transaction types

## API Usage

The API endpoints remain the same:
- `POST /incoming` - Categorize new transactions
- `POST /feedback` - Learn from user corrections
- `GET /health` - Health check

## Cost Considerations

OpenAI API usage is pay-per-use:
- GPT-3.5-turbo: ~$0.001 per 1K tokens
- Average transaction: ~50 tokens
- Cost per transaction: ~$0.00005 (1/20th of a cent)
- For 1000 transactions/month: ~$0.05

## Troubleshooting

### No API Key
If `OPENAI_API_KEY` is missing, the service falls back to basic keyword matching.

### API Errors
Check logs with:
```bash
docker logs firefly_iii_ai_service --tail=50
```

Common issues:
- Invalid API key
- Rate limiting (wait and retry)
- Network connectivity
- Insufficient API credits