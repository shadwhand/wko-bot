"""Bearer token authentication."""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)
_token = None


def set_token(token: str):
    global _token
    _token = token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if _token is None:
        return
    if credentials is None or credentials.credentials != _token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
