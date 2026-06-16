"""
tests/unit/test_keys.py — Tests for /v1/keys endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.keys import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def make_entity(status="active", days_left=45):
    expiry = (datetime.now(timezone.utc) + timedelta(days=days_left)).isoformat()
    return {
        "PartitionKey": "tokens",
        "RowKey": "fakehash",
        "github_id": "12345",
        "username": "sandeep",
        "email": "s@example.com",
        "token_hash": "fakehash",
        "status": status,
        "calls_total": 10,
        "calls_today": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expiry,
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }


# ── status ────────────────────────────────────────────────────────────────────

def test_status_no_key():
    r = client.get("/v1/keys/status")
    assert r.status_code == 401

def test_status_active():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.return_value = make_entity("active")
        mock_table.return_value = t
        r = client.get("/v1/keys/status", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["username"] == "sandeep"
    assert data["days_remaining"] > 0
    assert "calls_total" in data

def test_status_revoked():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.return_value = make_entity("revoked")
        mock_table.return_value = t
        r = client.get("/v1/keys/status", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 403

def test_status_not_found():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.side_effect = Exception("Not found")
        mock_table.return_value = t
        r = client.get("/v1/keys/status", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 404


# ── rotate ────────────────────────────────────────────────────────────────────

def test_rotate_no_key():
    r = client.post("/v1/keys/rotate")
    assert r.status_code == 401

def test_rotate_active():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.return_value = make_entity("active")
        mock_table.return_value = t
        r = client.post("/v1/keys/rotate", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "rotated"
    assert data["new_token"].startswith("as_tok_")
    assert "warning" in data

def test_rotate_revoked():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.return_value = make_entity("revoked")
        mock_table.return_value = t
        r = client.post("/v1/keys/rotate", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 403


# ── revoke ────────────────────────────────────────────────────────────────────

def test_revoke_no_key():
    r = client.delete("/v1/keys/revoke")
    assert r.status_code == 401

def test_revoke_active():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.return_value = make_entity("active")
        mock_table.return_value = t
        r = client.delete("/v1/keys/revoke", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 200
    assert r.json()["status"] == "revoked"

def test_revoke_not_found():
    with patch("api.keys._get_table") as mock_table:
        t = MagicMock()
        t.get_entity.side_effect = Exception("Not found")
        mock_table.return_value = t
        r = client.delete("/v1/keys/revoke", headers={"X-API-Key": "as_tok_test"})
    assert r.status_code == 404
