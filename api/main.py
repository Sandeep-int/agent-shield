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

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Agent Shield",
    description="Hardened Hybrid WAF & Prompt Injection Engine",
    version="1.2.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Rate limit exceeded"}
))
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
    prompt: str = Field(..., min_length=1, max_length=10000)

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

@app.post("/v1/check", response_model=CheckResponse)
@limiter.limit("30/minute")
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
    uvicorn.run(app, host="0.0.0.0", port=7860)