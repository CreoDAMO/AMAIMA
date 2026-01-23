# AMAIMA - Advanced Model-Aware AI Management Interface

## Overview
AMAIMA is a next-generation AI query platform with intelligent model routing. This project was imported from GitHub and adapted for the Replit environment.

## Project Architecture

### Frontend (Active)
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with custom dark theme
- **Location**: `amaima/frontend/`
- **Port**: 5000 (for Replit webview)
- **Key Features**:
  - Query input interface with demo response
  - Feature showcase cards
  - System status dashboard
  - Responsive dark theme design

### Backend (Reference Only)
- **Framework**: FastAPI with Python
- **Location**: `amaima/backend/`
- **Status**: Not running (designed for Docker environment)
- **Note**: The backend contains ML model routing code but requires significant dependencies (PyTorch, TensorFlow, etc.) that are not currently set up

## Running the Project

The project runs via a single workflow:
- **Workflow**: `AMAIMA Frontend`
- **Command**: `cd amaima/frontend && npm run dev`
- **Output**: Webview on port 5000

## File Structure
```
amaima/
├── frontend/           # Next.js frontend (active)
│   ├── src/
│   │   └── app/       # Next.js app router
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
├── backend/           # FastAPI backend (reference)
│   ├── app/
│   ├── auth/
│   ├── middleware/
│   ├── routers/
│   └── requirements.txt
└── mobile/           # Android client specs (reference)
```

## Development Notes
- Frontend is configured to allow all hosts for Replit proxy compatibility
- No authentication is required for the demo
- The backend would need a full Python environment with ML dependencies to run

## Recent Changes
- Adapted from Docker-based deployment to Replit environment
- Created simplified demo page without complex backend dependencies
- Configured Next.js for port 5000 with host allowance
- Set up Tailwind CSS with custom dark theme
