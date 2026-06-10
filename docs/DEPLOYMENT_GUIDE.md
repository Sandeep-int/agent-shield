# QUICK DEPLOYMENT GUIDE - SECURITY FIXES
## Agent Shield - Production Deployment

---

## 🚀 IMMEDIATE ACTION REQUIRED

### 1. Install New Dependencies
```bash
cd agent-shield
pip install -r requirements.txt
```

**New dependencies added:**
- `cryptography==43.0.3` (log encryption)
- `keyring==25.5.0` (secure token storage)

---

### 2. Generate Encryption Keys

#### Log Encryption Key
```bash
python -c "from cryptography.fernet import Fernet; print('LOG_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```
**⚠️ SAVE THIS OUTPUT - YOU'LL NEED IT TO DECRYPT LOGS!**

---

### 3. Calculate Model Checksums
```bash
cd agent-shield/models
sha256sum model.onnx
sha256sum model.onnx.data
```

**Save these hashes - you'll add them to environment variables.**

---

### 4. Configure Environment Variables

Create `.env` file:
```bash
# === REQUIRED ===
AGENT_SHIELD_API_KEY=your_api_key_here
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# === SECURITY (REQUIRED) ===
FORCE_HTTPS=true
LOG_ENCRYPTION_KEY=your_fernet_key_from_step_2

# === MODEL INTEGRITY (REQUIRED) ===
MODEL_ONNX_SHA256=hash_from_step_3
MODEL_ONNX_DATA_SHA256=hash_from_step_3

# === SECRETS MANAGEMENT (OPTIONAL - Choose one) ===
# Option A: Azure Key Vault
SECRET_BACKEND=azure
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/

# Option B: AWS Secrets Manager
# SECRET_BACKEND=aws
# AWS_REGION=us-east-1

# Option C: Environment Variables (default)
# SECRET_BACKEND=env

# === OAUTH (If using GitHub auth) ===
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

---

### 5. Migrate Secrets to Key Vault (OPTIONAL BUT RECOMMENDED)

#### Azure Key Vault
```bash
# Create Key Vault
az keyvault create --name agent-shield-vault --resource-group your-rg --location eastus

# Store secrets
az keyvault secret set --vault-name agent-shield-vault --name AGENT-SHIELD-API-KEY --value "your_key"
az keyvault secret set --vault-name agent-shield-vault --name AZURE-STORAGE-CONNECTION-STRING --value "your_connection"

# Update .env
export SECRET_BACKEND=azure
export AZURE_KEY_VAULT_URL=https://agent-shield-vault.vault.azure.net/
```

#### AWS Secrets Manager
```bash
# Create secrets
aws secretsmanager create-secret --name AGENT_SHIELD_API_KEY --secret-string "your_key" --region us-east-1
aws secretsmanager create-secret --name AZURE_STORAGE_CONNECTION_STRING --secret-string "your_connection" --region us-east-1

# Update .env
export SECRET_BACKEND=aws
export AWS_REGION=us-east-1
```

---

### 6. Test Locally
```bash
# Load environment
source .env  # or `set -a; source .env; set +a` on some shells

# Run tests
python -m pytest tests/

# Start API
cd agent-shield
python app.py
```

---

### 7. Verify Fixes

#### Test 1: UI Authentication
```bash
# WITHOUT API key - should fail
unset AGENT_SHIELD_API_KEY
python ui.py
# Enter a test prompt → Should see error about missing API key ✅

# WITH API key - should work
export AGENT_SHIELD_API_KEY=your_key
python ui.py
# Enter a test prompt → Should get response ✅
```

#### Test 2: Metrics Endpoint Authentication
```bash
# Without auth - should fail
curl http://localhost:8000/metrics
# Expected: 401 Unauthorized ✅

# With auth - should work
curl -H "X-API-Key: your_key" http://localhost:8000/metrics
# Expected: JSON response with metrics ✅
```

#### Test 3: Log Encryption
```bash
# Check if logs are encrypted
cat security_audit.log
# Expected: Binary/gibberish data, not readable text ✅
```

#### Test 4: Token Storage (CLI)
```bash
# Login via CLI
agent-shield auth
# Check where token is stored:

# macOS: Should be in Keychain
security find-generic-password -s agent-shield -a cli-token -w
# ✅ Token found in Keychain

# Windows: Should be in Credential Manager
# Open: Control Panel → Credential Manager → Windows Credentials
# ✅ Look for "agent-shield"

# Linux: Should be in Secret Service
secret-tool lookup service agent-shield username cli-token
# ✅ Token found
```

#### Test 5: Model Integrity
```bash
# Tamper with model (for testing)
echo "fake" >> agent-shield/models/model.onnx

# Start app
python app.py
# Expected: Checksum mismatch warning, re-downloads model ✅

# Restore model
git checkout agent-shield/models/model.onnx
```

---

### 8. Production Deployment

#### Docker
```bash
# Build with environment variables
docker build -t agent-shield:secure .

# Run with secrets
docker run -d \
  -e AGENT_SHIELD_API_KEY=your_key \
  -e FORCE_HTTPS=true \
  -e LOG_ENCRYPTION_KEY=your_fernet_key \
  -e MODEL_ONNX_SHA256=your_hash \
  -e MODEL_ONNX_DATA_SHA256=your_hash \
  -p 8000:8000 \
  agent-shield:secure
```

#### Azure App Service
```bash
# Set environment variables
az webapp config appsettings set --name agent-shield-app \
  --resource-group your-rg \
  --settings \
    AGENT_SHIELD_API_KEY=@Microsoft.KeyVault(...) \
    FORCE_HTTPS=true \
    LOG_ENCRYPTION_KEY=your_key \
    MODEL_ONNX_SHA256=your_hash \
    SECRET_BACKEND=azure \
    AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
```

#### AWS ECS/Fargate
```bash
# Store secrets in Secrets Manager (see step 5)

# Create task definition with environment variables:
{
  "containerDefinitions": [{
    "environment": [
      {"name": "FORCE_HTTPS", "value": "true"},
      {"name": "SECRET_BACKEND", "value": "aws"},
      {"name": "AWS_REGION", "value": "us-east-1"}
    ],
    "secrets": [
      {"name": "AGENT_SHIELD_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
    ]
  }]
}
```

---

## 🔒 SECURITY CHECKLIST

Before going to production, verify:

- [ ] All dependencies installed (`pip list | grep -E "cryptography|keyring"`)
- [ ] Environment variables configured (especially `FORCE_HTTPS=true`)
- [ ] Log encryption key generated and saved securely
- [ ] Model checksums calculated and configured
- [ ] Secrets migrated to Key Vault/Secrets Manager (recommended)
- [ ] OAuth HTTPS enforced (`FORCE_HTTPS=true`)
- [ ] Metrics endpoint requires authentication (test with `curl`)
- [ ] UI requires API key (test without key → should fail)
- [ ] Logs are encrypted (check `security_audit.log` is binary)
- [ ] CLI tokens stored in OS keyring (not plain text file)
- [ ] All tests pass (`pytest tests/`)

---

## 📋 ENVIRONMENT VARIABLES REFERENCE

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_SHIELD_API_KEY` | ✅ Yes | - | API authentication key |
| `AZURE_STORAGE_CONNECTION_STRING` | ✅ Yes | - | Azure Table Storage |
| `FORCE_HTTPS` | ✅ Yes | `true` | Enforce HTTPS for OAuth |
| `LOG_ENCRYPTION_KEY` | ✅ Yes | - | Fernet key for log encryption |
| `MODEL_ONNX_SHA256` | ✅ Yes | - | Model integrity checksum |
| `MODEL_ONNX_DATA_SHA256` | ✅ Yes | - | Model data checksum |
| `SECRET_BACKEND` | ⚪ Optional | `env` | `azure`, `aws`, or `env` |
| `AZURE_KEY_VAULT_URL` | ⚪ Optional | - | Azure Key Vault URL |
| `AWS_REGION` | ⚪ Optional | `us-east-1` | AWS region |
| `GITHUB_CLIENT_ID` | ⚪ Optional | - | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | ⚪ Optional | - | GitHub OAuth secret |

---

## 🆘 TROUBLESHOOTING

### Issue: "keyring library not installed"
```bash
pip install keyring==25.5.0
```

### Issue: "Checksum mismatch"
```bash
# Recalculate checksum
sha256sum agent-shield/models/model.onnx

# Update environment variable
export MODEL_ONNX_SHA256=new_hash_here
```

### Issue: "401 Unauthorized on /metrics"
```bash
# Make sure you're passing API key
curl -H "X-API-Key: your_key" http://localhost:8000/metrics
```

### Issue: "HTTPS required" error
```bash
# For local dev only, disable HTTPS check:
export FORCE_HTTPS=false

# For production, always use HTTPS!
```

### Issue: Logs not decrypting
```python
# Make sure you're using the SAME encryption key
from cryptography.fernet import Fernet

KEY = "your_original_key_from_step_2"  # ← MUST MATCH
cipher = Fernet(KEY.encode())

with open("security_audit.log", "rb") as f:
    for line in f:
        if line.strip():
            try:
                decrypted = cipher.decrypt(line.strip()).decode()
                print(decrypted)
            except Exception as e:
                print(f"Failed to decrypt line: {e}")
```

---

## 📞 SUPPORT

If you encounter issues:
1. Check environment variables: `env | grep AGENT_SHIELD`
2. Check logs: `tail -f security_audit.log` (encrypted)
3. Run tests: `pytest tests/ -v`
4. Verify dependencies: `pip list`

---

## ✅ SUCCESS CRITERIA

Your deployment is secure when:
- ✅ All 10 security fixes are active
- ✅ No critical vulnerabilities remain
- ✅ Tests pass with 100% success rate
- ✅ Logs are encrypted
- ✅ Tokens stored in OS keyring
- ✅ Metrics require authentication
- ✅ OAuth has CSRF protection
- ✅ Models verified with checksums

**You're now production-ready! 🚀**
