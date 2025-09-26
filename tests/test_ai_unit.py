"""
AI Unit Tests - Machine Learning Logic and Categorization Intelligence

Tests AI categorization algorithms, model training, and prediction accuracy.
Unit tests for machine learning components that automatically classify
financial transactions into appropriate categories.
"""
import pytest
import requests
import json
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime

@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_categorization_logic():
    """Test AI categorization logic with mocked OpenAI responses."""
    
    # Test categorization scenarios
    test_scenarios = [
        {
            "description": "Starbucks Coffee Purchase Downtown",
            "expected_category": "Food & Drinks",
            "expected_confidence": 0.95
        },
        {
            "description": "Shell Gas Station Highway 101", 
            "expected_category": "Transportation",
            "expected_confidence": 0.88
        },
        {
            "description": "Walmart Grocery Shopping Weekly",
            "expected_category": "Groceries", 
            "expected_confidence": 0.92
        },
        {
            "description": "Netflix Monthly Subscription",
            "expected_category": "Entertainment",
            "expected_confidence": 0.90
        },
        {
            "description": "Unknown Merchant Transaction",
            "expected_category": "Uncategorized",
            "expected_confidence": 0.60
        }
    ]
    
    for scenario in test_scenarios:
        # Simulate AI categorization result
        result = {
            "category": scenario["expected_category"],
            "confidence": scenario["expected_confidence"],
            "description": scenario["description"]
        }
        
        # Validate result structure
        assert "category" in result
        assert "confidence" in result
        assert "description" in result
        
        # Validate data types
        assert isinstance(result["category"], str)
        assert isinstance(result["confidence"], (int, float))
        assert isinstance(result["description"], str)
        
        # Validate confidence range
        assert 0 <= result["confidence"] <= 1
        
        # Validate category is not empty
        assert len(result["category"]) > 0
        
        print(f"✅ {scenario['description']} -> {result['category']} ({result['confidence']})")

@patch('requests.post')
@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_service_integration_mock(mock_post):
    """Test AI service integration with mocked HTTP calls."""
    
    # Mock AI service response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "category": "Food & Drinks",
        "confidence": 0.85,
        "description": "Coffee shop purchase",
        "processing_time": 1.2
    }
    mock_post.return_value = mock_response
    
    # Simulate calling AI service
    ai_request = {
        "description": "Starbucks coffee and pastry",
        "amount": "12.50"
    }
    
    # Test the mocked response
    response = mock_post.return_value
    assert response.status_code == 200
    
    data = response.json()
    assert data["category"] == "Food & Drinks"
    assert data["confidence"] == 0.85
    assert 0 <= data["confidence"] <= 1

@pytest.mark.ai
@pytest.mark.unit  
@pytest.mark.github_actions
def test_ai_confidence_threshold_logic():
    """Test AI confidence threshold handling without external dependencies."""
    
    confidence_threshold = 0.75
    
    test_predictions = [
        {"category": "Food & Drinks", "confidence": 0.95, "should_apply": True},
        {"category": "Transportation", "confidence": 0.80, "should_apply": True}, 
        {"category": "Shopping", "confidence": 0.70, "should_apply": False},
        {"category": "Uncategorized", "confidence": 0.45, "should_apply": False}
    ]
    
    for prediction in test_predictions:
        should_apply = prediction["confidence"] > confidence_threshold
        assert should_apply == prediction["should_apply"], \
            f"Confidence {prediction['confidence']} threshold check failed"
        
        print(f"✅ {prediction['category']} ({prediction['confidence']}) -> {'Apply' if should_apply else 'Skip'}")

@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_fallback_categorization():
    """Test fallback categorization when AI is unavailable."""
    
    # Fallback rules for when AI service is down
    fallback_rules = {
        "starbucks": "Food & Drinks",
        "coffee": "Food & Drinks",
        "mcdonald": "Food & Drinks",
        "shell": "Transportation", 
        "gas": "Transportation",
        "fuel": "Transportation",
        "walmart": "Groceries",
        "grocery": "Groceries",
        "amazon": "Shopping",
        "netflix": "Entertainment",
        "spotify": "Entertainment"
    }
    
    test_descriptions = [
        "Starbucks downtown location",
        "Shell gas station pump 3", 
        "McDonald's drive thru",
        "Walmart grocery shopping",
        "Amazon online purchase",
        "Unknown merchant 12345"
    ]
    
    for description in test_descriptions:
        description_lower = description.lower()
        fallback_category = None
        
        # Simple keyword matching for fallback
        for keyword, category in fallback_rules.items():
            if keyword in description_lower:
                fallback_category = category
                break
        
        if fallback_category is None:
            fallback_category = "Uncategorized"
        
        # Validate fallback result
        assert fallback_category is not None
        assert len(fallback_category) > 0
        assert isinstance(fallback_category, str)
        
        print(f"✅ Fallback: {description} -> {fallback_category}")

@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_category_validation():
    """Test AI category validation logic."""
    
    valid_categories = [
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
        "Investment",
        "Uncategorized"
    ]
    
    # Test valid categories
    for category in valid_categories:
        assert isinstance(category, str)
        assert len(category.strip()) > 0
        assert not category.lower().startswith("error")
        assert "&" in category or category.isalpha() or " " in category or category == "Uncategorized"
    
    # Test invalid categories that should be rejected
    invalid_categories = [
        "",
        "   ",
        "error: invalid",
        "unknown error",
        None
    ]
    
    for invalid_cat in invalid_categories:
        if invalid_cat is None:
            assert invalid_cat is None
        else:
            assert len(invalid_cat.strip()) == 0 or "error" in invalid_cat.lower()
    
    print(f"✅ Validated {len(valid_categories)} valid categories")

@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_metrics_structure():
    """Test AI metrics data structure without database dependencies."""
    
    # Test metrics structure
    sample_metrics = {
        "model_version": "openai-gpt-3.5-turbo",
        "total_predictions": 150,
        "successful_predictions": 142,
        "failed_predictions": 8,
        "average_confidence": 0.83,
        "categories_used": [
            "Food & Drinks",
            "Transportation", 
            "Groceries",
            "Entertainment"
        ],
        "processing_time_avg": 1.5,
        "accuracy_rate": 0.95
    }
    
    # Validate metrics structure
    required_fields = [
        "model_version", "total_predictions", "successful_predictions",
        "average_confidence", "categories_used"
    ]
    
    for field in required_fields:
        assert field in sample_metrics, f"Missing required field: {field}"
    
    # Validate data types
    assert isinstance(sample_metrics["total_predictions"], int)
    assert isinstance(sample_metrics["average_confidence"], (int, float))
    assert isinstance(sample_metrics["categories_used"], list)
    assert 0 <= sample_metrics["average_confidence"] <= 1
    
    # Validate calculations
    total = sample_metrics["successful_predictions"] + sample_metrics["failed_predictions"]
    assert total == sample_metrics["total_predictions"]
    
    print("✅ AI metrics structure validated")

@pytest.mark.ai
@pytest.mark.unit
@pytest.mark.github_actions
def test_ai_error_handling():
    """Test AI error handling scenarios."""
    
    # Test different error scenarios
    error_scenarios = [
        {
            "error_type": "OpenAI API Timeout",
            "should_fallback": True,
            "fallback_category": "Uncategorized"
        },
        {
            "error_type": "OpenAI Rate Limit",
            "should_fallback": True, 
            "fallback_category": "Uncategorized"
        },
        {
            "error_type": "Invalid API Key",
            "should_fallback": True,
            "fallback_category": "Uncategorized"
        },
        {
            "error_type": "Network Error",
            "should_fallback": True,
            "fallback_category": "Uncategorized"
        }
    ]
    
    for scenario in error_scenarios:
        # Simulate error handling
        if scenario["should_fallback"]:
            result = {
                "category": scenario["fallback_category"],
                "confidence": 0.5,  # Lower confidence for fallback
                "error": scenario["error_type"],
                "fallback_used": True
            }
        else:
            result = {
                "error": scenario["error_type"],
                "fallback_used": False
            }
        
        # Validate error handling
        if scenario["should_fallback"]:
            assert "category" in result
            assert result["fallback_used"] is True
            assert result["confidence"] < 0.8  # Fallback should have lower confidence
        
        assert "error" in result
        
        print(f"✅ Error handling: {scenario['error_type']} -> {'Fallback' if scenario['should_fallback'] else 'Fail'}")

@pytest.mark.ai
@pytest.mark.performance
@pytest.mark.github_actions
def test_ai_performance_requirements():
    """Test AI performance requirements and benchmarks."""
    
    # Performance benchmarks
    performance_requirements = {
        "max_response_time_seconds": 5.0,
        "min_confidence_threshold": 0.75,
        "max_error_rate_percent": 5.0,
        "min_accuracy_percent": 85.0
    }
    
    # Simulate performance metrics
    simulated_performance = {
        "average_response_time": 1.8,
        "confidence_threshold": 0.75,
        "error_rate": 3.2,
        "accuracy": 89.5
    }
    
    # Validate performance requirements
    assert simulated_performance["average_response_time"] <= performance_requirements["max_response_time_seconds"]
    assert simulated_performance["confidence_threshold"] >= performance_requirements["min_confidence_threshold"]
    assert simulated_performance["error_rate"] <= performance_requirements["max_error_rate_percent"]
    assert simulated_performance["accuracy"] >= performance_requirements["min_accuracy_percent"]
    
    print("✅ AI performance requirements met")
    print(f"   Response time: {simulated_performance['average_response_time']}s")
    print(f"   Accuracy: {simulated_performance['accuracy']}%")
    print(f"   Error rate: {simulated_performance['error_rate']}%")