---
title: Agent Shield
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
---

# Agent Shield: protects your AI

[![Application Runtime](https://img.shields.io/badge/HF%20Spaces-Active-blue?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/Sandeep120205/agent-shield)
[![API Status](https://img.shields.io/badge/API-Live-success?style=flat-square)](https://Sandeep120205-agent-shield.hf.space)

Agent Shield is an advanced, production-hardened security engine built to stop malicious inputs, code injections, and AI prompt hijacking before they reach backend applications.

---

## 🛡️ Multi-Layered Defense Architecture

Instead of relying on a single checkpoint, incoming strings must pass through a strict four-stage security waterfall:

flowchart TD
    A[Incoming Request Vector] --> B[Layer 0: Normalization & Canonicalization]
    B --> C[Layer 1: Deterministic Signature Filter]
    C --> D[Layer 2: Cognitive ML Classifier]
    D --> E[Layer 3: Contextual Policy & PII Guard]


| Security Layer | Component Name | Technical Function | Runtime Cost |
| :--- | :--- | :--- | :--- |
| **Layer 0** | `Normalization` | Decodes URL parameters and flattens Unicode homoglyphs to stop obfuscation tricks. | Less than 1ms |
| **Layer 1** | `Signature Filter` | Evaluates token-agnostic regex boundary statements to instantly drop classic exploit logic. | **4.5 ms** |
| **Layer 2** | `ML Classifier` | Processes complex semantic patterns using a fine-tuned **DistilBERT** transformer model. | Variable |
| **Layer 3** | `Contextual Policy` | Enforces structural data restrictions, input format safety bounds, and blocks PII leaks. | Less than 2ms |


### Key Engineering Features
* **Bypass Elimination:** Mitigates complex logical statements (like `admin' OR '1'='1`) by using flexible tracking boundaries instead of static text keywords.
* **Fail-Secure System Control:** Built with a strict containment policy. If any security module hits a runtime error or dependency fault, the application automatically blocks the entry stream (`HTTP 500`) to protect downstream assets.
* **Dynamic Path Resolution:** Uses absolute root-path calculation routines so configuration rules load accurately regardless of where the application container boots from.


### Technical Stack

**Web Framework:** Python 3.14, FastAPI, Pydantic v2

**AI & Machine Learning:** PyTorch, Hugging Face Transformers (DistilBERT Classifier)

**Security & Ops:** Docker, SlowAPI (Rate-Limiter), GitHub Actions


### Spin Up Agent Shield Locally

**1. Installation**

Clone the repository and set up a fresh Python virtual environment:

git clone https://github.com/Sandeep-int/agent-shield.git
cd agent-shield
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


**2. Launching the API Server**

Run the application from the root project directory using Uvicorn:

python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload


**Testing the API**

You can test the validation speed and defense layers using a simple terminal curl request:

curl -X POST "http://127.0.0.1:8000/v1/check" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"admin' OR '1'='1\"}"


**Response Received:**

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


**Current Project Roadmap**

**Phase 2 Pipeline (Next Step):** Automate synthetic attack payload data harvesting using automated security frameworks to build a training log bank of 2,500+ verified sample vectors.

**Model Retraining:** Retrain the core DistilBERT engine to target an accuracy threshold of 95%+ with a false-positive rate under 2%.