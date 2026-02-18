# AMAIMA - Advanced Model-Aware AI Management Interface

## Overview
AMAIMA is an enterprise-grade AI orchestration platform designed for intelligent model routing, multi-agent collaboration, and specialized reasoning across various domains. It leverages NVIDIA NIM for optimized cloud-based inference, featuring a FastAPI backend and a Next.js frontend, complemented by an Android mobile application. AMAIMA aims to provide a unified interface for managing and utilizing advanced AI models, with core capabilities in vision/multimodal reasoning (Cosmos R2), biology/drug discovery (BioNeMo), and robotics (ROS2/Isaac). The platform is built for scalability and extensibility, offering a plugin system and advanced features like conversation history, model benchmarking, and a tiered monetization system.

## User Preferences
I want iterative development.
Ask before making major changes.
Do not make changes to the `amaima/docs/integration-strategy_guide.md` file.

## System Architecture
AMAIMA adopts a cloud-first, modular architecture. The **Frontend** is built with Next.js 16 and React, styled with Tailwind CSS, providing a responsive UI with 7 operation types (General, Code, Analysis, Biology, Robotics, Vision, Agents) and real-time metrics. The **Backend** uses FastAPI with Python 3.11, integrating NVIDIA NIM for AI inference. Key architectural decisions include a Smart Router engine for domain-aware query classification and model selection, and domain-specific services for Vision (Cosmos R2), Biology (BioNeMo), and Robotics (ROS2/Isaac).

Multi-agent orchestration is managed by a Crew Manager using lightweight AgentRole/Crew classes, supporting various specialized crews (e.g., Drug Discovery, Navigation) and a LangChain Agent for stateful, graph-based workflow execution. A dynamic plugin system allows for extensibility. The system is designed for optional local package usage, gracefully falling back to cloud NIM APIs when heavy dependencies are unavailable.

UI/UX decisions prioritize a dark theme, query input interfaces with sample queries, real-time API status, routing decision visualization, and performance metrics. Core technical implementations include a unified smart router, an NVIDIA NIM API client, and an execution engine.

**Feature Specifications:**
- **Smart Router**: Analyzes queries for domain detection (biology, robotics, vision, general), complexity level (TRIVIAL to EXPERT), and selects appropriate NVIDIA NIM models, estimating performance.
- **API Endpoints**: Comprehensive set of RESTful APIs for core functionalities, domain-specific operations (biology, robotics, vision), agent execution, and plugin management.
- **Monetization System**: A three-tier subscription model (Community, Production, Enterprise) with usage tracking, API key management, and Stripe integration.
- **Advanced Features**: Includes persistent conversation history, file upload capabilities, automated model benchmarking, response caching, webhook notifications, team/organization accounts, custom routing rules, usage export, and A/B testing framework.
- **Stateful Workflow Agent**: Graph-based workflow engine with WorkflowState, WorkflowNode, and ConditionalEdge classes, supporting 5 built-in workflow types.
- **Agent Builder UI**: React Flow-based drag-and-drop visual agent workflow builder at `/agent-builder`, with node categories (Agents, Biology, Robotics, Workflow), pre-built templates (Research Pipeline, Drug Discovery, Navigation Crew), and direct execution via the backend agents API.
- **NIM Prompt Caching**: In-memory LRU cache (500 entries, 10min TTL) in `nvidia_nim_client.py` with SHA-256 hash-based key generation, reducing latency 20-30% on repeated queries. Stats exposed via `/v1/cache/stats`.
- **MAU Rate Limiting**: HTTP middleware in FastAPI that checks per-API-key monthly active usage against tier limits and triggers webhook alerts at the 900 MAU threshold.
- **Billing Analytics Dashboard**: Recharts-powered analytics tab in the billing page showing daily query volume, latency trends, model usage pie chart, endpoint breakdown, tier distribution, and cache performance stats via `/v1/billing/analytics`.
- **Integration Tests**: End-to-end tests for biology/drug discovery crew pipeline, protein analysis, NIM caching, and agent types (`tests/integration/test_biology_e2e.py`, 8 tests).
- **SSE Streaming**: Real-time Server-Sent Events streaming via `/v1/query/stream` endpoint using httpx async streaming from NVIDIA NIM, with EventSourceResponse and event types (start, token, finish, done, error). Frontend toggle for streaming mode with live token rendering and cursor animation.
- **User Authentication**: Full email/password auth system in `app/auth.py` with bcrypt hashing, JWT access tokens (60min, HS256) and refresh tokens (30-day with revocation). Endpoints: `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/me`, `/v1/auth/api-keys`. Users table with roles (user/admin), linked to api_keys via user_id. Frontend login/register page at `/login`.
- **Admin Dashboard**: Role-gated admin analytics in `app/admin.py` with aggregated platform metrics (total users, MAU, queries, tokens, revenue estimates, tier distribution, daily usage, model/endpoint breakdowns, top users). System health endpoint with database/cache/NIM status. Frontend admin page at `/admin` with recharts visualizations, KPI cards, and auto-refresh.

## Mobile App (Android)
- **Location**: `amaima/mobile/`
- **Stack**: Kotlin + Jetpack Compose, Hilt DI, Room DB, Retrofit/OkHttp, Material 3
- **ML Runtime**: ONNX Runtime (primary, `.onnx` models) + TensorFlow Lite (secondary, `.tflite` models) — replacing full TensorFlow for portability and smaller size
- **ML Manager**: `OnDeviceMLManager` in `app/src/main/java/com/amaima/app/ml/OnDeviceMLManager.kt` — dual-runtime inference engine supporting both ONNX and TFLite models
- **Build System**: Gradle 8.5, AGP 8.2.0, Kotlin 1.9.20, KSP for annotation processing
- **Min SDK**: 26 (Android 8.0), Target SDK: 34
- **Security**: Biometric auth, EncryptedSharedPreferences, certificate pinning, network security config
- **Features**: Background sync (WorkManager), WebSocket streaming, deep linking, offline support
- **Advanced ML Features** (in `app/src/main/java/com/amaima/app/ml/`):
  - **ModelRegistry + ModelStore**: Hot-swappable model lifecycle management with disk caching, SHA-256 integrity checks, LRU eviction (500MB cap), and StateFlow-based UI observation
  - **Quantized Models**: INT8/FP16/INT4 precision variants with automatic path resolution and NNAPI delegation for FP16 on TFLite
  - **StreamingInference**: Flow-based token-by-token and chunked inference with temperature/topK sampling, KV-cache support, and cancellation
  - **EmbeddingEngine**: On-device text (384-dim) and image (512-dim) embedding generation via ONNX, with cosine similarity and ImageNet normalization
  - **AudioEngine**: Whisper-style speech-to-text with log-mel spectrogram computation, VAD, chunked processing, real-time mic streaming via Flow, and WAV file support
  - **VisionEngine**: Image classification (MobileNet-compatible), OCR (CTC decoder), and object detection (YOLO-compatible) with softmax, NMS, and top-K results
  - **VectorStore**: In-memory vector database with cosine/euclidean/dot-product similarity search, metadata filtering, binary persistence, and LRU eviction (10K entries)
  - **ModelDownloader**: Asset-first model loading with HTTP fallback, progress callbacks, and cache management

## External Dependencies
- **NVIDIA NIM API**: Primary AI inference engine for all models.
- **Cosmos R2**: Used by the Vision Service for embodied reasoning, image/video analysis, and scene understanding.
- **BioNeMo**: Used by the Biology Service for drug discovery, protein analysis, and molecule optimization.
- **ROS2/Isaac**: Used by the Robotics Service for robot action planning, navigation, and vision-guided actions.
- **PostgreSQL**: Database for monetization system (api_keys, usage_events, monthly_usage), conversation history, benchmarking, and organization data.
- **Stripe**: Payment gateway for subscription management and billing.
- **Vercel**: Deployment platform for the frontend.
- **Docker Compose**: For multi-service deployment.
- **ONNX Runtime**: On-device ML inference for mobile (replaces TensorFlow).
- **TensorFlow Lite**: Lightweight on-device inference (secondary runtime for mobile).