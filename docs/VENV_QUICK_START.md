# 🚀 QUICK START - FIXED FOR EXTERNALLY-MANAGED ERROR

---

## ✅ **THE ERROR YOU'RE SEEING**

```
Error: externally-managed-environment
```

This is Python 3.11+ protecting your system. **Easy fix: Use virtual environment!**

---

## 🎯 **SOLUTION: AUTOMATED SETUP (1 COMMAND)**

### **Windows (PowerShell):**
```powershell
cd d:\projects\prompt-wall\agent-shield
.\setup.ps1
```

### **Linux/Mac:**
```bash
cd /path/to/prompt-wall/agent-shield
chmod +x setup.sh
./setup.sh
```

**✅ This automatically:**
- Creates virtual environment
- Installs all dependencies
- Generates encryption key
- Creates .env file
- Verifies everything works

**⏱️ Takes 3 minutes!**

---

## 📋 **MANUAL SETUP (IF AUTOMATED FAILS)**

### **Step 1: Create Virtual Environment (30 seconds)**

```bash
cd d:\projects\prompt-wall\agent-shield

# Create venv
python3 -m venv venv
# OR
python -m venv venv
```

---

### **Step 2: Activate Virtual Environment (10 seconds)**

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**✅ You'll see `(venv)` in your prompt:**
```
(venv) user@machine:~/agent-shield$
```

---

### **Step 3: Install Dependencies (2 minutes)**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install security packages (no ML)
pip install -r requirements-no-ml.txt
```

**✅ This installs:**
- ✅ `cryptography` (log encryption)
- ✅ `keyring` (token storage)
- ✅ `fastapi` (API framework)
- ✅ `azure-*` (logging & storage)
- ✅ All other security fixes

---

### **Step 4: Generate Encryption Key (10 seconds)**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**📝 COPY THIS OUTPUT!** Example:
```
3x4mpl3K3yH3r3Pl34s3S4v3Th1s==
```

---

### **Step 5: Set Environment Variables (30 seconds)**

**Linux/Mac:**
```bash
export AGENT_SHIELD_API_KEY=your_existing_api_key
export LOG_ENCRYPTION_KEY=paste_key_from_step_4
export FORCE_HTTPS=false
```

**Windows (PowerShell):**
```powershell
$env:AGENT_SHIELD_API_KEY="your_existing_api_key"
$env:LOG_ENCRYPTION_KEY="paste_key_from_step_4"
$env:FORCE_HTTPS="false"
```

---

### **Step 6: Test It! (30 seconds)**

```bash
python app.py
```

**✅ Expected Output:**
```
✓ L1: Vigil Scanner loaded
✓ L3: Custom Rules Engine loaded
══════ Security Engine Ready: L1 (Vigil) + L3 (Custom) - L2 disabled ══════
INFO:     Uvicorn running on http://0.0.0.0:7860
```

**Test in another terminal:**
```bash
curl http://localhost:7860/health
```

Expected: `{"status":"ok"}` ✅

---

## 🎉 **SUCCESS! YOU'RE DONE!**

All 10 security fixes are now active:
- ✅ UI Authentication
- ✅ HTTPS Enforcement
- ✅ CSRF Protection
- ✅ Metrics Auth
- ✅ Log Encryption
- ✅ Token Security (OS Keyring)
- ✅ Fail-Safe Blocking
- ✅ Model Integrity
- ✅ Secrets Management
- ✅ Dependency Locking

---

## 🆘 **TROUBLESHOOTING**

### **"python3: command not found"**
```bash
python -m venv venv
```

### **"Activate.ps1 cannot be loaded" (Windows)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### **"No module named 'venv'"**
```bash
# Linux
sudo apt install python3-venv

# Mac
brew install python3
```

### **Virtual environment won't activate**
```bash
# Delete and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

---

## 📋 **VIRTUAL ENVIRONMENT CHEAT SHEET**

### **Activate:**
```bash
# Linux/Mac
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat
```

### **Deactivate:**
```bash
deactivate
```

### **Check if active:**
```bash
which python  # Should show path inside venv
echo $VIRTUAL_ENV  # Should show venv path
```

### **Install packages:**
```bash
# Always activate first!
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1

# Then install
pip install package-name
```

---

## 🔄 **DAILY WORKFLOW**

Every time you work on the project:

```bash
# 1. Navigate to project
cd d:\projects\prompt-wall\agent-shield

# 2. Activate venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# 3. Work normally
python app.py
pip install new-package
pytest tests/

# 4. Deactivate when done
deactivate
```

---

## 📁 **WHAT GETS CREATED**

```
agent-shield/
├── venv/                  ← Virtual environment (don't commit!)
│   ├── bin/              ← Python & pip (Linux/Mac)
│   ├── Scripts/          ← Python & pip (Windows)
│   └── lib/              ← Installed packages
├── .env                  ← Your environment variables
├── requirements-no-ml.txt
└── app.py
```

**Add to `.gitignore`:**
```
venv/
.env
*.pyc
__pycache__/
```

---

## ✅ **VERIFY EVERYTHING WORKS**

Run these checks:

```bash
# 1. Activate venv
source venv/bin/activate

# 2. Check packages
python << EOF
import cryptography
import keyring
import fastapi
print("✅ All critical packages OK")
EOF

# 3. Check environment
echo $VIRTUAL_ENV  # Should show venv path

# 4. Start app
python app.py

# 5. Test endpoint (in another terminal)
curl http://localhost:7860/health
```

---

## 🎯 **SUMMARY**

### **The Problem:**
```
Error: externally-managed-environment
```

### **The Solution:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-no-ml.txt
```

### **Time to Fix:** 3 minutes
### **Result:** ✅ All 10 security fixes working!

---

## 🚀 **NEXT STEPS AFTER INSTALLATION**

1. ✅ Virtual environment created and activated
2. ✅ Dependencies installed
3. ✅ Encryption key generated
4. ✅ Environment variables set
5. ✅ API tested and working

**NOW:** Deploy to production! See `DEPLOYMENT_GUIDE.md`

---

**Your Agent Shield is secure and ready! 🛡️✨**
