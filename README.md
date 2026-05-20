---
title: Agent Shield
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
---

# 🛡️ Agent Shield: protects your AI

[![Application Runtime](https://img.shields.io/badge/HF%20Spaces-Active-blue?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/Sandeep120205/agent-shield)
[![API Status](https://img.shields.io/badge/API-Live-success?style=flat-square)](https://Sandeep120205-agent-shield.hf.space)

Agent Shield is a low-latency, multi-layered security gateway engineered to intercept malicious code injections, structural logical bypasses, and adversarial prompt hijacking attempts before they reach downstream Large Language Models (LLMs) and backend databases.

By combining deterministic canonicalization filters with a fine-tuned cognitive neural model, Agent Shield provides robust runtime defense-in-depth without introducing performance bottlenecks.

---

## 🛡️ Multi-Layered Defense Architecture

Instead of relying on a single checkpoint, incoming strings must pass through a strict four-stage security waterfall:

flowchart TD

    subgraph INPUT [User Input Space]
        A[Incoming Request Vector]
    end

    subgraph PIPELINE [Cascading Verification Engine]
        B(Layer 0: Canonicalization) -->|Normalized String| C(Layer 1: Deterministic Filter)
        C -->|Signature Passed| D(Layer 2: Machine Learning Classifier)
        D -->|Semantic Verified| E(Layer 3: Privacy & Context Guard)
    end

    subgraph SYSTEM [Downstream System Boundary]
        F[Secure Downstream Execution / LLM]
    end

    A --> B
    E -->|Clean Output Passed| F



| Security Layer | Component Name | Technical Function | Runtime Cost |
| :--- | :--- | :--- | :--- |
| **Layer 0** | `Normalization` | URL decoding and Unicode NFKC flattening to neutralize obfuscation homoglyphs. | < 1.0 ms |
| **Layer 1** | `Signature Filter` | Scans input against token-agnostic regex boundaries to drop SQLi/CMD/XSS logic instantly. | **4.5 ms** |
| **Layer 2** | `ML Classifier` | Evaluates semantic intent anomalies using a fine-tuned DistilBERT transformer model. | Variable |
| **Layer 3** | `Context Guard` | Restricts system-level prompt overrides, safety bounds, and prevents PII leaks. | < 2.0 ms |


### Key Engineering Features

* **Bypass Elimination:** Mitigates advanced logical bypasses (such as the classic admin' OR '1'='1 string manipulation vector) by evaluating contextual matching boundaries rather than checking for hardcoded static text keywords.

* **Fail-Secure System Control:** Implements a strict fail-closed protocol. If any security module encounters a dependency fault or unhandled runtime exception, the engine instantly drops a containment gate (HTTP 500) to secure downstream systems.

* **Dynamic Path Resolution:** Uses absolute root-path calculation routines so configuration rules load accurately regardless of where the application container boots from.


### Quick Start 

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