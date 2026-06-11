"""
cli/main.py — Agent Shield CLI
Commands:
  agent-shield                          → banner + API health
  agent-shield auth                     → GitHub OAuth login
  agent-shield auth --revoke            → revoke your token
  agent-shield check "<prompt>"         → scan a prompt
  agent-shield check "<prompt>" --api-key <key>  → scan with explicit key
"""
import sys
import os
import argparse
import json
import time
import threading
import webbrowser
import logging
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    print("[!] WARNING: keyring library not installed. Tokens will be stored in plain text.")
    print("    Install: pip install keyring")

API_BASE    = "https://agent-shield-chbxh2hkhxgucgax.eastasia-01.azurewebsites.net"
API_KEY_ENV = "AGENT_SHIELD_API_KEY"
TOKEN_FILE  = Path.home() / ".agent-shield" / "token"
KEYRING_SERVICE = "agent-shield"
KEYRING_USERNAME = "cli-token"

# ── ANSI true-color ──────────────────────────────────────────────────────────
_TOP    = (74,  144, 217)   # #4A90D9
_BOTTOM = (74,  144, 217)   # #4A90D9
_DIM    = (55,  75,  110)   # ← restored — used in print_banner() and cmd_auth()
_GREEN  = (80,  200, 120)
_RED    = (220, 80,  80)
_YELLOW = (220, 180, 80)
_RESET  = "\033[0m"


def _c(rgb, text):
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m{text}{_RESET}"

def _bold(text):
    return f"\033[1m{text}{_RESET}"

# ── ANSI Shadow banner ───────────────────────────────────────────────────────
_AGENT = [
    r" █████╗  ██████╗ ███████╗███╗   ██╗████████╗",
    r"██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝",
    r"███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ",
    r"██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ",
    r"██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ",
    r"╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ",
]
_DASH = [
    r"        ",
    r"        ",
    r"████╗   ",
    r"╚═══╝   ",
    r"        ",
    r"        ",
]
_SHIELD = [
    r"███████╗██╗  ██╗██╗███████╗██╗     ██████╗ ",
    r"██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗",
    r"███████╗███████║██║█████╗  ██║     ██║  ██║",
    r"╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║",
    r"███████║██║  ██║██║███████╗███████╗██████╔╝",
    r"╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝ ",
]

def print_banner():
    out = sys.stdout
    out.write("\n")
    for i in range(6):
        color = _TOP if i < 3 else _BOTTOM
        row = _AGENT[i] + _DASH[i] + _SHIELD[i]
        out.write(_c(color, row) + "\n")
    out.write("\n")
    out.flush()

# ── Token helpers with Keyring support ──────────────────────────────────────
def load_token() -> str | None:
    """Read token from OS keyring (secure) or file (fallback)"""
    try:
        # Try keyring first (most secure)
        if KEYRING_AVAILABLE:
            token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if token:
                return token
        
        # Fallback to file
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
    except Exception as e:
        logger.debug(f"Token load failed: {e}")
    return None

def save_token(token: str):
    """Save token to OS keyring (secure) or file (fallback)"""
    try:
        # Try keyring first (most secure - encrypted by OS)
        if KEYRING_AVAILABLE:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
            print(f"  Token saved securely to OS keyring")
            return
    except Exception as e:
        print(f"  [!] Keyring save failed: {e}")
    
    # Fallback to file
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)  # owner read/write only
    print(f"  [!] Token saved to file (less secure): {TOKEN_FILE}")

def delete_token():
    """Delete token from keyring and file"""
    try:
        # Delete from keyring
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except keyring.errors.PasswordDeleteError:
                pass
        
        # Delete from file
        TOKEN_FILE.unlink(missing_ok=True)
    except Exception as e:
        logger.debug(f"Token delete failed: {e}")

def get_api_key(explicit_key: str | None = None) -> str | None:
    """
    Priority:
    1. --api-key flag
    2. AGENT_SHIELD_API_KEY env var
    3. ~/.agent-shield/token (OAuth token)
    """
    if explicit_key:
        return explicit_key
    env_key = os.environ.get(API_KEY_ENV)
    if env_key:
        return env_key
    return load_token()

def _validate_http_url(url: str) -> str:
    if not url.startswith("https://"):
        raise ValueError(
            f"URL must use https:// scheme, got: {url!r}"
        )
    return url

def safe_urlopen(url_or_request, timeout=10):
    import urllib.request

    if isinstance(url_or_request, urllib.request.Request):
        target = url_or_request.full_url
    else:
        target = url_or_request
    _validate_http_url(target)
    return urllib.request.urlopen(url_or_request, timeout=timeout)  # nosec B310

# ── Health check ─────────────────────────────────────────────────────────────
def cmd_health():
    try:
        req = safe_urlopen(f"{API_BASE}/health", timeout=8)
        data = json.loads(req.read().decode())
        status = data.get("status", "unknown")
        if status in ("ok", "healthy"):
            print(_c(_GREEN, f"  ✔  API online") + f"  —  {API_BASE}")
        else:
            print(_c(_YELLOW, f"  ⚠  API status: {status}"))
    except Exception as e:
        print(_c(_RED, f"  ✘  API unreachable: {e}"))
    print()

# ── Auth command ─────────────────────────────────────────────────────────────
def cmd_auth(revoke: bool = False):
    """GitHub OAuth login or revoke"""
    import urllib.request
    import urllib.error

    if revoke:
        token = load_token()
        if not token:
            print(_c(_YELLOW, "  ⚠  No token found. Already logged out."))
            print()
            return
        # call revoke endpoint
        try:
            payload = json.dumps({"token": token}).encode()
            req = urllib.request.Request(
                f"{API_BASE}/auth/revoke",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            safe_urlopen(req, timeout=10)
        except Exception as e:
            logger.debug(f"Token revoke failed (best-effort): {e}")
        delete_token()
        print(_c(_GREEN, "  ✔  Token revoked. You are logged out."))
        print()
        return

    # ── Login flow ────────────────────────────────────────────────────────────
    login_url = f"{API_BASE}/auth/login"
    print(f"  Opening browser for GitHub login...")
    print(f"  URL: {_c(_DIM, login_url)}")
    print()

    # open browser
    try:
        webbrowser.open(login_url)
    except Exception:
        print(_c(_YELLOW, f"  ⚠  Could not open browser. Visit manually:"))
        print(f"     {login_url}")
        print()

    print("  Waiting for GitHub authorization", end="", flush=True)

    print()
    print()
    print(_c(_YELLOW, "  After authorizing in browser, your token will appear on screen."))
    print(_c(_YELLOW, "  Copy and paste it here:"))
    print()

    token = input("  Token: ").strip()

    if not token or not token.startswith("as_tok_"):
        print(_c(_RED, "  ✘  Invalid token format."))
        print()
        return

    save_token(token)
    print()
    print(_c(_GREEN, f"  ✔  Authenticated. Token saved to {TOKEN_FILE}"))
    print(_c(_DIM,   f"  Expires in 90 days. Run 'agent-shield auth --revoke' to logout."))
    print()

# ── Check command ─────────────────────────────────────────────────────────────
def cmd_check(prompt: str, api_key: str):
    import urllib.request
    import urllib.error

    try:
        payload = json.dumps({"prompt": prompt}).encode()
        req = urllib.request.Request(
            f"{API_BASE}/v1/check",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            method="POST"
        )
        with safe_urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        verdict  = data.get("verdict", "UNKNOWN")
        layer    = data.get("layer_hit", "?")
        conf     = data.get("confidence", 0.0)
        latency  = data.get("latency_ms", 0)

        if verdict == "BLOCK":
            v_colored = _c(_RED, _bold("  BLOCK"))
        elif verdict == "ALLOW":
            v_colored = _c(_GREEN, _bold("  ALLOW"))
        else:
            v_colored = _c(_YELLOW, _bold(f"  {verdict}"))

        print()
        print(f"  Verdict     {v_colored}")
        print(f"  Layer       {_bold(str(layer))}")
        print(f"  Confidence  {_bold(f'{conf:.4f}')}")
        print(f"  Latency     {_bold(f'{latency:.0f}ms')}")
        print()

    except Exception as e:
        print(_c(_RED, f"\n  ✘  Request failed: {e}\n"))

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="agent-shield",
        description="Agent Shield — LLM Prompt Injection Detection CLI",
        add_help=False
    )
    parser.add_argument("command", nargs="?", default=None)
    parser.add_argument("prompt",  nargs="?", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--revoke", action="store_true")
    parser.add_argument("--help", "-h", action="store_true")

    args = parser.parse_args()

    print_banner()

    # ── No command → health + help ────────────────────────────────────────────
    if args.help or args.command is None:
        cmd_health()
        # show login status
        token = load_token()
        if token:
            print(_c(_GREEN, f"  ✔  Logged in  —  token at {TOKEN_FILE}"))
        else:
            print(_c(_YELLOW, "  ⚠  Not logged in  —  run: agent-shield auth"))
        print()
        print("  Usage:")
        print("    agent-shield                          Health + status")
        print("    agent-shield auth                     Login with GitHub")
        print("    agent-shield auth --revoke            Logout")
        print("    agent-shield check \"<prompt>\"         Scan a prompt")
        print("    agent-shield check \"<prompt>\" --api-key <key>")
        print(f"\n  Env var: {API_KEY_ENV}=<your-key>")
        print()
        return

    # ── auth ──────────────────────────────────────────────────────────────────
    if args.command == "auth":
        cmd_auth(revoke=args.revoke)
        return

    # ── check ─────────────────────────────────────────────────────────────────
    if args.command == "check":
        if not args.prompt:
            print(_c(_RED, "  ✘  Provide a prompt: agent-shield check \"your prompt here\""))
            print()
            sys.exit(1)

        api_key = get_api_key(args.api_key)
        if not api_key:
            print(_c(_RED, "  ✘  Not authenticated."))
            print(f"  Run: agent-shield auth")
            print(f"  Or:  export {API_KEY_ENV}=your-key")
            print()
            sys.exit(1)

        cmd_check(args.prompt, api_key)
        return

    # ── unknown ───────────────────────────────────────────────────────────────
    print(_c(_YELLOW, f"  ⚠  Unknown command: {args.command}"))
    print("  Run: agent-shield --help")
    print()
    sys.exit(1)


if __name__ == "__main__":
    main()