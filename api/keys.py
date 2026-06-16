"""
api/keys.py — Token management for Agent Shield
Routes:
  GET    /v1/keys/status  → expiry + usage for calling token
  POST   /v1/keys/rotate  → issue new token, revoke old
  DELETE /v1/keys/revoke  → hard revoke a token
"""
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/keys", tags=["keys"])


def _get_table():
    import os
    from azure.data.tables import TableServiceClient
    conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    service = TableServiceClient.from_connection_string(conn)
    return service.get_table_client("agentshieldtokens")


def _hash(token: str) -> str:
    pepper = os.environ.get("TOKEN_HASH_PEPPER", "agentshield-default-pepper")
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        token.encode("utf-8"),
        pepper.encode("utf-8"),
        310000,
    )
    return derived.hex()


def _get_entity(token: str):
    table = _get_table()
    token_hash = _hash(token)
    try:
        return table, table.get_entity(partition_key="tokens", row_key=token_hash)
    except Exception:
        raise HTTPException(status_code=404, detail="Token not found")


@router.get("/status")
async def key_status(request: Request):
    """Expiry + usage for the calling token"""
    token = request.headers.get("X-API-Key", "")
    if not token:
        raise HTTPException(status_code=401, detail="X-API-Key required")

    _, entity = _get_entity(token)

    if entity.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Token is {entity.get('status')}")

    expires_at = entity.get("expires_at", "")
    expiry_dt = datetime.fromisoformat(expires_at)
    days_remaining = (expiry_dt - datetime.now(timezone.utc)).days

    return JSONResponse(content={
        "status": "active",
        "username": entity.get("username"),
        "expires_at": expires_at,
        "days_remaining": days_remaining,
        "calls_total": int(entity.get("calls_total", 0)),
        "calls_today": int(entity.get("calls_today", 0)),
    })


@router.post("/rotate")
async def key_rotate(request: Request):
    """Issue new token, revoke old. Returns new token once."""
    import secrets
    token = request.headers.get("X-API-Key", "")
    if not token:
        raise HTTPException(status_code=401, detail="X-API-Key required")

    table, entity = _get_entity(token)

    if entity.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Token is {entity.get('status')}")

    # Revoke old
    entity["status"] = "rotated"
    table.upsert_entity(entity)

    # Issue new
    new_token = f"as_tok_{secrets.token_urlsafe(32)}"
    new_hash = _hash(new_token)
    expiry = datetime.now(timezone.utc) + timedelta(days=90)

    new_entity = {
        "PartitionKey": "tokens",
        "RowKey": new_hash,
        "github_id": entity.get("github_id", ""),
        "username": entity.get("username", ""),
        "email": entity.get("email", ""),
        "token_hash": new_hash,
        "status": "active",
        "calls_total": 0,
        "calls_today": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expiry.isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    table.upsert_entity(new_entity)

    logger.info(f"Token rotated for {entity.get('username')}")
    return JSONResponse(content={
        "status": "rotated",
        "new_token": new_token,
        "expires_at": expiry.isoformat(),
        "warning": "Store this token now. It will not be shown again."
    })


@router.delete("/revoke")
async def key_revoke(request: Request):
    """Hard revoke calling token"""
    token = request.headers.get("X-API-Key", "")
    if not token:
        raise HTTPException(status_code=401, detail="X-API-Key required")

    table, entity = _get_entity(token)
    entity["status"] = "revoked"
    table.upsert_entity(entity)

    logger.info(f"Token revoked: {entity.get('username')}")
    return JSONResponse(content={"status": "revoked", "username": entity.get("username")})
