import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from app.modules.nvidia_nim_client import chat_completion
from app.agents.crew_manager import AgentRole, Crew


class WorkflowState:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
        self.current_node: str = "start"
        self.history: List[Dict[str, Any]] = []
        self.iteration: int = 0
        self.max_iterations: int = 10

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def set_context(self, key: str, value: Any):
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)


class WorkflowNode:
    def __init__(self, name: str, model: str = "meta/llama-3.1-70b-instruct",
                 system_prompt: str = "", temperature: float = 0.3):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature

    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        start_time = time.time()
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in state.messages[-10:]:
            messages.append(msg)

        try:
            result = await chat_completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2048,
            )
            response = result.get("content", "")
            state.add_message("assistant", response)
            state.history.append({
                "node": self.name,
                "model": self.model,
                "response": response,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            })
            return {"status": "success", "response": response}
        except Exception as e:
            logger.error(f"Node {self.name} failed: {e}")
            return {"status": "error", "error": str(e)}


class ConditionalEdge:
    def __init__(self, condition_fn, true_target: str, false_target: str):
        self.condition_fn = condition_fn
        self.true_target = true_target
        self.false_target = false_target

    def evaluate(self, state: WorkflowState) -> str:
        try:
            return self.true_target if self.condition_fn(state) else self.false_target
        except Exception:
            return self.false_target


class StatefulWorkflow:
    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, Any] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, node: WorkflowNode):
        self.nodes[node.name] = node

    def add_edge(self, from_node: str, to_node: str):
        self.edges[from_node] = to_node

    def add_conditional_edge(self, from_node: str, edge: ConditionalEdge):
        self.edges[from_node] = edge

    def set_entry_point(self, node_name: str):
        self.entry_point = node_name

    async def run(self, initial_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.time()
        state = WorkflowState()
        state.add_message("user", initial_input)

        if context:
            for k, v in context.items():
                state.set_context(k, v)

        current = self.entry_point
        if not current:
            return {"error": "No entry point set"}

        while current and current != "END" and state.iteration < state.max_iterations:
            state.iteration += 1
            state.current_node = current

            node = self.nodes.get(current)
            if not node:
                return {"error": f"Node '{current}' not found"}

            result = await node.execute(state)
            if result.get("status") == "error":
                return {
                    "workflow": self.name,
                    "status": "error",
                    "error": result.get("error"),
                    "history": state.history,
                    "iterations": state.iteration,
                }

            next_edge = self.edges.get(current)
            if isinstance(next_edge, ConditionalEdge):
                current = next_edge.evaluate(state)
            elif isinstance(next_edge, str):
                current = next_edge
            else:
                current = "END"

        return {
            "workflow": self.name,
            "status": "completed",
            "final_output": state.history[-1].get("response", "") if state.history else "",
            "history": state.history,
            "iterations": state.iteration,
            "total_latency_ms": round((time.time() - start_time) * 1000, 2),
        }


def build_research_workflow() -> StatefulWorkflow:
    workflow = StatefulWorkflow("Research Workflow")

    researcher = WorkflowNode(
        name="researcher",
        model="meta/llama-3.1-70b-instruct",
        system_prompt="You are a thorough researcher. Gather comprehensive data and evidence on the topic. Provide detailed findings with sources where possible.",
    )

    analyzer = WorkflowNode(
        name="analyzer",
        model="meta/llama-3.1-70b-instruct",
        system_prompt="You are an expert analyst. Review the research findings and extract key insights, patterns, and actionable conclusions. Be critical and thorough.",
    )

    synthesizer = WorkflowNode(
        name="synthesizer",
        model="meta/llama-3.1-8b-instruct",
        system_prompt="You are a skilled communicator. Synthesize the analysis into a clear, well-structured summary with actionable recommendations. Be concise but comprehensive.",
    )

    workflow.add_node(researcher)
    workflow.add_node(analyzer)
    workflow.add_node(synthesizer)

    workflow.add_edge("researcher", "analyzer")
    workflow.add_edge("analyzer", "synthesizer")
    workflow.add_edge("synthesizer", "END")
    workflow.set_entry_point("researcher")

    return workflow


def build_complex_reasoning_workflow() -> StatefulWorkflow:
    workflow = StatefulWorkflow("Complex Reasoning Workflow")

    decomposer = WorkflowNode(
        name="decomposer",
        model="meta/llama-3.1-70b-instruct",
        system_prompt="You are a problem decomposition expert. Break down complex problems into clear, manageable sub-problems. List each sub-problem with its dependencies.",
    )

    solver = WorkflowNode(
        name="solver",
        model="meta/llama-3.1-70b-instruct",
        system_prompt="You are a systematic problem solver. Address each sub-problem with detailed reasoning. Show your work step by step using chain-of-thought.",
    )

    validator = WorkflowNode(
        name="validator",
        model="meta/llama-3.1-70b-instruct",
        system_prompt="You are a critical reviewer. Validate the solutions for correctness, completeness, and logical consistency. Identify any gaps or errors.",
    )

    def needs_revision(state: WorkflowState) -> bool:
        # Only trigger on explicit affirmative revision signals from the validator.
        # Loose keywords like "error" or "missing" appear constantly in normal
        # technical prose and cause false-positive loops that burn 6× token cost.
        last_response = state.history[-1].get("response", "").lower() if state.history else ""
        revision_signals = [
            "requires revision",
            "needs revision",
            "revise the solution",
            "revise the answer",
            "incorrect conclusion",
            "logically inconsistent",
            "factually incorrect",
            "significant gap",
            "critical error",
            "must be corrected",
        ]
        has_explicit_revision_signal = any(signal in last_response for signal in revision_signals)
        return has_explicit_revision_signal and state.iteration < 6

    workflow.add_node(decomposer)
    workflow.add_node(solver)
    workflow.add_node(validator)

    workflow.add_edge("decomposer", "solver")
    workflow.add_edge("solver", "validator")
    workflow.add_conditional_edge("validator", ConditionalEdge(
        condition_fn=needs_revision,
        true_target="solver",
        false_target="END",
    ))
    workflow.set_entry_point("decomposer")

    return workflow


def build_domain_workflow(domain: str) -> StatefulWorkflow:
    domain_configs = {
        "biology": {
            "name": "Biology Research Workflow",
            "specialist_prompt": "You are a computational biology expert. Analyze biological queries including drug targets, protein structures, molecular interactions, and genomics. Provide scientifically rigorous responses.",
            "reviewer_prompt": "You are a biology peer reviewer. Validate scientific accuracy, check methodology, and ensure conclusions are supported by evidence.",
        },
        "robotics": {
            "name": "Robotics Planning Workflow",
            "specialist_prompt": "You are a robotics planning expert. Analyze tasks for autonomous systems including navigation, manipulation, and multi-robot coordination. Consider safety, physics constraints, and real-time requirements.",
            "reviewer_prompt": "You are a robotics safety reviewer. Validate plans for physical feasibility, safety compliance (ISO 10218/15066), and robustness under uncertainty.",
        },
        "vision": {
            "name": "Vision Analysis Workflow",
            "specialist_prompt": "You are a computer vision and multimodal reasoning expert. Analyze visual scenarios, scene understanding, object detection, and spatial reasoning tasks. Provide structured analysis with confidence levels.",
            "reviewer_prompt": "You are a vision system reviewer. Validate analysis for accuracy, check for biases, and ensure robust handling of edge cases.",
        },
        "audio": {
            "name": "Neural Audio Synthesis Workflow",
            "specialist_prompt": "You are an audio engineering and speech synthesis expert. Analyze text for emotional tone, pacing, and prosody to prepare for high-fidelity speech generation. Provide detailed synthesis parameters.",
            "reviewer_prompt": "You are an audio quality reviewer. Ensure the synthesis plan meets enterprise standards for clarity, naturalness, and emotional accuracy.",
        },
        "image_gen": {
            "name": "Visual Art Generation Workflow",
            "specialist_prompt": "You are a creative director and prompt engineering expert. Expand user concepts into detailed, high-fidelity visual descriptions using artistic terminology (lighting, composition, style).",
            "reviewer_prompt": "You are a visual quality reviewer. Validate that the generated prompt avoids artifacts, maintains consistency, and aligns with professional aesthetic standards.",
        },
    }

    config = domain_configs.get(domain, domain_configs["biology"])
    workflow = StatefulWorkflow(config["name"])

    classifier = WorkflowNode(
        name="classifier",
        model="meta/llama-3.1-8b-instruct",
        system_prompt=f"You are a {domain} query classifier. Analyze the query and determine: 1) Specific sub-domain, 2) Complexity level (simple/moderate/complex), 3) Required capabilities. Output a structured classification.",
    )

    specialist = WorkflowNode(
        name="specialist",
        model="meta/llama-3.1-70b-instruct",
        system_prompt=config["specialist_prompt"],
    )

    reviewer = WorkflowNode(
        name="reviewer",
        model="meta/llama-3.1-70b-instruct",
        system_prompt=config["reviewer_prompt"],
    )

    workflow.add_node(classifier)
    workflow.add_node(specialist)
    workflow.add_node(reviewer)

    workflow.add_edge("classifier", "specialist")
    workflow.add_edge("specialist", "reviewer")
    workflow.add_edge("reviewer", "END")
    workflow.set_entry_point("classifier")

    return workflow


WORKFLOW_REGISTRY = {
    "research": build_research_workflow,
    "complex_reasoning": build_complex_reasoning_workflow,
    "biology": lambda: build_domain_workflow("biology"),
    "robotics": lambda: build_domain_workflow("robotics"),
    "vision": lambda: build_domain_workflow("vision"),
    "audio": lambda: build_domain_workflow("audio"),
    "image_gen": lambda: build_domain_workflow("image_gen"),
    "agent_builder": build_research_workflow,
}


async def run_langchain_agent(query: str, workflow_type: str = "research",
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    builder = WORKFLOW_REGISTRY.get(workflow_type)
    if not builder:
        return {"error": f"Unknown workflow type: {workflow_type}. Available: {list(WORKFLOW_REGISTRY.keys())}"}

    workflow = builder()
    return await workflow.run(query, context=context)


async def list_workflows() -> List[Dict[str, str]]:
    return [
        {"id": "research", "name": "Research Workflow", "description": "Multi-step research with analysis and synthesis"},
        {"id": "complex_reasoning", "name": "Complex Reasoning", "description": "Problem decomposition with iterative validation"},
        {"id": "biology", "name": "Biology Research", "description": "Domain-specific biology analysis with peer review"},
        {"id": "robotics", "name": "Robotics Planning", "description": "Robot task planning with safety validation"},
        {"id": "vision", "name": "Vision Analysis", "description": "Visual reasoning with structured analysis"},
        {"id": "audio", "name": "Audio Synthesis", "description": "Neural speech synthesis and emotional tone analysis"},
        {"id": "image_gen", "name": "Visual Generation", "description": "Creative direction and high-fidelity prompt engineering"},
    ]
