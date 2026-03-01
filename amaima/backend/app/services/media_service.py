import io
import base64
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

async def get_media_response(b64_data: str, filename: str, mime_type: str):
    try:
        if not b64_data:
            raise HTTPException(status_code=400, detail="No data provided")
            
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
