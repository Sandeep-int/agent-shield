import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import os
import time

# Dynamic model path
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "bert_injection")

class BertClassifier:
    def __init__(self):
        # Point BOTH to the same folder
        path = "./models/fine_tuned_bert"
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(path)
            self.model = DistilBertForSequenceClassification.from_pretrained(path)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Critical load error: {e}")
            raise e

    def classify(self, prompt: str):
        start = time.time()
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=128).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            logits = outputs.logits
            confidence = torch.softmax(logits, dim=1)[0].max().item()
            is_injection = logits.argmax(dim=1).item() == 1
            
            return {
                "is_injection": is_injection,
                "confidence": confidence,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return {"is_injection": False, "confidence": 0.0, "latency_ms": (time.time() - start) * 1000, "error": str(e)}
