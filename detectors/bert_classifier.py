import os
import time
import numpy as np
import hashlib
from transformers import DistilBertTokenizer
from onnxruntime import InferenceSession

HF_MODEL = "Sandeep120205/agent-shield-distilbert"
HF_REVISION = "8d9339cfe468013da01a581f3399c1c19c4f51a3"  # pin to verified commit
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
LOCAL_TOKENIZER_PATH = os.path.join(MODEL_DIR, "fine_tuned_bert")
ONNX_PATH = os.path.join(MODEL_DIR, "model.onnx")
ONNX_DATA_PATH = os.path.join(MODEL_DIR, "model.onnx.data")
BLOB_ONNX = "https://agentshieldmodels.blob.core.windows.net/models/model.onnx"
BLOB_ONNX_DATA = "https://agentshieldmodels.blob.core.windows.net/models/model.onnx.data"

# SHA256 checksums for model integrity verification
EXPECTED_CHECKSUMS = {
    "model.onnx": os.environ.get("MODEL_ONNX_SHA256", ""),  # Set in production
    "model.onnx.data": os.environ.get("MODEL_ONNX_DATA_SHA256", "")  # Set in production
}

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: str, expected: str) -> bool:
    """Verify file checksum against expected value"""
    if not expected:
        print(f"[!] WARNING: No checksum configured for {os.path.basename(filepath)}")
        return True  # Skip verification if not configured
    actual = calculate_sha256(filepath)
    if actual != expected:
        print(f"[!] CHECKSUM MISMATCH for {os.path.basename(filepath)}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {actual}")
        return False
    print(f"[✓] Checksum verified for {os.path.basename(filepath)}")
    return True

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
    
    # Verify checksum after download
    filename = os.path.basename(dest)
    if filename in EXPECTED_CHECKSUMS:
        if not verify_checksum(dest, EXPECTED_CHECKSUMS[filename]):
            os.remove(dest)  # Delete corrupted file
            raise RuntimeError(f"Checksum verification failed for {filename} - possible tampering detected!")

class BertClassifier:
    def __init__(self):
        try:
            try:
                if not os.path.exists(ONNX_PATH):
                    download_file(BLOB_ONNX, ONNX_PATH)
                else:
                    # Verify existing file
                    if EXPECTED_CHECKSUMS["model.onnx"]:
                        if not verify_checksum(ONNX_PATH, EXPECTED_CHECKSUMS["model.onnx"]):
                            print(f"[!] Local ONNX file corrupted, re-downloading...")
                            download_file(BLOB_ONNX, ONNX_PATH)
                
                if not os.path.exists(ONNX_DATA_PATH):
                    download_file(BLOB_ONNX_DATA, ONNX_DATA_PATH)
                else:
                    # Verify existing file
                    if EXPECTED_CHECKSUMS["model.onnx.data"]:
                        if not verify_checksum(ONNX_DATA_PATH, EXPECTED_CHECKSUMS["model.onnx.data"]):
                            print(f"[!] Local ONNX data file corrupted, re-downloading...")
                            download_file(BLOB_ONNX_DATA, ONNX_DATA_PATH)
            except Exception as e:
                if not os.path.exists(ONNX_PATH):
                    raise RuntimeError(f"L2 ONNX unavailable and no local cache: {e}") from e
                print(f"[!] Blob download failed, using cached ONNX weights: {e}")

            try:
                self.tokenizer = DistilBertTokenizer.from_pretrained(
                    HF_MODEL,
                    revision=HF_REVISION,
                )
            except Exception as e:
                if not os.path.isdir(LOCAL_TOKENIZER_PATH):
                    raise RuntimeError(
                        f"L2 tokenizer load failed and no local cache at {LOCAL_TOKENIZER_PATH}: {e}"
                    ) from e
                print(f"[!] HuggingFace tokenizer fetch failed, using local cache: {e}")
                self.tokenizer = DistilBertTokenizer.from_pretrained(
                    LOCAL_TOKENIZER_PATH,
                    local_files_only=True,  # nosec B615
                )

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
                max_length=128,        # ← NEVER change. Model trained on 128.
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
            THRESHOLD = 0.85
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