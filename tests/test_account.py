import requests
import pytest
import config
from datetime import datetime
import random

def generate_unique_account_name():
    return f"test_account_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

@pytest.fixture(scope="module") # Create account once for the whole module
def created_account_id():

    unique_name = generate_unique_account_name()
    payload = {
        "name": unique_name,
        "type": "asset",
        "account_role": "sharedAsset",
    }
    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=payload)
    assert response.status_code == 200, f"Setup failed: status code {response.status_code}"
    account_id = response.json()["data"]["id"]
    yield account_id # when the test is done, this will be cleaned up

    # Cleanup: delete the account after tests complete
    requests.delete(f"{config.BASE_URL}/accounts/{account_id}", headers=config.HEADERS)


def test_post_account():
    unique_name = generate_unique_account_name()
    payload = {
        "name": unique_name,
        "type": "asset",
        "account_role": "sharedAsset",
    }
    response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=payload)
    data = response.json().get("data", {}).get("attributes", {})
    assert response.status_code == 200
    assert data.get("name") == unique_name
    assert data.get("type") == "asset"

def test_get_created_account(created_account_id):
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}", headers=config.HEADERS)
    assert response.status_code == 200
    data = response.json().get("data", {}).get("attributes", {})
    assert data.get("name", "").startswith("test_account_")

def test_update_created_account(created_account_id):
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

def test_get_accounts():
    response = requests.get(config.BASE_URL + '/accounts', headers=config.HEADERS)
    assert response.status_code == 200
    accounts = response.json().get("data", [])
    assert isinstance(accounts, list)
    assert len(accounts) > 0

def test_get_accounts_transactions(created_account_id):
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/transactions", headers=config.HEADERS)
    assert response.status_code == 200
    assert "data" in response.json()

def test_get_accounts_attachments(created_account_id):
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/attachments", headers=config.HEADERS)
    assert response.status_code == 200

def test_get_accounts_piggybank(created_account_id):
    response = requests.get(f"{config.BASE_URL}/accounts/{created_account_id}/piggy-banks", headers=config.HEADERS)
    assert response.status_code == 200

def test_get_invalid_account():
    invalid_id = 9999999
    response = requests.get(f"{config.BASE_URL}/accounts/{invalid_id}", headers=config.HEADERS)
    assert response.status_code in (404, 422)
