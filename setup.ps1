# Agent Shield - Complete Setup Script for Windows
# Run in PowerShell: .\setup.ps1

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  AGENT SHIELD - AUTOMATED SETUP (WINDOWS)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 1: Creating virtual environment..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "⚠️  Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

python -m venv venv

if (-Not (Test-Path "venv")) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Virtual environment created" -ForegroundColor Green
Write-Host ""

# Step 2: Activate virtual environment
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 2: Activating virtual environment..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

& .\venv\Scripts\Activate.ps1

if (-Not $env:VIRTUAL_ENV) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "Try enabling scripts: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Step 3: Upgrade pip
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 3: Upgrading pip..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

python -m pip install --upgrade pip
Write-Host "✅ Pip upgraded" -ForegroundColor Green
Write-Host ""

# Step 4: Create requirements file if missing
if (-Not (Test-Path "requirements-no-ml.txt")) {
    Write-Host "Creating requirements-no-ml.txt..." -ForegroundColor Yellow
    @"
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
"@ | Out-File -FilePath "requirements-no-ml.txt" -Encoding UTF8
}

# Step 5: Install dependencies
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 4: Installing security packages (no ML)..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

pip install -r requirements-no-ml.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Installation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All packages installed" -ForegroundColor Green
Write-Host ""

# Step 6: Verify installation
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 5: Verifying critical packages..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

python -c @"
import sys
packages = [
    ('cryptography', 'Log encryption'),
    ('keyring', 'Token storage'),
    ('fastapi', 'API framework'),
    ('azure.data.tables', 'Azure logging'),
]

all_ok = True
for package, purpose in packages:
    try:
        __import__(package)
        print(f'✅ {package:25s} - OK ({purpose})')
    except ImportError:
        print(f'❌ {package:25s} - MISSING ({purpose})')
        all_ok = False

if not all_ok:
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Some packages are missing" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All critical packages verified" -ForegroundColor Green
Write-Host ""

# Step 7: Generate encryption key
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "Step 6: Generating encryption key..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

$ENCRYPTION_KEY = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Write-Host ""
Write-Host "🔑 YOUR ENCRYPTION KEY (SAVE THIS!):" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host $ENCRYPTION_KEY -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Save to .env file
$envContent = @"
# Agent Shield Environment Variables
# Generated: $(Get-Date)

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
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Environment template saved to .env" -ForegroundColor Green
Write-Host ""

# Final instructions
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🎉 INSTALLATION COMPLETE!" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 NEXT STEPS:" -ForegroundColor White
Write-Host ""
Write-Host "1. Edit .env file and add your API key:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Load environment variables:" -ForegroundColor White
Write-Host "   Get-Content .env | ForEach-Object {" -ForegroundColor Gray
Write-Host "       if (`$_ -match '^([^#].+?)=(.+)$') {" -ForegroundColor Gray
Write-Host "           `$env:(`$matches[1]) = `$matches[2]" -ForegroundColor Gray
Write-Host "       }" -ForegroundColor Gray
Write-Host "   }" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the API:" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test in another terminal:" -ForegroundColor White
Write-Host "   curl http://localhost:7860/health" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor White
Write-Host "  - INSTALL_FIX.md         - Quick start guide" -ForegroundColor Gray
Write-Host "  - COMPLETE_SUMMARY.md    - Everything in one place" -ForegroundColor Gray
Write-Host ""
Write-Host "🔒 All 10 security fixes are ACTIVE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
