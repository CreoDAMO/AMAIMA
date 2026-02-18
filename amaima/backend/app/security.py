from fastapi import Security, HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

API_KEY_NAME = "X-API-Key"
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "default_secret_key_for_development")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    if api_key == API_SECRET_KEY:
        return {"id": "admin", "tier": "enterprise", "email": None}

    from app.billing import validate_api_key
    key_info = await validate_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return key_info


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.auth import decode_token, get_user_by_id
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(payload["sub"])
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def enforce_tier_limit(api_key_info: dict):
    if api_key_info.get("id") == "admin":
        return

    from app.billing import check_usage_limit
    usage = await check_usage_limit(api_key_info["id"], api_key_info["tier"])
    if not usage["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Monthly query limit reached",
                "tier": api_key_info["tier"],
                "limit": usage["limit"],
                "used": usage["current"],
                "upgrade_url": "/billing",
            },
        )
