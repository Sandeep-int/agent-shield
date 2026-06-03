import os
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
from detectors.bert_classifier import BertClassifier
from api.auth import router as auth_router, validate_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_API_KEY           = os.environ.get("AGENT_SHIELD_API_KEY", "")
AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        logger.warning("Unauthorized — missing API key")
        raise HTTPException(status_code=401, detail="Unauthorized. Valid X-API-Key required.")

    # Priority 1 — master env key (backward compatible)
    if VALID_API_KEY and api_key == VALID_API_KEY:
        return api_key

    # Priority 2 — OAuth token from Azure Table
    token_data = validate_token(api_key)
    if token_data:
        return api_key

    logger.warning(f"Unauthorized — invalid key: {api_key[:8]}...")
    raise HTTPException(status_code=401, detail="Unauthorized. Valid X-API-Key required.")

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
            "prompt": prompt[:500],
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
    return api_key in INTERNAL_KEYS

def _is_pro_key(api_key: str) -> bool:
    if not api_key or _is_internal_key(api_key):
        return False
    if VALID_API_KEY and api_key == VALID_API_KEY:
        return True
    return api_key.startswith("as_tok_")

def get_rate_limit_key(request: Request) -> str:
    """Dynamic API key resolution for tiered rate-limit buckets."""
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS if CORS_ALLOWED_ORIGINS else [],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)
app.add_middleware(SlowAPIMiddleware)

# ── Mount auth routes ─────────────────────────────────────────────────────────
app.include_router(auth_router)

try:
    scanner    = VigilScanner()
    classifier = BertClassifier()
    logger.info("✓ Security Engine Loaded: L0, L1, L2")
except Exception as e:
    logger.critical(f"FATAL: Core engine failed: {e}")
    raise

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

def _rate_limit_exempt_pro_or_internal(request: Request) -> bool:
    api_key = _resolve_api_key(request)
    return _is_internal_key(api_key) or _is_pro_key(api_key)

def _rate_limit_exempt_non_pro(request: Request) -> bool:
    api_key = _resolve_api_key(request)
    return _is_internal_key(api_key) or not _is_pro_key(api_key)

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
        logger.error(f"L2 Error: {e}")
        raise HTTPException(status_code=500, detail="Model inference failed.")

    total_latency = (time.time() - start_time) * 1000
    log_to_azure(target_payload, "ALLOW", 0.00, "COMPREHENSIVE_PASS", total_latency, client_ip)
    return CheckResponse(
        verdict="ALLOW",
        confidence=0.00,
        layer_hit="COMPREHENSIVE_PASS",
        latency_ms=total_latency,
        details={"all_checks": "verified_clean"}
    )

@app.get("/metrics")
async def metrics():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=7860)