# AMAIMA - Advanced Model-Aware AI Management Interface

## Overview
AMAIMA is a production AI query platform with intelligent model routing. The system consists of a FastAPI Python backend with a Smart Router engine and a Next.js frontend for the user interface.

## Project Architecture

### Frontend
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with custom dark theme
- **Location**: `amaima/frontend/`
- **Port**: 5000 (for Replit webview)
- **Key Features**:
  - Query input interface with operation type selection
  - Real-time API status and system metrics
  - Routing decision visualization
  - Performance metrics display

### Backend
- **Framework**: FastAPI with Python 3.11
- **Location**: `amaima/backend/`
- **Port**: 8000 (internal)
- **Key Features**:
  - Smart Router engine for query complexity analysis
  - Query processing with routing decisions
  - Health monitoring and statistics endpoints
  - CORS-enabled API

## Running the Project

Two workflows run the complete system:
1. **AMAIMA Backend**: `cd amaima/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. **AMAIMA Frontend**: `cd amaima/frontend && npm run dev`

## API Endpoints

- `GET /health` - Health check with component status
- `GET /v1/stats` - System statistics (queries, uptime, connections)
- `POST /v1/query` - Submit query for intelligent routing
- `GET /v1/models` - List available models

## Smart Router

The routing engine analyzes queries and determines:
- **Complexity Level**: TRIVIAL, SIMPLE, MODERATE, COMPLEX, EXPERT
- **Model Selection**: Routes to appropriate model based on query
- **Execution Mode**: streaming, batch, parallel
- **Security Level**: public, private, confidential, top_secret
- **Performance Estimates**: Latency and cost predictions

## File Structure
```
amaima/
├── frontend/           # Next.js frontend
│   ├── src/app/       # App router pages
│   ├── package.json
│   └── next.config.js
├── backend/           # FastAPI backend
│   ├── main.py        # Entry point
│   ├── app/core/      # Core modules
│   │   └── unified_smart_router.py
│   └── requirements.txt
└── mobile/           # Android client specs (reference)
```

## Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

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
