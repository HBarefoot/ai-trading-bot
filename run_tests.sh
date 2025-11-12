#!/bin/bash

# Test runner script for AI Trading Bot

echo "🧪 Running AI Trading Bot Test Suite"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest is not installed. Run: pip install pytest pytest-cov${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️ Virtual environment not activated. Activate with: source venv/bin/activate${NC}"
fi

# Run different test suites based on argument
case "$1" in
    "unit")
        echo "🔬 Running Unit Tests"
        pytest tests/ -m "not integration and not slow" -v
        ;;
    "integration")
        echo "🔗 Running Integration Tests"
        pytest tests/ -m integration -v
        ;;
    "ml")
        echo "🤖 Running ML Tests"
        pytest tests/ -m ml -v
        ;;
    "slow")
        echo "⏳ Running Slow Tests"
        pytest tests/ -m slow -v
        ;;
    "all")
        echo "🧪 Running All Tests"
        pytest tests/ -v
        ;;
    "coverage")
        echo "📊 Running Tests with Coverage"
        pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}📈 Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo "⚡ Running Quick Tests (no slow, no external)"
        pytest tests/ -m "not slow and not external" -x
        ;;
    *)
        echo "Usage: $0 {unit|integration|ml|slow|all|coverage|quick}"
        echo ""
        echo "Test categories:"
        echo "  unit        - Unit tests only"
        echo "  integration - Integration tests"
        echo "  ml          - Machine learning tests"
        echo "  slow        - Slow tests"
        echo "  all         - All tests"
        echo "  coverage    - Tests with coverage report"
        echo "  quick       - Quick tests (excludes slow/external)"
        exit 1
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi