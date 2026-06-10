# 🚀 QUICK START - FIX THE DEPENDENCY ERROR

## ✅ SOLUTION 1: INSTALL WITHOUT ML (FASTEST - 2 MINUTES)

This installs ALL 10 security fixes WITHOUT the ML layer (BERT).
L1 (Vigil) and L3 (Custom) detection still work perfectly.

### Step 1: Run Automated Installer
```bash
cd d:\projects\prompt-wall
python install_security_fixes.py
# Choose option 1: Security Fixes Only
```

### OR Manual Installation:
```bash
pip install -r agent-shield/requirements-no-ml.txt
```

---

## ✅ SOLUTION 2: FIX TORCH VERSION (IF YOU NEED ML)

The error happens because torch 2.1.0 doesn't exist for your system.

### For Windows:
```bash
# Install torch with CPU support
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Then install rest without torch
pip install fastapi uvicorn pydantic slowapi cryptography keyring httpx requests azure-storage-blob azure-data-tables pyyaml pytest transformers onnxruntime datasets pandas
```

### For Linux/Mac:
```bash
# Install torch separately
pip install torch

# Then install rest
pip install -r agent-shield/requirements.txt --no-deps torch
```

---

## 📋 AFTER INSTALLATION - TEST IT

### 1. Verify Critical Packages
```bash
python -c "from cryptography.fernet import Fernet; import keyring; print('✅ Security packages OK')"
```

### 2. Generate Encryption Key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
**SAVE THIS OUTPUT!**

### 3. Set Environment Variables
```bash
# Windows PowerShell
$env:AGENT_SHIELD_API_KEY="your_existing_key"
$env:LOG_ENCRYPTION_KEY="key_from_step_2"
$env:FORCE_HTTPS="false"  # for local testing

# Linux/Mac
export AGENT_SHIELD_API_KEY=your_existing_key
export LOG_ENCRYPTION_KEY=key_from_step_2
export FORCE_HTTPS=false  # for local testing
```

### 4. Test the API
```bash
cd agent-shield
python app.py
```

You should see:
```
✓ L1: Vigil Scanner loaded
⚠ L2 BERT Classifier unavailable: No module named 'torch'
⚠ Running without ML detection layer (L1 and L3 still active)
✓ L3: Custom Rules Engine loaded
══════ Security Engine Ready: L1 (Vigil) + L3 (Custom) - L2 disabled ══════
```

### 5. Test Endpoint (In Another Terminal)
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## ✅ WHAT'S WORKING

After installation, ALL 10 security fixes are active:

1. ✅ Gradio UI Authentication - Works
2. ✅ OAuth HTTPS + Cookies - Works
3. ✅ L2 Error Handling - Works (graceful degradation)
4. ✅ Metrics Authentication - Works
5. ✅ CSRF Protection - Works
6. ✅ Model Checksums - Works (when torch installed)
7. ✅ Dependency Pinning - Works
8. ✅ Secrets Manager - Works
9. ✅ OS Keyring - Works
10. ✅ Log Encryption - Works

---

## 🎯 WHICH OPTION TO CHOOSE?

### Choose Option 1 (No ML) if:
- ✅ You want to TEST the security fixes quickly
- ✅ You don't need BERT/ML detection
- ✅ L1 (Vigil) + L3 (Custom) is enough for you
- ✅ You're having dependency issues
- ✅ You want to deploy ASAP

### Choose Option 2 (With ML) if:
- ✅ You need maximum detection accuracy
- ✅ You have time for large downloads (~2GB)
- ✅ You can troubleshoot torch/ML issues

---

## 🆘 STILL GETTING ERRORS?

### Error: "No module named cryptography"
```bash
pip install cryptography keyring
```

### Error: "Could not find torch"
```bash
# Skip torch, use Option 1
pip install -r agent-shield/requirements-no-ml.txt
```

### Error: "Permission denied"
```bash
# Use virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r agent-shield/requirements-no-ml.txt
```

---

## 📞 NEED HELP?

1. Run automated installer: `python install_security_fixes.py`
2. Choose Option 1 (fastest, no ML)
3. If still fails, manually install:
   ```bash
   pip install fastapi uvicorn cryptography keyring
   ```

---

## ✅ SUCCESS CHECKLIST

- [ ] Installation completed without errors
- [ ] `python -c "import cryptography, keyring"` works
- [ ] Encryption key generated and saved
- [ ] Environment variables set
- [ ] `python app.py` starts successfully
- [ ] `curl http://localhost:8000/health` returns OK

**Once all checked, your security fixes are ACTIVE! 🎉**
