import httpx
import os

L25_URL = "https://sandeep120205-agent-shield-mdeberta-api.hf.space/predict"
TIMEOUT = 10.0

class MDebertaL25:
    async def check(self, prompt: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(L25_URL, json={"prompt": prompt})
                data = resp.json()
                return {
                    "is_injection": data.get("is_injection", False),
                    "confidence": data.get("confidence", 0.0)
                }
        except Exception:
            # Network failure → ALLOW (never block on L2.5 timeout)
            return {"is_injection": False, "confidence": 0.0}
