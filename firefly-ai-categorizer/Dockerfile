FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create volume mount points
VOLUME ["/app/data", "/app/logs"]

# Expose the port the app runs on
EXPOSE 8000

# Create a startup script
COPY app/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Command to run the application
CMD ["/app/startup.sh"]
