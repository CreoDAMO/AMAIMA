import pytest
from unittest.mock import AsyncMock, patch
from app.agents.langchain_agent import (
    WorkflowState,
    WorkflowNode,
    ConditionalEdge,
    StatefulWorkflow,
    build_research_workflow,
    build_complex_reasoning_workflow,
    build_domain_workflow,
    run_langchain_agent,
    list_workflows,
    WORKFLOW_REGISTRY,
)


@pytest.fixture
def mock_chat_completion():
    with patch("app.agents.langchain_agent.chat_completion", new_callable=AsyncMock) as mock:
        mock.return_value = {"content": "Workflow step completed successfully"}
        yield mock


class TestWorkflowState:
    def test_init(self):
        state = WorkflowState()
        assert state.messages == []
        assert state.context == {}
        assert state.current_node == "start"
        assert state.iteration == 0

    def test_add_message(self):
        state = WorkflowState()
        state.add_message("user", "Hello")
        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "user"
        assert state.messages[0]["content"] == "Hello"

    def test_context_operations(self):
        state = WorkflowState()
        state.set_context("domain", "biology")
        assert state.get_context("domain") == "biology"
        assert state.get_context("missing", "default") == "default"


class TestWorkflowNode:
    def test_init(self):
        node = WorkflowNode(
            name="test_node",
            model="meta/llama-3.1-8b-instruct",
            system_prompt="You are helpful",
        )
        assert node.name == "test_node"
        assert node.model == "meta/llama-3.1-8b-instruct"

    @pytest.mark.asyncio
    async def test_execute(self, mock_chat_completion):
        node = WorkflowNode(name="test", system_prompt="Be helpful")
        state = WorkflowState()
        state.add_message("user", "Test query")
        result = await node.execute(state)
        assert result["status"] == "success"
        assert result["response"] == "Workflow step completed successfully"
        assert len(state.history) == 1

    @pytest.mark.asyncio
    async def test_execute_error(self):
        with patch("app.agents.langchain_agent.chat_completion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API error")
            node = WorkflowNode(name="test")
            state = WorkflowState()
            state.add_message("user", "query")
            result = await node.execute(state)
            assert result["status"] == "error"


class TestConditionalEdge:
    def test_true_condition(self):
        edge = ConditionalEdge(
            condition_fn=lambda s: True,
            true_target="node_a",
            false_target="node_b",
        )
        state = WorkflowState()
        assert edge.evaluate(state) == "node_a"

    def test_false_condition(self):
        edge = ConditionalEdge(
            condition_fn=lambda s: False,
            true_target="node_a",
            false_target="node_b",
        )
        state = WorkflowState()
        assert edge.evaluate(state) == "node_b"

    def test_exception_defaults_to_false(self):
        edge = ConditionalEdge(
            condition_fn=lambda s: 1 / 0,
            true_target="node_a",
            false_target="node_b",
        )
        state = WorkflowState()
        assert edge.evaluate(state) == "node_b"


class TestStatefulWorkflow:
    @pytest.mark.asyncio
    async def test_simple_workflow(self, mock_chat_completion):
        workflow = StatefulWorkflow("Test")
        node_a = WorkflowNode(name="a", system_prompt="Step A")
        node_b = WorkflowNode(name="b", system_prompt="Step B")
        workflow.add_node(node_a)
        workflow.add_node(node_b)
        workflow.add_edge("a", "b")
        workflow.add_edge("b", "END")
        workflow.set_entry_point("a")

        result = await workflow.run("Test input")
        assert result["status"] == "completed"
        assert len(result["history"]) == 2
        assert result["iterations"] == 2

    @pytest.mark.asyncio
    async def test_no_entry_point(self, mock_chat_completion):
        workflow = StatefulWorkflow("Test")
        result = await workflow.run("input")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_missing_node(self, mock_chat_completion):
        workflow = StatefulWorkflow("Test")
        workflow.set_entry_point("nonexistent")
        result = await workflow.run("input")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_conditional_workflow(self, mock_chat_completion):
        workflow = StatefulWorkflow("Conditional Test")
        node_a = WorkflowNode(name="a")
        node_b = WorkflowNode(name="b")
        node_c = WorkflowNode(name="c")
        workflow.add_node(node_a)
        workflow.add_node(node_b)
        workflow.add_node(node_c)
        workflow.add_edge("a", "b")
        workflow.add_conditional_edge("b", ConditionalEdge(
            condition_fn=lambda s: False,
            true_target="a",
            false_target="END",
        ))
        workflow.set_entry_point("a")

        result = await workflow.run("input")
        assert result["status"] == "completed"
        assert result["iterations"] == 2

    @pytest.mark.asyncio
    async def test_max_iterations(self, mock_chat_completion):
        workflow = StatefulWorkflow("Loop")
        node = WorkflowNode(name="loop")
        workflow.add_node(node)
        workflow.add_edge("loop", "loop")
        workflow.set_entry_point("loop")

        result = await workflow.run("input")
        assert result["status"] == "completed"
        assert result["iterations"] == 10

    @pytest.mark.asyncio
    async def test_with_context(self, mock_chat_completion):
        workflow = StatefulWorkflow("Context Test")
        node = WorkflowNode(name="a")
        workflow.add_node(node)
        workflow.add_edge("a", "END")
        workflow.set_entry_point("a")

        result = await workflow.run("query", context={"domain": "biology"})
        assert result["status"] == "completed"


class TestBuiltInWorkflows:
    @pytest.mark.asyncio
    async def test_research_workflow(self, mock_chat_completion):
        workflow = build_research_workflow()
        assert workflow.name == "Research Workflow"
        result = await workflow.run("Analyze AI trends in 2026")
        assert result["status"] == "completed"
        assert len(result["history"]) == 3

    @pytest.mark.asyncio
    async def test_complex_reasoning_workflow(self, mock_chat_completion):
        workflow = build_complex_reasoning_workflow()
        assert workflow.name == "Complex Reasoning Workflow"
        result = await workflow.run("Solve this optimization problem")
        assert result["status"] == "completed"
        assert len(result["history"]) >= 3

    @pytest.mark.asyncio
    async def test_domain_workflow_biology(self, mock_chat_completion):
        workflow = build_domain_workflow("biology")
        assert workflow.name == "Biology Research Workflow"
        result = await workflow.run("Analyze EGFR protein binding")
        assert result["status"] == "completed"
        assert len(result["history"]) == 3

    @pytest.mark.asyncio
    async def test_domain_workflow_robotics(self, mock_chat_completion):
        workflow = build_domain_workflow("robotics")
        assert workflow.name == "Robotics Planning Workflow"

    @pytest.mark.asyncio
    async def test_domain_workflow_vision(self, mock_chat_completion):
        workflow = build_domain_workflow("vision")
        assert workflow.name == "Vision Analysis Workflow"


class TestRunLangchainAgent:
    @pytest.mark.asyncio
    async def test_run_research(self, mock_chat_completion):
        result = await run_langchain_agent("Research AI", workflow_type="research")
        assert result["status"] == "completed"
        assert result["workflow"] == "Research Workflow"

    @pytest.mark.asyncio
    async def test_run_unknown_type(self, mock_chat_completion):
        result = await run_langchain_agent("query", workflow_type="nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_workflow_registry(self):
        assert "research" in WORKFLOW_REGISTRY
        assert "complex_reasoning" in WORKFLOW_REGISTRY
        assert "biology" in WORKFLOW_REGISTRY
        assert "robotics" in WORKFLOW_REGISTRY
        assert "vision" in WORKFLOW_REGISTRY
        assert "audio" in WORKFLOW_REGISTRY
        assert "image_gen" in WORKFLOW_REGISTRY


class TestListWorkflows:
    @pytest.mark.asyncio
    async def test_list_workflows(self):
        workflows = await list_workflows()
        assert len(workflows) == 7
        ids = [w["id"] for w in workflows]
        assert "research" in ids
        assert "complex_reasoning" in ids
        assert "biology" in ids
        assert "robotics" in ids
        assert "vision" in ids
        assert "audio" in ids
        assert "image_gen" in ids
