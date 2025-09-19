import json
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Any
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

METRICS_DIR = Path("/app/data/metrics")
METRICS_FILE = METRICS_DIR / "model_metrics.json"

class MetricsError(Exception):
    """Custom exception for metrics-related errors."""
    pass

def initialize_metrics_storage() -> None:
    """Initialize metrics storage directory and files."""
    try:
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        if not METRICS_FILE.exists():
            save_metrics_data({"models": [], "predictions": []})
    except Exception as e:
        logger.error("Failed to initialize metrics storage: %s", str(e))
        raise MetricsError(f"Metrics storage initialization failed: {str(e)}")

def save_metrics_data(data: Dict[str, List]) -> None:
    """Save metrics data to file."""
    with open(METRICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_metrics_data() -> Dict[str, List]:
    """Load metrics data from file."""
    try:
        if not METRICS_FILE.exists():
            return {"models": [], "predictions": []}
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise MetricsError(f"Invalid metrics file format: {str(e)}")

def calculate_model_metrics(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict[str, Any]:
    """
    Calculate comprehensive model metrics.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        labels: List of unique category labels
        
    Returns:
        Dictionary of metrics
    """
    # Calculate basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted'
    )
    
    # Calculate confusion matrix
    conf_matrix = confusion_matrix(y_true, y_pred, labels=labels)
    
    # Convert confusion matrix to list for JSON serialization
    conf_matrix_list = conf_matrix.tolist()
    
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "confusion_matrix": conf_matrix_list,
        "labels": labels
    }

def record_model_metrics(
    version_id: str,
    metrics: Dict[str, Any],
    training_size: int,
    test_size: int
) -> None:
    """
    Record metrics for a trained model.
    
    Args:
        version_id: Model version ID
        metrics: Dictionary of calculated metrics
        training_size: Number of training samples
        test_size: Number of test samples
    """
    try:
        initialize_metrics_storage()
        data = load_metrics_data()
        
        model_record = {
            "version_id": version_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "training_size": training_size,
            "test_size": test_size
        }
        
        data["models"].append(model_record)
        save_metrics_data(data)
        logger.info("Recorded metrics for model version %s", version_id)
        
    except Exception as e:
        logger.error("Failed to record model metrics: %s", str(e))
        raise MetricsError(f"Failed to record metrics: {str(e)}")

def record_prediction(
    version_id: str,
    description: str,
    predicted_category: str,
    confidence: float,
    actual_category: str = None
) -> None:
    """
    Record individual prediction details.
    
    Args:
        version_id: Model version ID
        description: Transaction description
        predicted_category: Predicted category
        confidence: Prediction confidence score
        actual_category: Actual category if known (e.g., from feedback)
    """
    try:
        initialize_metrics_storage()
        data = load_metrics_data()
        
        prediction_record = {
            "version_id": version_id,
            "timestamp": datetime.utcnow().isoformat(),
            "description": description,
            "predicted_category": predicted_category,
            "confidence": float(confidence),
            "actual_category": actual_category
        }
        
        data["predictions"].append(prediction_record)
        save_metrics_data(data)
        
    except Exception as e:
        logger.error("Failed to record prediction: %s", str(e))
        raise MetricsError(f"Failed to record prediction: {str(e)}")

def get_model_performance_summary(version_id: str = None) -> Dict[str, Any]:
    """
    Get performance summary for a model version or all versions.
    
    Args:
        version_id: Optional model version ID
        
    Returns:
        Dictionary with performance metrics summary
    """
    try:
        data = load_metrics_data()
        
        if version_id:
            models = [m for m in data["models"] if m["version_id"] == version_id]
            predictions = [p for p in data["predictions"] if p["version_id"] == version_id]
        else:
            models = data["models"]
            predictions = data["predictions"]
            
        if not models:
            return {"error": "No metrics found"}
            
        # Calculate average metrics across models
        avg_metrics = {
            "accuracy": np.mean([m["metrics"]["accuracy"] for m in models]),
            "precision": np.mean([m["metrics"]["precision"] for m in models]),
            "recall": np.mean([m["metrics"]["recall"] for m in models]),
            "f1_score": np.mean([m["metrics"]["f1_score"] for m in models])
        }
        
        # Calculate prediction statistics
        pred_stats = {
            "total_predictions": len(predictions),
            "avg_confidence": np.mean([p["confidence"] for p in predictions]) if predictions else 0,
            "correct_predictions": len([p for p in predictions if p["actual_category"] and p["actual_category"] == p["predicted_category"]])
        }
        
        return {
            "model_metrics": avg_metrics,
            "prediction_stats": pred_stats,
            "num_models": len(models),
            "latest_timestamp": max(m["timestamp"] for m in models) if models else None
        }
        
    except Exception as e:
        logger.error("Failed to get performance summary: %s", str(e))
        raise MetricsError(f"Failed to get summary: {str(e)}")

def generate_performance_report(output_dir: Path = METRICS_DIR) -> Path:
    """
    Generate a detailed performance report in HTML format.
    
    Args:
        output_dir: Directory to save the report
        
    Returns:
        Path to the generated report file
    """
    try:
        data = load_metrics_data()
        
        # Convert to pandas DataFrames
        models_df = pd.DataFrame([
            {
                "Version": m["version_id"],
                "Timestamp": m["timestamp"],
                "Accuracy": m["metrics"]["accuracy"],
                "Precision": m["metrics"]["precision"],
                "Recall": m["metrics"]["recall"],
                "F1 Score": m["metrics"]["f1_score"],
                "Training Size": m["training_size"],
                "Test Size": m["test_size"]
            }
            for m in data["models"]
        ])
        
        predictions_df = pd.DataFrame([
            {
                "Version": p["version_id"],
                "Timestamp": p["timestamp"],
                "Description": p["description"],
                "Predicted": p["predicted_category"],
                "Actual": p["actual_category"],
                "Confidence": p["confidence"]
            }
            for p in data["predictions"]
        ])
        
        # Generate HTML report
        report_path = output_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(report_path, 'w') as f:
            f.write("<html><head><title>Model Performance Report</title></head><body>")
            f.write("<h1>Model Performance Report</h1>")
            
            f.write("<h2>Model Metrics Summary</h2>")
            f.write(models_df.describe().to_html())
            
            f.write("<h2>Model Metrics Over Time</h2>")
            f.write(models_df.to_html())
            
            f.write("<h2>Recent Predictions</h2>")
            f.write(predictions_df.tail(100).to_html())
            
            f.write("</body></html>")
            
        logger.info("Generated performance report at %s", report_path)
        return report_path
        
    except Exception as e:
        logger.error("Failed to generate performance report: %s", str(e))
        raise MetricsError(f"Failed to generate report: {str(e)}")