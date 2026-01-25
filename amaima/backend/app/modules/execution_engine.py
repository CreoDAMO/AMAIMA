from typing import Dict, Any
import time
import random
import asyncio

async def execute_model(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates a call to an external model API.
    """
    start_time = time.time()

    # Simulate network latency and processing time
    await asyncio.sleep(random.uniform(0.1, 0.5))

    end_time = time.time()

    return {
        "output": f"Mock response for model {decision['model']}",
        "actual_latency_ms": int((end_time - start_time) * 1000),
        "actual_cost_usd": random.uniform(0.001, 0.005),
    }
