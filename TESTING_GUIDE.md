# Testing Guide for పద్యార్చన (Padyarchana)

## Overview

This project includes a comprehensive test suite with unit tests, API tests, and integration tests to ensure code quality and reliability.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_models.py           # Unit tests for database models
├── test_api/
│   ├── test_poems.py        # API tests for poem endpoints
│   ├── test_poets.py        # API tests for poet endpoints
│   └── test_search.py       # API tests for search endpoints
└── test_integration.py      # End-to-end integration tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::test_create_poet

# Run using the test script
./scripts/run_tests.sh
```

### Using the Test Script

The project includes a convenient test runner script:

```bash
./scripts/run_tests.sh
```

This script will:
- Activate the virtual environment
- Run all tests with verbose output
- Generate coverage reports (HTML and terminal)
- Display a summary of results

## Test Coverage

### Current Coverage

The test suite covers:

#### Unit Tests (test_models.py)
- ✅ Poet model creation and validation
- ✅ Meter model creation and validation
- ✅ Poem model with relationships
- ✅ Word and PoemWord relationships
- ✅ Sandhi model creation
- ✅ Samasa model creation
- ✅ Gana model creation
- ✅ Yati model creation
- ✅ Prasa model creation
- ✅ Model repr methods
- ✅ Timestamp tracking

#### API Tests (test_api/)
**Poems API (test_poems.py)**
- ✅ GET /api/poems (list all)
- ✅ GET /api/poems/{id} (get one)
- ✅ POST /api/poems (create)
- ✅ PUT /api/poems/{id} (update)
- ✅ DELETE /api/poems/{id} (delete)
- ✅ Pagination
- ✅ Error handling (404s)

**Poets API (test_poets.py)**
- ✅ GET /api/poets (list all)
- ✅ GET /api/poets/{id} (get one)
- ✅ POST /api/poets (create)
- ✅ PUT /api/poets/{id} (update)
- ✅ DELETE /api/poets/{id} (delete)
- ✅ Error handling

**Search API (test_search.py)**
- ✅ Text search
- ✅ Filter by poet
- ✅ Filter by meter
- ✅ Filter by literary form
- ✅ Combined filters
- ✅ Pagination
- ✅ Autocomplete functionality
- ✅ No results handling

#### Integration Tests (test_integration.py)
- ✅ Complete poem workflow (create poet, meter, poem)
- ✅ Search workflow with multiple poems
- ✅ Update and delete workflow
- ✅ Autocomplete workflow
- ✅ Health check
- ✅ Pagination across multiple pages

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

### Database Fixtures
- `test_engine` - Creates an in-memory SQLite database for testing
- `test_session` - Provides a database session for tests

### Data Fixtures
- `sample_poet` - Creates a test poet (Vemana)
- `sample_meter` - Creates a test meter (Aata Veladi)
- `sample_poem` - Creates a test poem with relationships
- `multiple_poems` - Creates 5 test poems for pagination/search tests

### Client Fixture
- `client` - Provides an async HTTP client for API testing

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.asyncio
async def test_new_feature(test_session):
    """Test description."""
    # Arrange
    entity = MyModel(field="value")
    test_session.add(entity)
    await test_session.commit()

    # Act
    await test_session.refresh(entity)

    # Assert
    assert entity.id is not None
    assert entity.field == "value"
```

### API Test Example

```python
@pytest.mark.asyncio
async def test_new_endpoint(client: AsyncClient):
    """Test description."""
    # Arrange
    data = {"key": "value"}

    # Act
    response = await client.post("/api/endpoint", json=data)

    # Assert
    assert response.status_code == 200
    assert response.json()["key"] == "value"
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_complete_workflow(client: AsyncClient):
    """Test description."""
    # Create
    create_response = await client.post("/api/resource", json={...})
    resource_id = create_response.json()["id"]

    # Read
    get_response = await client.get(f"/api/resource/{resource_id}")
    assert get_response.status_code == 200

    # Update
    update_response = await client.put(f"/api/resource/{resource_id}", json={...})
    assert update_response.status_code == 200

    # Delete
    delete_response = await client.delete(f"/api/resource/{resource_id}")
    assert delete_response.status_code == 204
```

## Coverage Goals

Current coverage targets:
- **Overall**: >80%
- **Models**: >90%
- **API Endpoints**: >85%
- **Business Logic**: >80%

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html # Windows
```

## Continuous Integration

For CI/CD integration, add to your workflow:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Best Practices

### 1. Test Naming
- Use descriptive names: `test_<what>_<condition>_<expected>`
- Example: `test_create_poem_with_invalid_data_returns_422`

### 2. AAA Pattern
- **Arrange**: Set up test data
- **Act**: Execute the code being tested
- **Assert**: Verify the results

### 3. Test Independence
- Each test should be independent
- Use fixtures for setup
- Don't rely on test execution order

### 4. Async Testing
- Always use `@pytest.mark.asyncio` for async tests
- Use `await` for async operations

### 5. Error Testing
- Test both success and failure cases
- Verify error messages and status codes

## Troubleshooting

### Tests Not Running
```bash
# Ensure pytest is installed
pip install pytest pytest-asyncio pytest-cov

# Ensure in virtual environment
source venv/bin/activate
```

### Database Errors
```bash
# Tests use in-memory database
# Each test gets a fresh database
# Check conftest.py for fixture configuration
```

### Import Errors
```bash
# Ensure project root is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async Errors
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check for @pytest.mark.asyncio decorator
```

## Test Metrics

Run tests and get metrics:

```bash
# Test count
pytest --collect-only

# Test duration
pytest --durations=10

# Failed tests only
pytest --lf

# Specific markers
pytest -m "unit"  # If markers are defined
```

## Adding New Test Categories

To add a new test category:

1. Create new test file in appropriate directory
2. Add fixtures to conftest.py if needed
3. Follow existing naming conventions
4. Update this guide with new tests

## Pre-commit Testing

Recommended: Run tests before committing

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
pytest tests/ -x
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Test Database

Tests use an in-memory SQLite database:
- Fresh database for each test
- No persistence between tests
- Fast execution
- No cleanup needed

## Summary

The Padyarchana test suite provides:
- ✅ Comprehensive coverage of all major features
- ✅ Fast execution (in-memory database)
- ✅ Easy to run and extend
- ✅ Clear separation of concerns
- ✅ Proper async/await handling
- ✅ Isolated tests (no side effects)

---

**Happy Testing! 🧪**

Ensuring code quality for Telugu literary heritage preservation.
