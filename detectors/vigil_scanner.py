import os
import yaml
import re
import time
import unicodedata
import logging

class VigilScanner:
    def __init__(self, rules_file=None):
        # If no explicit path is passed, calculate it dynamically relative to this file
        if rules_file is None:
            # 1. Get the absolute path of vigil_scanner.py
            current_file_path = os.path.abspath(__file__)
            # 2. Get the parent root directory (agent-shield/) by moving up 2 levels
            project_root = os.path.dirname(os.path.dirname(current_file_path))
            # 3. Create absolute path targeting the root-level config asset
            rules_file = os.path.join(project_root, "vigil_patterns.yaml")
        
        logging.info(f"[*] Signature Engine binding rules file from: {rules_file}")
        
        with open(rules_file, "r", encoding="utf-8") as f:
            self.rules = yaml.safe_load(f)
    
    def normalize(self, text: str) -> str:
        # Step 1: Convert Unicode variants to standard form (NFKC representation)
        text = unicodedata.normalize("NFKC", text)
        
        # Step 2: Remove zero-width characters and hidden evasive spaces
        text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad]', '', text)
        
        # Step 3: Clean up and collapse irregular spacing tokens
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def scan(self, text: str) -> dict:
        start = time.time()
        
        # Normalize first to neutralize obfuscation tricks
        normalized = self.normalize(text)
        
        hits = []
        for pattern in self.rules.get("patterns", []):
            # re.IGNORECASE is redundant here if your regex tokens use (?i), 
            # but keeping it guarantees strict fallback enforcement
            if re.search(pattern["regex"], normalized, re.IGNORECASE):
                hits.append({
                    "name": pattern["name"], 
                    "severity": pattern["severity"]
                })
        
        return {
            "blocked": len(hits) > 0,
            "hits": hits,
            "latency_ms": (time.time() - start) * 1000,
            "original": text,
            "normalized": normalized
        }