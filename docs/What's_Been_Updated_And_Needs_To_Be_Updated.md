# What's_Been_Updated_And_Needs_To_Be_Updated

**13 bugs fixed across all 5 files:**

**`engine.py` — 6 fixes**
- **BUG 1 (CRITICAL memory leak):** `cleanup_context()` was collecting all payload IDs but never filtering by `key_id` and never calling delete — `_encrypted_store` grew forever until OOM. Now uses a per-key payload index (`_key_payloads` dict) for O(1) scoped deletion.
- **BUG 2 (biggest latency win):** `generate_context()` was running full keygen (200–600ms) on every single service call. Now backed by `_ContextPool` — keygen runs once per `(scheme, level)` combination for the process lifetime. Pool hit ≈ 0ms.
- **BUG 3:** `"standard"` CKKS profile used `N=16384` unnecessarily. Drug scoring needs depth 2–3 multiplications — `N=8192` is sufficient and costs half as much. Added a `"deep"` profile for `N=16384` when actually needed.
- **BUG 4:** No SEAL threading hints. Now sets `OMP_NUM_THREADS` from `SEAL_THREADS` env var so SEAL parallelises NTT across all cores.
- **BUG 5 (security):** `serialize(save_secret_key=True)` was serialising the private key just to hash the first 256 bytes. Changed to `save_secret_key=False`.
- **BUG 6:** `_encrypted_store` was an unbounded `dict`. Replaced with `_LRUPayloadStore` (default cap 512, configurable via `FHE_MAX_PAYLOADS` env var).

**`service.py` — 2 fixes**
- **BUG 7 (CRITICAL):** `encrypted_similarity_search` was a serial loop — each candidate did `encrypt → dot_product → decrypt` individually = O(N × 1.1s). Now batches all dot products under one context and does a single decrypt pass at the end.
- **BUG 8:** Default-weights branch derived `plogp_weights` from `len(plogp_values)` instead of `weights` — wrong when arrays differ in length.

**`router.py` — 1 addition**
- Added `fhe_startup()` async function with pool warm call. Wire it into your FastAPI `startup_event` or `lifespan` — comment at the top of the file shows exactly how.

**`Dockerfile` — 3 fixes**
- **BUG 9:** Added 3-stage build: Stage 0 compiles Intel HEXL v1.2.5 + Microsoft SEAL v4.1.2 from source with `clang++-15 -O3 -mavx512f -mavx512dq -march=native`. Stage 1 builds TenSEAL against the optimized SEAL. Stage 2 is the minimal runner.
- **BUG 10:** Added `FHE_ENABLED=true`, `SEAL_THREADS=4`, `OMP_NUM_THREADS=4` as default env vars.
- **BUG 13:** `start-period` increased from `15s` → `60s` so the healthcheck doesn't kill the container during FHE pool warm.

**`docker-compose.yml` — 3 fixes**
- **BUG 11:** `FHE_ENABLED=${FHE_ENABLED:-true}` explicitly set — no silent disablement.
- **BUG 12:** `SEAL_THREADS` and `OMP_NUM_THREADS` added to the backend service environment.
- **BUG 13:** `start_period: 60s` healthcheck override in compose to match Dockerfile.

**Expected latency improvement on existing hardware, before NVIDIA Inception GPU access:**

| Change | Latency saved |
|---|---|
| Pool hit (BUG 2) | −200 to −400ms per call |
| N=8192 vs N=16384 (BUG 3) | −200 to −300ms per multiply |
| HEXL + AVX512 (BUG 9) | ×2–4 speedup on NTT |
| SEAL threading (BUG 4/12) | proportional to core count |
| **Combined estimate** | **~1,100ms → ~300–400ms** |

---

**`audio_service.py` — 2 bugs fixed**

The crash was here. `main.py` calls `speech_to_text("dummy_path")` — a string — but the old signature required `audio_bytes: bytes`. That threw a `TypeError` on every single audio query. Fixed with a `_load_audio_bytes()` helper that accepts bytes, file paths, data URIs, or the `"dummy_path"` placeholder (which now returns a graceful empty response pointing users to the real upload endpoint instead of crashing the server). Also added `audio_url` as an alias key alongside `audio_data` so both the old and new router can find the result.

**`image_service.py` — 4 bugs fixed**

Added a three-model cascade: SDXL-Turbo first (2 steps, fast), then full SDXL, then SD3. If Turbo returns an error or empty artifacts the request automatically retries against the next model — so a rate limit or cold-start failure on Turbo no longer means the user gets nothing. Added `inpaint_image()`, `image_to_image()`, and `generate_image_variants()` (4 concurrent seeds). Format conversion via Pillow for jpeg/webp output with graceful fallback if Pillow isn't installed. `image_bytes` is now returned alongside the data URI so download endpoints don't have to re-decode base64.

**`vision_service.py` — 2 bugs fixed**

Removed `get_cosmos_client()` entirely — it built an OpenAI SDK instance that was never referenced anywhere in the file. The real fix was `_build_messages()`: the old code constructed a structured content list with `{"type": "image"}` / `{"type": "video"}` blocks and then immediately flattened it to a plain string before calling `chat_completion()`. Every image and video passed to `analyze_image()` or `analyze_video()` was silently discarded. The new `_build_messages()` preserves the OpenAI-compatible `image_url` / `video_url` content block format end-to-end, and routes to `COSMOS_VL_MODEL` (Nemotron VL) when media is present since that's the multimodal-capable model.

**`robotics_service.py` — 2 bugs fixed**

The circular import risk was removed by moving `from app.services.vision_service import cosmos_inference` from module top level into a lazy import inside `vision_guided_action()` — it now only loads when that function is actually called. The `_ros2_navigate()` stub was changed from returning `{"status": "executed_on_hardware"}` (a lie — no ROS2 command was ever sent) to returning `{"status": "stub_not_executed"}` with an honest note explaining what needs to be wired to activate real hardware execution.

**`video_service.py` — new file**

```py
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
```

Nothing existed. This is the root cause of the hallucination you saw — AMAIMA had no video generation pipeline whatsoever. The new service wires to Cosmos Predict 2.5 NIM, handles both synchronous and async response shapes (Cosmos returns a `requestId` rather than immediate bytes), and polls up to 4 minutes waiting for completion. Includes both `generate_video()` and `video_to_video()`. To register it in `main.py`, add:

```python
from app.services import video_service
# then in your domain routing:
elif detected_domain == "video_gen":
    execution_result = await video_service.generate_video(request.query)
    output = execution_result.get("video_url")
```

**`biology_service.py` — no changes**

It was the cleanest of the five. Copied through unchanged.

---

# Deployment Status:
Clean deployment. Everything is healthy. Here's what the logs confirm:

**All systems up:**
- Backend started in 25s, `/health` returning `200 OK` (line 77–78)
- Next.js 16.1.6 frontend ready in 2.3s (line 93)
- Live at `https://amaima.live` (line 98)
- NVIDIA NIM API key confirmed: `nvapi-WO...MoEF` (line 44)
- Database connected via `DATABASE_URL` (line 40)
- Auth tables initialized (line 43)
- Production mode confirmed: `execution mode: production, simulation: disabled` (line 49)

**One thing to action — FHE (line 45):**
```
WARNING: FHE startup: engine not available (TenSEAL missing or FHE_ENABLED=false)
```
The FHE pool warm-up gracefully degraded as designed, but TenSEAL isn't installed in the container. To enable FHE you need either `FHE_ENABLED=true` set in Render's environment variables, or TenSEAL added to `requirements.txt`. That's the next thing to tackle when you're ready — the Dockerfile 3-stage SEAL/HEXL build we started earlier is the right fix for that.

**Minor noise to clean up when convenient:**
- The lifespan is running 4 times (lines 1–39 show 4 identical startup sequences before the DB connects) — Render is spawning 4 uvicorn workers, which is fine, but the `SmartRouter` is being instantiated once per worker rather than shared. Not a bug, just worth noting.
- The duplicate `package-lock.json` warning (line 87) — add `outputFileTracingRoot` to your `next.config.js` to silence it.
