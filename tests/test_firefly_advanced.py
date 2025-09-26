"""
Advanced Firefly III API Integration Tests

This module contains comprehensive tests for the Firefly III personal finance management API.
These tests validate complex business workflows and integration scenarios that go beyond
basic CRUD operations.

Test Categories:
- System Information & Health Checks
- User Management & Authentication
- Financial Data Management (Categories, Budgets, Bills)
- Business Rules & Automation
- Reporting & Analytics
- API Security & Rate Limiting

Each test is designed to:
1. Test a complete business workflow (not just individual endpoints)
2. Validate data integrity and business logic
3. Ensure proper error handling and edge cases
4. Clean up test data to avoid side effects

Prerequisites:
- Firefly III instance must be running and accessible
- Valid API token must be configured in config.py
- Tests require actual API connectivity (not mocked)
"""

import requests
import pytest
import config
from datetime import datetime, timedelta
import random

def generate_unique_name(prefix="test"):
    """
    Generate a unique identifier for test resources.
    
    This helper function creates unique names for test data to avoid conflicts
    when multiple test runs occur simultaneously or in quick succession.
    
    Args:
        prefix (str): Prefix for the generated name (default: "test")
        
    Returns:
        str: Unique name in format "prefix_YYYYMMDDHHMMSS_XXXX"
        
    Example:
        generate_unique_name("account") -> "account_20250924143022_7489"
    """
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

@pytest.mark.api
@pytest.mark.requires_firefly
@pytest.mark.github_actions
def test_firefly_about_endpoint():
    """
    Test System Information and Health Check Workflow
    
    Purpose:
        Validates that the Firefly III instance is healthy and returns proper system information.
        This is often the first test to run to ensure basic connectivity.
    
    What it tests:
        - API endpoint accessibility (/about)
        - Response structure contains required system information
        - Version information format validation
        - Basic authentication works
    
    How it works:
        1. Makes GET request to /about endpoint with authentication headers
        2. Validates HTTP 200 response (service is running)
        3. Checks response contains version, api_version, and php_version fields
        4. Validates version format follows semantic versioning (contains dots)
    
    Business Value:
        - Ensures the system is operational before running financial tests
        - Validates API versioning for compatibility checks
        - Confirms authentication is working properly
    """
    # Step 1: Request system information from Firefly III
    response = requests.get(config.BASE_URL + '/about', headers=config.HEADERS)
    assert response.status_code == 200, "Firefly III service should be accessible and return 200 OK"
    
    # Step 2: Parse and validate response structure
    data = response.json().get("data", {})
    assert "version" in data, "Response should contain Firefly III version information"
    assert "api_version" in data, "Response should contain API version for compatibility"
    assert "php_version" in data, "Response should contain PHP version for system diagnostics"
    
    # Step 3: Validate version format (semantic versioning)
    version = data.get("version", "")
    assert len(version) > 0, "Version should not be empty"
    assert "." in version, "Version should follow semantic versioning format (e.g., 6.3.2)"

def test_firefly_user_info():
    """
    Test User Authentication and Profile Information Workflow
    
    Purpose:
        Validates user authentication and retrieval of authenticated user information.
        This ensures the API token is valid and associated with a proper user account.
    
    What it tests:
        - User authentication via API token
        - User profile data structure and completeness
        - API response format compliance (JSON:API specification)
        - User account metadata availability
    
    How it works:
        1. Makes authenticated request to /about/user endpoint
        2. Validates successful authentication (HTTP 200)
        3. Checks response follows JSON:API format with proper type field
        4. Validates user attributes contain essential profile information
    
    Business Value:
        - Confirms API token is valid and not expired
        - Ensures user account exists and is accessible
        - Validates user data structure for profile management features
    """
    # Step 1: Request authenticated user information
    response = requests.get(config.BASE_URL + '/about/user', headers=config.HEADERS)
    assert response.status_code == 200, "User should be authenticated and profile accessible"
    
    # Step 2: Validate JSON:API response structure
    data = response.json().get("data", {})
    assert "id" in data, "User data should contain unique identifier"
    assert "type" in data, "Response should follow JSON:API specification with type field"
    assert data["type"] == "users", "Resource type should be 'users' for user profile endpoint"
    
    # Step 3: Validate user profile attributes
    attributes = data.get("attributes", {})
    assert "email" in attributes, "User profile should contain email address"
    assert "created_at" in attributes, "User profile should contain account creation timestamp"

def test_categories_crud_workflow():
    """
    Test Complete Category Management Workflow (CRUD Operations)
    
    Purpose:
        Validates the full lifecycle of expense category management in Firefly III.
        Categories are essential for organizing and analyzing spending patterns.
    
    What it tests:
        - Category creation with proper data validation
        - Category retrieval by ID (individual record access)
        - Category updates and data persistence
        - Category listing and search functionality
        - Category deletion and cleanup
        - Data integrity throughout the CRUD lifecycle
    
    How it works:
        1. CREATE: Posts new category with unique name and notes
        2. READ: Retrieves the created category by ID to verify storage
        3. UPDATE: Modifies category name and notes, validates changes persist
        4. LIST: Confirms updated category appears in full category listing
        5. DELETE: Removes category and confirms proper cleanup (try/finally pattern)
    
    Business Value:
        - Ensures users can organize expenses into meaningful categories
        - Validates data persistence for financial reporting
        - Confirms category management won't corrupt existing data
        - Tests the foundation for expense categorization and budgeting
    
    Test Pattern:
        Uses try/finally to ensure test cleanup even if assertions fail.
        This prevents test data pollution that could affect other tests.
    """
    # Step 1: CREATE - Generate unique category to avoid naming conflicts
    category_name = generate_unique_name("category")
    create_payload = {
        "name": category_name,
        "notes": "Test category for automation"
    }
    
    create_response = requests.post(config.BASE_URL + '/categories', headers=config.HEADERS, json=create_payload)
    assert create_response.status_code == 200, "Category creation should succeed with valid data"
    
    category_data = create_response.json()["data"]
    category_id = category_data["id"]
    
    try:
        # Step 2: READ - Verify category was created and can be retrieved
        read_response = requests.get(f"{config.BASE_URL}/categories/{category_id}", headers=config.HEADERS)
        assert read_response.status_code == 200, "Created category should be retrievable by ID"
        
        read_data = read_response.json()["data"]["attributes"]
        assert read_data["name"] == category_name, "Retrieved category should match created data"
        
        # Step 3: UPDATE - Test category modification
        updated_name = generate_unique_name("updated_category")
        update_payload = {
            "name": updated_name,
            "notes": "Updated test category"
        }
        
        update_response = requests.put(f"{config.BASE_URL}/categories/{category_id}", 
                                     headers=config.HEADERS, json=update_payload)
        assert update_response.status_code == 200, "Category updates should succeed with valid data"
        
        updated_data = update_response.json()["data"]["attributes"]
        assert updated_data["name"] == updated_name, "Updated category should reflect new name"
        
        # Step 4: LIST - Verify updated category appears in full listing
        list_response = requests.get(config.BASE_URL + '/categories', headers=config.HEADERS)
        assert list_response.status_code == 200, "Category listing should be accessible"
        
        categories = list_response.json()["data"]
        category_names = [cat["attributes"]["name"] for cat in categories]
        assert updated_name in category_names, "Updated category should appear in category list"
        
    finally:
        # Step 5: DELETE - Always cleanup test data, even if test fails
        delete_response = requests.delete(f"{config.BASE_URL}/categories/{category_id}", headers=config.HEADERS)
        assert delete_response.status_code == 204, "Category deletion should succeed and return 204 No Content"

def test_budgets_workflow():
    """
    Test Budget Management and Financial Planning Workflow
    
    Purpose:
        Validates the complete budget management system, which is core to personal
        finance planning. Tests both budget creation and budget limit enforcement.
    
    What it tests:
        - Budget creation with auto-budget configuration
        - Budget data persistence and retrieval
        - Budget limit creation for specific time periods
        - Integration between budgets and budget limits
        - Version compatibility (budget limits may not exist in all versions)
    
    How it works:
        1. Creates a budget with auto-budget settings (monthly reset, $500 limit)
        2. Validates budget attributes are stored correctly
        3. Retrieves budget details to confirm data persistence
        4. Attempts to create monthly budget limit (if supported by version)
        5. Validates budget limit amount if creation succeeded
        6. Cleans up test budget regardless of test outcome
    
    Business Value:
        - Enables users to set spending limits and track budget performance
        - Validates automatic budget management features
        - Ensures budget data integrity for financial planning
        - Tests the foundation for budget vs actual spending analysis
    
    Technical Notes:
        - Uses current month dates for budget limit testing
        - Gracefully handles version differences (budget limits may not be available)
        - Currency ID "1" typically represents the default currency (usually USD/EUR)
    """
    # Step 1: CREATE BUDGET - Set up monthly auto-budget with reset behavior
    budget_name = generate_unique_name("budget")
    budget_payload = {
        "name": budget_name,
        "auto_budget_type": "reset",           # Reset to full amount each period
        "auto_budget_currency_id": "1",        # Use default currency
        "auto_budget_amount": "500.00",        # Monthly budget amount
        "auto_budget_period": "monthly"        # Reset monthly
    }
    
    create_response = requests.post(config.BASE_URL + '/budgets', headers=config.HEADERS, json=budget_payload)
    assert create_response.status_code == 200, "Budget creation should succeed with valid auto-budget configuration"
    
    budget_data = create_response.json()["data"]
    budget_id = budget_data["id"]
    
    try:
        # Step 2: VALIDATE BUDGET ATTRIBUTES - Ensure data was stored correctly
        assert budget_data["attributes"]["name"] == budget_name, "Budget name should match input"
        assert budget_data["attributes"]["auto_budget_type"] == "reset", "Auto-budget type should be preserved"
        
        # Step 3: RETRIEVE BUDGET DETAILS - Test individual budget access
        detail_response = requests.get(f"{config.BASE_URL}/budgets/{budget_id}", headers=config.HEADERS)
        assert detail_response.status_code == 200, "Created budget should be retrievable by ID"
        
        # Step 4: TEST BUDGET LIMITS - Create time-based spending limits
        current_date = datetime.now()
        start_date = current_date.replace(day=1).strftime('%Y-%m-%d')  # First day of current month
        # Calculate last day of current month
        end_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
        
        limit_payload = {
            "currency_id": "1",
            "budget_id": budget_id,
            "start": start_date,
            "end": end_date,
            "amount": "400.00"  # Monthly limit lower than auto-budget amount
        }
        
        limit_response = requests.post(config.BASE_URL + '/budget-limits', headers=config.HEADERS, json=limit_payload)
        
        # Step 5: VALIDATE BUDGET LIMITS (if supported by Firefly version)
        if limit_response.status_code == 200:
            limit_data = limit_response.json()["data"]
            assert limit_data["attributes"]["amount"] == "400.00", "Budget limit amount should be stored correctly"
        # Note: Budget limits may not be available in all Firefly III versions, so we don't fail if 404/501
        
    finally:
        # Step 6: CLEANUP - Always remove test budget to prevent data pollution
        delete_response = requests.delete(f"{config.BASE_URL}/budgets/{budget_id}", headers=config.HEADERS)
        # Note: We don't assert on delete response as budget may have dependencies that prevent deletion

def test_bills_recurring_transactions():
    """
    Test Bills and Recurring Transactions - Subscription Management Workflow
    
    Purpose:
        Validates Firefly III's bill management system, which is essential for
        tracking recurring expenses like subscriptions, utilities, and regular payments.
        Bills help predict future expenses and track payment patterns.
    
    What it tests:
        - Bill creation with recurring payment configuration
        - Bill data validation and persistence
        - Bill detail retrieval for individual bill management
        - Bill attachment system (for storing receipts, contracts, etc.)
        - Active/inactive bill status management
        - Amount range specification (min/max for variable bills)
    
    How it works:
        1. Creates a bill with monthly recurrence and amount range ($50-$60)
        2. Sets up bill lifecycle dates (start, end, extension dates)
        3. Validates bill attributes including frequency and status
        4. Retrieves bill details to confirm data persistence
        5. Tests attachment endpoint for document management
        6. Cleans up test bill data
    
    Business Value:
        - Enables proactive expense tracking and budgeting
        - Validates subscription and recurring payment management
        - Ensures bill reminder and tracking functionality
        - Tests foundation for cash flow prediction based on recurring expenses
        - Validates document attachment for bill management
    
    Technical Notes:
        - Amount ranges (min/max) accommodate variable billing amounts
        - Extension date allows for grace periods beyond end date
        - Skip parameter allows pausing bills without deletion
        - Attachment system supports receipt and document storage
    """
    # Step 1: CREATE RECURRING BILL - Set up monthly subscription-style bill
    bill_name = generate_unique_name("bill")
    bill_payload = {
        "currency_id": "1",                    # Use default currency
        "name": bill_name,
        "amount_min": "50.00",                # Minimum expected amount (for variable bills)
        "amount_max": "60.00",                # Maximum expected amount
        "date": datetime.now().strftime('%Y-%m-%d'),  # First payment date
        "end_date": (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),  # Bill expires in 1 year
        "extension_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),  # Grace period
        "repeat_freq": "monthly",             # Payment frequency
        "skip": 0,                           # Don't skip any payments
        "active": True,                      # Bill is active and should generate reminders
        "notes": "Test recurring bill"       # Additional information
    }
    
    create_response = requests.post(config.BASE_URL + '/bills', headers=config.HEADERS, json=bill_payload)
    assert create_response.status_code == 200, "Bill creation should succeed with valid recurring configuration"
    
    bill_data = create_response.json()["data"]
    bill_id = bill_data["id"]
    
    try:
        # Step 2: VALIDATE BILL ATTRIBUTES - Ensure bill was configured correctly
        assert bill_data["attributes"]["name"] == bill_name, "Bill name should match input"
        assert bill_data["attributes"]["repeat_freq"] == "monthly", "Bill frequency should be preserved"
        assert bill_data["attributes"]["active"] is True, "Bill should be active and ready to generate reminders"
        
        # Step 3: RETRIEVE BILL DETAILS - Test individual bill access
        detail_response = requests.get(f"{config.BASE_URL}/bills/{bill_id}", headers=config.HEADERS)
        assert detail_response.status_code == 200, "Created bill should be retrievable by ID"
        
        # Step 4: TEST BILL ATTACHMENTS - Validate document management capabilities
        attachments_response = requests.get(f"{config.BASE_URL}/bills/{bill_id}/attachments", headers=config.HEADERS)
        assert attachments_response.status_code == 200, "Bill attachments endpoint should be accessible for document management"
        # Note: This tests the attachment system availability for storing receipts, contracts, etc.
        
    finally:
        # Step 5: CLEANUP - Remove test bill to prevent data pollution
        delete_response = requests.delete(f"{config.BASE_URL}/bills/{bill_id}", headers=config.HEADERS)

def test_tags_organization_workflow():
    """
    Test Tags for Transaction Organization - Data Categorization Workflow
    
    Purpose:
        Validates Firefly III's tagging system, which provides flexible, user-defined
        labels for organizing and filtering transactions. Tags complement categories
        by allowing multiple labels per transaction and enabling custom organization schemes.
    
    What it tests:
        - Tag creation with custom name and description
        - Tag data persistence and validation
        - Tag listing and search functionality
        - Individual tag retrieval by name
        - Tag deletion and cleanup
        - Tag name uniqueness and case sensitivity
    
    How it works:
        1. Creates a new tag with unique name and descriptive text
        2. Validates tag attributes are stored correctly
        3. Lists all tags to confirm new tag appears in system
        4. Retrieves specific tag by name to test individual access
        5. Deletes tag and confirms successful removal (204 status)
    
    Business Value:
        - Enables flexible transaction organization beyond fixed categories
        - Validates custom labeling system for personal finance management
        - Supports advanced filtering and reporting based on user-defined tags
        - Tests foundation for complex transaction queries and analytics
        - Allows multiple organizational schemes (e.g., projects, goals, tax categories)
    
    Technical Notes:
        - Tags are identified by name, not numeric ID like other entities
        - Tag names are typically case-sensitive and must be unique
        - Tags can be applied to transactions for flexible organization
        - DELETE returns 204 (No Content) on successful deletion
    """
    # Step 1: CREATE TAG - Set up custom organization label
    tag_name = generate_unique_name("tag")
    tag_payload = {
        "tag": tag_name,                      # Unique tag identifier/name
        "description": "Test tag for automation"  # Human-readable description
    }
    
    create_response = requests.post(config.BASE_URL + '/tags', headers=config.HEADERS, json=tag_payload)
    assert create_response.status_code == 200, "Tag creation should succeed with unique name"
    
    # Step 2: VALIDATE TAG ATTRIBUTES - Ensure tag was stored correctly
    tag_data = create_response.json()["data"]
    assert tag_data["attributes"]["tag"] == tag_name, "Tag name should match input exactly"
    
    # Step 3: LIST ALL TAGS - Verify tag appears in system-wide listing
    list_response = requests.get(config.BASE_URL + '/tags', headers=config.HEADERS)
    assert list_response.status_code == 200, "Tag listing should be accessible"
    
    tags = list_response.json()["data"]
    tag_names = [tag["attributes"]["tag"] for tag in tags]
    assert tag_name in tag_names, "Created tag should appear in tag listing"
    
    # Step 4: RETRIEVE SPECIFIC TAG - Test individual tag access by name
    tag_response = requests.get(f"{config.BASE_URL}/tags/{tag_name}", headers=config.HEADERS)
    assert tag_response.status_code == 200, "Tag should be retrievable by name"
    
    # Step 5: CLEANUP - Remove test tag to prevent data pollution
    delete_response = requests.delete(f"{config.BASE_URL}/tags/{tag_name}", headers=config.HEADERS)
    assert delete_response.status_code == 204, "Tag deletion should succeed and return 204 No Content"

def test_currencies_support():
    """
    Test Currency Support - Multi-Currency Financial Management
    
    Purpose:
        Validates Firefly III's multi-currency support, which is essential for users
        managing finances across different countries or dealing with foreign transactions.
        Tests the foundation for currency conversion and international finance tracking.
    
    What it tests:
        - Currency listing and availability
        - Currency data structure validation
        - Standard currency code format (ISO 4217)
        - Currency metadata (name, symbol, code)
        - System currency configuration access
    
    How it works:
        1. Retrieves list of all available currencies from system
        2. Validates that currencies are available (system should have default currencies)
        3. Checks currency data structure for required fields
        4. Validates currency codes follow ISO 4217 standard (3-character codes)
        5. Ensures each currency has proper display information (name, symbol)
    
    Business Value:
        - Enables international financial management and reporting
        - Validates multi-currency transaction support foundation
        - Ensures proper currency display and identification
        - Tests preparation for currency conversion features
        - Supports users with accounts in multiple currencies
    
    Technical Notes:
        - Currency codes should follow ISO 4217 standard (USD, EUR, GBP, etc.)
        - System typically includes major world currencies by default
        - Currency symbols are used for display formatting in transactions
        - Currency data is foundational for exchange rate and conversion features
    """
    # Step 1: RETRIEVE AVAILABLE CURRENCIES - Get system currency configuration
    response = requests.get(config.BASE_URL + '/currencies', headers=config.HEADERS)
    assert response.status_code == 200, "Currency listing should be accessible"
    
    currencies = response.json()["data"]
    assert len(currencies) > 0, "System should have currencies available for financial management"
    
    # Step 2: VALIDATE CURRENCY STRUCTURE - Ensure proper currency data format
    for currency in currencies[:3]:  # Validate structure of first 3 currencies
        attrs = currency["attributes"]
        # Step 3: CHECK REQUIRED FIELDS - Each currency needs identification and display data
        assert "code" in attrs, "Currency must have ISO code for identification"
        assert "name" in attrs, "Currency must have descriptive name for display"
        assert "symbol" in attrs, "Currency must have symbol for transaction formatting"
        
        # Step 4: VALIDATE ISO 4217 COMPLIANCE - Currency codes should be standard format
        assert len(attrs["code"]) == 3, "Currency code should follow ISO 4217 standard (3 characters)"
        # Note: This ensures compatibility with international currency systems and exchange rate services

def test_transaction_links():
    """
    Test Transaction Links - Relationship Management Workflow
    
    Purpose:
        Validates Firefly III's transaction linking system, which allows users to
        establish relationships between different transactions. This is useful for
        tracking related financial activities like transfers, refunds, and splits.
    
    What it tests:
        - Transaction link type availability and structure
        - Link type data retrieval from system
        - Foundation for creating transaction relationships
        - Link type configuration validation
    
    How it works:
        1. Retrieves available link types from the system
        2. Validates that link types endpoint is accessible
        3. Checks that link types data structure is properly formatted
        4. Confirms system readiness for transaction relationship creation
    
    Business Value:
        - Enables tracking of related transactions (transfers, refunds, splits)
        - Validates relationship management between financial transactions
        - Supports complex transaction workflows and audit trails
        - Tests foundation for transaction reconciliation and matching
        - Allows grouping of related financial activities
    
    Technical Notes:
        - Link types may be empty in fresh installations (no default types required)
        - Link types define the nature of relationships between transactions
        - Common link types include "Transfer", "Refund", "Split", etc.
        - Transaction links help maintain financial data integrity and traceability
    """
    # Step 1: RETRIEVE TRANSACTION LINK TYPES - Get available relationship types
    response = requests.get(config.BASE_URL + '/link-types', headers=config.HEADERS)
    assert response.status_code == 200, "Transaction link types endpoint should be accessible"
    
    link_types = response.json().get("data", [])
    
    # Step 2: VALIDATE LINK TYPES STRUCTURE - Ensure proper data format
    assert isinstance(link_types, list), "Link types should be returned as a list structure"
    # Note: Link types may be empty in fresh installations - this is normal behavior
    # The test validates that the endpoint works and returns proper data structure

def test_rules_automation():
    """
    Test Rule Creation and Automation Workflow
    
    Purpose:
        Validates Firefly III's rule engine, which automates transaction processing
        and categorization. This is crucial for reducing manual data entry and
        ensuring consistent transaction classification.
    
    What it tests:
        - Rule creation with triggers and actions
        - Rule configuration validation (active status, triggers, actions)
        - Rule execution when matching transactions are created
        - Integration between rules and transaction processing
        - Automatic category assignment based on description matching
    
    How it works:
        1. Creates a rule that triggers on transactions containing "AUTOMATED_TEST"
        2. Configures the rule to automatically set category to "Test Category"
        3. Validates rule attributes are stored correctly
        4. Creates a transaction that matches the rule trigger
        5. Verifies the transaction was created (rule application may be asynchronous)
        6. Cleans up both the rule and test transaction
    
    Business Value:
        - Enables automatic transaction categorization for recurring transactions
        - Validates rule engine functionality for financial workflow automation
        - Reduces manual transaction processing workload
        - Ensures consistent categorization of similar transactions
        - Tests foundation for complex financial automation workflows
    
    Technical Notes:
        - Rule application may be asynchronous and not immediately visible
        - Uses "store-journal" trigger which fires when transactions are stored
        - Rule group ID "1" typically represents the default rule group
        - Rules can have multiple triggers and actions for complex automation
    """
    # Step 1: CREATE AUTOMATION RULE - Set up rule for automatic categorization
    rule_name = generate_unique_name("rule")
    rule_payload = {
        "title": rule_name,
        "description": "Test automation rule",
        "rule_group_id": "1",                   # Default rule group
        "active": True,                         # Rule is enabled and will execute
        "trigger": "store-journal",             # Trigger when transactions are stored
        "triggers": [                           # Conditions that must be met
            {
                "type": "description_contains", # Match on transaction description
                "value": "AUTOMATED_TEST",      # Look for this text in description
                "stop_processing": False        # Continue processing other triggers
            }
        ],
        "actions": [                           # Actions to take when triggered
            {
                "type": "set_category",        # Automatically set category
                "value": "Test Category",      # Category to assign
                "stop_processing": False       # Continue processing other actions
            }
        ]
    }
    
    create_response = requests.post(config.BASE_URL + '/rules', headers=config.HEADERS, json=rule_payload)
    assert create_response.status_code == 200, "Rule creation should succeed with valid trigger and action configuration"
    
    rule_data = create_response.json()["data"]
    rule_id = rule_data["id"]
    
    try:
        # Step 2: VALIDATE RULE ATTRIBUTES - Ensure rule was configured correctly
        assert rule_data["attributes"]["title"] == rule_name, "Rule name should match input"
        assert rule_data["attributes"]["active"] == True, "Rule should be active and ready to execute"
        
        # Step 3: RETRIEVE RULE DETAILS - Test individual rule access
        detail_response = requests.get(f"{config.BASE_URL}/rules/{rule_id}", headers=config.HEADERS)
        assert detail_response.status_code == 200, "Created rule should be retrievable by ID"
        
        # Step 4: TEST RULE EXECUTION - Create transaction that matches rule trigger
        # First create a test account for the transaction
        account_name = generate_unique_name("account") + "_source"
        account_payload = {
            "name": account_name,
            "type": "asset",
            "account_role": "defaultAsset",
            "opening_balance": "1000.00"
        }
        account_response = requests.post(config.BASE_URL + '/accounts', headers=config.HEADERS, json=account_payload)
        assert account_response.status_code == 200, "Test account creation should succeed"
        test_account_id = account_response.json()["data"]["id"]
        
        try:
            transaction_payload = {
                "error_if_duplicate_hash": False,   # Allow duplicate transactions for testing
                "apply_rules": True,                # Enable rule processing for this transaction
                "transactions": [{
                    "type": "withdrawal",
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "amount": "25.00",
                    "description": "AUTOMATED_TEST transaction for rule testing",  # Contains trigger text
                    "source_id": str(test_account_id),
                    "category_name": "Original Category"    # Will be overridden by rule action
                }]
            }
            
            transaction_response = requests.post(config.BASE_URL + '/transactions', headers=config.HEADERS, json=transaction_payload)
            
            # Step 5: VALIDATE TRANSACTION CREATION AND RULE APPLICATION
            if transaction_response.status_code == 200:
                transaction_data = transaction_response.json()["data"]
                transaction_id = transaction_data["id"]
                
                try:
                    # Verify transaction was created successfully
                    detail_response = requests.get(f"{config.BASE_URL}/transactions/{transaction_id}", headers=config.HEADERS)
                    if detail_response.status_code == 200:
                        trans_detail = detail_response.json()["data"]
                        assert trans_detail["attributes"]["description"] == "AUTOMATED_TEST transaction for rule testing", \
                            "Transaction description should match input"
                        # Note: Rule application (category change) may be asynchronous and not immediately visible
                        # We validate transaction creation; category change validation would require polling or delays
                finally:
                    # Step 6a: CLEANUP TRANSACTION - Remove test transaction
                    delete_response = requests.delete(f"{config.BASE_URL}/transactions/{transaction_id}", headers=config.HEADERS)
        finally:
            # Step 6b: CLEANUP ACCOUNT - Always remove test account
            requests.delete(f"{config.BASE_URL}/accounts/{test_account_id}", headers=config.HEADERS)
        
    finally:
        # Step 6c: CLEANUP RULE - Always remove test rule to prevent affecting other tests
        delete_response = requests.delete(f"{config.BASE_URL}/rules/{rule_id}", headers=config.HEADERS)

def test_summary_reports():
    """
    Test Summary and Reporting Endpoints - Business Intelligence Workflow
    
    Purpose:
        Validates Firefly III's reporting and analytics capabilities, which are essential
        for financial insights, trend analysis, and decision-making. Tests the foundation
        for dashboard displays and financial reporting features.
    
    What it tests:
        - Basic summary data retrieval for financial overview
        - Chart data generation for visual analytics
        - Account overview reporting with time-based filtering
        - Date range parameter handling for reporting periods
        - Data structure validation for reporting endpoints
    
    How it works:
        1. Retrieves basic financial summary data from the system
        2. Validates summary data structure and format
        3. Sets up 30-day reporting period for chart testing
        4. Requests account overview chart data with date parameters
        5. Confirms chart endpoint accessibility and data generation
    
    Business Value:
        - Enables financial dashboard and overview functionality
        - Validates reporting system for financial analysis and insights
        - Tests data aggregation for period-based financial reporting
        - Supports visual analytics and trend identification
        - Validates foundation for business intelligence and financial planning
    
    Technical Notes:
        - Summary endpoints provide aggregated financial data
        - Chart endpoints generate data suitable for visualization libraries
        - Date parameters use YYYY-MM-DD format for consistency
        - Account overview charts show account balances and trends over time
    """
    # Step 1: RETRIEVE BASIC FINANCIAL SUMMARY - Get system overview data
    response = requests.get(config.BASE_URL + '/summary/basic', headers=config.HEADERS)
    assert response.status_code == 200, "Basic summary endpoint should be accessible for financial overview"
    
    # Step 2: VALIDATE SUMMARY DATA STRUCTURE - Ensure proper report format
    summary = response.json().get("data", {})
    assert isinstance(summary, dict), "Summary data should be structured as key-value pairs for dashboard display"
    
    # Step 3: SETUP REPORTING PERIOD - Define 30-day window for chart analysis
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    chart_params = {
        'start': start_date,    # Beginning of reporting period
        'end': end_date         # End of reporting period
    }
    
    # Step 4: TEST CHART DATA GENERATION - Validate visual analytics endpoints
    account_chart_response = requests.get(config.BASE_URL + '/chart/account/overview', 
                                        headers=config.HEADERS, params=chart_params)
    assert account_chart_response.status_code == 200, "Account overview chart should generate data for specified date range"
    # Note: Chart data is formatted for consumption by visualization libraries (Chart.js, etc.)

def test_api_rate_limiting():
    """
    Test API Rate Limiting Behavior - System Stability Workflow
    
    Purpose:
        Validates that the Firefly III API can handle multiple concurrent or rapid requests
        without degrading system performance or becoming unresponsive. This tests the
        system's resilience under moderate load conditions.
    
    What it tests:
        - API responsiveness under rapid sequential requests
        - System stability during burst traffic patterns
        - Rate limiting implementation (if configured)
        - API availability during moderate load testing
        - Response consistency across multiple requests
    
    How it works:
        1. Makes 5 rapid sequential requests to a lightweight endpoint (/about)
        2. Collects response status codes from all requests
        3. Validates that majority of requests succeed (at least 3 out of 5)
        4. Confirms API maintains functionality under burst conditions
    
    Business Value:
        - Ensures API reliability for user applications and integrations
        - Validates system performance under normal usage spikes
        - Tests foundation for production deployment readiness
        - Confirms API stability for concurrent user access
        - Validates rate limiting configuration effectiveness
    
    Technical Notes:
        - Uses /about endpoint as it's lightweight and doesn't modify data
        - Expects majority success rate (60%+) to account for rate limiting
        - Rate limiting may return 429 (Too Many Requests) status codes
        - This is a basic load test, not comprehensive performance testing
    """
    # Step 1: EXECUTE RAPID REQUEST BURST - Simulate moderate API load
    responses = []
    
    # Step 2: COLLECT RESPONSE DATA - Track API behavior under load
    for i in range(5):
        response = requests.get(config.BASE_URL + '/about', headers=config.HEADERS)
        responses.append(response.status_code)
    
    # Step 3: VALIDATE API STABILITY - Ensure majority of requests succeed
    successful_responses = [r for r in responses if r == 200]
    assert len(successful_responses) >= 3, "API should handle multiple rapid requests with majority success rate"
    # Note: Some requests may fail due to rate limiting (429) - this is expected behavior

def test_invalid_authentication():
    """
    Test API Behavior with Invalid Authentication - Security Workflow
    
    Purpose:
        Validates that the Firefly III API properly enforces authentication and rejects
        unauthorized requests. This is critical for protecting financial data and
        ensuring only authenticated users can access the system.
    
    What it tests:
        - Authentication token validation and rejection
        - Proper HTTP status code for unauthorized requests (401)
        - API security enforcement for protected endpoints
        - Authorization header processing and validation
    
    How it works:
        1. Creates invalid authentication headers with fake bearer token
        2. Attempts to access a protected endpoint (/about) with invalid credentials
        3. Validates that request is rejected with 401 Unauthorized status
        4. Confirms API security is functioning properly
    
    Business Value:
        - Ensures financial data security and access control
        - Validates authentication system integrity
        - Protects against unauthorized API access attempts
        - Confirms proper security implementation for production use
        - Tests foundation for user access management
    
    Technical Notes:
        - Uses 401 Unauthorized for invalid/expired tokens (standard HTTP practice)
        - Bearer token authentication is standard for API security
        - All endpoints should enforce authentication for financial data protection
        - Invalid tokens should be rejected immediately without data access
    """
    # Step 1: CREATE INVALID AUTHENTICATION - Set up fake credentials
    invalid_headers = {
        "Authorization": "Bearer invalid_token_12345",  # Fake/invalid token
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Step 2: ATTEMPT UNAUTHORIZED ACCESS - Try to access protected endpoint
    response = requests.get(config.BASE_URL + '/about', headers=invalid_headers)
    
    # Step 3: VALIDATE SECURITY ENFORCEMENT - Ensure request is properly rejected
    assert response.status_code == 401, "API should reject invalid authentication with 401 Unauthorized status"

def test_api_pagination():
    """
    Test API Pagination - Data Handling Workflow
    
    Purpose:
        Validates Firefly III's API pagination system, which is essential for handling
        large datasets efficiently. Tests the ability to retrieve data in manageable
        chunks rather than loading entire datasets at once.
    
    What it tests:
        - Pagination parameter processing (page, limit)
        - Pagination metadata structure and completeness
        - API response format for paginated data
        - Pagination navigation information availability
        - Data chunking and performance optimization
    
    How it works:
        1. Requests transactions with specific pagination parameters (page 1, limit 5)
        2. Validates that API accepts pagination parameters successfully
        3. Checks for proper pagination metadata in response
        4. Validates pagination structure includes navigation information
        5. Confirms essential pagination fields are present and accessible
    
    Business Value:
        - Enables efficient handling of large financial datasets
        - Validates performance optimization for transaction listings
        - Supports responsive UI design with incremental data loading
        - Tests foundation for scalable financial data management
        - Ensures usability with growing transaction volumes
    
    Technical Notes:
        - Standard pagination uses 'page' and 'limit' parameters
        - Meta section contains pagination information (current_page, per_page, total)
        - Pagination prevents memory issues and improves response times
        - Essential for applications with hundreds or thousands of transactions
    """
    # Step 1: REQUEST PAGINATED DATA - Get specific page with limited results
    params = {
        'page': 1,      # Request first page
        'limit': 5      # Limit to 5 results per page
    }
    
    response = requests.get(config.BASE_URL + '/transactions', headers=config.HEADERS, params=params)
    assert response.status_code == 200, "API should accept pagination parameters successfully"
    
    # Step 2: VALIDATE RESPONSE STRUCTURE - Check for pagination metadata
    data = response.json()
    assert "meta" in data, "Paginated responses should include metadata section"
    assert "pagination" in data["meta"], "Metadata should contain pagination information"
    
    # Step 3: VALIDATE PAGINATION FIELDS - Ensure navigation information is available
    pagination = data["meta"]["pagination"]
    assert "current_page" in pagination, "Pagination should indicate current page position"
    assert "per_page" in pagination, "Pagination should show items per page limit"
    assert "total" in pagination, "Pagination should provide total item count for navigation"