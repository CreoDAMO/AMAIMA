# How Enterprises Deploy AMAIMA

AMAIMA is designed for high-governance AI orchestration. Follow this guide for production deployment.

## Deployment Architecture

1.  **Public Inspection Layer** (Frontend)
    *   **Platform**: Vercel or similar static hosting.
    *   **Path**: `/playground` for simulation testing.
    *   **Access**: Public read-only or SSO-protected.

2.  **Private Execution Layer** (Backend)
    *   **Platform**: AWS EC2, EKS (Kubernetes), or Google Cloud Run.
    *   **Endpoint**: `/v1/query` protected by API keys/OAuth2.
    *   **Storage**: PostgreSQL for telemetry, Redis for caching.

## Configuration & Safeguards

### Execution Mode Toggle
Control the risk profile using the `AMAIMA_EXECUTION_MODE` environment variable:
*   `decision-only`: (Default) System routes and logs but does not execute model calls.
*   `execution-enabled`: Full end-to-end processing enabled.

### Versioned Telemetry
All decisions are tagged with `decision_schema_version` (e.g., `1.0.0`) for audit stability.

## Integration Flow

1.  **Simulate**: Client calls `/v1/simulate` to preview routing.
2.  **Inspect**: Admin reviews decision transparency via the "Why This Route?" panel.
3.  **Execute**: Authorized client submits `/v1/query` for final processing.

## Monitoring & Compliance

*   **Observability**: Grafana dashboards monitor upscale rates, latency, and costs.
*   **Audit**: NIST 800-53 and SOC2 control mappings are available in the whitepaper.
*   **Privacy**: Telemetry data is hashed; sensitive inputs can be excluded via policy.

---
*Contact: governance@amaima.ai for enterprise licenses and pilot checklists.*
