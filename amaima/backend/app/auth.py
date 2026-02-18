import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import asyncpg
from passlib.context import CryptContext
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def init_auth_tables():
    pool = await get_pool()
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            last_login_at TIMESTAMPTZ
        )
    """)
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            revoked BOOLEAN DEFAULT false
        )
    """)
    await pool.execute("""
        DO $$ BEGIN
            ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id);
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)
    logger.info("Auth tables initialized")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def register_user(email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()

    existing = await pool.fetchrow("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise ValueError("Email already registered")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    user_id = secrets.token_hex(12)
    password_hash = hash_password(password)

    await pool.execute(
        """INSERT INTO users (id, email, password_hash, display_name, role)
           VALUES ($1, $2, $3, $4, 'user')""",
        user_id, email, password_hash, display_name or email.split("@")[0]
    )

    access_token = create_access_token(user_id, email, "user")
    refresh_token = create_refresh_token(user_id)

    refresh_id = secrets.token_hex(8)
    refresh_hash = pwd_context.hash(refresh_token[:32])
    await pool.execute(
        """INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
           VALUES ($1, $2, $3, $4)""",
        refresh_id, user_id, refresh_hash,
        datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name or email.split("@")[0],
        "role": "user",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()

    user = await pool.fetchrow(
        "SELECT id, email, password_hash, display_name, role, is_active FROM users WHERE email = $1",
        email
    )

    if not user or not verify_password(password, user["password_hash"]):
        return None

    if not user["is_active"]:
        return None

    await pool.execute(
        "UPDATE users SET last_login_at = NOW() WHERE id = $1", user["id"]
    )

    access_token = create_access_token(user["id"], user["email"], user["role"])
    refresh_token = create_refresh_token(user["id"])

    refresh_id = secrets.token_hex(8)
    refresh_hash = pwd_context.hash(refresh_token[:32])
    await pool.execute(
        """INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
           VALUES ($1, $2, $3, $4)""",
        refresh_id, user["id"], refresh_hash,
        datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "user_id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "role": user["role"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(refresh_token_str: str) -> Optional[Dict[str, Any]]:
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        return None

    user_id = payload.get("sub")
    pool = await get_pool()

    user = await pool.fetchrow(
        "SELECT id, email, role, is_active FROM users WHERE id = $1", user_id
    )
    if not user or not user["is_active"]:
        return None

    new_access = create_access_token(user["id"], user["email"], user["role"])
    return {
        "access_token": new_access,
        "token_type": "bearer",
    }


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    user = await pool.fetchrow(
        """SELECT id, email, display_name, role, is_active, created_at, last_login_at
           FROM users WHERE id = $1""",
        user_id
    )
    if not user:
        return None
    return dict(user)


async def get_user_api_keys(user_id: str) -> list:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, key_prefix, tier, is_active, created_at
           FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC""",
        user_id
    )
    return [dict(r) for r in rows]


async def link_api_key_to_user(api_key_id: str, user_id: str):
    pool = await get_pool()
    await pool.execute(
        "UPDATE api_keys SET user_id = $1 WHERE id = $2", user_id, api_key_id
    )


async def list_all_users(limit: int = 100, offset: int = 0) -> list:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id, email, display_name, role, is_active, created_at, last_login_at
           FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2""",
        limit, offset
    )
    return [dict(r) for r in rows]


async def count_users() -> int:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) as cnt FROM users")
    return row["cnt"] if row else 0
