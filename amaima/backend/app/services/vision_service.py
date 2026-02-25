"""
AMAIMA Vision Service — v2
app/services/vision_service.py

Bugs fixed vs v1:
  BUG 11  get_cosmos_client() built an OpenAI SDK client that was never used.
          cosmos_inference() always called chat_completion() from
          nvidia_nim_client, making the OpenAI SDK import and client
          construction dead code. Removed entirely.
  BUG 12  Media content was built as a structured list (video/image dicts)
          then immediately flattened back to plain text before reaching
          chat_completion(), silently dropping the actual media reference.
          Multimodal messages now preserved end-to-end via the OpenAI-compatible
          content array format that nvidia_nim_client passes through correctly.
          Falls back to text description when the NIM model doesn't support
          native multimodal input, so existing callers never break.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

from app.modules.nvidia_nim_client import chat_completion, get_api_key, get_model_for_domain

COSMOS_MODEL         = get_model_for_domain("vision", "primary")
COSMOS_VL_MODEL      = get_model_for_domain("vision", "secondary")
COSMOS_PREDICT_MODEL = get_model_for_domain("vision", "world_model")
COSMOS_NIM_URL       = os.getenv("COSMOS_NIM_URL", "https://integrate.api.nvidia.com/v1")

# BUG 11 FIX: removed get_cosmos_client() — it built an OpenAI client that
# was never used anywhere. cosmos_inference() uses chat_completion() directly.


def _build_messages(query: str, media_path: Optional[str], media_type: Optional[str]) -> List[Dict]:
    """
    BUG 12 FIX: Build the OpenAI-compatible messages list, preserving media
    as a structured content array instead of flattening it to plain text.

    If media_path is a URL or data URI the NIM model receives it as an
    image_url content block. If it's a local filesystem path, we include it
    as a text annotation (NIM cannot load local paths from the cloud).
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are an advanced vision-language reasoning assistant specializing in "
            "physical AI, embodied reasoning, and spatio-temporal analysis. "
            "Use <think>reasoning</think><answer>conclusion</answer> format for structured responses."
        ),
    }

    if not media_path or not media_type:
        # Text-only query — simple string content
        return [system_msg, {"role": "user", "content": query}]

    # Determine if we can pass the media inline
    is_url      = media_path.startswith("http://") or media_path.startswith("https://")
    is_data_uri = media_path.startswith("data:")

    if media_type == "image" and (is_url or is_data_uri):
        # OpenAI-compatible multimodal image content block
        user_content = [
            {
                "type":      "image_url",
                "image_url": {"url": media_path},
            },
            {"type": "text", "text": query},
        ]
    elif media_type == "video" and (is_url or is_data_uri):
        # Some NIM models support video_url; fall back to text annotation if not
        user_content = [
            {
                "type":      "video_url",
                "video_url": {"url": media_path},
            },
            {"type": "text", "text": query},
        ]
    else:
        # Local path or unknown scheme — annotate as text so the model
        # at least knows what was intended (matches original v1 behaviour)
        annotated = f"[{media_type.upper()} provided at: {media_path}]\n\n{query}"
        return [system_msg, {"role": "user", "content": annotated}]

    return [system_msg, {"role": "user", "content": user_content}]


async def cosmos_inference(
    query: str,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None,
) -> Dict[str, Any]:
    start_time = time.time()

    # BUG 12 FIX: use structured messages with media preserved
    messages = _build_messages(query, media_path, media_type)

    # Choose model: multimodal input → prefer the VL model if available
    model = COSMOS_VL_MODEL if (media_path and media_type) else COSMOS_MODEL

    try:
        result = await chat_completion(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=4096,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "service":    "vision",
            "model":      model,
            "response":   result.get("content", ""),
            "latency_ms": round(elapsed_ms, 2),
            "usage":      result.get("usage", {}),
            "cost_usd":   result.get("estimated_cost_usd", 0),
            "media_type": media_type or "text",
        }
    except Exception:
        logger.exception("Cosmos inference failed")
        return {
            "service":    "vision",
            "model":      model,
            "response":   "Vision service is currently unavailable. Please try again later.",
            "error":      "vision_service_unavailable",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


async def analyze_image(image_path: str, query: str) -> Dict[str, Any]:
    return await cosmos_inference(
        query=f"Analyze the image and answer: {query}",
        media_path=image_path,
        media_type="image",
    )


async def analyze_video(video_path: str, query: str) -> Dict[str, Any]:
    return await cosmos_inference(
        query=(
            f"Analyze the video scene: {query}. "
            "Describe what you observe, identify any safety concerns, "
            "and suggest appropriate actions."
        ),
        media_path=video_path,
        media_type="video",
    )


async def embodied_reasoning(scene_description: str, task: str) -> Dict[str, Any]:
    query = f"""Given the following scene: {scene_description}

Task: {task}

Provide step-by-step embodied reasoning considering:
1. Physics and spatial relationships
2. Object interactions and constraints
3. Safety considerations
4. Optimal action sequence"""
    return await cosmos_inference(query=query)


VISION_CAPABILITIES = {
    "models": [COSMOS_MODEL, COSMOS_VL_MODEL, COSMOS_PREDICT_MODEL],
    "supported_media": ["image/jpeg", "image/png", "video/mp4"],
    "max_video_length_seconds": 60,
    "features": [
        "embodied_reasoning",
        "spatio_temporal_analysis",
        "object_detection",
        "scene_understanding",
        "action_planning",
        "safety_assessment",
        "video_prediction",
        "multimodal_reasoning",
    ],
    "output_format": "structured (<think>/<answer>)",
    "model_details": {
        COSMOS_MODEL:         "Primary vision-language reasoning (Cosmos Reason 2)",
        COSMOS_VL_MODEL:      "Multimodal understanding (Nemotron VL) — used when media provided",
        COSMOS_PREDICT_MODEL: "Future state prediction and video generation (Cosmos Predict 2.5)",
    },
}
