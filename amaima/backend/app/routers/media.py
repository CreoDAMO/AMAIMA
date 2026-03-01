from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import io
import base64
from typing import Dict

router = APIRouter(prefix="/v1/media", tags=["media"])

@router.post("/download")
async def download_media(data: Dict[str, str] = Body(...)):
    """
    Generic endpoint to download base64 encoded media (Image, Video, Audio).
    Expects {"base64": "...", "filename": "...", "mime_type": "..."}
    """
    try:
        b64_data = data.get("base64")
        filename = data.get("filename", "download")
        mime_type = data.get("mime_type", "application/octet-stream")
        
        if not b64_data:
            raise HTTPException(status_code=400, detail="No data provided")
            
        # Strip data URI prefix if present
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
            
        file_bytes = base64.b64decode(b64_data)
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
