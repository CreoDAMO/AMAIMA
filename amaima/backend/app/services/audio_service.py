import logging
import time
import httpx
import base64
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

ASR_MODEL = "nvidia/parakeet-ctc-1.1b"
TTS_MODEL = "nvidia/magpie-tts-multilingual"

# NVIDIA NIM base URL for audio endpoints
NIM_BASE_URL = "https://ai.api.nvidia.com/v1"


def _get_api_key() -> str:
    key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not key:
        raise EnvironmentError(
            "NVIDIA_NIM_API_KEY is not set. "
            "Audio services require a valid NVIDIA NIM API key."
        )
    return key


async def text_to_speech(text: str, voice: str = "English-US.Female-1") -> Dict[str, Any]:
    """
    Synthesizes speech from text using NVIDIA Magpie TTS Multilingual via NIM.
    Returns a base64-encoded WAV audio payload suitable for inline playback.
    """
    start_time = time.time()
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "text": text,
        "voice": voice,
        "encoding": "LINEAR_PCM",
        "sample_rate_hz": 22050,
        "language_code": "en-US",
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
            # NIM TTS returns audio as base64-encoded PCM or WAV
            audio_b64 = data.get("audio") or data.get("audio_base64") or data.get("data")
            if audio_b64:
                return {
                    "service": "audio",
                    "task": "tts",
                    "model": TTS_MODEL,
                    "audio_data": f"data:audio/wav;base64,{audio_b64}",
                    "label": "Neural Audio Synthesis",
                    "quality": "high-fidelity",
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }
            else:
                # Riva streaming endpoint may return raw bytes
                audio_bytes = response.content
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                return {
                    "service": "audio",
                    "task": "tts",
                    "model": TTS_MODEL,
                    "audio_data": f"data:audio/wav;base64,{audio_b64}",
                    "label": "Neural Audio Synthesis",
                    "quality": "high-fidelity",
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

        # Non-200 — surface the real error
        error_detail = response.text[:500]
        logger.error(f"TTS NIM returned {response.status_code}: {error_detail}")
        raise RuntimeError(
            f"NVIDIA NIM TTS returned HTTP {response.status_code}: {error_detail}"
        )

    except httpx.TimeoutException:
        raise RuntimeError("NVIDIA NIM TTS request timed out after 60 seconds.")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error calling NVIDIA NIM TTS: {e}")


async def speech_to_text(audio_bytes: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
    """
    Transcribes audio using NVIDIA Parakeet CTC 1.1B via NIM.
    Accepts raw PCM bytes (16-bit, mono, 16kHz by default).
    """
    start_time = time.time()
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Encode audio as base64 for the NIM REST payload
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "audio": audio_b64,
        "sample_rate_hz": sample_rate,
        "language_code": "en-US",
        "encoding": "LINEAR_PCM",
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
                "service": "audio",
                "task": "asr",
                "model": ASR_MODEL,
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


AUDIO_CAPABILITIES = {
    "models": [ASR_MODEL, TTS_MODEL],
    "features": ["asr", "tts"],
    "tts_voices": [
        "English-US.Female-1",
        "English-US.Male-1",
        "English-GB.Female-1",
    ],
    "asr_languages": ["en-US"],
    "simulated": False,
}
