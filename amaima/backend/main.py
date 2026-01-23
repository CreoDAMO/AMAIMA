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


@app.on_event("startup")
async def startup():
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


@app.post("/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        app_state.query_count += 1
        start_time = datetime.now()
        
        if not app_state.smart_router:
            raise HTTPException(status_code=503, detail="Smart router not initialized")
        
        routing_decision = app_state.smart_router.route(
            query=request.query,
            operation=request.operation
        )
        
        response_text = f"AMAIMA Response: Analyzed query about '{request.query[:100]}{'...' if len(request.query) > 100 else ''}' with {routing_decision.complexity.name} complexity using {routing_decision.model_size.name} model."
        
        response = QueryResponse(
            response_id=str(uuid.uuid4()),
            response_text=response_text,
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
    return {
        "available_models": [
            {"name": "NANO_1B", "parameters": "1B", "status": "available"},
            {"name": "SMALL_3B", "parameters": "3B", "status": "available"},
            {"name": "MEDIUM_7B", "parameters": "7B", "status": "available"},
            {"name": "LARGE_13B", "parameters": "13B", "status": "available"},
            {"name": "XL_34B", "parameters": "34B", "status": "available"},
        ],
        "default_model": "MEDIUM_7B"
    }


@app.get("/v1/stats")
async def get_statistics():
    return {
        "total_queries": app_state.query_count,
        "uptime_seconds": (datetime.now() - app_state.start_time).total_seconds(),
        "active_connections": len(app_state.active_connections),
        "version": "5.0.0"
    }


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
