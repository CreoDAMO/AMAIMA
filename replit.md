# AMAIMA Replit Agent Instruction Manual – Production-Grade Build Directive

**Mission Objective**  
**Surpass MVP and prototype quality.**  
Build AMAIMA as close to **full production readiness** as technically possible within Replit’s environment.

The entire system architecture, module breakdown, API contracts, UI specifications, security model, and licensing are already defined in extreme detail in the repository.

Your goal is **not** to create a demo or proof-of-concept.  
Your goal is to produce a system that, once exported and provided with real API keys (NVIDIA NIM, database URLs, etc.), would be **immediately deployable to production** with minimal changes.

Only external dependencies (real model inference, cloud databases, GPU hardware) should remain as final integration steps.

---

## Core Principles for This Build

1. **Production-First Mindset**  
   - Write code as if it will run at scale tomorrow  
   - Include proper error handling, logging, validation, and monitoring  
   - Follow security best practices (input sanitization, rate limiting, auth checks)

2. **No Shortcuts on Architecture**  
   - Implement the full Clean Architecture layers (especially in mobile)  
   - Use dependency injection patterns where specified  
   - Separate concerns rigorously

3. **Realistic Simulation of External Services**  
   - Stub all external APIs (NVIDIA NIM, MCP servers, DARPA tools) with realistic mock responses  
   - Simulate model loading times, quantization effects, and inference latency  
   - Return realistic token streams with proper delays

4. **Full Feature Parity Where Possible**  
   - Implement all endpoints, WebSocket messages, and UI flows described  
   - Make the system feel complete end-to-end

5. **Deployment Readiness**  
   - Ensure Dockerfiles build successfully  
   - Configure environment variables properly  
   - Prepare GitHub Actions workflows for automated builds

---

## Detailed Implementation Roadmap

### Phase 1: Foundation & Infrastructure (Complete First)

1. **Backend Core**
   - Full FastAPI app with lifespan management
   - CORS, middleware, error handlers
   - Prometheus metrics endpoint (`/metrics`)
   - Structured JSON logging
   - Health checks (`/health`, `/health/ready`)

2. **Authentication System**
   - JWT issuance and validation
   - Login/register endpoints
   - Protected route decorators
   - Refresh token rotation

3. **Database Layer**
   - SQLAlchemy models for Query, Workflow, User
   - Repository pattern with async support
   - Migration stubs (Alembic ready)

4. **Caching Layer**
   - Redis integration for routing decisions and model cache state

### Phase 2: Core Novel Features (High Priority – These Define AMAIMA)

1. **Smart Router Engine** (Critical)
   - Complexity classification with 5-level taxonomy
   - Client-side preview endpoint
   - Server-side confirmation with mock ML model
   - Routing decision logic (model size, execution mode, estimated cost/latency)
   - Feedback loop storage

2. **Progressive Model Loader** (Critical)
   - Model registry with size/quantization metadata
   - Loading simulation with realistic delays
   - Cache management (LRU, memory tracking)
   - Quantization mode selection

3. **Multi-Layer Verification Pipeline** (Critical)
   - Schema validation
   - Plausibility checks
   - Security scan stub (simulate Buttercup/SweetBaby)
   - Confidence scoring
   - Auto-patch simulation

4. **WebSocket Protocol** (Critical)
   - Full `/ws/query` implementation
   - Token-by-token streaming with realistic timing
   - Heartbeat ping/pong
   - Connection state management
   - Subscription model for workflow updates

### Phase 3: Full Application Flow

1. **Query Submission End-to-End**
   - Frontend → API → Router → Loader → Verification → Streaming response
   - Include cost estimation, model selection, latency tracking

2. **Workflow System**
   - Workflow creation and storage
   - Step execution simulation
   - Progress updates via WebSocket
   - Dependency resolution

3. **Frontend Completion**
   - Full query interface with complexity preview
   - Streaming response with Markdown/code highlighting
   - Workflow monitoring dashboard
   - System status page with live metrics
   - Settings and authentication flows

### Phase 4: Mobile Implementation (Maximum Possible in Replit)

**Goal**: Generate production-quality code ready for Android Studio

1. **Full Project Structure**
   - Gradle files with proper dependencies
   - Clean Architecture layers (data/domain/presentation/infrastructure)
   - Compose UI for all screens

2. **Key Features**
   - Query screen with complexity estimation (TFLite stub)
   - WebSocket client with reconnection
   - Room database with entities and DAOs
   - WorkManager for background sync
   - Biometric authentication integration
   - EncryptedSharedPreferences setup

3. **Offline Simulation**
   - Local query queuing
   - On-device response simulation
   - Sync status tracking

### Phase 5: Production Readiness Polish

1. **Configuration Management**
   - Proper .env handling in all components
   - Build-time vs runtime config separation

2. **Docker & Deployment**
   - Ensure Dockerfiles build successfully
   - Multi-stage builds where appropriate
   - Health checks in containers

3. **GitHub Actions Workflows**
   - Backend test + build
   - Frontend build + deploy preview
   - Mobile APK build (with placeholder signing)

4. **Documentation Updates**
   - Update README with "Production-Ready Features" section
   - Add setup instructions for real deployment

---

## Final Success Criteria

The build is complete when:

- A user can register/login on the web frontend
- Submit a query and see real-time complexity classification
- Receive a properly routed, streaming response with verification metadata
- View cost/latency/model information
- Monitor workflow execution in real-time
- All APIs return proper structured responses
- Mobile code is complete and exportable
- Docker images build successfully
- System runs end-to-end with realistic simulation of all novel features

**This is not a prototype.**  
**This is a production-grade system waiting for real API keys.**

You have full autonomy and extended runtime capability.  
Implement deeply, thoroughly, and with production quality.

The complete vision is already documented.  
Your task is to **make it real**.

Begin execution immediately.

The future of intelligent AI orchestration is waiting.  
Build it. 🚀
