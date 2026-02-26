"""
AMAIMA Audio Router
app/routers/audio.py

Exposes TTS and ASR as proper HTTP endpoints.
Previously audio was only reachable via the inline dispatch in
process_query() in main.py, which had no way to accept a real audio file
for transcription (it passed "dummy_path" to speech_to_text every time).

Endpoints:
  POST /v1/audio/synthesize       Text → base64 WAV data URI
  POST /v1/audio/synthesize/file  Text → raw WAV file download
  POST /v1/audio/transcribe       Multipart audio file → transcript
  POST /v1/audio/transcribe-b64   base64 audio payload → transcript
  GET  /v1/audio/voices           Available TTS voices
  GET  /v1/audio/capabilities     Capabilities + NIM config status

Registration in main.py:
  from app.routers.audio import router as audio_router
  app.include_router(audio_router)
"""

import base64
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.audio_service import (
    text_to_speech,
    speech_to_text,
    list_voices,
    AUDIO_CAPABILITIES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/audio", tags=["Speech — TTS & ASR"])


# ── Request models ─────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    text:     str = Field(..., max_length=5000, description="Text to convert to speech")
    voice:    str = Field(default="English-US.Female-1",
                          description="Voice name. Use GET /v1/audio/voices for list.")
    language: str = Field(default="en-US", description="BCP-47 language code")


class TranscribeB64Request(BaseModel):
    audio_b64:   str = Field(..., description="Base64-encoded audio bytes (WAV/MP3/FLAC)")
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")


# ── TTS endpoints ──────────────────────────────────────────────────────────────

@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    """
    Convert text to speech using NVIDIA Magpie TTS Multilingual.
    Returns a base64 data URI (data:audio/wav;base64,...) playable
    directly in an HTML audio element or AMAIMA's chat audio player.
    """
    try:
        result = await text_to_speech(text=req.text, voice=req.voice)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "service":    result.get("service"),
        "task":       result.get("task"),
        "model":      result.get("model"),
        "audio_data": result.get("audio_data"),    # data:audio/wav;base64,...
        "audio_url":  result.get("audio_url"),     # same, alias key
        "voice":      result.get("voice"),
        "label":      result.get("label"),
        "latency_ms": result.get("latency_ms"),
    }


@router.post("/synthesize/file")
async def synthesize_file(req: SynthesizeRequest):
    """
    Same as /synthesize but returns the raw WAV binary for direct download.
    Useful when you want to save the file rather than play it inline.
    """
    try:
        result = await text_to_speech(text=req.text, voice=req.voice)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Decode the data URI to raw bytes for the file response
    audio_data = result.get("audio_data", "")
    if "," in audio_data:
        audio_bytes = base64.b64decode(audio_data.split(",", 1)[1])
    else:
        raise HTTPException(status_code=502, detail="TTS returned no audio data")

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'attachment; filename="amaima_speech.wav"',
            "X-Latency-MS":        str(result.get("latency_ms", 0)),
            "X-Model":             str(result.get("model", "")),
            "X-Voice":             str(result.get("voice", "")),
        },
    )


# ── ASR endpoints ──────────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_file(
    file:        UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, FLAC)"),
    sample_rate: int        = Form(default=16000),
):
    """
    Transcribe an uploaded audio file using NVIDIA Parakeet CTC 1.1B.

    This is the real transcription endpoint that main.py's domain dispatch
    previously could not reach (it was calling speech_to_text("dummy_path")).
    Accepts multipart/form-data audio uploads up to 25MB.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = await speech_to_text(audio_bytes, sample_rate=sample_rate)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not result.get("transcript") and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])

    return {
        "transcript": result.get("transcript", ""),
        "model":      result.get("model"),
        "latency_ms": result.get("latency_ms"),
        "task":       result.get("task"),
    }


@router.post("/transcribe-b64")
async def transcribe_b64(req: TranscribeB64Request):
    """
    Transcribe audio submitted as a base64 string.
    Useful for browser-based audio recording (MediaRecorder → base64).
    """
    try:
        audio_bytes = base64.b64decode(req.audio_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Decoded audio is empty")

    try:
        result = await speech_to_text(audio_bytes, sample_rate=req.sample_rate)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "transcript": result.get("transcript", ""),
        "model":      result.get("model"),
        "latency_ms": result.get("latency_ms"),
    }


# ── Info endpoints ─────────────────────────────────────────────────────────────

@router.get("/voices")
async def get_voices():
    """List available Magpie TTS voices and the default selection."""
    return list_voices()


@router.get("/capabilities")
async def get_capabilities():
    """Audio service capabilities, models, and NIM configuration status."""
    return AUDIO_CAPABILITIES
