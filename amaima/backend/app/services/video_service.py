"""
AMAIMA Video Generation Service — v1
app/services/video_service.py

NEW FILE — no prior implementation existed.
This is what AMAIMA was hallucinating about when it claimed it could generate
video but returned nothing.

Wires to:
  TEXT-TO-VIDEO  — NVIDIA NIM nvidia/cosmos-predict2-5b
                   (Cosmos Predict 2.5 — already registered in vision_service
                    as COSMOS_PREDICT_MODEL; reused here for generation)
  VIDEO-TO-VIDEO — Same model with init_video payload

Cosmos generates 5-second 720p video from a text prompt.
The NIM endpoint is async: returns a job_id, not immediate bytes.
This service submits, polls, and returns the final MP4.

Capabilities:
  generate_video(prompt)              -> MP4 base64 data URI + metadata
  video_to_video(prompt, video_b64)   -> transformed MP4
  describe_capabilities()             -> manifest for the router/health endpoint
"""

import os
import io
import time
import base64
import logging
import asyncio
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

# ── NIM config ────────────────────────────────────────────────────────────────
_NIM_API_KEY = (
    os.getenv("NVIDIA_NIM_API_KEY") or
    os.getenv("NVIDIA_API_KEY") or
    ""
)

_GENAI_BASE  = "https://ai.api.nvidia.com/v1/genai"
_STATUS_BASE = "https://ai.api.nvidia.com/v1/status"

# Cosmos Predict 2.5 — same model registered in vision_service as world_model
VIDEO_MODEL = os.getenv("COSMOS_VIDEO_MODEL", "nvidia/cosmos-predict2-5b")

_SUBMIT_TIMEOUT = 30.0
_POLL_TIMEOUT   = 30.0
_POLL_INTERVAL  = 5.0    # seconds between status polls
_MAX_POLLS      = 48     # 48 × 5s = 4 min max wait


def _is_configured() -> bool:
    return bool(_NIM_API_KEY)


def _headers() -> Dict[str, str]:
    if not _NIM_API_KEY:
        raise EnvironmentError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Video generation requires a valid NVIDIA NIM API key."
        )
    return {
        "Authorization": f"Bearer {_NIM_API_KEY}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def _extract_video_b64(resp_json: Dict[str, Any]) -> Optional[str]:
    """
    Parse base64 video bytes from NIM response regardless of shape.
    Cosmos NIM shapes observed:
      Sync:  { "video": "<b64 MP4>" }
             { "videos": [ { "b64_mp4": "..." } ] }
             { "artifacts": [ { "base64": "..." } ] }
      Async: { "requestId": "...", "status": "pending" }  → returns None
    """
    for key in ("video", "video_b64", "mp4_b64"):
        raw = resp_json.get(key)
        if raw:
            return raw

    for arr_key in ("videos", "artifacts"):
        arr = resp_json.get(arr_key, [])
        if arr:
            item = arr[0]
            raw  = item.get("b64_mp4") or item.get("base64") or item.get("video")
            if raw:
                return raw

    return resp_json.get("b64_json")


def _extract_job_id(resp_json: Dict[str, Any]) -> Optional[str]:
    return (
        resp_json.get("requestId") or
        resp_json.get("job_id") or
        resp_json.get("id")
    )


async def _poll_job(job_id: str) -> Optional[str]:
    """
    Poll the NIM async status endpoint until the video is ready.
    Returns base64 video string, or None on timeout/failure.
    """
    url = f"{_STATUS_BASE}/{job_id}"
    for attempt in range(_MAX_POLLS):
        await asyncio.sleep(_POLL_INTERVAL)
        try:
            async with httpx.AsyncClient(timeout=_POLL_TIMEOUT) as client:
                resp = await client.get(url, headers=_headers())
                resp.raise_for_status()
                data = resp.json()

            status = data.get("status", "").lower()
            logger.debug(
                f"Cosmos video job {job_id} — poll {attempt + 1}/{_MAX_POLLS}: {status}"
            )

            if status in ("succeeded", "completed", "done"):
                video_b64 = _extract_video_b64(data)
                if video_b64:
                    return video_b64
                # Done status but no bytes yet — keep polling one more cycle
            elif status in ("failed", "error", "cancelled"):
                logger.error(f"Cosmos video job {job_id} reached terminal status: {status}")
                return None
            # "pending" / "running" — continue

        except Exception as e:
            logger.warning(f"Cosmos poll error (attempt {attempt + 1}): {e}")

    logger.error(f"Cosmos video job {job_id} timed out after {_MAX_POLLS} polls")
    return None


async def generate_video(
    prompt: str,
    output_format: str = "mp4",
    resolution: str = "720p",
) -> Dict[str, Any]:
    """
    Generate a 5-second video from a text prompt using Cosmos Predict 2.5.

    prompt: Scene description. Keep under 300 words for best quality.
    output_format: "mp4" (only option currently supported by Cosmos NIM).
    resolution: "720p" (1280×720) — fixed by the model.

    Returns:
      {
        "service":     "video",
        "task":        "generation",
        "model":       "nvidia/cosmos-predict2-5b",
        "video_data":  "data:video/mp4;base64,...",
        "video_url":   "data:video/mp4;base64,...",
        "video_bytes": <bytes>,
        "format":      "mp4",
        "duration_s":  5,
        "resolution":  "720p",
        "prompt":      "...",
        "latency_ms":  45000,
        "simulated":   False,
      }

    ⚠ Typical generation time: 30–90 seconds. This call blocks while polling.
    """
    start_time = time.time()

    if not _is_configured():
        return {
            "service":   "video",
            "error":     "unconfigured",
            "message":   "NVIDIA_NIM_API_KEY not set. Video generation requires a valid key.",
            "simulated": False,
        }

    # Trim to Cosmos word limit
    words = prompt.split()
    if len(words) > 290:
        prompt = " ".join(words[:290])
        logger.warning("Video prompt trimmed to 290 words for Cosmos model limit")

    payload = {
        "prompt":     prompt,
        "model":      VIDEO_MODEL,
        "num_frames": 121,       # ~5 seconds at 24fps
        "resolution": "720p",
    }

    try:
        async with httpx.AsyncClient(timeout=_SUBMIT_TIMEOUT) as client:
            resp = await client.post(
                f"{_GENAI_BASE}/{VIDEO_MODEL}",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            resp_json = resp.json()

        # Try sync response first
        video_b64 = _extract_video_b64(resp_json)

        if not video_b64:
            # Async path — get job_id and poll
            job_id = _extract_job_id(resp_json)
            if not job_id:
                raise RuntimeError(
                    f"Cosmos returned no video data and no job_id. "
                    f"Response keys: {list(resp_json.keys())}"
                )
            logger.info(f"Cosmos async video job submitted: {job_id} — polling…")
            video_b64 = await _poll_job(job_id)
            if not video_b64:
                raise RuntimeError(
                    f"Cosmos video job {job_id} completed but returned no video bytes"
                )

        video_bytes = base64.b64decode(video_b64)
        elapsed     = round((time.time() - start_time) * 1000, 2)
        data_uri    = f"data:video/mp4;base64,{video_b64}"

        logger.info(
            f"Video generated: {len(video_bytes) // 1024}KB "
            f"latency={elapsed / 1000:.1f}s model={VIDEO_MODEL}"
        )
        return {
            "service":     "video",
            "task":        "generation",
            "model":       VIDEO_MODEL,
            "video_data":  data_uri,
            "video_url":   data_uri,
            "video_bytes": video_bytes,
            "format":      output_format,
            "duration_s":  5,
            "resolution":  resolution,
            "prompt":      prompt,
            "latency_ms":  elapsed,
            "size_bytes":  len(video_bytes),
            "simulated":   False,
        }

    except httpx.HTTPStatusError as e:
        err = f"HTTP {e.response.status_code}: {e.response.text[:300]}"
        logger.error(f"Video generation failed: {err}")
        raise RuntimeError(f"NVIDIA NIM Cosmos returned {err}")
    except httpx.TimeoutException:
        raise RuntimeError(
            "Cosmos video submission timed out. "
            "Check NIM service availability and retry."
        )
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling Cosmos NIM: {e}")


async def video_to_video(
    prompt: str,
    source_video_b64: str,
    output_format: str = "mp4",
) -> Dict[str, Any]:
    """
    Transform an existing video guided by a new text prompt (Cosmos Video2World).
    source_video_b64: base64-encoded MP4 bytes.
    """
    start_time = time.time()

    if not _is_configured():
        return {
            "service":   "video",
            "error":     "unconfigured",
            "message":   "NVIDIA_NIM_API_KEY not set.",
            "simulated": False,
        }

    words = prompt.split()
    if len(words) > 290:
        prompt = " ".join(words[:290])

    payload = {
        "prompt":      prompt,
        "model":       VIDEO_MODEL,
        "init_video":  source_video_b64,
        "num_frames":  121,
        "resolution":  "720p",
    }

    try:
        async with httpx.AsyncClient(timeout=_SUBMIT_TIMEOUT) as client:
            resp = await client.post(
                f"{_GENAI_BASE}/{VIDEO_MODEL}",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            resp_json = resp.json()

        video_b64 = _extract_video_b64(resp_json)
        if not video_b64:
            job_id = _extract_job_id(resp_json)
            if not job_id:
                raise RuntimeError("No video data and no job_id in video2video response")
            video_b64 = await _poll_job(job_id)
            if not video_b64:
                raise RuntimeError("Video2Video job returned no bytes")

        video_bytes = base64.b64decode(video_b64)
        elapsed     = round((time.time() - start_time) * 1000, 2)
        data_uri    = f"data:video/mp4;base64,{video_b64}"

        return {
            "service":     "video",
            "task":        "video-to-video",
            "model":       VIDEO_MODEL,
            "video_data":  data_uri,
            "video_url":   data_uri,
            "video_bytes": video_bytes,
            "format":      output_format,
            "latency_ms":  elapsed,
            "size_bytes":  len(video_bytes),
            "simulated":   False,
        }

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"NVIDIA NIM Cosmos v2v HTTP {e.response.status_code}: {e.response.text[:300]}")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling Cosmos NIM: {e}")


VIDEO_CAPABILITIES = {
    "model":          VIDEO_MODEL,
    "features":       ["text_to_video", "video_to_video"],
    "output_formats": ["mp4"],
    "duration_s":     5,
    "resolution":     "720p (1280×720)",
    "prompt_limit":   "< 300 words",
    "typical_latency_s": "30–90s",
    "simulated":      False,
    "note": (
        "Video generation queues on NVIDIA NIM. "
        "Response is held open while polling for completion."
    ),
}
