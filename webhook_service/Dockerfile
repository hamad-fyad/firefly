FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Default environment variables for webhook service
ENV AI_SERVICE_URL=http://ai-service:8001
ENV FIREFLY_API_URL=http://firefly-app:8080

# Create volume mount points
VOLUME ["/app/logs"]

# Expose the correct port (webhook service runs on 8000)
EXPOSE 8000

# Simple health check without curl dependency
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Command to run the webhook service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
