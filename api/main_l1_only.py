from fastapi import FastAPI, Request
from pydantic import BaseModel
import sys
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detectors.vigil_scanner import VigilScanner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detectors.vigil_scanner import VigilScanner

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

scanner = VigilScanner()

class CheckRequest(BaseModel):
    prompt: str

@app.post("/v1/check")
@limiter.limit("10/minute")
async def check_prompt(request: Request, req: CheckRequest):
    result = scanner.scan(req.prompt)
    return {
        "verdict": "BLOCK" if result["blocked"] else "ALLOW",
        "confidence": 0.95 if result["blocked"] else 0.0,
        "layer_hit": "L1_VIGIL",
        "latency_ms": result["latency_ms"],
        "details": {"hits": result["hits"]} if result["blocked"] else {}
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
