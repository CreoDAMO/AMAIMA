"""
AMAIMA Video Generation Router
app/routers/video.py

Exposes Cosmos Predict 2.5 text-to-video as proper HTTP endpoints.
No video router or domain dispatch existed before — this is the entire
missing pipeline AMAIMA was hallucinating about.

Endpoints:
  POST /v1/video/generate           Text → base64 MP4 data URI (sync, blocks up to ~4min)
  POST /v1/video/generate/download  Text → raw MP4 file download
  POST /v1/video/transform          Video-to-video (prompt-guided transformation)
  GET  /v1/video/capabilities       Model info, limits, latency expectations

Registration in main.py:
  from app.routers.video import router as video_router
  app.include_router(video_router)

Domain dispatch in main.py process_query() — add this block:
  elif detected_domain == "video_gen":
      execution_result = await video_service.generate_video(request.query)
      output = execution_result.get("video_url")
"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.video_service import (
    generate_video,
    video_to_video,
    VIDEO_CAPABILITIES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/video", tags=["Video Generation — Cosmos Predict 2.5"])


# ── Request models ─────────────────────────────────────────────────────────────

class VideoGenerateRequest(BaseModel):
    prompt:        str = Field(
        ...,
        max_length=2000,
        description=(
            "Scene description for video generation. "
            "Keep under 300 words for best quality. "
            "Be specific: describe camera angle, motion, lighting, subjects."
        ),
    )
    output_format: str = Field(default="mp4")


class VideoTransformRequest(BaseModel):
    prompt:           str = Field(
        ...,
        max_length=2000,
        description="How to transform the source video",
    )
    source_video_b64: str = Field(
        ...,
        description="Base64-encoded source MP4 video bytes",
    )
    output_format:    str = Field(default="mp4")


# ── Generation endpoints ───────────────────────────────────────────────────────

@router.post("/generate")
async def api_generate_video(req: VideoGenerateRequest):
    """
    Generate a 5-second 720p video from a text prompt using Cosmos Predict 2.5.

    ⚠ This request holds the HTTP connection open while Cosmos generates.
    Typical generation time: 30–90 seconds.
    The response includes a base64 data:video/mp4 URI playable in a <video> tag.

    For production with many concurrent users, consider the async job pattern
    (submit → poll) listed in the backlog roadmap.
    """
    try:
        result = await generate_video(
            prompt=req.prompt,
            output_format=req.output_format,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Strip raw bytes for JSON serialization
    result.pop("video_bytes", None)
    return result


@router.post("/generate/download")
async def api_generate_video_download(req: VideoGenerateRequest):
    """
    Same as /generate but returns the raw MP4 binary for direct download.
    """
    try:
        result = await generate_video(
            prompt=req.prompt,
            output_format=req.output_format,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    video_bytes = result.get("video_bytes")
    if not video_bytes:
        # Fallback: decode from data URI
        import base64
        data_uri = result.get("video_data", "") or result.get("video_url", "")
        if "," in data_uri:
            video_bytes = base64.b64decode(data_uri.split(",", 1)[1])
        else:
            raise HTTPException(status_code=502, detail="No video data returned")

    return Response(
        content=video_bytes,
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="amaima_video.mp4"',
            "X-Latency-MS":        str(result.get("latency_ms", 0)),
            "X-Model":             str(result.get("model", "")),
            "X-Duration-S":        str(result.get("duration_s", 5)),
            "X-Resolution":        str(result.get("resolution", "720p")),
        },
    )


@router.post("/transform")
async def api_video_transform(req: VideoTransformRequest):
    """
    Transform an existing video with a new text prompt using Cosmos Video2World.
    source_video_b64 must be base64-encoded MP4 bytes (max ~50MB).

    ⚠ Same latency warning as /generate — holds connection for 30–90 seconds.
    """
    try:
        result = await video_to_video(
            prompt=req.prompt,
            source_video_b64=req.source_video_b64,
            output_format=req.output_format,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result.pop("video_bytes", None)
    return result


# ── Info endpoints ─────────────────────────────────────────────────────────────

@router.get("/capabilities")
async def get_capabilities():
    """Cosmos video generation capabilities, model info, and latency expectations."""
    return VIDEO_CAPABILITIES
