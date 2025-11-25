#!/bin/bash
# Test runner script for Padyarchana

echo "================================================"
echo "  పద్యార్చన (Padyarchana) - Test Runner"
echo "================================================"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🧪 Running tests..."
echo ""

# Run tests with coverage
pytest tests/ \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short

TEST_EXIT_CODE=$?

echo ""
echo "================================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
else
    echo "❌ Some tests failed. Please review the output above."
fi

echo "================================================"

exit $TEST_EXIT_CODE
