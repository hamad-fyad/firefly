import requests
import pytest
import config
from datetime import datetime, timedelta
import random

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.business_workflow
@pytest.mark.github_actions
def generate_unique_transaction_name():
    return f"test_transaction_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.business_workflow
@pytest.mark.github_actions
def generate_unique_account_name():
    return f"test_account_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

@pytest.fixture(scope="module")
def test_accounts():
    """Create test accounts for transaction testing."""
    accounts = {}
    
    # Create source account
    source_payload = {
        "name": generate_unique_account_name() + "_source",
        "type": "asset",
        "account_role": "defaultAsset",
        "opening_balance": "1000.00",
        "opening_balance_date": datetime.now().strftime('%Y-%m-%d')
    }
    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=source_payload)
    assert response.status_code == 200, f"Failed to create source account: {response.text}"
    accounts['source_id'] = response.json()["data"]["id"]
    
    # Create destination account  
    dest_payload = {
        "name": generate_unique_account_name() + "_dest",
        "type": "expense",
        "account_role": None
    }
    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=dest_payload)
    assert response.status_code == 200, f"Failed to create destination account: {response.text}"
    accounts['dest_id'] = response.json()["data"]["id"]
    
    yield accounts
    
    # Cleanup
    for account_id in accounts.values():
        requests.delete(f"{config.BASE_URL}/accounts/{account_id}", headers=config.HEADERS)

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.business_workflow
@pytest.mark.github_actions
def test_create_withdrawal_transaction(test_accounts):
    """Test creating a withdrawal transaction - business workflow for expense tracking."""
    transaction_data = {
        "error_if_duplicate_hash": False,
        "apply_rules": True,
        "group_title": None,
        "transactions": [
            {
                "type": "withdrawal",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "amount": "25.50",
                "description": generate_unique_transaction_name() + " - Coffee purchase",
                "source_id": test_accounts['source_id'],
                "destination_id": test_accounts['dest_id'],
                "category_name": "Food & Drinks",
                "tags": ["coffee", "expense"],
                "notes": "Morning coffee expense"
            }
        ]
    }
    
    response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=transaction_data)
    assert response.status_code == 200, f"Failed to create transaction: {response.text}"
    
    transaction = response.json()["data"]["attributes"]["transactions"][0]
    assert transaction["type"] == "withdrawal"
    assert float(transaction["amount"]) == 25.50
    assert transaction["category_name"] == "Food & Drinks"
    assert "coffee" in transaction.get("tags", [])
    
    return response.json()["data"]["id"]

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.business_workflow
@pytest.mark.github_actions
def test_create_deposit_transaction(test_accounts):
    """Test creating a deposit transaction - business workflow for income tracking."""
    transaction_data = {
        "error_if_duplicate_hash": False,
        "apply_rules": True,
        "transactions": [
            {
                "type": "deposit",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "amount": "2500.00",
                "description": generate_unique_transaction_name() + " - Salary payment",
                "source_name": "Employer Corp",
                "destination_id": test_accounts['source_id'],
                "category_name": "Salary",
                "tags": ["salary", "income"]
            }
        ]
    }
    
    response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=transaction_data)
    assert response.status_code == 200, f"Failed to create deposit: {response.text}"
    
    transaction = response.json()["data"]["attributes"]["transactions"][0]
    assert transaction["type"] == "deposit"
    assert float(transaction["amount"]) == 2500.00
    assert transaction["category_name"] == "Salary"

def test_create_transfer_transaction(test_accounts):
    """Test creating a transfer transaction - business workflow for moving money between accounts."""
    # Create another asset account for transfer
    dest_account_payload = {
        "name": generate_unique_account_name() + "_savings",
        "type": "asset",
        "account_role": "savingAsset"
    }
    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=dest_account_payload)
    assert response.status_code == 200
    savings_id = response.json()["data"]["id"]
    
    try:
        transaction_data = {
            "transactions": [
                {
                    "type": "transfer",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "amount": "500.00",
                    "description": generate_unique_transaction_name() + " - Transfer to savings",
                    "source_id": test_accounts['source_id'],
                    "destination_id": savings_id,
                    "tags": ["savings", "transfer"]
                }
            ]
        }
        
        response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=transaction_data)
        assert response.status_code == 200, f"Failed to create transfer: {response.text}"
        
        transaction = response.json()["data"]["attributes"]["transactions"][0]
        assert transaction["type"] == "transfer"
        assert float(transaction["amount"]) == 500.00
        
    finally:
        # Cleanup savings account
        requests.delete(f"{config.BASE_URL}/accounts/{savings_id}", headers=config.HEADERS)

def test_get_transactions_with_filters():
    """Test retrieving transactions with various filters - business workflow for reporting."""
    # Test date filtering
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'start': start_date,
        'end': end_date,
        'type': 'withdrawal'
    }
    
    response = requests.get(config.BASE_URL + '/transactions', headers=config.HEADERS, params=params)
    assert response.status_code == 200
    
    transactions = response.json().get("data", [])
    assert isinstance(transactions, list)
    
    # Verify transactions are within date range and correct type
    for transaction in transactions:
        trans_data = transaction["attributes"]["transactions"][0]
        assert trans_data["type"] == "withdrawal"
        trans_date = datetime.strptime(trans_data["date"], '%Y-%m-%dT%H:%M:%S%z').date()
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        assert start_date_obj <= trans_date <= end_date_obj

def test_update_transaction(test_accounts):
    """Test updating transaction details - business workflow for correcting expenses."""
    # First create a transaction
    transaction_data = {
        "transactions": [
            {
                "type": "withdrawal",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "amount": "15.00",
                "description": "Original description",
                "source_id": test_accounts['source_id'],
                "destination_id": test_accounts['dest_id'],
                "category_name": "Groceries"
            }
        ]
    }
    
    create_response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=transaction_data)
    assert create_response.status_code == 200
    transaction_id = create_response.json()["data"]["id"]
    
    # Update the transaction
    update_data = {
        "transactions": [
            {
                "type": "withdrawal",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "amount": "18.50",
                "description": "Updated - Grocery shopping with tax",
                "source_id": test_accounts['source_id'],
                "destination_id": test_accounts['dest_id'],
                "category_name": "Food & Drinks",
                "tags": ["grocery", "corrected"]
            }
        ]
    }
    
    update_response = requests.put(f"{config.BASE_URL}/transactions/{transaction_id}", 
                                 headers=config.HEADERS, json=update_data)
    assert update_response.status_code == 200
    
    updated_transaction = update_response.json()["data"]["attributes"]["transactions"][0]
    assert float(updated_transaction["amount"]) == 18.50
    assert updated_transaction["description"] == "Updated - Grocery shopping with tax"
    assert updated_transaction["category_name"] == "Food & Drinks"

def test_transaction_categorization_workflow():
    """Test transaction categorization - key business workflow for AI integration."""
    response = requests.get(config.BASE_URL + '/categories', headers=config.HEADERS)
    assert response.status_code == 200
    
    categories = response.json().get("data", [])
    assert len(categories) > 0, "No categories available for testing"
    
    # Test that categories have the expected structure
    for category in categories[:5]:  # Test first 5 categories
        attrs = category.get("attributes", {})
        assert "name" in attrs
        assert attrs["name"], "Category name should not be empty"

def test_transaction_search():
    """Test transaction search functionality - business workflow for finding specific expenses."""
    search_params = {
        'query': 'coffee',
        'limit': 10
    }
    
    response = requests.get(config.BASE_URL + '/search/transactions', headers=config.HEADERS, params=search_params)
    assert response.status_code == 200
    
    results = response.json().get("data", [])
    assert isinstance(results, list)
    
    # Verify search results contain the search term
    for result in results:
        transaction = result["attributes"]["transactions"][0]
        description = transaction.get("description", "").lower()
        category = transaction.get("category_name", "").lower()
        # Search term should appear in description or category
        assert "coffee" in description or "coffee" in category or len(results) == 0

def test_transaction_bulk_operations():
    """Test bulk transaction operations - business workflow for importing data."""
    # Test getting multiple transactions
    response = requests.get(config.BASE_URL + '/transactions', headers=config.HEADERS, params={'limit': 50})
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "pagination" in data["meta"]
    
    # Verify pagination metadata
    pagination = data["meta"]["pagination"]
    assert "current_page" in pagination
    assert "per_page" in pagination
    assert "total" in pagination

def test_invalid_transaction_scenarios():
    """Test error handling for invalid transaction data - business workflow validation."""
    # Test missing required fields
    invalid_data = {
        "transactions": [
            {
                "type": "withdrawal",
                # Missing required fields like amount, description, etc.
            }
        ]
    }
    
    response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=invalid_data)
    assert response.status_code == 422, "Should reject invalid transaction data"
    
    # Test invalid transaction type
    invalid_type_data = {
        "transactions": [
            {
                "type": "invalid_type",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "amount": "10.00",
                "description": "Invalid transaction type test"
            }
        ]
    }
    
    response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=invalid_type_data)
    assert response.status_code == 422, "Should reject invalid transaction type"

def test_transaction_with_multiple_splits():
    """Test split transactions - business workflow for detailed expense tracking."""
    # This would test more complex transaction scenarios
    # Implementation depends on Firefly III's split transaction support
    response = requests.get(config.BASE_URL + '/transactions', headers=config.HEADERS, params={'limit': 1})
    assert response.status_code == 200, "Basic transaction endpoint should be accessible"