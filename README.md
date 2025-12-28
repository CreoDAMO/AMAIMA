# AMAIMA System README

**Advanced Multimodal AI Model Architecture - Enterprise-Grade AI Orchestration Platform**

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-109989?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Kotlin 1.9](https://img.shields.io/badge/Kotlin-B125EA?style=for-the-badge&logo=kotlin&logoColor=white)](https://kotlinlang.org/)
[![License: AMAIMA v1.0](https://img.shields.io/badge/License-AMAIMA%20v1.0-blueviolet?style=for-the-badge)](LICENSE)

</div>

---

## Overview

AMAIMA delivers a next-generation AI infrastructure that intelligently routes queries across multiple model architectures for optimal resource utilization, cost efficiency, and response quality. The platform integrates three key components:

- **Python Backend Infrastructure** — Enterprise-grade AI orchestration with 18 consolidated modules
- **Web Frontend Application** — Modern React/Next.js interface with real-time streaming
- **Android Mobile Client** — Native application featuring offline-first architecture

The Smart Router Engine drives core innovation by analyzing query complexity with client-side ML and historical patterns to select models from 1B to 200B parameters. This method cuts costs up to 40% versus always-cloud strategies while hitting sub-200ms response times for 95% of queries.

<div align="center">
<img src="docs/images/architecture-overview.png" alt="AMAIMA Architecture Overview" width="800"/>
</div>

---

## Key Features

### Intelligent Query Routing

A 5-level taxonomy—TRIVIAL, SIMPLE, STANDARD, ADVANCED, EXPERT—routes queries to optimal models. Classification factors include device capabilities, network conditions, security needs, and query history. Routing completes in under 50ms for seamless selection.

### Progressive Model Loading

TensorRT quantization (INT8/FP16/BF16) reduces memory up to 4x. The loader uses lazy loading and smart caching to achieve under 2-second cold starts for common models. LRU eviction keeps peak memory below 50GB in high-traffic scenarios.

### Multi-Platform Consistency

Identical API contracts, data models, authentication, and error handling across platforms minimize context switching for developers and deliver uniform user experiences.

### Defense-Grade Security

DARPA AIxCC scanning with auto-patching supports NIST 800-53 and FedRAMP compliance. Multi-factor auth, AES-256 encryption, and certificate pinning protect against attacks.

### Offline-First Mobile Architecture

The Android client enables full offline operation via local TensorFlow Lite inference, Room caching, and WorkManager sync. Users submit queries and run workflows offline, with automatic reconnection sync.

---

## Project Structure

```
amaima/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # REST endpoints and WebSocket handlers
│   │   ├── core/              # Configuration, security, and utilities
│   │   ├── models/            # Pydantic models and DTOs
│   │   ├── services/          # Business logic and ML orchestration
│   │   └── modules/           # 18 consolidated backend modules
│   ├── tests/                 # Unit and integration tests
│   ├── Dockerfile             # Container definition
│   └── pyproject.toml         # Poetry dependencies
│
├── frontend/                   # Next.js 15 web application
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # React components and UI kit
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # Utilities and API clients
│   │   ├── store/             # Zustand state management
│   │   └── styles/            # Global styles and themes
│   ├── public/                # Static assets
│   ├── Dockerfile             # Container definition
│   └── package.json           # npm dependencies
│
├── mobile/                     # Android Kotlin application
│   ├── app/
│   │   ├── data/              # Repository pattern, Room database
│   │   ├── domain/            # Use cases and business logic
│   │   ├── presentation/      # Jetpack Compose UI layer
│   │   └── infrastructure/    # TensorFlow Lite, auth, networking
│   ├── gradle/                # Build configuration
│   └── build.gradle.kts       # Gradle dependencies
│
├── docs/                       # Documentation and guides
├── docker-compose.yml         # Local development orchestration
├── Makefile                   # Development commands
└── README.md                  # This file
```

---

## Prerequisites

### System Requirements

| Component | Minimum      | Recommended     |
|-----------|--------------|-----------------|
| CPU       | 8 cores      | 16 cores        |
| Memory    | 16GB         | 64GB            |
| Storage   | 50GB SSD     | 200GB NVMe      |
| GPU (optional) | NVIDIA RTX 3080 | NVIDIA A100 |
| OS        | Ubuntu 22.04 LTS / macOS 14+ / Windows 11 | Same |

### Required Accounts and APIs

- **Docker Hub Account** — For base images and container pushes
- **Nvidia NIM API Access** — For inference acceleration (optional; local models supported)
- **GitHub Account** — For repository and CI/CD

### Software Dependencies

| Tool              | Version | Purpose                  |
|-------------------|---------|--------------------------|
| Docker            | 24.0+   | Container runtime/builds |
| Docker Compose    | 2.20+   | Multi-container orchestration |
| Python            | 3.10+   | Backend development      |
| Node.js           | 20.x    | Frontend development     |
| JDK               | 17      | Android development      |
| kubectl           | 1.28+   | Kubernetes deployment    |
| terraform         | 1.6+    | Infrastructure provisioning |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/AMAIMA.git
cd amaima
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your keys and settings
```

### 3. Launch Development Environment

```bash
docker-compose up -d
```

Or run components separately:

```bash
# Backend
cd backend
make install
make dev

# Frontend
cd frontend
npm install
npm run dev

# Mobile
cd mobile
# Open in Android Studio
```

### 4. Access Interfaces

| Service     | URL                          | Credentials |
|-------------|------------------------------|-------------|
| Backend API | http://localhost:8000/api/docs | None (dev)  |
| Frontend    | http://localhost:3000        | None (dev)  |
| Prometheus  | http://localhost:9090        | None        |
| Grafana     | http://localhost:3001        | admin/admin |

---

## Backend Development

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Server

```bash
make dev
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Commands

```bash
make test      # Tests
make lint      # Linting
make format    # Formatting
make type-check # Type checking
make docs      # OpenAPI docs
```

### Environment Variables (.env)

```env
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key

NVIDIA_API_KEY=your-key
DATABASE_URL=postgresql://user:pass@localhost:5432/amaima
REDIS_URL=redis://localhost:6379

ALLOWED_ORIGINS=http://localhost:3000
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_MINUTES=15
REFRESH_TOKEN_DAYS=30

DEFAULT_MODEL_SIZE=nano
TENSORRT_ENABLED=true
QUANTIZATION_MODE=fp16
```

---

## Frontend Development

### Installation

```bash
cd frontend
npm install
npm install @tensorflow/tfjs @tensorflow-models/universal-sentence-encoder framer-motion zustand
```

### Run Server

```bash
npm run dev
# Build preview
npm run build && npm run start
```

### Commands

```bash
npm test            # Unit
npm run test:e2e    # E2E
npm run lint
npm run type-check
npm run test:visual
```

### Environment Variables (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_OFFLINE_MODE=true

NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret
```

---

## Mobile Development

### Setup

```bash
cd mobile
# Open in Android Studio Ladybug+
```

Configure SDK:
- Platform 34
- Build-Tools 34.0.0

### Build

```bash
./gradlew assembleDebug   # Debug
./gradlew assembleRelease # Release
./gradlew bundleRelease   # Bundle
```

### Configuration (res/values/config.xml)

```xml
<resources>
    <string name="api_base_url">https://api.amaima.example.com</string>
    <string name="ws_base_url">wss://api.amaima.example.com/ws</string>
    <string name="ml_model_cache_size_mb">500</string>
    <string name="offline_enabled">true</string>
    <bool name="biometric_enabled">true</bool>
    <bool name="certificate_pinning_enabled">true</bool>
</resources>
```

### TFLite Models

Place in `app/src/main/assets/models/`:
- complexity_estimation.tflite
- sentiment_analysis.tflite
- keyword_extraction.tflite

---

## Model Specifications

| Size   | Parameters | Use Case                  | Cost/1K Tokens |
|--------|------------|---------------------------|----------------|
| NANO   | 1B         | Simple queries            | $0.0003        |
| MICRO  | 3B         | Standard conversations    | $0.0005        |
| MINI   | 7B         | Code/analysis             | $0.0007        |
| MEDIUM | 13B        | Complex reasoning         | $0.0009        |
| LARGE  | 33B        | Advanced tasks            | $0.0012        |
| ULTRA  | 200B       | Expert responses          | $0.0015        |

### Quantization Modes

| Mode | Reduction | Accuracy Impact | GPUs          |
|------|-----------|-----------------|---------------|
| FP32 | Baseline  | None            | Development   |
| FP16 | 2x        | Minimal         | Production    |
| BF16 | 2x        | None (Ampere+)  | Modern        |
| INT8 | 4x        | ~1%             | Memory-limited|

### Complexity Levels

| Level    | Indicators                          | Example                              |
|----------|-------------------------------------|--------------------------------------|
| TRIVIAL  | <10 words, no terms                 | "What is the weather?"               |
| SIMPLE   | 10-25 words, basic                  | "Explain photosynthesis simply."     |
| STANDARD | 25-50 words, domain terms           | "How does REST API auth work?"       |
| ADVANCED | 50-100 words, multiple concepts     | "Design e-commerce microservices."   |
| EXPERT   | >100 words, specialized             | "Optimize distributed transactions." |

---

## Deployment

### Docker

**Backend**:
```bash
docker build -t amaima/backend:latest ./backend
docker run -d -p 8000:8000 --env-file backend/.env amaima/backend:latest
```

**Frontend**:
```bash
docker build -t amaima/frontend:latest ./frontend
docker run -d -p 80:80 amaima/frontend:latest
```

### Kubernetes

```bash
kubectl create namespace amaima
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/monitoring/
```

### Terraform

```bash
cd infrastructure/terraform
terraform init
terraform apply -var="environment=production"
```

---

## API Reference

### REST

| Method | Endpoint              | Description          |
|--------|-----------------------|----------------------|
| POST   | `/api/v1/query`       | Submit query         |
| GET    | `/api/v1/query/{id}`  | Get result           |
| POST   | `/api/v1/workflow`    | Create workflow      |
| GET    | `/api/v1/workflow/{id}` | Get workflow       |
| POST   | `/api/v1/models/load` | Pre-load model       |
| GET    | `/api/v1/health`      | Health check         |

### WebSocket

| Endpoint             | Description                 |
|----------------------|-----------------------------|
| `/ws/query`          | Stream query responses      |
| `/ws/workflow/{id}`  | Workflow progress           |
| `/ws/metrics`        | Real-time metrics           |

Full docs: `/api/docs` (Swagger) or `/api/docs/redoc`.

---

## Testing

**Backend**:
```bash
cd backend
pytest tests/ --cov=app
```

**Frontend**:
```bash
cd frontend
npm test
npm run test:e2e
```

**Mobile**:
```bash
cd mobile
./gradlew test
./gradlew connectedAndroidTest
```

Coverage: Backend 90%+, Frontend 85%+, Mobile 80%+.

---

## Contributing

1. Fork repo
2. Create branch: `git checkout -b feature/name`
3. Add tests
4. Run suite: `make test-all`
5. Submit PR

Standards: PEP8/Black (backend), Prettier (frontend), Kotlin Guide (mobile).

---

## Monitoring

Metrics: `/metrics` (Prometheus)

Key:
- `amaima_query_latency_seconds` (p95 < 0.2)
- `amaima_model_load_seconds` (p95 < 2.0)

JSON logging with configurable level.

---

## Troubleshooting

**Backend start failure** → Check `docker logs`, verify `.env`.

**WebSocket issues** → Check CORS, console errors.

**Mobile crashes** → `adb logcat | grep amaima`.

**GPU OOM** → Lower batch, enable quantization.

---

## License

**AMAIMA is multi-licensed under the AMAIMA License v1.0 (December 28, 2025)**

You must choose **ONE** of the following options:

1. **AMAIMA Community License** – Responsible open-source use (individuals, research, non-commercial)  
2. **AMAIMA Production License** – Source-available with delayed open transition (Business Source License 1.1)  
3. **AMAIMA Commercial License** – Full unrestricted enterprise use (proprietary)

Full license text available in [`LICENSE`](LICENSE).

For commercial licensing inquiries: licensing@amaima.ai

---

## Support

- Docs: https://docs.amaima.example.com
- Issues: https://github.com/your-org/amaima/issues
- Discord: https://discord.gg/amaima
- Email: support@amaima.example.com

---

<div align="center">

**AMAIMA** — *Intelligent AI Orchestration at Scale*

</div>
