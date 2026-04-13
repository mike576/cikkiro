#!/bin/bash

# Test runner script for deployed application

echo "Installing test dependencies..."
pip install -q requests 2>/dev/null || true

echo ""
echo "========================================================================"
echo "RUNNING DEPLOYMENT TESTS"
echo "========================================================================"
echo ""

cd "$(dirname "$0")"

python3 tests/test_deployment.py

exit_code=$?

echo ""
echo "========================================================================"
if [ $exit_code -eq 0 ]; then
    echo "✓ All tests completed successfully"
else
    echo "✗ Some tests failed - see details above"
fi
echo "========================================================================"
echo ""

exit $exit_code
