---
title: Agent Shield
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
---

# Agent Shield: Hybrid Web Application Firewall & Prompt Injection Guard

[![Application Runtime](https://img.shields.io/badge/HF%20Spaces-Active-blue?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/Sandeep120205/agent-shield)
[![API Status](https://img.shields.io/badge/API-Live-success?style=flat-square)](https://Sandeep120205-agent-shield.hf.space)

Agent Shield is an advanced, production-hardened security engine built to stop malicious inputs, code injections, and AI prompt hijacking before they reach backend applications.

---

## 🛡️ Multi-Layered Defense Architecture

Instead of relying on a single checkpoint, incoming strings must pass through a four-stage security waterfall:

[ Incoming Payload ]
│
▼
┌────────────────────────────────────────┐
│ Layer 0: Normalization & Cleaning      │
└───────────────────┬────────────────────┘
│
▼
┌────────────────────────────────────────┐
│ Layer 1: High-Speed Signature Filter   │
└───────────────────┬────────────────────┘
│
▼
┌────────────────────────────────────────┐
│ Layer 2: Machine Learning Classifier   │
└───────────────────┬────────────────────┘
│
▼
┌────────────────────────────────────────┐
│ Layer 3: Contextual Policy & PII Guard │
└────────────────────────────────────────┘


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