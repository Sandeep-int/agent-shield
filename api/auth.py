"""
api/auth.py — GitHub OAuth handler for Agent Shield
Routes:
  GET /auth/login     → redirects to GitHub OAuth
  GET /auth/callback  → handles GitHub callback, generates token, saves to Azure Table
  POST /auth/revoke   → revokes a token
"""
import os
import secrets
import time
import logging
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)

GITHUB_CLIENT_ID     = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")

TOKEN_EXPIRY_DAYS = 90

router = APIRouter(prefix="/auth", tags=["auth"])


def get_table_client():
    from azure.data.tables import TableServiceClient
    service = TableServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    try:
        service.create_table("agentshieldtokens")
    except Exception:
        pass
    return service.get_table_client("agentshieldtokens")


def generate_token() -> str:
    """Generate a secure random token prefixed with as_tok_"""
    return f"as_tok_{secrets.token_urlsafe(32)}"


def save_token(github_id: str, username: str, email: str, token: str):
    """Save token to Azure Table Storage"""
    try:
        table = get_table_client()
        expiry = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
        entity = {
            "PartitionKey": "tokens",
            "RowKey": token,
            "github_id": str(github_id),
            "username": username,
            "email": email or "",
            "token": token,
            "status": "active",
            "calls_total": 0,
            "calls_today": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expiry.isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        table.upsert_entity(entity)
        logger.info(f"Token saved for GitHub user: {username}")
    except Exception as e:
        logger.error(f"Failed to save token: {e}")
        raise


def validate_token(token: str) -> dict | None:
    """
    Validate token against Azure Table.
    Returns entity if valid, None if invalid/expired/revoked.
    """
    try:
        table = get_table_client()
        entity = table.get_entity(partition_key="tokens", row_key=token)

        # check status
        if entity.get("status") != "active":
            return None

        # check expiry
        expires_at = entity.get("expires_at", "")
        if expires_at:
            expiry = datetime.fromisoformat(expires_at)
            if datetime.now(timezone.utc) > expiry:
                # auto-revoke expired token
                entity["status"] = "expired"
                table.upsert_entity(entity)
                return None

        # update last_seen + call count
        entity["last_seen"] = datetime.now(timezone.utc).isoformat()
        entity["calls_total"] = int(entity.get("calls_total", 0)) + 1
        entity["calls_today"] = int(entity.get("calls_today", 0)) + 1
        table.upsert_entity(entity)

        return dict(entity)
    except Exception:
        return None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/login")
async def auth_login():
    """Redirect user to GitHub OAuth page"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="OAuth not configured")

    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=read:user,user:email"
        f"&prompt=consent"
    )
    return RedirectResponse(url=github_url)


@router.get("/callback")
async def auth_callback(request: Request):
    """
    GitHub redirects here after user authorizes.
    Exchange code for token, save to Azure Table, return token to CLI.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code")

    # Exchange code for GitHub access token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_data = resp.json()

    github_access_token = token_data.get("access_token")
    if not github_access_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    # Fetch GitHub user profile
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
            timeout=10,
        )
        user_data = user_resp.json()

    github_id = str(user_data.get("id", ""))
    username  = user_data.get("login", "unknown")
    email     = user_data.get("email", "")

    if not github_id:
        raise HTTPException(status_code=400, detail="Could not fetch GitHub identity")

    # Generate Agent Shield token
    as_token = generate_token()
    save_token(github_id, username, email, as_token)

    logger.info(f"OAuth success: {username} (GitHub ID: {github_id})")

    # Return token to CLI — CLI polls this page
    return JSONResponse(content={
        "status": "success",
        "token": as_token,
        "username": username,
        "expires_in_days": TOKEN_EXPIRY_DAYS,
        "message": f"Authenticated as {username}. Token saved."
    })


@router.post("/revoke")
async def auth_revoke(request: Request):
    """Revoke a token — called by CLI on agent-shield auth --revoke"""
    body = await request.json()
    token = body.get("token", "")

    if not token:
        raise HTTPException(status_code=400, detail="Token required")

    try:
        table = get_table_client()
        entity = table.get_entity(partition_key="tokens", row_key=token)
        entity["status"] = "revoked"
        table.upsert_entity(entity)
        logger.info(f"Token revoked: {entity.get('username', 'unknown')}")
        return JSONResponse(content={"status": "revoked"})
    except Exception:
        raise HTTPException(status_code=404, detail="Token not found")