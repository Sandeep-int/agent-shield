import re
import time

class CustomL3:
    def __init__(self):
        # PII patterns
        self.patterns = {
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'password': r'(password|passwd|pwd)\s*[:=]\s*["\']?[\w@#$%^&*]+',
            'api_key': r'(api[_-]?key|apikey)\s*[:=]\s*["\']?[\w\-]+',
        }
        self.toxic_words = ['kill', 'hate', 'abuse', 'racist', 'sexist']
    
    def check(self, prompt: str):
        start = time.time()
        
        # Check PII
        for pattern_name, pattern in self.patterns.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                return {
                    "passed": False,
                    "reason": f"PII detected: {pattern_name}",
                    "latency_ms": (time.time() - start) * 1000
                }
        
        # Check toxicity
        prompt_lower = prompt.lower()
        for word in self.toxic_words:
            if word in prompt_lower:
                return {
                    "passed": False,
                    "reason": f"Toxic content detected: {word}",
                    "latency_ms": (time.time() - start) * 1000
                }
        
        return {
            "passed": True,
            "reason": "Passed",
            "latency_ms": (time.time() - start) * 1000
        }
