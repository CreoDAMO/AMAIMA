import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def get_admin_analytics() -> Dict[str, Any]:
    pool = await get_pool()
    now = datetime.utcnow()
    month = now.strftime("%Y-%m")

    total_users = await pool.fetchval("SELECT COUNT(*) FROM users") or 0
    total_api_keys = await pool.fetchval("SELECT COUNT(*) FROM api_keys") or 0
    active_api_keys = await pool.fetchval(
        "SELECT COUNT(*) FROM api_keys WHERE is_active = true"
    ) or 0

    monthly_queries = await pool.fetchval(
        "SELECT COALESCE(SUM(query_count), 0) FROM monthly_usage WHERE month = $1",
        month
    ) or 0
    monthly_tokens = await pool.fetchval(
        "SELECT COALESCE(SUM(total_tokens), 0) FROM monthly_usage WHERE month = $1",
        month
    ) or 0

    tier_dist = await pool.fetch(
        "SELECT tier, COUNT(*) as cnt FROM api_keys WHERE is_active = true GROUP BY tier"
    )
    tier_distribution = {row["tier"]: row["cnt"] for row in tier_dist}

    daily_usage = await pool.fetch(
        """SELECT DATE(created_at) as day, COUNT(*) as queries, COALESCE(SUM(tokens_estimated), 0) as tokens
           FROM usage_events
           WHERE created_at >= $1
           GROUP BY DATE(created_at) ORDER BY day""",
        now - timedelta(days=30)
    )
    daily_data = [
        {"date": str(row["day"]), "queries": row["queries"], "tokens": row["tokens"]}
        for row in daily_usage
    ]

    model_usage = await pool.fetch(
        """SELECT model_used, COUNT(*) as cnt, COALESCE(AVG(latency_ms), 0) as avg_latency
           FROM usage_events
           WHERE created_at >= $1 AND model_used != ''
           GROUP BY model_used ORDER BY cnt DESC LIMIT 20""",
        now - timedelta(days=30)
    )
    model_data = [
        {"model": row["model_used"], "count": row["cnt"], "avg_latency_ms": round(float(row["avg_latency"]), 1)}
        for row in model_usage
    ]

    endpoint_usage = await pool.fetch(
        """SELECT endpoint, COUNT(*) as cnt
           FROM usage_events
           WHERE created_at >= $1
           GROUP BY endpoint ORDER BY cnt DESC""",
        now - timedelta(days=30)
    )
    endpoint_data = [{"endpoint": row["endpoint"], "count": row["cnt"]} for row in endpoint_usage]

    avg_latency = await pool.fetchval(
        "SELECT COALESCE(AVG(latency_ms), 0) FROM usage_events WHERE created_at >= $1",
        now - timedelta(days=30)
    ) or 0

    top_users = await pool.fetch(
        """SELECT ak.user_email as email, ak.tier, mu.query_count, mu.total_tokens
           FROM monthly_usage mu
           JOIN api_keys ak ON ak.id = mu.api_key_id
           WHERE mu.month = $1
           ORDER BY mu.query_count DESC LIMIT 10""",
        month
    )
    top_users_data = [
        {
            "email": row["email"] or "unknown",
            "tier": row["tier"],
            "queries": row["query_count"],
            "tokens": row["total_tokens"],
        }
        for row in top_users
    ]

    revenue_estimate = (
        tier_distribution.get("production", 0) * 49 +
        tier_distribution.get("enterprise", 0) * 299
    )

    return {
        "overview": {
            "total_users": total_users,
            "total_api_keys": total_api_keys,
            "active_api_keys": active_api_keys,
            "monthly_queries": monthly_queries,
            "monthly_tokens": monthly_tokens,
            "avg_latency_ms": round(float(avg_latency), 1),
            "estimated_mrr_usd": revenue_estimate,
        },
        "tier_distribution": tier_distribution,
        "daily_usage": daily_data,
        "model_usage": model_data,
        "endpoint_usage": endpoint_data,
        "top_users": top_users_data,
        "month": month,
    }


async def get_system_health() -> Dict[str, Any]:
    pool = await get_pool()
    now = datetime.utcnow()

    db_ok = True
    try:
        await pool.fetchval("SELECT 1")
    except Exception:
        db_ok = False

    recent_errors = await pool.fetchval(
        """SELECT COUNT(*) FROM usage_events
           WHERE status_code >= 400 AND created_at >= $1""",
        now - timedelta(hours=1)
    ) or 0

    recent_total = await pool.fetchval(
        """SELECT COUNT(*) FROM usage_events WHERE created_at >= $1""",
        now - timedelta(hours=1)
    ) or 0

    error_rate = (recent_errors / recent_total * 100) if recent_total > 0 else 0

    queries_per_minute = await pool.fetchval(
        """SELECT COUNT(*) FROM usage_events WHERE created_at >= $1""",
        now - timedelta(minutes=5)
    ) or 0
    qpm = round(queries_per_minute / 5, 1)

    from app.modules.nvidia_nim_client import is_configured, get_cache_stats
    cache_stats = get_cache_stats()

    return {
        "status": "healthy" if db_ok and error_rate < 10 else "degraded",
        "database": {"connected": db_ok},
        "nvidia_nim": {"configured": is_configured()},
        "cache": cache_stats,
        "error_rate_pct": round(error_rate, 2),
        "queries_per_minute": qpm,
        "recent_errors_1h": recent_errors,
        "timestamp": now.isoformat(),
    }


async def get_all_users_with_usage(limit: int = 50, offset: int = 0) -> list:
    pool = await get_pool()
    month = datetime.utcnow().strftime("%Y-%m")

    rows = await pool.fetch(
        """SELECT u.id, u.email, u.display_name, u.role, u.is_active, u.created_at, u.last_login_at,
                  COALESCE(
                      (SELECT SUM(mu.query_count) FROM monthly_usage mu
                       JOIN api_keys ak ON ak.id = mu.api_key_id
                       WHERE ak.user_id = u.id AND mu.month = $1), 0
                  ) as monthly_queries,
                  (SELECT COUNT(*) FROM api_keys ak WHERE ak.user_id = u.id) as api_key_count
           FROM users u
           ORDER BY u.created_at DESC
           LIMIT $2 OFFSET $3""",
        month, limit, offset
    )
    return [dict(r) for r in rows]
