from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/robotics", tags=["robotics"])


class NavigateRequest(BaseModel):
    command: str = Field(..., description="Navigation command (e.g., 'move forward 2 meters')")
    target_position: Optional[Dict[str, float]] = Field(default=None, description="Target x,y,z coordinates")


class PlanRequest(BaseModel):
    query: str = Field(..., description="Task description for the robot")
    environment: Optional[str] = Field(default=None, description="Environment context")
    robot_type: str = Field(default="amr", description="Robot type: amr, arm, manipulator, humanoid, drone")


class SimulateRequest(BaseModel):
    action: str = Field(..., description="Action to simulate")
    environment: str = Field(default="indoor", description="Simulation environment")


class VisionActionRequest(BaseModel):
    scene_description: str = Field(..., description="Description of the scene")
    task: str = Field(..., description="Task to accomplish")
    robot_type: str = Field(default="amr", description="Robot type")


@router.post("/navigate")
async def navigate_robot(request: NavigateRequest):
    from app.services.robotics_service import navigate
    try:
        result = await navigate(request.command, request.target_position)
        return result
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def plan_action(request: PlanRequest):
    from app.services.robotics_service import plan_robot_action
    try:
        result = await plan_robot_action(request.query, request.environment, request.robot_type)
        return result
    except Exception as e:
        logger.error(f"Action planning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    from app.services.robotics_service import simulate_action
    try:
        result = await simulate_action(request.action, request.environment)
        return result
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vision-action")
async def vision_guided(request: VisionActionRequest):
    from app.services.robotics_service import vision_guided_action
    try:
        result = await vision_guided_action(request.scene_description, request.task, request.robot_type)
        return result
    except Exception as e:
        logger.error(f"Vision-guided action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def robotics_capabilities():
    from app.services.robotics_service import ROBOTICS_CAPABILITIES
    return ROBOTICS_CAPABILITIES
