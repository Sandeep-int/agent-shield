import yaml
import re
import time
import unicodedata

class VigilScanner:
    def __init__(self, rules_file="detectors/vigil_patterns.yaml"):
        with open(rules_file) as f:
            self.rules = yaml.safe_load(f)
    
    def normalize(self, text: str) -> str:
        # Step 1: Convert Unicode variants to standard form
        text = unicodedata.normalize("NFKC", text)
        
        # Step 2: Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad]', '', text)
        
        # Step 3: Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def scan(self, text):
        start = time.time()
        
        # Normalize first
        normalized = self.normalize(text)
        
        hits = []
        for pattern in self.rules["patterns"]:
            if re.search(pattern["regex"], normalized, re.IGNORECASE):
                hits.append({"name": pattern["name"], "severity": pattern["severity"]})
        
        return {
            "blocked": len(hits) > 0,
            "hits": hits,
            "latency_ms": (time.time() - start) * 1000,
            "original": text,
            "normalized": normalized
        }