import requests
import pytest
import config
from datetime import datetime, timedelta
import random

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def generate_unique_name(prefix="test"):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def test_firefly_about_endpoint():
    """Test Firefly III about endpoint - system information workflow."""
    response = requests.get(config.BASE_URL + '/about', headers=config.HEADERS)
    assert response.status_code == 200
    
    data = response.json().get("data", {})
    assert "version" in data
    assert "api_version" in data
    assert "php_version" in data
    
    # Verify version format
    version = data.get("version", "")
    assert len(version) > 0
    assert "." in version  # Should be semantic version like 6.3.2

def test_firefly_user_info():
    """Test current user information - user management workflow."""
    response = requests.get(config.BASE_URL + '/about/user', headers=config.HEADERS)
    assert response.status_code == 200
    
    data = response.json().get("data", {})
    assert "id" in data
    assert "type" in data
    assert data["type"] == "users"
    
    attributes = data.get("attributes", {})
    assert "email" in attributes
    assert "created_at" in attributes

def test_categories_crud_workflow():
    """Test complete category CRUD operations - expense categorization workflow."""
    # Create category
    category_name = generate_unique_name("category")
    create_payload = {
        "name": category_name,
        "notes": "Test category for automation"
    }
    
    create_response = requests.post(config.BASE_URL + '/categories', headers=config.HEADERS, json=create_payload)
    assert create_response.status_code == 200
    
    category_data = create_response.json()["data"]
    category_id = category_data["id"]
    
    try:
        # Read category
        read_response = requests.get(f"{config.BASE_URL}/categories/{category_id}", headers=config.HEADERS)
        assert read_response.status_code == 200
        
        read_data = read_response.json()["data"]["attributes"]
        assert read_data["name"] == category_name
        
        # Update category
        updated_name = generate_unique_name("updated_category")
        update_payload = {
            "name": updated_name,
            "notes": "Updated test category"
        }
        
        update_response = requests.put(f"{config.BASE_URL}/categories/{category_id}", 
                                     headers=config.HEADERS, json=update_payload)
        assert update_response.status_code == 200
        
        updated_data = update_response.json()["data"]["attributes"]
        assert updated_data["name"] == updated_name
        
        # List categories
        list_response = requests.get(config.BASE_URL + '/categories', headers=config.HEADERS)
        assert list_response.status_code == 200
        
        categories = list_response.json()["data"]
        category_names = [cat["attributes"]["name"] for cat in categories]
        assert updated_name in category_names
        
    finally:
        # Delete category
        delete_response = requests.delete(f"{config.BASE_URL}/categories/{category_id}", headers=config.HEADERS)
        assert delete_response.status_code == 204

def test_budgets_workflow():
    """Test budget management - financial planning workflow."""
    # Create budget
    budget_name = generate_unique_name("budget")
    budget_payload = {
        "name": budget_name,
        "auto_budget_type": "reset",
        "auto_budget_currency_id": "1",
        "auto_budget_amount": "500.00",
        "auto_budget_period": "monthly"
    }
    
    create_response = requests.post(config.BASE_URL + '/budgets', headers=config.HEADERS, json=budget_payload)
    assert create_response.status_code == 200
    
    budget_data = create_response.json()["data"]
    budget_id = budget_data["id"]
    
    try:
        # Verify budget creation
        assert budget_data["attributes"]["name"] == budget_name
        assert budget_data["attributes"]["auto_budget_type"] == "reset"
        
        # Get budget details
        detail_response = requests.get(f"{config.BASE_URL}/budgets/{budget_id}", headers=config.HEADERS)
        assert detail_response.status_code == 200
        
        # Test budget limits
        current_date = datetime.now()
        start_date = current_date.replace(day=1).strftime('%Y-%m-%d')
        end_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
        
        limit_payload = {
            "currency_id": "1",
            "budget_id": budget_id,
            "start": start_date,
            "end": end_date,
            "amount": "400.00"
        }
        
        limit_response = requests.post(config.BASE_URL + '/budget-limits', headers=config.HEADERS, json=limit_payload)
        # Budget limits may not be available in all Firefly versions
        if limit_response.status_code == 200:
            limit_data = limit_response.json()["data"]
            assert limit_data["attributes"]["amount"] == "400.00"
        
    finally:
        # Clean up budget
        requests.delete(f"{config.BASE_URL}/budgets/{budget_id}", headers=config.HEADERS)

def test_bills_recurring_transactions():
    """Test bills and recurring transactions - subscription management workflow."""
    # Create bill
    bill_name = generate_unique_name("bill")
    bill_payload = {
        "currency_id": "1",
        "name": bill_name,
        "amount_min": "50.00",
        "amount_max": "60.00",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "end_date": (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
        "extension_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "repeat_freq": "monthly",
        "skip": 0,
        "active": True,
        "notes": "Test recurring bill"
    }
    
    create_response = requests.post(config.BASE_URL + '/bills', headers=config.HEADERS, json=bill_payload)
    assert create_response.status_code == 200
    
    bill_data = create_response.json()["data"]
    bill_id = bill_data["id"]
    
    try:
        # Verify bill creation
        assert bill_data["attributes"]["name"] == bill_name
        assert bill_data["attributes"]["repeat_freq"] == "monthly"
        assert bill_data["attributes"]["active"] is True
        
        # Get bill details
        detail_response = requests.get(f"{config.BASE_URL}/bills/{bill_id}", headers=config.HEADERS)
        assert detail_response.status_code == 200
        
        # Test bill attachments endpoint
        attachments_response = requests.get(f"{config.BASE_URL}/bills/{bill_id}/attachments", headers=config.HEADERS)
        assert attachments_response.status_code == 200
        
    finally:
        # Clean up bill
        requests.delete(f"{config.BASE_URL}/bills/{bill_id}", headers=config.HEADERS)

def test_tags_organization_workflow():
    """Test tags for transaction organization - data categorization workflow."""
    # Create tag
    tag_name = generate_unique_name("tag")
    tag_payload = {
        "tag": tag_name,
        "description": "Test tag for automation"
    }
    
    create_response = requests.post(config.BASE_URL + '/tags', headers=config.HEADERS, json=tag_payload)
    assert create_response.status_code == 200
    
    tag_data = create_response.json()["data"]
    assert tag_data["attributes"]["tag"] == tag_name
    
    # List all tags
    list_response = requests.get(config.BASE_URL + '/tags', headers=config.HEADERS)
    assert list_response.status_code == 200
    
    tags = list_response.json()["data"]
    tag_names = [tag["attributes"]["tag"] for tag in tags]
    assert tag_name in tag_names
    
    # Get specific tag
    tag_response = requests.get(f"{config.BASE_URL}/tags/{tag_name}", headers=config.HEADERS)
    assert tag_response.status_code == 200
    
    # Clean up
    delete_response = requests.delete(f"{config.BASE_URL}/tags/{tag_name}", headers=config.HEADERS)
    assert delete_response.status_code == 204

def test_currencies_support():
    """Test currency support - multi-currency workflow."""
    # Get available currencies
    response = requests.get(config.BASE_URL + '/currencies', headers=config.HEADERS)
    assert response.status_code == 200
    
    currencies = response.json()["data"]
    assert len(currencies) > 0
    
    # Verify currency structure
    for currency in currencies[:3]:  # Check first 3 currencies
        attrs = currency["attributes"]
        assert "code" in attrs
        assert "name" in attrs
        assert "symbol" in attrs
        assert len(attrs["code"]) == 3  # Currency codes should be 3 characters

def test_transaction_links():
    """Test transaction links - relationship management workflow."""
    # Get link types
    response = requests.get(config.BASE_URL + '/link-types', headers=config.HEADERS)
    assert response.status_code == 200
    
    link_types = response.json().get("data", [])
    # Link types may be empty in fresh installations
    assert isinstance(link_types, list)

def test_rules_automation():
    """Test rules for transaction automation - business rule workflow."""
    # Create rule group first
    group_name = generate_unique_name("rule_group")
    group_payload = {
        "title": group_name,
        "description": "Test rule group for automation"
    }
    
    group_response = requests.post(config.BASE_URL + '/rule-groups', headers=config.HEADERS, json=group_payload)
    assert group_response.status_code == 200
    
    group_id = group_response.json()["data"]["id"]
    
    try:
        # Create rule
        rule_name = generate_unique_name("rule")
        rule_payload = {
            "title": rule_name,
            "description": "Test automation rule",
            "rule_group_id": group_id,
            "active": True,
            "strict": True,
            "stop_processing": False,
            "triggers": [
                {
                    "type": "description_contains",
                    "value": "Starbucks"
                }
            ],
            "actions": [
                {
                    "type": "set_category",
                    "value": "Food & Drinks"
                }
            ]
        }
        
        rule_response = requests.post(config.BASE_URL + '/rules', headers=config.HEADERS, json=rule_payload)
        assert rule_response.status_code == 200
        
        rule_data = rule_response.json()["data"]
        rule_id = rule_data["id"]
        
        # Verify rule structure
        assert rule_data["attributes"]["title"] == rule_name
        assert rule_data["attributes"]["active"] is True
        
        # Clean up rule
        requests.delete(f"{config.BASE_URL}/rules/{rule_id}", headers=config.HEADERS)
        
    finally:
        # Clean up rule group
        requests.delete(f"{config.BASE_URL}/rule-groups/{group_id}", headers=config.HEADERS)

def test_summary_reports():
    """Test summary and reporting endpoints - business intelligence workflow."""
    # Test basic summary
    response = requests.get(config.BASE_URL + '/summary/basic', headers=config.HEADERS)
    assert response.status_code == 200
    
    summary = response.json().get("data", {})
    assert isinstance(summary, dict)
    
    # Test chart data
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    chart_params = {
        'start': start_date,
        'end': end_date
    }
    
    # Test account chart
    account_chart_response = requests.get(config.BASE_URL + '/chart/account/overview', 
                                        headers=config.HEADERS, params=chart_params)
    assert account_chart_response.status_code == 200

def test_api_rate_limiting():
    """Test API rate limiting behavior - system stability workflow."""
    # Make multiple rapid requests to test rate limiting
    responses = []
    
    for i in range(5):
        response = requests.get(config.BASE_URL + '/about', headers=config.HEADERS)
        responses.append(response.status_code)
    
    # Most responses should be successful
    successful_responses = [r for r in responses if r == 200]
    assert len(successful_responses) >= 3, "API should handle multiple requests"

def test_invalid_authentication():
    """Test API behavior with invalid authentication - security workflow."""
    invalid_headers = {
        "Authorization": "Bearer invalid_token_12345",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    response = requests.get(config.BASE_URL + '/about', headers=invalid_headers)
    assert response.status_code == 401, "Should reject invalid authentication"

def test_api_pagination():
    """Test API pagination - data handling workflow."""
    # Test with pagination parameters
    params = {
        'page': 1,
        'limit': 5
    }
    
    response = requests.get(config.BASE_URL + '/transactions', headers=config.HEADERS, params=params)
    assert response.status_code == 200
    
    data = response.json()
    assert "meta" in data
    assert "pagination" in data["meta"]
    
    pagination = data["meta"]["pagination"]
    assert "current_page" in pagination
    assert "per_page" in pagination
    assert "total" in pagination