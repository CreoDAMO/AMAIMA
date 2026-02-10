# AMAIMA - Advanced Model-Aware AI Management Interface

## Overview
AMAIMA is a production AI query platform with intelligent model routing. The system consists of a FastAPI Python backend with a Smart Router engine and a Next.js frontend for the user interface. The backend uses NVIDIA NIM for real AI model inference.

## Project Architecture

### Frontend
- **Framework**: Next.js 16 with React
- **Styling**: Tailwind CSS with custom dark theme
- **Location**: `amaima/frontend/`
- **Port**: 5000 (for Replit webview)
- **Deployment**: Vercel-ready with `vercel.json` config
- **Key Features**:
  - Query input interface with operation type selection
  - Real-time API status and system metrics
  - Routing decision visualization
  - Performance metrics display
  - API routes proxy to backend via `BACKEND_URL` env var

### Backend
- **Framework**: FastAPI with Python 3.11
- **Location**: `amaima/backend/`
- **Port**: 8000 (internal)
- **AI Inference**: NVIDIA NIM API (cloud-based, no GPU required)
- **Key Features**:
  - Smart Router engine for query complexity analysis
  - NVIDIA NIM integration for real AI model inference
  - Query processing with routing decisions
  - Health monitoring and statistics endpoints
  - CORS-enabled API

## Running the Project

Two workflows run the complete system:
1. **AMAIMA Backend**: `cd amaima/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. **AMAIMA Frontend**: `cd amaima/frontend && npm run dev -- --webpack`

## API Endpoints

- `GET /health` - Health check with component status
- `GET /v1/stats` - System statistics (queries, uptime, connections)
- `POST /v1/query` - Submit query for intelligent routing and AI inference
- `GET /v1/models` - List available NVIDIA NIM models
- `GET /v1/capabilities` - System capabilities and model details
- `POST /v1/simulate` - Simulate routing without execution

## Smart Router

The routing engine analyzes queries and determines:
- **Complexity Level**: TRIVIAL, SIMPLE, MODERATE, COMPLEX, EXPERT
- **Model Selection**: Routes to appropriate NVIDIA NIM model based on query complexity
- **Execution Mode**: streaming, batch, parallel
- **Performance Estimates**: Latency and cost predictions

### Model Mapping (NVIDIA NIM)
- TRIVIAL/SIMPLE -> meta/llama-3.1-8b-instruct
- MODERATE -> meta/llama-3.1-70b-instruct
- COMPLEX -> mistralai/mixtral-8x7b-instruct-v0.1
- EXPERT -> meta/llama-3.1-405b-instruct

## File Structure
```
amaima/
├── frontend/                    # Next.js frontend
│   ├── src/app/                # App router pages
│   ├── src/app/api/            # API routes (proxy to backend)
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
│   │   └── smart_router_engine.py  # Query routing logic
│   └── app/security.py        # API key auth
└── docs/                      # Documentation
```

## Environment Variables
- `BACKEND_URL`: Backend API URL for frontend proxy (default: http://localhost:8000)
- `NVIDIA_API_KEY`: NVIDIA NIM API key for AI inference (secret)
- `API_SECRET_KEY`: Backend API authentication key
- `AMAIMA_EXECUTION_MODE`: Set to `execution-enabled` for real inference

## Vercel Deployment (Frontend)
1. Set Root Directory to `amaima/frontend` in Vercel project settings
2. Set `BACKEND_URL` environment variable to your hosted backend URL
3. The frontend build works with `next build`

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
- February 10, 2026: Migrated project to new Replit environment. Installed all backend Python packages and frontend Node.js dependencies. Fixed missing query client module and tsconfig path aliases. Updated Next.js dev origins config.
- February 10, 2026: Integrated NVIDIA NIM for real AI inference. Added vercel.json for Vercel deployment. Updated model mappings from placeholders to real NVIDIA NIM models (Llama 3.1, Mixtral, Gemma 2). Updated execution engine to call NVIDIA NIM API.
- February 10, 2026: Fixed .gitignore `lib/` pattern that was blocking frontend src/app/core/lib/ files from being tracked in git (root cause of Vercel build failure). Created docs/fixed-mobile-workflow.md with corrected GitHub Actions cache key syntax.
