import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/mnt/d/projects/prompt-wall')
from api.main import app

client = TestClient(app)

def test_rate_limit_blocks_after_10():
    # First 10 should pass
    for i in range(10):
        response = client.post("/v1/check", json={"prompt": "test"})
        assert response.status_code == 200, f"Request {i+1} should pass"
    
    # 11th should be blocked
    response = client.post("/v1/check", json={"prompt": "test"})
    assert response.status_code == 429, "11th request should be blocked"

def test_health_not_rate_limited():
    # Health should allow more requests
    for i in range(15):
        response = client.get("/health")
        assert response.status_code == 200