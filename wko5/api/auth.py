"""Bearer token authentication."""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)
_token = None


def set_token(token: str):
    global _token
    _token = token


def get_token_value() -> str | None:
    """Return the current auth token (for runtime config endpoint)."""
    return _token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if _token is None:
        raise HTTPException(status_code=503, detail="Auth not configured")
    if credentials is None or credentials.credentials != _token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
