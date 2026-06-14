import httpx

L25_URL = "https://sandeep120205-agent-shield-mdeberta-api.hf.space/predict"
TIMEOUT = 10.0


class MDebertaL25:
    async def check(self, prompt: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(L25_URL, json={"prompt": prompt})
                resp.raise_for_status()
                data = resp.json()
                return {
                    "is_injection": data.get("is_injection", False),
                    "confidence": data.get("confidence", 0.0)
                }
        except Exception:
            # INTENTIONAL FAIL-OPEN — L2.5 is an external HF Spaces dependency.
            # HF Spaces free tier has no uptime SLA. Blocking on network failure
            # would make Azure production availability dependent on HF reliability.
            # L3 custom rules still run after this — attack coverage maintained.
            return {"is_injection": False, "confidence": 0.0}