#!/usr/bin/env python3
"""
Test script for the corrected Firefly III webhook processing
Tests actual webhook events that Firefly III sends
"""

import requests
import json
import time

# Service URLs
WEBHOOK_URL = "http://localhost:8000"
AI_SERVICE_URL = "http://localhost:8001"

def test_webhook_event(event_name, webhook_data):
    """Test a specific webhook event"""
    print(f"\n🧪 Testing {event_name}...")
    
    try:
        response = requests.post(
            f"{WEBHOOK_URL}/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {event_name} - SUCCESS")
            print(f"   Status: {result.get('result', {}).get('status', 'N/A')}")
            if 'insights' in result.get('result', {}):
                print(f"   Insights: {result['result']['insights']}")
            return True
        else:
            print(f"❌ {event_name} - HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"💥 {event_name} - Connection Error (Is the service running?)")
        return False
    except Exception as e:
        print(f"💥 {event_name} - Error: {str(e)}")
        return False

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Service: {health['service']}")
            print(f"✅ Version: {health['version']}")
            print(f"✅ Supported Events: {health['supported_events']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"💥 Health check error: {str(e)}")
        return False

def main():
    print("🧠💰 Enhanced AI Financial Intelligence - Webhook Test")
    print("=" * 60)
    print("Testing corrected Firefly III webhook event handling")
    print("Real events: Transaction & Budget created/updated/removed, Budget amount changes, After any event")
    print()
    
    # Test health check first
    if not test_health_check():
        print("\n❌ Health check failed. Make sure the webhook service is running:")
        print("   cd webhook_service && python3 -m uvicorn main:app --reload --port 8000")
        return
    
    # Test actual Firefly III webhook events
    test_events = [
        ("Transaction Created", {
            "trigger": "STORE_TRANSACTION",
            "response": "transactions",
            "content": {
                "transactions": [{
                    "transaction_journal_id": "123",
                    "description": "Coffee at Starbucks",
                    "amount": "4.50",
                    "currency_code": "USD",
                    "date": "2024-01-15",
                    "type": "withdrawal"
                }]
            }
        }),
        
        ("Transaction Updated", {
            "trigger": "UPDATE_TRANSACTION",
            "response": "transactions", 
            "content": {
                "transactions": [{
                    "transaction_journal_id": "123",
                    "description": "Coffee at Starbucks (corrected)",
                    "amount": "4.75",
                    "currency_code": "USD"
                }]
            }
        }),
        
        ("Transaction Removed", {
            "trigger": "DESTROY_TRANSACTION",
            "response": "transactions",
            "content": {
                "transaction_id": "123",
                "deleted_at": "2024-01-15T10:30:00Z"
            }
        }),
        
        ("Budget Created", {
            "trigger": "STORE_BUDGET",
            "response": "budgets",
            "content": {
                "budget": {
                    "id": "456", 
                    "name": "Food & Dining",
                    "limit": "500.00",
                    "currency_code": "USD"
                }
            }
        }),
        
        ("Budget Updated/Amount Changed", {
            "trigger": "UPDATE_BUDGET",
            "response": "budgets",
            "content": {
                "budget": {
                    "id": "456",
                    "name": "Food & Dining", 
                    "old_amount": "500.00",
                    "new_amount": "600.00",
                    "currency_code": "USD"
                }
            }
        }),
        
        ("Budget Removed", {
            "trigger": "DESTROY_BUDGET", 
            "response": "budgets",
            "content": {
                "budget": {
                    "id": "456",
                    "name": "Food & Dining"
                }
            }
        }),
        
        ("After Any Event", {
            "trigger": "ANY_EVENT",
            "response": "any",
            "content": {
                "event_type": "financial_activity",
                "summary": "User activity detected",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        })
    ]
    
    print("🚀 Running webhook tests...")
    
    success_count = 0
    for event_name, webhook_data in test_events:
        if test_webhook_event(event_name, webhook_data):
            success_count += 1
        time.sleep(0.5)  # Small delay between tests
    
    print(f"\n📊 Test Results: {success_count}/{len(test_events)} events processed successfully")
    
    if success_count == len(test_events):
        print("🎉 All tests passed! The webhook service is correctly handling real Firefly III events.")
    else:
        print("⚠️ Some tests failed. Check the service logs for details.")
    
    print("\n💡 Next steps:")
    print("   1. Start AI service: cd firefly-ai-categorizer && python3 -m uvicorn app.main:app --reload --port 8001")
    print("   2. Test with real Firefly III instance")
    print("   3. Configure Firefly III webhooks to point to this service")

if __name__ == "__main__":
    main()