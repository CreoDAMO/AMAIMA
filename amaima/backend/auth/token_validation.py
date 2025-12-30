# backend/auth/token_validation.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
from redis import Redis

# JWT configuration
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Redis for token blacklisting
redis_client = Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

async def validate_token(token: str, expected_type: str = "access") -> dict:
    """
    Validate JWT token and return payload.
    
    This function performs the following checks:
    1. Verify token signature using RS256
    2. Check token type claim
    3. Verify token hasn't expired
    4. Check token blacklist
    5. Extract and return claims
    """
    
    try:
        # Decode token (verification happens automatically with complete=True)
        payload = jwt.decode(
            token,
            key=await get_public_key(),
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["sub", "exp", "iat", "type"]
            }
        )
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}"
            )
        
        # Check blacklist for refresh tokens
        if token_type == "refresh":
            jti = payload.get("jti")
            if redis_client.sismember("blacklisted_tokens", jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
        
        # Verify user still exists and is active
        user = await get_user_by_id(payload.get("sub"))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    """
    Dependency for protected endpoints.
    Returns the authenticated user object.
    """
    
    payload = await validate_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
