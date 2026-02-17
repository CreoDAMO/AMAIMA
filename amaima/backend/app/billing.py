import asyncpg
import hashlib
import secrets
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

API_KEY_HASH_SALT = b"amaima_api_key_salt_v1"
API_KEY_HASH_ITERATIONS = 200_000

TIER_LIMITS = {
    "community": {
        "queries_per_month": 1000,
        "name": "Community",
        "description": "Free tier - 1,000 queries/month",
    },
    "production": {
        "queries_per_month": 10000,
        "name": "Production",
        "description": "Production tier - 10,000 queries/month",
    },
    "enterprise": {
        "queries_per_month": -1,
        "name": "Enterprise",
        "description": "Enterprise tier - Unlimited queries",
    },
}

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


def hash_api_key(key: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        key.encode("utf-8"),
        API_KEY_HASH_SALT,
        API_KEY_HASH_ITERATIONS,
    )
    return dk.hex()


async def create_api_key(email: Optional[str] = None, tier: str = "community") -> Dict[str, Any]:
    pool = await get_pool()
    key_id = secrets.token_hex(8)
    raw_key = f"amaima_{secrets.token_hex(24)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]

    await pool.execute(
        """INSERT INTO api_keys (id, key_hash, key_prefix, user_email, tier)
           VALUES ($1, $2, $3, $4, $5)""",
        key_id, key_hash, key_prefix, email, tier
    )

    return {
        "id": key_id,
        "api_key": raw_key,
        "prefix": key_prefix,
        "tier": tier,
        "email": email,
    }


async def validate_api_key(raw_key: str) -> Optional[Dict[str, Any]]:
    pool = await get_pool()
    key_hash = hash_api_key(raw_key)

    row = await pool.fetchrow(
        """SELECT id, key_prefix, user_email, tier, stripe_customer_id,
                  stripe_subscription_id, is_active
           FROM api_keys WHERE key_hash = $1""",
        key_hash
    )

    if not row or not row["is_active"]:
        return None

    tier = row["tier"]
    if row["stripe_subscription_id"]:
        sub = await pool.fetchrow(
            "SELECT status FROM stripe.subscriptions WHERE id = $1",
            row["stripe_subscription_id"]
        )
        if sub and sub["status"] in ("active", "trialing"):
            pass
        else:
            tier = "community"

    return {
        "id": row["id"],
        "email": row["user_email"],
        "tier": tier,
        "stripe_customer_id": row["stripe_customer_id"],
        "stripe_subscription_id": row["stripe_subscription_id"],
    }


async def check_usage_limit(api_key_id: str, tier: str) -> Dict[str, Any]:
    pool = await get_pool()
    month = datetime.utcnow().strftime("%Y-%m")

    row = await pool.fetchrow(
        "SELECT query_count FROM monthly_usage WHERE api_key_id = $1 AND month = $2",
        api_key_id, month
    )

    current_count = row["query_count"] if row else 0
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["community"])["queries_per_month"]

    if limit == -1:
        return {"allowed": True, "current": current_count, "limit": -1, "remaining": -1}

    return {
        "allowed": current_count < limit,
        "current": current_count,
        "limit": limit,
        "remaining": max(0, limit - current_count),
    }


async def record_usage(api_key_id: str, endpoint: str, model_used: str = "",
                       tokens_estimated: int = 0, latency_ms: int = 0, status_code: int = 200):
    pool = await get_pool()
    month = datetime.utcnow().strftime("%Y-%m")

    await pool.execute(
        """INSERT INTO usage_events (api_key_id, endpoint, model_used, tokens_estimated, latency_ms, status_code)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        api_key_id, endpoint, model_used, tokens_estimated, latency_ms, status_code
    )

    await pool.execute(
        """INSERT INTO monthly_usage (api_key_id, month, query_count, total_tokens)
           VALUES ($1, $2, 1, $3)
           ON CONFLICT (api_key_id, month)
           DO UPDATE SET query_count = monthly_usage.query_count + 1,
                         total_tokens = monthly_usage.total_tokens + $3""",
        api_key_id, month, tokens_estimated
    )


async def get_usage_stats(api_key_id: str) -> Dict[str, Any]:
    pool = await get_pool()
    month = datetime.utcnow().strftime("%Y-%m")

    monthly = await pool.fetchrow(
        "SELECT query_count, total_tokens FROM monthly_usage WHERE api_key_id = $1 AND month = $2",
        api_key_id, month
    )

    key_info = await pool.fetchrow(
        "SELECT tier, user_email, stripe_customer_id FROM api_keys WHERE id = $1",
        api_key_id
    )

    tier = key_info["tier"] if key_info else "community"
    tier_info = TIER_LIMITS.get(tier, TIER_LIMITS["community"])

    return {
        "api_key_id": api_key_id,
        "tier": tier,
        "tier_name": tier_info["name"],
        "month": month,
        "queries_used": monthly["query_count"] if monthly else 0,
        "queries_limit": tier_info["queries_per_month"],
        "tokens_used": monthly["total_tokens"] if monthly else 0,
        "email": key_info["user_email"] if key_info else None,
        "stripe_customer_id": key_info["stripe_customer_id"] if key_info else None,
    }


async def update_api_key_tier(api_key_id: str, tier: str, stripe_customer_id: Optional[str] = None,
                               stripe_subscription_id: Optional[str] = None):
    pool = await get_pool()
    await pool.execute(
        """UPDATE api_keys SET tier = $1, stripe_customer_id = $2,
                  stripe_subscription_id = $3, updated_at = NOW()
           WHERE id = $4""",
        tier, stripe_customer_id, stripe_subscription_id, api_key_id
    )


async def list_api_keys(email: Optional[str] = None) -> list:
    pool = await get_pool()
    if email:
        rows = await pool.fetch(
            "SELECT id, key_prefix, user_email, tier, is_active, created_at FROM api_keys WHERE user_email = $1 ORDER BY created_at DESC",
            email
        )
    else:
        rows = await pool.fetch(
            "SELECT id, key_prefix, user_email, tier, is_active, created_at FROM api_keys ORDER BY created_at DESC LIMIT 50"
        )
    return [dict(r) for r in rows]
