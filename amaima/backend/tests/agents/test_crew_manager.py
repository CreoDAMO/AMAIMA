import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.crew_manager import AgentRole, Crew, run_research_crew, run_custom_crew


@pytest.fixture
def mock_chat_completion():
    with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
        mock.return_value = {"content": "Test response from model"}
        yield mock


class TestAgentRole:
    def test_init(self):
        agent = AgentRole(
            name="Test Agent",
            goal="Test goal",
            backstory="Test backstory",
            model="meta/llama-3.1-8b-instruct",
        )
        assert agent.name == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.backstory == "Test backstory"
        assert agent.model == "meta/llama-3.1-8b-instruct"
        assert agent.memory == []

    def test_default_model(self):
        agent = AgentRole(name="A", goal="G", backstory="B")
        assert agent.model == "meta/llama-3.1-8b-instruct"

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_chat_completion):
        agent = AgentRole(name="Tester", goal="Test", backstory="Expert")
        result = await agent.execute("Analyze this topic")

        assert result["agent"] == "Tester"
        assert result["response"] == "Test response from model"
        assert result["model"] == "meta/llama-3.1-8b-instruct"
        assert "latency_ms" in result
        assert len(agent.memory) == 2

    @pytest.mark.asyncio
    async def test_execute_with_context(self, mock_chat_completion):
        agent = AgentRole(name="Tester", goal="Test", backstory="Expert")
        result = await agent.execute("Analyze", context="Previous findings")

        assert result["response"] == "Test response from model"
        call_args = mock_chat_completion.call_args
        messages = call_args[1]["messages"] if "messages" in call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("messages", [])
        user_msg = [m for m in messages if m["role"] == "user"]
        assert any("Previous findings" in m["content"] for m in user_msg)

    @pytest.mark.asyncio
    async def test_execute_error(self):
        with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API error")
            agent = AgentRole(name="Tester", goal="Test", backstory="Expert")
            result = await agent.execute("task")
            assert "error" in result
            assert result["agent"] == "Tester"

    @pytest.mark.asyncio
    async def test_memory_accumulation(self, mock_chat_completion):
        agent = AgentRole(name="Tester", goal="Test", backstory="Expert")
        await agent.execute("Task 1")
        await agent.execute("Task 2")
        assert len(agent.memory) == 4


class TestCrew:
    @pytest.mark.asyncio
    async def test_sequential_process(self, mock_chat_completion):
        agents = [
            AgentRole(name="Agent1", goal="G1", backstory="B1"),
            AgentRole(name="Agent2", goal="G2", backstory="B2"),
        ]
        crew = Crew(name="Test Crew", agents=agents, process="sequential")
        result = await crew.kickoff("Test task")

        assert result["crew"] == "Test Crew"
        assert result["process"] == "sequential"
        assert len(result["results"]) == 2
        assert result["agents_used"] == ["Agent1", "Agent2"]
        assert "final_output" in result
        assert "total_latency_ms" in result

    @pytest.mark.asyncio
    async def test_parallel_process(self, mock_chat_completion):
        agents = [
            AgentRole(name="Agent1", goal="G1", backstory="B1"),
            AgentRole(name="Agent2", goal="G2", backstory="B2"),
        ]
        crew = Crew(name="Test Crew", agents=agents, process="parallel")
        result = await crew.kickoff("Test task")

        assert result["process"] == "parallel"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_hierarchical_process(self, mock_chat_completion):
        agents = [
            AgentRole(name="Manager", goal="G1", backstory="B1"),
            AgentRole(name="Worker1", goal="G2", backstory="B2"),
            AgentRole(name="Worker2", goal="G3", backstory="B3"),
        ]
        crew = Crew(name="Test Crew", agents=agents, process="hierarchical")
        result = await crew.kickoff("Test task")

        assert result["process"] == "hierarchical"
        assert len(result["results"]) == 3


class TestResearchCrew:
    @pytest.mark.asyncio
    async def test_run_research_crew(self, mock_chat_completion):
        result = await run_research_crew("AI trends 2026")
        assert result["crew"] == "Research Crew"
        assert len(result["results"]) == 3
        assert result["agents_used"] == ["Researcher", "Analyst", "Synthesizer"]


class TestCustomCrew:
    @pytest.mark.asyncio
    async def test_run_custom_crew(self, mock_chat_completion):
        roles = [
            {"name": "Scout", "goal": "Find info", "backstory": "Researcher"},
            {"name": "Writer", "goal": "Write report", "backstory": "Author"},
        ]
        result = await run_custom_crew("Write a report", roles)
        assert result["crew"] == "Custom Crew"
        assert len(result["results"]) == 2
