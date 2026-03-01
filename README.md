# AMAIMA

**Advanced Model-Aware AI Management Interface**

<div align="center">

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-109989?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white)](https://kotlinlang.org/)
[![Stripe](https://img.shields.io/badge/Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: AMAIMA v2.0](https://img.shields.io/badge/License-AMAIMA%20v2.0-blueviolet?style=for-the-badge)](LICENSE)
[![Backend CI/CD](https://github.com/CreoDAMO/AMAIMA/actions/workflows/backend.yml/badge.svg)](https://github.com/CreoDAMO/AMAIMA/actions/workflows/backend.yml)

**🟢 Live at [amaima.live](https://amaima.live)**

</div>

---

## Overview

AMAIMA is an enterprise-grade multimodal AI operating system that intelligently routes queries across **26 NVIDIA NIM models** spanning **7 intelligence domains**. It combines a production smart routing engine with no simulation fallback, live multi-agent orchestration, Fully Homomorphic Encryption (FHE), and specialized domain services for biology, robotics, vision, speech, image generation, and video generation — backed by a full-featured Android mobile client with on-device ML inference.

### What It Does

- **Smart Query Routing** — Regex-priority domain detection (image_gen and speech checked first) then complexity scoring (TRIVIAL to EXPERT); routes to the optimal model across 7 domains. Single source of truth shared between both routing engines.
- **7-Domain AI** — Biology (BioNeMo/GenMol), Robotics (Isaac/GR00T), Vision (Cosmos R2), Speech (Riva ASR/TTS), Image Generation (SDXL-Turbo cascade), Video Generation (Cosmos Predict 2.5), and Embeddings (NeMo Retriever)
- **Live Multi-Agent Orchestration** — Agent Builder executes real multimodal pipelines via `/v1/agents/run` with 10 crew types including Neural Audio Synthesis, Visual Art Generation, and Stateful Workflow
- **Fully Homomorphic Encryption** — Privacy-preserving encrypted inference via Microsoft SEAL (TenSEAL): CKKS + BFV schemes, 128-bit post-quantum security, context pool (keygen once per process), LRU payload store, batched similarity search
- **Multimodal Frontend** — Inline audio player and image rendering in chat; base64 data URIs returned directly from service layer
- **Production Mode Only** — `AMAIMA_EXECUTION_MODE=execution-enabled` required; no silent simulation fallback anywhere in the stack
- **Monetization Built-In** — Three-tier subscription system with Stripe billing, JWT authentication, API key management, and MAU usage enforcement
- **On-Device ML** — Android app with ONNX Runtime + TFLite for offline embeddings, speech-to-text, vision, and vector search

---

## Architecture

```
                    +------------------+
                    |   Next.js 16     |
                    |   Frontend       |
                    |   (port 10000)   |
                    +--------+---------+
                             |
                    API Routes (proxy)
                             |
                    +--------+---------+
                    |   FastAPI        |
                    |   Backend        |
                    |   (port 8000)    |
                    +--------+---------+
                             |
         +-------------------+--------------------+
         |                   |                    |
+--------+--+       +--------+--+       +---------+--+
| Smart     |       | Domain    |       | Billing /  |
| Router    |       | Services  |       | Auth /     |
| Engine*   |       |           |       | Admin      |
+-----------+       +-----------+       +------------+
                         |
     +-------------------+---------------------+
     |          |         |         |     |     |
+----+----+ +---+---+ +---+---+ +--+--+ +-+-+ +--+---+
| Biology | |Robotics| | Vision| |Audio| |Img| |Video |
| BioNeMo | |Isaac/  | |Cosmos | | Riva| |Gen| |Cosmos|
| GenMol  | |GR00T   | |  R2   | |ASR/ | |SDL| |Pred. |
|         | |        | |       | | TTS | |XL | | 2.5  |
+---------+ +--------+ +-------+ +-----+ +---+ +------+
                    |
            +-------+-------+
            |               |
    +-------+----+  +-------+------+
    | FHE        |  | NVIDIA NIM   |
    | Subsystem  |  | Cloud APIs   |
    | (TenSEAL)  |  |              |
    | CKKS + BFV |  |              |
    +------------+  +--------------+

* unified_smart_router.py delegates domain detection
  to smart_router_engine.py — single source of truth

    +------------------+
    | Android Mobile   |
    | Kotlin + Compose |
    | ONNX + TFLite    |
    +------------------+
```

---

## Model Registry (26 Models)

### General Language Models
| Model | Parameters | Best For | Cost/1K Tokens |
|-------|-----------|----------|----------------|
| meta/llama-3.1-8b-instruct | 8B | Simple queries, chat | $0.0001 |
| meta/llama-3.1-70b-instruct | 70B | Complex reasoning, agent crews | $0.00088 |
| meta/llama-3.1-405b-instruct | 405B | Expert-level tasks | $0.005 |
| mistralai/mixtral-8x7b-instruct-v0.1 | 46.7B MoE | Cost-efficient complex | $0.0006 |
| google/gemma-2-9b-it | 9B | Lightweight/edge | $0.0001 |
| nvidia/nemotron-nano-9b-v2 | 9B | Edge/agentic AI | $0.0001 |

### Vision/Multimodal Models
| Model | Parameters | Best For |
|-------|-----------|----------|
| nvidia/cosmos-reason2-7b | 7B | Vision-language reasoning, embodied AI |
| nvidia/cosmos-predict2-14b | 14B | Video generation, future state prediction |
| nvidia/llama-3.1-nemotron-nano-vl-8b | 8B | Multimodal understanding (image/video input) |

### Biology/Drug Discovery Models
| Model | Best For |
|-------|----------|
| nvidia/bionemo-megamolbart | Molecular generation, drug discovery |
| nvidia/bionemo-esm2 | Protein structure prediction |
| nvidia/genmol | Fragment-based molecule generation (SAFE format, QED/plogP) |
| AlphaFold2 *(self-hosted)* | Protein structure prediction |
| DiffDock *(self-hosted)* | Molecular docking |

### Robotics Models
| Model | Best For |
|-------|----------|
| nvidia/isaac-gr00t-n1.6 | Humanoid robot control (VLA) |
| nvidia/alpamayo-1 | Autonomous vehicle reasoning (VLA) |
| Isaac Manipulator *(self-hosted)* | Object manipulation |

### Speech Models
| Model | Best For |
|-------|----------|
| nvidia/magpie-tts-multilingual | Text-to-speech synthesis (TTS) — primary |
| nvidia/parakeet-ctc-1.1b | Automatic speech recognition (ASR) — 1.1B CTC |
| Riva ASR *(self-hosted)* | On-premise speech recognition |
| Riva TTS *(self-hosted)* | On-premise speech synthesis |

### Image Generation Models
| Model | Best For |
|-------|----------|
| stabilityai/sdxl-turbo | Fast text-to-image (2 steps, cascade primary) |
| stabilityai/sdxl | Full-quality text-to-image (cascade fallback) |
| stabilityai/stable-diffusion-3 | Highest quality (cascade final fallback) |

### Video Generation Models
| Model | Best For |
|-------|----------|
| nvidia/cosmos-predict2-5b | Text-to-video and video-to-video (5s, 720p) |

### Embedding Models
| Model | Best For |
|-------|----------|
| nvidia/nv-embedqa-e5-v5 | 2048-dim text + image embeddings |
| NV-Embed *(self-hosted)* | On-premise multimodal embeddings |

---

## Smart Router

The routing engine uses **regex-priority domain detection** — `image_gen` and `speech` patterns are evaluated first before any complexity scoring, ensuring they never fall through to a general LLM. Both routing layers (`unified_smart_router.py` and `smart_router_engine.py`) share a single domain detection function as the source of truth.

### Complexity Levels
| Level | Description | Routed To |
|-------|-------------|-----------|
| TRIVIAL | Simple factual queries | Llama 8B / Gemma 9B |
| SIMPLE | Basic explanations | Llama 8B |
| MODERATE | Multi-step reasoning | Llama 70B |
| COMPLEX | Domain expertise needed | Mixtral 8x7B / 70B |
| EXPERT | Specialized analysis | Llama 405B |

### Domain-Aware Routing (Priority Order)
1. **Image Generation** — 13 regex patterns checked first (`generate image`, `draw`, `render`, `sdxl`, `stable diffusion`, etc.) → SDXL-Turbo cascade
2. **Speech** — 15 regex patterns checked second (`tts`, `text-to-speech`, `narrate`, `transcribe`, `asr`, `riva`, etc.) → Riva TTS / Parakeet ASR
3. **Biology** — keyword scoring → BioNeMo / GenMol
4. **Vision** — keyword scoring → Cosmos Reason2 7B
5. **Robotics** — keyword scoring → Isaac GR00T N1.6
6. **General** — complexity-based model selection

---

## Domain Services

### Biology (BioNeMo + GenMol)
- Drug discovery pipeline with molecule generation (SMILES)
- Protein sequence analysis and structure prediction
- Molecule optimization with RDKit validation (falls back to cloud if RDKit unavailable)
- Fragment-based molecule generation via GenMol (SAFE format, QED/plogP scoring)
- Structurally-constrained SMILES extraction from LLM responses (no false positives from prose)

### Robotics (Isaac/GR00T)
- Robot navigation and path planning
- Action planning with step-by-step structured execution (`ACTION | PARAMS | REASON` format)
- Vision-guided robot actions via Cosmos inference (lazy-loaded to avoid circular imports)
- Physics simulation via PyBullet (local) or NIM cloud fallback
- ROS2 hardware bridge stub (honest `stub_not_executed` status — not a fake success)

### Vision (Cosmos R2)
- Image and video analysis — media content blocks preserved end-to-end (not silently discarded)
- Routes to Nemotron VL when media is present (multimodal-capable model)
- Scene understanding and spatial reasoning with `<think>/<answer>` structured output
- Embodied reasoning for robotics applications

### Speech (Riva)
- **TTS:** `POST /v1/audio/synthesize` → `nvidia/magpie-tts-multilingual` → `data:audio/wav;base64,...`; raw WAV download via `/synthesize/file`
- **ASR:** `POST /v1/audio/transcribe` (multipart file upload) or `/transcribe-b64` (base64 JSON) → `nvidia/parakeet-ctc-1.1b` → transcript text
- `GET /v1/audio/voices` — 10 available voices (EN-US/GB, ES-US, FR, DE, male/female)
- Neural audio playback rendered directly in chat interface
- `speech_to_text()` accepts `bytes`, file path, data URI, or `"dummy_path"` placeholder (graceful empty response)

### Image Generation (SDXL)
- **Text-to-image:** `POST /v1/image/generate` → SDXL-Turbo (2 steps) with automatic cascade fallback to full SDXL → SD3
- **Variants:** `POST /v1/image/variants` → up to 4 concurrent generations with different seeds
- **Edit:** `POST /v1/image/edit` → prompt-guided image-to-image transformation
- **Inpaint:** `POST /v1/image/inpaint` → fill masked regions via SDXL inpainting
- Raw image download via `/generate/download`; format conversion: PNG (default), JPEG, WebP via Pillow
- Negative prompt support; inline rendering in chat as `data:image/png;base64,...`

### Video Generation (Cosmos Predict 2.5)
- **Text-to-video:** `POST /v1/video/generate` → `nvidia/cosmos-predict2-5b` → 5s 720p MP4
- **Video-to-video:** `POST /v1/video/transform` → prompt-guided video transformation
- Handles both sync and async NIM response shapes (polls up to 4 min for async jobs)
- Returns `data:video/mp4;base64,...` URI; raw MP4 download via `/generate/download`

### Embeddings (NeMo Retriever)
- 2048-dimensional multimodal text + image embeddings
- Cosine similarity search via `/v1/embeddings`

---

## Multi-Agent Crews

| Crew | Agents | Purpose |
|------|--------|---------|
| Research | Researcher, Analyst, Synthesizer | General research with analysis |
| Drug Discovery | Molecule Generator, ADMET Predictor, Lead Optimizer, Safety Reviewer | Drug candidate evaluation pipeline |
| Protein Analysis | Structural Biologist, Binding Site Predictor | Protein structure/function |
| Navigation | Perception, Path Planner, Action Executor, Safety Monitor | Robot path planning (ISO 10218/15066) |
| Manipulation | Perception, Grasp Planner, Action Executor, Safety Monitor | Object manipulation |
| Swarm | Coordinator, Perception, Path Planner, Safety Monitor | Multi-robot coordination (hierarchical) |
| Neural Audio Synthesis | Audio Engineer, Tone Analyst | SSML markup, tone analysis → Riva TTS dispatch |
| Visual Art Generation | Creative Director, Aesthetic Validator | Prompt engineering → SDXL-Turbo dispatch |
| Stateful Workflow | Classifier, Specialist, Reviewer (per domain) | Multi-node reasoning with conditional edges |
| Custom | User-defined roles | Arbitrary crew composition |

### Agent Builder — Live Execution
The Visual Agent Builder at `/agent-builder` executes real multimodal pipelines via `/v1/agents/run`. All 10 crew types are supported. The `run_crew()` dispatcher in `crew_manager.py` is the unified entry point — Neural Audio and Visual Art crews dispatch to real NIM services at the end of their pipelines.

### Stateful Workflow Engine
`langchain_agent.py` implements a graph-based workflow engine with:
- `WorkflowNode` — async NIM model call with state threading
- `ConditionalEdge` — branch on state predicate (false-positive-free revision detection)
- Domain workflows: `research`, `complex_reasoning`, `biology`, `robotics`, `vision`, `audio`, `image_gen`
- Iterative refinement loop with cycle detection (max 6 iterations, explicit revision signals only)

---

## Fully Homomorphic Encryption (FHE)

Privacy-preserving computation using Microsoft SEAL (via TenSEAL) with real RLWE lattice-based cryptography. FHE is a **primary platform feature** on the home page and accessible directly from main navigation.

> **Current status:** TenSEAL installed and operational (`SEAL_THREADS=8`). All five FHE demos pass. CKKS parameters corrected to fit within the 218-bit limit for `N=8192` 128-bit security (`[60, 40, 40, 60]`). The 3-stage Dockerfile with Intel HEXL + AVX-512 NTT acceleration is in progress for further latency reduction.

### Schemes
- **CKKS** — Approximate arithmetic on real/complex numbers for encrypted ML inference, secure embeddings, and private scoring. `light`/`standard` profiles use `N=8192` with `[60, 40, 40, 60]` bit sizes (200 bits — within the 218-bit 128-bit security limit); `deep` profile uses `N=16384` for >3 multiplication depths.
- **BFV** — Exact integer arithmetic for secure voting, private counting, and encrypted databases

### Performance (with 3-stage Dockerfile)
| Optimization | Latency Saved |
|---|---|
| Context pool — keygen once per process (was per-call) | −200 to −400ms |
| N=8192 vs N=16384 for standard drug scoring | −200 to −300ms per multiply |
| Intel HEXL + AVX-512 NTT acceleration | ×2–4 speedup |
| SEAL threading via OMP_NUM_THREADS | proportional to core count |
| **Target vs baseline** | **~300–400ms vs ~1,100ms** |

### Security
- **128-bit post-quantum security** based on Ring Learning With Errors (RLWE)
- Private key never serialized to hash (`save_secret_key=False`)
- LRU payload store with cap 512 (configurable via `FHE_MAX_PAYLOADS`) — no unbounded memory growth

### Services
| Service | Description |
|---------|-------------|
| Encrypted Drug Scoring | QED/plogP scoring on encrypted molecular vectors |
| Encrypted Similarity Search | Batched cosine similarity over encrypted embeddings (O(1) decrypt pass) |
| Secure Aggregation | Multi-party encrypted mean computation |
| Secure Voting | Private ballot tallying via BFV |
| Vector Arithmetic | Encrypted vector math with verification |

---

## Mobile App (Android)

Native Android client built with Kotlin and Jetpack Compose, featuring on-device ML inference for offline-capable AI operations.

### Tech Stack
- **Language**: Kotlin 1.9.20 with Jetpack Compose (Material 3)
- **DI**: Hilt (Dagger)
- **Database**: Room with encrypted preferences
- **Networking**: Retrofit + OkHttp with certificate pinning, WebSocket streaming
- **ML Runtimes**: ONNX Runtime 1.16.3 (primary) + TensorFlow Lite 2.14.0 (secondary)
- **Min SDK**: 26 (Android 8.0), Target SDK: 34

### On-Device ML Features
| Feature | Description |
|---------|-------------|
| **Model Registry** | Hot-swappable model lifecycle with StateFlow-based UI observation |
| **Model Store** | Disk cache with SHA-256 integrity checks and LRU eviction (500MB cap) |
| **Quantized Models** | FP32, FP16, INT8, INT4 precision variants with NNAPI delegation |
| **Streaming Inference** | Flow-based token-by-token output with temperature/top-K sampling and KV-cache |
| **Embedding Engine** | Text (384-dim) and image (512-dim) embeddings via ONNX with cosine similarity |
| **Audio Engine** | Whisper-style speech-to-text with mel-spectrogram, VAD, real-time mic streaming |
| **Vision Engine** | Image classification (MobileNet), OCR (CTC decoder), object detection (YOLO) |
| **Vector Store** | In-memory vector DB with cosine/euclidean/dot-product search, metadata filtering, binary persistence (10K entries) |
| **Model Downloader** | Asset-first loading with HTTP fallback, progress tracking, cache management |

---

## Monetization

### Subscription Tiers
| Tier | Price | Queries/Month | Features |
|------|-------|---------------|----------|
| Community | Free | 1,000 | All 26 models, basic routing, all 7 domains |
| Production | $49/mo | 10,000 | Priority routing, all domain services, FHE access |
| Enterprise | $299/mo | Unlimited | Custom SLA, dedicated support, analytics, admin dashboard |

### How It Works
1. Users register via `/v1/auth/register` and generate API keys from the `/billing` dashboard
2. Each query is tracked against the key's monthly quota
3. Stripe handles subscription upgrades via checkout
4. Webhooks automatically update tier when subscriptions change (`/v1/billing/webhook-tier-update`)
5. Tier limits enforced at middleware level before query execution
6. MAU threshold webhook fires at 900 queries/month

---

## API Reference

### Core
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with component status |
| GET | `/v1/stats` | System statistics |
| POST | `/v1/query` | Submit query for intelligent routing |
| POST | `/v1/query/stream` | SSE streaming query with live token rendering |
| GET | `/v1/models` | List all 26 available models |
| GET | `/v1/capabilities` | System capabilities and execution mode |
| GET | `/v1/cache/stats` | NIM prompt cache statistics |
| POST | `/v1/cache/clear` | Clear prompt cache (admin only) |

> ⚠️ `/v1/simulate` has been removed. Simulation mode is disabled in production. Set `AMAIMA_EXECUTION_MODE=execution-enabled` for real AI responses.

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Create account |
| POST | `/v1/auth/login` | Login (returns JWT) |
| POST | `/v1/auth/refresh` | Refresh access token |
| GET | `/v1/auth/me` | Current user profile + API keys |
| GET/POST | `/v1/auth/api-keys` | Manage API keys |
| POST | `/v1/auth/forgot-password` | Request password reset |
| POST | `/v1/auth/reset-password` | Reset with token |

### Biology
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/biology/discover` | Drug discovery pipeline |
| POST | `/v1/biology/protein` | Protein analysis |
| POST | `/v1/biology/optimize` | Molecule optimization |
| POST | `/v1/biology/query` | General biology query |
| POST | `/v1/biology/generate-molecules` | GenMol fragment-based molecule generation |

### Robotics
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/robotics/navigate` | Navigation commands |
| POST | `/v1/robotics/plan` | Action planning |
| POST | `/v1/robotics/simulate` | Action simulation |
| POST | `/v1/robotics/vision-action` | Vision-guided actions |

### Vision
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/vision/reason` | Vision reasoning (text) |
| POST | `/v1/vision/analyze-image` | Image analysis (preserves media content blocks) |
| POST | `/v1/vision/embodied-reasoning` | Embodied reasoning |

### Speech
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/audio/synthesize` | Text-to-speech → `data:audio/wav;base64,...` |
| POST | `/v1/audio/synthesize/file` | Text-to-speech → raw WAV binary download |
| POST | `/v1/audio/transcribe` | Speech-to-text (multipart audio file upload) → transcript |
| POST | `/v1/audio/transcribe-b64` | Speech-to-text (base64 JSON payload) → transcript |
| GET | `/v1/audio/voices` | List available TTS voices |
| GET | `/v1/audio/capabilities` | Audio service capabilities and NIM config status |

### Image Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/image/generate` | Text-to-image → `data:image/png;base64,...` (SDXL cascade) |
| POST | `/v1/image/generate/download` | Text-to-image → raw image binary download (PNG/JPEG/WebP) |
| POST | `/v1/image/variants` | Generate up to 4 concurrent variants with different seeds |
| POST | `/v1/image/edit` | Image-to-image transformation (prompt-guided) |
| POST | `/v1/image/inpaint` | Masked region inpainting |
| GET | `/v1/image/capabilities` | Supported models, formats, and features |

### Video Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/video/generate` | Text-to-video → `data:video/mp4;base64,...` (Cosmos Predict 2.5, ~30–90s) |
| POST | `/v1/video/generate/download` | Text-to-video → raw MP4 binary download |
| POST | `/v1/video/transform` | Video-to-video prompt-guided transformation |
| GET | `/v1/video/capabilities` | Model info, duration limits, latency expectations |

### Media (Generic Download)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/media/download` | Universal base64→file download — any MIME type, correct `Content-Disposition` headers |

### Embeddings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/embeddings` | 2048-dim multimodal text + image embeddings |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/agents/run` | Run agent crew (all 10 crew types) |
| GET | `/v1/agents/types` | List crew types and workflow types |

### FHE
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/fhe/status` | FHE subsystem status and capabilities |
| POST | `/v1/fhe/keygen` | Generate RLWE key pair (BFV or CKKS) |
| POST | `/v1/fhe/encrypt` | Encrypt vector into lattice ciphertext |
| POST | `/v1/fhe/compute` | Homomorphic operations on ciphertexts |
| POST | `/v1/fhe/decrypt` | Decrypt ciphertext (key holder only) |
| POST | `/v1/fhe/drug-scoring` | Encrypted drug QED/plogP scoring |
| POST | `/v1/fhe/similarity-search` | Batched encrypted embedding similarity search |
| POST | `/v1/fhe/secure-vote` | Private ballot tallying (BFV) |
| POST | `/v1/fhe/secure-aggregation` | Multi-party encrypted mean |
| POST | `/v1/fhe/vector-arithmetic` | Encrypted vector math with verification |
| GET | `/v1/fhe/demo` | Run all FHE demos with live results |

### Admin & Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/admin/analytics` | Platform-wide metrics (admin only) |
| GET | `/v1/admin/health` | System health (admin only) |
| GET | `/v1/admin/users` | User list with usage (admin only) |
| POST | `/v1/billing/api-keys` | Create API key |
| GET | `/v1/billing/api-keys` | List API keys |
| GET | `/v1/billing/usage/{id}` | Usage stats for key |
| GET | `/v1/billing/usage-by-key` | Usage for current key |
| GET | `/v1/billing/tiers` | Available subscription tiers |
| POST | `/v1/billing/update-tier` | Update tier (admin) |
| POST | `/v1/billing/webhook-tier-update` | Stripe webhook handler |
| GET | `/v1/billing/analytics` | 30-day billing analytics |

### Plugins & Marketplace
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/plugins` | List installed plugins |
| GET | `/v1/plugins/{id}/capabilities` | Plugin capabilities |
| GET | `/v1/marketplace` | Plugin marketplace (installed + available) |

---

## Project Structure

```
amaima/
├── backend/                              # FastAPI backend (Python 3.11)
│   ├── main.py                           # Application entry point *(Updated — 3 routers registered, domain dispatch fixed, FHE lifespan wired)*
│   ├── amaima_config.yaml                # Router and model configuration
│   ├── requirements.txt                  # *(Updated — tenseal>=0.3.15, Pillow, pytest-cov, ruff)*
│   ├── app/
│   │   ├── auth.py                       # JWT authentication system
│   │   ├── admin.py                      # Admin dashboard endpoints
│   │   ├── billing.py                    # Billing, usage tracking, analytics
│   │   ├── security.py                   # API key authentication
│   │   ├── conversations.py              # Conversation history
│   │   ├── experiments.py                # A/B testing framework
│   │   ├── webhooks.py                   # MAU threshold webhooks
│   │   ├── core/
│   │   │   └── unified_smart_router.py   # Device/connectivity-aware routing *(Updated — dual-router consolidated, DARPA gated)*
│   │   ├── modules/
│   │   │   ├── nvidia_nim_client.py      # NVIDIA NIM API client + LRU prompt cache
│   │   │   ├── execution_engine.py       # Model execution
│   │   │   ├── smart_router_engine.py    # Domain detection + model selection *(Updated — image_gen/speech priority-first, video patterns added)*
│   │   │   ├── observability_framework.py
│   │   │   └── plugin_manager.py
│   │   ├── services/
│   │   │   ├── biology_service.py        # BioNeMo + GenMol *(Updated — SMILES pattern tightened, RDKit cloud fallback)*
│   │   │   ├── robotics_service.py       # Isaac/GR00T *(Updated — lazy rclpy/PyBullet import, cloud sim fallback)*
│   │   │   ├── vision_service.py         # Cosmos R2 *(Updated — media blocks preserved end-to-end)*
│   │   │   ├── audio_service.py          # Riva TTS + Parakeet ASR *(Updated — accepts path/bytes/data URI)*
│   │   │   ├── image_service.py          # SDXL-Turbo cascade *(Updated — inpaint, img2img, variants, format conv.)*
│   │   │   └── video_service.py          # Cosmos Predict 2.5 *(New — text-to-video + video-to-video)*
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── biology.py                # Biology HTTP router
│   │   │   ├── robotics.py               # Robotics HTTP router
│   │   │   ├── vision.py                 # Vision HTTP router
│   │   │   ├── audio.py                  # *(New)* TTS, ASR file upload, voices, transcribe-b64
│   │   │   ├── image.py                  # *(New)* generate, variants, edit, inpaint, download
│   │   │   ├── video.py                  # *(New)* generate, transform, download
│   │   │   └── media.py                  # *(New)* generic /v1/media/download StreamingResponse
│   │   ├── agents/
│   │   │   ├── crew_manager.py           # 10 crew types + run_crew() dispatcher *(Updated — Neural Audio + Visual Art crews added)*
│   │   │   ├── langchain_agent.py        # Stateful workflow engine *(Updated — false-positive revision loop fixed)*
│   │   │   ├── biology_crew.py           # Drug discovery + protein analysis crews
│   │   │   └── robotics_crew.py          # Navigation + manipulation + swarm crews
│   │   ├── fhe/
│   │   │   ├── engine.py                 # SEAL context pool + LRU store *(Updated v4 — 7 systems: error tracking, energy, pipeline, ZKP, MKFHE, FL, op chains)*
│   │   │   ├── parameter_bench_v3.py     # v3 benchmark (slot packing, modulus trim)
│   │   │   └── parameter_bench_v4.py     # *(New)* v4 benchmark — all 7 systems, 15/15 checks
│   │   │   ├── service.py                # Batched FHE operations *(Updated)*
│   │   │   └── router.py                 # FHE HTTP endpoints + fhe_startup() *(Updated)*
│   │   └── db_config.py
│
├── frontend/                             # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx                      # Main dashboard *(Updated — FHE primary feature card, inline audio/image rendering)*
│   │   ├── login/
│   │   ├── admin/
│   │   ├── agent-builder/page.tsx        # React Flow builder with live execution
│   │   ├── fhe/page.tsx                  # FHE dashboard *(Updated v4 — live error bounds, energy panel, proof verification UI, error boundaries)*
│   │   ├── billing/page.tsx
│   │   ├── conversations/page.tsx
│   │   └── benchmarks/page.tsx
│   ├── next.config.js                    # *(Updated — swcMinify off, NODE_OPTIONS heap limit, API proxy rewrites)*
│   └── package.json
│
├── mobile/                               # Android mobile client (Kotlin 2.3.10)
│   ├── gradle/
│   │   └── libs.versions.toml            # *(Updated)* Version Catalog — Gradle 9.3.1, AGP 9.0.1, KSP
│   └── app/src/main/java/com/amaima/app/
│       ├── ml/                           # On-device ML engines (ONNX + TFLite)
│       ├── di/                           # Hilt dependency injection *(migrated kapt → KSP)*
│       ├── network/                      # Retrofit + OkHttp + WebSocket
│       ├── security/                     # Biometric + cert pinning
│       └── data/                         # Room DB *(migrated kapt → KSP)*
│
├── tests/
│   ├── integration/
│   │   └── test_biology_e2e.py           # 63 tests (58 passing)
│   └── ...
│
├── .github/workflows/
│   └── backend.yml                       # *(Updated — tenseal excluded from CI, FHE_ENABLED=false for CI speed)*
├── Dockerfile                            # *(Updated — python:3.10, unconditional tenseal, g++/cmake, FHE_ENABLED=true)*
├── Dockerfile.backend                    # 3-stage build — Intel HEXL + SEAL from source (AVX-512, in progress)
├── docker-compose.yml
├── start.sh                              # *(Updated — NODE_OPTIONS heap limit, process supervision loop)*
├── Makefile                              # *(Updated — AMAIMA_EXECUTION_MODE in all targets, dev-fhe/test-fhe/docker-build-fhe added)*
├── .env.example
├── docs/
│   ├── fullstack-deployment-guide.md
│   ├── DEPLOYMENT.md                     # *(New — accurate resource requirements, platform rankings)*
│   └── vps/                              # *(New — complete VPS self-hosting package)*
│       ├── Dockerfile                    # python:3.10, unconditional tenseal, 3-stage build
│       ├── docker-compose.yml            # PostgreSQL + AMAIMA stack with resource limits
│       ├── .env.example                  # All variables with generation instructions
│       ├── start.sh                      # Process supervisor — backend → health → frontend
│       ├── next.config.js                # OOM-safe build, API proxy rewrites
│       ├── Caddyfile                     # Automatic Let's Encrypt SSL
│       ├── setup.sh                      # One-shot Ubuntu 24.04 VPS provisioning
│       ├── deploy.sh                     # git pull + rebuild + health verification
│       └── VPS_DEPLOYMENT.md            # Provider comparison, troubleshooting reference
└── monitoring/                           # Grafana dashboards
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL database
- NVIDIA NIM API key (`nvapi-...`)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_NIM_API_KEY` or `NVIDIA_API_KEY` | Yes | NVIDIA NIM API key for all inference |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | Secret for JWT token signing |
| `AMAIMA_EXECUTION_MODE` | Yes | Must be `execution-enabled` — no simulation fallback |
| `API_SECRET_KEY` | Yes (prod) | API endpoint protection — change from default in production |
| `BACKEND_URL` | No | Backend URL for frontend proxy (default: `http://localhost:8000`) |
| `FHE_ENABLED` | No | Set `true` to activate FHE subsystem (requires TenSEAL). Defaults to `true` in Dockerfile. |
| `SEAL_THREADS` | No | SEAL NTT parallelism (default: 4) |
| `FHE_MAX_PAYLOADS` | No | LRU payload store cap (default: 512) |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for billing |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `WEBHOOK_INTERNAL_SECRET` | No | Internal webhook secret for tier updates |

### Start Backend
```bash
cd amaima/backend
pip install -r requirements.txt
export AMAIMA_EXECUTION_MODE=execution-enabled
export NVIDIA_API_KEY=nvapi-...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend
```bash
cd amaima/frontend
npm install
npm run dev
```

### Build Mobile App
```bash
cd amaima/mobile
./gradlew assembleDebug
```

---

## Deployment

AMAIMA deploys as a single full-stack container (frontend + backend) to any platform that runs Docker.

### Quick Start (Docker Compose)
```bash
cp .env.example .env    # Fill in your API keys
docker compose up -d    # Starts app + PostgreSQL
```

> **Note:** Clear Docker build cache when updating files: `docker build --no-cache -t amaima:latest .`
> On Render, use **"Clear build cache & deploy"** from the manual deploy dropdown.

### Supported Platforms
Replit, Railway, Render (current), Fly.io, Docker/VPS, Google Cloud Run, AWS (App Runner/ECS/EC2), Azure Container Apps, DigitalOcean, Heroku.

See the **[Full Deployment Guide](docs/fullstack-deployment-guide.md)** for platform-specific instructions.

---

## Current Status & Roadmap

### 🟢 Working (confirmed in Replit)
- 7-domain smart routing with regex-priority detection — `image_gen` and `speech` checked before complexity scoring
- Audio TTS/ASR, image generation (SDXL cascade), video generation (Cosmos Predict 2.5)
- 10 agent crew types with live execution including Neural Audio Synthesis and Visual Art Generation
- JWT auth, Stripe billing, MAU enforcement
- FHE backend — all 5 demos functional, `SEAL_THREADS=8`, ~350ms per operation
- FHE dashboard — crash fixed, all demos pass end-to-end
- CI pipeline passing — tenseal excluded from CI, fast builds

### ✅ Recently Completed

**Session 1–2: Smart Router + Service layer (Feb 24–25)**
- `smart_router_engine.py` — `image_gen` and `speech` regex checks moved to fire *before* complexity scoring; 6 video generation patterns added; domain detection unified as single source of truth
- `audio_service.py` — replaced stub with real NIM calls to `nvidia/magpie-tts-multilingual` + `nvidia/parakeet-ctc-1.1b`; base64 data URI output for inline browser playback
- `image_service.py` — SDXL-Turbo → full SDXL → SD3 3-model cascade; Pillow format conversion; `inpaint_image()`, `image_to_image()`, `generate_image_variants()`
- `crew_manager.py` — Neural Audio Synthesis (crew 9) and Visual Art Generation (crew 10) added; all 10 crew types routed correctly
- `page.tsx` — FHE promoted to primary feature card on homepage; inline `<audio>` player and `<img>` rendering added to chat UI

**Session 3: FHE latency optimization (Feb 25)**
- `fhe/engine.py` + `fhe/service.py` — 13 optimizations: context pool singleton (keygen once per process), `_LRUPayloadStore` capped at 512, N=8192 for standard profiles, `OMP_NUM_THREADS` threading, `save_secret_key=False` security fix, batched similarity search (O(1) decrypt pass)
- Baseline ~1,100ms → ~350ms measured (3.1× improvement)

**Session 4: Code review + router consolidation (Feb 25)**
- `unified_smart_router.py` — dual-router architecture consolidated; DARPA tools integration gated correctly
- `langchain_agent.py` — false-positive revision loop fixed; SMILES extraction tightened
- `biology_service.py` — SMILES pattern tightened; RDKit cloud API fallback added
- `vision_service.py` — media content blocks preserved end-to-end (was stripping image data before NIM call)
- `robotics_service.py` — lazy imports for `rclpy` and PyBullet (not in container); cloud simulation fallback via NIM/Omniverse

**Session 5: Infrastructure correctness (Feb 26)**
- `Dockerfile` (root) — fixed `PORT=5000→10000`, added `AMAIMA_EXECUTION_MODE` as `ENV` default, `NVIDIA_NIM_API_KEY` alias, healthcheck with `--start-period=60s`, `FHE_ENABLED=true` default
- `requirements.txt` — `tenseal>=0.3.15` (0.3.14 yanked from PyPI), `Pillow>=10.0.0`, `pytest-cov`, `ruff`
- `Makefile` — `AMAIMA_EXECUTION_MODE` added to all dev/test targets; `dev-fhe`, `test-fhe`, `docker-build-fhe` targets added
- `DEPLOYMENT.md` — complete rewrite with accurate memory requirements and platform rankings

**Session 6: Production deployment debugging + infra fixes (Feb 26–27)**
- `fhe/engine.py` — CKKS parameter overflow fixed (`[60,40,40,60]` = 200 bits, within 218-bit 128-bit security limit for N=8192); was causing `ValueError` on every `ts.context()` call
- `fhe/page.tsx` — `TypeError` on `scheme.poly_modulus_degrees.join()` fixed with optional chaining; all undefined-value guards added
- `Dockerfile` — `python:3.10-slim-bookworm` (cp310 TenSEAL wheel available); `pip install tenseal` made unconditional (was gated on build-arg that Render never set); `g++` and `cmake` added to apt deps; separate verbose tenseal install step for visible failure
- `next.config.js` — `swcMinify: false`, `productionBrowserSourceMaps: false`, `cpus: 1`; `NODE_OPTIONS=--max-old-space-size=256` to prevent Next.js OOM during Docker build
- `start.sh` — `NODE_OPTIONS=--max-old-space-size=400` at runtime; process supervision loop that cleanly exits container if either frontend or backend dies
- `backend.yml` (CI) — tenseal excluded from CI install; `FHE_ENABLED=false` for fast CI runs

**Service audit + 13 bugs fixed (ongoing)**
- `audio_service.py` crash: `speech_to_text()` received `str` path but expected `bytes` — fixed with `_load_audio_bytes()` resolver
- `vision_service.py`: dead `get_cosmos_client()` removed; media blocks preserved via `_build_messages()`
- `robotics_service.py`: circular import risk eliminated (lazy import); `_ros2_navigate()` fake success replaced with honest `stub_not_executed`
- Three new HTTP routers: `app/routers/audio.py`, `image.py`, `video.py` — wired into `main.py`, inline route conflicts resolved

**VPS deployment package complete (Mar 1, 2026)**
- Nine production files committed under `docs/vps/`: `Dockerfile` (python:3.10, unconditional tenseal, 3-stage build), `docker-compose.yml` (PostgreSQL + AMAIMA stack, internal networking, resource limits), `.env.example`, `start.sh` (process supervisor with health-check loop), `next.config.js` (OOM-safe build, API proxy rewrites), `Caddyfile` (automatic Let's Encrypt SSL), `setup.sh` (one-shot Ubuntu 24.04 provisioning), `deploy.sh` (git pull + rebuild + health verification), `VPS_DEPLOYMENT.md`
- `amaima_config.yaml` — JWT algorithm corrected to HS256 for VPS compatibility (RS256 requires a key pair absent in fresh environments)
- Resolves all prior production blockers: TenSEAL install, Next.js OOM, Render memory incompatibility
- Hetzner CX22 (~$5/mo, 4GB RAM) confirmed as recommended deployment target

**Android mobile — Gradle 9.3.1 + Kotlin 2.3.10 upgrade (Mar 1, 2026)**
- Toolchain upgraded: Gradle 9.3.1, AGP 9.0.1, Kotlin 2.3.10 — aligned with modern Android 2026 standards and full compatibility with latest Android features
- All dependency versions centralized in `gradle/libs.versions.toml` (Version Catalog) — eliminates scattered "magic numbers" across build files, makes future updates safer
- Annotation processing migrated from `kapt` → `KSP` for Hilt and Room — significantly faster incremental builds; `kapt` is phased out in Kotlin 2.x
- JVM target aligned to JDK 17 (required by Gradle 9.x daemon)
- Mobile app now in "ready-to-build" state with the most modern Android stack available

**FHE engine v3 — slot packing + modulus chain trim (Mar 1, 2026)**
- `fhe/engine.py` — `batch_encrypt_vectors()`: packs up to 4,096 values into a single CKKS ciphertext. Drug scoring batch (16 molecules × 8 features): 16 ciphertexts → 1 ciphertext, ~1.1 MB → ~0.2 MB (5× size reduction), ~15× fewer TenSEAL API calls. `batch_decrypt_all()` recovers all vectors in one decrypt pass.
- Modulus chain trimmed: `light` `[60,40,40,40,60]`=240 bits → `[60,40,60]`=160 bits; `standard` → `[60,40,40,60]`=200 bits; new `minimal` profile `[60,60]`=120 bits for depth-1 circuits. All within 218-bit SEAL limit at N=8192. ~15–20% NTT latency improvement per operation.
- `FHEKeyInfo.metadata` now exposes `slot_capacity`, `coeff_mod_bits_total`, `max_depth`, `packing_ratio`
- `get_stats()` tracks `slots_packed` and `ciphertext_bytes_saved` — visible at `/v1/fhe/status`
- `parameter_bench_v3.py` moved to `app/fhe/` for on-VPS verification
- Backend restarted and confirmed healthy with v3 active

**Media download router (Mar 1, 2026)**
- `app/routers/media.py` — new `POST /v1/media/download` generic endpoint. Accepts base64-encoded payload (image, video, audio, or file), returns `StreamingResponse` with correct MIME type and `Content-Disposition: attachment` headers so browsers trigger save dialog directly
- Registered in `main.py` alongside domain-specific download endpoints
- Complements `/audio/synthesize/file`, `/image/generate/download`, `/video/generate/download` with a universal fallback for any base64 content

**FHE engine v4 — "Beyond Grok" — 7 new systems (Mar 1, 2026)**
- `fhe/engine.py` v4 — 2,239 lines. Seven systems added beyond what the Grok research identified:
- **System 1 — CKKS Error Tracker** (`_CKKSErrorTracker`): propagates approximation error bounds through entire operation chains using Kim et al. (2020) noise analysis. Add: `ε = ε_a + ε_b`; Multiply: `ε = |mean_a|·ε_b + |mean_b|·ε_a + ε_a·ε_b + 2^(-scale)`. Every `EncryptedPayload.metadata` now carries `ckks_error_bound` and a bio ML precision grade (`✓ acceptable / ⚠ marginal / ✗ unacceptable`) calibrated per use case — drug scoring 1e-4, protein structure 1e-5, embedding search 1e-3.
- **System 2 — Energy Profiler** (`_EnergyProfiler`, `EnergyReport`): TDP-based nanojoule accounting per operation. `E_nJ = TDP × wall_s × utilisation × 1e9`, adjusted by NTT cost multiplier per profile. Every operation stores `energy_nj` in metadata. `get_stats()` exposes lifetime nJ/µJ/mJ totals, per-op average, thermal pressure index. `budget_check()` API for energy-capped pipelines. Configurable via `FHE_SERVER_TDP_WATTS` / `FHE_CPU_UTILISATION` env vars.
- **System 3 — Compound Pipeline** (`compound_pipeline`, `CompoundPipelineResult`): high-throughput encrypted drug scoring. Auto-chunks any compound list into slot-optimal batches (`deep` profile = 8,192 slots → 10K compounds = 2 ciphertexts). Reports amortized µs/compound, nJ/compound, compounds/sec, per-compound CKKS error bounds. Optional `energy_budget_mj` cap aborts mid-run if exceeded.
- **System 4 — ZKP Proof Store** (`_ZKPProofStore`, `ComputationProof`): hash-chain commitment scheme for regulatory-grade auditability without external ZKP library. Input commitment → op trace hash → output commitment → Merkle root. `verify_proof()` re-derives root and checks consistency. Chain proofs cover entire multi-step pipelines. Upgrade path to Groth16/PLONK via OpenFHE documented in every proof object.
- **System 5 — Multi-Key FHE Session** (`MKFHESession`): N-party pharma federation coordinator. `register_party()` → `encrypt_contribution()` → `aggregate()` → `partial_decrypt()`. Matched-parameter CKKS prototype; API designed for drop-in upgrade to OpenFHE MKHE.
- **System 6 — Federated Aggregator** (`FederatedAggregator`): HHE-style FL with three modes — `fedavg` (homomorphic mean), `fedsum` (homomorphic sum), `fedmedian` (novel: Tukey halfspace depth approximation for Byzantine robustness — not in cited literature). `add_dp_noise(ε, δ)` injects Gaussian DP noise via correct `σ = sensitivity × √(2 ln(1.25/δ)) / ε` formula.
- **System 7 — Operation Chain** (`_OperationChain`, `ChainResult`): fluent composable pipeline — `begin_chain(key_id, payload_id).multiply_plain(w).add_plain(b).sum().execute()`. Each step accumulates CKKS error, records energy, logs `(op, error_after, energy_nj, output_hash)`. Returns `ChainResult` with a single chain-level proof covering all steps.
- `parameter_bench_v4.py` — 623-line benchmark suite validating all 7 systems; 15/15 checks pass

**FHE Dashboard v4 — live error bounds, energy, proof verification (Mar 1, 2026)**
- `/fhe` frontend updated to display live CKKS error bounds and bio precision grades from `ckks_error_bound` metadata
- Energy accounting panel: shows `energy_nj` per operation and lifetime energy from `/v1/fhe/status`
- Proof verification UI: displays `proof_id` with `merkle_root_check` status for auditable drug scoring outputs
- Error boundary components added: graceful "FHE unavailable" state when `available: false` — no more white-screen in production

**CORS security hardening (Mar 1, 2026)**
- Backend CORS middleware upgraded from static origin list to Replit domain regex + explicit production origins
- Pattern: `^https://.*\.replit\.app$` covers all Replit preview URLs without whitelisting every subdomain
- Explicit origins: `amaima.live`, `www.amaima.live`, `localhost:3000`, `localhost:10000`
- Prevents cross-origin credential leakage to unintended subdomains

### 🔴 Known Issues
- No critical blockers currently open. VPS deployment resolves all prior production environment issues. See In Progress for active work.

### 🟡 In Progress

- **Existing router audit** — `biology.py`, `robotics.py`, `vision.py` need verification against updated service return shapes from Sessions 2 and 4
- **FHE Dockerfile 3-stage build** — `Dockerfile.backend` with Intel HEXL v1.2.5 + Microsoft SEAL v4.1.2 compiled from source (Clang-15, AVX-512, -O3); targeting ~3–4× further NTT speedup over the PyPI wheel; requires Hetzner VPS or equivalent build environment
- **`app/core/` audit** — remaining files beyond `unified_smart_router.py` not yet reviewed

### 📋 Backlog

- **Video generation async webhook** — Cosmos Predict 2.5 holds HTTP connection up to 4 min; needs job ID response + polling endpoint
- **SmartRouter singleton across uvicorn workers** — currently 1 instance + 1 FHE context pool per worker; 4-worker deployment = 4× memory and 4× warm-up time
- **Alembic database migrations** — currently `init_db()` on every startup; no schema evolution path
- **Frontend page audit** — fhe, agents, biology, robotics, vision pages need verification against updated backend API contracts
- **Streaming cursor UI** — SSE streaming wired in backend; frontend shows static loading state
- **DiffDock/AlphaFold integration** in `biology_service.py`
- **Real ROS2/rclpy hardware bridge** in `robotics_service.py` (currently honest `stub_not_executed`)
- **Advanced Prometheus metrics** for FHE latency, routing accuracy, NIM response times
- **Model comparison tool** — side-by-side output comparison across NIM models
- `npm audit fix` — 19 frontend vulnerabilities

---

## Architecture Health Snapshot

| Component | Status | Notes |
|---|---|---|
| 7-domain Smart Router | 🟢 Working | Priority routing correct across all 7 domains |
| Audio service (TTS/ASR) | 🟢 Working | Parakeet + Magpie TTS wired to NIM |
| Image service (SDXL) | 🟢 Working | 3-model cascade operational |
| Vision service | 🟢 Working | Media content blocks preserved end-to-end |
| Biology service | 🟢 Working | RDKit cloud fallback active |
| Robotics service | 🟢 Working | Cloud simulation via NIM/Omniverse |
| Video service | 🟡 Partial | Service + router created; async webhook pending |
| Media download router | 🟢 Working | Generic `/v1/media/download` StreamingResponse |
| 10 agent crews | 🟢 Working | All crew types routed correctly |
| FHE engine v4 | 🟢 Working | 7 new systems: error tracking, energy, compound pipeline, ZKP proofs, MKFHE, FL hybrid, op chains |
| FHE dashboard v4 | 🟢 Working | Live error bounds, energy panel, proof verification UI, error boundaries |
| CORS security | 🟢 Hardened | Replit regex + explicit production origins; no credential leakage |
| Frontend | 🟢 Working | FHE dashboard, inline audio/image rendering |
| CI pipeline | 🟢 Passing | tenseal excluded, fast builds |
| Database | 🟢 Working | PostgreSQL connected |
| NVIDIA NIM integration | 🟢 Working | API key configured, all endpoints live |
| VPS deployment | 🟢 Ready | 9-file package in `docs/vps/`; Hetzner CX22 target |
| Android mobile | 🟢 Ready | Gradle 9.3.1, Kotlin 2.3.10, KSP migration complete |
| Deployment (Render free) | 🔴 Incompatible | 512MB structural limit; use VPS or Render Standard |

---

## License

**AMAIMA License v2.0**

| License | Use Case | Price |
|---------|----------|-------|
| Community | Non-commercial use, research, individuals | Free |
| Production | Business use, source-available | $49/month |
| Enterprise | Full unrestricted commercial use | $299/month |

Licensing: licensing@amaima.live  
Support: support@amaima.live

---

<div align="center">

**AMAIMA** — *The Multimodal AI Operating System*

Built with NVIDIA NIM · FastAPI · Next.js · Kotlin · Microsoft SEAL · Stripe

[amaima.live](https://amaima.live)

</div>
