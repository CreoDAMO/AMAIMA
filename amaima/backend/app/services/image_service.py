import logging
import time
import os
import httpx
import base64
from typing import Dict, Any

logger = logging.getLogger(__name__)

IMAGE_GEN_MODEL = "nvidia/sdxl-turbo"
NIM_IMAGE_URL = "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo"


def _get_api_key() -> str:
    key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not key:
        raise EnvironmentError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Image generation requires a valid NVIDIA NIM API key."
        )
    return key


async def generate_image(
    prompt: str,
    negative_prompt: str = "",
    steps: int = 2,
    seed: int = 0,
) -> Dict[str, Any]:
    """
    Generates an image from a text prompt using SDXL-Turbo on NVIDIA NIM.
    Returns a base64 data URI suitable for inline <img> rendering.

    SDXL-Turbo is optimized for 2–4 step generation; steps=2 is the default
    for fast turnaround without quality loss.
    """
    start_time = time.time()
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "text_prompts": [
            {"text": prompt, "weight": 1.0}
        ],
        "seed": seed,
        "sampler": "K_EULER_ANCESTRAL",
        "steps": steps,
        "cfg_scale": 1.5,  # Low CFG for turbo mode
    }

    if negative_prompt:
        payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                NIM_IMAGE_URL,
                headers=headers,
                json=payload,
            )

        if response.status_code == 200:
            data = response.json()
            artifacts = data.get("artifacts", [])

            if not artifacts:
                raise RuntimeError(
                    "NVIDIA NIM SDXL-Turbo returned 200 but 'artifacts' list is empty. "
                    "The prompt may have been filtered or the model returned no output."
                )

            image_b64 = artifacts[0].get("base64")
            if not image_b64:
                raise RuntimeError(
                    "NVIDIA NIM SDXL-Turbo artifact missing 'base64' field. "
                    f"Artifact keys present: {list(artifacts[0].keys())}"
                )

            return {
                "service": "image",
                "task": "generation",
                "model": IMAGE_GEN_MODEL,
                "image_data": f"data:image/png;base64,{image_b64}",
                "label": "Advanced Visual Generation Engine",
                "prompt": prompt,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "simulated": False,
            }

        # Non-200 — surface the real error with status and body
        error_detail = response.text[:500]
        logger.error(f"SDXL-Turbo NIM returned {response.status_code}: {error_detail}")
        raise RuntimeError(
            f"NVIDIA NIM SDXL-Turbo returned HTTP {response.status_code}: {error_detail}"
        )

    except httpx.TimeoutException:
        raise RuntimeError(
            "NVIDIA NIM SDXL-Turbo request timed out after 60 seconds. "
            "Image generation typically takes 5–15 seconds; a timeout suggests a network issue."
        )
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling NVIDIA NIM SDXL-Turbo: {e}")


IMAGE_CAPABILITIES = {
    "models": [IMAGE_GEN_MODEL],
    "features": ["text_to_image"],
    "default_steps": 2,
    "max_steps": 4,
    "simulated": False,
}
