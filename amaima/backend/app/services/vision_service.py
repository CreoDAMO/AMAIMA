import os
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False
    logger.info("OpenAI SDK not available; using httpx for NIM calls")

from app.modules.nvidia_nim_client import chat_completion, get_api_key, get_model_for_domain

COSMOS_MODEL = get_model_for_domain("vision", "primary")
COSMOS_VL_MODEL = get_model_for_domain("vision", "secondary")
COSMOS_PREDICT_MODEL = get_model_for_domain("vision", "world_model")
COSMOS_NIM_URL = os.getenv("COSMOS_NIM_URL", "https://integrate.api.nvidia.com/v1")


def get_cosmos_client():
    if HAS_OPENAI_SDK:
        api_key = get_api_key()
        if api_key:
            return OpenAI(base_url=COSMOS_NIM_URL, api_key=api_key)
    return None


async def cosmos_inference(
    query: str,
    media_path: Optional[str] = None,
    media_type: Optional[str] = None,
) -> Dict[str, Any]:
    start_time = time.time()

    messages = [
        {
            "role": "system",
            "content": "You are an advanced vision-language reasoning assistant specializing in physical AI, embodied reasoning, and spatio-temporal analysis. Use <think>reasoning</think><answer>conclusion</answer> format for structured responses."
        },
        {"role": "user", "content": query}
    ]

    if media_path and media_type:
        media_content = []
        if media_type == "video":
            media_content.append({"type": "video", "video": media_path, "fps": 4})
        elif media_type == "image":
            media_content.append({"type": "image", "image": media_path})
        media_content.append({"type": "text", "text": query})
        messages[1]["content"] = media_content # type: ignore

    try:
        api_messages = []
        for m in messages:
            if isinstance(m["content"], list):
                text_parts = [p["text"] for p in m["content"] if p.get("type") == "text"]
                combined_text = " ".join(text_parts) if text_parts else query
                if media_path and media_type:
                    combined_text = f"[{media_type.upper()} provided: {media_path}] {combined_text}"
                api_messages.append({"role": m["role"], "content": combined_text})
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})

        result = await chat_completion(
            model=COSMOS_MODEL,
            messages=api_messages,
            temperature=0.2,
            max_tokens=4096,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "service": "vision",
            "model": COSMOS_MODEL,
            "response": result.get("content", ""),
            "latency_ms": round(elapsed_ms, 2),
            "usage": result.get("usage", {}),
            "cost_usd": result.get("estimated_cost_usd", 0),
            "media_type": media_type or "text",
        }
    except Exception as e:
        # Log full exception details on the server, but do not return them to the client.
        logger.exception("Cosmos inference failed")
        return {
            "service": "vision",
            "model": COSMOS_MODEL,
            "response": "Vision service is currently unavailable. Please try again later.",
            "error": "vision_service_unavailable",
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
        query=f"Analyze the video scene: {query}. Describe what you observe, identify any safety concerns, and suggest appropriate actions.",
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
        COSMOS_MODEL: "Primary vision-language reasoning (Cosmos Reason 2)",
        COSMOS_VL_MODEL: "Multimodal understanding (Nemotron VL)",
        COSMOS_PREDICT_MODEL: "Future state prediction and video generation (Cosmos Predict 2.5)",
    },
}
