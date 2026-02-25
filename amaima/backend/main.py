"""
AMAIMA Production Backend Server
FastAPI-based REST and WebSocket interface
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
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
import hashlib

from app.core.unified_smart_router import SmartRouter, RoutingDecision
from app.modules.smart_router_engine import route_query
from app.modules.execution_engine import execute_model
from app.security import get_api_key, enforce_tier_limit, get_current_user, require_admin
from app.routers.biology import router as biology_router
from app.routers.robotics import router as robotics_router
from app.routers.vision import router as vision_router
from app.services import video_service
from app.services import audio_service
from app.services import image_service as image_gen_service
from fastapi import Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

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


class AgentCrewRequest(BaseModel):
    task: str = Field(..., description="Task for the agent crew")
    crew_type: str = Field(
        default="research",
        description="Crew type: research, drug_discovery, protein_analysis, navigation, "
                    "manipulation, swarm, neural_audio_synthesis, visual_art_generation, workflow, custom"
    )
    process: str = Field(default="sequential", description="Process: sequential, parallel, hierarchical")
    roles: Optional[List[Dict[str, Any]]] = Field(default=None, description="Custom roles for custom crew type")
    environment: Optional[str] = Field(default=None, description="Environment context for robotics crews")
    robot_type: Optional[str] = Field(default="amr", description="Robot type for robotics crews")


class CreateApiKeyRequest(BaseModel):
    email: Optional[str] = None
    tier: str = Field(default="community", description="Tier: community, production, enterprise")


class UpdateTierRequest(BaseModel):
    api_key_id: str
    tier: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


class ConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    operation_type: Optional[str] = "general"
    model: Optional[str] = None


class MessageRequest(BaseModel):
    content: str
    role: str = "user"


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


class VoteRequest(BaseModel):
    winner: str


# ─────────────────────────────────────────────────────────────────────────────
# App state
# ─────────────────────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — startup and shutdown
# ─────────────────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
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

    # ── NVIDIA NIM key check ──────────────────────────────────────────────────
    from app.modules.nvidia_nim_client import is_configured, get_api_key
    nim_key = get_api_key()
    if nim_key:
        logger.info(
            f"NVIDIA NIM configured: key={nim_key[:8]}...{nim_key[-4:]}, length={len(nim_key)}"
        )
    else:
        logger.warning(
            "NVIDIA NIM NOT configured: no API key found. "
            "Checked: NVIDIA_API_KEY, NVIDIA_NIM_API_KEY, NIM_API_KEY, NGC_API_KEY"
        )

    # ── FHE context pool warm-up ──────────────────────────────────────────────
    # Pre-generates CKKS and BFV contexts once at startup so the first
    # request hits the pool (≈0ms) instead of paying keygen cost (200-600ms).
    try:
        from app.fhe.router import fhe_startup
        await fhe_startup()
        logger.info("FHE context pool warmed up successfully")
    except Exception as e:
        logger.warning(f"FHE pool warm-up skipped (FHE may be unavailable): {e}")

    from app.db_config import get_database_url
    db_url = get_database_url()
    logger.info(f"Database configured: {bool(db_url)}")
    logger.info("AMAIMA API server started — execution mode: production, simulation: disabled")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("AMAIMA API server shutting down")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AMAIMA API",
    description="Advanced Multimodal AI Model Architecture — Production API (no simulation mode)",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.fhe.router import router as fhe_router

app.include_router(biology_router)
app.include_router(robotics_router)
app.include_router(vision_router)
app.include_router(fhe_router)


# ─────────────────────────────────────────────────────────────────────────────
# Health + Stats
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    components = {
        "router": {
            "status": "healthy" if app_state.smart_router else "unavailable",
            "type": "smart_router",
        },
        "api": {
            "status": "healthy",
            "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
            "query_count": app_state.query_count,
        },
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
        timestamp=datetime.now(),
    )


@app.get("/v1/stats")
async def get_stats():
    return {
        "total_queries": app_state.query_count,
        "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
        "active_connections": len(app_state.active_connections),
        "version": "5.0.0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core query endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/query", response_model=ExecuteResponse)
async def process_query(request: QueryRequest, api_key_info: dict = Depends(get_api_key)):
    try:
        await enforce_tier_limit(api_key_info)
        start_time_ms = datetime.now()

        if not app_state.smart_router:
            app_state.smart_router = SmartRouter(darpa_enabled=False)

        routing_decision = app_state.smart_router.route(request.query, operation=request.operation)
        detected_domain = routing_decision.reasoning.get("detected_domain", "general")

        # ── Specialized domain dispatch ───────────────────────────────────────
        if detected_domain == "audio":
            if "transcribe" in request.query.lower() or "speech to text" in request.query.lower():
                # ASR path — in production, caller should POST audio bytes to /v1/audio/transcribe
                raise HTTPException(
                    status_code=400,
                    detail="ASR requires audio input. POST audio bytes to /v1/audio/transcribe instead."
                )
            else:
                execution_result = await audio_service.text_to_speech(request.query)
            # Return the base64 data URI; frontend renders it as <audio>
            output = execution_result.get("audio_data", "")

        elif detected_domain == "image_gen":
            execution_result = await image_gen_service.generate_image(request.query)
            # Return the base64 data URI; frontend renders it as <img>
            output = execution_result.get("image_data", "")

        else:
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
            output = execution_result.get("output", "")

        response = {
            "query_hash": hashlib.md5(request.query.encode()).hexdigest(),
            "complexity_level": routing_decision.complexity.name,
            "model": routing_decision.model_size.name,
            "execution_mode": routing_decision.execution_mode.value,
            "confidence": {"overall": routing_decision.confidence},
            "reasons": {"routing": [str(routing_decision.reasoning)]},
            "simulated": False,
            "output": output,
            "actual_latency_ms": int((datetime.now() - start_time_ms).total_seconds() * 1000),
            "actual_cost_usd": routing_decision.estimated_cost,
        }

        app_state.query_count += 1
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

    if not is_configured():
        raise HTTPException(
            status_code=503,
            detail="NVIDIA NIM API key not configured. Set NVIDIA_API_KEY to enable streaming."
        )

    decision = route_query(request.query, simulate=False)
    model_used = decision.get("model", "unknown")

    router_model = decision.get("model", "")
    nim_model = (
        router_model if router_model in NVIDIA_MODELS
        else get_model_for_complexity(decision.get("complexity_level", "SIMPLE"))
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are AMAIMA, an Advanced Multimodal AI assistant powered by NVIDIA NIM. "
                "Provide clear, accurate, and helpful responses."
            ),
        },
        {"role": "user", "content": request.query},
    ]

    async def event_generator():
        start_time = datetime.now()
        yield {
            "event": "start",
            "data": json.dumps({"model": nim_model, "complexity": decision.get("complexity_level", "SIMPLE")}),
        }
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


# ─────────────────────────────────────────────────────────────────────────────
# Audio endpoints — real Riva ASR + TTS
# ─────────────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: str = Field(default="English-US.Female-1", description="TTS voice identifier")


class ASRRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded PCM audio bytes")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")


@app.post("/v1/audio/synthesize")
async def synthesize_speech(request: TTSRequest, api_key_info: dict = Depends(get_api_key)):
    """
    Text-to-speech via NVIDIA Riva (Magpie TTS Multilingual).
    Returns a base64 data URI (data:audio/wav;base64,...) for inline playback.
    """
    try:
        result = await audio_service.text_to_speech(request.text, voice=request.voice)
        return result
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/audio/transcribe")
async def transcribe_speech(request: ASRRequest, api_key_info: dict = Depends(get_api_key)):
    """
    Automatic speech recognition via NVIDIA Parakeet CTC 1.1B.
    Accepts base64-encoded PCM audio, returns transcript text.
    """
    import base64
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        result = await audio_service.speech_to_text(audio_bytes, sample_rate=request.sample_rate)
        return result
    except Exception as e:
        logger.error(f"ASR failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Image generation endpoint — real SDXL-Turbo
# ─────────────────────────────────────────────────────────────────────────────

class ImageGenRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: str = Field(default="", description="Negative prompt")
    steps: int = Field(default=2, description="Diffusion steps (2-4 for SDXL-Turbo)")


@app.post("/v1/image/generate")
async def generate_image_endpoint(request: ImageGenRequest, api_key_info: dict = Depends(get_api_key)):
    """
    Text-to-image generation via NVIDIA NIM SDXL-Turbo.
    Returns a base64 data URI (data:image/png;base64,...) for inline rendering.
    """
    try:
        result = await image_gen_service.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            steps=request.steps,
        )
        return result
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Agent crews — unified dispatcher via run_crew()
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/agents/run")
async def run_agent_crew(request: AgentCrewRequest):
    """
    Dispatches to the appropriate crew via the unified run_crew() dispatcher.
    Supports all 8 crew types including Neural Audio Synthesis and Visual Art Generation.
    """
    try:
        crew_type = request.crew_type.lower()

        # ── Biology crews ─────────────────────────────────────────────────────
        if crew_type == "drug_discovery":
            from app.agents.biology_crew import run_drug_discovery_crew
            return await run_drug_discovery_crew(request.task)

        elif crew_type == "protein_analysis":
            from app.agents.biology_crew import run_protein_analysis_crew
            return await run_protein_analysis_crew(request.task)

        # ── Robotics crews ────────────────────────────────────────────────────
        elif crew_type == "navigation":
            from app.agents.robotics_crew import run_navigation_crew
            return await run_navigation_crew(
                request.task,
                request.environment or "indoor",
                request.robot_type or "amr",
            )

        elif crew_type == "manipulation":
            from app.agents.robotics_crew import run_manipulation_crew
            return await run_manipulation_crew(request.task)

        elif crew_type == "swarm":
            from app.agents.robotics_crew import run_swarm_crew
            return await run_swarm_crew(request.task, environment=request.environment or "warehouse")

        # ── Stateful workflow crew ────────────────────────────────────────────
        elif crew_type == "workflow":
            from app.agents.langchain_agent import run_langchain_agent
            workflow_type = request.environment or "research"
            return await run_langchain_agent(request.task, workflow_type=workflow_type)

        # ── All remaining crew types go through run_crew() ────────────────────
        # Covers: research, neural_audio_synthesis, audio, visual_art_generation,
        #         image_gen, and custom — with audio/image dispatching to real services
        else:
            from app.agents.crew_manager import run_crew
            return await run_crew(
                task=request.task,
                crew_type=crew_type,
                process=request.process,
                roles=request.roles,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent crew execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/agents/types")
async def list_agent_types():
    return {
        "crew_types": [
            {"id": "research",               "name": "Research Crew",                 "description": "Researcher, Analyst, Synthesizer for general research tasks"},
            {"id": "drug_discovery",         "name": "Drug Discovery Crew",           "description": "Molecule Generator, ADMET Predictor, Lead Optimizer, Safety Reviewer"},
            {"id": "protein_analysis",       "name": "Protein Analysis Crew",         "description": "Structural Biologist, Binding Site Predictor"},
            {"id": "navigation",             "name": "Navigation Crew",               "description": "Perception, Path Planner, Action Executor, Safety Monitor"},
            {"id": "manipulation",           "name": "Manipulation Crew",             "description": "Perception, Grasp Planner, Action Executor, Safety Monitor"},
            {"id": "swarm",                  "name": "Swarm Coordination Crew",       "description": "Coordinator, Perception, Path Planner, Safety Monitor"},
            {"id": "neural_audio_synthesis", "name": "Neural Audio Synthesis Crew",   "description": "Audio Engineer + Tone Analyst → NVIDIA Riva TTS dispatch"},
            {"id": "visual_art_generation",  "name": "Visual Art Generation Crew",    "description": "Creative Director + Aesthetic Validator → SDXL-Turbo dispatch"},
            {"id": "workflow",               "name": "Stateful Workflow",             "description": "Multi-step stateful workflows (research, complex_reasoning, biology, robotics, vision)"},
            {"id": "custom",                 "name": "Custom Crew",                   "description": "Build your own crew with custom roles"},
        ],
        "processes": ["sequential", "parallel", "hierarchical"],
        "workflow_types": ["research", "complex_reasoning", "biology", "robotics", "vision"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Models + capabilities
# ─────────────────────────────────────────────────────────────────────────────

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
    models_info = [
        {
            "id": model_id,
            "name": info["name"],
            "params": info["parameters"],
            "context_window": info["context_window"],
            "cost_per_1k_tokens": info["cost_per_1k_tokens"],
        }
        for model_id, info in NVIDIA_MODELS.items()
    ]
    return {
        "models": models_info,
        "nvidia_nim_configured": is_configured(),
        "execution_modes": ["batch_parallel", "parallel_min_latency", "streaming"],
        "security_levels": ["standard", "fhe_encrypted"],
        "complexity_levels": ["TRIVIAL", "SIMPLE", "MODERATE", "COMPLEX", "EXPERT"],
        "max_context": 128000,
        "simulation_mode": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Embeddings
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/embeddings")
async def generate_embeddings_endpoint(
    texts: list[str] = Body(..., description="List of texts to embed"),
    model: str = Body(default="nvidia/nv-embedqa-e5-v5", description="Embedding model"),
    input_type: str = Body(default="query", description="Input type: query or passage"),
    api_key_info: dict = Depends(get_api_key),
):
    from app.modules.nvidia_nim_client import generate_embeddings
    try:
        result = await generate_embeddings(texts=texts, model=model, input_type=input_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Biology molecule generation
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/biology/generate-molecules")
async def generate_molecules_endpoint(
    smiles: str = Body(..., description="Input SMILES or SAFE format molecule string"),
    num_molecules: int = Body(default=5, description="Number of molecules to generate"),
    temperature: float = Body(default=2.0, description="Sampling temperature"),
    noise: float = Body(default=1.0, description="Noise level for generation"),
    step_size: int = Body(default=1, description="Diffusion step size"),
    scoring: str = Body(default="QED", description="Scoring function: QED or plogP"),
    api_key_info: dict = Depends(get_api_key),
):
    from app.modules.nvidia_nim_client import generate_molecules
    try:
        result = await generate_molecules(
            smiles=smiles,
            num_molecules=num_molecules,
            temperature=temperature,
            noise=noise,
            step_size=step_size,
            scoring=scoring,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Workflow
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/workflow", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    try:
        start_time = datetime.now()
        results = []
        completed = set()
        max_iterations = len(request.steps) * 2
        iteration = 0

        while len(completed) < len(request.steps) and iteration < max_iterations:
            iteration += 1
            for step in request.steps:
                if step.step_id in completed:
                    continue
                if step.dependencies and not all(dep in completed for dep in step.dependencies):
                    continue
                results.append({
                    "step_id": step.step_id,
                    "step_type": step.step_type,
                    "status": "completed",
                    "output": f"Processed {step.step_type} with params: {step.parameters}",
                })
                completed.add(step.step_id)

        return WorkflowResponse(
            workflow_id=request.workflow_id,
            status="completed" if len(completed) == len(request.steps) else "partial",
            results=results,
            total_steps=len(request.steps),
            completed_steps=len(completed),
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/auth/register")
async def register(request: RegisterRequest):
    from app.auth import register_user
    try:
        return await register_user(request.email, request.password, request.display_name)
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


@app.get("/v1/auth/api-keys")
@app.post("/v1/auth/api-keys")
async def manage_user_api_keys(user: dict = Depends(get_current_user)):
    from app.billing import create_api_key
    from app.auth import link_api_key_to_user
    result = await create_api_key(email=user["email"], tier="community")
    await link_api_key_to_user(result["id"], user["id"])
    return result


@app.post("/v1/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    from app.auth import request_password_reset
    reset_token = await request_password_reset(request.email)
    base_msg = "If an account with that email exists, a password reset link has been generated."
    if not reset_token:
        return {"message": base_msg}
    return {
        "message": base_msg,
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
    return {"message": "Password has been reset successfully."}


# ─────────────────────────────────────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/admin/analytics")
async def admin_analytics(admin: dict = Depends(require_admin)):
    from app.admin import get_admin_analytics
    return await get_admin_analytics()


@app.get("/v1/admin/health")
async def admin_health(admin: dict = Depends(require_admin)):
    from app.admin import get_system_health
    return await get_system_health()


@app.get("/v1/admin/users")
async def admin_users(limit: int = 50, offset: int = 0, admin: dict = Depends(require_admin)):
    from app.admin import get_all_users_with_usage
    users = await get_all_users_with_usage(limit=limit, offset=offset)
    return {"users": users, "limit": limit, "offset": offset}


# ─────────────────────────────────────────────────────────────────────────────
# Billing
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/billing/api-keys")
async def create_api_key_endpoint(request: CreateApiKeyRequest):
    from app.billing import create_api_key
    return await create_api_key(email=request.email, tier="community")


@app.get("/v1/billing/api-keys")
async def list_api_keys_endpoint(email: Optional[str] = None):
    from app.billing import list_api_keys
    keys = await list_api_keys(email=email)
    return {"api_keys": keys}


@app.get("/v1/billing/usage/{api_key_id}")
async def get_usage_endpoint(api_key_id: str):
    from app.billing import get_usage_stats
    return await get_usage_stats(api_key_id)


@app.get("/v1/billing/usage-by-key")
async def get_usage_by_key(api_key_info: dict = Depends(get_api_key)):
    from app.billing import get_usage_stats
    return await get_usage_stats(api_key_info["id"])


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


@app.get("/v1/billing/analytics")
async def billing_analytics(api_key_id: Optional[str] = None):
    try:
        from app.billing import get_pool
        pool = await get_pool()

        async def safe_fetch(query, *args):
            try:
                return await pool.fetch(query, *args)
            except Exception:
                return []

        key_filter = "AND api_key_id = $1" if api_key_id else ""
        args = [api_key_id] if api_key_id else []

        daily_rows = await safe_fetch(
            f"""SELECT DATE(created_at) as day, COUNT(*) as queries,
                       SUM(tokens_estimated) as tokens, AVG(latency_ms)::int as avg_latency,
                       SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successes
                FROM usage_events
                WHERE created_at >= NOW() - INTERVAL '30 days' {key_filter}
                GROUP BY DATE(created_at) ORDER BY day""",
            *args,
        )
        model_rows = await safe_fetch(
            f"""SELECT model_used, COUNT(*) as count, SUM(tokens_estimated) as tokens
                FROM usage_events
                WHERE created_at >= NOW() - INTERVAL '30 days' AND model_used != '' {key_filter}
                GROUP BY model_used ORDER BY count DESC LIMIT 10""",
            *args,
        )
        endpoint_rows = await safe_fetch(
            f"""SELECT endpoint, COUNT(*) as count, AVG(latency_ms)::int as avg_latency
                FROM usage_events
                WHERE created_at >= NOW() - INTERVAL '30 days' {key_filter}
                GROUP BY endpoint ORDER BY count DESC""",
            *args,
        )
        tier_rows = await safe_fetch(
            "SELECT tier, COUNT(*) as count FROM api_keys WHERE is_active = TRUE GROUP BY tier"
        )

        from app.modules.nvidia_nim_client import get_cache_stats
        cache = get_cache_stats()

        return {
            "daily_usage": [
                {
                    "day": str(r["day"]),
                    "queries": r["queries"],
                    "tokens": r["tokens"] or 0,
                    "avg_latency": r["avg_latency"] or 0,
                    "success_rate": round(r["successes"] / max(r["queries"], 1) * 100, 1),
                }
                for r in daily_rows
            ],
            "model_breakdown": [
                {"model": r["model_used"], "count": r["count"], "tokens": r["tokens"] or 0}
                for r in model_rows
            ],
            "endpoint_breakdown": [
                {"endpoint": r["endpoint"], "count": r["count"], "avg_latency": r["avg_latency"] or 0}
                for r in endpoint_rows
            ],
            "tier_distribution": [
                {"tier": r["tier"], "count": r["count"]} for r in tier_rows
            ],
            "cache_stats": cache,
            "period": "30_days",
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {"daily_usage": [], "model_breakdown": [], "endpoint_breakdown": [],
                "tier_distribution": [], "cache_stats": {}, "period": "30_days"}


# ─────────────────────────────────────────────────────────────────────────────
# Conversations
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/conversations")
async def create_conversation_endpoint(request: ConversationRequest, api_key_info: dict = Depends(get_api_key)):
    from app.conversations import create_conversation
    return await create_conversation(
        api_key_id=api_key_info["id"],
        title=request.title or "New Conversation",
        operation_type=request.operation_type or "general",
        model=request.model or "unknown",
    )


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

    await add_message(conversation_id=conversation_id, role="user", content=request.content, model="user")

    decision = route_query(request.content, simulate=False)
    result = await execute_model(decision)

    model_used = decision.get("model", "unknown")
    latency = result.get("actual_latency_ms", 0)
    tokens = len(result.get("output", "")) // 4

    try:
        from app.benchmarks import record_benchmark
        await record_benchmark(
            model=model_used,
            query_complexity=decision.get("complexity_level", "SIMPLE"),
            domain=decision.get("domain", "general"),
            latency_ms=latency,
            tokens_input=len(request.content) // 4,
            tokens_output=tokens,
            cost_usd=result.get("actual_cost_usd", 0),
            success=True,
        )
    except Exception:
        pass

    assistant_msg = await add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.get("output", ""),
        model=model_used,
    )
    return assistant_msg


# ─────────────────────────────────────────────────────────────────────────────
# Feedback
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/v1/feedback")
async def submit_feedback(request: FeedbackRequest):
    logger.info(f"Feedback received: {request.feedback_type} for {request.response_id}")
    return {
        "status": "recorded",
        "response_id": request.response_id,
        "feedback_type": request.feedback_type,
        "timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Plugins + Marketplace
# ─────────────────────────────────────────────────────────────────────────────

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
    raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")


@app.get("/v1/marketplace")
async def marketplace_list():
    from app.modules.plugin_manager import list_plugins
    plugins = list_plugins()
    marketplace = [
        {
            "id": p["id"], "name": p["name"], "description": p.get("description", ""),
            "version": p.get("version", "1.0.0"), "category": p.get("category", "general"),
            "installed": True, "capabilities": p.get("capabilities", []),
        }
        for p in plugins
    ]
    marketplace.extend([
        {"id": "nlp-sentiment",  "name": "Sentiment Analysis",         "description": "Analyze text sentiment and emotion",              "version": "1.0.0", "category": "nlp",         "installed": False, "capabilities": ["sentiment_analysis", "emotion_detection"]},
        {"id": "data-viz",       "name": "Data Visualization",          "description": "Generate charts and graphs from data",            "version": "1.0.0", "category": "analytics",   "installed": False, "capabilities": ["chart_generation", "data_plotting"]},
        {"id": "code-review",    "name": "Code Review",                 "description": "Automated code review and suggestions",           "version": "1.0.0", "category": "development", "installed": False, "capabilities": ["code_analysis", "security_scan"]},
        {"id": "translation",    "name": "Multi-Language Translation",  "description": "Translate text between 100+ languages",           "version": "1.0.0", "category": "nlp",         "installed": False, "capabilities": ["translation", "language_detection"]},
    ])
    return {"plugins": marketplace, "total": len(marketplace)}


# ─────────────────────────────────────────────────────────────────────────────
# MAU rate-limit middleware
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def mau_rate_limit_middleware(request, call_next):
    from starlette.responses import JSONResponse

    if not request.url.path.startswith("/v1/") or request.method == "OPTIONS":
        return await call_next(request)

    skip_paths = ["/v1/billing", "/v1/cache", "/v1/models", "/v1/capabilities",
                  "/v1/stats", "/v1/agents/types"]
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
                        key_info["id"], month,
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

                    if current == 900 or (900 < current <= 910 and current % 10 == 0):
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


# ─────────────────────────────────────────────────────────────────────────────
# WebSockets
# ─────────────────────────────────────────────────────────────────────────────

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
                await websocket.send_text(json.dumps({"error": "Smart router not initialized"}))
                continue

            routing_decision = app_state.smart_router.route(query, operation)
            await websocket.send_text(json.dumps({
                "response_id": str(uuid.uuid4()),
                "query": query,
                "routing": {
                    "mode": routing_decision.execution_mode.value,
                    "model": routing_decision.model_size.name,
                    "complexity": routing_decision.complexity.name,
                    "confidence": routing_decision.confidence,
                },
                "response_text": f"Processed: {query[:50]}...",
            }))
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        app_state.active_connections.pop(connection_id, None)


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
                    "queriesPerMinute": app_state.query_count / max(
                        1, (datetime.now() - app_state.start_time).total_seconds() / 60
                    ),
                },
                "timestamp": datetime.now().isoformat(),
            }
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("System status WebSocket disconnected")


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
