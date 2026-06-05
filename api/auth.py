"""
api/auth.py — GitHub OAuth handler for Agent Shield
Routes:
  GET /auth/login     → redirects to GitHub OAuth with CSRF state
  GET /auth/callback  → handles GitHub callback, validates state, generates token
  POST /auth/revoke   → revokes a token
"""
import os
import secrets
import time
import logging
import httpx
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException, Cookie
from fastapi.responses import JSONResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)

GITHUB_CLIENT_ID     = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
AZURE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "true").lower() == "true"

TOKEN_EXPIRY_DAYS = 90

# CSRF state storage (in-memory for simplicity, use Redis in production)
oauth_states = {}

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


def hash_token(token: str) -> str:
    """BLAKE2b hash of token — stored in Azure, never plain text"""
    return hashlib.blake2b(token.encode(), digest_size=32).hexdigest()

def save_token(github_id: str, username: str, email: str, token: str):
    """Save token to Azure Table Storage"""
    try:
        table = get_table_client()
        expiry = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
        token_hash = hash_token(token)
        entity = {
            "PartitionKey": "tokens",
            "RowKey": token_hash,
            "github_id": str(github_id),
            "username": username,
            "email": email or "",
            "token_hash": token_hash,
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
        token_hash = hash_token(token)
        entity = table.get_entity(partition_key="tokens", row_key=token_hash)

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
async def auth_login(request: Request):
    """Redirect user to GitHub OAuth page with CSRF state"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="OAuth not configured")
    
    # Force HTTPS check
    if FORCE_HTTPS and request.url.scheme != "https":
        raise HTTPException(status_code=400, detail="HTTPS required")
    
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "created_at": datetime.now(timezone.utc).timestamp(),
        "ip": request.client.host if request.client else "unknown"
    }
    
    # Clean up old states (older than 10 minutes)
    now = datetime.now(timezone.utc).timestamp()
    oauth_states.clear()
    oauth_states[state] = {"created_at": now, "ip": request.client.host if request.client else "unknown"}

    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=read:user,user:email"
        f"&state={state}"
        f"&prompt=consent"
    )
    return RedirectResponse(url=github_url)


@router.get("/callback")
async def auth_callback(request: Request):
    """
    GitHub redirects here after user authorizes.
    Validates CSRF state, exchanges code for token, returns httpOnly cookie.
    """
    # Force HTTPS check
    if FORCE_HTTPS and request.url.scheme != "https":
        raise HTTPException(status_code=400, detail="HTTPS required")
    
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code")
    
    # Validate CSRF state
    if not state or state not in oauth_states:
        logger.warning(f"Invalid or expired OAuth state from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=400, detail="Invalid or expired state (CSRF protection)")
    
    # Check state age (max 10 minutes)
    state_data = oauth_states.pop(state)
    state_age = datetime.now(timezone.utc).timestamp() - state_data["created_at"]
    if state_age > 600:  # 10 minutes
        raise HTTPException(status_code=400, detail="State expired")
    
    # Exchange code for GitHub access token

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

    # Return token with httpOnly cookie (more secure than JSON)
    response = JSONResponse(content={
        "status": "success",
        "token": as_token,
        "username": username,
        "expires_in_days": TOKEN_EXPIRY_DAYS,
        "message": f"Authenticated as {username}. Token saved. Copy token for CLI use."
    })
    
    # Set httpOnly cookie (more secure, but also return token for CLI compatibility)
    response.set_cookie(
        key="agent_shield_token",
        value=as_token,
        httponly=True,
        secure=FORCE_HTTPS,  # Only send over HTTPS
        samesite="strict",
        max_age=TOKEN_EXPIRY_DAYS * 86400
    )
    
    return response


@router.post("/revoke")
async def auth_revoke(request: Request):
    """Revoke a token — called by CLI on agent-shield auth --revoke"""
    body = await request.json()
    token = body.get("token", "")

    if not token:
        raise HTTPException(status_code=400, detail="Token required")

    try:
        table = get_table_client()
        token_hash = hash_token(token)
        entity = table.get_entity(partition_key="tokens", row_key=token_hash)
        entity["status"] = "revoked"
        table.upsert_entity(entity)
        logger.info(f"Token revoked: {entity.get('username', 'unknown')}")
        return JSONResponse(content={"status": "revoked"})
    except Exception:
        raise HTTPException(status_code=404, detail="Token not found")