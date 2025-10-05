#!/usr/bin/env python3
"""
ChatGPT Integration Diagnostic Tool

This script helps diagnose issues with the ChatGPT/OpenAI integration 
in the Firefly AI Categorizer service.

Usage:
  python3 test_chatgpt.py
  python3 test_chatgpt.py --description "Amazon purchase"
  python3 test_chatgpt.py --endpoint http://localhost:8082
"""

import argparse
import requests
import json
import time
import os
from typing import Dict, Any

def test_environment():
    """Test local environment variables."""
    print("\n🔍 Environment Check")
    print("=" * 50)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        key_preview = f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else "[short_key]"
        print(f"✅ OPENAI_API_KEY: {key_preview} (length: {len(openai_key)})")
        
        if not openai_key.startswith("sk-"):
            print("⚠️  Warning: OpenAI API key should start with 'sk-'")
        if len(openai_key) < 40:
            print("⚠️  Warning: OpenAI API key seems too short")
    else:
        print("❌ OPENAI_API_KEY: Not set")
    
    firefly_token = os.getenv("FIREFLY_TOKEN")
    if firefly_token:
        token_preview = f"{firefly_token[:8]}...{firefly_token[-4:]}" if len(firefly_token) > 12 else "[short_token]"
        print(f"✅ FIREFLY_TOKEN: {token_preview} (length: {len(firefly_token)})")
    else:
        print("❌ FIREFLY_TOKEN: Not set")

def test_service_health(endpoint: str) -> Dict[str, Any]:
    """Test service health endpoint."""
    print(f"\n🏥 Health Check")
    print("=" * 50)
    
    try:
        response = requests.get(f"{endpoint}/health", timeout=10)
        health_data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Service Status: {health_data.get('status', 'unknown')}")
        print(f"Model Status: {health_data.get('model_status', 'unknown')}")
        print(f"Model Type: {health_data.get('model_type', 'unknown')}")
        print(f"Database Status: {health_data.get('database_status', 'unknown')}")
        print(f"Storage Mode: {health_data.get('storage_mode', 'unknown')}")
        
        if health_data.get('model_status') != 'available':
            print("⚠️  Warning: Model not available")
            
        return health_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {str(e)}")
        return {"status": "error", "error": str(e)}

def test_debug_env(endpoint: str) -> Dict[str, Any]:
    """Test debug environment endpoint."""
    print(f"\n🐛 Environment Debug")
    print("=" * 50)
    
    try:
        response = requests.get(f"{endpoint}/debug-env", timeout=10)
        debug_data = response.json()
        
        env_check = debug_data.get("environment_check", {})
        suggestions = debug_data.get("suggestions", {})
        
        print(f"OpenAI Key Set: {env_check.get('openai_api_key_set', False)}")
        print(f"OpenAI Key Length: {env_check.get('openai_key_length', 0)}")
        print(f"Firefly Token Set: {env_check.get('firefly_token_set', False)}")
        print(f"Firefly Token Length: {env_check.get('firefly_token_length', 0)}")
        
        print("\n💡 Suggestions:")
        for key, suggestion in suggestions.items():
            print(f"  {key}: {suggestion}")
            
        return debug_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Debug endpoint failed: {str(e)}")
        return {"status": "error", "error": str(e)}

def test_ai_categorization(endpoint: str, description: str) -> Dict[str, Any]:
    """Test AI categorization with detailed logging."""
    print(f"\n🤖 AI Categorization Test")
    print("=" * 50)
    
    test_payload = {"description": description}
    
    try:
        print(f"Testing description: '{description}'")
        print("Sending request to AI service...")
        
        start_time = time.time()
        response = requests.post(
            f"{endpoint}/test-ai", 
            json=test_payload,
            timeout=30
        )
        duration = time.time() - start_time
        
        print(f"Response time: {duration:.2f}s")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Test Status: {result.get('status', 'unknown')}")
            print(f"Predicted Category: {result.get('predicted_category', 'none')}")
            print(f"Processing Duration: {result.get('duration_seconds', 0):.2f}s")
            print(f"OpenAI Client: {result.get('openai_client_status', 'unknown')}")
            print(f"Message: {result.get('message', 'none')}")
            
            if result.get('status') != 'test_passed':
                print("\n❌ Test failed:")
                print(f"Error: {result.get('error', 'unknown')}")
                
                suggestions = result.get('suggestions', [])
                if suggestions:
                    print("\n💡 Suggestions:")
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"  {i}. {suggestion}")
            
            return result
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
                return error_data
            except:
                print(f"Response text: {response.text}")
                return {"status": "http_error", "code": response.status_code}
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out (30s)")
        return {"status": "timeout"}
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return {"status": "request_error", "error": str(e)}

def test_webhook_simulation(endpoint: str, description: str) -> Dict[str, Any]:
    """Simulate a real webhook call from Firefly III."""
    print(f"\n📡 Webhook Simulation Test")
    print("=" * 50)
    
    # Simulate actual Firefly III webhook payload
    webhook_payload = {
        "content": {
            "transactions": [{
                "transaction_journal_id": "999",
                "description": description
            }]
        }
    }
    
    try:
        print(f"Simulating webhook for: '{description}'")
        print("Sending webhook payload...")
        
        start_time = time.time()
        response = requests.post(
            f"{endpoint}/incoming",
            json=webhook_payload,
            timeout=30
        )
        duration = time.time() - start_time
        
        print(f"Response time: {duration:.2f}s")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Webhook Status: {result.get('status', 'unknown')}")
            print(f"Category: {result.get('category', 'none')}")
            print(f"Confidence: {result.get('confidence', 0)}")
            
            if 'message' in result:
                print(f"Message: {result.get('message')}")
                
            return result
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
                return error_data
            except:
                print(f"Response text: {response.text}")
                return {"status": "http_error", "code": response.status_code}
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook test failed: {str(e)}")
        return {"status": "request_error", "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Test ChatGPT integration in Firefly AI Categorizer")
    parser.add_argument("--endpoint", default="http://localhost:8082", help="AI service endpoint")
    parser.add_argument("--description", default="Coffee from Starbucks", help="Test transaction description")
    parser.add_argument("--skip-env", action="store_true", help="Skip local environment check")
    
    args = parser.parse_args()
    
    print("🤖 ChatGPT Integration Diagnostic Tool")
    print("=" * 60)
    
    # Test local environment
    if not args.skip_env:
        test_environment()
    
    # Test service health
    health_result = test_service_health(args.endpoint)
    
    # Test debug endpoint
    debug_result = test_debug_env(args.endpoint)
    
    # Test AI categorization
    ai_result = test_ai_categorization(args.endpoint, args.description)
    
    # Test webhook simulation
    webhook_result = test_webhook_simulation(args.endpoint, args.description)
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    
    health_ok = health_result.get("model_status") == "available"
    ai_ok = ai_result.get("status") == "test_passed"
    webhook_ok = webhook_result.get("status") in ["AI category assigned", "category_updated"]
    
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"AI Test: {'✅ PASS' if ai_ok else '❌ FAIL'}")
    print(f"Webhook Test: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    if all([health_ok, ai_ok, webhook_ok]):
        print("\n🎉 All tests passed! ChatGPT integration is working.")
    else:
        print("\n⚠️ Some tests failed. Check the details above.")
        print("\n💡 Common fixes:")
        print("1. Verify OPENAI_API_KEY is set and valid")
        print("2. Check OpenAI account has available quota")
        print("3. Ensure network connectivity")
        print("4. Restart the AI service container")

if __name__ == "__main__":
    main()