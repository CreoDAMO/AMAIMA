"""
AMAIMA Image Generation Router
app/routers/image.py

Exposes SDXL image generation as proper HTTP endpoints.
The image_gen domain was already handled inline in main.py's
process_query() but there was no dedicated router, no download endpoint,
no inpainting, and no variant generation.

Endpoints:
  POST /v1/image/generate           Text → base64 PNG data URI
  POST /v1/image/generate/download  Text → raw image file download
  POST /v1/image/variants           Text → up to 4 concurrent variants
  POST /v1/image/edit               Image-to-image transformation
  POST /v1/image/inpaint            Masked region inpainting
  GET  /v1/image/capabilities       Supported models, formats, features

Registration in main.py:
  from app.routers.image import router as image_router
  app.include_router(image_router)
"""

import base64
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.image_service import (
    generate_image,
    generate_image_variants,
    inpaint_image,
    image_to_image,
    IMAGE_CAPABILITIES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/image", tags=["Image Generation — SDXL"])


# ── Request models ─────────────────────────────────────────────────────────────

class ImageGenerateRequest(BaseModel):
    prompt:          str   = Field(..., description="Text description of the image to generate")
    negative_prompt: str   = Field(default="",    description="Elements to exclude from the image")
    steps:           int   = Field(default=2,     ge=2,  le=50)
    seed:            int   = Field(default=0,     description="0 = random seed")
    output_format:   str   = Field(default="png", description="Output format: png, jpeg, webp")
    width:           int   = Field(default=1024,  ge=512, le=2048)
    height:          int   = Field(default=1024,  ge=512, le=2048)


class ImageVariantsRequest(BaseModel):
    prompt:        str = Field(...)
    n:             int = Field(default=4, ge=1, le=4)
    output_format: str = Field(default="png")


class ImageEditRequest(BaseModel):
    prompt:          str   = Field(..., description="Description of the desired result")
    image_b64:       str   = Field(..., description="Base64-encoded source image (PNG or JPEG)")
    strength:        float = Field(default=0.65, ge=0.1, le=1.0,
                                   description="How much to change the image (0=none, 1=complete)")
    negative_prompt: str   = Field(default="")
    output_format:   str   = Field(default="png")


class ImageInpaintRequest(BaseModel):
    prompt:          str = Field(..., description="What to fill the masked region with")
    image_b64:       str = Field(..., description="Base64-encoded source image")
    mask_b64:        str = Field(..., description="Base64 mask: white=replace, black=keep")
    negative_prompt: str = Field(default="")
    output_format:   str = Field(default="png")


# ── Generation endpoints ───────────────────────────────────────────────────────

@router.post("/generate")
async def api_generate_image(req: ImageGenerateRequest):
    """
    Generate an image from a text prompt using SDXL-Turbo (cascade: SDXL → SD3 on failure).
    Returns a base64 data URI (data:image/png;base64,...) renderable directly in an
    <img> tag or AMAIMA's chat image renderer.
    """
    try:
        result = await generate_image(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            steps=req.steps,
            seed=req.seed,
            output_format=req.output_format,
            width=req.width,
            height=req.height,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Strip raw bytes — not JSON-serializable
    result.pop("image_bytes", None)
    return result


@router.post("/generate/download")
async def api_generate_image_download(req: ImageGenerateRequest):
    """
    Same as /generate but returns the raw image binary for direct download.
    Content-Type is set based on output_format (png, jpeg, webp).
    """
    try:
        result = await generate_image(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            steps=req.steps,
            seed=req.seed,
            output_format=req.output_format,
            width=req.width,
            height=req.height,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    image_bytes = result.get("image_bytes")
    if not image_bytes:
        # Fallback: decode from data URI if bytes weren't returned
        data_uri = result.get("image_data", "")
        if "," in data_uri:
            image_bytes = base64.b64decode(data_uri.split(",", 1)[1])
        else:
            raise HTTPException(status_code=502, detail="No image data returned")

    fmt  = req.output_format.lower().strip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp"}.get(fmt, "image/png")

    return Response(
        content=image_bytes,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="amaima_image.{fmt}"',
            "X-Latency-MS":        str(result.get("latency_ms", 0)),
            "X-Model":             str(result.get("model", "")),
        },
    )


@router.post("/variants")
async def api_image_variants(req: ImageVariantsRequest):
    """
    Generate up to 4 image variants concurrently with different random seeds.
    Each variant is generated independently; partial successes are returned.
    """
    try:
        result = await generate_image_variants(
            prompt=req.prompt,
            n=req.n,
            output_format=req.output_format,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return result


@router.post("/edit")
async def api_image_edit(req: ImageEditRequest):
    """
    Transform an existing image guided by a new text prompt (image-to-image).
    source image must be base64-encoded PNG or JPEG.
    strength=0.65 preserves ~35% of the original; strength=0.9 rewrites almost entirely.
    """
    try:
        result = await image_to_image(
            prompt=req.prompt,
            source_image_b64=req.image_b64,
            strength=req.strength,
            output_format=req.output_format,
            negative_prompt=req.negative_prompt,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result.pop("image_bytes", None)
    return result


@router.post("/inpaint")
async def api_image_inpaint(req: ImageInpaintRequest):
    """
    Fill a masked region of an image using SDXL inpainting.
    mask_b64: white pixels = area to replace, black pixels = area to keep.
    """
    try:
        result = await inpaint_image(
            prompt=req.prompt,
            image_b64=req.image_b64,
            mask_b64=req.mask_b64,
            output_format=req.output_format,
            negative_prompt=req.negative_prompt,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result.pop("image_bytes", None)
    return result


# ── Info endpoints ─────────────────────────────────────────────────────────────

@router.get("/capabilities")
async def get_capabilities():
    """Image generation capabilities, model cascade, and supported formats."""
    return IMAGE_CAPABILITIES
