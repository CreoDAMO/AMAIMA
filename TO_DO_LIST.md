# AMAIMA Project To-Do List

## Core Infrastructure & Backend
- [ ] **FHE Engine Optimization**: Implement the 3-stage Docker build with Intel HEXL and Microsoft SEAL v4.1.2 for AVX-512 acceleration.
- [ ] **SmartRouter Singleton**: Refactor `AppState` to ensure `SmartRouter` is shared across uvicorn workers instead of being instantiated per worker.
- [ ] **Database Migrations**: Set up Alembic for formal database schema management.
- [ ] **Advanced Monitoring**: Expand `observability_framework.py` to include custom Prometheus metrics for FHE latency and model routing accuracy.

## AI Services & Integration
- [ ] **Video Generation Polish**: Add asynchronous webhook support for long-running Cosmos video generation tasks to avoid holding HTTP connections open for >60s.
- [ ] **Biology Domain Expansion**: Integrate Protein Design (DiffDock/AlphaFold) into the `biology_service.py` beyond simple molecule scoring.
- [ ] **Robotics Hardware Bridge**: Replace stubs in `robotics_service.py` with actual ROS2/rclpy message publishers for real-world hardware integration.

## Frontend & UX
- [ ] **FHE Dashboard**: Build out the `/fhe` route with interactive demos for encrypted drug discovery and secure voting.
- [ ] **Streaming Cursor UI**: Add a typing animation/cursor for the SSE streaming mode in the chat interface.
- [ ] **Model Comparison Tool**: Create a UI component to compare outputs from different models side-by-side (e.g., GPT-4 vs Llama-3-70B).

## Maintenance & DevOps
- [ ] **CI/CD Cleanup**: Verify and fix the failing GitHub Action workflows (backend.yml) and ensure multi-platform builds for the mobile app.
- [ ] **Dependency Audit**: Regular audit of `requirements.txt` and `package.json` for security vulnerabilities.
- [ ] **Documentation**: Update the Technical Whitepaper to reflect the newly added FHE and Video Generation capabilities.
