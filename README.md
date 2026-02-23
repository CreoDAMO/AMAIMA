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

</div>

---

## Overview

AMAIMA is an enterprise-grade multimodal AI operating system that intelligently routes queries across **26 NVIDIA NIM models** spanning **6 intelligence domains**. It combines a smart routing engine, live multi-agent orchestration, Fully Homomorphic Encryption (FHE), and specialized domain services for biology, robotics, vision, audio, and image generation — backed by a full-featured Android mobile client with on-device ML inference.

### What It Does

- **Smart Query Routing** — Analyzes query complexity (TRIVIAL to EXPERT) and automatically routes to the optimal model across 6 domains
- **6-Domain AI** — Dedicated services for Biology (BioNeMo/GenMol), Robotics (Isaac/GR00T), Vision (Cosmos R2), Speech (Riva ASR/TTS), Image Generation (SDXL-Turbo), and Embeddings (NeMo Retriever)
- **Live Multi-Agent Orchestration** — Agent Builder directly executes multimodal pipelines via the agent engine, with specialized Audio and Visual Art crews
- **Fully Homomorphic Encryption** — Privacy-preserving encrypted inference via Microsoft SEAL (TenSEAL), prominently integrated across the platform
- **Multimodal Frontend** — Rich media rendering for generated images and neural audio playback directly in the chat interface
- **Monetization Built-In** — Three-tier subscription system with Stripe billing, JWT authentication, API key management, and usage tracking
- **On-Device ML** — Android app with ONNX Runtime + TFLite for offline embeddings, speech-to-text, vision, and vector search
- **Cloud-First** — No GPU required; all cloud inference runs through NVIDIA NIM APIs

---

## Architecture

```
                    +------------------+
                    |   Next.js 16     |
                    |   Frontend       |
                    |   (port 5000)    |
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
| Engine    |       |           |       | Admin      |
+-----------+       +-----------+       +------------+
                         |
     +-------------------+--------------------+
     |          |         |         |         |
+----+----+ +---+---+ +---+---+ +---+---+ +--+----+
| Biology | |Robotics| | Vision| | Audio | | Image |
| BioNeMo | |Isaac/  | |Cosmos | | Riva  | | Gen   |
| GenMol  | |GR00T   | |  R2   | | ASR/  | |SDXL-  |
|         | |        | |       | | TTS   | |Turbo  |
+---------+ +--------+ +-------+ +-------+ +-------+
                    |
            +-------+-------+
            |               |
    +-------+----+  +-------+------+
    | FHE        |  | NVIDIA NIM   |
    | Subsystem  |  | Cloud APIs   |
    | (TenSEAL)  |  |              |
    +------------+  +--------------+

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
| meta/llama-3.1-70b-instruct | 70B | Complex reasoning | $0.00088 |
| meta/llama-3.1-405b-instruct | 405B | Expert-level tasks | $0.005 |
| mistralai/mixtral-8x7b-instruct-v0.1 | 46.7B MoE | Cost-efficient complex | $0.0006 |
| google/gemma-2-9b-it | 9B | Lightweight/edge | $0.0001 |
| nvidia/nemotron-nano-9b-v2 | 9B | Edge/agentic AI | $0.0001 |

### Vision/Multimodal Models
| Model | Parameters | Best For |
|-------|-----------|----------|
| nvidia/cosmos-reason2-7b | 7B | Vision-language reasoning, embodied AI |
| nvidia/cosmos-predict2-14b | 14B | Video generation, future prediction |
| nvidia/llama-3.1-nemotron-nano-vl-8b | 8B | Multimodal understanding |

### Biology/Drug Discovery Models
| Model | Best For |
|-------|----------|
| nvidia/bionemo-megamolbart | Molecular generation, drug discovery |
| nvidia/bionemo-esm2 | Protein structure prediction |
| nvidia/genmol | Fragment-based molecule generation (SAFE format, QED/plogP optimization) |
| AlphaFold2 *(self-hosted)* | Protein structure prediction |
| DiffDock *(self-hosted)* | Molecular docking |

### Robotics Models
| Model | Best For |
|-------|----------|
| nvidia/isaac-gr00t-n1.6 | Humanoid robot control (VLA) |
| nvidia/alpamayo-1 | Autonomous vehicle reasoning (VLA) |
| Isaac Manipulator *(self-hosted)* | Object manipulation |

### Speech Models *(New)*
| Model | Best For |
|-------|----------|
| nvidia/riva-asr | Automatic speech recognition (ASR) |
| nvidia/riva-tts | Text-to-speech synthesis (TTS) |
| Riva ASR *(self-hosted)* | On-premise speech recognition |
| Riva TTS *(self-hosted)* | On-premise speech synthesis |

### Image Generation Models *(New)*
| Model | Best For |
|-------|----------|
| nvidia/sdxl-turbo | High-quality text-to-image generation |

### Embedding Models
| Model | Best For |
|-------|----------|
| nvidia/nemo-retriever-multimodal-embedding | 2048-dim text + image embeddings |
| NV-Embed *(self-hosted)* | On-premise multimodal embeddings |
| VILA *(self-hosted)* | Visual-language alignment |

---

## Smart Router

The routing engine classifies queries across five complexity levels and automatically routes to the optimal model:

| Level | Description | Routed To |
|-------|-------------|-----------|
| TRIVIAL | Simple factual queries | Llama 8B / Gemma 9B |
| SIMPLE | Basic explanations | Llama 8B |
| MODERATE | Multi-step reasoning | Llama 70B |
| COMPLEX | Domain expertise needed | Mixtral 8x7B / 70B |
| EXPERT | Specialized analysis | Llama 405B |

### Domain-Aware Routing
- **Biology** keywords (drug, protein, molecule, SMILES) → BioNeMo / GenMol
- **Vision** keywords (image, video, scene, visual) → Cosmos Reason2 7B
- **Robotics** keywords (robot, navigate, grasp, plan) → Isaac GR00T N1.6
- **Speech** keywords (audio, speech, transcribe, voice, speak, TTS, ASR) → Riva ASR/TTS *(New)*
- **Image Generation** keywords (generate image, draw, create picture, render) → SDXL-Turbo *(New)*
- **Embeddings** keywords (embed, similarity, search, retrieve) → NeMo Retriever
- **General** queries → Complexity-based model selection

---

## Domain Services

### Biology (BioNeMo + GenMol)
- Drug discovery pipeline with molecule generation
- Protein sequence analysis and structure prediction
- Molecule optimization with SMILES validation
- Fragment-based molecule generation via GenMol (SAFE format)
- QED/plogP scoring optimization

### Robotics (Isaac/GR00T)
- Robot navigation and path planning
- Action planning with step-by-step execution
- Vision-guided robot actions
- Physics simulation

### Vision (Cosmos R2)
- Image and video analysis
- Scene understanding and spatial reasoning
- Embodied reasoning for robotics applications
- Future state prediction

### Speech — Automatic Speech Recognition + Text-to-Speech *(New)*
- Speech-to-text (ASR) via NVIDIA Riva models
- Text-to-speech synthesis (TTS) via NVIDIA Riva models
- Neural audio playback rendered directly in the chat interface
- Smart Router auto-detects audio intent from natural language queries

### Image Generation *(New)*
- High-quality text-to-image generation via SDXL-Turbo on NVIDIA NIM
- Generated images displayed inline in the chat with "Advanced Visual Generation Engine" label
- Smart Router auto-detects image generation intent from natural language queries

### Embeddings (NeMo Retriever)
- 2048-dimensional multimodal text + image embeddings
- Cosine similarity search via `/v1/embeddings`

---

## Multi-Agent Crews

| Crew | Agents | Purpose |
|------|--------|---------|
| Research | Researcher, Analyst, Writer | General research with analysis |
| Drug Discovery | Chemist, Pharmacologist, Toxicologist | Drug candidate evaluation |
| Protein Analysis | Bioinformatician, Structural Biologist | Protein structure/function |
| Navigation | Planner, Mapper, Controller | Robot path planning |
| Manipulation | Grasp Planner, Motion Controller | Object manipulation |
| Swarm | Coordinator, Communicator | Multi-robot coordination |
| Neural Audio Synthesis *(New)* | Audio Engineer, Tone Analyst | Speech pacing, emotional tone analysis |
| Visual Art Generation *(New)* | Creative Director, Aesthetic Validator | Lighting, composition, aesthetic QA |

### Agent Builder — Live Execution *(New)*
The Visual Agent Builder at `/agent-builder` now directly executes pipelines via the agent engine (`/v1/agents/run`). Previously a visual-only tool, it now:
- Runs multimodal workflows with real model calls
- Auto-detects when a workflow requires Speech, Vision, or Image Gen domains based on the nodes being orchestrated
- Supports all 8 crew types including the new Audio and Visual Art crews
- Passes structured `crew_type` payloads recognized by the crew manager

---

## Fully Homomorphic Encryption (FHE)

Privacy-preserving computation using Microsoft SEAL (via TenSEAL) with real RLWE lattice-based cryptography. FHE is now a **primary platform feature** surfaced on the home page and accessible directly from the main navigation.

### Schemes
- **CKKS** — Approximate arithmetic on real/complex numbers for encrypted ML inference, secure embeddings, and private scoring
- **BFV** — Exact integer arithmetic for secure voting, private counting, and encrypted databases

### Security
- **128-bit post-quantum security** based on Ring Learning With Errors (RLWE), resistant to quantum attacks
- Server-side key management for demonstration; production deployments use client-held keys

### Services
| Service | Description |
|---------|-------------|
| Encrypted Drug Scoring | QED/plogP scoring on encrypted molecular vectors |
| Encrypted Similarity Search | Cosine similarity over encrypted embeddings |
| Secure Aggregation | Multi-party encrypted mean computation |
| Secure Voting | Private ballot tallying via BFV |
| Vector Arithmetic | Encrypted vector math with verification |

### Navigation Integration *(New)*
- "FHE & Zero Trust" promoted to primary feature on the home page
- Direct navigation links: Main Dashboard → Agent Builder → FHE Subsystem
- FHE dashboard includes breadcrumb navigation back to the main control plane
- Enterprise iconography (Shield, Lock, Brain) unified across all FHE UI surfaces

---

## Mobile App (Android)

A native Android client built with Kotlin and Jetpack Compose, featuring on-device ML inference for offline-capable AI operations.

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

### Security
- Biometric authentication
- EncryptedSharedPreferences for sensitive data
- Certificate pinning for API communication
- Network security config with domain restrictions

---

## Monetization

### Subscription Tiers

| Tier | Price | Queries/Month | Features |
|------|-------|---------------|----------|
| Community | Free | 1,000 | All 26 models, basic routing, all 6 domains |
| Production | $49/mo | 10,000 | Priority routing, all domain services, FHE access |
| Enterprise | $299/mo | Unlimited | Custom SLA, dedicated support, analytics, admin dashboard |

### How It Works
1. Users register via `/v1/auth/register` and generate API keys from the `/billing` dashboard
2. Each query is tracked against the key's monthly quota
3. Stripe handles subscription upgrades via checkout
4. Webhooks automatically update tier when subscriptions change
5. Tier limits are enforced before query execution
6. Webhook alerts fire at 900 MAU threshold

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
| GET | `/v1/capabilities` | System capabilities |
| POST | `/v1/simulate` | Simulate routing without execution |
| GET | `/v1/cache/stats` | NIM prompt cache statistics |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Create account |
| POST | `/v1/auth/login` | Login (returns JWT) |
| POST | `/v1/auth/refresh` | Refresh access token |
| GET | `/v1/auth/me` | Current user profile |
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
| POST | `/v1/vision/reason` | Vision reasoning |
| POST | `/v1/vision/analyze-image` | Image analysis |
| POST | `/v1/vision/embodied-reasoning` | Embodied reasoning |

### Speech *(New)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/audio/transcribe` | Speech-to-text (ASR) via Riva |
| POST | `/v1/audio/synthesize` | Text-to-speech (TTS) via Riva |

### Image Generation *(New)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/image/generate` | Text-to-image via SDXL-Turbo |

### Embeddings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/embeddings` | Multimodal text + image embeddings (2048-dim) |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/agents/run` | Run agent crew (all 8 crew types) |
| GET | `/v1/agents/types` | List crew types |

### FHE (Fully Homomorphic Encryption)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/fhe/status` | FHE subsystem status and capabilities |
| POST | `/v1/fhe/keygen` | Generate RLWE key pair (BFV or CKKS) |
| POST | `/v1/fhe/encrypt` | Encrypt vector into lattice ciphertext |
| POST | `/v1/fhe/compute` | Homomorphic operations on ciphertexts |
| POST | `/v1/fhe/decrypt` | Decrypt ciphertext (key holder only) |
| POST | `/v1/fhe/drug-scoring` | Encrypted drug QED/plogP scoring |
| POST | `/v1/fhe/similarity-search` | Encrypted embedding similarity search |
| POST | `/v1/fhe/secure-vote` | Private ballot tallying (BFV) |
| POST | `/v1/fhe/secure-aggregation` | Multi-party encrypted mean |
| POST | `/v1/fhe/vector-arithmetic` | Encrypted vector math with verification |
| GET | `/v1/fhe/demo` | Run all FHE demos with live results |

### Admin & Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/admin/analytics` | Platform-wide metrics (admin only) |
| GET | `/v1/admin/health` | System health status (admin only) |
| POST | `/v1/billing/api-keys` | Create API key |
| GET | `/v1/billing/api-keys` | List API keys |
| GET | `/v1/billing/usage/{id}` | Usage stats for key |
| GET | `/v1/billing/tiers` | Available tiers |
| POST | `/v1/billing/update-tier` | Update tier (admin) |
| GET | `/v1/billing/analytics` | Billing analytics data |

### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/plugins` | List plugins |
| GET | `/v1/plugins/{id}/capabilities` | Plugin capabilities |

---

## Project Structure

```
amaima/
├── backend/                              # FastAPI backend (Python 3.11)
│   ├── main.py                           # Application entry point
│   ├── amaima_config.yaml                # Configuration
│   ├── app/
│   │   ├── auth.py                       # JWT authentication system
│   │   ├── admin.py                      # Admin dashboard endpoints
│   │   ├── billing.py                    # Billing, usage tracking, analytics
│   │   ├── security.py                   # API key authentication
│   │   ├── core/
│   │   │   └── unified_smart_router.py   # Smart routing engine
│   │   ├── modules/
│   │   │   ├── nvidia_nim_client.py      # NVIDIA NIM API client + prompt cache
│   │   │   ├── execution_engine.py       # Model execution
│   │   │   ├── smart_router_engine.py    # Query routing + domain detection
│   │   │   └── plugin_manager.py         # Plugin system
│   │   ├── services/
│   │   │   ├── biology_service.py        # BioNeMo + GenMol drug discovery
│   │   │   ├── robotics_service.py       # Isaac/GR00T robotics
│   │   │   ├── vision_service.py         # Cosmos R2 vision
│   │   │   ├── audio_service.py          # Riva ASR + TTS *(New)*
│   │   │   └── image_gen_service.py      # SDXL-Turbo image generation *(New)*
│   │   ├── agents/
│   │   │   ├── crew_manager.py           # Multi-agent framework (8 crew types)
│   │   │   ├── biology_crew.py           # Biology agent crews
│   │   │   ├── robotics_crew.py          # Robotics agent crews
│   │   │   ├── audio_crew.py             # Neural Audio Synthesis crew *(New)*
│   │   │   └── visual_art_crew.py        # Visual Art Generation crew *(New)*
│   │   └── middleware/
│   │       └── rate_limiter.py           # MAU rate limiting middleware
│   └── tests/
│       └── integration/                  # End-to-end tests
│
├── frontend/                             # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx                      # Main dashboard (FHE promoted to primary) *(Updated)*
│   │   ├── login/                        # Auth pages
│   │   ├── admin/                        # Admin dashboard
│   │   ├── agent-builder/page.tsx        # React Flow builder (live execution) *(Updated)*
│   │   ├── fhe/page.tsx                  # FHE dashboard with breadcrumb nav *(Updated)*
│   │   ├── billing/page.tsx              # Billing + analytics dashboard
│   │   ├── conversations/page.tsx        # Conversation history
│   │   └── benchmarks/page.tsx           # Model benchmarking
│   └── next.config.js
│
├── mobile/                               # Android mobile client (Kotlin)
│   ├── app/
│   │   ├── build.gradle.kts
│   │   ├── proguard-rules.pro
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── res/
│   │       └── java/com/amaima/app/
│   │           ├── ml/
│   │           │   ├── OnDeviceMLManager.kt
│   │           │   ├── ModelRegistry.kt
│   │           │   ├── ModelStore.kt
│   │           │   ├── ModelDownloader.kt
│   │           │   ├── StreamingInference.kt
│   │           │   ├── EmbeddingEngine.kt
│   │           │   ├── AudioEngine.kt
│   │           │   ├── VisionEngine.kt
│   │           │   └── VectorStore.kt
│   │           ├── di/
│   │           ├── network/
│   │           ├── security/
│   │           └── data/
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   └── gradle/
│
├── tests/
│   ├── integration/
│   │   └── test_biology_e2e.py
│   └── ...
│
├── Dockerfile
├── start.sh
├── docker-compose.yml
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
- NVIDIA NIM API key
- Android Studio (for mobile development)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_NIM_API_KEY` | Yes | NVIDIA NIM API key for inference |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | Secret for JWT token signing |
| `AMAIMA_EXECUTION_MODE` | Yes | Set to `execution-enabled` for real AI responses |
| `BACKEND_URL` | No | Backend URL for frontend proxy (default: http://localhost:8000) |
| `API_SECRET_KEY` | Yes (production) | Protects API endpoints — change from default in production |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for billing |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |

### Start Backend
```bash
cd amaima/backend
pip install -r requirements.txt
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

### On Replit
Both services run automatically via configured workflows:
- **AMAIMA Backend** on port 8000
- **AMAIMA Frontend** on port 5000 (webview)

---

## Deployment

AMAIMA deploys as a single full-stack container (frontend + backend) to any platform that runs Docker.

### Quick Start (Docker Compose)
```bash
cp .env.example .env    # Fill in your API keys
docker compose up -d    # Starts app + PostgreSQL
```
App runs at `http://localhost:5000`

### Supported Platforms
Replit, Railway, Render, Fly.io, Docker/VPS, Google Cloud Run, AWS (App Runner/ECS/EC2), Azure Container Apps, DigitalOcean, and Heroku.

See the **[Full Deployment Guide](docs/fullstack-deployment-guide.md)** for step-by-step instructions for each platform, including PostgreSQL setup, environment variables, SSL, and production configuration.

---

## Implemented Features

All features below are fully built and operational:

- **26-Model Registry** — Full platform catalog: 20 cloud-available NVIDIA NIM models + 6 self-hosted catalog entries across 6 intelligence domains
- **6-Domain Smart Router** — Auto-detects Biology, Vision, Robotics, Speech, Image Generation, and Embeddings from natural language queries and routes accordingly *(Speech + Image Gen new)*
- **Audio Service** — Server-side ASR (speech-to-text) and TTS (text-to-speech) via NVIDIA Riva, with neural audio playback in the chat UI *(New)*
- **Image Generation Service** — Text-to-image via SDXL-Turbo on NVIDIA NIM, with inline image rendering in the chat UI *(New)*
- **Live Agent Builder** — React Flow drag-and-drop builder at `/agent-builder` now executes real multimodal pipelines via `/v1/agents/run`, with 8 crew types including Neural Audio Synthesis and Visual Art Generation *(Updated)*
- **FHE Primary Navigation** — "FHE & Zero Trust" promoted to primary home page feature; direct nav links connect Main Dashboard, Agent Builder, and FHE Subsystem; FHE page includes breadcrumb navigation *(Updated)*
- **Fully Homomorphic Encryption** — Privacy-preserving computation via Microsoft SEAL (TenSEAL): CKKS + BFV schemes, 128-bit post-quantum security, encrypted drug scoring, similarity search, secure voting, and aggregation
- **GenMol Molecule Generation** — Fragment-based molecule generation with SAFE format and QED/plogP optimization via `/v1/biology/generate-molecules`
- **Multimodal Embeddings** — 2048-dimensional text + image embeddings via NeMo Retriever at `/v1/embeddings`
- **SSE Streaming** — Real-time Server-Sent Events via `/v1/query/stream` with live token rendering
- **JWT Authentication** — Email/password auth with bcrypt, JWT access/refresh tokens, role-based access control, password recovery
- **Admin Dashboard** — Role-gated analytics with platform metrics, daily usage trends, model/endpoint breakdowns, and system health monitoring
- **NIM Prompt Caching** — In-memory LRU cache (500 entries, 10min TTL) with SHA-256 keys, reducing latency 20–30% on repeated queries
- **MAU Rate Limiting** — Per-API-key monthly active usage enforcement with 429 status and webhook alerts at 900 MAU threshold
- **Billing Analytics Dashboard** — Recharts-powered analytics with daily query volume, latency trends, model usage breakdown, and cache performance
- **Conversation History** — Persistent chat threads at `/conversations`
- **Model Benchmarking** — Automated benchmarking at `/benchmarks`
- **Custom Model Routing Rules** — Enterprise users can define custom routing preferences
- **Integration Tests** — 63 tests (55 unit + 8 integration) covering biology/drug discovery crews, NIM caching, agent types, and rate limiting
- **Multi-Platform Deployment** — Full-stack Docker container deployable to 10+ platforms
- **Android Mobile App** — Native Kotlin + Jetpack Compose client with dual-runtime on-device ML (ONNX + TFLite), featuring model hot-swapping, quantized inference (FP16/INT8/INT4), streaming token generation, text/image embeddings, Whisper speech-to-text, vision classification/OCR/detection, and local vector search with persistence

---

## Future Roadmap

### In Progress
- **FHE Latency Optimization** — CPU-first hardening: Clang++ + Intel HEXL recompile, SIMD batching, parameter tuning targeting <100ms per operation (down from 1.1s baseline)

### Medium Priority
- **File Upload Processing** — Direct image/document upload for vision and biology endpoints
- **Team Management** — Shared organization accounts with role-based access (admin, developer, viewer)
- **Usage Export** — CSV/JSON export of usage data for enterprise reporting

### Lower Priority
- **WebSocket Streaming** — Real-time bidirectional communication for interactive agent sessions
- **A/B Testing Framework** — Compare model responses side-by-side for quality evaluation
- **Plugin Marketplace** — Community-contributed plugins for additional domain services
- **Multi-Region Deployment** — Route to nearest NIM endpoint for lower latency
- **Fine-Tuning Pipeline** — Allow users to fine-tune models on their own data via NIM

---

## License

**AMAIMA License v2.0**

Three licensing options:
1. **Community License** — Free for non-commercial use, research, and individuals
2. **Production License** — Source-available for business use ($49/month)
3. **Enterprise License** — Full unrestricted commercial use ($299/month)

For licensing inquiries: licensing@amaima.live
For support: support@amaima.live

---

<div align="center">

**AMAIMA** — *The Multimodal AI Operating System*

Built with NVIDIA NIM · FastAPI · Next.js · Kotlin · Microsoft SEAL · Stripe

[amaima.live](https://amaima.live)

</div>
