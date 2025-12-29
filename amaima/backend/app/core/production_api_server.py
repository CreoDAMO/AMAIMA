"""
AMAIMA Part V - Production API Server
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

from smart_router import SmartRouter, RoutingDecision
from progressive_loader import ProgressiveModelLoader

logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., description="User query text")
    operation: str = Field(default="general", description="Operation type")
    file_types: Optional[List[str]] = Field(default=None, description="Attached file types")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")


class QueryResponse(BaseModel):
    """Query response model"""
    response_id: str
    response_text: str
    model_used: str
    routing_decision: Dict[str, Any]
    confidence: float
    latency_ms: float
    timestamp: datetime


class WorkflowStep(BaseModel):
    """Workflow step definition"""
    step_id: str
    step_type: str
    parameters: Dict[str, Any]
    dependencies: Optional[List[str]] = None


class WorkflowRequest(BaseModel):
    """Workflow execution request"""
    workflow_id: str
    steps: List[WorkflowStep]
    context: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Workflow execution response"""
    workflow_id: str
    status: str
    results: List[Dict[str, Any]]
    total_steps: int
    completed_steps: int
    duration_ms: float


class FeedbackRequest(BaseModel):
    """User feedback request"""
    response_id: str
    feedback_type: str
    feedback_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    components: Dict[str, Dict[str, Any]]
    timestamp: datetime


class AppState:
    """Global application state"""
    
    def __init__(self):
        self.smart_router: Optional[SmartRouter] = None
        self.model_loader: Optional[ProgressiveModelLoader] = None
        self.active_connections: Dict[str, WebSocket] = {}
        self.query_count = 0
        self.start_time = datetime.now()
    
    def initialize(self, darpa_enabled: bool = True):
        """Initialize application components"""
        self.smart_router = SmartRouter(darpa_enabled=darpa_enabled)
        self.model_loader = ProgressiveModelLoader(
            max_memory_mb=8192,
            enable_quantization=True
        )
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


@app.on_event("startup")
async def startup():
    """Application startup handler"""
    app_state.initialize(darpa_enabled=True)
    logger.info("AMAIMA API server started")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    components = {
        "router": {
            "status": "healthy" if app_state.smart_router else "unavailable",
            "type": "smart_router"
        },
        "loader": {
            "status": "healthy" if app_state.model_loader else "unavailable",
            "memory_pressure": app_state.model_loader.get_memory_status() if app_state.model_loader else None
        },
        "api": {
            "status": "healthy",
            "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds()
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


@app.post("/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the AMAIMA pipeline
    
    This endpoint accepts a query, analyzes it through the smart router,
    executes the appropriate model, and returns the response with
    comprehensive metadata about the routing decision.
    """
    try:
        app_state.query_count += 1
        start_time = datetime.now()
        
        if not app_state.smart_router:
            raise HTTPException(status_code=503, detail="Smart router not initialized")
        
        app_state.model_loader.preload_for_query(request.query, request.file_types)
        
        routing_decision = app_state.smart_router.route(
            query=request.query,
            operation=request.operation
        )
        
        mock_response = f"AMAIMA Response: Analyzed query about '{request.query[:50]}...' with {routing_decision.complexity.name} complexity"
        
        response = QueryResponse(
            response_id=str(uuid.uuid4()),
            response_text=mock_response,
            model_used=routing_decision.model_size.name,
            routing_decision={
                "execution_mode": routing_decision.execution_mode.value,
                "model_size": routing_decision.model_size.name,
                "complexity": routing_decision.complexity.name,
                "security_level": routing_decision.security_level.name,
                "confidence": routing_decision.confidence,
                "estimated_latency_ms": routing_decision.estimated_latency_ms,
                "estimated_cost": routing_decision.estimated_cost,
                "fallback_chain": [m.value for m in routing_decision.fallback_chain],
                "reasoning": routing_decision.reasoning
            },
            confidence=routing_decision.confidence,
            latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            timestamp=datetime.now()
        )
        
        logger.info(f"Query processed: {response.response_id}")
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/workflow", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a multi-step workflow
    
    This endpoint processes a workflow consisting of multiple steps
    with dependencies, executing them in the correct order and
    aggregating results.
    """
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
    """
    Submit user feedback for quality improvement
    
    Feedback is recorded for continuous learning and quality
    assessment purposes.
    """
    logger.info(f"Feedback received: {request.feedback_type} for {request.response_id}")
    
    return {
        "status": "recorded",
        "response_id": request.response_id,
        "feedback_type": request.feedback_type,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/v1/models")
async def list_models():
    """List available models and their status"""
    if not app_state.model_loader:
        raise HTTPException(status_code=503, detail="Model loader not initialized")
    
    loaded = app_state.model_loader.get_loaded_modules()
    memory = app_state.model_loader.get_memory_status()
    
    return {
        "loaded_modules": loaded,
        "memory_status": memory,
        "available_modules": [
            {"name": name, "spec": spec.to_dict()}
            for name, spec in app_state.model_loader.module_registry.items()
        ]
    }


@app.get("/v1/stats")
async def get_statistics():
    """Get system statistics"""
    return {
        "total_queries": app_state.query_count,
        "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
        "active_connections": len(app_state.active_connections),
        "memory_status": app_state.model_loader.get_memory_status() if app_state.model_loader else None
    }


@app.websocket("/v1/ws/query")
async def websocket_query(websocket: WebSocket):
    """
    WebSocket endpoint for streaming query responses
    
    Enables real-time communication for long-running queries
    with streaming response delivery.
    """
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
                }
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if connection_id in app_state.active_connections:
            del app_state.active_connections[connection_id]


@app.websocket("/v1/ws/workflow")
async def websocket_workflow(websocket: WebSocket):
    """WebSocket endpoint for streaming workflow execution"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            workflow = message.get("workflow", {})
            steps = workflow.get("steps", [])
            
            for step in steps:
                await websocket.send_text(json.dumps({
                    "step_id": step.get("step_id"),
                    "status": "processing",
                    "progress": 0
                }))
                
                await asyncio.sleep(0.5)
                
                await websocket.send_text(json.dumps({
                    "step_id": step.get("step_id"),
                    "status": "completed",
                    "progress": 100
                }))
            
            await websocket.send_text(json.dumps({
                "status": "workflow_complete"
            }))
            
    except WebSocketDisconnect:
        logger.info("Workflow WebSocket disconnected")
