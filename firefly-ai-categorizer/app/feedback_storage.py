import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import tempfile
import shutil
import os

# Set up logging
logger = logging.getLogger(__name__)

DATA_FILE = Path("/app/data/training_feedback.json")
DATA_DIR = DATA_FILE.parent

class FeedbackError(Exception):
    """Custom exception for feedback storage related errors."""
    pass

def validate_feedback(description: str, category: str) -> None:
    """
    Validate feedback data before saving.
    
    Args:
        description: Transaction description text
        category: Category name
        
    Raises:
        ValueError: If validation fails
    """
    if not description or not isinstance(description, str):
        raise ValueError("Description must be a non-empty string")
    if not category or not isinstance(category, str):
        raise ValueError("Category must be a non-empty string")

def load_feedback() -> List[Dict]:
    """
    Load existing feedback data from file.
    
    Returns:
        List of feedback entries
        
    Raises:
        FeedbackError: If loading fails
    """
    try:
        if not DATA_FILE.exists():
            logger.info("No existing feedback file, starting with empty list")
            return []
            
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            raise ValueError("Invalid feedback data format")
            
        return data
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse feedback file: %s", str(e))
        raise FeedbackError("Invalid feedback file format")
    except Exception as e:
        logger.error("Failed to load feedback: %s", str(e))
        raise FeedbackError(f"Failed to load feedback: {str(e)}")

def save_feedback(description: str, category: str) -> None:
    """
    Save new feedback entry safely using atomic write.
    
    Args:
        description: Transaction description text
        category: Category name
        
    Raises:
        FeedbackError: If saving fails
    """
    try:
        # Validate input
        validate_feedback(description, category)
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing feedback
        feedback = load_feedback()
        
        # Add new entry with timestamp
        feedback.append({
            "desc": description,
            "cat": category,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', dir=str(DATA_DIR), delete=False) as tf:
            json.dump(feedback, tf, indent=2)
            temp_name = tf.name
            
        # Atomic replace
        shutil.move(temp_name, str(DATA_FILE))
        
        logger.info("Successfully saved new feedback entry")
        
    except (ValueError, FeedbackError) as e:
        logger.error("Error saving feedback: %s", str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error saving feedback: %s", str(e))
        if 'temp_name' in locals():
            try:
                os.unlink(temp_name)
            except:
                pass
        raise FeedbackError(f"Failed to save feedback: {str(e)}")
