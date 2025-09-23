# Firefly III AI Integration Test Suite

This comprehensive test suite validates the Firefly III AI categorization system, including the core Firefly API, AI categorizer service, webhook integration, and database storage.

## Overview

The test suite is designed to validate:

1. **Firefly III API** - Core financial management functionality
2. **AI Categorizer Service** - OpenAI-powered transaction categorization  
3. **Webhook Service** - Real-time transaction processing
4. **Database Integration** - PostgreSQL metrics and AI model storage
5. **End-to-End Workflows** - Complete business process validation

## Test Organization

### Test Files

- `test_account.py` - Original account management tests
- `test_firefly_transactions.py` - Transaction CRUD and business workflows
- `test_firefly_advanced.py` - Advanced Firefly features (budgets, bills, rules)
- `test_ai_service.py` - AI categorization functionality and performance
- `test_webhook_service.py` - Webhook processing and integration

### Test Categories (Pytest Markers)

- `@pytest.mark.unit` - Unit tests with mocks
- `@pytest.mark.integration` - Multi-service integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.business_workflow` - End-to-end business process validation
- `@pytest.mark.requires_firefly` - Requires Firefly III running
- `@pytest.mark.requires_ai_service` - Requires AI service running
- `@pytest.mark.requires_webhook_service` - Requires webhook service running
- `@pytest.mark.requires_database` - Requires PostgreSQL database

## Setup

### Prerequisites

1. **Docker and Docker Compose** - For running services
2. **Python 3.8+** - For running tests
3. **Required Python packages**:
   ```bash
   pip install pytest requests python-dotenv pytest-cov allure-pytest
   ```

### Environment Configuration

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure API tokens** in `.env`:
   ```env
   FIREFLY_TOKEN=your_firefly_api_token
   OPENAI_API_KEY=your_openai_api_key
   API_TESTING_TOKEN=your_api_testing_token
   ```

3. **Database setup** (automated via Docker):
   ```env
   DATABASE_URL=postgresql://ai_user:ai_password@ai-db:5432/ai_metrics
   ```

## Running Tests

### Quick Test Commands

```bash
# Check service status
python run_tests.py check

# Run all tests
python run_tests.py all

# Run specific test suites
python run_tests.py unit        # Unit tests only
python run_tests.py api         # Firefly API tests
python run_tests.py ai          # AI service tests
python run_tests.py webhook     # Webhook tests
python run_tests.py integration # Full integration tests

# Start/stop services
python run_tests.py start
python run_tests.py stop
```

### Manual Pytest Commands

```bash
# Run all tests
pytest

# Run specific markers
pytest -m unit
pytest -m "api and business_workflow"
pytest -m "not requires_ai_service"

# Run specific files
pytest tests/test_firefly_transactions.py
pytest tests/test_ai_service.py -v

# Run with coverage
pytest --cov=firefly-ai-categorizer --cov-report=html
```

## Service Management

### Starting Services

```bash
# Start all services
docker compose up -d

# Start specific services
docker compose up -d ai-service ai-db
docker compose up -d webhook-service
```

### Service Health Checks

```bash
# Firefly III
curl http://localhost:8080/api/v1/about

# AI Service
curl http://localhost:8082/health

# Webhook Service  
curl http://localhost:8001/health

# AI Database
docker compose exec ai-db pg_isready -U ai_user
```

## Test Data Management

### Automatic Cleanup

Tests automatically clean up created data:
- Test accounts are deleted after test completion
- Test transactions are removed
- Test categories, budgets, and bills are cleaned up

### Manual Cleanup

If tests fail and leave test data:

```bash
# List test accounts
curl -H "Authorization: Bearer $FIREFLY_TOKEN" \
     "http://localhost:8080/api/v1/accounts" | jq '.data[] | select(.attributes.name | startswith("test_"))'

# Clean up via Firefly UI or API
```

## Business Workflow Tests

### Core Workflows Tested

1. **Expense Tracking**
   - Create withdrawal transactions
   - Categorize expenses automatically
   - Track spending by category

2. **Income Management**
   - Record deposit transactions
   - Categorize income sources
   - Monitor income trends

3. **Budget Management**
   - Create and manage budgets
   - Track budget performance
   - Set budget limits and alerts

4. **AI Categorization**
   - Automatic transaction categorization
   - Confidence threshold handling
   - Fallback categorization rules

5. **Webhook Processing**
   - Real-time transaction processing
   - AI service integration
   - Error handling and recovery

### Example Business Scenarios

```python
# Expense tracking workflow
def test_expense_workflow():
    # Create expense account
    # Record coffee purchase transaction
    # Verify AI categorizes as "Food & Drinks"
    # Check transaction appears in expense reports

# Budget management workflow  
def test_budget_workflow():
    # Create monthly food budget
    # Record food purchases
    # Verify budget tracking
    # Test budget limit alerts
```

## Mocking Strategy

### External Service Mocks

- **OpenAI API** - Mocked for unit tests to avoid API costs
- **Firefly III** - Real API used for integration tests
- **Database** - Real PostgreSQL for integration, mocked for unit tests

### Mock Patterns

```python
# AI service mocking
@patch('openai.chat.completions.create')
def test_ai_categorization(mock_openai):
    mock_response = Mock()
    mock_response.choices[0].message.content = "Food & Drinks"
    mock_openai.return_value = mock_response
    
    # Test AI categorization logic
```

## Performance Testing

### Metrics Tracked

- **AI Response Time** - Categorization latency
- **Webhook Processing Time** - End-to-end processing
- **Database Performance** - Query execution time
- **API Response Times** - Firefly III API performance

### Performance Benchmarks

- AI categorization: < 2 seconds
- Webhook processing: < 5 seconds  
- Database queries: < 100ms
- API calls: < 1 second

## Troubleshooting

### Common Issues

1. **Service Not Running**
   ```bash
   python run_tests.py check
   docker compose up -d
   ```

2. **Database Connection Failed**
   ```bash
   docker compose logs ai-db
   docker compose restart ai-db
   ```

3. **API Authentication Failed**
   - Check `FIREFLY_TOKEN` in `.env`
   - Verify token permissions in Firefly UI

4. **OpenAI API Errors**
   - Check `OPENAI_API_KEY` in `.env`
   - Verify OpenAI account has credits

### Debug Mode

```bash
# Verbose test output
pytest -v -s

# Debug specific test
pytest tests/test_ai_service.py::test_ai_categorization -v -s

# Show print statements
pytest --capture=no
```

## Continuous Integration

### GitHub Actions Integration

Tests can be integrated with CI/CD:

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker compose up -d
      - name: Run tests
        run: python run_tests.py all
```

### Test Reports

- **Allure Reports** - Generated in `allure-results/`
- **Coverage Reports** - Generated in `htmlcov/`
- **Pytest HTML** - Custom HTML reports

## Contributing

### Adding New Tests

1. Follow existing test patterns and naming
2. Add appropriate pytest markers
3. Include business workflow validation
4. Add mocks for external services
5. Update this README if needed

### Test Guidelines

- **Business-focused** - Test real user workflows
- **Isolated** - Use fixtures and cleanup
- **Documented** - Clear test descriptions
- **Reliable** - Deterministic and repeatable
- **Fast** - Unit tests < 1s, integration tests < 30s

## License

This test suite is part of the Firefly III AI Integration project.