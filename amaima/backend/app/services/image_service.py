"""
AMAIMA Image Generation Service — v2
app/services/image_service.py

Bugs fixed vs v1:
  BUG 4  Only SDXL-Turbo was wired — no fallback to full SDXL. Added model
         cascade: sdxl-turbo → stable-diffusion-xl → stable-diffusion-3-medium.
  BUG 5  No inpainting, img2img, or variant generation. All three added.
  BUG 6  No format selection — always returned PNG. Now accepts jpeg/png/webp
         and converts via Pillow if available.
  BUG 7  No raw download path. generate_image() now also returns image_bytes
         so callers can write the file directly without re-decoding base64.
"""

import logging
import time
import os
import io
import asyncio
import httpx
import base64
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

IMAGE_GEN_MODEL    = "nvidia/sdxl-turbo"
IMAGE_GEN_FALLBACK = "stabilityai/stable-diffusion-xl"
IMAGE_GEN_FALLBACK2 = "stabilityai/stable-diffusion-3-medium"

NIM_IMAGE_BASE = "https://ai.api.nvidia.com/v1/genai"

# Model-specific endpoint URLs
_MODEL_URLS = {
    "nvidia/sdxl-turbo":                         f"{NIM_IMAGE_BASE}/stabilityai/sdxl-turbo",
    "stabilityai/stable-diffusion-xl":           f"{NIM_IMAGE_BASE}/stabilityai/stable-diffusion-xl",
    "stabilityai/stable-diffusion-3-medium":     f"{NIM_IMAGE_BASE}/stabilityai/stable-diffusion-3-medium",
}

# BUG 4 FIX: ordered cascade — fast turbo first, full SDXL as fallback
_MODEL_CASCADE = [
    "nvidia/sdxl-turbo",
    "stabilityai/stable-diffusion-xl",
    "stabilityai/stable-diffusion-3-medium",
]


def _get_api_key() -> str:
    key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not key:
        raise EnvironmentError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Image generation requires a valid NVIDIA NIM API key."
        )
    return key


def _is_configured() -> bool:
    return bool(os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY"))


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def _extract_image_b64(data: Dict[str, Any]) -> Optional[str]:
    """Parse base64 image from NIM response regardless of shape."""
    artifacts = data.get("artifacts", [])
    if artifacts:
        b64 = artifacts[0].get("base64")
        if b64:
            return b64

    images = data.get("images", [])
    if images:
        b64 = images[0].get("b64_json") or images[0].get("base64")
        if b64:
            return b64

    return data.get("b64_json") or data.get("base64")


def _convert_format(image_bytes: bytes, target_fmt: str) -> bytes:
    """BUG 6 FIX: Convert raw PNG bytes to the requested output format."""
    fmt = target_fmt.lower().strip(".")
    if fmt in ("png",):
        return image_bytes  # already PNG from NIM
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        out = io.BytesIO()
        pil_fmt = {"jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}.get(fmt, "PNG")
        if pil_fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(out, format=pil_fmt, quality=95)
        return out.getvalue()
    except ImportError:
        logger.warning("Pillow not installed — returning raw PNG regardless of requested format")
        return image_bytes


async def generate_image(
    prompt: str,
    negative_prompt: str = "",
    steps: int = 2,
    seed: int = 0,
    output_format: str = "png",
    width: int = 1024,
    height: int = 1024,
    cfg_scale: float = 1.5,
) -> Dict[str, Any]:
    """
    Generate an image from a text prompt.

    BUG 4 FIX: tries SDXL-Turbo first, falls back to full SDXL, then SD3.
    BUG 6 FIX: respects output_format (png, jpeg, webp).
    BUG 7 FIX: returns image_bytes for direct file download.
    """
    start_time = time.time()

    last_error = None
    for model in _MODEL_CASCADE:
        url = _MODEL_URLS[model]
        # SDXL-Turbo: max 4 steps, low CFG. Full SDXL: 20-50 steps, higher CFG.
        is_turbo = "turbo" in model
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "seed":         seed,
            "sampler":      "K_EULER_ANCESTRAL" if is_turbo else "K_DPM_2_ANCESTRAL",
            "steps":        min(steps, 4) if is_turbo else max(steps, 20),
            "cfg_scale":    1.5 if is_turbo else 7.5,
        }
        if negative_prompt:
            payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})
        if not is_turbo:
            payload["width"]  = width
            payload["height"] = height

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(url, headers=_headers(), json=payload)

            if response.status_code == 200:
                data = response.json()
                image_b64 = _extract_image_b64(data)
                if not image_b64:
                    raise RuntimeError(
                        f"NIM {model} returned 200 but no image data. "
                        f"Keys: {list(data.keys())}"
                    )

                # BUG 6+7 FIX
                raw_bytes      = base64.b64decode(image_b64)
                output_bytes   = _convert_format(raw_bytes, output_format)
                fmt            = output_format.lower().strip(".")
                data_uri       = f"data:image/{fmt};base64,{base64.b64encode(output_bytes).decode()}"

                return {
                    "service":     "image",
                    "task":        "generation",
                    "model":       model,
                    "image_data":  data_uri,   # backward compat key
                    "image_url":   data_uri,   # new unified key
                    "image_bytes": output_bytes,
                    "format":      fmt,
                    "label":       "Advanced Visual Generation Engine",
                    "prompt":      prompt,
                    "latency_ms":  round((time.time() - start_time) * 1000, 2),
                    "simulated":   False,
                }

            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            logger.warning(f"Image model {model} returned {last_error} — trying fallback")

        except httpx.TimeoutException:
            last_error = f"{model} timed out"
            logger.warning(f"{last_error} — trying fallback")
        except httpx.RequestError as e:
            last_error = f"Network error on {model}: {e}"
            logger.warning(f"{last_error} — trying fallback")
        except RuntimeError as e:
            last_error = str(e)
            logger.warning(f"{model}: {last_error} — trying fallback")

    raise RuntimeError(
        f"All image generation models failed. Last error: {last_error}"
    )


# ── BUG 5 FIX: inpainting, img2img, variant generation ─────────────────────

async def inpaint_image(
    prompt: str,
    image_b64: str,
    mask_b64: str,
    output_format: str = "png",
    negative_prompt: str = "",
) -> Dict[str, Any]:
    """Fill a masked region of an image guided by a text prompt."""
    start_time = time.time()
    url = _MODEL_URLS["stabilityai/stable-diffusion-xl"]
    payload = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "init_image":   image_b64,
        "mask_image":   mask_b64,
        "cfg_scale":    7.0,
        "steps":        30,
        "mode":         "image-to-image",
        "image_strength": 0.35,
    }
    if negative_prompt:
        payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(url, headers=_headers(), json=payload)
        response.raise_for_status()
        image_b64_out = _extract_image_b64(response.json())
        if not image_b64_out:
            raise RuntimeError("No image in inpaint response")
        raw_bytes    = base64.b64decode(image_b64_out)
        output_bytes = _convert_format(raw_bytes, output_format)
        fmt          = output_format.lower().strip(".")
        return {
            "service":     "image",
            "task":        "inpaint",
            "model":       IMAGE_GEN_FALLBACK,
            "image_data":  f"data:image/{fmt};base64,{base64.b64encode(output_bytes).decode()}",
            "image_url":   f"data:image/{fmt};base64,{base64.b64encode(output_bytes).decode()}",
            "image_bytes": output_bytes,
            "format":      fmt,
            "latency_ms":  round((time.time() - start_time) * 1000, 2),
        }
    except Exception as e:
        raise RuntimeError(f"Inpainting failed: {e}")


async def image_to_image(
    prompt: str,
    source_image_b64: str,
    strength: float = 0.65,
    output_format: str = "png",
    negative_prompt: str = "",
) -> Dict[str, Any]:
    """Transform an existing image with a new text prompt."""
    start_time = time.time()
    url = _MODEL_URLS["stabilityai/stable-diffusion-xl"]
    payload = {
        "text_prompts":   [{"text": prompt, "weight": 1.0}],
        "init_image":     source_image_b64,
        "cfg_scale":      7.5,
        "steps":          30,
        "mode":           "image-to-image",
        "image_strength": 1.0 - strength,
    }
    if negative_prompt:
        payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(url, headers=_headers(), json=payload)
        response.raise_for_status()
        image_b64_out = _extract_image_b64(response.json())
        if not image_b64_out:
            raise RuntimeError("No image in img2img response")
        raw_bytes    = base64.b64decode(image_b64_out)
        output_bytes = _convert_format(raw_bytes, output_format)
        fmt          = output_format.lower().strip(".")
        return {
            "service":     "image",
            "task":        "image-to-image",
            "model":       IMAGE_GEN_FALLBACK,
            "image_data":  f"data:image/{fmt};base64,{base64.b64encode(output_bytes).decode()}",
            "image_url":   f"data:image/{fmt};base64,{base64.b64encode(output_bytes).decode()}",
            "image_bytes": output_bytes,
            "format":      fmt,
            "latency_ms":  round((time.time() - start_time) * 1000, 2),
        }
    except Exception as e:
        raise RuntimeError(f"Image-to-image failed: {e}")


async def generate_image_variants(
    prompt: str,
    n: int = 4,
    output_format: str = "png",
) -> Dict[str, Any]:
    """Generate up to 4 concurrent image variants with different seeds."""
    n     = min(max(1, n), 4)
    seeds = [0, 42, 1337, 9999][:n]

    tasks   = [generate_image(prompt=prompt, seed=s, output_format=output_format) for s in seeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    variants = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            variants.append({"index": i, "error": str(r)})
        else:
            r.pop("image_bytes", None)   # strip bytes for JSON response
            variants.append({"index": i, **r})

    return {
        "service":  "image",
        "task":     "variants",
        "variants": variants,
        "count":    len([v for v in variants if "error" not in v]),
        "prompt":   prompt,
    }


IMAGE_CAPABILITIES = {
    "models": _MODEL_CASCADE,
    "features": ["text_to_image", "inpainting", "image_to_image", "variants"],
    "output_formats": ["png", "jpeg", "webp"],
    "default_steps":  2,
    "max_steps":      50,
    "simulated":      False,
    "model_details": {
        "nvidia/sdxl-turbo":                     "Fast 2-4 step generation (primary)",
        "stabilityai/stable-diffusion-xl":       "Full quality SDXL (fallback + inpaint/img2img)",
        "stabilityai/stable-diffusion-3-medium": "SD3 (second fallback)",
    },
}
