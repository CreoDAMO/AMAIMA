import logging
import time
import os
import httpx
import base64
from typing import Optional, Dict, Any, List
from app.modules.nvidia_nim_client import get_model_for_domain, get_api_key

logger = logging.getLogger(__name__)

IMAGE_GEN_MODEL = "nvidia/sdxl-turbo"

async def generate_image(prompt: str, negative_prompt: str = "") -> Dict[str, Any]:
    start_time = time.time()
    api_key = get_api_key()
    
    if not api_key:
        logger.warning("NVIDIA_API_KEY not found, using simulation")
        return {
            "service": "image",
            "task": "generation",
            "model": IMAGE_GEN_MODEL,
            "image_url": "https://images.nvidia.com/placeholder-gen.png",
            "latency_ms": 0.1,
            "simulated": True
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    payload = {
        "text_prompts": [{"text": prompt}],
        "seed": 0,
        "sampler": "K_EULER_ANCESTRAL",
        "steps": 2
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo",
                headers=headers,
                json=payload,
            )
            
        if response.status_code == 200:
            data = response.json()
            artifacts = data.get("artifacts", [])
            if artifacts:
                image_base64 = artifacts[0].get("base64")
                return {
                    "service": "image",
                    "task": "generation",
                    "model": IMAGE_GEN_MODEL,
                    "image_url": f"data:image/png;base64,{image_base64}",
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "label": "Advanced Visual Generation Engine"
                }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")

    return {
        "service": "image",
        "task": "generation",
        "model": IMAGE_GEN_MODEL,
        "image_url": "https://images.nvidia.com/placeholder-gen.png",
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "error": "Failed to generate image"
    }

IMAGE_CAPABILITIES = {
    "models": [IMAGE_GEN_MODEL],
    "features": ["text_to_image", "image_to_image", "inpainting"],
}
