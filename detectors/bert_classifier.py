import os
import time
import numpy as np
from transformers import DistilBertTokenizer
from onnxruntime import InferenceSession

HF_MODEL = "Sandeep120205/agent-shield-distilbert"
HF_REVISION = "main"  # nosec B615 - private model, no public SHA
MODEL_VERSION = os.environ.get("MODEL_VERSION", "distilbert-v1")
MODEL_DIR = "/home/models"
ONNX_PATH = os.path.join(MODEL_DIR, "model.onnx")
ONNX_DATA_PATH = os.path.join(MODEL_DIR, "model.onnx.data")
BLOB_ONNX = "https://agentshieldmodels.blob.core.windows.net/models/model.onnx"
BLOB_ONNX_DATA = "https://agentshieldmodels.blob.core.windows.net/models/model.onnx.data"

THRESHOLD = 0.85  # owned here ONLY — never check in main.py

def download_file(url: str, dest: str):
    import requests
    print(f"[*] Downloading {os.path.basename(dest)} from Blob...")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"[✓] Downloaded {os.path.basename(dest)}")

class BertClassifier:
    def __init__(self):
        try:
            if not os.path.exists(ONNX_PATH):
                download_file(BLOB_ONNX, ONNX_PATH)
            if not os.path.exists(ONNX_DATA_PATH):
                download_file(BLOB_ONNX_DATA, ONNX_DATA_PATH)
            LOCAL_TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer")
            if os.path.isdir(LOCAL_TOKENIZER_PATH):
                self.tokenizer = DistilBertTokenizer.from_pretrained(  # nosec B615
                    LOCAL_TOKENIZER_PATH,
                    local_files_only=True
                )
                print("[✓] L2: Tokenizer loaded from local cache")
            else:
                self.tokenizer = DistilBertTokenizer.from_pretrained(
                    HF_MODEL,
                    revision=HF_REVISION  # nosec B615
                )
                self.tokenizer.save_pretrained(LOCAL_TOKENIZER_PATH)
                print("[✓] L2: Tokenizer downloaded and cached locally")
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
                max_length=128,        # NEVER change — model trained on 128
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
                "is_injection": predicted_class == 1 and confidence > THRESHOLD,
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