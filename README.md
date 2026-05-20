# Agent Shield: Hybrid Web Application Firewall & Prompt Injection Guard

[![Application Runtime](https://img.shields.io/badge/HF%20Spaces-Active-blue?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/Sandeep120205/agent-shield)
[![API Status](https://img.shields.io/badge/API-Live-success?style=flat-square)](https://Sandeep120205-agent-shield.hf.space)

Agent Shield is a multi-layered security engine built to stop malicious inputs, code injections, and AI prompt hijacking before they reach backend business applications. 

By combining rapid regex rules with a deep learning classifier, Agent Shield provides high-performance protection without slowing down application logic.

---

## 🛡️ Multi-Layered Defense Architecture

Instead of relying on a single security check, Agent Shield drops inputs through a four-stage waterfall system:

Incoming Payload
│
▼
┌─────────────────────────────────────────┐
│ Layer 0: Normalization & Cleaning       │ -> Decodes URLs and neutralizes hidden Unicode tricks
└────────────────────┬────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ Layer 1: High-Speed Signature Filter    │ -> Instantly drops known exploits via regex (4.5ms)
└────────────────────┬────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ Layer 2: Machine Learning Classifier    │ -> DistilBERT model catches hidden semantic anomalies
└────────────────────┬────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│ Layer 3: Contextual Policy & PII Guard  │ -> Blocks data leaks and checks specific format rules
└─────────────────────────────────────────┘


### Key Engineering Features
* **Bypass Elimination:** Mitigates complex logical statements (like `admin' OR '1'='1`) by using flexible boundaries instead of static keywords.
* **Fail-Secure Code:** Built with a strict containment policy. If any security module hits a runtime error, the app automatically blocks the request (`HTTP 500`) to protect the system.
* **Dynamic Path Management:** Uses absolute root-path calculation routines so configuration rules load accurately regardless of where the application container boots from.

---

## ⚡ Technical Stack

* **Web Framework:** Python 3.14, FastAPI, Pydantic v2
* **AI & Machine Learning:** PyTorch, Hugging Face Transformers (DistilBERT Classifier)
* **Security & Ops:** Docker, SlowAPI (Rate-Limiter), GitHub Actions

---

## 🚀 Getting Started (Local Setup)

### 1. Installation
Clone the repository and set up a fresh Python virtual environment:
```bash
git clone [https://github.com/Sandeep-int/agent-shield.git](https://github.com/Sandeep-int/agent-shield.git)
cd agent-shield
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
2. Launching the API Server
Run the application from the root project directory using Uvicorn:

Bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
🧪 Testing the API
You can test the validation speed and defense layers using a simple terminal curl request:

Bash
curl -X POST "[http://127.0.0.1:8000/v1/check](http://127.0.0.1:8000/v1/check)" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"admin' OR '1'='1\"}"
Expected Interception Response:
JSON
{
  "verdict": "BLOCK",
  "confidence": 0.99,
  "layer_hit": "L1_VIGIL_SIGNATURE",
  "latency_ms": 4.53,
  "details": {
    "hits": [
      {
        "name": "sql_operator_bypass",
        "severity": "CRITICAL"
      }
    ]
  }
}
📈 Current Project Roadmap
Phase 2 Pipeline (Next Step): Automate synthetic attack payload data harvesting using automated security frameworks to build a training log bank of 2,500+ verified sample vectors.

Model Retraining: Retrain the core DistilBERT engine to target an accuracy threshold of 95%+ with a false-positive rate under 2%.


---

### Syncing the Code Documentation

Once you have replaced the contents of your `README.md` file with the markdown block above, push it out to your remote repositories to update your profile presentation:

```bash
git add README.md
git commit -m "docs: refresh readme design to show hybrid defense layers and 4.5ms latency benchmarks"
git push origin main
git push hf main