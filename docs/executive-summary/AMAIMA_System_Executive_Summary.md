# AMAIMA System Executive Summary
**Advanced Model-Aware AI Management Interface - Complete Platform Overview**

---

## Platform Vision

AMAIMA is an enterprise-grade AI orchestration platform that intelligently routes queries across 14 NVIDIA NIM models, providing optimal resource utilization, cost efficiency, and response quality. The platform features domain-specialized services for vision, biology, and robotics with a three-tier monetization system.

**Platform Components:**
1. **Python Backend** - FastAPI-based AI orchestration with NVIDIA NIM inference
2. **Web Frontend** - Next.js 16 + React interface with billing, benchmarks, and admin tools
3. **Android Mobile Client** - Native Kotlin app (planned for Phase 2)

---

## Backend Infrastructure (Python / FastAPI)

### Architecture

The backend implements a **cloud-first modular architecture** organized across 6 functional layers with 16 database tables:

**Core Layer**
- **Smart Router Engine** (`smart_router_engine.py`): Analyzes query complexity (TRIVIAL → EXPERT) using keyword detection and domain classification, routing to the optimal model from a registry of 14 NVIDIA NIM models
- **NVIDIA NIM Client** (`nvidia_nim_client.py`): Cloud-based inference via NVIDIA's hosted API endpoints — no local GPU required
- **Execution Engine** (`execution_engine.py`): Manages model execution with automatic benchmark recording (latency, tokens, cost)

**Domain Services Layer**
- **Vision Service** (`vision_service.py`): Cosmos R2 for embodied reasoning, image/video analysis, scene understanding
- **Biology Service** (`biology_service.py`): BioNeMo for drug discovery, protein analysis, molecule optimization, SMILES validation
- **Robotics Service** (`robotics_service.py`): Robot action planning, navigation, vision-guided actions, simulation

**Multi-Agent Layer**
- **Crew Manager** (`crew_manager.py`): Base AgentRole and Crew classes with sequential, parallel, and hierarchical orchestration
- **Biology Crews** (`biology_crew.py`): Drug Discovery and Protein Analysis crews
- **Robotics Crews** (`robotics_crew.py`): Navigation, Manipulation, and Swarm Coordination crews

**Business Layer**
- **Billing Service** (`billing.py`): Three-tier subscription system (Community/Production/Enterprise) with usage tracking and tier enforcement
- **Organizations** (`organizations.py`): Team accounts with owner/admin/member roles and shared billing
- **Webhooks** (`webhooks.py`): HMAC-SHA512 signed usage alert notifications with auto-disable after failures

**Intelligence Layer**
- **Response Caching** (`benchmarks.py`): MD5-keyed cache with 24-hour TTL to reduce NIM API costs
- **Model Benchmarking** (`benchmarks.py`): Automatic latency/token/cost recording, leaderboard, timeseries data
- **A/B Testing** (`experiments.py`): Side-by-side model comparison experiments with voting and statistics
- **Conversations** (`conversations.py`): Persistent chat threads with message history and model tracking

**Infrastructure Layer**
- **Plugin Manager** (`plugin_manager.py`): Dynamic plugin registration for domain services
- **Observability** (`observability_framework.py`): Structured logging and metrics
- **Security** (`security.py`): API key authentication and tier enforcement middleware

### Model Registry (14 NVIDIA NIM Models)

| Category | Model | Use Case |
|----------|-------|----------|
| **General** | meta/llama-3.1-8b-instruct | Simple queries |
| **General** | meta/llama-3.1-70b-instruct | Moderate/advanced queries |
| **General** | meta/llama-3.1-405b-instruct | Expert-level queries |
| **General** | mistralai/mixtral-8x7b-instruct-v0.1 | Cost-efficient MoE |
| **General** | google/gemma-2-9b-it | Lightweight/edge |
| **General** | nvidia/nemotron-nano-9b-v2 | Edge deployment, agentic AI |
| **Vision** | nvidia/cosmos-reason2-7b | Vision-language reasoning, embodied AI |
| **Vision** | nvidia/cosmos-predict2-14b | Video generation, future state prediction |
| **Vision** | nvidia/llama-3.1-nemotron-nano-vl-8b | Multimodal understanding |
| **Biology** | nvidia/bionemo-megamolbart | Molecular generation, drug discovery |
| **Biology** | nvidia/bionemo-esm2 | Protein structure prediction |
| **Robotics** | nvidia/isaac-gr00t-n1.6 | Humanoid robot control (VLA) |
| **Robotics** | nvidia/alpamayo-1 | Autonomous vehicle reasoning (VLA) |
| **Routing** | nvidia/nemotron-nano-9b-v2 | Default edge/agentic model |

### Domain-Aware Routing

The Smart Router automatically classifies queries by domain:
- **Biology** (drug/protein/molecule keywords) → `nvidia/bionemo-megamolbart`
- **Vision** (image/video/scene keywords) → `nvidia/cosmos-reason2-7b`
- **Robotics** (robot/navigate/grasp keywords) → `nvidia/isaac-gr00t-n1.6`
- **General** → complexity-based selection across Llama/Mixtral/Gemma models

### API Endpoints (40+)

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Core | `/health`, `/v1/stats`, `/v1/query`, `/v1/models`, `/v1/capabilities`, `/v1/simulate` | Health, stats, query routing, model listing |
| Biology | `/v1/biology/discover`, `/protein`, `/optimize`, `/query`, `/capabilities` | Drug discovery, protein analysis |
| Robotics | `/v1/robotics/navigate`, `/plan`, `/simulate`, `/vision-action`, `/capabilities` | Robot control and planning |
| Vision | `/v1/vision/reason`, `/analyze-image`, `/embodied-reasoning`, `/capabilities` | Image/video understanding |
| Agents | `/v1/agents/run`, `/types` | Multi-agent crew execution |
| Billing | `/v1/billing/usage`, `/tiers`, `/api-keys`, `/update-tier` | Subscription management |
| Conversations | `/v1/conversations` (CRUD), `/messages` | Chat thread management |
| Benchmarks | `/v1/benchmarks`, `/leaderboard`, `/timeseries` | Performance tracking |
| Cache | `/v1/cache/stats`, `/clear` | Response cache management |
| Webhooks | `/v1/webhooks` (CRUD), `/events` | Usage alert webhooks |
| Organizations | `/v1/organizations` (CRUD), `/members` | Team account management |
| Experiments | `/v1/experiments` (CRUD), `/run`, `/vote` | A/B testing |
| Routing Rules | `/v1/routing-rules` (CRUD) | Custom model routing (Enterprise) |
| Export | `/v1/export/usage`, `/benchmarks` | CSV/JSON data export |
| Plugins | `/v1/plugins`, `/marketplace` | Plugin management |
| File Upload | `/v1/upload` | 10MB multipart file upload |
| Stripe (frontend) | `/api/stripe/checkout`, `/portal`, `/webhook`, `/products`, `/publishable-key` | Payment processing (frontend routes, not backend) |

### Database Schema (16 Tables)

| Table | Purpose |
|-------|---------|
| `api_keys` | API key management with tier, Stripe customer/subscription IDs |
| `usage_events` | Per-query usage tracking |
| `monthly_usage` | Aggregated monthly usage per API key |
| `conversations` | Chat thread metadata |
| `messages` | Individual chat messages with model/latency tracking |
| `uploads` | File upload metadata with MD5 checksums |
| `model_benchmarks` | Per-query performance data (latency, tokens, cost) |
| `response_cache` | Cached query responses with TTL |
| `webhook_endpoints` | Registered webhook URLs with signing keys |
| `webhook_events` | Webhook delivery log |
| `organizations` | Team/org accounts |
| `org_members` | Organization membership with roles |
| `routing_rules` | Custom model routing preferences (Enterprise) |
| `experiments` | A/B testing experiment definitions |
| `experiment_trials` | Individual A/B test trial results |
| `decision_telemetry` | Routing decision audit log |

---

## Monetization System

### Three-Tier Subscription Model

| Tier | Price | Queries/Month | Features |
|------|-------|---------------|----------|
| **Community** | Free | 1,000 | All 14 models, basic routing, API access |
| **Production** | $49/mo | 10,000 | Priority routing, all domain services, webhook alerts |
| **Enterprise** | $299/mo | Unlimited | Custom routing rules, team accounts, dedicated support, A/B testing |

### Payment Infrastructure
- **Stripe Integration**: Managed via Replit's `stripe-replit-sync` for automatic schema management, webhook handling, and sandbox→production migration
- **Billing Dashboard**: Plan cards, API key management, usage meter with real-time tracking
- **Automatic Tier Enforcement**: Middleware checks usage against limits, webhooks notify at 80%/100% thresholds
- **Production Ready**: Environment-aware credentials (sandbox in dev, live keys on publish)

---

## Web Frontend (Next.js 16 + React 18)

### Technology Stack
- **Framework**: Next.js 16 with App Router
- **UI**: Tailwind CSS with custom dark theme (glassmorphism design)
- **Icons**: Lucide React
- **Language**: TypeScript
- **Port**: 5000 (Replit webview compatible)
- **Deployment**: Vercel-ready with `vercel.json` config

### Pages & Features

1. **Query Interface** (`/`)
   - 7 operation types: General, Code, Analysis, Biology, Robotics, Vision, Agents
   - Domain-specific sample queries for quick testing
   - Real-time API status and system metrics
   - Routing decision visualization with model selection details
   - Query history with localStorage persistence

2. **Billing Dashboard** (`/billing`)
   - Subscription plan cards with Stripe checkout
   - API key creation and management (copy, revoke)
   - Real-time usage meter showing queries used vs. limit
   - Stripe Customer Portal access for subscription management

3. **Benchmarks** (`/benchmarks`)
   - Model performance leaderboard (avg latency, tokens, cost per model)
   - Response cache statistics (entries, hit rate, size)
   - Performance timeseries data

4. **Conversations** (`/conversations`)
   - Thread sidebar with conversation list
   - Message history with AI response metadata
   - Create/delete conversation threads

5. **Settings** (`/settings`) - 4 tabs:
   - **Organizations**: Create teams, manage members with roles
   - **Webhooks**: Register alert endpoints, view delivery history
   - **Experiments**: Create and run A/B model comparison tests
   - **Routing Rules**: Custom model preferences (Enterprise tier)

### Frontend API Architecture
- **23 API proxy routes** in `src/app/api/` forward requests to the Python backend (17 v1 groups + 5 Stripe + 1 health)
- SSRF protection via allowlist-based URL mapping (no user input in outgoing URLs)
- Stripe routes handle checkout, portal, webhook, products, and publishable key
- All proxy routes forward HTTP status codes from backend

### Security
- **SSRF Prevention**: All proxy routes use pre-defined URL maps instead of user-supplied paths
- **API Key Authentication**: Protected endpoints require `X-API-Key` header
- **HMAC-SHA512**: Webhook payloads signed for verification
- **Cache Control**: `no-cache` headers to prevent stale content in iframe proxies

---

## Android Client (Scaffolded - Phase 2 Completion)

### Architecture (Design Spec + App Scaffold in `amaima/mobile/`)
- **Clean Architecture**: Jetpack Compose UI + Room database + Retrofit
- **On-Device ML**: TensorFlow Lite for complexity estimation
- **Offline-First**: Background sync via WorkManager
- **Security**: Biometric auth, EncryptedSharedPreferences, certificate pinning
- **Target SDK**: 34 (Android 14), Min SDK: 26 (Android 8.0)

---

## System Integration

### Data Flow: Query Submission
1. User selects operation type and enters query in web interface
2. Frontend sends POST to `/api/v1/query` proxy route
3. Backend Smart Router classifies domain (biology/vision/robotics/general)
4. Router determines complexity level (TRIVIAL → EXPERT)
5. Response cache checked — if hit, return cached response immediately
6. If cache miss, NVIDIA NIM Client sends inference request to selected model
7. Response cached with 24-hour TTL for future identical queries
8. Benchmark data recorded (latency, tokens, cost, model used)
9. Usage event logged against API key for billing enforcement
10. If usage crosses 80% or 100% of tier limit, webhook alerts fire

### Deployment Configuration

**Current (Replit)**
```yaml
Backend:
  - Framework: FastAPI + Uvicorn
  - Port: 8000 (internal)
  - AI Inference: NVIDIA NIM cloud API (no GPU required)

Frontend:
  - Framework: Next.js 16
  - Port: 5000 (Replit webview)
  - Proxy: API routes forward to backend on port 8000

Database:
  - PostgreSQL (Neon-backed via Replit)
  - 16 tables across public schema
  - Stripe schema managed by stripe-replit-sync

Payments:
  - Stripe (sandbox in dev, live keys on publish)
  - Managed webhooks via stripe-replit-sync
```

**Production (Vercel + External Backend)**
```yaml
Frontend:
  - Vercel deployment with vercel.json config
  - Environment: BACKEND_URL pointing to hosted backend

Backend:
  - Any cloud provider (AWS, GCP, Azure, Railway, etc.)
  - Requires: Python 3.11+, PostgreSQL, NVIDIA_API_KEY

Database:
  - Any PostgreSQL provider (Neon, Supabase, RDS, etc.)
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `NVIDIA_API_KEY` | Yes | NVIDIA NIM API key for AI inference |
| `BACKEND_URL` | Yes | Backend URL for frontend proxy (default: `http://localhost:8000`) |
| `AMAIMA_EXECUTION_MODE` | No | Set to `execution-enabled` for real inference |
| `API_SECRET_KEY` | No | Backend API authentication key |
| `SESSION_SECRET` | No | Session encryption key |
| `COSMOS_NIM_URL` | No | Cosmos R2 endpoint (default: `https://integrate.api.nvidia.com/v1`) |
| `BIONEMO_NIM_URL` | No | BioNeMo endpoint (default: `https://integrate.api.nvidia.com/v1`) |
| `NEXT_PUBLIC_API_URL` | No | Public API URL for frontend (default: `http://localhost:8000`) |

---

## Security & Compliance

### Authentication & Authorization
- **API Key System**: Per-user keys with tier-based access control
- **Tier Enforcement**: Middleware validates usage limits before processing queries
- **Stripe Integration**: Subscription changes automatically update API key tiers via webhooks

### Data Protection
- **In Transit**: HTTPS/TLS for all external communication
- **Webhook Signing**: HMAC-SHA512 signatures on all webhook payloads
- **SSRF Prevention**: Allowlist-based URL mapping on all API proxy routes
- **Input Validation**: File uploads limited to 10MB with MD5 checksum verification
- **Auto-Disable**: Webhooks disabled after 5 consecutive delivery failures

### Code Quality
- **CodeQL Scanning**: Automated security analysis on all commits
- **No Hardcoded Secrets**: All credentials via environment variables or Replit integrations

---

## File Structure

```
amaima/
├── frontend/                       # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx                # Main query interface
│   │   ├── layout.tsx              # Root layout with navigation
│   │   ├── billing/page.tsx        # Subscription & API key management
│   │   ├── benchmarks/page.tsx     # Performance dashboard
│   │   ├── conversations/page.tsx  # Chat thread interface
│   │   ├── settings/page.tsx       # Orgs/Webhooks/Experiments/Rules
│   │   ├── components/
│   │   │   └── Navigation.tsx      # Global nav bar
│   │   ├── api/v1/                 # 13 API proxy route groups
│   │   └── api/stripe/             # 5 Stripe API routes
│   ├── src/lib/
│   │   ├── stripeClient.ts         # Stripe credential management
│   │   └── stripeInit.ts           # Stripe schema initialization
│   ├── scripts/
│   │   └── seed-products.ts        # Stripe product creation script
│   ├── vercel.json                 # Vercel deployment config
│   ├── next.config.js
│   └── package.json
├── backend/                        # FastAPI backend
│   ├── main.py                     # Entry point (40+ endpoints)
│   ├── amaima_config.yaml          # Configuration
│   ├── app/
│   │   ├── core/
│   │   │   └── unified_smart_router.py
│   │   ├── modules/
│   │   │   ├── nvidia_nim_client.py        # NVIDIA NIM API client
│   │   │   ├── execution_engine.py         # Model execution
│   │   │   ├── smart_router_engine.py      # Query routing + domain detection
│   │   │   ├── plugin_manager.py           # Plugin system
│   │   │   └── observability_framework.py  # Logging/metrics
│   │   ├── services/
│   │   │   ├── vision_service.py           # Cosmos R2 vision
│   │   │   ├── biology_service.py          # BioNeMo biology
│   │   │   └── robotics_service.py         # Isaac robotics
│   │   ├── agents/
│   │   │   ├── crew_manager.py             # Multi-agent framework
│   │   │   ├── biology_crew.py             # Drug/protein crews
│   │   │   └── robotics_crew.py            # Navigation/manipulation crews
│   │   ├── routers/
│   │   │   ├── biology.py
│   │   │   ├── robotics.py
│   │   │   └── vision.py
│   │   ├── billing.py                      # Subscription billing
│   │   ├── conversations.py                # Chat threads
│   │   ├── benchmarks.py                   # Performance + caching + export
│   │   ├── organizations.py                # Team accounts
│   │   ├── webhooks.py                     # Usage alerts + routing rules
│   │   ├── experiments.py                  # A/B testing
│   │   ├── database.py                     # Connection pool management
│   │   └── security.py                     # API key auth
│   └── uploads/                            # File upload storage
├── docs/
│   ├── executive-summary/
│   │   └── AMAIMA_System_Executive_Summary.md
│   └── integration-strategy_guide.md
└── .env.example                            # Environment variable reference
```

---

## Design Decisions

1. **Cloud-First**: All AI inference via NVIDIA NIM cloud APIs — no local GPU, torch, or vLLM required
2. **Graceful Fallbacks**: Domain services use try/except for optional imports, defaulting to cloud endpoints
3. **Lightweight Agents**: Custom AgentRole/Crew classes instead of heavy CrewAI dependency
4. **Single Database**: PostgreSQL handles everything — billing, conversations, benchmarks, cache, orgs
5. **Stripe via Replit**: `stripe-replit-sync` manages schema, webhooks, and sandbox→production migration automatically
6. **SSRF-Safe Proxies**: Frontend API routes use pre-built URL maps, never interpolating user input into URLs

---

## Roadmap

### Phase 1 (Completed - Q1 2026)
- ✅ Smart Router with 5-level complexity analysis
- ✅ 14 NVIDIA NIM model integrations
- ✅ Domain services: Vision (Cosmos R2), Biology (BioNeMo), Robotics (Isaac)
- ✅ Multi-agent crews: Research, Drug Discovery, Protein, Navigation, Manipulation, Swarm
- ✅ Three-tier monetization with Stripe billing
- ✅ Conversation history with persistent threads
- ✅ Model benchmarking and performance leaderboard
- ✅ Response caching (24hr TTL)
- ✅ Webhook notifications for usage alerts
- ✅ Team/organization accounts
- ✅ Custom routing rules (Enterprise tier)
- ✅ A/B testing for model comparison
- ✅ Usage data export (CSV/JSON)
- ✅ Plugin marketplace
- ✅ File upload support (10MB)
- ✅ Full frontend with billing, benchmarks, conversations, settings

### Phase 2 (Completed - Q2 2026)
- ✅ Android mobile client (Kotlin + Jetpack Compose)
- ✅ WebSocket streaming responses
- ✅ Advanced workflow builder with visual programming
- ✅ Multi-modal input (voice, images, video in query interface)
- ✅ Domain-specialized routing (Biology, Robotics, Vision)

### Phase 3 (Q3 2026)
- [ ] Collaborative workspaces (shared conversations, team analytics)
- [ ] Enhanced analytics dashboard with usage forecasting
- [ ] Enterprise SSO integration (SAML/OIDC)
- [ ] Custom model fine-tuning via NeMo

### Phase 4 (Q4 2026)
- [ ] Edge computing support
- [ ] Full MCP ecosystem integration
- [ ] Global CDN for model distribution
- [ ] Advanced personalization (per-user model tuning)

---

## Cost Model

### Per-Query Costs (NVIDIA NIM)
| Model Size | Cost per 1K Tokens | Typical Use |
|-----------|-------------------|-------------|
| 8B-9B (Llama/Gemma/Nemotron) | ~$0.0003 | Simple queries |
| 70B (Llama) | ~$0.0008 | Moderate queries |
| 405B (Llama) | ~$0.0015 | Expert queries |
| Domain models (BioNeMo/Cosmos/Isaac) | ~$0.0005-0.001 | Specialized queries |

### Subscription Revenue
| Tier | Price | Gross Margin (est.) |
|------|-------|-------------------|
| Community | Free | N/A (acquisition) |
| Production | $49/mo | ~80% at avg usage |
| Enterprise | $299/mo | ~85% with volume |

---

## Success Metrics

### Performance KPIs
- **Uptime**: 99.9% target
- **Query Routing**: <50ms p95 latency
- **API Response**: <200ms p95 (cached), <2s p95 (NIM inference)
- **Cache Hit Rate**: >30% target (reduces NIM API costs)

### Business KPIs
- **MRR Growth**: Track Production + Enterprise subscriptions
- **API Key Activations**: New developer signups
- **Query Volume**: Total queries processed per month
- **Cache Savings**: Estimated NIM API cost avoided via response caching

---

**Document Version**: 6.0.0
**Last Updated**: February 17, 2026
**Status**: Production Ready
