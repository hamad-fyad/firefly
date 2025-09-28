# Database Setup for AI Categorizer

This document explains how to set up and troubleshoot the database for the AI Categorizer service.

## 🏗️ Architecture

The AI Categorizer uses PostgreSQL to store:
- **Model Metrics**: Training performance and version information
- **Prediction Logs**: Individual categorization results with confidence scores
- **Accuracy Feedback**: User corrections for continuous learning

## 🚀 Automatic Setup

The service will automatically initialize the database on startup:

1. **Docker Compose**: The `ai-db` service creates a PostgreSQL instance
2. **Startup Script**: `app/startup.sh` runs `app/init_database.py`
3. **Fallback**: If database fails, the service uses file storage

## 🔧 Manual Database Initialization

If automatic initialization fails, you can manually create the tables:

### Option 1: Using SQL Script

```bash
# Connect to the PostgreSQL container
docker exec -it firefly_iii_ai_db psql -U ai_user -d ai_metrics

# Run the initialization script
\i /path/to/init_database.sql
```

### Option 2: Using Python Script

```bash
# From inside the AI service container
docker exec -it firefly_iii_ai_service python -m app.init_database
```

## 🩺 Health Check & Troubleshooting

### Check Service Status

```bash
curl http://localhost:8082/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_status": "available", 
  "model_type": "openai",
  "database_status": "available",
  "storage_mode": "database"
}
```

### Common Issues

#### 1. "relation 'accuracy_feedback' does not exist"

**Symptoms**: Logs show SQL errors about missing tables
```
psycopg2.errors.UndefinedTable) relation "accuracy_feedback" does not exist
```

**Solution**: Run database initialization
```bash
docker exec -it firefly_iii_ai_service python -m app.init_database
```

#### 2. Database Connection Failed

**Symptoms**: `database_status: "error"` in health check

**Solutions**:
1. Check PostgreSQL container is running:
   ```bash
   docker ps | grep ai_db
   ```

2. Check database connection settings in docker-compose.yaml:
   ```yaml
   environment:
     DATABASE_URL: postgresql://ai_user:ai_password@ai-db:5432/ai_metrics
   ```

3. Restart the database container:
   ```bash
   docker-compose restart ai-db
   ```

#### 3. File Storage Fallback

**Symptoms**: `storage_mode: "file"` in health check

**What it means**: Database unavailable, using local files instead
- ✅ Service still works
- ❌ No advanced metrics/learning
- 🔄 Will auto-switch when database is available

## 📊 Database Schema

### model_metrics
Stores AI model performance data:
```sql
id              SERIAL PRIMARY KEY
version_id      VARCHAR(100) -- Model version identifier  
timestamp       TIMESTAMP    -- When model was trained
metrics         JSONB        -- Performance metrics (accuracy, precision, etc.)
training_size   INTEGER      -- Number of training samples
test_size       INTEGER      -- Number of test samples
```

### prediction_logs  
Records individual AI predictions:
```sql
id                  SERIAL PRIMARY KEY
version_id          VARCHAR(100) -- Model version used
timestamp           TIMESTAMP    -- Prediction time
description         TEXT         -- Transaction description
predicted_category  VARCHAR(100) -- AI's prediction
confidence          FLOAT        -- AI confidence (0-1)
actual_category     VARCHAR(100) -- User's correction (nullable)
```

### accuracy_feedback
Tracks user corrections for learning:
```sql
id                  SERIAL PRIMARY KEY
prediction_id       INTEGER      -- Reference to prediction_logs.id
description         TEXT         -- Transaction description  
predicted_category  VARCHAR(100) -- What AI predicted
actual_category     VARCHAR(100) -- What user corrected to
confidence          FLOAT        -- Original AI confidence
is_correct          INTEGER      -- 1=correct, 0=incorrect
feedback_source     VARCHAR(50)  -- 'user', 'auto', 'manual'
timestamp           TIMESTAMP    -- Feedback time
```

## 🔄 Backup & Recovery

### Export Data
```bash
docker exec firefly_iii_ai_db pg_dump -U ai_user ai_metrics > ai_backup.sql
```

### Import Data  
```bash
docker exec -i firefly_iii_ai_db psql -U ai_user ai_metrics < ai_backup.sql
```

## 📈 Monitoring

### Check Database Size
```sql
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation 
FROM pg_stats 
WHERE schemaname = 'public';
```

### View Recent Activity
```sql
-- Recent predictions
SELECT * FROM prediction_logs ORDER BY timestamp DESC LIMIT 10;

-- Accuracy by category  
SELECT 
    predicted_category,
    AVG(is_correct::float) as accuracy,
    COUNT(*) as total_feedback
FROM accuracy_feedback 
GROUP BY predicted_category 
ORDER BY total_feedback DESC;
```

## 🐳 Docker Configuration

The database is configured in `docker-compose.yaml`:

```yaml
ai-db:
  image: postgres:15-alpine
  container_name: firefly_iii_ai_db
  environment:
    POSTGRES_DB: ai_metrics
    POSTGRES_USER: ai_user  
    POSTGRES_PASSWORD: ai_password
  ports:
    - "5433:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ai_user -d ai_metrics"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## 🔐 Security Notes

- Database credentials are in environment variables
- Default ports avoid conflicts (5433 instead of 5432)
- Network isolated within Docker Compose
- Regular PostgreSQL security best practices apply

## 📞 Support

If you encounter database issues:

1. Check the health endpoint: `curl http://localhost:8082/health`
2. Review container logs: `docker logs firefly_iii_ai_service`
3. Verify database container: `docker logs firefly_iii_ai_db`
4. Test manual initialization: `docker exec -it firefly_iii_ai_service python -m app.init_database`

The service is designed to be resilient - it will work with file storage even if the database is unavailable.