import os
import time
import numpy as np
from transformers import DistilBertTokenizer
from onnxruntime import InferenceSession

HF_MODEL = "Sandeep120205/agent-shield-distilbert"
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
ONNX_PATH = os.path.join(MODEL_DIR, "model.onnx")

class BertClassifier:
    def __init__(self):
        try:
            # Load tokenizer from HF Hub (works on Azure)
            self.tokenizer = DistilBertTokenizer.from_pretrained(HF_MODEL)
            self.session = InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])
            print("[✓] L2: ONNX model loaded")
        except Exception as e:
            raise RuntimeError(f"L2 load failed: {e}")

    def classify(self, prompt: str):
        start = time.time()
        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="np",
                truncation=True,
                max_length=256,
                padding="max_length"
            )
            feeds = {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64)
            }
            logits = self.session.run(["logits"], feeds)[0]
            probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
            predicted_class = int(np.argmax(probs, axis=1)[0])
            confidence = float(probs[0][predicted_class])
            return {
                "is_injection": predicted_class == 1,
                "confidence": confidence,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return {
                "is_injection": False,
                "confidence": 0.0,
                "latency_ms": (time.time() - start) * 1000,
                "error": str(e)
            }
