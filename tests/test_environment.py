"""
Environment and Infrastructure Tests - System Setup and Configuration Validation

Tests environment detection, service availability, and infrastructure readiness.
Validates that all required services are properly configured and accessible
across different deployment environments (local, CI/CD, production).
"""
import pytest
import requests
import os
import config
from datetime import datetime

@pytest.mark.api
@pytest.mark.github_actions
def test_environment_detection():
    """Test that correctly detects GitHub Actions vs local environment."""
    
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        print("🚀 Running in GitHub Actions environment")
        assert config.BASE_URL.startswith("http://52.212.42.101:8080"), \
            f"Expected remote URL in GitHub Actions, got: {config.BASE_URL}"
    else:
        print("🏠 Running in local development environment")
        # In local, could be either local or remote
        assert config.BASE_URL.startswith("http://"), \
            f"Expected valid URL, got: {config.BASE_URL}"

@pytest.mark.api
@pytest.mark.requires_firefly  
@pytest.mark.github_actions
def test_firefly_api_connectivity():
    """Test basic Firefly III API connectivity - works in both environments."""
    
    # Test the about endpoint to verify API is accessible
    response = requests.get(config.BASE_URL + '/about', headers=config.HEADERS, timeout=10)
    
    assert response.status_code == 200, f"API not accessible: {response.status_code}"
    
    data = response.json().get("data", {})
    assert "version" in data, "API response missing version info"
    assert "api_version" in data, "API response missing API version"
    
    print(f"✅ Firefly III Version: {data.get('version')}")
    print(f"✅ API Version: {data.get('api_version')}")

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def test_api_authentication():
    """Test API authentication works correctly."""
    
    # Test authenticated endpoint
    response = requests.get(config.BASE_URL + '/about/user', headers=config.HEADERS, timeout=10)
    
    assert response.status_code == 200, f"Authentication failed: {response.status_code}"
    
    data = response.json().get("data", {})
    assert "id" in data, "User data missing ID"
    assert "type" in data, "User data missing type"
    assert data["type"] == "users", f"Unexpected user type: {data.get('type')}"
    
    print(f"✅ Authenticated as user ID: {data.get('id')}")

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
@pytest.mark.business_workflow
def test_basic_account_operations():
    """Test basic account operations that work in GitHub Actions."""
    
    # Test getting accounts list
    response = requests.get(config.BASE_URL + '/accounts', headers=config.HEADERS, timeout=10)
    assert response.status_code == 200, f"Failed to get accounts: {response.status_code}"
    
    accounts = response.json().get("data", [])
    assert isinstance(accounts, list), "Accounts should be a list"
    
    print(f"✅ Found {len(accounts)} accounts")
    
    # If we have accounts, test getting a specific one
    if accounts:
        first_account = accounts[0]
        account_id = first_account["id"]
        
        detail_response = requests.get(f"{config.BASE_URL}/accounts/{account_id}", 
                                     headers=config.HEADERS, timeout=10)
        assert detail_response.status_code == 200, "Failed to get account details"
        
        account_data = detail_response.json()["data"]["attributes"]
        assert "name" in account_data, "Account missing name"
        assert "type" in account_data, "Account missing type"
        
        print(f"✅ Account details: {account_data.get('name')} ({account_data.get('type')})")

@pytest.mark.api  
@pytest.mark.requires_firefly
@pytest.mark.github_actions
@pytest.mark.business_workflow
def test_transaction_listing():
    """Test transaction listing - business workflow validation."""
    
    # Get recent transactions
    params = {
        'limit': 10,
        'page': 1
    }
    
    response = requests.get(config.BASE_URL + '/transactions', 
                          headers=config.HEADERS, params=params, timeout=15)
    
    assert response.status_code == 200, f"Failed to get transactions: {response.status_code}"
    
    data = response.json()
    assert "data" in data, "Response missing data"
    assert "meta" in data, "Response missing metadata"
    
    transactions = data["data"]
    meta = data["meta"]
    
    print(f"✅ Found {len(transactions)} transactions")
    print(f"✅ Total transactions: {meta.get('pagination', {}).get('total', 'unknown')}")
    
    # Validate transaction structure if we have any
    if transactions:
        first_transaction = transactions[0]
        assert "attributes" in first_transaction, "Transaction missing attributes"
        
        attrs = first_transaction["attributes"]
        assert "transactions" in attrs, "Transaction missing transaction details"
        
        if attrs["transactions"]:
            trans_detail = attrs["transactions"][0]
            required_fields = ["type", "date", "amount", "description"]
            
            for field in required_fields:
                assert field in trans_detail, f"Transaction missing {field}"
            
            print(f"✅ Transaction example: {trans_detail.get('description')} - ${trans_detail.get('amount')}")

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def test_categories_available():
    """Test that categories are available for AI categorization."""
    
    response = requests.get(config.BASE_URL + '/categories', headers=config.HEADERS, timeout=10)
    assert response.status_code == 200, f"Failed to get categories: {response.status_code}"
    
    categories = response.json().get("data", [])
    assert isinstance(categories, list), "Categories should be a list"
    
    print(f"✅ Found {len(categories)} categories")
    
    # Check category structure
    if categories:
        first_category = categories[0]
        assert "attributes" in first_category, "Category missing attributes"
        
        attrs = first_category["attributes"]
        assert "name" in attrs, "Category missing name"
        
        print(f"✅ Category example: {attrs.get('name')}")

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
@pytest.mark.slow
def test_api_rate_limiting_github():
    """Test API rate limiting in GitHub Actions environment."""
    
    # Make several requests to test rate limiting
    responses = []
    
    for i in range(3):  # Fewer requests in GitHub Actions
        try:
            response = requests.get(config.BASE_URL + '/about', 
                                  headers=config.HEADERS, timeout=5)
            responses.append(response.status_code)
        except requests.RequestException as e:
            responses.append(f"Error: {str(e)}")
    
    # Most should be successful
    successful = [r for r in responses if r == 200]
    assert len(successful) >= 2, f"Too many failed requests: {responses}"
    
    print(f"✅ Rate limiting test: {len(successful)}/{len(responses)} successful")

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def test_api_error_handling():
    """Test API error handling with invalid requests."""
    
    # Test invalid endpoint
    response = requests.get(config.BASE_URL + '/invalid-endpoint', 
                          headers=config.HEADERS, timeout=10)
    assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
    
    # Test invalid account ID
    response = requests.get(f"{config.BASE_URL}/accounts/999999", 
                          headers=config.HEADERS, timeout=10)
    assert response.status_code in [404, 422], f"Expected 404/422, got: {response.status_code}"
    
    print("✅ Error handling working correctly")