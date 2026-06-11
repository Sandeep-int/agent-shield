#!/bin/bash

echo "=========================================="
echo "Fixing Dependencies and Running Tests"
echo "=========================================="

# Install/upgrade dependencies
echo ""
echo "Step 1: Installing/upgrading dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install requirements"
    exit 1
fi

echo ""
echo "Step 2: Verifying critical imports..."
python -c "from transformers import DistilBertTokenizer; print('✓ transformers OK')"
python -c "from fastapi import FastAPI; print('✓ fastapi OK')"
python -c "from detectors.l3_custom import CustomL3; print('✓ l3_custom OK')"

echo ""
echo "Step 3: Running safe context tests..."
python tests/run_safe_context_tests.py

echo ""
echo "Step 4: Running pytest..."
python -m pytest tests/test_l3_safe_context.py tests/test_l3_toxic_wordboundary.py -v --tb=short

echo ""
echo "=========================================="
echo "COMPLETE"
echo "=========================================="
