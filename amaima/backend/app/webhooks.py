import asyncio
import asyncpg
import httpx
import json
import hmac
import hashlib
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.billing import get_pool

logger = logging.getLogger(__name__)

# Default events for webhooks
DEFAULT_WEBHOOK_EVENTS = ["usage.limit_warning", "usage.limit_reached"]
WEBHOOK_TIMEOUT = 5  # seconds


# ============================================================================
# WEBHOOK FUNCTIONS
# ============================================================================

async def create_webhook(
    api_key_id: str,
    url: str,
    events: Optional[List[str]] = None,
    org_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new webhook endpoint for an API key.
    
    Args:
        api_key_id: The API key ID to associate with the webhook
        url: The webhook URL to send notifications to
        events: List of events to subscribe to (default: usage alerts)
        org_id: Organization ID (optional)
    
    Returns:
        Dictionary containing webhook details
    """
    pool = await get_pool()
    webhook_id = secrets.token_hex(8)
    secret = secrets.token_hex(16)
    events_list = events or DEFAULT_WEBHOOK_EVENTS
    
    try:
        await pool.execute(
            """INSERT INTO webhook_endpoints
               (id, api_key_id, org_id, url, events, secret, is_active, failure_count, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())""",
            webhook_id, api_key_id, org_id, url, events_list, secret, True, 0
        )
        
        logger.info(f"Created webhook {webhook_id} for API key {api_key_id}")
        
        return {
            "id": webhook_id,
            "api_key_id": api_key_id,
            "org_id": org_id,
            "url": url,
            "events": events_list,
            "secret": secret,
            "is_active": True,
            "failure_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise


async def list_webhooks(api_key_id: str) -> List[Dict[str, Any]]:
    """
    List all webhooks for an API key.
    
    Args:
        api_key_id: The API key ID to list webhooks for
    
    Returns:
        List of webhook endpoint dictionaries
    """
    pool = await get_pool()
    
    try:
        rows = await pool.fetch(
            """SELECT id, api_key_id, org_id, url, events, secret, is_active,
                      failure_count, last_triggered_at, created_at
               FROM webhook_endpoints
               WHERE api_key_id = $1
               ORDER BY created_at DESC""",
            api_key_id
        )
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to list webhooks for {api_key_id}: {e}")
        return []


async def delete_webhook(webhook_id: str) -> bool:
    """
    Delete a webhook and its associated events.
    
    Args:
        webhook_id: The webhook ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    pool = await get_pool()
    
    try:
        # Delete cascading events first
        await pool.execute(
            "DELETE FROM webhook_events WHERE webhook_id = $1",
            webhook_id
        )
        
        # Delete the webhook endpoint
        result = await pool.execute(
            "DELETE FROM webhook_endpoints WHERE id = $1",
            webhook_id
        )
        
        logger.info(f"Deleted webhook {webhook_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {e}")
        return False


async def trigger_webhook(
    webhook_id: str,
    event_type: str,
    payload: Dict[str, Any]
) -> bool:
    """
    Trigger a webhook by sending an HTTP POST request.
    Records the event and handles failures.
    
    Args:
        webhook_id: The webhook ID to trigger
        event_type: The type of event (e.g., 'usage.limit_warning')
        payload: The JSON payload to send
    
    Returns:
        True if successful, False otherwise
    """
    pool = await get_pool()
    
    try:
        # Get webhook details
        webhook = await pool.fetchrow(
            """SELECT id, url, secret, failure_count, is_active
               FROM webhook_endpoints
               WHERE id = $1""",
            webhook_id
        )
        
        if not webhook or not webhook["is_active"]:
            logger.warning(f"Webhook {webhook_id} not found or inactive")
            return False
        
        # Prepare the webhook request
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": _generate_signature(payload, webhook["secret"]),
        }
        
        # Send the webhook request
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            response = await client.post(
                webhook["url"],
                json=payload,
                headers=headers
            )
        
        # Record the event
        status = "sent" if response.status_code == 200 else "failed"
        
        await pool.execute(
            """INSERT INTO webhook_events
               (webhook_id, event_type, payload, status, response_code, created_at)
               VALUES ($1, $2, $3, $4, $5, NOW())""",
            webhook_id, event_type, json.dumps(payload), status, response.status_code
        )
        
        # Update last triggered timestamp
        await pool.execute(
            """UPDATE webhook_endpoints
               SET last_triggered_at = NOW()
               WHERE id = $1""",
            webhook_id
        )
        
        if status == "sent":
            # Reset failure count on success
            await pool.execute(
                "UPDATE webhook_endpoints SET failure_count = 0 WHERE id = $1",
                webhook_id
            )
            logger.info(f"Successfully triggered webhook {webhook_id} for {event_type}")
            return True
        else:
            # Increment failure count
            new_failure_count = webhook["failure_count"] + 1
            await pool.execute(
                "UPDATE webhook_endpoints SET failure_count = $1 WHERE id = $2",
                new_failure_count, webhook_id
            )
            
            # Disable webhook after 5 consecutive failures
            if new_failure_count >= 5:
                await pool.execute(
                    "UPDATE webhook_endpoints SET is_active = FALSE WHERE id = $1",
                    webhook_id
                )
                logger.warning(f"Webhook {webhook_id} disabled after 5 failures")
            
            logger.error(f"Failed to trigger webhook {webhook_id}: HTTP {response.status_code}")
            return False
            
    except asyncio.TimeoutError:
        logger.error(f"Webhook {webhook_id} request timed out")
        await _increment_webhook_failure(webhook_id)
        return False
    except Exception as e:
        logger.error(f"Error triggering webhook {webhook_id}: {e}")
        await _increment_webhook_failure(webhook_id)
        return False


async def check_usage_alerts(
    api_key_id: str,
    current_usage: int,
    limit: int
) -> None:
    """
    Check if usage hits 80% or 100% of limit and trigger matching webhooks.
    
    Args:
        api_key_id: The API key ID
        current_usage: Current usage count
        limit: Usage limit (-1 for unlimited)
    """
    pool = await get_pool()
    
    if limit == -1:  # Unlimited tier
        return
    
    usage_percentage = (current_usage / limit) * 100
    event_type = None
    
    if usage_percentage >= 100:
        event_type = "usage.limit_reached"
    elif usage_percentage >= 80:
        event_type = "usage.limit_warning"
    else:
        return
    
    try:
        # Get webhooks subscribed to this event
        webhooks = await pool.fetch(
            """SELECT id FROM webhook_endpoints
               WHERE api_key_id = $1
               AND is_active = TRUE
               AND $2 = ANY(events)""",
            api_key_id, event_type
        )
        
        # Trigger all matching webhooks
        payload = {
            "event": event_type,
            "api_key_id": api_key_id,
            "current_usage": current_usage,
            "limit": limit,
            "percentage": usage_percentage,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        for webhook in webhooks:
            await trigger_webhook(webhook["id"], event_type, payload)
            
        logger.info(f"Checked usage alerts for {api_key_id}: {usage_percentage}%")
        
    except Exception as e:
        logger.error(f"Error checking usage alerts for {api_key_id}: {e}")


# ============================================================================
# ROUTING RULES FUNCTIONS
# ============================================================================

async def create_routing_rule(
    api_key_id: str,
    name: str,
    preferred_model: str,
    domain: Optional[str] = None,
    min_complexity: Optional[str] = None,
    max_complexity: Optional[str] = None,
    fallback_model: Optional[str] = None,
    priority: int = 0,
    org_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new routing rule for an API key (Enterprise feature).
    
    Args:
        api_key_id: The API key ID
        name: Descriptive name for the rule
        preferred_model: The preferred model to route to
        domain: Optional domain filter
        min_complexity: Optional minimum query complexity
        max_complexity: Optional maximum query complexity
        fallback_model: Optional fallback model if preferred is unavailable
        priority: Rule priority (higher = more important)
        org_id: Organization ID (optional)
    
    Returns:
        Dictionary containing routing rule details
    """
    pool = await get_pool()
    rule_id = secrets.token_hex(8)
    
    try:
        await pool.execute(
            """INSERT INTO routing_rules
               (id, api_key_id, org_id, name, domain, min_complexity, max_complexity,
                preferred_model, fallback_model, is_active, priority, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())""",
            rule_id, api_key_id, org_id, name, domain, min_complexity, max_complexity,
            preferred_model, fallback_model, True, priority
        )
        
        logger.info(f"Created routing rule {rule_id} for API key {api_key_id}")
        
        return {
            "id": rule_id,
            "api_key_id": api_key_id,
            "org_id": org_id,
            "name": name,
            "domain": domain,
            "min_complexity": min_complexity,
            "max_complexity": max_complexity,
            "preferred_model": preferred_model,
            "fallback_model": fallback_model,
            "is_active": True,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to create routing rule: {e}")
        raise


async def list_routing_rules(api_key_id: str) -> List[Dict[str, Any]]:
    """
    List all active routing rules for an API key, ordered by priority.
    
    Args:
        api_key_id: The API key ID
    
    Returns:
        List of routing rule dictionaries
    """
    pool = await get_pool()
    
    try:
        rows = await pool.fetch(
            """SELECT id, api_key_id, org_id, name, domain, min_complexity, max_complexity,
                      preferred_model, fallback_model, is_active, priority, created_at
               FROM routing_rules
               WHERE api_key_id = $1 AND is_active = TRUE
               ORDER BY priority DESC, created_at ASC""",
            api_key_id
        )
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to list routing rules for {api_key_id}: {e}")
        return []


async def get_matching_rule(
    api_key_id: str,
    domain: Optional[str] = None,
    complexity: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the best matching routing rule for a query.
    
    Args:
        api_key_id: The API key ID
        domain: The domain/subject of the query (optional)
        complexity: The complexity level of the query (optional)
    
    Returns:
        The matching rule dictionary, or None if no match
    """
    pool = await get_pool()
    
    try:
        # Build the query to find matching rules
        # Rules are matched based on domain and complexity filters
        query = """
            SELECT id, api_key_id, org_id, name, domain, min_complexity, max_complexity,
                   preferred_model, fallback_model, is_active, priority, created_at
            FROM routing_rules
            WHERE api_key_id = $1 AND is_active = TRUE
        """
        params = [api_key_id]
        param_idx = 2
        
        if domain:
            query += f" AND (domain IS NULL OR domain = ${param_idx})"
            params.append(domain)
            param_idx += 1
        else:
            query += " AND domain IS NULL"
        
        if complexity:
            query += f""" AND (min_complexity IS NULL OR min_complexity <= ${param_idx})
                           AND (max_complexity IS NULL OR max_complexity >= ${param_idx + 1})"""
            params.extend([complexity, complexity])
            param_idx += 2
        
        query += " ORDER BY priority DESC LIMIT 1"
        
        rule = await pool.fetchrow(query, *params)
        
        if rule:
            logger.info(f"Found matching rule {rule['id']} for API key <redacted>")
            return dict(rule)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting matching rule for API key <redacted>: {e}")
        return None


async def update_routing_rule(rule_id: str, **kwargs) -> bool:
    """
    Update a routing rule with new values.
    
    Args:
        rule_id: The rule ID to update
        **kwargs: Fields to update (name, domain, min_complexity, max_complexity,
                 preferred_model, fallback_model, is_active, priority)
    
    Returns:
        True if successful, False otherwise
    """
    pool = await get_pool()
    
    # Allowed fields to update
    allowed_fields = {
        "name", "domain", "min_complexity", "max_complexity",
        "preferred_model", "fallback_model", "is_active", "priority"
    }
    
    # Filter kwargs to only allowed fields
    update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not update_fields:
        logger.warning(f"No valid fields to update for rule {rule_id}")
        return False
    
    try:
        # Build the UPDATE query dynamically
        set_clause = ", ".join([f"{k} = ${i}" for i, k in enumerate(update_fields.keys(), 1)])
        query = f"UPDATE routing_rules SET {set_clause} WHERE id = ${len(update_fields) + 1}"
        
        values = list(update_fields.values()) + [rule_id]
        
        await pool.execute(query, *values)
        
        logger.info(f"Updated routing rule {rule_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update routing rule {rule_id}: {e}")
        return False


async def delete_routing_rule(rule_id: str) -> bool:
    """
    Delete a routing rule.
    
    Args:
        rule_id: The rule ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    pool = await get_pool()
    
    try:
        await pool.execute(
            "DELETE FROM routing_rules WHERE id = $1",
            rule_id
        )
        
        logger.info(f"Deleted routing rule {rule_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete routing rule {rule_id}: {e}")
        return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_signature(payload: Dict[str, Any], secret: str) -> str:
    """
    Generate a webhook signature for verification.
    
    Args:
        payload: The payload dictionary
        secret: The webhook secret
    
    Returns:
        Hex-encoded signature
    """
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


async def _increment_webhook_failure(webhook_id: str) -> None:
    """
    Increment the failure count for a webhook and disable if needed.
    
    Args:
        webhook_id: The webhook ID
    """
    pool = await get_pool()
    
    try:
        webhook = await pool.fetchrow(
            "SELECT failure_count FROM webhook_endpoints WHERE id = $1",
            webhook_id
        )
        
        if webhook:
            new_count = webhook["failure_count"] + 1
            
            # Record the event with pending status
            await pool.execute(
                "UPDATE webhook_endpoints SET failure_count = $1 WHERE id = $2",
                new_count, webhook_id
            )
            
            if new_count >= 5:
                await pool.execute(
                    "UPDATE webhook_endpoints SET is_active = FALSE WHERE id = $1",
                    webhook_id
                )
                logger.warning(f"Webhook {webhook_id} disabled after {new_count} failures")
    except Exception as e:
        logger.error(f"Error incrementing webhook failure count: {e}")
