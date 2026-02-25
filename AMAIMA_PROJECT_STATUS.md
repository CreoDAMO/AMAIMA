# AMAIMA Project Status
**Last updated:** 2026-02-25 | **Deployment:** https://amaima.live | **Status:** 🟢 Live

---

## ✅ COMPLETED — Files Updated This Session

### Backend Core

#### `main.py`
- Removed `from app.services import audio_service, image_gen_service` → fixed to `from app.services import audio_service` + `from app.services import image_service as image_gen_service` (CI/CD fix)
- Removed `/v1/simulate` endpoint (called `route_query(simulate=True)` which now raises `EnvironmentError`)
- Fixed audio output field: `audio_url` → `audio_data` (base64 data URI)
- Fixed image output field: `image_url` → `image_data` (base64 data URI)
- Fixed ASR path in `/v1/query`: was calling `speech_to_text("dummy_path")` (string) — now raises `400` pointing to `/v1/audio/transcribe`
- Added `/v1/audio/synthesize` and `/v1/audio/transcribe` as dedicated typed endpoints
- Added `/v1/image/generate` as a dedicated typed endpoint
- Fixed `/v1/agents/run` to dispatch `neural_audio_synthesis` and `visual_art_generation` through `run_crew()` instead of raising `400 Unknown crew type`
- Added `fhe_startup()` call in lifespan with `try/except` so TenSEAL absence degrades gracefully
- Fixed streaming endpoint: removed fake SSE fallback when NIM unconfigured → now raises `503`
- `simulated: False` hardcoded throughout

#### `app/modules/smart_router_engine.py`
- `IMAGE_GEN_PATTERNS` (13 regex) and `SPEECH_PATTERNS` (15 regex) checked **before** complexity scoring via `_match_patterns()` — early exit with `confidence=1.0`
- `route_query()` short-circuits for `image_gen` and `speech` domains, bypasses `_select_model()`
- `AMAIMA_EXECUTION_MODE` check: raises `EnvironmentError` if not `"execution-enabled"` — no silent simulation fallback
- `simulated: False`, `execution_mode_active: True` hardcoded in decision dict
- Schema version bumped to `2.0.0`

#### `app/core/unified_smart_router.py`
- **Root cause fix for all domain routing failures:** `DOMAIN_KEYWORDS` dict removed — was matching `"image"` → `vision` before `image_gen` could fire
- `route()` method now delegates domain detection to `smart_router_engine.detect_domain()` — single source of truth across both routers
- All other logic (device capability, connectivity, execution mode, model size, latency/cost estimation) unchanged

### Backend Services

#### `app/services/audio_service.py`
- Real `httpx.AsyncClient` POST to `https://ai.api.nvidia.com/v1/nvidia/magpie-tts-multilingual`
- `_load_audio_bytes()` helper: accepts `bytes`, file paths, data URIs, or `"dummy_path"` placeholder (graceful empty response instead of crash)
- `audio_url` alias added alongside `audio_data` so old and new routers both find the result
- Returns `data:audio/wav;base64,{b64}` URI for inline playback
- `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY` check raises `EnvironmentError` if missing (no silent failure)
- 60s timeout with explicit `TimeoutException` handling
- `simulated: False` in `AUDIO_CAPABILITIES`

#### `app/services/image_service.py`
- Real SDXL-Turbo POST to `https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo`
- Three-model cascade: SDXL-Turbo (2 steps) → full SDXL → SD3 on error/empty artifacts
- `negative_prompt` support (appended with `weight: -1.0`)
- Returns `data:image/png;base64,{b64}` URI; `image_bytes` also returned for download endpoints
- Added `inpaint_image()`, `image_to_image()`, `generate_image_variants()` (4 concurrent seeds)
- Format conversion via Pillow (jpeg/webp) with graceful fallback if Pillow not installed
- `simulated: False` in `IMAGE_CAPABILITIES`

#### `app/services/vision_service.py`
- Removed unused `get_cosmos_client()` (built OpenAI SDK instance never referenced)
- Fixed `_build_messages()`: old code constructed `{"type": "image"}` / `{"type": "video"}` content blocks then immediately flattened to plain string — media was silently discarded on every call. Now preserves OpenAI-compatible `image_url` / `video_url` content block format end-to-end
- Routes to `COSMOS_VL_MODEL` (Nemotron VL) when media is present
- `logger.exception()` used for full traceback on server without leaking to client

#### `app/services/robotics_service.py`
- Circular import risk removed: `from app.services.vision_service import cosmos_inference` moved from module top-level into lazy import inside `vision_guided_action()`
- `_ros2_navigate()` stub: changed `status: "executed_on_hardware"` (lie) → `status: "stub_not_executed"` with honest note for hardware wiring

#### `app/services/biology_service.py`
- SMILES extraction regex tightened: replaced broad `[A-Za-z0-9@+\-\[\]\(\)=#/\\\.%]+` with structurally-constrained pattern requiring at least one bond/branch/stereo character
- Deduplication added (`seen` set), cap raised from 10 → 20 candidates
- Filter requires carbon (`C` or `c`) AND structural character — eliminates false positives from prose words like `"NVIDIA"`, `"Carbon"`, `"None"`

#### `app/services/video_service.py` — **NEW FILE**
- Wires to `nvidia/cosmos-predict2-5b` (Cosmos Predict 2.5 NIM)
- Handles both sync and async NIM response shapes (Cosmos returns `requestId` rather than immediate bytes)
- Polls up to 4 minutes (`48 × 5s`) for job completion
- `generate_video(prompt)` → MP4 base64 data URI + metadata
- `video_to_video(prompt, video_b64)` → transformed MP4
- `VIDEO_CAPABILITIES` manifest for router/health endpoint
- **Still needs:** registration in `main.py` (see TODO below)

### Backend Agents

#### `app/agents/crew_manager.py`
- `AUDIO_ENGINEER` + `TONE_ANALYST` agents added → `run_neural_audio_crew()` pipeline
- `CREATIVE_DIRECTOR` + `AESTHETIC_VALIDATOR` agents added → `run_visual_art_crew()` pipeline
- `run_crew()` top-level dispatcher added — routes `crew_type` string to correct implementation
- `CREW_REGISTRY` maps `"audio"` → `"neural_audio"`, `"image_gen"` → `"visual_art"`, etc.

#### `app/agents/langchain_agent.py`
- Fixed `needs_revision()` predicate in `build_complex_reasoning_workflow()`: replaced loose single-word matches (`"error"`, `"missing"`, `"gap"`) with 10 explicit multi-word revision signals (`"requires revision"`, `"incorrect conclusion"`, etc.) — eliminates false-positive loops that were burning 3–6× token cost on every complex reasoning call
- `audio` and `image_gen` domain workflows registered in `WORKFLOW_REGISTRY` (LLM planning layer only — media dispatch is in `crew_manager.py`)

#### `app/agents/biology_crew.py` — No changes needed (clean)
#### `app/agents/robotics_crew.py` — No changes needed (clean)

### FHE

#### `app/fhe/engine.py`
- **BUG 1 (CRITICAL — memory leak):** `cleanup_context()` never called delete — `_encrypted_store` grew until OOM. Fixed with per-key `_key_payloads` index for O(1) scoped deletion
- **BUG 2 (biggest latency win):** `generate_context()` ran full keygen (200–600ms) on every call. Now backed by `_ContextPool` — keygen runs once per `(scheme, level)` per process lifetime. Pool hit ≈ 0ms
- **BUG 3:** `"standard"` CKKS profile used `N=16384` unnecessarily — `N=8192` sufficient for depth 2–3 multiplications, half the cost. `"deep"` profile added for `N=16384`
- **BUG 4:** SEAL threading: `OMP_NUM_THREADS` now set from `SEAL_THREADS` env var
- **BUG 5 (security):** `serialize(save_secret_key=True)` was serialising the private key just to hash it. Changed to `save_secret_key=False`
- **BUG 6:** `_encrypted_store` replaced with `_LRUPayloadStore` (cap 512, configurable via `FHE_MAX_PAYLOADS`)

#### `app/fhe/service.py`
- **BUG 7 (CRITICAL — O(N) serial loop):** `encrypted_similarity_search` did `encrypt → dot_product → decrypt` per candidate. Now batches all dot products under one context, single decrypt pass at end
- **BUG 8:** `plogp_weights` derived from `len(plogp_values)` instead of `len(weights)` — wrong when arrays differ in length

#### `app/fhe/router.py`
- `fhe_startup()` async function added with pool warm call — wired into `main.py` lifespan

---

## 🔴 KNOWN ISSUE — FHE Dashboard Crash

**Symptom:** `amaima.live/fhe` → "Application error: a client-side exception has occurred"

**Root cause:** The `/fhe` frontend page(s) are hitting a backend API route or importing a module that doesn't exist yet, or the FHE page component itself has a runtime error (likely trying to call an endpoint that returns an error because TenSEAL isn't installed).

**Confirmed from logs:**
```
WARNING: FHE startup: engine not available (TenSEAL missing or FHE_ENABLED=false)
```
TenSEAL is not in the container — any FHE API call will fail, and if the frontend doesn't handle that error gracefully it crashes.

---

## 📋 TODO — Prioritised

### 🔴 Critical (Blocking features / crashes)

- [ ] **Fix FHE dashboard crash** — All `/fhe` page.tsx files need to be audited and updated:
  - Add error boundaries around FHE API calls so TenSEAL absence shows a degraded UI instead of crashing
  - Check every `fetch('/api/fhe/...')` call has a try/catch and renders a fallback state
  - Likely affected: `src/app/fhe/page.tsx` and any sub-route pages under `/fhe`

- [ ] **Register `video_service.py` in `main.py`** — The new video generation service exists but is not wired up:
  ```python
  from app.services import video_service
  # In /v1/query domain routing:
  elif detected_domain == "video_gen":
      execution_result = await video_service.generate_video(request.query)
      output = execution_result.get("video_url")
  # Add dedicated endpoint:
  # POST /v1/video/generate
  ```
  Also add `VIDEO_GEN_PATTERNS` to `smart_router_engine.py` so the router can detect video generation intent.

- [ ] **Add `video_gen` route patterns to `smart_router_engine.py`**:
  ```python
  VIDEO_GEN_PATTERNS = [
      r"\bgenerate\s+(a\s+)?video\b",
      r"\bcreate\s+(a\s+)?video\b",
      r"\btext.?to.?video\b",
      r"\bcosmos\s+video\b",
      r"\banimate\b",
      r"\bvideo\s+generation\b",
  ]
  ```

- [ ] **Add routers for Audio, Image, and Video to `app/routers/`** — Currently only `biology.py`, `robotics.py`, `vision.py` exist. Need:
  - `app/routers/audio.py` — wraps `audio_service.text_to_speech()` and `speech_to_text()`
  - `app/routers/image.py` — wraps `image_service.generate_image()` and variants
  - `app/routers/video.py` — wraps `video_service.generate_video()` and `video_to_video()`
  - Update `app/routers/__init__.py` to export all routers
  - Include new routers in `main.py` via `app.include_router(...)`

- [ ] **Audit `app/routers/biology.py`, `robotics.py`, `vision.py`** — These were not reviewed this session. Need to check they are consistent with the updated service files (especially `vision.py` after the `_build_messages()` fix and `robotics.py` after the lazy import fix).

- [ ] **Audit `app/core/` directory** — Not reviewed this session. Needs a pass to confirm consistency with the unified_smart_router changes. Files to check:
  - `app/core/unified_smart_router.py` ✅ Updated this session
  - Any other files in `app/core/` (execution engine wrappers, config loaders, etc.)

### 🟡 High Priority

- [ ] **FHE: Install TenSEAL via 3-stage Dockerfile** — The Dockerfile 3-stage build (Intel HEXL v1.2.5 + Microsoft SEAL v4.1.2 compiled with Clang-15, AVX-512, -O3) needs to be completed and deployed. Currently TenSEAL is missing from the container. Expected latency improvement once installed:

  | Change | Latency saved |
  |---|---|
  | Context pool hit (BUG 2) | −200 to −400ms per call |
  | N=8192 vs N=16384 (BUG 3) | −200 to −300ms per multiply |
  | HEXL + AVX-512 (BUG 9) | ×2–4 speedup on NTT |
  | SEAL threading (BUG 4) | proportional to core count |
  | **Combined estimate** | **~1,100ms → ~300–400ms** |

- [ ] **Fix duplicate lockfile warning** — Add `outputFileTracingRoot` to `next.config.js`:
  ```js
  turbopack: { root: './amaima/frontend' }
  ```

- [ ] **`SmartRouter` singleton across uvicorn workers** — Currently instantiated once per worker (4 workers = 4 instances). Refactor `AppState` to use shared memory or move router to a module-level singleton with a lock.

- [ ] **Video generation: async webhook support** — `video_service.py` holds the HTTP connection open while polling Cosmos (up to 4 min). Replace with a webhook/callback pattern so the HTTP response returns immediately with a `job_id` and the frontend polls `/v1/video/status/{job_id}`.

- [ ] **`page.tsx` audit — all frontend pages** — The main `page.tsx` was updated. Other pages that may need updates:
  - `src/app/fhe/page.tsx` (confirmed crashing — highest priority)
  - `src/app/agents/page.tsx`
  - `src/app/biology/page.tsx`
  - `src/app/robotics/page.tsx`
  - `src/app/vision/page.tsx`
  - Any video generation page if it exists

### 🟢 Normal Priority

- [ ] **Database migrations** — Set up Alembic for formal schema management instead of `init_db()` on every startup

- [ ] **Biology domain expansion** — Integrate DiffDock/AlphaFold into `biology_service.py` beyond molecule scoring

- [ ] **Robotics hardware bridge** — Replace `_ros2_navigate()` stub (currently `status: "stub_not_executed"`) with real ROS2/rclpy message publishers

- [ ] **Streaming cursor UI** — Add typing animation for SSE streaming mode in chat interface

- [ ] **Model comparison tool** — UI component to compare outputs from different models side-by-side

- [ ] **Advanced monitoring** — Expand `observability_framework.py` with custom Prometheus metrics for FHE latency and model routing accuracy

- [ ] **Dependency audit** — `requirements.txt` has 19 vulnerabilities (1 moderate, 18 high) flagged by `npm audit`. Run `npm audit fix` for non-breaking fixes.

- [ ] **Documentation** — Update Technical Whitepaper to reflect FHE fixes, video generation, new crew types, and router consolidation

- [ ] **CI/CD** — Verify GitHub Action `backend.yml` and multi-platform mobile builds

---

## 📊 Current Deployment Health

**As of 2026-02-25 04:37 UTC:**

| Component | Status | Notes |
|---|---|---|
| Backend API | 🟢 Healthy | `/health` 200 OK, 23s startup |
| Frontend | 🟢 Live | Next.js 16.1.6, ready in 2.4s |
| Database | 🟢 Connected | `DATABASE_URL` configured |
| Auth | 🟢 Initialized | Tables ready |
| NVIDIA NIM | 🟢 Configured | `nvapi-WO...MoEF` (70 chars) |
| Execution mode | 🟢 Production | Simulation disabled |
| FHE | 🔴 Degraded | TenSEAL not installed |
| FHE Dashboard `/fhe` | 🔴 Crashing | Client-side exception |
| Video Generation | 🟡 Incomplete | `video_service.py` exists but not wired to router |
| RDKit | 🟡 Cloud-only | Not installed locally; validation via NIM |
| ROS2 | 🟡 Stub | Hardware bridge not wired |
| PyBullet | 🟡 Stub | Simulation via NIM cloud |

---

## 🗂 File Change Summary

| File | Status | Key Change |
|---|---|---|
| `main.py` | ✅ Updated | Import fix, audio/image field names, agent dispatch, FHE startup, no simulate |
| `smart_router_engine.py` | ✅ Updated | Regex domain priority, no simulation fallback |
| `unified_smart_router.py` | ✅ Updated | Delegated domain detection to smart_router_engine |
| `audio_service.py` | ✅ Updated | Real NIM calls, dummy_path fix, audio_url alias |
| `image_service.py` | ✅ Updated | 3-model cascade, variants, format conversion |
| `vision_service.py` | ✅ Updated | _build_messages() fix, media no longer discarded |
| `robotics_service.py` | ✅ Updated | Lazy import, honest ROS2 stub |
| `biology_service.py` | ✅ Updated | SMILES regex tightened |
| `video_service.py` | ✅ Created | New — Cosmos Predict 2.5, not yet wired |
| `crew_manager.py` | ✅ Updated | Neural audio + visual art crews, run_crew() dispatcher |
| `langchain_agent.py` | ✅ Updated | needs_revision() false-positive fix |
| `fhe/engine.py` | ✅ Updated | 6 bugs fixed (memory leak, pool, LRU, security) |
| `fhe/service.py` | ✅ Updated | Batched similarity search, weight bug |
| `fhe/router.py` | ✅ Updated | fhe_startup() added |
| `biology_crew.py` | ✅ Clean | No changes needed |
| `robotics_crew.py` | ✅ Clean | No changes needed |
| `app/routers/audio.py` | ❌ Missing | Needs to be created |
| `app/routers/image.py` | ❌ Missing | Needs to be created |
| `app/routers/video.py` | ❌ Missing | Needs to be created |
| `app/routers/biology.py` | ⚠️ Unreviewed | Needs audit against updated service |
| `app/routers/robotics.py` | ⚠️ Unreviewed | Needs audit against updated service |
| `app/routers/vision.py` | ⚠️ Unreviewed | Needs audit against updated service |
| `app/core/*` | ⚠️ Unreviewed | Needs audit (except unified_smart_router.py) |
| `src/app/fhe/page.tsx` | 🔴 Crashing | Needs error boundaries + degraded state |
| Other `page.tsx` files | ⚠️ Unreviewed | Agents, biology, robotics, vision pages |
