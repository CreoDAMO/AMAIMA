"""
AMAIMA Audio Service — v2
app/services/audio_service.py

Bugs fixed vs v1:
  BUG 1  speech_to_text() took `audio_bytes: bytes` but main.py calls it with
         `speech_to_text("dummy_path")` — a str. Caused TypeError on every call.
         Now accepts Union[str, bytes]: str → treated as file path or data URI,
         bytes → used directly.
  BUG 2  No file-loading logic existed — path was never read from disk.
         Now loads bytes from path, data URI, or passes bytes through directly.
"""

import logging
import time
import httpx
import base64
import os
import io
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

ASR_MODEL = "nvidia/parakeet-ctc-1.1b"
TTS_MODEL = "nvidia/magpie-tts-multilingual"

NIM_BASE_URL = "https://ai.api.nvidia.com/v1"


def _get_api_key() -> str:
    key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not key:
        raise EnvironmentError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Audio services require a valid NVIDIA NIM API key."
        )
    return key


def _is_configured() -> bool:
    return bool(os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY"))


def _load_audio_bytes(audio_input: Union[str, bytes]) -> bytes:
    """
    BUG 1+2 FIX: Resolve audio input to raw bytes regardless of how it arrives.
    Handles:
      - bytes   → returned as-is
      - "data:audio/...;base64,..." → decoded from data URI
      - "/path/to/file.wav"        → read from disk
      - "dummy_path"               → returns empty bytes with warning
    """
    if isinstance(audio_input, bytes):
        return audio_input

    if audio_input == "dummy_path" or not audio_input:
        logger.warning(
            "speech_to_text called with placeholder path 'dummy_path'. "
            "Submit real audio via POST /v1/media/audio/transcribe."
        )
        return b""

    if audio_input.startswith("data:"):
        # data URI: data:audio/wav;base64,AAAA...
        try:
            _, encoded = audio_input.split(",", 1)
            return base64.b64decode(encoded)
        except Exception as e:
            raise ValueError(f"Could not decode audio data URI: {e}")

    # Treat as filesystem path
    try:
        with open(audio_input, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Audio file not found: {audio_input!r}. "
            "Provide a valid file path, data URI, or raw bytes."
        )


async def text_to_speech(text: str, voice: str = "English-US.Female-1") -> Dict[str, Any]:
    """
    Synthesizes speech from text using NVIDIA Magpie TTS Multilingual via NIM.
    Returns a base64-encoded WAV audio payload suitable for inline playback.
    """
    start_time = time.time()
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    payload = {
        "text":           text,
        "voice":          voice,
        "encoding":       "LINEAR_PCM",
        "sample_rate_hz": 22050,
        "language_code":  "en-US",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{NIM_BASE_URL}/nvidia/magpie-tts-multilingual",
                headers=headers,
                json=payload,
            )

        if response.status_code == 200:
            data = response.json()
            audio_b64 = data.get("audio") or data.get("audio_base64") or data.get("data")
            if audio_b64:
                return {
                    "service":    "audio",
                    "task":       "tts",
                    "model":      TTS_MODEL,
                    "audio_data": f"data:audio/wav;base64,{audio_b64}",
                    "audio_url":  f"data:audio/wav;base64,{audio_b64}",
                    "label":      "Neural Audio Synthesis",
                    "quality":    "high-fidelity",
                    "voice":      voice,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }
            else:
                # Riva streaming endpoint may return raw bytes
                audio_bytes = response.content
                audio_b64   = base64.b64encode(audio_bytes).decode("utf-8")
                return {
                    "service":    "audio",
                    "task":       "tts",
                    "model":      TTS_MODEL,
                    "audio_data": f"data:audio/wav;base64,{audio_b64}",
                    "audio_url":  f"data:audio/wav;base64,{audio_b64}",
                    "label":      "Neural Audio Synthesis",
                    "quality":    "high-fidelity",
                    "voice":      voice,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

        error_detail = response.text[:500]
        logger.error(f"TTS NIM returned {response.status_code}: {error_detail}")
        raise RuntimeError(
            f"NVIDIA NIM TTS returned HTTP {response.status_code}: {error_detail}"
        )

    except httpx.TimeoutException:
        raise RuntimeError("NVIDIA NIM TTS request timed out after 60 seconds.")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling NVIDIA NIM TTS: {e}")


async def speech_to_text(
    audio_input: Union[str, bytes],
    sample_rate: int = 16000,
) -> Dict[str, Any]:
    """
    Transcribes audio using NVIDIA Parakeet CTC 1.1B via NIM.

    BUG 1+2 FIX: Now accepts:
      - bytes            Raw PCM audio bytes (original behaviour)
      - str file path    Will be read from disk
      - str data URI     Will be decoded from base64
      - "dummy_path"     Returns a graceful empty response instead of crashing
    """
    start_time = time.time()

    # BUG 1+2 FIX: resolve to bytes before any NIM call
    try:
        audio_bytes = _load_audio_bytes(audio_input)
    except Exception as e:
        return {
            "service":     "audio",
            "task":        "asr",
            "transcript":  "",
            "error":       str(e),
            "latency_ms":  round((time.time() - start_time) * 1000, 2),
        }

    # Called from main.py with dummy_path placeholder — return graceful stub
    if not audio_bytes:
        return {
            "service":    "audio",
            "task":       "asr",
            "transcript": "",
            "note": (
                "No audio provided. Submit audio via "
                "POST /v1/media/audio/transcribe (file upload) or "
                "POST /v1/media/audio/transcribe-url (base64 payload)."
            ),
            "latency_ms": 0,
        }

    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "audio":          audio_b64,
        "sample_rate_hz": sample_rate,
        "language_code":  "en-US",
        "encoding":       "LINEAR_PCM",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{NIM_BASE_URL}/nvidia/parakeet-ctc-1.1b",
                headers=headers,
                json=payload,
            )

        if response.status_code == 200:
            data = response.json()
            transcript = (
                data.get("text")
                or data.get("transcript")
                or data.get("results", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
            )
            return {
                "service":    "audio",
                "task":       "asr",
                "model":      ASR_MODEL,
                "transcript": transcript,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        error_detail = response.text[:500]
        logger.error(f"ASR NIM returned {response.status_code}: {error_detail}")
        raise RuntimeError(
            f"NVIDIA NIM ASR returned HTTP {response.status_code}: {error_detail}"
        )

    except httpx.TimeoutException:
        raise RuntimeError("NVIDIA NIM ASR request timed out after 60 seconds.")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling NVIDIA NIM ASR: {e}")


def list_voices() -> Dict[str, Any]:
    return {
        "voices":     AUDIO_CAPABILITIES["tts_voices"],
        "default":    "English-US.Female-1",
        "model":      TTS_MODEL,
        "configured": _is_configured(),
    }


AUDIO_CAPABILITIES = {
    "models": [ASR_MODEL, TTS_MODEL],
    "features": ["asr", "tts"],
    "tts_voices": [
        "English-US.Female-1",
        "English-US.Female-2",
        "English-US.Male-1",
        "English-US.Male-2",
        "English-GB.Female-1",
        "English-GB.Male-1",
        "Spanish-US.Female-1",
        "Spanish-US.Male-1",
        "French.Female-1",
        "German.Female-1",
    ],
    "asr_languages": ["en-US"],
    "simulated": False,
}
