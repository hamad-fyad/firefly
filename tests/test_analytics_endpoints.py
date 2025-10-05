"""
Test suite for enhanced analytics endpoints in the AI webhook system.
Tests the new multi-event financial intelligence capabilities.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Test fixtures and setup
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test' + 'x' * 47,  # 51 chars total
        'FIREFLY_TOKEN': 'test_token_' + 'x' * 52,  # 64 chars total
        'FIREFLY_API_URL': 'http://localhost:8080'
    }):
        yield

@pytest.fixture
def sample_webhook_events():
    """Sample webhook events for different Firefly III event types."""
    return {
        'transaction_store': {
            "trigger": "STORE_TRANSACTION",
            "response": "TRANSACTIONS",
            "content": {
                "id": "123",
                "type": "withdrawal",
                "attributes": {
                    "transactions": [{
                        "description": "Coffee at Starbucks",
                        "amount": "4.50",
                        "type": "withdrawal",
                        "date": "2024-01-15",
                        "source_name": "Checking Account",
                        "destination_name": "Starbucks"
                    }]
                }
            }
        },
        'budget_store': {
            "trigger": "STORE_BUDGET",
            "response": "BUDGETS", 
            "content": {
                "id": "456",
                "type": "budgets",
                "attributes": {
                    "name": "Dining Out",
                    "period": "monthly",
                    "amount": "200.00"
                }
            }
        },
        'account_store': {
            "trigger": "STORE_ACCOUNT",
            "response": "ACCOUNTS",
            "content": {
                "id": "789",
                "type": "accounts",
                "attributes": {
                    "name": "New Savings Account",
                    "type": "asset",
                    "account_role": "savingAsset",
                    "opening_balance": "1000.00"
                }
            }
        }
    }

class TestWebhookAnalyticsEndpoints:
    """Test the enhanced webhook service analytics endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_env_vars):
        """Setup test client with mocked environment."""
        from webhook_service.main import app
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test basic health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "analytics_enabled" in data
    
    def test_multi_event_webhook_processing(self, sample_webhook_events):
        """Test that different webhook events are processed correctly."""
        # Test transaction event
        response = self.client.post("/webhook/firefly", 
                                   json=sample_webhook_events['transaction_store'])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["event_type"] == "STORE_TRANSACTION"
        assert "ai_analysis" in data
    
    def test_budget_webhook_processing(self, sample_webhook_events):
        """Test budget creation webhook processing."""
        response = self.client.post("/webhook/firefly",
                                   json=sample_webhook_events['budget_store'])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["event_type"] == "STORE_BUDGET"
        assert "budget_analysis" in data
    
    def test_account_webhook_processing(self, sample_webhook_events):
        """Test account creation webhook processing."""
        response = self.client.post("/webhook/firefly",
                                   json=sample_webhook_events['account_store'])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success" 
        assert data["event_type"] == "STORE_ACCOUNT"
    
    def test_real_time_insights_endpoint(self):
        """Test real-time insights analytics endpoint."""
        response = self.client.get("/analytics/real-time-insights")
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "spending_velocity", "budget_health", "recent_activity",
            "ai_confidence", "anomalies_detected", "last_updated"
        ]
        for field in expected_fields:
            assert field in data
    
    def test_spending_patterns_endpoint(self):
        """Test spending patterns analytics endpoint.""" 
        response = self.client.get("/analytics/spending-patterns")
        assert response.status_code == 200
        data = response.json()
        
        assert "category_trends" in data
        assert "spending_velocity" in data
        assert "pattern_analysis" in data
        assert "predictions" in data
    
    def test_budget_analysis_endpoint(self):
        """Test budget analysis analytics endpoint."""
        response = self.client.get("/analytics/budget-analysis") 
        assert response.status_code == 200
        data = response.json()
        
        assert "budget_performance" in data
        assert "category_allocation" in data
        assert "recommendations" in data
    
    def test_financial_health_endpoint(self):
        """Test financial health score endpoint."""
        response = self.client.get("/analytics/financial-health")
        assert response.status_code == 200
        data = response.json()
        
        assert "health_score" in data
        assert "factors" in data
        assert "recommendations" in data
        assert "trend" in data
    
    def test_legacy_webhook_compatibility(self):
        """Test that legacy webhook endpoint still works."""
        legacy_payload = {
            "trigger": "STORE_TRANSACTION",
            "response": "TRANSACTIONS",
            "content": {
                "attributes": {
                    "transactions": [{
                        "description": "Test transaction",
                        "amount": "10.00"
                    }]
                }
            }
        }
        
        response = self.client.post("/webhook", json=legacy_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestAIServiceAnalyticsEndpoints:
    """Test the enhanced AI service analytics endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_env_vars):
        """Setup AI service test client."""
        # Mock the AI service imports
        with patch('openai.OpenAI'):
            # Add AI categorizer to path
            ai_service_path = os.path.join(project_root, 'firefly-ai-categorizer')
            if ai_service_path not in sys.path:
                sys.path.insert(0, ai_service_path)
            from app.main import app
            self.client = TestClient(app)
    
    @patch('app.main.predict_category')
    def test_analyze_transaction_endpoint(self, mock_predict):
        """Test enhanced transaction analysis endpoint."""
        mock_predict.return_value = {
            "category": "Food & Dining",
            "confidence": 0.92
        }
        
        payload = {
            "description": "Lunch at McDonald's",
            "amount": "12.50",
            "type": "withdrawal"
        }
        
        response = self.client.post("/analyze-transaction", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "categorization" in data
        assert "spending_analysis" in data
        assert "pattern_recognition" in data
        assert "recommendations" in data
    
    def test_analyze_budget_endpoint(self):
        """Test budget analysis endpoint."""
        payload = {
            "name": "Groceries",
            "amount": "400.00", 
            "period": "monthly"
        }
        
        response = self.client.post("/analyze-budget", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "budget_name" in data
        assert "realism_score" in data
        assert "recommendations" in data
        assert "success_probability" in data
    
    @patch('app.main.get_predictions_data')
    def test_financial_insights_endpoint(self, mock_predictions):
        """Test financial insights endpoint."""
        mock_predictions.return_value = [
            {"predicted_category": "Food", "confidence": 0.85},
            {"predicted_category": "Transport", "confidence": 0.92},
            {"predicted_category": "Food", "confidence": 0.78}
        ]
        
        response = self.client.get("/analytics/insights")
        assert response.status_code == 200
        data = response.json()
        
        assert "spending_velocity" in data
        assert "category_trends" in data
        assert "ai_confidence" in data
        assert "recommendations" in data
    
    @patch('app.main.get_predictions_data')
    def test_spending_patterns_endpoint(self, mock_predictions):
        """Test spending patterns analysis endpoint."""
        mock_predictions.return_value = [
            {"predicted_category": "Food", "timestamp": "2024-01-15"},
            {"predicted_category": "Transport", "timestamp": "2024-01-16"},
            {"predicted_category": "Food", "timestamp": "2024-01-17"}
        ]
        
        response = self.client.get("/analytics/patterns")
        assert response.status_code == 200
        data = response.json()
        
        assert "category_distribution" in data
        assert "trends" in data
        assert "predictions" in data
    
    def test_budget_analysis_comprehensive(self):
        """Test comprehensive budget analysis endpoint."""
        response = self.client.get("/analytics/budget-analysis")
        assert response.status_code == 200
        data = response.json()
        
        assert "budget_performance" in data
        assert "recommendations" in data
        assert "insights" in data
    
    @patch('app.main.get_model_performance_summary')
    @patch('app.main.get_predictions_data')
    def test_health_score_endpoint(self, mock_predictions, mock_performance):
        """Test financial health score calculation."""
        mock_predictions.return_value = [{"confidence": 0.85}] * 8
        mock_performance.return_value = {"accuracy": 0.87}
        
        response = self.client.get("/analytics/health-score")
        assert response.status_code == 200
        data = response.json()
        
        assert "health_score" in data
        assert "factors" in data
        assert "insights" in data
        assert "trend" in data
    
    def test_store_analytics_endpoint(self):
        """Test analytics data storage endpoint."""
        payload = {
            "transaction_id": "123",
            "insights": {
                "category": "Food",
                "confidence": 0.92,
                "spending_pattern": "normal"
            }
        }
        
        response = self.client.post("/store-analytics", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "analytics_stored"
        assert data["transaction_id"] == "123"


class TestIntegrationWorkflow:
    """Test the integration between webhook service and AI analytics."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_env_vars):
        """Setup integration test environment."""
        from webhook_service.main import app as webhook_app
        self.webhook_client = TestClient(webhook_app)
    
    @patch('webhook_service.main.requests.post')
    def test_end_to_end_transaction_flow(self, mock_ai_request):
        """Test complete flow from webhook to AI analysis."""
        # Mock AI service response
        mock_ai_request.return_value.json.return_value = {
            "categorization": {"category": "Food", "confidence": 0.89},
            "spending_analysis": {"amount_analysis": "normal"},
            "recommendations": ["Track dining expenses"]
        }
        mock_ai_request.return_value.status_code = 200
        
        # Send webhook event
        webhook_payload = {
            "trigger": "STORE_TRANSACTION",
            "response": "TRANSACTIONS",
            "content": {
                "attributes": {
                    "transactions": [{
                        "description": "Dinner at Italian restaurant",
                        "amount": "45.00",
                        "type": "withdrawal"
                    }]
                }
            }
        }
        
        response = self.webhook_client.post("/webhook/firefly", json=webhook_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "ai_analysis" in data
        
        # Verify AI service was called
        assert mock_ai_request.called
        ai_call_args = mock_ai_request.call_args
        assert "/analyze-transaction" in ai_call_args[0][0]
    
    @patch('webhook_service.main.requests.post') 
    def test_budget_creation_workflow(self, mock_ai_request):
        """Test budget creation and analysis workflow."""
        # Mock AI budget analysis response
        mock_ai_request.return_value.json.return_value = {
            "budget_name": "Entertainment",
            "realism_score": 0.75,
            "recommendations": ["Monitor movie subscriptions"]
        }
        mock_ai_request.return_value.status_code = 200
        
        webhook_payload = {
            "trigger": "STORE_BUDGET",
            "response": "BUDGETS",
            "content": {
                "attributes": {
                    "name": "Entertainment",
                    "period": "monthly",
                    "amount": "100.00"
                }
            }
        }
        
        response = self.webhook_client.post("/webhook/firefly", json=webhook_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["event_type"] == "STORE_BUDGET"
        assert "budget_analysis" in data


class TestErrorHandling:
    """Test error handling in analytics endpoints."""
    
    @pytest.fixture(autouse=True) 
    def setup(self, mock_env_vars):
        """Setup test clients."""
        from webhook_service.main import app as webhook_app
        self.webhook_client = TestClient(webhook_app)
        
        with patch('openai.OpenAI'):
            # Add AI categorizer to path  
            ai_service_path = os.path.join(project_root, 'firefly-ai-categorizer')
            if ai_service_path not in sys.path:
                sys.path.insert(0, ai_service_path)
            from app.main import app as ai_app
            self.ai_client = TestClient(ai_app)
    
    def test_invalid_webhook_payload(self):
        """Test handling of invalid webhook payloads."""
        invalid_payload = {"invalid": "data"}
        
        response = self.webhook_client.post("/webhook/firefly", json=invalid_payload)
        assert response.status_code == 200  # Should handle gracefully
        data = response.json()
        assert "error" in data or data.get("status") == "success"
    
    def test_ai_service_unavailable(self):
        """Test webhook handling when AI service is unavailable."""
        with patch('webhook_service.main.requests.post') as mock_request:
            mock_request.side_effect = Exception("AI service unavailable")
            
            webhook_payload = {
                "trigger": "STORE_TRANSACTION",
                "response": "TRANSACTIONS", 
                "content": {"attributes": {"transactions": [{"description": "test"}]}}
            }
            
            response = self.webhook_client.post("/webhook/firefly", json=webhook_payload)
            # Should still process the webhook even if AI analysis fails
            assert response.status_code == 200
    
    def test_missing_transaction_description(self):
        """Test AI analysis with missing required data."""
        payload = {"amount": "10.00"}  # Missing description
        
        response = self.ai_client.post("/analyze-transaction", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])