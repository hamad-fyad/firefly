#!/usr/bin/env python3
"""
Test script to verify AI improvements:
1. GPT-4 model upgrade
2. Dynamic category creation
3. No more defaulting to "Other"
"""

import requests
import json
import time

# Test endpoint
BASE_URL = "http://52.212.42.101:8082"

def test_categorization(description):
    """Test a single transaction categorization"""
    print(f"\n🧪 Testing: '{description}'")
    
    try:
        # Test the categorization endpoint
        response = requests.post(
            f"{BASE_URL}/test-categorize",
            json={"description": description},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            category = result.get("predicted_category", "Unknown")
            confidence = result.get("confidence", 0.0)
            
            print(f"✅ Category: {category}")
            print(f"📊 Confidence: {confidence:.2f}")
            
            if category == "Other":
                print("⚠️  Still using 'Other' - need to redeploy with new code")
            else:
                print("🎉 Success - no 'Other' category!")
                
            return category, confidence
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None, None

def main():
    """Test various transaction types"""
    print("🚀 Testing AI Improvements")
    print("=" * 50)
    
    # Test cases that should get specific categories (not "Other")
    test_cases = [
        "Pet grooming service",  # Should create "Pet Care" category
        "Piano lessons",  # Should create "Education" or "Music Lessons"
        "Car insurance premium",  # Should be "Insurance"
        "Veterinary clinic visit",  # Should create "Pet Care" or "Veterinary"
        "Lawn care service",  # Should create "Home Services" or "Landscaping"
        "Wedding photography",  # Should create "Professional Services" or "Photography"
        "Dry cleaning",  # Should create "Personal Services"
        "Phone repair",  # Should create "Repairs" or "Electronics"
    ]
    
    results = []
    for description in test_cases:
        category, confidence = test_categorization(description)
        if category:
            results.append((description, category, confidence))
        time.sleep(1)  # Be nice to the API
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY OF RESULTS:")
    print("=" * 50)
    
    other_count = 0
    for desc, cat, conf in results:
        status = "❌ Other" if cat == "Other" else "✅ Specific"
        print(f"{status}: {desc[:30]:<30} → {cat} ({conf:.2f})")
        if cat == "Other":
            other_count += 1
    
    print(f"\n📊 Results: {len(results) - other_count}/{len(results)} got specific categories")
    
    if other_count == 0:
        print("🎉 SUCCESS: No 'Other' categories - AI is creating specific categories!")
    else:
        print(f"⚠️  {other_count} transactions still got 'Other' - may need to redeploy")

if __name__ == "__main__":
    main()