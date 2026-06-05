import asyncio
import hashlib
import os
import re
import sys
import time
import logging
import urllib.parse
import unicodedata
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.vigil_scanner import VigilScanner
from detectors.l3_custom import CustomL3
from api.auth import router as auth_router, validate_token
from api.secrets_manager import get_secret

# Import BERT classifier only if dependencies available
try:
    from detectors.bert_classifier import BertClassifier
    BERT_AVAILABLE = True
except ImportError as e:
    BERT_AVAILABLE = False
    BertClassifier = None
    import warnings
    warnings.warn(f"BERT classifier unavailable: {e}. Running without ML layer.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_API_KEY           = get_secret("AGENT_SHIELD_API_KEY", "")
AZURE_CONNECTION_STRING = get_secret("AZURE_STORAGE_CONNECTION_STRING", "")

def hash_key(key: str) -> str:
    """BLAKE2b hash — keys stored as hash in Azure, never plain"""
    return hashlib.blake2b(key.encode(), digest_size=32).hexdigest()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        logger.warning("Unauthorized — missing API key")
        raise HTTPException(status_code=401, detail="Unauthorized. Valid X-API-Key required.")
    if VALID_API_KEY and hash_key(api_key) == VALID_API_KEY:
        return api_key
    token_data = validate_token(api_key)
    if token_data:
        return api_key
    logger.warning(f"Unauthorized — invalid key: {api_key[:8]}...")
    raise HTTPException(status_code=401, detail="Unauthorized. Valid X-API-Key required.")

_PII_REDACTIONS = (
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[CARD_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"api[_-]?key\s*[:=]\s*[\"']?[\w\-]+", re.IGNORECASE), "[APIKEY_REDACTED]"),
    (re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*[\"']?[\w@#$%^&*]+", re.IGNORECASE), "[PASSWORD_REDACTED]"),
)


def sanitize_prompt(prompt: str) -> str:
    """Redact common PII/secrets patterns from the prompt before logging to Azure Table."""
    for pattern, replacement in _PII_REDACTIONS:
        prompt = pattern.sub(replacement, prompt)
    return prompt

def log_to_azure(prompt, verdict, confidence, layer_hit, latency_ms, client_ip):
    try:
        from azure.data.tables import TableServiceClient
        service = TableServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        table = service.get_table_client("agentshieldlogs")
        try:
            service.create_table("agentshieldlogs")
        except Exception:
            pass
        entity = {
            "PartitionKey": verdict,
            "RowKey": str(time.time_ns()),
            "prompt": sanitize_prompt(prompt)[:500],
            "verdict": verdict,
            "confidence": float(confidence),
            "layer_hit": layer_hit,
            "latency_ms": float(latency_ms),
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        table.upsert_entity(entity)
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")

# --- Tiered key-based rate limiting ---
MAX_BODY_BYTES = 10240
INTERNAL_KEYS = set(filter(None, os.environ.get("AGENT_STRIKE_INTERNAL_KEYS", "").split(",")))

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

def _resolve_api_key(request: Request) -> str:
    return request.headers.get("X-API-Key", "")

def _is_internal_key(api_key: str) -> bool:
    return hash_key(api_key) in INTERNAL_KEYS

def _is_pro_key(api_key: str) -> bool:
    if not api_key or _is_internal_key(api_key):
        return False
    if VALID_API_KEY and hash_key(api_key) == VALID_API_KEY:
        return True
    return api_key.startswith("as_tok_")

def get_rate_limit_key(request: Request) -> str:
    api_key = _resolve_api_key(request)
    if _is_internal_key(api_key):
        return "internal-unlimited"
    if _is_pro_key(api_key):
        return f"pro:{api_key}"
    return f"ip:{get_remote_address(request)}"

limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title="Agent Shield",
    description="Hardened Hybrid WAF & Prompt Injection Engine",
    version="1.2.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Rate limit exceeded"}
))

@app.middleware("http")
async def payload_size_guard(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Payload Too Large"},
                )
        except ValueError:
            pass
    return await call_next(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if "server" in response.headers:
        del response.headers["server"]
    if "x-powered-by" in response.headers:
        del response.headers["x-powered-by"]
    return response

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS if CORS_ALLOWED_ORIGINS else [],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.include_router(auth_router)

# Initialize detection engines with fallback for optional ML layer
try:
    scanner = VigilScanner()
    logger.info("✓ L1: Vigil Scanner loaded")
except Exception as e:
    logger.critical(f"FATAL: L1 Vigil Scanner failed: {e}")
    raise

# L2 BERT Classifier - Optional (graceful degradation if unavailable)
if BERT_AVAILABLE:
    try:
        classifier = BertClassifier()
        logger.info("✓ L2: BERT Classifier loaded")
    except Exception as e:
        logger.warning(f"⚠ L2 BERT Classifier failed to initialize: {e}")
        logger.warning("⚠ Running without ML detection layer (L1 and L3 still active)")
        BERT_AVAILABLE = False
        classifier = None
else:
    logger.warning("⚠ L2 BERT dependencies not installed (numpy, torch, transformers)")
    logger.warning("⚠ Running without ML detection layer (L1 and L3 still active)")
    classifier = None

try:
    l3 = CustomL3()
    logger.info("✓ L3: Custom Rules Engine loaded")
except Exception as e:
    logger.critical(f"FATAL: L3 Custom Rules failed: {e}")
    raise

if BERT_AVAILABLE:
    logger.info("═══ Security Engine Ready: L1 (Vigil) + L2 (BERT) + L3 (Custom) ═══")
else:
    logger.info("═══ Security Engine Ready: L1 (Vigil) + L3 (Custom) - L2 disabled ═══")

class CheckRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)

    @field_validator("prompt")
    @classmethod
    def normalize_and_validate(cls, value: str) -> str:
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
    verdict: str
    confidence: float
    layer_hit: str
    latency_ms: float
    details: dict

class FeedbackRequest(CheckRequest):
    reason: str = Field(..., min_length=1, max_length=500)

def _rate_limit_exempt_pro_or_internal() -> bool:
    return False  # handled by get_rate_limit_key bucket

def _rate_limit_exempt_non_pro() -> bool:
    return False  # handled by get_rate_limit_key bucket

@app.post("/v1/check", response_model=CheckResponse)
@limiter.limit(
    "10/minute",
    key_func=get_remote_address,
    exempt_when=_rate_limit_exempt_pro_or_internal,
)
@limiter.limit(
    "60/minute",
    key_func=lambda request: _resolve_api_key(request),
    exempt_when=_rate_limit_exempt_non_pro,
)
async def check_prompt(request: Request, req: CheckRequest, api_key: str = Security(verify_api_key)):
    start_time = time.time()
    target_payload = req.prompt
    client_ip = get_remote_address(request)

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
        logger.error(f"L1 Error: {e}")
        raise HTTPException(status_code=500, detail="Inspection failed.")

    # L2: BERT Classifier (skip if not available)
    if BERT_AVAILABLE and classifier:
        try:
            loop = asyncio.get_event_loop()
            bert_result = await asyncio.wait_for(
                loop.run_in_executor(None, classifier.classify, target_payload),
                timeout=10.0
            )
            if bert_result.get("is_injection"):
                latency = (time.time() - start_time) * 1000
                log_to_azure(target_payload, "BLOCK", bert_result["confidence"], "L2_ONNX_MODEL", latency, client_ip)
                return CheckResponse(
                    verdict="BLOCK",
                    confidence=float(bert_result["confidence"]),
                    layer_hit="L2_ONNX_MODEL",
                    latency_ms=latency,
                    details={"model_confidence": bert_result["confidence"]}
                )
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            logger.error("L2 timeout — blocking as safe default")
            log_to_azure(target_payload, "BLOCK", 0.99, "L2_TIMEOUT_BLOCK", latency, client_ip)
            return CheckResponse(
                verdict="BLOCK",
                confidence=0.99,
                layer_hit="L2_TIMEOUT_BLOCK",
                latency_ms=latency,
                details={"reason": "L2 inference timeout — blocked by fail-safe policy"}
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.error(f"L2 Error: {e} — blocking as safe default")
            log_to_azure(target_payload, "BLOCK", 0.99, "L2_ERROR_BLOCK", latency, client_ip)
            return CheckResponse(
                verdict="BLOCK",
                confidence=0.99,
                layer_hit="L2_ERROR_BLOCK",
                latency_ms=latency,
                details={"reason": f"L2 inference error — blocked by fail-safe policy: {str(e)[:100]}"}
            )

    l3_result = l3.check(target_payload)
    if not l3_result.get("passed"):
        total_latency = (time.time() - start_time) * 1000
        log_to_azure(target_payload, "BLOCK", 0.99, "L3_CUSTOM_RULES", total_latency, client_ip)
        return CheckResponse(
            verdict="BLOCK",
            confidence=0.99,
            layer_hit="L3_CUSTOM_RULES",
            latency_ms=total_latency,
            details={"reason": l3_result.get("reason")}
        )

    total_latency = (time.time() - start_time) * 1000
    log_to_azure(target_payload, "ALLOW", 0.00, "COMPREHENSIVE_PASS", total_latency, client_ip)
    return CheckResponse(
        verdict="ALLOW",
        confidence=0.00,
        layer_hit="COMPREHENSIVE_PASS",
        latency_ms=total_latency,
        details={"all_checks": "verified_clean"}
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics(api_key: str = Security(verify_api_key)):
    try:
        from azure.data.tables import TableServiceClient
        service = TableServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        table = service.get_table_client("agentshieldlogs")
        entities = list(table.list_entities())
        total = len(entities)
        block_count = sum(1 for e in entities if e.get("verdict") == "BLOCK")
        allow_count = sum(1 for e in entities if e.get("verdict") == "ALLOW")
        layer_counts = {}
        for e in entities:
            layer = e.get("layer_hit", "UNKNOWN")
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        latencies = [e.get("latency_ms", 0) for e in entities if e.get("latency_ms")]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
        return {
            "total_requests": total,
            "block_count": block_count,
            "allow_count": allow_count,
            "block_rate_percent": round((block_count / total) * 100, 2) if total else 0,
            "avg_latency_ms": avg_latency,
            "layer_breakdown": layer_counts
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.post("/v1/feedback")
@limiter.limit("10/minute", key_func=get_remote_address)
@limiter.limit("60/minute", key_func=lambda request: _resolve_api_key(request), exempt_when=_rate_limit_exempt_non_pro)
async def feedback(request: Request, req: FeedbackRequest, api_key: str = Security(verify_api_key)):
    client_ip = get_remote_address(request)
    try:
        log_to_azure(f"{req.prompt}\n[feedback_reason] {req.reason}", "MISSED", 0.00, "USER_REPORTED", 0.0, client_ip)
    except Exception as e:
        logger.error(f"Feedback log failed: {e}")
        raise HTTPException(status_code=500, detail="Feedback logging failed.")
    return {"status": "logged", "verdict": "MISSED"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"), port=7860)  # nosec B104