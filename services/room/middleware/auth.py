from functools import wraps
from typing import Optional, List
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import httpx
import os

class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer()
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
        
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        token = credentials.credentials
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_service_url}/verify-token",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials"
                )
            return response.json()

auth_middleware = AuthMiddleware()

def require_auth(scopes: Optional[List[str]] = None):
    """Decorator to require authentication with optional scope check"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user_data: dict = Security(require_auth_security), **kwargs):
            if scopes and not any(scope in user_data.get('scopes', []) for scope in scopes):
                raise HTTPException(status_code=403, detail="Not authorized")
            return await func(*args, user_data=user_data, **kwargs)
        return wrapper
    return decorator

async def require_auth_security(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    """Require security-level authentication for endpoints"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # In a real implementation, you would verify the token here
    return {
        "user_id": 1,
        "token": credentials.credentials,
        "scopes": ["admin"]
    }
