import pytest
from unittest.mock import AsyncMock, patch
from app.agents.robotics_crew import (
    run_navigation_crew,
    run_manipulation_crew,
    run_swarm_crew,
    PERCEPTION_AGENT,
    PATH_PLANNER,
    ACTION_EXECUTOR,
    SAFETY_MONITOR,
)


@pytest.fixture
def mock_chat_completion():
    with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
        mock.return_value = {"content": "Robot action planned successfully"}
        yield mock


class TestRoboticsAgentRoles:
    def test_perception_agent(self):
        assert PERCEPTION_AGENT.name == "Perception Agent"
        assert "environment" in PERCEPTION_AGENT.goal
        assert PERCEPTION_AGENT.model == "meta/llama-3.1-70b-instruct"

    def test_path_planner(self):
        assert PATH_PLANNER.name == "Path Planner"
        assert "collision-free" in PATH_PLANNER.goal

    def test_action_executor(self):
        assert ACTION_EXECUTOR.name == "Action Executor"
        assert ACTION_EXECUTOR.model == "meta/llama-3.1-8b-instruct"

    def test_safety_monitor(self):
        assert SAFETY_MONITOR.name == "Safety Monitor"
        assert "ISO" in SAFETY_MONITOR.backstory


class TestNavigationCrew:
    @pytest.mark.asyncio
    async def test_run_navigation_crew(self, mock_chat_completion):
        result = await run_navigation_crew(
            "Navigate to loading dock",
            environment="warehouse",
            robot_type="amr",
        )
        assert result["crew"] == "Navigation Crew"
        assert result["process"] == "sequential"
        assert len(result["results"]) == 4
        assert "Perception Agent" in result["agents_used"]
        assert "Path Planner" in result["agents_used"]
        assert "Action Executor" in result["agents_used"]
        assert "Safety Monitor" in result["agents_used"]

    @pytest.mark.asyncio
    async def test_navigation_defaults(self, mock_chat_completion):
        result = await run_navigation_crew("Go forward")
        assert result["crew"] == "Navigation Crew"

    @pytest.mark.asyncio
    async def test_navigation_error(self):
        with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("ROS2 unavailable")
            result = await run_navigation_crew("test")
            assert any("error" in r for r in result["results"])


class TestManipulationCrew:
    @pytest.mark.asyncio
    async def test_run_manipulation_crew(self, mock_chat_completion):
        result = await run_manipulation_crew(
            "Pick up the red box",
            object_description="Small red cardboard box, 10x10x10cm",
        )
        assert result["crew"] == "Manipulation Crew"
        assert result["process"] == "sequential"
        assert len(result["results"]) == 4
        assert "Grasp Planner" in result["agents_used"]

    @pytest.mark.asyncio
    async def test_manipulation_default_object(self, mock_chat_completion):
        result = await run_manipulation_crew("Grasp object")
        assert result["crew"] == "Manipulation Crew"


class TestSwarmCrew:
    @pytest.mark.asyncio
    async def test_run_swarm_crew(self, mock_chat_completion):
        result = await run_swarm_crew(
            "Coordinate warehouse inventory scan",
            num_robots=5,
            environment="warehouse",
        )
        assert result["crew"] == "Swarm Coordination Crew"
        assert result["process"] == "hierarchical"
        assert len(result["results"]) == 4
        assert "Swarm Coordinator" in result["agents_used"]

    @pytest.mark.asyncio
    async def test_swarm_defaults(self, mock_chat_completion):
        result = await run_swarm_crew("Patrol area")
        assert result["crew"] == "Swarm Coordination Crew"
        assert "final_output" in result
