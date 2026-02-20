# AMAIMA - Advanced Model-Aware AI Management Interface

An enterprise-grade AI orchestration platform for intelligent model routing, multi-agent collaboration, and specialized reasoning across multiple domains. Powered by NVIDIA NIM for optimized cloud-based inference.

## Key Features

### Smart Router Engine
Domain-aware query classification and model selection across 6 domains:
- **General** - Chat, code generation, analysis, and reasoning
- **Vision** - Scene understanding, image/video analysis (Cosmos R2)
- **Biology** - Drug discovery, protein analysis, molecule generation (BioNeMo, GenMol)
- **Robotics** - Action planning, navigation, manipulation (ROS2/Isaac)
- **Speech** - Automatic speech recognition and text-to-speech (Riva)
- **Embedding** - Multimodal text+image embeddings (NeMo Retriever)

Complexity scoring from TRIVIAL to EXPERT with automatic model selection and performance estimation.

### Model Registry (26 Models)
Full platform catalog across all domains:
- **20 cloud-available models** verified on NVIDIA NIM cloud API
- **6 self-hosted catalog entries** (AlphaFold2, VILA, Isaac Manipulator, Riva ASR/TTS, DiffDock)

### Multi-Agent Orchestration
- Crew Manager with lightweight AgentRole/Crew classes
- Specialized crews: Drug Discovery, Navigation, Research Pipeline
- LangChain Agent for stateful, graph-based workflow execution
- Visual Agent Builder UI with drag-and-drop React Flow interface

### SSE Streaming
Real-time Server-Sent Events streaming via `/v1/query/stream` with live token rendering and cursor animation in the frontend.

### User Authentication
- Email/password authentication with bcrypt hashing
- JWT access tokens (60min) and refresh tokens (30-day with revocation)
- Role-based access control (user/admin)
- Password recovery via token-based reset flow
- Default admin account: `admin@amaima.live`

### Admin Dashboard
Role-gated analytics with platform metrics, daily usage trends, model/endpoint breakdowns, system health monitoring, and KPI visualizations.

### Monetization System
Three-tier subscription model (Community, Production, Enterprise) with:
- Usage tracking and API key management
- Stripe integration for billing
- MAU rate limiting with webhook alerts
- Billing analytics dashboard

### GenMol Molecule Generation
NVIDIA GenMol integration for fragment-based molecule generation with SAFE format, QED/plogP scoring optimization via `/v1/biology/generate-molecules`.

### Multimodal Embeddings
NeMo Retriever Multimodal Embedding model for 2048-dimensional text+image embeddings via `/v1/embeddings`.

### NIM Prompt Caching
In-memory LRU cache (500 entries, 10min TTL) with SHA-256 key generation, reducing latency 20-30% on repeated queries.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **AI Engine**: NVIDIA NIM API
- **Database**: PostgreSQL
- **Auth**: JWT (HS256) with bcrypt
- **Payments**: Stripe

### Frontend
- **Framework**: Next.js 16 with React
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Agent Builder**: React Flow
- **Theme**: Dark mode

### Mobile (Android)
- **Language**: Kotlin + Jetpack Compose
- **ML Runtime**: ONNX Runtime (primary) + TensorFlow Lite (secondary)
- **Architecture**: Hilt DI, Room DB, Retrofit/OkHttp, Material 3
- **Min SDK**: 26 (Android 8.0)
- **Features**: Biometric auth, background sync, WebSocket streaming, offline support
- **On-Device ML**: Streaming inference, embedding engine, audio engine (Whisper-style), vision engine, vector store

## Project Structure

```
amaima/
├── backend/
│   ├── main.py                          # FastAPI application entry point
│   ├── app/
│   │   ├── auth.py                      # Authentication system
│   │   ├── admin.py                     # Admin dashboard endpoints
│   │   └── modules/
│   │       ├── nvidia_nim_client.py     # NVIDIA NIM API client + model registry
│   │       ├── smart_router_engine.py   # Domain detection + model routing
│   │       ├── crew_manager.py          # Multi-agent orchestration
│   │       └── plugin_manager.py        # Dynamic plugin system
│   └── tests/
│       └── integration/                 # End-to-end tests
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                     # Main dashboard
│   │   ├── login/                       # Auth pages
│   │   ├── admin/                       # Admin dashboard
│   │   ├── billing/                     # Billing & analytics
│   │   ├── agent-builder/               # Visual workflow builder
│   │   ├── conversations/               # Chat history
│   │   └── benchmarks/                  # Model benchmarking
│   └── next.config.js
├── mobile/                              # Android app (Kotlin)
│   └── app/src/main/java/com/amaima/app/
│       └── ml/                          # On-device ML engines
└── docs/                                # Documentation
```

## API Endpoints

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/query` | POST | Submit query with smart routing |
| `/v1/query/stream` | POST | SSE streaming query |
| `/v1/models` | GET | List all available models |
| `/v1/stats` | GET | Platform statistics |
| `/v1/cache/stats` | GET | Prompt cache metrics |

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/register` | POST | Create account |
| `/v1/auth/login` | POST | Login (returns JWT) |
| `/v1/auth/refresh` | POST | Refresh access token |
| `/v1/auth/me` | GET | Current user profile |
| `/v1/auth/api-keys` | GET/POST | Manage API keys |
| `/v1/auth/forgot-password` | POST | Request password reset |
| `/v1/auth/reset-password` | POST | Reset with token |

### Domain-Specific
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/biology/generate-molecules` | POST | GenMol molecule generation |
| `/v1/embeddings` | POST | Multimodal embeddings |
| `/v1/biology/*` | Various | Protein analysis, drug discovery |
| `/v1/robotics/*` | Various | Navigation, action planning |
| `/v1/vision/*` | Various | Scene analysis, image understanding |

### Admin & Billing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/admin/analytics` | GET | Platform-wide metrics |
| `/v1/admin/health` | GET | System health status |
| `/v1/billing/analytics` | GET | Usage analytics |

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL
- NVIDIA NIM API key

### Backend
```bash
cd amaima/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd amaima/frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API key for model inference |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret for JWT token signing |
| `STRIPE_SECRET_KEY` | Stripe API key for billing |

## License

Proprietary - All rights reserved.
