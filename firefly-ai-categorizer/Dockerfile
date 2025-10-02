FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && chmod 755 /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Default environment variables for AI service
ENV FIREFLY_API_URL=http://firefly-app:8080

# Create volume mount points
VOLUME ["/app/data", "/app/logs"]

# Expose the correct port (AI service runs on 8001)
EXPOSE 8001

# Simple health check without curl dependency
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health', timeout=5)" || exit 1

# Command to run the AI categorizer service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]
