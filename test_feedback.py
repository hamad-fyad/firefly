#!/usr/bin/env python3
"""
Test script to simulate transaction category feedback
"""
import requests
import json

def test_feedback():
    # Simulate the feedback format that should be sent to AI service
    feedback_data = {
        "transactions": [
            {
                "description": "bought coffee machine at amazon",
                "category_name": "Food & Drink"
            }
        ]
    }
    
    try:
        # Try to call the AI service feedback endpoint via Docker
        # We'll use the webhook service as a proxy since it can reach the AI service
        print("Testing feedback mechanism...")
        print(f"Feedback data: {feedback_data}")
        
        # Since we can't directly reach the AI service from outside Docker,
        # let's just document what would happen:
        print("\n=== FEEDBACK SIMULATION ===")
        print("1. User manually changed category:")
        print("   Transaction: 'bought coffee machine at amazon'")
        print("   From: Shopping → To: Food & Drink")
        print("\n2. Expected AI feedback process:")
        print("   - AI service /feedback endpoint would receive:")
        print(f"     {json.dumps(feedback_data, indent=2)}")
        print("   - save_feedback() would store: description='bought coffee machine at amazon', category='Food & Drink'")
        print("   - retrain_model() would update the model with this new training data")
        print("\n3. Future predictions for similar transactions should improve")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_feedback()