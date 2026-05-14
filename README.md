---
title: Agent Shield
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: ui.py
pinned: false
---

# Agent Shield

LLM Prompt Injection Detection Engine.

**Layers:**
- L0: Unicode normalization
- L1: Vigil regex scanner
- L2: DistilBERT classifier (93% accuracy)
- L3: Guardrails AI (PII + toxic detection)

**Deploy:** https://huggingface.co/spaces/Sandeep120205/agent-shield
