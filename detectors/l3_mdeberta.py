import httpx

L3_URL = "https://sandeep120205-agent-shield-mdeberta-api.hf.space/predict"

class MDebertaL3:
    async def check(self, prompt: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(L3_URL, json={"prompt": prompt})
                data = resp.json()
                return {"is_injection": data.get("is_injection", False), "confidence": data.get("confidence", 0.0)}
        except Exception:
            # INTENTIONAL FAIL-OPEN — L3 is an external HF Spaces dependency.
            return {"is_injection": False, "confidence": 0.0}
