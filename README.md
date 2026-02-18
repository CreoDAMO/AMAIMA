# AMAIMA

**Advanced Model-Aware AI Management Interface**

<div align="center">

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-109989?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![Stripe](https://img.shields.io/badge/Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: AMAIMA v1.0](https://img.shields.io/badge/License-AMAIMA%20v1.0-blueviolet?style=for-the-badge)](LICENSE)
[![Backend CI/CD](https://github.com/CreoDAMO/AMAIMA/actions/workflows/backend.yml/badge.svg)](https://github.com/CreoDAMO/AMAIMA/actions/workflows/backend.yml)

</div>

---

## Overview

AMAIMA is an enterprise-grade AI orchestration platform that intelligently routes queries across 14 NVIDIA NIM models for optimal cost, speed, and quality. It combines a smart routing engine with specialized domain services for biology/drug discovery, robotics, and vision/multimodal reasoning.

### What It Does

- **Smart Query Routing** - Analyzes query complexity (TRIVIAL to EXPERT) and automatically selects the best model
- **Domain-Specific AI** - Dedicated services for biology (BioNeMo), robotics (Isaac/GR00T), and vision (Cosmos R2)
- **Multi-Agent Crews** - Orchestrated agent teams for research, drug discovery, protein analysis, navigation, and manipulation
- **Monetization Built-In** - Three-tier subscription system with Stripe billing, API key management, and usage tracking
- **Cloud-First** - No GPU required; all inference runs through NVIDIA NIM cloud APIs

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
              +--------------+--------------+
              |              |              |
     +--------+--+  +--------+--+  +--------+--+
     | Smart     |  | Domain    |  | Billing   |
     | Router    |  | Services  |  | Service   |
     | Engine    |  |           |  |           |
     +-----------+  +-----------+  +-----------+
                         |
         +---------------+---------------+
         |               |               |
    +----+----+    +-----+-----+   +-----+-----+
    | Biology |    | Robotics  |   | Vision    |
    | BioNeMo |    | Isaac/    |   | Cosmos R2 |
    |         |    | GR00T     |   |           |
    +---------+    +-----------+   +-----------+
                         |
                 +-------+-------+
                 | NVIDIA NIM    |
                 | Cloud APIs    |
                 +---------------+
```

---

## Model Registry (14 Models)

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

### Robotics Models
| Model | Best For |
|-------|----------|
| nvidia/isaac-gr00t-n1.6 | Humanoid robot control (VLA) |
| nvidia/alpamayo-1 | Autonomous vehicle reasoning (VLA) |

---

## Smart Router

The routing engine classifies queries across five complexity levels and routes to the optimal model:

| Level | Description | Routed To |
|-------|-------------|-----------|
| TRIVIAL | Simple factual queries | Llama 8B / Gemma 9B |
| SIMPLE | Basic explanations | Llama 8B |
| MODERATE | Multi-step reasoning | Llama 70B |
| COMPLEX | Domain expertise needed | Mixtral 8x7B / 70B |
| EXPERT | Specialized analysis | Llama 405B |

### Domain-Aware Routing
- **Biology** keywords (drug, protein, molecule) -> BioNeMo MegaMolBART
- **Vision** keywords (image, video, scene) -> Cosmos Reason2 7B
- **Robotics** keywords (robot, navigate, grasp) -> Isaac GR00T N1.6
- **General** queries -> Complexity-based model selection

---

## Domain Services

### Biology (BioNeMo)
- Drug discovery pipeline with molecule generation
- Protein sequence analysis and structure prediction
- Molecule optimization with SMILES validation
- General biology/chemistry queries

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

---

## Monetization

### Subscription Tiers

| Tier | Price | Queries/Month | Features |
|------|-------|---------------|----------|
| Community | Free | 1,000 | All 14 models, basic routing |
| Production | $49/mo | 10,000 | Priority routing, all domain services |
| Enterprise | $299/mo | Unlimited | Custom SLA, dedicated support, analytics |

### How It Works
1. Users generate API keys from the `/billing` dashboard
2. Each query is tracked against the key's monthly quota
3. Stripe handles subscription upgrades via checkout
4. Webhooks automatically update tier when subscriptions change
5. Tier limits are enforced before query execution

---

## API Reference

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with component status |
| GET | `/v1/stats` | System statistics |
| POST | `/v1/query` | Submit query for intelligent routing |
| GET | `/v1/models` | List available models |
| GET | `/v1/capabilities` | System capabilities |
| POST | `/v1/simulate` | Simulate routing without execution |

### Biology
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/biology/discover` | Drug discovery pipeline |
| POST | `/v1/biology/protein` | Protein analysis |
| POST | `/v1/biology/optimize` | Molecule optimization |
| POST | `/v1/biology/query` | General biology query |

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

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/agents/run` | Run agent crew |
| GET | `/v1/agents/types` | List crew types |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/billing/api-keys` | Create API key |
| GET | `/v1/billing/api-keys` | List API keys |
| GET | `/v1/billing/usage/{id}` | Usage stats for key |
| GET | `/v1/billing/tiers` | Available tiers |
| POST | `/v1/billing/update-tier` | Update tier (admin) |

### Plugins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/plugins` | List plugins |
| GET | `/v1/plugins/{id}/capabilities` | Plugin capabilities |

---

## Project Structure

```
amaima/
├── backend/                         # FastAPI backend (Python 3.11)
│   ├── main.py                      # Application entry point
│   ├── amaima_config.yaml           # Configuration
│   ├── app/
│   │   ├── core/
│   │   │   └── unified_smart_router.py  # Smart routing engine
│   │   ├── modules/
│   │   │   ├── nvidia_nim_client.py     # NVIDIA NIM API client
│   │   │   ├── execution_engine.py      # Model execution
│   │   │   ├── smart_router_engine.py   # Query routing + domain detection
│   │   │   └── plugin_manager.py        # Plugin system
│   │   ├── services/
│   │   │   ├── vision_service.py        # Cosmos R2 vision
│   │   │   ├── biology_service.py       # BioNeMo drug discovery
│   │   │   └── robotics_service.py      # Isaac/GR00T robotics
│   │   ├── agents/
│   │   │   ├── crew_manager.py          # Multi-agent framework
│   │   │   ├── biology_crew.py          # Biology agent crews
│   │   │   └── robotics_crew.py         # Robotics agent crews
│   │   ├── billing.py                   # Billing & usage tracking
│   │   └── security.py                 # API key authentication
│   └── app/routers/                     # FastAPI routers
│
├── frontend/                        # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx                     # Main dashboard
│   │   ├── agent-builder/page.tsx       # React Flow agent builder
│   │   ├── billing/page.tsx             # Billing, analytics dashboard
│   │   ├── conversations/page.tsx       # Conversation history
│   │   ├── benchmarks/page.tsx          # Model benchmarking
│   │   └── api/                         # API route proxies
│   │       ├── v1/                      # Backend proxy routes
│   │       └── stripe/                  # Stripe checkout/webhook
│   ├── src/lib/
│   │   ├── stripeClient.ts              # Stripe client
│   │   └── stripeInit.ts                # Stripe initialization
│   ├── scripts/seed-products.ts         # Stripe product seeding
│   └── vercel.json                      # Vercel deployment config
│
├── Dockerfile                       # Full-stack container
├── start.sh                         # Full-stack startup script
├── docker-compose.yml               # Docker Compose with PostgreSQL
├── .env.example                     # Environment variable template
├── docs/                            # Documentation
│   └── fullstack-deployment-guide.md    # 10-platform deployment guide
├── mobile/                          # Android client (spec only)
└── monitoring/                      # Grafana dashboards
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL database
- NVIDIA NIM API key

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_API_KEY` | Yes | NVIDIA NIM API key for inference |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `AMAIMA_EXECUTION_MODE` | Yes | Set to `execution-enabled` for real AI responses |
| `BACKEND_URL` | No | Backend URL for frontend proxy (default: http://localhost:8000) |
| `API_SECRET_KEY` | Yes (production) | Protects API endpoints. Must be changed from default in production |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for billing |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |

### Start Backend
```bash
cd amaima/backend
pip install -r requirements.txt  # or use pip install
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend
```bash
cd amaima/frontend
npm install
npm run dev
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

## License

**AMAIMA License v1.0**

Three licensing options:
1. **Community License** - Free for non-commercial use, research, and individuals
2. **Production License** - Source-available for business use ($49/month)
3. **Enterprise License** - Full unrestricted commercial use ($299/month)

For licensing inquiries: licensing@amaima.ai

---

## Implemented Features

These features are fully built and operational:

- **NIM Prompt Caching** - In-memory LRU cache (500 entries, 10min TTL) with SHA-256 keys, reducing latency 20-30% on repeated queries. Stats at `/v1/cache/stats`
- **MAU Rate Limiting** - Per-API-key monthly active usage enforcement with 429 status when exceeded, plus webhook alerts at 900 MAU threshold
- **Billing Analytics Dashboard** - Recharts-powered analytics tab with daily query volume, latency trends, model usage breakdown, endpoint stats, tier distribution, and cache performance
- **Agent Builder UI** - React Flow drag-and-drop visual workflow builder at `/agent-builder` with pre-built templates (Research Pipeline, Drug Discovery, Navigation Crew)
- **Conversation History** - Persistent chat threads at `/conversations`
- **Model Benchmarking** - Automated benchmarking at `/benchmarks`
- **Webhook Notifications** - Alerts when users approach usage limits (900 MAU threshold) or when Stripe subscription events occur
- **Custom Model Routing Rules** - Enterprise users can define custom routing preferences
- **Integration Tests** - 63 tests (55 unit + 8 integration) covering biology/drug discovery crews, NIM caching, agent types, and rate limiting
- **Multi-Platform Deployment** - Full-stack Docker container deployable to 10+ platforms (see [Deployment Guide](docs/fullstack-deployment-guide.md))

---

## Future Roadmap

### High Priority
- **Streaming Responses** - Server-Sent Events (SSE) for real-time token streaming on long queries
- **User Authentication** - Full user accounts with email/password or OAuth login tied to API keys
- **Admin Dashboard** - Analytics panel showing usage across all users, revenue metrics, and system health

### Medium Priority
- **File Upload Processing** - Direct image/document upload for vision and biology endpoints
- **Team Management** - Shared organization accounts with role-based access (admin, developer, viewer)
- **Usage Export** - CSV/JSON export of usage data for enterprise reporting

### Lower Priority
- **Android Mobile Client** - Native app implementation from existing spec
- **WebSocket Streaming** - Real-time bidirectional communication for interactive agent sessions
- **A/B Testing Framework** - Compare model responses side-by-side for quality evaluation
- **Plugin Marketplace** - Community-contributed plugins for additional domain services
- **Multi-Region Deployment** - Route to nearest NIM endpoint for lower latency
- **Fine-Tuning Pipeline** - Allow users to fine-tune models on their own data via NIM

---

<div align="center">

**AMAIMA** - *Intelligent AI Orchestration at Scale*

Built with NVIDIA NIM, FastAPI, Next.js, and Stripe

</div>
