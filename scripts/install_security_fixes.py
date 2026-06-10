#!/usr/bin/env python3
"""
Agent Shield - Automated Installation Script
Installs security fixes with or without ML dependencies
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=False, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║      AGENT SHIELD - SECURITY FIXES INSTALLATION          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("Choose installation mode:")
    print("1. Security Fixes Only (Fastest, no ML)")
    print("2. Full Installation (Includes ML/BERT)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "3":
        print("Installation cancelled.")
        return
    
    # Upgrade pip first
    print("\n🔧 Upgrading pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    if choice == "1":
        # Security fixes only
        print("\n📦 Installing SECURITY FIXES ONLY (no ML dependencies)")
        print("This installs: cryptography, keyring, fastapi, azure, etc.")
        print("BERT/ML detection will be DISABLED (L1 and L3 still work)")
        
        requirements_file = "requirements-no-ml.txt"
        if not os.path.exists(requirements_file):
            print(f"❌ File not found: {requirements_file}")
            print("Creating it now...")
            with open(requirements_file, "w") as f:
                f.write("""# Security Fixes Only
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
""")
        
        success = run_command(
            f"{sys.executable} -m pip install -r {requirements_file}",
            "Installing security packages"
        )
        
        if success:
            print("\n" + "="*60)
            print("✅ SECURITY FIXES INSTALLED SUCCESSFULLY!")
            print("="*60)
            print("\n⚠️  NOTE: ML detection (BERT) is disabled")
            print("    L1 (Vigil) and L3 (Custom) layers are active")
            print("\n📋 Next steps:")
            print("1. Generate encryption key:")
            print("   python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
            print("\n2. Set environment variables:")
            print("   export AGENT_SHIELD_API_KEY=your_key")
            print("   export LOG_ENCRYPTION_KEY=key_from_step_1")
            print("\n3. Test:")
            print("   python app.py")
        
    elif choice == "2":
        # Full installation
        print("\n📦 Installing FULL STACK (with ML dependencies)")
        print("This may take several minutes...")
        print("⚠️  Warning: Torch is large (~2GB)")
        
        # Try main requirements first
        success = run_command(
            f"{sys.executable} -m pip install -r requirements.txt",
            "Installing all packages"
        )
        
        if not success:
            print("\n⚠️  Full installation failed. Trying fallback...")
            print("Installing in groups...")
            
            # Group 1: Core
            run_command(
                f"{sys.executable} -m pip install fastapi uvicorn pydantic slowapi",
                "Installing core API packages"
            )
            
            # Group 2: Security (CRITICAL)
            run_command(
                f"{sys.executable} -m pip install cryptography keyring",
                "Installing security packages"
            )
            
            # Group 3: Azure
            run_command(
                f"{sys.executable} -m pip install azure-storage-blob azure-data-tables",
                "Installing Azure packages"
            )
            
            # Group 4: HTTP
            run_command(
                f"{sys.executable} -m pip install httpx requests",
                "Installing HTTP packages"
            )
            
            # Group 5: ML (may fail)
            print("\n⚠️  Attempting ML packages (may fail on some systems)...")
            ml_success = run_command(
                f"{sys.executable} -m pip install torch transformers onnxruntime datasets",
                "Installing ML packages"
            )
            
            if not ml_success:
                print("\n⚠️  ML packages failed - continuing without BERT")
                print("    L1 and L3 layers will still work")
            
            # Group 6: Utils
            run_command(
                f"{sys.executable} -m pip install pyyaml pytest pandas",
                "Installing utilities"
            )
        
        print("\n" + "="*60)
        print("✅ INSTALLATION COMPLETE!")
        print("="*60)
    
    else:
        print("❌ Invalid choice")
        return
    
    # Final verification
    print("\n" + "="*60)
    print("🔍 VERIFYING CRITICAL PACKAGES")
    print("="*60)
    
    critical_packages = [
        ("cryptography", "Log encryption"),
        ("keyring", "Token storage"),
        ("fastapi", "API framework"),
    ]
    
    all_ok = True
    for package, purpose in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package:20s} - OK ({purpose})")
        except ImportError:
            print(f"❌ {package:20s} - MISSING ({purpose})")
            all_ok = False
    
    if all_ok:
        print("\n🎉 All critical packages installed successfully!")
        print("\n📋 NEXT STEPS:")
        print("="*60)
        print("1. Generate encryption key:")
        print("   python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        print("\n2. Set environment variables:")
        print("   export AGENT_SHIELD_API_KEY=your_key")
        print("   export LOG_ENCRYPTION_KEY=key_from_step_1")
        print("   export FORCE_HTTPS=true")
        print("\n3. Test the API:")
        print("   cd agent-shield")
        print("   python app.py")
        print("\n4. Verify fixes:")
        print("   curl -H 'X-API-Key: your_key' http://localhost:8000/health")
    else:
        print("\n❌ Some packages failed to install")
        print("Try: pip install -r requirements-no-ml.txt")

if __name__ == "__main__":
    main()
