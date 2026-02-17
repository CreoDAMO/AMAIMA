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

## External Dependencies
- **NVIDIA NIM API**: Primary AI inference engine for all models.
- **Cosmos R2**: Used by the Vision Service for embodied reasoning, image/video analysis, and scene understanding.
- **BioNeMo**: Used by the Biology Service for drug discovery, protein analysis, and molecule optimization.
- **ROS2/Isaac**: Used by the Robotics Service for robot action planning, navigation, and vision-guided actions.
- **PostgreSQL**: Database for monetization system (api_keys, usage_events, monthly_usage), conversation history, benchmarking, and organization data.
- **Stripe**: Payment gateway for subscription management and billing.
- **Vercel**: Deployment platform for the frontend.
- **Docker Compose**: For multi-service deployment.