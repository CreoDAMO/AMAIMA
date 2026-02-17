"""
AMAIMA Production Backend Server
FastAPI-based REST and WebSocket interface
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging
import uuid
import os

from app.core.unified_smart_router import SmartRouter, RoutingDecision
from app.modules.smart_router_engine import route_query
from app.modules.execution_engine import execute_model
from app.security import get_api_key, enforce_tier_limit
from app.routers import biology as biology_router
from app.routers import robotics as robotics_router
from app.routers import vision as vision_router
from fastapi import Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str = Field(..., description="User query text")
    operation: str = Field(default="general", description="Operation type")
    file_types: Optional[List[str]] = Field(default=None, description="Attached file types")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")


class QueryResponse(BaseModel):
    response_id: str
    response_text: str
    model_used: str
    routing_decision: Dict[str, Any]
    confidence: float
    latency_ms: float
    timestamp: datetime

class ExecuteResponse(BaseModel):
    query_hash: str
    complexity_level: str
    model: str
    execution_mode: str
    confidence: Dict[str, float]
    reasons: Dict[str, list]
    simulated: bool
    execution: Optional[str] = None
    confidence_scope: Optional[str] = None
    output: str
    actual_latency_ms: int
    actual_cost_usd: float


class WorkflowStep(BaseModel):
    step_id: str
    step_type: str
    parameters: Dict[str, Any]
    dependencies: Optional[List[str]] = None


class WorkflowRequest(BaseModel):
    workflow_id: str
    steps: List[WorkflowStep]
    context: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    results: List[Dict[str, Any]]
    total_steps: int
    completed_steps: int
    duration_ms: float


class FeedbackRequest(BaseModel):
    response_id: str
    feedback_type: str
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, Dict[str, Any]]
    timestamp: datetime


class AppState:
    def __init__(self):
        self.smart_router: Optional[SmartRouter] = None
        self.active_connections: Dict[str, WebSocket] = {}
        self.query_count = 0
        self.start_time = datetime.now()
    
    def initialize(self, darpa_enabled: bool = False):
        self.smart_router = SmartRouter(darpa_enabled=darpa_enabled)
        logger.info("Application initialized")


app_state = AppState()

app = FastAPI(
    title="AMAIMA API",
    description="Advanced Multimodal AI Model Architecture - Production API",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(biology_router.router)
app.include_router(robotics_router.router)
app.include_router(vision_router.router)


@app.on_event("startup")
async def startup():
    from app.database import init_db
    from app.modules.observability_framework import get_metrics
    from app.modules.plugin_manager import initialize_builtin_plugins
    init_db()
    metrics = get_metrics()
    metrics.start_metrics_server()
    initialize_builtin_plugins()
    app_state.initialize(darpa_enabled=False)
    logger.info("AMAIMA API server started")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    components = {
        "router": {
            "status": "healthy" if app_state.smart_router else "unavailable",
            "type": "smart_router"
        },
        "api": {
            "status": "healthy",
            "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
            "query_count": app_state.query_count
        }
    }
    
    all_healthy = all(
        c.get("status") == "healthy" 
        for c in components.values() 
        if isinstance(c, dict) and "status" in c
    )
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version="5.0.0",
        components=components,
        timestamp=datetime.now()
    )


@app.post("/v1/query", response_model=ExecuteResponse)
async def process_query(request: QueryRequest, api_key_info: dict = Depends(get_api_key)):
    try:
        await enforce_tier_limit(api_key_info)

        start_time_ms = datetime.now()
        decision = route_query(request.query, simulate=False)
        decision["_original_query"] = request.query
        execution_result = await execute_model(decision)
        decision.pop("_original_query", None)
        response = {**decision, **execution_result}
        
        app_state.query_count += 1

        latency = int((datetime.now() - start_time_ms).total_seconds() * 1000)
        tokens_est = len(response.get("output", "")) // 4

        try:
            from app.billing import record_usage
            await record_usage(
                api_key_id=api_key_info.get("id", "admin"),
                endpoint="/v1/query",
                model_used=response.get("model", ""),
                tokens_estimated=tokens_est,
                latency_ms=latency,
            )
        except Exception as usage_err:
            logger.warning(f"Usage tracking failed: {usage_err}")

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/workflow", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    try:
        start_time = datetime.now()
        results = []
        
        step_map = {step.step_id: step for step in request.steps}
        completed = set()
        
        max_iterations = len(request.steps) * 2
        iteration = 0
        
        while len(completed) < len(request.steps) and iteration < max_iterations:
            iteration += 1
            
            for step in request.steps:
                if step.step_id in completed:
                    continue
                
                if step.dependencies:
                    if not all(dep in completed for dep in step.dependencies):
                        continue
                
                result = {
                    "step_id": step.step_id,
                    "step_type": step.step_type,
                    "status": "completed",
                    "output": f"Processed {step.step_type} with params: {step.parameters}"
                }
                
                results.append(result)
                completed.add(step.step_id)
        
        return WorkflowResponse(
            workflow_id=request.workflow_id,
            status="completed" if len(completed) == len(request.steps) else "partial",
            results=results,
            total_steps=len(request.steps),
            completed_steps=len(completed),
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/feedback")
async def submit_feedback(request: FeedbackRequest):
    logger.info(f"Feedback received: {request.feedback_type} for {request.response_id}")
    
    return {
        "status": "recorded",
        "response_id": request.response_id,
        "feedback_type": request.feedback_type,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/v1/models")
async def list_models():
    from app.modules.nvidia_nim_client import list_available_models, is_configured, get_model_for_complexity
    models = list_available_models()
    default = get_model_for_complexity("MODERATE")
    return {
        "available_models": models,
        "default_model": default,
        "nvidia_nim_configured": is_configured(),
    }


@app.get("/v1/capabilities")
async def get_capabilities():
    from app.modules.nvidia_nim_client import list_available_models, NVIDIA_MODELS, is_configured
    models_info = []
    for model_id, info in NVIDIA_MODELS.items():
        models_info.append({
            "id": model_id,
            "name": info["name"],
            "params": info["parameters"],
            "context_window": info["context_window"],
            "cost_per_1k_tokens": info["cost_per_1k_tokens"],
        })
    return {
        "models": models_info,
        "nvidia_nim_configured": is_configured(),
        "execution_modes": ["batch_parallel", "parallel_min_latency", "streaming_real_time"],
        "security_levels": ["low", "medium", "high", "paranoid"],
        "complexity_levels": ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "EXPERT", "BORDERLINE_ADVANCED_EXPERT"],
        "max_context": 128000,
        "tunable_params": {
            "confidence_weights": {
                "complexity": 0.4, 
                "model_fit": 0.35, 
                "execution_fit": 0.25
            }
        }
    }


@app.post("/v1/simulate")
async def simulate_query_endpoint(request: QueryRequest):
    """
    Simulates a query routing decision without executing the query.
    """
    try:
        decision = route_query(request.query, simulate=True)
        return decision
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/stats")
async def get_statistics():
    return {
        "total_queries": app_state.query_count,
        "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
        "active_connections": len(app_state.active_connections),
        "version": "5.0.0"
    }


class AgentCrewRequest(BaseModel):
    task: str = Field(..., description="Task for the agent crew")
    crew_type: str = Field(default="research", description="Crew type: research, drug_discovery, protein_analysis, navigation, manipulation, swarm, custom")
    process: str = Field(default="sequential", description="Process: sequential, parallel, hierarchical")
    roles: Optional[List[Dict[str, Any]]] = Field(default=None, description="Custom roles for custom crew type")
    environment: Optional[str] = Field(default=None, description="Environment context for robotics crews")
    robot_type: Optional[str] = Field(default="amr", description="Robot type for robotics crews")


@app.post("/v1/agents/run")
async def run_agent_crew(request: AgentCrewRequest):
    try:
        if request.crew_type == "research":
            from app.agents.crew_manager import run_research_crew
            result = await run_research_crew(request.task, request.process)
        elif request.crew_type == "drug_discovery":
            from app.agents.biology_crew import run_drug_discovery_crew
            result = await run_drug_discovery_crew(request.task)
        elif request.crew_type == "protein_analysis":
            from app.agents.biology_crew import run_protein_analysis_crew
            result = await run_protein_analysis_crew(request.task)
        elif request.crew_type == "navigation":
            from app.agents.robotics_crew import run_navigation_crew
            result = await run_navigation_crew(request.task, request.environment or "indoor", request.robot_type or "amr")
        elif request.crew_type == "manipulation":
            from app.agents.robotics_crew import run_manipulation_crew
            result = await run_manipulation_crew(request.task)
        elif request.crew_type == "swarm":
            from app.agents.robotics_crew import run_swarm_crew
            result = await run_swarm_crew(request.task, environment=request.environment or "warehouse")
        elif request.crew_type == "custom" and request.roles:
            from app.agents.crew_manager import run_custom_crew
            result = await run_custom_crew(request.task, request.roles, request.process)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown crew type: {request.crew_type}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent crew execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/agents/types")
async def list_agent_types():
    return {
        "crew_types": [
            {"id": "research", "name": "Research Crew", "description": "Researcher, Analyst, Synthesizer for general research tasks"},
            {"id": "drug_discovery", "name": "Drug Discovery Crew", "description": "Molecule Generator, ADMET Predictor, Lead Optimizer, Safety Reviewer"},
            {"id": "protein_analysis", "name": "Protein Analysis Crew", "description": "Structural Biologist, Binding Site Predictor"},
            {"id": "navigation", "name": "Navigation Crew", "description": "Perception, Path Planner, Action Executor, Safety Monitor"},
            {"id": "manipulation", "name": "Manipulation Crew", "description": "Perception, Grasp Planner, Action Executor, Safety Monitor"},
            {"id": "swarm", "name": "Swarm Coordination Crew", "description": "Coordinator, Perception, Path Planner, Safety Monitor"},
            {"id": "custom", "name": "Custom Crew", "description": "Build your own crew with custom roles"},
        ],
        "processes": ["sequential", "parallel", "hierarchical"],
    }


@app.get("/v1/plugins")
async def list_plugins():
    from app.modules.plugin_manager import list_plugins
    return {"plugins": list_plugins()}


@app.get("/v1/plugins/{plugin_id}/capabilities")
async def plugin_capabilities(plugin_id: str):
    from app.modules.plugin_manager import get_plugin_capabilities
    caps = get_plugin_capabilities(plugin_id)
    if caps:
        return caps
    raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found or has no capabilities")


@app.websocket("/v1/ws/query")
async def websocket_query(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    app_state.active_connections[connection_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            query = message.get("query", "")
            operation = message.get("operation", "general")
            
            if not app_state.smart_router:
                await websocket.send_text(json.dumps({
                    "error": "Smart router not initialized"
                }))
                continue
            
            routing_decision = app_state.smart_router.route(query, operation)
            
            response = {
                "response_id": str(uuid.uuid4()),
                "query": query,
                "routing": {
                    "mode": routing_decision.execution_mode.value,
                    "model": routing_decision.model_size.name,
                    "complexity": routing_decision.complexity.name,
                    "confidence": routing_decision.confidence
                },
                "response_text": f"Processed: {query[:50]}..."
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if connection_id in app_state.active_connections:
            del app_state.active_connections[connection_id]


@app.websocket("/v1/ws/system")
async def websocket_system_status(websocket: WebSocket):
    await websocket.accept()
    
    try:
        import psutil
        while True:
            status = {
                "type": "system_status",
                "data": {
                    "cpuUsage": psutil.cpu_percent(),
                    "memoryUsage": psutil.virtual_memory().percent,
                    "activeQueries": app_state.query_count,
                    "queriesPerMinute": app_state.query_count / max(1, (datetime.now() - app_state.start_time).total_seconds() / 60)
                },
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        logger.info("System status WebSocket disconnected")


class CreateApiKeyRequest(BaseModel):
    email: Optional[str] = None
    tier: str = Field(default="community", description="Tier: community, production, enterprise")


class UpdateTierRequest(BaseModel):
    api_key_id: str
    tier: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


@app.post("/v1/billing/api-keys")
async def create_api_key_endpoint(request: CreateApiKeyRequest):
    from app.billing import create_api_key
    result = await create_api_key(email=request.email, tier="community")
    return result


@app.get("/v1/billing/api-keys")
async def list_api_keys_endpoint(email: Optional[str] = None):
    from app.billing import list_api_keys
    keys = await list_api_keys(email=email)
    return {"api_keys": keys}


@app.get("/v1/billing/usage/{api_key_id}")
async def get_usage_endpoint(api_key_id: str, api_key_info: dict = Depends(get_api_key)):
    if api_key_info.get("id") != "admin" and api_key_info.get("id") != api_key_id:
        raise HTTPException(status_code=403, detail="Access denied")
    from app.billing import get_usage_stats
    stats = await get_usage_stats(api_key_id)
    return stats


@app.get("/v1/billing/usage-by-key")
async def get_usage_by_key(api_key_info: dict = Depends(get_api_key)):
    from app.billing import get_usage_stats
    stats = await get_usage_stats(api_key_info["id"])
    return stats


@app.post("/v1/billing/update-tier")
async def update_tier_endpoint(request: UpdateTierRequest, api_key_info: dict = Depends(get_api_key)):
    if api_key_info.get("id") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.billing import update_api_key_tier
    await update_api_key_tier(
        api_key_id=request.api_key_id,
        tier=request.tier,
        stripe_customer_id=request.stripe_customer_id,
        stripe_subscription_id=request.stripe_subscription_id,
    )
    return {"status": "updated", "api_key_id": request.api_key_id, "tier": request.tier}


@app.post("/v1/billing/webhook-tier-update")
async def webhook_tier_update(request: UpdateTierRequest):
    webhook_secret = os.getenv("WEBHOOK_INTERNAL_SECRET", "")
    if not webhook_secret:
        raise HTTPException(status_code=403, detail="Webhook not configured")
    from app.billing import update_api_key_tier
    await update_api_key_tier(
        api_key_id=request.api_key_id,
        tier=request.tier,
        stripe_customer_id=request.stripe_customer_id,
        stripe_subscription_id=request.stripe_subscription_id,
    )
    return {"status": "updated"}


@app.get("/v1/billing/tiers")
async def list_tiers():
    from app.billing import TIER_LIMITS
    return {"tiers": TIER_LIMITS}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
