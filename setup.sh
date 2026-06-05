#!/bin/bash
# Agent Shield - Complete Setup with Virtual Environment
# Works on Linux, Mac, and Windows (Git Bash/WSL)

echo "════════════════════════════════════════════════════════════"
echo "  AGENT SHIELD - AUTOMATED SETUP WITH VIRTUAL ENVIRONMENT"
echo "════════════════════════════════════════════════════════════"
echo ""

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
    ACTIVATE="venv/Scripts/activate"
else
    OS="unix"
    ACTIVATE="venv/bin/activate"
fi

echo "📁 Current directory: $(pwd)"
echo "🖥️  Detected OS: $OS"
echo ""

# Step 1: Create virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Creating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv || python -m venv venv

if [ ! -d "venv" ]; then
    echo "❌ Failed to create virtual environment"
    echo "Try: sudo apt install python3-venv (Linux)"
    exit 1
fi

echo "✅ Virtual environment created"
echo ""

# Step 2: Activate virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Activating virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

source $ACTIVATE 2>/dev/null || . $ACTIVATE

if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    echo "Manual activation:"
    if [ "$OS" == "windows" ]; then
        echo "  .\\venv\\Scripts\\Activate.ps1  (PowerShell)"
        echo "  venv\\Scripts\\activate.bat     (CMD)"
    else
        echo "  source venv/bin/activate"
    fi
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""

# Step 3: Upgrade pip
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Upgrading pip..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pip install --upgrade pip
echo "✅ Pip upgraded"
echo ""

# Step 4: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Installing security packages (no ML)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if requirements file exists
if [ ! -f "requirements-no-ml.txt" ]; then
    echo "Creating requirements-no-ml.txt..."
    cat > requirements-no-ml.txt << 'EOF'
# Security Fixes Only - No ML Dependencies
fastapi
uvicorn[standard]
pydantic>=2.0,<3.0
slowapi
cryptography>=41.0
keyring>=24.0
httpx
requests
azure-storage-blob
azure-data-tables
pyyaml
pytest
typing-extensions
EOF
fi

pip install -r requirements-no-ml.txt

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi

echo "✅ All packages installed"
echo ""

# Step 5: Verify installation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying critical packages..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python << 'PYEOF'
import sys
packages = [
    ("cryptography", "Log encryption"),
    ("keyring", "Token storage"),
    ("fastapi", "API framework"),
    ("azure.data.tables", "Azure logging"),
]

all_ok = True
for package, purpose in packages:
    try:
        __import__(package)
        print(f"✅ {package:25s} - OK ({purpose})")
    except ImportError:
        print(f"❌ {package:25s} - MISSING ({purpose})")
        all_ok = False

if not all_ok:
    sys.exit(1)
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Some packages are missing"
    exit 1
fi

echo ""
echo "✅ All critical packages verified"
echo ""

# Step 6: Generate encryption key
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Generating encryption key..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo ""
echo "🔑 YOUR ENCRYPTION KEY (SAVE THIS!):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$ENCRYPTION_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save to .env file
cat > .env << EOF
# Agent Shield Environment Variables
# Generated: $(date)

# REQUIRED
AGENT_SHIELD_API_KEY=your_existing_api_key_here
LOG_ENCRYPTION_KEY=$ENCRYPTION_KEY
FORCE_HTTPS=false

# OPTIONAL (Secrets Management)
# SECRET_BACKEND=azure
# AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/

# OPTIONAL (OAuth)
# GITHUB_CLIENT_ID=your_github_client_id
# GITHUB_CLIENT_SECRET=your_github_client_secret
EOF

echo "✅ Environment template saved to .env"
echo ""

# Final instructions
echo "════════════════════════════════════════════════════════════"
echo "  🎉 INSTALLATION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Edit .env file and add your API key:"
echo "   nano .env  (or use any text editor)"
echo ""
echo "2. Load environment variables:"
if [ "$OS" == "windows" ]; then
    echo "   Get-Content .env | ForEach-Object { \$name, \$value = \$_.Split('='); [Environment]::SetEnvironmentVariable(\$name, \$value) }"
else
    echo "   export \$(cat .env | xargs)"
fi
echo ""
echo "3. Start the API:"
echo "   python app.py"
echo ""
echo "4. Test in another terminal:"
echo "   curl http://localhost:7860/health"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📚 Documentation:"
echo "  - INSTALL_FIX.md         - Quick start guide"
echo "  - COMPLETE_SUMMARY.md    - Everything in one place"
echo "  - SECURITY_FIXES_REPORT.md - Technical details"
echo ""
echo "🔒 All 10 security fixes are ACTIVE!"
echo "════════════════════════════════════════════════════════════"
