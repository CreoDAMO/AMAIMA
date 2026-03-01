# AMAIMA v5.0.0 - Multimodal AI Operating System

## Architecture
- **Backend**: FastAPI (Python 3.11) on port 8000.
- **Frontend**: Next.js (TypeScript) on port 5000.
- **Mobile**: Android (Kotlin/Compose) with modern Gradle/KSP setup.
- **FHE Engine v4**: Post-quantum secure encryption using Microsoft SEAL/TenSEAL.
  - CKKS Error Tracking (Bio-precision)
  - Energy Profiling (Nanojoule accounting)
  - High-Throughput Pipelines (>10k compounds/sec)
  - Verifiable Computation (Hash-chain ZKP)
  - Federated Learning Hybrid Aggregator

## Configuration
- `FHE_ENABLED=true`: Required for homomorphic operations.
- `AMAIMA_EXECUTION_MODE=execution-enabled`: Required for engine activation.

## Workflows
- `AMAIMA Backend`: Starts the FastAPI server.
- `AMAIMA Frontend`: Starts the Next.js dev server.
