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
- **TTS:** `POST /v1/audio/synthesize` → `nvidia/magpie-tts-multilingual` → `data:audio/wav;base64,...`
- **ASR:** `POST /v1/audio/transcribe` → `nvidia/parakeet-ctc-1.1b` → transcript text
- Neural audio playback rendered directly in chat interface

### Image Generation (SDXL)
- **Text-to-image:** `POST /v1/image/generate` → SDXL-Turbo (2 steps) with automatic cascade fallback to full SDXL → SD3
- Negative prompt support
- `inpaint_image()`, `image_to_image()`, `generate_image_variants()` (4 concurrent seeds)
- Format conversion: PNG (default), JPEG, WebP via Pillow
- Inline image rendering in chat interface as `data:image/png;base64,...`

### Video Generation (Cosmos Predict 2.5) *(New)*
- **Text-to-video:** `POST /v1/video/generate` → `nvidia/cosmos-predict2-5b` → 5s 720p MP4
- **Video-to-video:** `POST /v1/video/transform` → prompt-guided video transformation
- Handles both sync and async NIM response shapes (polls up to 4 min for async jobs)
- Returns `data:video/mp4;base64,...` URI

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

> **Current status:** TenSEAL not yet installed in the production container. Set `FHE_ENABLED=true` and deploy the 3-stage Dockerfile (Intel HEXL + SEAL from source) to activate. The system degrades gracefully — FHE endpoints return `503` rather than crashing when TenSEAL is unavailable.

### Schemes
- **CKKS** — Approximate arithmetic on real/complex numbers for encrypted ML inference, secure embeddings, and private scoring. `N=8192` standard profile; `N=16384` deep profile for >3 multiplication depths.
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
| POST | `/v1/audio/transcribe` | Speech-to-text (base64 PCM input) → transcript |

### Image Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/image/generate` | Text-to-image → `data:image/png;base64,...` (SDXL cascade) |

### Video Generation *(New)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/video/generate` | Text-to-video → `data:video/mp4;base64,...` (Cosmos Predict 2.5) |
| POST | `/v1/video/transform` | Video-to-video transformation |

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
│   ├── main.py                           # Application entry point
│   ├── amaima_config.yaml                # Router and model configuration
│   ├── requirements.txt
│   ├── app/
│   │   ├── auth.py                       # JWT authentication system
│   │   ├── admin.py                      # Admin dashboard endpoints
│   │   ├── billing.py                    # Billing, usage tracking, analytics
│   │   ├── security.py                   # API key authentication
│   │   ├── conversations.py              # Conversation history
│   │   ├── experiments.py                # A/B testing framework
│   │   ├── webhooks.py                   # MAU threshold webhooks
│   │   ├── core/
│   │   │   └── unified_smart_router.py   # Device/connectivity-aware routing *(Updated)*
│   │   ├── modules/
│   │   │   ├── nvidia_nim_client.py      # NVIDIA NIM API client + LRU prompt cache
│   │   │   ├── execution_engine.py       # Model execution
│   │   │   ├── smart_router_engine.py    # Domain detection + model selection *(Updated)*
│   │   │   ├── observability_framework.py
│   │   │   └── plugin_manager.py
│   │   ├── services/
│   │   │   ├── biology_service.py        # BioNeMo + GenMol *(Updated)*
│   │   │   ├── robotics_service.py       # Isaac/GR00T *(Updated)*
│   │   │   ├── vision_service.py         # Cosmos R2 *(Updated)*
│   │   │   ├── audio_service.py          # Riva TTS + Parakeet ASR *(Updated)*
│   │   │   ├── image_service.py          # SDXL-Turbo cascade *(Updated)*
│   │   │   └── video_service.py          # Cosmos Predict 2.5 *(New)*
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── biology.py                # Biology HTTP router
│   │   │   ├── robotics.py               # Robotics HTTP router
│   │   │   ├── vision.py                 # Vision HTTP router
│   │   │   ├── audio.py                  # ⚠️ Needs to be created
│   │   │   ├── image.py                  # ⚠️ Needs to be created
│   │   │   └── video.py                  # ⚠️ Needs to be created
│   │   ├── agents/
│   │   │   ├── crew_manager.py           # 10 crew types + run_crew() dispatcher *(Updated)*
│   │   │   ├── langchain_agent.py        # Stateful workflow engine *(Updated)*
│   │   │   ├── biology_crew.py           # Drug discovery + protein analysis crews
│   │   │   └── robotics_crew.py          # Navigation + manipulation + swarm crews
│   │   ├── fhe/
│   │   │   ├── engine.py                 # SEAL context pool + LRU store *(Updated)*
│   │   │   ├── service.py                # Batched FHE operations *(Updated)*
│   │   │   └── router.py                 # FHE HTTP endpoints + fhe_startup() *(Updated)*
│   │   └── db_config.py
│
├── frontend/                             # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx                      # Main dashboard (FHE primary feature) *(Updated)*
│   │   ├── login/
│   │   ├── admin/
│   │   ├── agent-builder/page.tsx        # React Flow builder with live execution
│   │   ├── fhe/page.tsx                  # ⚠️ Crashing — needs error boundaries
│   │   ├── billing/page.tsx
│   │   ├── conversations/page.tsx
│   │   └── benchmarks/page.tsx
│   ├── next.config.js
│   └── package.json
│
├── mobile/                               # Android mobile client (Kotlin)
│   └── app/src/main/java/com/amaima/app/
│       ├── ml/                           # On-device ML engines
│       ├── di/                           # Hilt dependency injection
│       ├── network/                      # Retrofit + WebSocket
│       ├── security/                     # Biometric + cert pinning
│       └── data/
│
├── tests/
│   ├── integration/
│   │   └── test_biology_e2e.py           # 63 tests (58 passing)
│   └── ...
│
├── Dockerfile                            # 3-stage build (⚠️ HEXL+SEAL stage pending)
├── docker-compose.yml
├── start.sh
├── .env.example
├── docs/
│   └── fullstack-deployment-guide.md
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
| `FHE_ENABLED` | No | Set `true` to activate FHE subsystem (requires TenSEAL) |
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

### 🟢 Production (Live at amaima.live)
- 7-domain smart routing with regex-priority detection
- All NIM model calls real — no simulation anywhere
- Audio (TTS/ASR), image generation (SDXL cascade), video generation (Cosmos Predict 2.5)
- 10 agent crew types with live execution
- JWT auth, Stripe billing, MAU enforcement
- FHE backend (engine + service + router) with context pool and batched search

### 🔴 Known Issues
- **FHE dashboard (`/fhe`) crashing** — client-side exception; needs error boundaries for graceful TenSEAL-absent state
- **TenSEAL not installed in container** — FHE endpoints return `503` until 3-stage Dockerfile deployed
- **`video_service.py` not yet wired** to router patterns or `main.py` domain dispatch

### 🟡 In Progress
- **FHE Dockerfile 3-stage build** — Intel HEXL v1.2.5 + Microsoft SEAL v4.1.2 compiled with Clang-15, AVX-512, -O3; targeting ~300ms per FHE operation (down from ~1.1s baseline)
- **Missing routers** — `app/routers/audio.py`, `image.py`, `video.py` need to be created
- **Existing router audit** — `biology.py`, `robotics.py`, `vision.py` need review against updated services
- **`app/core/` audit** — remaining files beyond `unified_smart_router.py` not yet reviewed
- **FHE frontend** — all `/fhe` page.tsx files need error boundaries and degraded state UI

### 📋 Backlog
- Video generation async webhook (avoid holding HTTP connections up to 4 min)
- SmartRouter singleton across uvicorn workers (currently 1 instance per worker)
- Alembic database migrations (currently `init_db()` on every startup)
- Streaming cursor UI (typing animation for SSE mode)
- Model comparison tool (side-by-side output comparison)
- DiffDock/AlphaFold integration in `biology_service.py`
- Real ROS2/rclpy hardware bridge in `robotics_service.py`
- Advanced Prometheus metrics for FHE latency and routing accuracy
- `outputFileTracingRoot` in `next.config.js` to silence duplicate lockfile warning
- `npm audit fix` for 19 frontend vulnerabilities

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
