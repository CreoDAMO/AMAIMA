# AMAIMA - Advanced Model-Aware AI Management Interface

## Overview
AMAIMA is an enterprise-grade AI orchestration platform with intelligent model routing, multi-agent collaboration, and specialized capabilities for vision/multimodal reasoning (Cosmos R2), biology/drug discovery (BioNeMo), and robotics (ROS2/Isaac). The system uses NVIDIA NIM for optimized cloud-based inference with a FastAPI backend, Next.js frontend, and Android mobile app.

## Project Architecture

### Frontend
- **Framework**: Next.js 16 with React
- **Styling**: Tailwind CSS with custom dark theme
- **Location**: `amaima/frontend/`
- **Port**: 5000 (for Replit webview)
- **Deployment**: Vercel-ready with `vercel.json` config
- **Key Features**:
  - Query input interface with 7 operation types (General, Code, Analysis, Biology, Robotics, Vision, Agents)
  - Real-time API status and system metrics
  - Routing decision visualization
  - Performance metrics display
  - API routes proxy to backend via `BACKEND_URL` env var
  - Domain-specific sample queries for each operation type

### Backend
- **Framework**: FastAPI with Python 3.11
- **Location**: `amaima/backend/`
- **Port**: 8000 (internal)
- **AI Inference**: NVIDIA NIM API (cloud-based, no GPU required)
- **Key Features**:
  - Smart Router engine with domain-aware query classification
  - NVIDIA NIM integration for real AI model inference
  - Domain-specific services: Vision (Cosmos R2), Biology (BioNeMo), Robotics (ROS2/Isaac)
  - Multi-agent crews: Research, Drug Discovery, Protein Analysis, Navigation, Manipulation, Swarm
  - Plugin manager for extensibility
  - Health monitoring and statistics endpoints
  - CORS-enabled API

### Domain Services
- **Vision Service** (`app/services/vision_service.py`): Cosmos R2 for embodied reasoning, image/video analysis, scene understanding
- **Biology Service** (`app/services/biology_service.py`): BioNeMo for drug discovery, protein analysis, molecule optimization, SMILES validation
- **Robotics Service** (`app/services/robotics_service.py`): Robot action planning, navigation, vision-guided actions, simulation

### Multi-Agent Crews
- **Crew Manager** (`app/agents/crew_manager.py`): Base AgentRole and Crew classes with sequential/parallel/hierarchical orchestration
- **Biology Crew** (`app/agents/biology_crew.py`): Drug Discovery and Protein Analysis crews
- **Robotics Crew** (`app/agents/robotics_crew.py`): Navigation, Manipulation, and Swarm Coordination crews

### Plugin System
- **Plugin Manager** (`app/modules/plugin_manager.py`): Dynamic plugin registration, built-in plugins for biology/vision/robotics

## Running the Project

Two workflows run the complete system:
1. **AMAIMA Backend**: `cd amaima/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. **AMAIMA Frontend**: `cd amaima/frontend && npm run dev -- --webpack`

## API Endpoints

### Core
- `GET /health` - Health check with component status
- `GET /v1/stats` - System statistics (queries, uptime, connections)
- `POST /v1/query` - Submit query for intelligent routing and AI inference
- `GET /v1/models` - List available NVIDIA NIM models
- `GET /v1/capabilities` - System capabilities and model details
- `POST /v1/simulate` - Simulate routing without execution

### Biology
- `POST /v1/biology/discover` - Drug discovery pipeline
- `POST /v1/biology/protein` - Protein sequence analysis
- `POST /v1/biology/optimize` - Molecule optimization
- `POST /v1/biology/query` - General biology/chemistry query
- `GET /v1/biology/capabilities` - Biology service capabilities

### Robotics
- `POST /v1/robotics/navigate` - Robot navigation commands
- `POST /v1/robotics/plan` - Robot action planning
- `POST /v1/robotics/simulate` - Action simulation
- `POST /v1/robotics/vision-action` - Vision-guided robot actions
- `GET /v1/robotics/capabilities` - Robotics service capabilities

### Vision
- `POST /v1/vision/reason` - Vision reasoning with optional media
- `POST /v1/vision/analyze-image` - Image analysis
- `POST /v1/vision/embodied-reasoning` - Embodied reasoning
- `GET /v1/vision/capabilities` - Vision service capabilities

### Agents
- `POST /v1/agents/run` - Run agent crew (research, drug_discovery, protein_analysis, navigation, manipulation, swarm, custom)
- `GET /v1/agents/types` - List available crew types

### Plugins
- `GET /v1/plugins` - List registered plugins
- `GET /v1/plugins/{id}/capabilities` - Plugin capabilities

## Smart Router

The routing engine analyzes queries and determines:
- **Domain Detection**: biology, robotics, vision, or general (keyword-based classification)
- **Complexity Level**: TRIVIAL, SIMPLE, MODERATE, COMPLEX, EXPERT
- **Model Selection**: Routes to appropriate NVIDIA NIM model based on query complexity
- **Execution Mode**: streaming, batch, parallel
- **Performance Estimates**: Latency and cost predictions

### Model Registry (14 NVIDIA NIM Models)

#### General Language Models
- meta/llama-3.1-8b-instruct (TRIVIAL/SIMPLE complexity)
- meta/llama-3.1-70b-instruct (MODERATE/ADVANCED complexity)
- meta/llama-3.1-405b-instruct (EXPERT complexity)
- mistralai/mixtral-8x7b-instruct-v0.1 (COMPLEX, cost-efficient MoE)
- google/gemma-2-9b-it (lightweight/edge)
- nvidia/nemotron-nano-9b-v2 (edge deployment, agentic AI)

#### Vision/Multimodal Models
- nvidia/cosmos-reason2-7b (primary vision-language reasoning, embodied AI)
- nvidia/cosmos-predict2-14b (video generation, future state prediction)
- nvidia/llama-3.1-nemotron-nano-vl-8b (multimodal understanding)

#### Biology/Drug Discovery Models
- nvidia/bionemo-megamolbart (molecular generation, drug discovery)
- nvidia/bionemo-esm2 (protein structure prediction)

#### Robotics Models
- nvidia/isaac-gr00t-n1.6 (humanoid robot control, VLA)
- nvidia/alpamayo-1 (autonomous vehicle reasoning, VLA)

### Domain-Aware Routing
- Biology queries (drug/protein/molecule keywords) -> nvidia/bionemo-megamolbart
- Vision queries (image/video/scene keywords) -> nvidia/cosmos-reason2-7b
- Robotics queries (robot/navigate/grasp keywords) -> nvidia/isaac-gr00t-n1.6
- General queries -> complexity-based model selection (Llama/Mixtral/Gemma)

## File Structure
```
amaima/
├── frontend/                    # Next.js frontend
│   ├── src/app/                # App router pages
│   ├── src/app/api/            # API routes (proxy to backend)
│   │   └── v1/
│   │       ├── query/route.ts
│   │       ├── biology/route.ts
│   │       ├── robotics/route.ts
│   │       ├── vision/route.ts
│   │       ├── agents/route.ts
│   │       └── plugins/route.ts
│   ├── src/app/core/           # Core components, hooks, lib
│   ├── vercel.json             # Vercel deployment config
│   ├── package.json
│   └── next.config.js
├── backend/                    # FastAPI backend
│   ├── main.py                 # Entry point
│   ├── amaima_config.yaml      # Configuration
│   ├── app/core/               # Core modules
│   │   └── unified_smart_router.py
│   ├── app/modules/            # Feature modules
│   │   ├── nvidia_nim_client.py    # NVIDIA NIM API client
│   │   ├── execution_engine.py     # Model execution
│   │   ├── smart_router_engine.py  # Query routing + domain detection
│   │   ├── plugin_manager.py       # Plugin system
│   │   └── observability_framework.py
│   ├── app/services/           # Domain-specific services
│   │   ├── vision_service.py       # Cosmos R2 vision/embodied reasoning
│   │   ├── biology_service.py      # BioNeMo drug discovery/protein
│   │   └── robotics_service.py     # ROS2/Isaac robotics
│   ├── app/routers/            # FastAPI routers
│   │   ├── biology.py
│   │   ├── robotics.py
│   │   └── vision.py
│   ├── app/agents/             # Multi-agent orchestration
│   │   ├── crew_manager.py         # Base crew framework
│   │   ├── biology_crew.py         # Drug discovery/protein crews
│   │   └── robotics_crew.py        # Navigation/manipulation/swarm crews
│   └── app/security.py        # API key auth
└── docs/                      # Documentation
    └── integration-strategy_guide.md
```

## Environment Variables
- `BACKEND_URL`: Backend API URL for frontend proxy (default: http://localhost:8000)
- `NVIDIA_API_KEY`: NVIDIA NIM API key for AI inference (secret)
- `API_SECRET_KEY`: Backend API authentication key
- `AMAIMA_EXECUTION_MODE`: Set to `execution-enabled` for real inference
- `COSMOS_NIM_URL`: Cosmos R2 NIM endpoint (default: https://integrate.api.nvidia.com/v1)
- `BIONEMO_NIM_URL`: BioNeMo NIM endpoint (default: https://integrate.api.nvidia.com/v1)

## Design Decisions
- Cloud-first architecture: Heavy packages (torch, vLLM, RDKit, rclpy, PyBullet) are optional with graceful fallbacks to cloud NIM APIs
- Services use try/except for optional imports, defaulting to cloud endpoints when local packages unavailable
- Multi-agent crews use lightweight AgentRole/Crew classes instead of heavy CrewAI dependency
- Plugin system allows dynamic registration of domain services

## Recent Changes
- Set up full production system with Python backend
- Configured Smart Router for query complexity analysis
- Connected frontend to backend API
- Both workflows running and verified working
- Added favicon with AI-themed icon
- Added sample query buttons for quick testing
- Implemented query history with localStorage persistence
- Added loading skeleton states for polished UX
- Added collapsible Available Models display from /v1/models endpoint
- Updated: January 24, 2026
- February 10, 2026: Migrated project to new Replit environment. Installed all backend Python packages and frontend Node.js dependencies.
- February 10, 2026: Integrated NVIDIA NIM for real AI inference. Added vercel.json for Vercel deployment. Updated model mappings to real NVIDIA NIM models.
- February 11, 2026: Created comprehensive backend deployment guide.
- February 17, 2026: Major integration update - Added Vision (Cosmos R2), Biology (BioNeMo), and Robotics (ROS2/Isaac) services with cloud-first NIM APIs. Created multi-agent crew orchestration (research, drug discovery, navigation, manipulation, swarm). Enhanced smart router with domain-aware keyword classification. Added plugin manager. Created frontend API proxy routes and updated UI with 7 operation types and domain-specific sample queries.
- February 17, 2026: Expanded model registry from 5 to 14 models. Added Cosmos Reason2 7B, Cosmos Predict 2.5 14B, Nemotron Nano 9B v2, Nemotron Nano VL 8B, BioNeMo MegaMolBART, BioNeMo ESM-2, Isaac GR00T N1.6, and Alpamayo 1. Implemented domain-aware model routing (biology/vision/robotics queries auto-route to specialized models). Updated frontend with domain badges, categories, and model descriptions.
- February 17, 2026: Monetization system - Three-tier subscription (Community free/1K queries, Production $49/10K, Enterprise $499/unlimited). PostgreSQL tables: api_keys, usage_events, monthly_usage. Backend billing service with usage tracking, tier enforcement middleware. Stripe integration via stripe-replit-sync with checkout, portal, webhook routes. Billing dashboard with plan cards, API key management, usage meter. Security: billing endpoints require authentication, usage endpoint enforces ownership, update-tier restricted to admin, webhook handles subscription tier changes automatically.
