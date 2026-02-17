from typing import Dict, Any
import time
import random
import asyncio
import logging

logger = logging.getLogger(__name__)


async def execute_model(decision: Dict[str, Any]) -> Dict[str, Any]:
    from .nvidia_nim_client import is_configured, get_model_for_complexity, chat_completion

    start_time = time.time()
    complexity_level = decision.get("complexity_level", "SIMPLE")
    query_hash = decision.get("query_hash", "unknown")
    original_query = decision.get("_original_query", "")

    if decision.get("simulated", True):
        await asyncio.sleep(random.uniform(0.05, 0.15))
        elapsed = (time.time() - start_time) * 1000
        return {
            "output": "Simulation only - no execution.",
            "actual_latency_ms": int(elapsed),
            "actual_cost_usd": 0.0,
        }

    if not is_configured():
        await asyncio.sleep(random.uniform(0.05, 0.15))
        elapsed = (time.time() - start_time) * 1000
        return {
            "output": "NVIDIA API key not configured. Set the NVIDIA_API_KEY environment variable to enable real AI inference.",
            "actual_latency_ms": int(elapsed),
            "actual_cost_usd": 0.0,
        }

    router_model = decision.get("model", "")
    from .nvidia_nim_client import NVIDIA_MODELS
    if router_model in NVIDIA_MODELS:
        nim_model = router_model
    else:
        nim_model = get_model_for_complexity(complexity_level)

    messages = [
        {
            "role": "system",
            "content": (
                "You are AMAIMA, an Advanced Multimodal AI assistant. "
                "Provide clear, accurate, and helpful responses. "
                "When appropriate, structure your response with headings, bullet points, or code blocks."
            ),
        },
        {"role": "user", "content": original_query},
    ]

    try:
        result = await chat_completion(
            model=nim_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )

        return {
            "output": result["content"],
            "actual_latency_ms": int(result["latency_ms"]),
            "actual_cost_usd": result["estimated_cost_usd"],
        }

    except Exception as e:
        logger.error(f"NVIDIA NIM execution failed: {e}")
        elapsed = (time.time() - start_time) * 1000
        return {
            "output": "AI inference error: An internal error occurred while processing your request.",
            "actual_latency_ms": int(elapsed),
            "actual_cost_usd": 0.0,
        }
