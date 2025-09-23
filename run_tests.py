#!/usr/bin/env python3
"""
Firefly III AI Integration Test Runner

This script provides convenient ways to run different test suites and check service status.
"""

import sys
import subprocess
import requests
import time
import argparse
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tests.test_config import get_test_service_status, FIREFLY_URL, AI_SERVICE_URL, WEBHOOK_SERVICE_URL
except ImportError:
    # Fallback URLs if test_config not available
    FIREFLY_URL = "http://localhost:8080"
    AI_SERVICE_URL = "http://localhost:8082" 
    WEBHOOK_SERVICE_URL = "http://localhost:8001"

def check_services():
    """Check status of all services required for testing."""
    print("🔍 Checking service status...")
    
    services = {
        "Firefly III": f"{FIREFLY_URL}/api/v1/about",
        "AI Service": f"{AI_SERVICE_URL}/health", 
        "Webhook Service": f"{WEBHOOK_SERVICE_URL}/health"
    }
    
    status = {}
    
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                status[name] = "✅ Running"
            else:
                status[name] = f"❌ Error (HTTP {response.status_code})"
        except requests.RequestException as e:
            status[name] = f"❌ Not accessible ({str(e)[:50]}...)"
    
    print("\nService Status:")
    for name, state in status.items():
        print(f"  {name}: {state}")
    
    return all("✅" in state for state in status.values())

def run_unit_tests():
    """Run unit tests with mocks."""
    print("🧪 Running unit tests...")
    cmd = ["python", "-m", "pytest", "-m", "unit", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_api_tests():
    """Run Firefly API tests."""
    print("🔌 Running Firefly API tests...")
    cmd = ["python", "-m", "pytest", "-m", "api or not (requires_ai_service or requires_webhook_service)", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_integration_tests():
    """Run full integration tests."""
    print("🔗 Running integration tests...")
    if not check_services():
        print("❌ Some services are not running. Please start all services first.")
        print("Run: docker compose up -d")
        return 1
    
    cmd = ["python", "-m", "pytest", "-m", "integration", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_business_workflow_tests():
    """Run business workflow tests."""
    print("💼 Running business workflow tests...")
    cmd = ["python", "-m", "pytest", "-m", "business_workflow", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_ai_tests():
    """Run AI service specific tests."""
    print("🤖 Running AI service tests...")
    cmd = ["python", "-m", "pytest", "tests/test_ai_service.py", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_webhook_tests():
    """Run webhook service tests."""
    print("🔗 Running webhook tests...")
    cmd = ["python", "-m", "pytest", "tests/test_webhook_service.py", "-v"]
    return subprocess.run(cmd, cwd=project_root).returncode

def run_all_tests():
    """Run all tests in sequence."""
    print("🚀 Running all tests...")
    
    # Check services first
    services_ok = check_services()
    
    test_suites = [
        ("Unit Tests", run_unit_tests),
        ("API Tests", run_api_tests),
        ("AI Tests", run_ai_tests),
        ("Webhook Tests", run_webhook_tests),
    ]
    
    if services_ok:
        test_suites.append(("Integration Tests", run_integration_tests))
        test_suites.append(("Business Workflow Tests", run_business_workflow_tests))
    else:
        print("⚠️  Skipping integration tests - services not running")
    
    results = {}
    for name, test_func in test_suites:
        print(f"\n{'='*50}")
        print(f"Running {name}")
        print(f"{'='*50}")
        
        result = test_func()
        results[name] = "✅ PASSED" if result == 0 else "❌ FAILED"
    
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    for name, result in results.items():
        print(f"{name}: {result}")
    
    failed_tests = [name for name, result in results.items() if "❌" in result]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test suite(s) failed")
        return 1
    else:
        print(f"\n✅ All {len(results)} test suites passed!")
        return 0

def start_services():
    """Start all services with docker compose."""
    print("🚀 Starting services...")
    cmd = ["docker", "compose", "up", "-d"]
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("⏳ Waiting for services to start...")
        time.sleep(10)  # Give services time to start
        check_services()
    
    return result.returncode

def stop_services():
    """Stop all services."""
    print("🛑 Stopping services...")
    cmd = ["docker", "compose", "down"]
    return subprocess.run(cmd, cwd=project_root).returncode

def main():
    parser = argparse.ArgumentParser(description="Firefly III AI Integration Test Runner")
    parser.add_argument("command", choices=[
        "check", "unit", "api", "ai", "webhook", "integration", 
        "business", "all", "start", "stop"
    ], help="Test command to run")
    
    args = parser.parse_args()
    
    commands = {
        "check": check_services,
        "unit": run_unit_tests,
        "api": run_api_tests,
        "ai": run_ai_tests,
        "webhook": run_webhook_tests,
        "integration": run_integration_tests,
        "business": run_business_workflow_tests,
        "all": run_all_tests,
        "start": start_services,
        "stop": stop_services
    }
    
    if args.command == "check":
        success = commands[args.command]()
        return 0 if success else 1
    else:
        return commands[args.command]()

if __name__ == "__main__":
    sys.exit(main())