import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import asyncpg
import bcrypt
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

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
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await pool.execute("""
        DO $$ BEGIN
            ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id);
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)

    admin_email = "admin@amaima.xyz"
    existing_admin = await pool.fetchrow("SELECT id FROM users WHERE email = $1", admin_email)
    if not existing_admin:
        admin_id = secrets.token_hex(12)
        admin_pw = os.getenv("ADMIN_DEFAULT_PASSWORD", "AMAIMAadmin2026!")
        admin_hash = hash_password(admin_pw)
        await pool.execute(
            """INSERT INTO users (id, email, password_hash, display_name, role)
               VALUES ($1, $2, $3, $4, 'admin')""",
            admin_id, admin_email, admin_hash, "AMAIMA Admin"
        )
        logger.info("Default admin user created: %s", admin_email)
    else:
        await pool.execute("UPDATE users SET role = 'admin' WHERE email = $1 AND role != 'admin'", admin_email)

    logger.info("Auth tables initialized")


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


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
    refresh_hash = hash_password(refresh_token[:32])
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
    refresh_hash = hash_password(refresh_token[:32])
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


async def request_password_reset(email: str) -> Optional[str]:
    pool = await get_pool()
    user = await pool.fetchrow("SELECT id, email, is_active FROM users WHERE email = $1", email)
    if not user or not user["is_active"]:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_id = secrets.token_hex(8)
    token_hash = hash_password(raw_token[:32])

    await pool.execute(
        "UPDATE password_reset_tokens SET used = true WHERE user_id = $1 AND used = false",
        user["id"]
    )

    await pool.execute(
        """INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
           VALUES ($1, $2, $3, $4)""",
        token_id, user["id"], token_hash,
        datetime.utcnow() + timedelta(hours=1)
    )

    return f"{token_id}:{raw_token}"


async def reset_password(token: str, new_password: str) -> bool:
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")

    pool = await get_pool()

    parts = token.split(":", 1)
    if len(parts) == 2:
        token_id, raw_token = parts
        row = await pool.fetchrow(
            """SELECT id, user_id, token_hash, expires_at FROM password_reset_tokens
               WHERE id = $1 AND used = false AND expires_at > NOW()""",
            token_id
        )
        if row and verify_password(raw_token[:32], row["token_hash"]):
            matched_row = row
        else:
            matched_row = None
    else:
        rows = await pool.fetch(
            """SELECT id, user_id, token_hash, expires_at FROM password_reset_tokens
               WHERE used = false AND expires_at > NOW()
               ORDER BY created_at DESC LIMIT 10"""
        )
        matched_row = None
        for row in rows:
            try:
                if verify_password(token[:32], row["token_hash"]):
                    matched_row = row
                    break
            except Exception:
                continue

    if not matched_row:
        return False

    new_hash = hash_password(new_password)
    await pool.execute(
        "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2",
        new_hash, matched_row["user_id"]
    )
    await pool.execute(
        "UPDATE password_reset_tokens SET used = true WHERE id = $1",
        matched_row["id"]
    )
    await pool.execute(
        "UPDATE refresh_tokens SET revoked = true WHERE user_id = $1",
        matched_row["user_id"]
    )

    return True
