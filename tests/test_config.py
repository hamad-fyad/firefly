# Test Configuration for Firefly III AI Integration
# This file extends the existing config.py with additional test settings

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "firefly-ai-categorizer" / "app"))

# Environment detection
IS_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'
IS_LOCAL_DEV = not IS_GITHUB_ACTIONS

# Test service URLs - adapt based on environment
if IS_GITHUB_ACTIONS:
    # GitHub Actions uses remote Firefly instance
    FIREFLY_URL = os.getenv('FIREFLY_BASE_URL', 'http://52.212.42.101:8080/api/v1').replace('/api/v1', '')
    AI_SERVICE_URL = None  # AI service not available in GitHub Actions
    WEBHOOK_SERVICE_URL = None  # Webhook service not available in GitHub Actions
    TEST_DATABASE_URL = None  # Database not available in GitHub Actions
else:
    # Local development
    AI_SERVICE_URL = "http://localhost:8082"
    WEBHOOK_SERVICE_URL = "http://localhost:8001"
    FIREFLY_URL = "http://localhost:8080"
    TEST_DATABASE_URL = "postgresql://ai_user:ai_password@localhost:5433/ai_metrics"

# Test timeouts
DEFAULT_TIMEOUT = 10
SERVICE_STARTUP_TIMEOUT = 30

# Test data settings
MAX_TEST_ACCOUNTS = 10
MAX_TEST_TRANSACTIONS = 50
CLEANUP_TEST_DATA = True

# Mock settings for unit tests
USE_MOCKS_FOR_EXTERNAL_SERVICES = True
MOCK_OPENAI_RESPONSES = True
MOCK_FIREFLY_RESPONSES = False  # We want to test real Firefly API

# AI Model test settings (only for local development)
AI_CONFIDENCE_THRESHOLD = 0.75
AI_FALLBACK_CATEGORY = "Uncategorized"

# Webhook test settings (only for local development)
WEBHOOK_TIMEOUT = 15
WEBHOOK_RETRY_COUNT = 3

# Test categories for validation
VALID_CATEGORIES = [
    "Food & Drinks",
    "Transportation", 
    "Groceries",
    "Entertainment",
    "Shopping",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Travel",
    "Business",
    "Income",
    "Savings",
    "Investment"
]

# Test transaction types
CATEGORIZABLE_TRANSACTION_TYPES = ["withdrawal", "deposit"]
NON_CATEGORIZABLE_TRANSACTION_TYPES = ["transfer", "opening-balance", "reconciliation"]

def get_test_service_status():
    """Check which services are available for testing."""
    import requests
    
    services = {
        "firefly": False,
        "ai_service": False, 
        "webhook_service": False,
        "ai_database": False
    }
    
    # Always test Firefly (available in both local and GitHub Actions)
    try:
        firefly_url = FIREFLY_URL if FIREFLY_URL else "http://52.212.42.101:8080"
        response = requests.get(f"{firefly_url}/api/v1/about", timeout=5)
        services["firefly"] = response.status_code == 200
    except:
        pass
    
    # AI service and webhook only available in local development
    if not IS_GITHUB_ACTIONS:
        try:
            if AI_SERVICE_URL:
                response = requests.get(f"{AI_SERVICE_URL}/health", timeout=5)
                services["ai_service"] = response.status_code == 200
        except:
            pass
        
        try:
            if WEBHOOK_SERVICE_URL:
                response = requests.get(f"{WEBHOOK_SERVICE_URL}/health", timeout=5)
                services["webhook_service"] = response.status_code == 200
        except:
            pass
        
        # Test database connection (only in local development)
        if TEST_DATABASE_URL:
            try:
                import psycopg2
                conn = psycopg2.connect(TEST_DATABASE_URL)
                conn.close()
                services["ai_database"] = True
            except:
                pass
    
    return services

# Pytest markers for conditional tests
pytest_markers = {
    "requires_firefly": "requires Firefly III service running",
    "requires_ai_service": "requires AI service running", 
    "requires_webhook_service": "requires webhook service running",
    "requires_database": "requires AI database running",
    "integration": "integration test requiring multiple services",
    "unit": "unit test with mocks",
    "slow": "slow test that may take time",
    "business_workflow": "test that validates business workflows"
}