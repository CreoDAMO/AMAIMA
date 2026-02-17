import asyncpg
import hashlib
import logging
import csv
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

from .billing import get_pool

logger = logging.getLogger(__name__)


def generate_cache_key(query_text: str, model: str) -> str:
    """Generate a deterministic MD5 hash key for cache."""
    combined = f"{query_text}:{model}"
    return hashlib.md5(combined.encode()).hexdigest()


async def record_benchmark(
    model: str,
    query_complexity: str,
    domain: str,
    latency_ms: int,
    tokens_input: int,
    tokens_output: int,
    cost_usd: float,
    success: bool,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a benchmark entry for a model query."""
    pool = await get_pool()
    
    try:
        row = await pool.fetchrow(
            """INSERT INTO model_benchmarks 
               (model, query_complexity, domain, latency_ms, tokens_input, 
                tokens_output, cost_usd, success, error_message, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
               RETURNING id, created_at""",
            model, query_complexity, domain, latency_ms, tokens_input,
            tokens_output, Decimal(str(cost_usd)), success, error_message
        )
        logger.info(f"Benchmark recorded: {model} - {query_complexity} - {latency_ms}ms")
        return dict(row)
    except Exception as e:
        logger.error(f"Error recording benchmark: {e}")
        raise


async def get_benchmark_stats(model: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """Get aggregated benchmark statistics."""
    pool = await get_pool()
    
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        if model:
            rows = await pool.fetch(
                """SELECT 
                   model,
                   COUNT(*) as total_queries,
                   AVG(latency_ms) as avg_latency,
                   MIN(latency_ms) as min_latency,
                   MAX(latency_ms) as max_latency,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate,
                   AVG(cost_usd) as avg_cost,
                   SUM(tokens_input) as total_tokens_input,
                   SUM(tokens_output) as total_tokens_output
                   FROM model_benchmarks
                   WHERE model = $1 AND created_at >= $2
                   GROUP BY model""",
                model, since
            )
        else:
            rows = await pool.fetch(
                """SELECT 
                   model,
                   COUNT(*) as total_queries,
                   AVG(latency_ms) as avg_latency,
                   MIN(latency_ms) as min_latency,
                   MAX(latency_ms) as max_latency,
                   SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate,
                   AVG(cost_usd) as avg_cost,
                   SUM(tokens_input) as total_tokens_input,
                   SUM(tokens_output) as total_tokens_output
                   FROM model_benchmarks
                   WHERE created_at >= $1
                   GROUP BY model
                   ORDER BY avg_latency ASC""",
                since
            )
        
        stats = []
        for row in rows:
            stats.append({
                "model": row["model"],
                "total_queries": row["total_queries"],
                "avg_latency_ms": float(row["avg_latency"]) if row["avg_latency"] else 0,
                "min_latency_ms": row["min_latency"],
                "max_latency_ms": row["max_latency"],
                "success_rate": float(row["success_rate"]) if row["success_rate"] else 0,
                "avg_cost_usd": float(row["avg_cost"]) if row["avg_cost"] else 0,
                "total_tokens_input": row["total_tokens_input"],
                "total_tokens_output": row["total_tokens_output"],
            })
        
        logger.info(f"Retrieved benchmark stats for {len(stats)} models (last {days} days)")
        return {"stats": stats, "days": days}
    except Exception as e:
        logger.error(f"Error getting benchmark stats: {e}")
        raise


async def get_benchmark_leaderboard() -> Dict[str, Any]:
    """Get models ranked by performance (latency-based)."""
    pool = await get_pool()
    
    try:
        rows = await pool.fetch(
            """SELECT 
               model,
               COUNT(*) as total_queries,
               AVG(latency_ms) as avg_latency,
               SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate,
               AVG(cost_usd) as avg_cost
               FROM model_benchmarks
               WHERE created_at >= NOW() - INTERVAL '7 days'
               GROUP BY model
               ORDER BY avg_latency ASC""",
        )
        
        leaderboard = []
        for idx, row in enumerate(rows, 1):
            leaderboard.append({
                "rank": idx,
                "model": row["model"],
                "total_queries": row["total_queries"],
                "avg_latency_ms": float(row["avg_latency"]) if row["avg_latency"] else 0,
                "success_rate": float(row["success_rate"]) if row["success_rate"] else 0,
                "avg_cost_usd": float(row["avg_cost"]) if row["avg_cost"] else 0,
            })
        
        logger.info(f"Retrieved leaderboard with {len(leaderboard)} models")
        return {"leaderboard": leaderboard, "period": "7_days"}
    except Exception as e:
        logger.error(f"Error getting benchmark leaderboard: {e}")
        raise


async def get_benchmark_timeseries(model: str, days: int = 7) -> Dict[str, Any]:
    """Get latency data points over time for a specific model."""
    pool = await get_pool()
    
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        rows = await pool.fetch(
            """SELECT 
               DATE(created_at) as date,
               AVG(latency_ms) as avg_latency,
               MIN(latency_ms) as min_latency,
               MAX(latency_ms) as max_latency,
               COUNT(*) as query_count,
               SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
               FROM model_benchmarks
               WHERE model = $1 AND created_at >= $2
               GROUP BY DATE(created_at)
               ORDER BY date ASC""",
            model, since
        )
        
        datapoints = []
        for row in rows:
            datapoints.append({
                "date": row["date"].isoformat(),
                "avg_latency_ms": float(row["avg_latency"]) if row["avg_latency"] else 0,
                "min_latency_ms": row["min_latency"],
                "max_latency_ms": row["max_latency"],
                "query_count": row["query_count"],
                "success_rate": float(row["success_rate"]) if row["success_rate"] else 0,
            })
        
        logger.info(f"Retrieved timeseries for {model} ({days} days): {len(datapoints)} datapoints")
        return {"model": model, "days": days, "datapoints": datapoints}
    except Exception as e:
        logger.error(f"Error getting benchmark timeseries: {e}")
        raise


async def get_cached_response(query_text: str, model: str) -> Optional[Dict[str, Any]]:
    """Get cached response for a query, incrementing hit count."""
    pool = await get_pool()
    cache_key = generate_cache_key(query_text, model)
    
    try:
        # Check if cache entry exists and is not expired
        row = await pool.fetchrow(
            """SELECT cache_key, response_text, tokens_used, hit_count
               FROM response_cache
               WHERE cache_key = $1 AND expires_at > NOW()""",
            cache_key
        )
        
        if not row:
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
        
        # Increment hit count
        await pool.execute(
            """UPDATE response_cache
               SET hit_count = hit_count + 1
               WHERE cache_key = $1""",
            cache_key
        )
        
        logger.info(f"Cache hit for key: {cache_key}")
        return {
            "response_text": row["response_text"],
            "tokens_used": row["tokens_used"],
            "hit_count": row["hit_count"] + 1,
        }
    except Exception as e:
        logger.error(f"Error getting cached response: {e}")
        raise


async def set_cached_response(
    query_text: str,
    model: str,
    response_text: str,
    tokens_used: int,
    ttl_hours: int = 24,
) -> Dict[str, Any]:
    """Store response in cache."""
    pool = await get_pool()
    cache_key = generate_cache_key(query_text, model)
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    try:
        await pool.execute(
            """INSERT INTO response_cache 
               (cache_key, query_text, model, response_text, tokens_used, 
                hit_count, created_at, expires_at)
               VALUES ($1, $2, $3, $4, $5, 0, NOW(), $6)
               ON CONFLICT (cache_key)
               DO UPDATE SET response_text = $4, tokens_used = $5, 
                             expires_at = $6, hit_count = 0""",
            cache_key, query_text, model, response_text, tokens_used, expires_at
        )
        
        logger.info(f"Cached response for key: {cache_key} (TTL: {ttl_hours}h)")
        return {
            "cache_key": cache_key,
            "ttl_hours": ttl_hours,
            "expires_at": expires_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error setting cached response: {e}")
        raise


async def clear_expired_cache() -> Dict[str, Any]:
    """Delete expired cache entries."""
    pool = await get_pool()
    
    try:
        result = await pool.execute(
            """DELETE FROM response_cache
               WHERE expires_at <= NOW()"""
        )
        
        # Parse the result to get affected rows
        deleted_count = int(result.split()[-1]) if result else 0
        logger.info(f"Cleared {deleted_count} expired cache entries")
        
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Error clearing expired cache: {e}")
        raise


async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics (hit rate, total entries, space saved)."""
    pool = await get_pool()
    
    try:
        # Get overall cache stats
        stats = await pool.fetchrow(
            """SELECT 
               COUNT(*) as total_entries,
               SUM(hit_count) as total_hits,
               SUM(LENGTH(response_text)) as total_bytes,
               AVG(hit_count) as avg_hit_count,
               MAX(hit_count) as max_hit_count
               FROM response_cache
               WHERE expires_at > NOW()"""
        )
        
        # Calculate hit rate
        all_requests = await pool.fetchrow(
            """SELECT 
               COUNT(*) as total_entries,
               SUM(hit_count) as total_hits
               FROM response_cache
               WHERE expires_at > NOW()"""
        )
        
        total_entries = stats["total_entries"] if stats["total_entries"] else 0
        total_hits = (all_requests["total_hits"] or 0) if all_requests else 0
        total_requests = total_entries + total_hits
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        total_bytes = stats["total_bytes"] or 0
        
        logger.info(f"Cache stats: {total_entries} entries, {hit_rate:.2f}% hit rate")
        
        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "hit_rate_percent": round(hit_rate, 2),
            "total_bytes": total_bytes,
            "avg_hit_count": float(stats["avg_hit_count"]) if stats["avg_hit_count"] else 0,
            "max_hit_count": stats["max_hit_count"],
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise


async def export_usage_data(
    api_key_id: str,
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Any:
    """Export usage data for an API key as JSON dict or CSV string."""
    pool = await get_pool()
    
    try:
        # Parse dates if provided
        where_clause = "WHERE api_key_id = $1"
        params = [api_key_id]
        
        if start_date:
            where_clause += " AND created_at >= $2"
            params.append(start_date)
        
        if end_date:
            where_clause += f" AND created_at <= ${len(params) + 1}"
            params.append(end_date)
        
        # Get usage events
        rows = await pool.fetch(
            f"""SELECT endpoint, model_used, tokens_estimated, latency_ms, 
                      status_code, created_at
               FROM usage_events
               {where_clause}
               ORDER BY created_at DESC""",
            *params
        )
        
        logger.info(f"Exported {len(rows)} usage records for API key {api_key_id}")
        
        if format == "json":
            return {
                "api_key_id": api_key_id,
                "total_records": len(rows),
                "start_date": start_date,
                "end_date": end_date,
                "events": [
                    {
                        "endpoint": row["endpoint"],
                        "model_used": row["model_used"],
                        "tokens_estimated": row["tokens_estimated"],
                        "latency_ms": row["latency_ms"],
                        "status_code": row["status_code"],
                        "created_at": row["created_at"].isoformat(),
                    }
                    for row in rows
                ],
            }
        elif format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["created_at", "endpoint", "model_used", "tokens_estimated", "latency_ms", "status_code"]
            )
            writer.writeheader()
            
            for row in rows:
                writer.writerow({
                    "created_at": row["created_at"].isoformat(),
                    "endpoint": row["endpoint"],
                    "model_used": row["model_used"],
                    "tokens_estimated": row["tokens_estimated"],
                    "latency_ms": row["latency_ms"],
                    "status_code": row["status_code"],
                })
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        logger.error(f"Error exporting usage data: {e}")
        raise


async def export_benchmarks_data(
    model: Optional[str] = None,
    format: str = "json",
    days: int = 30,
) -> Any:
    """Export benchmark data as JSON dict or CSV string."""
    pool = await get_pool()
    
    try:
        since = datetime.utcnow() - timedelta(days=days)
        
        where_clause = "WHERE created_at >= $1"
        params: list = [since]
        
        if model:
            where_clause += " AND model = $2"
            params.append(model)
        
        rows = await pool.fetch(
            f"""SELECT model, query_complexity, domain, latency_ms, 
                      tokens_input, tokens_output, cost_usd, success, 
                      error_message, created_at
               FROM model_benchmarks
               {where_clause}
               ORDER BY created_at DESC""",
            *params
        )
        
        logger.info(f"Exported {len(rows)} benchmark records (last {days} days)")
        
        if format == "json":
            return {
                "model": model,
                "days": days,
                "total_records": len(rows),
                "benchmarks": [
                    {
                        "model": row["model"],
                        "query_complexity": row["query_complexity"],
                        "domain": row["domain"],
                        "latency_ms": row["latency_ms"],
                        "tokens_input": row["tokens_input"],
                        "tokens_output": row["tokens_output"],
                        "cost_usd": float(row["cost_usd"]),
                        "success": row["success"],
                        "error_message": row["error_message"],
                        "created_at": row["created_at"].isoformat(),
                    }
                    for row in rows
                ],
            }
        elif format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["created_at", "model", "query_complexity", "domain", 
                           "latency_ms", "tokens_input", "tokens_output", "cost_usd", "success", "error_message"]
            )
            writer.writeheader()
            
            for row in rows:
                writer.writerow({
                    "created_at": row["created_at"].isoformat(),
                    "model": row["model"],
                    "query_complexity": row["query_complexity"],
                    "domain": row["domain"],
                    "latency_ms": row["latency_ms"],
                    "tokens_input": row["tokens_input"],
                    "tokens_output": row["tokens_output"],
                    "cost_usd": float(row["cost_usd"]),
                    "success": row["success"],
                    "error_message": row["error_message"],
                })
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        logger.error(f"Error exporting benchmark data: {e}")
        raise
