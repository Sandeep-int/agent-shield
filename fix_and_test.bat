@echo off
echo ==========================================
echo Fixing Dependencies and Running Tests
echo ==========================================

echo.
echo Step 1: Installing/upgrading dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    exit /b 1
)

echo.
echo Step 2: Verifying critical imports...
python -c "from transformers import DistilBertTokenizer; print('✓ transformers OK')"
python -c "from fastapi import FastAPI; print('✓ fastapi OK')"
python -c "from detectors.l3_custom import CustomL3; print('✓ l3_custom OK')"

echo.
echo Step 3: Running safe context tests...
python tests\run_safe_context_tests.py

echo.
echo Step 4: Testing specific failures...
python tests\test_specific_failures.py

echo.
echo ==========================================
echo COMPLETE
echo ==========================================
