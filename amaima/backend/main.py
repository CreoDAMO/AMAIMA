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
from app.security import get_api_key, enforce_tier_limit, get_current_user, require_admin
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
    try:
        from app.auth import init_auth_tables
        await init_auth_tables()
    except Exception as e:
        logger.warning(f"Auth tables init skipped: {e}")
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
        model_used = decision.get("model", "unknown")

        try:
            from app.benchmarks import get_cached_response, set_cached_response
            cached = await get_cached_response(request.query, model_used)
            if cached:
                cached["cache_hit"] = True
                app_state.query_count += 1
                return cached
        except Exception as cache_err:
            logger.debug(f"Cache lookup skipped: {cache_err}")

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

        try:
            from app.benchmarks import set_cached_response, record_benchmark
            await set_cached_response(request.query, model_used, response)
            await record_benchmark(
                model=model_used,
                query_complexity=decision.get("complexity_level", "SIMPLE"),
                domain=decision.get("domain", "general"),
                latency_ms=latency,
                tokens_input=len(request.query) // 4,
                tokens_output=tokens_est,
                cost_usd=response.get("actual_cost_usd", 0),
                success=True
            )
        except Exception as bench_err:
            logger.debug(f"Benchmark/cache write skipped: {bench_err}")

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/query/stream")
async def stream_query(request: QueryRequest, api_key_info: dict = Depends(get_api_key)):
    from sse_starlette.sse import EventSourceResponse
    from app.modules.nvidia_nim_client import (
        is_configured, chat_completion_stream, NVIDIA_MODELS, get_model_for_complexity
    )

    await enforce_tier_limit(api_key_info)
    decision = route_query(request.query, simulate=False)
    model_used = decision.get("model", "unknown")

    if decision.get("simulated", True) or not is_configured():
        async def sim_gen():
            tokens = "Streaming is not available in simulation mode. Configure NVIDIA_API_KEY for real-time streaming.".split()
            for i, tok in enumerate(tokens):
                yield {"event": "token", "data": json.dumps({"content": tok + " ", "index": i + 1})}
                await asyncio.sleep(0.03)
            yield {"event": "done", "data": json.dumps({"model": model_used, "total_tokens": len(tokens), "latency_ms": 0})}
        return EventSourceResponse(sim_gen())

    router_model = decision.get("model", "")
    nim_model = router_model if router_model in NVIDIA_MODELS else get_model_for_complexity(decision.get("complexity_level", "SIMPLE"))

    messages = [
        {"role": "system", "content": "You are AMAIMA, an Advanced Multimodal AI assistant. Provide clear, accurate, and helpful responses."},
        {"role": "user", "content": request.query},
    ]

    async def event_generator():
        start_time = datetime.now()
        yield {"event": "start", "data": json.dumps({"model": nim_model, "complexity": decision.get("complexity_level", "SIMPLE")})}
        try:
            async for chunk in chat_completion_stream(model=nim_model, messages=messages):
                yield {"event": chunk["event"], "data": json.dumps(chunk["data"])}

                if chunk["event"] == "done":
                    latency = int((datetime.now() - start_time).total_seconds() * 1000)
                    tokens_est = chunk["data"].get("total_tokens", 0)
                    try:
                        from app.billing import record_usage
                        await record_usage(
                            api_key_id=api_key_info.get("id", "admin"),
                            endpoint="/v1/query/stream",
                            model_used=nim_model,
                            tokens_estimated=tokens_est,
                            latency_ms=latency,
                        )
                    except Exception:
                        pass
                    app_state.query_count += 1
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


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
        elif request.crew_type == "workflow":
            from app.agents.langchain_agent import run_langchain_agent
            workflow_type = request.environment or "research"
            result = await run_langchain_agent(request.task, workflow_type=workflow_type)
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
            {"id": "workflow", "name": "Stateful Workflow", "description": "Multi-step stateful workflows with conditional logic (research, complex_reasoning, biology, robotics, vision)"},
        ],
        "processes": ["sequential", "parallel", "hierarchical"],
        "workflow_types": ["research", "complex_reasoning", "biology", "robotics", "vision"],
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


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="Password (min 8 characters)")
    display_name: Optional[str] = Field(default=None, description="Display name")


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Email address for password reset")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password (min 8 characters)")


@app.post("/v1/auth/register")
async def register(request: RegisterRequest):
    from app.auth import register_user
    try:
        result = await register_user(request.email, request.password, request.display_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/v1/auth/login")
async def login(request: LoginRequest):
    from app.auth import login_user
    result = await login_user(request.email, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return result


@app.post("/v1/auth/refresh")
async def refresh_token(request: RefreshRequest):
    from app.auth import refresh_access_token
    result = await refresh_access_token(request.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return result


@app.get("/v1/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    from app.auth import get_user_api_keys
    keys = await get_user_api_keys(user["id"])
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "role": user.get("role"),
            "created_at": str(user.get("created_at", "")),
            "last_login_at": str(user.get("last_login_at", "")),
        },
        "api_keys": keys,
    }


@app.post("/v1/auth/api-keys")
async def create_user_api_key(user: dict = Depends(get_current_user)):
    from app.billing import create_api_key
    from app.auth import link_api_key_to_user
    result = await create_api_key(email=user["email"], tier="community")
    await link_api_key_to_user(result["id"], user["id"])
    return result


@app.post("/v1/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    from app.auth import request_password_reset
    reset_token = await request_password_reset(request.email)
    if not reset_token:
        return {"message": "If an account with that email exists, a password reset link has been generated."}
    logger.info("Password reset requested for: %s", request.email)
    return {
        "message": "If an account with that email exists, a password reset link has been generated.",
        "reset_token": reset_token,
        "expires_in": "1 hour",
        "note": "Use this token with /v1/auth/reset-password to set a new password.",
    }


@app.post("/v1/auth/reset-password")
async def reset_password_endpoint(request: ResetPasswordRequest):
    from app.auth import reset_password
    try:
        success = await reset_password(request.token, request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password has been reset successfully. You can now log in with your new password."}


@app.get("/v1/admin/analytics")
async def admin_analytics(admin: dict = Depends(require_admin)):
    from app.admin import get_admin_analytics
    return await get_admin_analytics()


@app.get("/v1/admin/health")
async def admin_health(admin: dict = Depends(require_admin)):
    from app.admin import get_system_health
    return await get_system_health()


@app.get("/v1/admin/users")
async def admin_users(
    limit: int = 50, offset: int = 0,
    admin: dict = Depends(require_admin)
):
    from app.admin import get_all_users_with_usage
    users = await get_all_users_with_usage(limit=limit, offset=offset)
    return {"users": users, "limit": limit, "offset": offset}


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
async def get_usage_endpoint(api_key_id: str):
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


# ── Conversation History ──────────────────────────────────

class ConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    operation_type: Optional[str] = "general"
    model: Optional[str] = None

class MessageRequest(BaseModel):
    content: str
    role: str = "user"

@app.post("/v1/conversations")
async def create_conversation(request: ConversationRequest, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import create_conversation
    result = await create_conversation(
        api_key_id=api_key_info["id"],
        title=request.title or "New Conversation",
        operation_type=request.operation_type or "general",
        model=request.model
    )
    return result

@app.get("/v1/conversations")
async def list_conversations(limit: int = 20, offset: int = 0, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import list_conversations
    convos = await list_conversations(api_key_info["id"], limit, offset)
    return {"conversations": convos}

@app.get("/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    from app.conversations import get_conversation
    convo = await get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@app.post("/v1/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: MessageRequest, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import add_message, get_conversation
    convo = await get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_msg = await add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.content
    )

    decision = route_query(request.content, simulate=False)
    result = await execute_model(decision)

    from app.benchmarks import record_benchmark
    model_used = decision.get("model", "unknown")
    latency = result.get("actual_latency_ms", 0)
    tokens = len(result.get("output", "")) // 4
    await record_benchmark(
        model=model_used,
        query_complexity=decision.get("complexity_level", "SIMPLE"),
        domain=decision.get("domain", "general"),
        latency_ms=latency,
        tokens_input=len(request.content) // 4,
        tokens_output=tokens,
        cost_usd=result.get("actual_cost_usd", 0),
        success=True
    )

    assistant_msg = await add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.get("output", ""),
        model=model_used,
        tokens_used=tokens,
        latency_ms=latency,
        metadata={"routing": decision}
    )

    return {"user_message": user_msg, "assistant_message": assistant_msg}

@app.delete("/v1/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import delete_conversation
    await delete_conversation(conversation_id)
    return {"status": "deleted"}

@app.get("/v1/conversations/search/{query}")
async def search_conversations_endpoint(query: str, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import search_conversations
    results = await search_conversations(api_key_info["id"], query)
    return {"conversations": results}


# ── File Upload ──────────────────────────────────────

from fastapi import UploadFile, File as FastAPIFile

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/v1/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    purpose: str = "general",
    api_key_info: dict = Depends(get_api_key)
):
    import hashlib
    import secrets as sec

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    allowed_types = ["image/png", "image/jpeg", "image/gif", "image/webp",
                     "application/pdf", "text/plain", "text/csv",
                     "chemical/x-mdl-sdfile", "chemical/x-pdb"]
    content_type = file.content_type or "application/octet-stream"

    file_id = sec.token_hex(8)
    checksum = hashlib.md5(content).hexdigest()
    filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    from app.billing import get_pool
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO uploads (id, api_key_id, filename, content_type, size_bytes, storage_path, checksum, purpose)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        file_id, api_key_info["id"], file.filename, content_type, len(content), filepath, checksum, purpose
    )

    return {
        "id": file_id,
        "filename": file.filename,
        "content_type": content_type,
        "size_bytes": len(content),
        "purpose": purpose
    }

@app.get("/v1/uploads")
async def list_uploads(api_key_info: dict = Depends(get_api_key)):
    from app.billing import get_pool
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, filename, content_type, size_bytes, purpose, created_at FROM uploads WHERE api_key_id = $1 ORDER BY created_at DESC",
        api_key_info["id"]
    )
    return {"uploads": [dict(r) for r in rows]}


# ── Model Benchmarks ──────────────────────────────────────

@app.get("/v1/benchmarks")
async def get_benchmarks(model: Optional[str] = None, days: int = 30):
    from app.benchmarks import get_benchmark_stats
    stats = await get_benchmark_stats(model, days)
    return {"benchmarks": stats}

@app.get("/v1/benchmarks/leaderboard")
async def get_leaderboard():
    from app.benchmarks import get_benchmark_leaderboard
    board = await get_benchmark_leaderboard()
    return {"leaderboard": board}

@app.get("/v1/benchmarks/timeseries/{model_id:path}")
async def get_timeseries(model_id: str, days: int = 7):
    from app.benchmarks import get_benchmark_timeseries
    data = await get_benchmark_timeseries(model_id, days)
    return {"timeseries": data}


# ── Response Cache ──────────────────────────────────────

@app.get("/v1/cache/stats")
async def cache_stats():
    from app.benchmarks import get_cache_stats
    stats = await get_cache_stats()
    return stats

@app.post("/v1/cache/clear")
async def clear_cache(api_key_info: dict = Depends(get_api_key)):
    if api_key_info.get("id") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.benchmarks import clear_expired_cache
    deleted = await clear_expired_cache()
    return {"status": "cleared", "entries_removed": deleted}


# ── Webhooks ──────────────────────────────────────

class WebhookRequest(BaseModel):
    url: str
    events: Optional[List[str]] = None

@app.post("/v1/webhooks")
async def create_webhook(request: WebhookRequest, api_key_info: dict = Depends(get_api_key)):
    from app.webhooks import create_webhook
    webhook = await create_webhook(api_key_info["id"], request.url, request.events)
    return webhook

@app.get("/v1/webhooks")
async def list_webhooks(api_key_info: dict = Depends(get_api_key)):
    from app.webhooks import list_webhooks
    hooks = await list_webhooks(api_key_info["id"])
    return {"webhooks": hooks}

@app.delete("/v1/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.webhooks import delete_webhook
    await delete_webhook(webhook_id)
    return {"status": "deleted"}


# ── Organizations ──────────────────────────────────────

class OrgRequest(BaseModel):
    name: str

class OrgMemberRequest(BaseModel):
    api_key_id: str
    role: str = "member"

@app.post("/v1/organizations")
async def create_org(request: OrgRequest, api_key_info: dict = Depends(get_api_key)):
    from app.organizations import create_organization
    org = await create_organization(request.name, api_key_info["id"])
    return org

@app.get("/v1/organizations")
async def list_orgs(api_key_info: dict = Depends(get_api_key)):
    from app.organizations import list_organizations
    orgs = await list_organizations(api_key_info["id"])
    return {"organizations": orgs}

@app.get("/v1/organizations/{org_id}")
async def get_org(org_id: str):
    from app.organizations import get_organization
    org = await get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.post("/v1/organizations/{org_id}/members")
async def add_org_member(org_id: str, request: OrgMemberRequest, api_key_info: dict = Depends(get_api_key)):
    from app.organizations import add_member
    member = await add_member(org_id, request.api_key_id, request.role, api_key_info["id"])
    return member

@app.delete("/v1/organizations/{org_id}/members/{member_key_id}")
async def remove_org_member(org_id: str, member_key_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.organizations import remove_member
    await remove_member(org_id, member_key_id)
    return {"status": "removed"}

@app.delete("/v1/organizations/{org_id}")
async def delete_org(org_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.organizations import delete_organization
    await delete_organization(org_id)
    return {"status": "deleted"}


# ── Custom Routing Rules ──────────────────────────────────────

class RoutingRuleRequest(BaseModel):
    name: str
    preferred_model: str
    domain: Optional[str] = None
    min_complexity: Optional[str] = None
    max_complexity: Optional[str] = None
    fallback_model: Optional[str] = None
    priority: int = 0

@app.post("/v1/routing-rules")
async def create_routing_rule(request: RoutingRuleRequest, api_key_info: dict = Depends(get_api_key)):
    if api_key_info.get("tier") != "enterprise" and api_key_info.get("id") != "admin":
        raise HTTPException(status_code=403, detail="Enterprise tier required for custom routing rules")
    from app.webhooks import create_routing_rule
    rule = await create_routing_rule(
        api_key_info["id"], request.name, request.preferred_model,
        request.domain, request.min_complexity, request.max_complexity,
        request.fallback_model, request.priority
    )
    return rule

@app.get("/v1/routing-rules")
async def list_routing_rules(api_key_info: dict = Depends(get_api_key)):
    from app.webhooks import list_routing_rules
    rules = await list_routing_rules(api_key_info["id"])
    return {"rules": rules}

@app.delete("/v1/routing-rules/{rule_id}")
async def delete_routing_rule(rule_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.webhooks import delete_routing_rule
    await delete_routing_rule(rule_id)
    return {"status": "deleted"}


# ── Usage Export ──────────────────────────────────────

from fastapi.responses import PlainTextResponse

@app.get("/v1/export/usage")
async def export_usage(format: str = "json", start_date: Optional[str] = None, end_date: Optional[str] = None, api_key_info: dict = Depends(get_api_key)):
    from app.benchmarks import export_usage_data
    data = await export_usage_data(api_key_info["id"], format, start_date, end_date)
    if format == "csv":
        return PlainTextResponse(content=data, media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=usage_export.csv"})
    return data

@app.get("/v1/export/benchmarks")
async def export_benchmarks(model: Optional[str] = None, format: str = "json", days: int = 30):
    from app.benchmarks import export_benchmarks_data
    data = await export_benchmarks_data(model, format, days)
    if format == "csv":
        return PlainTextResponse(content=data, media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=benchmarks_export.csv"})
    return data


# ── A/B Testing Experiments ──────────────────────────────────────

class ExperimentRequest(BaseModel):
    name: str
    model_a: str
    model_b: str
    description: Optional[str] = None
    traffic_split: float = 0.5

class VoteRequest(BaseModel):
    winner: str

@app.post("/v1/experiments")
async def create_experiment(request: ExperimentRequest, api_key_info: dict = Depends(get_api_key)):
    from app.experiments import create_experiment
    exp = await create_experiment(
        api_key_info["id"], request.name, request.model_a, request.model_b,
        request.description, request.traffic_split
    )
    return exp

@app.get("/v1/experiments")
async def list_experiments(api_key_info: dict = Depends(get_api_key)):
    from app.experiments import list_experiments
    exps = await list_experiments(api_key_info["id"])
    return {"experiments": exps}

@app.get("/v1/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    from app.experiments import get_experiment
    exp = await get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

@app.post("/v1/experiments/{experiment_id}/status")
async def update_experiment_status(experiment_id: str, status: str, api_key_info: dict = Depends(get_api_key)):
    from app.experiments import update_experiment_status
    result = await update_experiment_status(experiment_id, status)
    return result

@app.post("/v1/experiments/{experiment_id}/run")
async def run_experiment_trial(experiment_id: str, request: QueryRequest, api_key_info: dict = Depends(get_api_key)):
    from app.experiments import run_trial
    trial = await run_trial(experiment_id, request.query)
    return trial

@app.post("/v1/experiments/trials/{trial_id}/vote")
async def vote_trial(trial_id: int, request: VoteRequest, api_key_info: dict = Depends(get_api_key)):
    from app.experiments import vote_trial
    result = await vote_trial(trial_id, request.winner)
    return result

@app.get("/v1/experiments/{experiment_id}/stats")
async def experiment_stats(experiment_id: str):
    from app.experiments import get_experiment_stats
    stats = await get_experiment_stats(experiment_id)
    return stats

@app.delete("/v1/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str, api_key_info: dict = Depends(get_api_key)):
    from app.experiments import delete_experiment
    await delete_experiment(experiment_id)
    return {"status": "deleted"}


# ── Plugin Marketplace ──────────────────────────────────────

@app.get("/v1/marketplace")
async def marketplace_list():
    from app.modules.plugin_manager import list_plugins
    plugins = list_plugins()
    marketplace = []
    for p in plugins:
        marketplace.append({
            "id": p["id"],
            "name": p["name"],
            "description": p.get("description", ""),
            "version": p.get("version", "1.0.0"),
            "category": p.get("category", "general"),
            "installed": True,
            "capabilities": p.get("capabilities", [])
        })

    marketplace.extend([
        {"id": "nlp-sentiment", "name": "Sentiment Analysis", "description": "Analyze text sentiment and emotion", "version": "1.0.0", "category": "nlp", "installed": False, "capabilities": ["sentiment_analysis", "emotion_detection"]},
        {"id": "data-viz", "name": "Data Visualization", "description": "Generate charts and graphs from data", "version": "1.0.0", "category": "analytics", "installed": False, "capabilities": ["chart_generation", "data_plotting"]},
        {"id": "code-review", "name": "Code Review", "description": "Automated code review and suggestions", "version": "1.0.0", "category": "development", "installed": False, "capabilities": ["code_analysis", "security_scan"]},
        {"id": "translation", "name": "Multi-Language Translation", "description": "Translate text between 100+ languages", "version": "1.0.0", "category": "nlp", "installed": False, "capabilities": ["translation", "language_detection"]},
    ])
    return {"plugins": marketplace, "total": len(marketplace)}


@app.get("/v1/cache/stats")
async def cache_stats():
    from app.modules.nvidia_nim_client import get_cache_stats
    return get_cache_stats()


@app.post("/v1/cache/clear")
async def cache_clear(api_key_info: dict = Depends(get_api_key)):
    if api_key_info.get("id") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.modules.nvidia_nim_client import clear_cache
    clear_cache()
    return {"status": "cache_cleared"}


MAU_TIER_LIMITS = {
    "community": 50,
    "production": 500,
    "enterprise": -1,
}


@app.middleware("http")
async def mau_rate_limit_middleware(request, call_next):
    from starlette.responses import JSONResponse

    if not request.url.path.startswith("/v1/") or request.method == "OPTIONS":
        return await call_next(request)

    skip_paths = ["/v1/billing", "/v1/cache", "/v1/models", "/v1/capabilities", "/v1/stats", "/v1/agents/types"]
    if any(request.url.path.startswith(p) for p in skip_paths):
        return await call_next(request)

    api_key_header = request.headers.get("X-API-Key")
    if api_key_header and api_key_header != os.getenv("API_SECRET_KEY", "default_secret_key_for_development"):
        try:
            from app.billing import validate_api_key, get_pool, TIER_LIMITS
            key_info = await validate_api_key(api_key_header)
            if key_info:
                tier = key_info.get("tier", "community")
                tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["community"])
                monthly_limit = tier_config["queries_per_month"]

                if monthly_limit != -1:
                    pool = await get_pool()
                    month = datetime.now().strftime("%Y-%m")
                    row = await pool.fetchrow(
                        "SELECT query_count FROM monthly_usage WHERE api_key_id = $1 AND month = $2",
                        key_info["id"], month
                    )
                    current = row["query_count"] if row else 0

                    if current >= monthly_limit:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Monthly usage limit reached",
                                "tier": tier,
                                "limit": monthly_limit,
                                "used": current,
                                "upgrade_url": "/billing",
                            },
                        )

                    if current == 900 or (current > 900 and current <= 910 and current % 10 == 0):
                        asyncio.create_task(
                            _trigger_mau_threshold_webhook(key_info["id"], current, monthly_limit)
                        )
        except Exception as e:
            logger.debug(f"MAU rate-limit check skipped: {e}")

    return await call_next(request)


async def _trigger_mau_threshold_webhook(api_key_id: str, current_usage: int, limit: int):
    try:
        from app.webhooks import check_usage_alerts
        await check_usage_alerts(api_key_id, current_usage, limit)
        logger.info(f"MAU threshold webhook triggered at {current_usage}/{limit}")
    except Exception as e:
        logger.debug(f"MAU webhook skipped: {e}")


@app.get("/v1/billing/analytics")
async def billing_analytics(api_key_id: Optional[str] = None):
    try:
        from app.billing import get_pool
        pool = await get_pool()

        daily_usage = []
        try:
            rows = await pool.fetch(
                """SELECT DATE(created_at) as day, COUNT(*) as queries, 
                          SUM(tokens_estimated) as tokens, AVG(latency_ms)::int as avg_latency,
                          SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successes
                   FROM usage_events
                   WHERE created_at >= NOW() - INTERVAL '30 days'
                   """ + ("AND api_key_id = $1" if api_key_id else "") + """
                   GROUP BY DATE(created_at) ORDER BY day""",
                *([api_key_id] if api_key_id else [])
            )
            daily_usage = [{"day": str(r["day"]), "queries": r["queries"], "tokens": r["tokens"] or 0,
                            "avg_latency": r["avg_latency"] or 0, "success_rate": round(r["successes"] / max(r["queries"], 1) * 100, 1)} for r in rows]
        except Exception:
            pass

        model_breakdown = []
        try:
            rows = await pool.fetch(
                """SELECT model_used, COUNT(*) as count, SUM(tokens_estimated) as tokens
                   FROM usage_events
                   WHERE created_at >= NOW() - INTERVAL '30 days' AND model_used != ''
                   """ + ("AND api_key_id = $1" if api_key_id else "") + """
                   GROUP BY model_used ORDER BY count DESC LIMIT 10""",
                *([api_key_id] if api_key_id else [])
            )
            model_breakdown = [{"model": r["model_used"], "count": r["count"], "tokens": r["tokens"] or 0} for r in rows]
        except Exception:
            pass

        endpoint_breakdown = []
        try:
            rows = await pool.fetch(
                """SELECT endpoint, COUNT(*) as count, AVG(latency_ms)::int as avg_latency
                   FROM usage_events
                   WHERE created_at >= NOW() - INTERVAL '30 days'
                   """ + ("AND api_key_id = $1" if api_key_id else "") + """
                   GROUP BY endpoint ORDER BY count DESC""",
                *([api_key_id] if api_key_id else [])
            )
            endpoint_breakdown = [{"endpoint": r["endpoint"], "count": r["count"], "avg_latency": r["avg_latency"] or 0} for r in rows]
        except Exception:
            pass

        tier_distribution = []
        try:
            rows = await pool.fetch(
                """SELECT tier, COUNT(*) as count FROM api_keys WHERE is_active = TRUE GROUP BY tier"""
            )
            tier_distribution = [{"tier": r["tier"], "count": r["count"]} for r in rows]
        except Exception:
            pass

        from app.modules.nvidia_nim_client import get_cache_stats
        cache = get_cache_stats()

        return {
            "daily_usage": daily_usage,
            "model_breakdown": model_breakdown,
            "endpoint_breakdown": endpoint_breakdown,
            "tier_distribution": tier_distribution,
            "cache_stats": cache,
            "period": "30_days",
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {
            "daily_usage": [],
            "model_breakdown": [],
            "endpoint_breakdown": [],
            "tier_distribution": [],
            "cache_stats": {},
            "period": "30_days",
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
