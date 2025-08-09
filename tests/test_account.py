import requests
import pytest
import config
from datetime import datetime
import random

# Utility: Generate a unique account name
def generate_unique_account_name():
    return f"test_account_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

# 1. Test creating an account
def test_post_account():
    unique_name = generate_unique_account_name()

    payload = {
        "name": unique_name,
        "type": "asset",
        "account_role": "sharedAsset",
    }

    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=payload)
    data = response.json().get("data", {}).get("attributes", {})

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert data.get("name") == unique_name, "Account name does not match"
    assert data.get("type") == "asset", "Account type is not 'asset'"

    # Save account ID for follow-up tests (if using pytest fixtures or globals)
    global created_account_id
    created_account_id = response.json()["data"]["id"]

# 2. Test retrieving the newly created account by ID
def test_get_created_account():
    
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}", headers=config.HEADERS)
    assert response.status_code == 200
    data = response.json().get("data", {}).get("attributes", {})
    assert data.get("name", "").startswith("test_account_")

# 3. Test updating the created account
def test_update_created_account():
    updated_name = generate_unique_account_name()

    payload = {
        "name": updated_name,
        "type": "asset",
        "account_role": "sharedAsset"
    }

    response = requests.put(f"{config.BASE_URL}/accounts/{created_account_id}", headers=config.HEADERS, json=payload)
    assert response.status_code == 200
    updated_data = response.json().get("data", {}).get("attributes", {})
    assert updated_data.get("name") == updated_name

# 4. Test listing all accounts and checking the count is >= 1
def test_get_accounts():
    response = requests.get(config.BASE_URL + '/accounts', headers=config.HEADERS)
    assert response.status_code == 200
    accounts = response.json().get("data", [])
    assert isinstance(accounts, list)
    assert len(accounts) > 0

# 5. Test transactions for account (should exist or be empty)
def test_get_accounts_transactions():
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/transactions", headers=config.HEADERS)
    assert response.status_code == 200
    assert "data" in response.json()

# 6. Test attachments for account
def test_get_accounts_attachments():
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/attachments", headers=config.HEADERS)
    assert response.status_code == 200

# 7. Test piggy banks for account
def test_get_accounts_piggybank():
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/piggy-banks", headers=config.HEADERS)
    assert response.status_code == 200

# 8. Test getting an invalid account (edge case)
def test_get_invalid_account():
    invalid_id = 9999999
    response = requests.get(f"{config.BASE_URL}/accounts/{invalid_id}", headers=config.HEADERS)
    assert response.status_code == 404 or response.status_code == 422
# 9. Test deleting an account
def test_delete_account():
    response = requests.delete(f"{config.BASE_URL}/accounts/{created_account_id}", headers=config.HEADERS)
    assert response.status_code == 204
