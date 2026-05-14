import os
import sys
import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Dynamic import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.vigil_scanner import VigilScanner
from detectors.bert_classifier import BertClassifier
from detectors.l3_custom import CustomL3

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI + Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Agent Shield",
    description="LLM Prompt Injection Detection (L0-L3)",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Rate limit exceeded"}
))
app.add_middleware(SlowAPIMiddleware)

# Initialize detectors
try:
    scanner = VigilScanner()
    classifier = BertClassifier()
    l3_checker = CustomL3()
    logger.info("✓ All detectors loaded (L0-L3)")
except Exception as e:
    logger.error(f"Detector load failed: {e}")
    raise

# Models
class CheckRequest(BaseModel):
    prompt: str

class CheckResponse(BaseModel):
    verdict: str
    confidence: float
    layer_hit: str
    latency_ms: float
    details: dict

# Routes
@app.post("/v1/check", response_model=CheckResponse)
@limiter.limit("10/minute")
async def check_prompt(request: Request, req: CheckRequest):
    """Run prompt through L1→L2→L3 detection chain."""
    
    if not req.prompt or len(req.prompt.strip()) == 0:
        return CheckResponse(
            verdict="REJECT",
            confidence=1.0,
            layer_hit="VALIDATION",
            latency_ms=0,
            details={"reason": "Empty prompt"}
        )
    
    start_time = time.time()
    
    # L1: Vigil regex scan
    try:
        vigil_result = scanner.scan(req.prompt)
        if vigil_result["blocked"]:
            return CheckResponse(
                verdict="BLOCK",
                confidence=0.95,
                layer_hit="L1_VIGIL",
                latency_ms=vigil_result.get("latency_ms", 0),
                details={"hits": vigil_result.get("hits", [])}
            )
    except Exception as e:
        logger.error(f"L1 error: {e}")
        return CheckResponse(
            verdict="ERROR",
            confidence=0.0,
            layer_hit="L1_ERROR",
            latency_ms=(time.time() - start_time) * 1000,
            details={"error": str(e)}
        )
    
    # L2: DistilBERT classification
    try:
        bert_result = classifier.classify(req.prompt)
        if bert_result.get("is_injection") and bert_result.get("confidence", 0) > 0.7:
            return CheckResponse(
                verdict="BLOCK",
                confidence=bert_result["confidence"],
                layer_hit="L2_BERT",
                latency_ms=bert_result.get("latency_ms", 0),
                details={"model_confidence": bert_result["confidence"]}
            )
    except Exception as e:
        logger.error(f"L2 error: {e}")
        return CheckResponse(
            verdict="ERROR",
            confidence=0.0,
            layer_hit="L2_ERROR",
            latency_ms=(time.time() - start_time) * 1000,
            details={"error": str(e)}
        )
    
    # L3: Custom PII + Toxicity check
    try:
        l3_result = l3_checker.check(req.prompt)
        if not l3_result["passed"]:
            return CheckResponse(
                verdict="BLOCK",
                confidence=0.99,
                layer_hit="L3_CUSTOM",
                latency_ms=l3_result.get("latency_ms", 0),
                details={"reason": l3_result["reason"]}
            )
    except Exception as e:
        logger.error(f"L3 error: {e}")
    
    # All layers passed
    total_latency = (time.time() - start_time) * 1000
    return CheckResponse(
        verdict="ALLOW",
        confidence=0.0,
        layer_hit="L1_L2_L3_PASS",
        latency_ms=total_latency,
        details={"all_checks": "passed"}
    )

@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request):
    """Health check endpoint."""
    return {
        "status": "ok",
        "product": "Agent Shield",
        "layers": ["L0_UNICODE", "L1_VIGIL", "L2_BERT", "L3_CUSTOM"],
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Shield",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "check_endpoint": "POST /v1/check"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
