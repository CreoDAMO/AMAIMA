from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/vision", tags=["vision"])


@router.post("/reason")
async def reason_on_media(
    query: str = Form(..., description="Reasoning query about the media"),
    media_file: Optional[UploadFile] = File(default=None, description="Image or video file"),
):
    from app.services.vision_service import cosmos_inference

    media_path = None
    media_type = None

    if media_file:
        file_ext = Path(media_file.filename).suffix.lower()
        media_type = "video" if file_ext in [".mp4", ".avi", ".mov"] else "image"
        media_path = f"/tmp/amaima_{uuid.uuid4().hex}{file_ext}"

        try:
            content = await media_file.read()
            with open(media_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process uploaded file: {e}")

    try:
        result = await cosmos_inference(query, media_path, media_type)
        return result
    except Exception as e:
        logger.error(f"Vision reasoning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if media_path:
            try:
                Path(media_path).unlink(missing_ok=True)
            except Exception:
                pass


@router.post("/analyze-image")
async def analyze_image(
    query: str = Form(..., description="Question about the image"),
    image_file: UploadFile = File(..., description="Image file (JPEG/PNG)"),
):
    from app.services.vision_service import analyze_image as do_analyze

    file_ext = Path(image_file.filename).suffix.lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise HTTPException(status_code=400, detail="Supported formats: JPEG, PNG, BMP, WebP")

    media_path = f"/tmp/amaima_{uuid.uuid4().hex}{file_ext}"
    try:
        content = await image_file.read()
        with open(media_path, "wb") as f:
            f.write(content)
        result = await do_analyze(media_path, query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            Path(media_path).unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/embodied-reasoning")
async def embodied_reasoning(
    scene: str = Form(..., description="Scene description"),
    task: str = Form(..., description="Task to reason about"),
):
    from app.services.vision_service import embodied_reasoning as reason
    try:
        result = await reason(scene, task)
        return result
    except Exception as e:
        logger.error(f"Embodied reasoning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def vision_capabilities():
    from app.services.vision_service import VISION_CAPABILITIES
    return VISION_CAPABILITIES
