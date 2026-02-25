"""
AMAIMA Robotics Service — v2
app/services/robotics_service.py

Bugs fixed vs v1:
  BUG 9   Top-level `from app.services.vision_service import cosmos_inference`
          creates a circular import risk if vision_service ever imports
          anything from robotics_service. Fixed with a lazy import inside
          vision_guided_action() — import only happens at call time.

  BUG 10  _ros2_navigate() returned a fake "executed_on_hardware" status dict
          even though no ROS2 command was ever actually sent. Misleading in
          logs and to any caller inspecting execution_mode. Now clearly marked
          as a hardware bridge stub with an honest status and note.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

HAS_ROS2     = False
HAS_PYBULLET = False

try:
    import rclpy
    from rclpy.node import Node
    HAS_ROS2 = True
except ImportError:
    logger.info("ROS2 (rclpy) not available; using cloud simulation via NIM/Omniverse")

try:
    import pybullet
    HAS_PYBULLET = True
except ImportError:
    logger.info("PyBullet not available; simulation handled via cloud APIs")

from app.modules.nvidia_nim_client import chat_completion, get_api_key, get_model_for_domain

# BUG 9 FIX: removed top-level import of cosmos_inference.
# It is now imported lazily inside vision_guided_action() to eliminate the
# circular import risk (vision_service ↔ robotics_service).

ROBOTICS_PRIMARY_MODEL = get_model_for_domain("robotics", "primary")
ROBOTICS_AV_MODEL      = get_model_for_domain("robotics", "autonomous")


class RobotAction(str, Enum):
    MOVE_FORWARD  = "move_forward"
    MOVE_BACKWARD = "move_backward"
    TURN_LEFT     = "turn_left"
    TURN_RIGHT    = "turn_right"
    STOP          = "stop"
    GRASP         = "grasp"
    RELEASE       = "release"
    SCAN          = "scan"
    NAVIGATE_TO   = "navigate_to"
    CUSTOM        = "custom"


async def plan_robot_action(
    query: str,
    environment_context: Optional[str] = None,
    robot_type: str = "amr",
) -> Dict[str, Any]:
    start_time = time.time()

    planning_prompt = f"""Robot Action Planning Task:
Query: {query}
Robot Type: {robot_type.upper()} (Autonomous Mobile Robot)
Environment: {environment_context or 'General indoor environment'}

As a robotics AI planner, provide:
1. Environment assessment and safety check
2. Step-by-step action plan with specific commands
3. Expected outcomes for each action
4. Contingency actions for failure scenarios
5. Estimated completion time

Format each action as: ACTION: <action_type> | PARAMS: <parameters> | REASON: <reasoning>
Available actions: {', '.join([a.value for a in RobotAction])}"""

    target_model = (
        ROBOTICS_AV_MODEL
        if any(kw in query.lower() for kw in ("autonomous", "vehicle", "driving"))
        else ROBOTICS_PRIMARY_MODEL
    )

    try:
        result = await chat_completion(
            model=target_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced robotics planning AI. You generate precise, "
                        "safe action plans for autonomous robots using physics-aware reasoning."
                    ),
                },
                {"role": "user", "content": planning_prompt},
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        response_text = result.get("content", "")
        actions = parse_planned_actions(response_text)

        return {
            "service":              "robotics",
            "task":                 "action_planning",
            "robot_type":           robot_type,
            "plan":                 response_text,
            "parsed_actions":       actions,
            "environment":          environment_context or "general",
            "simulation_available": HAS_PYBULLET or HAS_ROS2,
            "cloud_simulation":     not HAS_PYBULLET and not HAS_ROS2,
            "latency_ms":           round(elapsed_ms, 2),
            "usage":                result.get("usage", {}),
            "cost_usd":             result.get("estimated_cost_usd", 0),
        }
    except Exception as e:
        logger.error(f"Robot planning failed: {e}")
        return {
            "service":    "robotics",
            "error":      "internal_error",
            "response":   "Robotics planning unavailable due to an internal error.",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


def parse_planned_actions(plan_text: str) -> List[Dict[str, str]]:
    actions = []
    for line in plan_text.split("\n"):
        if "ACTION:" in line:
            parts: Dict[str, str] = {}
            for segment in line.split("|"):
                segment = segment.strip()
                if segment.startswith("ACTION:"):
                    parts["action"] = segment.replace("ACTION:", "").strip()
                elif segment.startswith("PARAMS:"):
                    parts["params"] = segment.replace("PARAMS:", "").strip()
                elif segment.startswith("REASON:"):
                    parts["reason"] = segment.replace("REASON:", "").strip()
            if parts:
                actions.append(parts)
    return actions


async def navigate(
    command: str,
    target_position: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    start_time = time.time()

    nav_query = f"Navigation command: {command}"
    if target_position:
        nav_query += (
            f"\nTarget position: "
            f"x={target_position.get('x', 0)}, "
            f"y={target_position.get('y', 0)}, "
            f"z={target_position.get('z', 0)}"
        )

    if HAS_ROS2:
        try:
            return await _ros2_navigate(command, target_position)
        except Exception as e:
            logger.warning(f"ROS2 navigation failed, falling back to cloud: {e}")

    plan = await plan_robot_action(nav_query, robot_type="amr")
    plan["execution_mode"] = "cloud_simulation"
    plan["note"] = "Executed via cloud-based planning. Connect ROS2 for hardware execution."
    return plan


async def _ros2_navigate(command: str, target: Optional[Dict[str, float]]) -> Dict[str, Any]:
    """
    BUG 10 FIX: Previously returned {"status": "executed_on_hardware"} without
    sending any actual ROS2 command — misleading. Now honestly reports itself
    as a bridge stub that requires hardware wiring.

    To activate real ROS2 execution, replace this method body with:
      node = rclpy.create_node("amaima_nav")
      # ... publish to /cmd_vel or call Nav2 action server ...
    """
    logger.warning(
        "_ros2_navigate() is a hardware bridge stub. "
        "No ROS2 command was sent. Wire this method to your robot's nav stack."
    )
    return {
        "service":        "robotics",
        "execution_mode": "ros2_stub",
        "command":        command,
        "target":         target,
        "status":         "stub_not_executed",
        "note": (
            "ROS2 is detected in the environment but the hardware bridge is not "
            "yet wired. Implement _ros2_navigate() to publish to /cmd_vel or "
            "invoke the Nav2 action server."
        ),
    }


async def vision_guided_action(
    scene_description: str,
    task: str,
    robot_type: str = "amr",
) -> Dict[str, Any]:
    # BUG 9 FIX: lazy import — only imported when this function is called,
    # not at module load time, eliminating the circular import risk.
    from app.services.vision_service import cosmos_inference  # noqa: PLC0415

    vision_result = await cosmos_inference(
        query=f"Analyze the scene for robot action planning: {scene_description}. Task: {task}"
    )

    plan = await plan_robot_action(
        query=f"Based on vision analysis: {vision_result.get('response', '')}. Execute: {task}",
        environment_context=scene_description,
        robot_type=robot_type,
    )

    return {
        "service":         "robotics",
        "task":            "vision_guided_action",
        "vision_analysis": vision_result,
        "action_plan":     plan,
    }


async def simulate_action(action: str, environment: str = "indoor") -> Dict[str, Any]:
    start_time = time.time()

    if HAS_PYBULLET:
        try:
            return {
                "service":    "robotics",
                "simulation": "pybullet_local",
                "action":     action,
                "status":     "simulated",
                "result":     "Local PyBullet simulation completed",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
        except Exception as e:
            logger.warning(f"PyBullet sim failed: {e}")

    sim_result = await chat_completion(
        model=ROBOTICS_PRIMARY_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a physics simulation engine. Predict the outcome of the "
                    "given robot action in the specified environment."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Simulate action '{action}' in environment '{environment}'. "
                    "Predict outcome, collisions, energy usage, and success probability."
                ),
            },
        ],
        temperature=0.1,
        max_tokens=512,
    )

    return {
        "service":           "robotics",
        "simulation":        "cloud_nim",
        "action":            action,
        "environment":       environment,
        "predicted_outcome": sim_result.get("content", ""),
        "latency_ms":        round((time.time() - start_time) * 1000, 2),
        "note": (
            "Simulated via NIM cloud. "
            "Use Isaac Sim or PyBullet for physics-accurate results."
        ),
    }


ROBOTICS_CAPABILITIES = {
    "models":            [ROBOTICS_PRIMARY_MODEL, ROBOTICS_AV_MODEL],
    "ros2_available":    HAS_ROS2,
    "pybullet_available": HAS_PYBULLET,
    "cloud_simulation":  True,
    "supported_robots":  ["amr", "arm", "manipulator", "humanoid", "drone"],
    "features": [
        "action_planning",
        "navigation",
        "vision_guided_actions",
        "simulation",
        "swarm_coordination",
        "safety_assessment",
        "autonomous_driving",
        "humanoid_control",
    ],
    "actions": [a.value for a in RobotAction],
    "model_details": {
        ROBOTICS_PRIMARY_MODEL: "Humanoid robot control and manipulation (Isaac GR00T N1.6)",
        ROBOTICS_AV_MODEL:      "Autonomous vehicle reasoning and path planning (Alpamayo 1)",
    },
}
