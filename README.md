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

Instead of relying on a single checkpoint, incoming strings must pass through a strict four-stage security waterfall:

```mermaid
graph TD
    A[Incoming Payload Vector] --> B[Layer 0: Normalization & Cleaning]
    B --> C[Layer 1: High-Speed Signature Filter]
    C --> D[Layer 2: Machine Learning Classifier]
    D --> E[Layer 3: Contextual Policy & PII Guard]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style B fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px
    style C fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style D fill:#ede7f6,stroke:#673ab7,stroke-width:2px
    style E fill:#e8f5e9,stroke:#4caf50,stroke-width:2px


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