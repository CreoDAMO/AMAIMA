# AMAIMA Governance & Compliance

## Governance Diagram
```mermaid
graph TD
    User((User)) --> API[AMAIMA API]
    API --> Router{Smart Router}
    Router --> Complexity[Complexity Analysis]
    Router --> ModelFit[Model Fit Evaluation]
    Router --> Security[Security Policy Check]
    
    Complexity --> Decision[Routing Decision]
    ModelFit --> Decision
    Security --> Decision
    
    Decision --> Execution[Model Execution]
    Execution --> Telemetry[Decision Telemetry]
    Telemetry --> Feedback[User Feedback]
    Feedback --> Tuning[Heuristic Tuning]
    Tuning --> Router
```

## SOC2 / NIST Mapping
| Control ID | Control Name | AMAIMA Implementation |
|------------|--------------|------------------------|
| AC-2 | Account Management | Integrated Replit Auth |
| AU-2 | Event Logging | Decision Telemetry Schema |
| SC-7 | Boundary Protection | Smart Router Security Levels |
| SI-4 | Information System Monitoring | Real-time Health & Stats Endpoints |
