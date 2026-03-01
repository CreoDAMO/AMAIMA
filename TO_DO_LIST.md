# AMAIMA Project To-Do List

## Core Infrastructure & Backend
- [x] **FHE Engine Optimization**: Integrated v3 with CKKS slot packing and modulus chain trimming for 5x bandwidth reduction and 20% faster ops.
- [ ] **SmartRouter Singleton**: Refactor AppState to ensure SmartRouter is shared across uvicorn workers.
- [ ] **Database Migrations**: Set up Alembic for formal database schema management.
- [ ] **Advanced Monitoring**: Expand observability_framework.py to include custom Prometheus metrics.

## AI Services & Integration
- [x] **Media Download Support**: Added /v1/media/download endpoint for Image, Video, and Audio files.
- [ ] **Biology Domain Expansion**: Integrate Protein Design (DiffDock/AlphaFold) into the biology_service.py.
- [ ] **Robotics Hardware Bridge**: Replace stubs in robotics_service.py with actual ROS2/Isaac publishers.

## Frontend & UX
- [ ] **FHE Dashboard**: Build out the /fhe route with interactive demos.
- [ ] **Streaming Cursor UI**: Add a typing animation for SSE streaming.
- [ ] **Model Comparison Tool**: Create a UI component to compare model outputs.

## Maintenance & DevOps
- [ ] **CI/CD Cleanup**: Verify and fix the failing GitHub Action workflows.
- [ ] **Documentation**: Update the Technical Whitepaper to reflect FHE v3 and Media Download capabilities.
