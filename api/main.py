import os
import sys
import time
import logging
import urllib.parse
import unicodedata
from datetime import datetime, timezone

# FastAPI core imports
from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader  # ← NEW: reads X-API-Key from request header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# Rate limiting imports (slowapi wraps Flask-Limiter logic for FastAPI)
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Make sure project root is in path so detectors/ can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.vigil_scanner import VigilScanner       # L1: Signature/pattern scanner
from detectors.bert_classifier import BertClassifier   # L2: ONNX DistilBERT model

# ─────────────────────────────────────────────
# LOGGING SETUP
# Logs go to Azure App Service log stream
# View via: Azure Portal → App Service → Log Stream
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# ENVIRONMENT VARIABLES
# NEVER hardcode secrets. Always use env vars.
# Set these in Azure Portal → App Service → Configuration → App Settings
# ─────────────────────────────────────────────
AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")

# API key loaded from environment — set this in Azure App Settings
# Key name: AGENT_SHIELD_API_KEY
# Value: generate a strong random key (use: openssl rand -hex 32)
VALID_API_KEY = os.environ.get("AGENT_SHIELD_API_KEY", "")

# ─────────────────────────────────────────────
# API KEY AUTH SETUP
# APIKeyHeader tells FastAPI to look for "X-API-Key" in request headers
# auto_error=False → we handle the error manually (custom message)
# ─────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency function — injected into protected endpoints.
    Every request to /v1/check must pass through this first.
    If key is missing or wrong → 401 Unauthorized.
    If key matches env var → request proceeds.
    """
    if not api_key or api_key != VALID_API_KEY:
        logger.warning("Unauthorized access attempt — invalid or missing API key")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Valid X-API-Key header required."
        )
    return api_key


# ─────────────────────────────────────────────
# AUDIT LOGGING TO AZURE TABLE STORAGE
# Every request (ALLOW or BLOCK) is logged to Azure Table Storage
# Table name: agentshieldlogs
# Useful for: threat analysis, retraining data, compliance
# ─────────────────────────────────────────────
def log_to_azure(prompt, verdict, confidence, layer_hit, latency_ms, client_ip):
    try:
        from azure.data.tables import TableServiceClient
        service = TableServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        table = service.get_table_client("agentshieldlogs")
        try:
            service.create_table("agentshieldlogs")  # creates table if not exists
        except:
            pass  # table already exists — safe to ignore
        entity = {
            "PartitionKey": verdict,           # BLOCK or ALLOW — used for filtering
            "RowKey": str(time.time_ns()),     # unique ID using nanosecond timestamp
            "prompt": prompt[:500],            # truncated to 500 chars for storage limits
            "verdict": verdict,
            "confidence": float(confidence),
            "layer_hit": layer_hit,            # which layer caught it: L1, L2, or PASS
            "latency_ms": float(latency_ms),
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        table.upsert_entity(entity)
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")  # log failure but don't crash API


# ─────────────────────────────────────────────
# RATE LIMITER SETUP
# Limits requests per IP address
# Current limit: 30 requests per minute per IP
# Prevents abuse, brute force, and DDoS
# ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Agent Shield",
    description="Hardened Hybrid WAF & Prompt Injection Engine",
    version="1.2.0"   # bumped version — API key auth added
)

app.state.limiter = limiter

# When rate limit is hit → return 429 with clean JSON message
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Rate limit exceeded. Max 30 requests/minute."}
))
app.add_middleware(SlowAPIMiddleware)


# ─────────────────────────────────────────────
# SECURITY ENGINE STARTUP
# Loads L1 (Vigil signature scanner) and L2 (ONNX BERT model) at startup
# If either fails → app crashes intentionally (can't run without security engine)
# ─────────────────────────────────────────────
try:
    scanner = VigilScanner()        # L1: pattern/signature based detection
    classifier = BertClassifier()   # L2: ML model (DistilBERT ONNX, 99.29% accuracy)
    logger.info("✓ Security Engine Loaded: L1_VIGIL + L2_ONNX")
except Exception as e:
    logger.critical(f"FATAL: Core engine failed to load: {e}")
    raise


# ─────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# Pydantic models validate and sanitize input automatically
# ─────────────────────────────────────────────
class CheckRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)

    @field_validator("prompt")
    @classmethod
    def normalize_and_validate(cls, value: str) -> str:
        """
        Sanitizes input before scanning:
        1. Strip whitespace
        2. URL decode (catches base64/encoded injections)
        3. Unicode normalize (catches unicode obfuscation attacks)
        4. Remove combining characters (zero-width chars, diacritics used to bypass)
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Empty payload.")
        decoded = urllib.parse.unquote(cleaned)
        normalized = "".join(
            ch for ch in unicodedata.normalize('NFKC', decoded)
            if not unicodedata.combining(ch)
        )
        return normalized


class CheckResponse(BaseModel):
    verdict: str          # BLOCK or ALLOW
    confidence: float     # 0.0 to 1.0
    layer_hit: str        # which layer made the decision
    latency_ms: float     # total processing time
    details: dict         # extra info (hits, model score, etc.)


# ─────────────────────────────────────────────
# MAIN ENDPOINT: /v1/check
# Protected by: API key auth + rate limiting
# Flow: L1 Vigil → L2 ONNX Model → ALLOW
# ─────────────────────────────────────────────
@app.post("/v1/check", response_model=CheckResponse)
@limiter.limit("30/minute")
async def check_prompt(
    request: Request,
    req: CheckRequest,
    api_key: str = Depends(verify_api_key)   # ← NEW: API key checked before anything else
):
    start_time = time.time()
    target_payload = req.prompt
    client_ip = get_remote_address(request)

    # ── LAYER 1: Vigil Signature Scanner ──
    # Fast pattern matching against known injection signatures
    # If hit → immediately BLOCK, skip L2
    try:
        vigil_result = scanner.scan(target_payload)
        if vigil_result.get("blocked", False):
            latency = (time.time() - start_time) * 1000
            log_to_azure(target_payload, "BLOCK", 0.99, "L1_VIGIL_SIGNATURE", latency, client_ip)
            return CheckResponse(
                verdict="BLOCK",
                confidence=0.99,
                layer_hit="L1_VIGIL_SIGNATURE",
                latency_ms=latency,
                details={"hits": vigil_result.get("hits", [])}
            )
    except Exception as e:
        logger.error(f"L1 Vigil Error: {e}")
        raise HTTPException(status_code=500, detail="L1 inspection failed.")

    # ── LAYER 2: ONNX DistilBERT Model ──
    # ML-based detection — catches novel/obfuscated injections L1 misses
    # Threshold: 0.75 confidence (tunable — currently above default 0.5)
    try:
        bert_result = classifier.classify(target_payload)
        if bert_result.get("is_injection") and bert_result.get("confidence", 0) > 0.75:
            latency = (time.time() - start_time) * 1000
            log_to_azure(target_payload, "BLOCK", bert_result["confidence"], "L2_ONNX_MODEL", latency, client_ip)
            return CheckResponse(
                verdict="BLOCK",
                confidence=float(bert_result["confidence"]),
                layer_hit="L2_ONNX_MODEL",
                latency_ms=latency,
                details={"model_confidence": bert_result["confidence"]}
            )
    except Exception as e:
        logger.error(f"L2 ONNX Error: {e}")
        raise HTTPException(status_code=500, detail="L2 model inference failed.")

    # ── COMPREHENSIVE PASS ──
    # Both layers cleared → prompt is clean
    total_latency = (time.time() - start_time) * 1000
    log_to_azure(target_payload, "ALLOW", 0.00, "COMPREHENSIVE_PASS", total_latency, client_ip)
    return CheckResponse(
        verdict="ALLOW",
        confidence=0.00,
        layer_hit="COMPREHENSIVE_PASS",
        latency_ms=total_latency,
        details={"all_checks": "verified_clean"}
    )


# ─────────────────────────────────────────────
# HEALTH CHECK ENDPOINT
# Public — no API key required
# Used by Azure App Service to verify app is running
# ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "Agent Shield Active", "version": "1.2.0"}


# ─────────────────────────────────────────────
# LOCAL DEV ENTRY POINT
# Not used in Azure — Azure uses gunicorn/uvicorn via startup command
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)