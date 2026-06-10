import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.main import app

client = TestClient(app)
TEST_API_KEY = os.environ.get("AGENT_SHIELD_API_KEY", "test-key")
HEADERS = {"X-API-Key": TEST_API_KEY}

def test_rate_limit_blocks_after_120():
    for i in range(120):
        response = client.post("/v1/check", json={"prompt": "test"}, headers=HEADERS)
        assert response.status_code == 200, f"Request {i+1} should pass"
    response = client.post("/v1/check", json={"prompt": "test"}, headers=HEADERS)
    assert response.status_code == 429, "121st request should be blocked"

def test_health_not_rate_limited():
    for i in range(15):
        response = client.get("/health")
        assert response.status_code == 200