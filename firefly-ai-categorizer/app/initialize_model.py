#!/usr/bin/env python3
"""
Initialize AI model with basic training data
"""
import json
import logging
from pathlib import Path
from .ai_model import retrain_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_initial_training_data():
    """Create initial training data with common transaction categories."""
    
    # Basic training data with common transaction patterns
    initial_data = [
        {"desc": "coffee", "cat": "Food & Drink"},
        {"desc": "cafe", "cat": "Food & Drink"},
        {"desc": "restaurant", "cat": "Food & Drink"},
        {"desc": "grocery", "cat": "Groceries"},
        {"desc": "supermarket", "cat": "Groceries"},
        {"desc": "gas station", "cat": "Transportation"},
        {"desc": "fuel", "cat": "Transportation"},
        {"desc": "taxi", "cat": "Transportation"},
        {"desc": "uber", "cat": "Transportation"},
        {"desc": "amazon", "cat": "Shopping"},
        {"desc": "ebay", "cat": "Shopping"},
        {"desc": "shopping", "cat": "Shopping"},
        {"desc": "pharmacy", "cat": "Healthcare"},
        {"desc": "doctor", "cat": "Healthcare"},
        {"desc": "hospital", "cat": "Healthcare"},
        {"desc": "electricity", "cat": "Utilities"},
        {"desc": "water bill", "cat": "Utilities"},
        {"desc": "internet", "cat": "Utilities"},
        {"desc": "phone bill", "cat": "Utilities"},
        {"desc": "rent", "cat": "Housing"},
        {"desc": "mortgage", "cat": "Housing"},
        {"desc": "salary", "cat": "Income"},
        {"desc": "paycheck", "cat": "Income"},
        {"desc": "interest", "cat": "Income"},
        {"desc": "atm", "cat": "Bank Fees"},
        {"desc": "bank fee", "cat": "Bank Fees"},
        {"desc": "netflix", "cat": "Entertainment"},
        {"desc": "spotify", "cat": "Entertainment"},
        {"desc": "movie", "cat": "Entertainment"},
        {"desc": "gym", "cat": "Health & Fitness"},
        {"desc": "fitness", "cat": "Health & Fitness"},
    ]
    
    # Ensure data directory exists
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    data_file = data_dir / "training_feedback.json"
    
    # Save initial training data
    with open(data_file, 'w') as f:
        json.dump(initial_data, f, indent=2)
    
    logger.info(f"Created initial training data with {len(initial_data)} samples")
    return data_file

def main():
    """Initialize the model with basic training data."""
    try:
        logger.info("Initializing AI model with basic training data...")
        
        # Create initial training data
        data_file = create_initial_training_data()
        
        # Train the initial model
        retrain_model()
        
        logger.info("AI model initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize AI model: {str(e)}")
        raise

if __name__ == "__main__":
    main()