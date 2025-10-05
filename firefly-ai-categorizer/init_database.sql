-- AI Categorizer Database Schema
-- Run this SQL script to manually create the required tables

-- Create model_metrics table
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metrics JSONB NOT NULL,
    training_size INTEGER NOT NULL,
    test_size INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_version_id ON model_metrics(version_id);

-- Create prediction_logs table
CREATE TABLE IF NOT EXISTS prediction_logs (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    predicted_category VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    actual_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prediction_logs_version_id ON prediction_logs(version_id);

-- Create accuracy_feedback table
CREATE TABLE IF NOT EXISTS accuracy_feedback (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    predicted_category VARCHAR(100) NOT NULL,
    actual_category VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    is_correct INTEGER NOT NULL,
    feedback_source VARCHAR(50) DEFAULT 'user' NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_accuracy_feedback_prediction_id ON accuracy_feedback(prediction_id);
CREATE INDEX IF NOT EXISTS idx_accuracy_feedback_predicted_category ON accuracy_feedback(predicted_category);

-- Insert sample data (optional)
-- This helps test the tables and provides some initial data

INSERT INTO model_metrics (version_id, metrics, training_size, test_size) 
VALUES ('initial_20250928', '{"accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1_score": 0.9}', 50, 0)
ON CONFLICT DO NOTHING;

-- Verify tables were created
SELECT 'model_metrics' as table_name, COUNT(*) as row_count FROM model_metrics
UNION ALL
SELECT 'prediction_logs' as table_name, COUNT(*) as row_count FROM prediction_logs  
UNION ALL
SELECT 'accuracy_feedback' as table_name, COUNT(*) as row_count FROM accuracy_feedback;