#!/bin/bash
set -e

echo "Starting Firefly AI Categorizer..."

# Initialize model if it doesn't exist
if [ ! -f "/app/data/models/current_model.pkl" ]; then
    echo "No trained model found. Initializing with basic training data..."
    cd /app
    if python -m app.initialize_model; then
        echo "Model initialization successful!"
    else
        echo "Model initialization failed, but continuing with service startup..."
        echo "Service will use default categories until model is available."
    fi
else
    echo "Existing model found, skipping initialization."
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000