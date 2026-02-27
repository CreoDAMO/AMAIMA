import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from app.modules.nvidia_nim_client import chat_completion


class AgentRole:
    def __init__(self, name: str, goal: str, backstory: str, model: str = "meta/llama-3.1-8b-instruct"):
        self.name = name
        self.goal = goal
        self.backstory = backstory
        self.model = model
        self.memory: List[Dict[str, str]] = []

    async def execute(self, task: str, context: str = "") -> Dict[str, Any]:
        start_time = time.time()
        messages = [
            {"role": "system", "content": f"You are {self.name}. {self.backstory}\nGoal: {self.goal}"},
        ]
        for mem in self.memory[-5:]:
            messages.append(mem)

        if context:
            messages.append({"role": "user", "content": f"Context from previous agent:\n{context}\n\nTask: {task}"})
        else:
            messages.append({"role": "user", "content": task})

        try:
            result = await chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            response = result.get("content", "")
            self.memory.append({"role": "user", "content": task})
            self.memory.append({"role": "assistant", "content": response})

            return {
                "agent": self.name,
                "response": response,
                "model": self.model,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            return {
                "agent": self.name,
                "error": str(e),
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }


class Crew:
    def __init__(self, name: str, agents: List[AgentRole], process: str = "sequential"):
        self.name = name
        self.agents = agents
        self.process = process

    async def kickoff(self, task: str) -> Dict[str, Any]:
        start_time = time.time()
        results = []
        context = ""

        if self.process == "sequential":
            for agent in self.agents:
                result = await agent.execute(task, context)
                results.append(result)
                context = result.get("response", "")

        elif self.process == "parallel":
            import asyncio
            tasks = [agent.execute(task) for agent in self.agents]
            results = list(await asyncio.gather(*tasks))

        elif self.process == "hierarchical":
            manager = self.agents[0]
            manager_result = await manager.execute(f"Break down this task for your team: {task}")
            results.append(manager_result)
            context = manager_result.get("response", "")
            for agent in self.agents[1:]:
                result = await agent.execute(task, context)
                results.append(result)
                context += f"\n{agent.name}: {result.get('response', '')}"

        total_time = round((time.time() - start_time) * 1000, 2)

        return {
            "crew": self.name,
            "process": self.process,
            "agents_used": [a.name for a in self.agents],
            "results": results,
            "final_output": results[-1].get("response", "") if results else "",
            "total_latency_ms": total_time,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Standard crew agent definitions
# ─────────────────────────────────────────────────────────────────────────────

RESEARCHER = AgentRole(
    name="Researcher",
    goal="Gather comprehensive data and evidence on the given topic",
    backstory="Expert in data collection and research methodology with broad domain knowledge",
    model="meta/llama-3.1-70b-instruct",
)

ANALYST = AgentRole(
    name="Analyst",
    goal="Analyze gathered data and extract actionable insights",
    backstory="Data analysis specialist skilled in pattern recognition and critical thinking",
    model="meta/llama-3.1-70b-instruct",
)

SYNTHESIZER = AgentRole(
    name="Synthesizer",
    goal="Combine analysis into clear, actionable recommendations",
    backstory="Expert communicator who transforms complex analysis into clear guidance",
    model="meta/llama-3.1-8b-instruct",
)


# ─────────────────────────────────────────────────────────────────────────────
# Neural Audio Synthesis Crew
# Orchestrates TTS via the audio_service — the final node dispatches to
# NVIDIA Riva rather than returning LLM text.
# ─────────────────────────────────────────────────────────────────────────────

AUDIO_ENGINEER = AgentRole(
    name="Audio Engineer",
    goal="Analyze the input text and determine optimal pacing, emphasis, and voice parameters for synthesis",
    backstory="Expert in speech prosody, SSML markup, and neural TTS systems. Prepares text for high-quality audio synthesis.",
    model="meta/llama-3.1-70b-instruct",
)

TONE_ANALYST = AgentRole(
    name="Tone Analyst",
    goal="Evaluate the emotional tone and speaking style required, then finalize the synthesis-ready script",
    backstory="Specialist in linguistic analysis and voice characterization. Produces the final polished text for the TTS engine.",
    model="meta/llama-3.1-8b-instruct",
)


async def run_neural_audio_crew(task: str) -> Dict[str, Any]:
    """
    Neural Audio Synthesis crew:
      1. Audio Engineer — analyzes pacing and emphasis
      2. Tone Analyst — refines the script
      3. TTS dispatch — sends the finalized script to NVIDIA Riva TTS
    """
    from app.services.audio_service import text_to_speech

    crew = Crew(
        name="Neural Audio Synthesis",
        agents=[AUDIO_ENGINEER, TONE_ANALYST],
        process="sequential",
    )
    crew_result = await crew.kickoff(task)

    # The final agent output is the synthesis-ready script
    synthesis_script = crew_result.get("final_output", task)

    # Dispatch to real TTS service
    tts_result = await text_to_speech(synthesis_script)

    crew_result["tts_output"] = tts_result
    crew_result["audio_data"] = tts_result.get("audio_data")
    crew_result["service_type"] = "neural_audio_synthesis"

    return crew_result


# ─────────────────────────────────────────────────────────────────────────────
# Visual Art Generation Crew
# Orchestrates image generation via image_gen_service — the final node
# dispatches to SDXL-Turbo rather than returning LLM text.
# ─────────────────────────────────────────────────────────────────────────────

CREATIVE_DIRECTOR = AgentRole(
    name="Creative Director",
    goal="Interpret the user's creative intent and write a detailed, optimized image generation prompt",
    backstory="Expert in visual storytelling, prompt engineering for diffusion models, and cinematic composition. "
              "Produces highly detailed prompts specifying lighting, style, subject, mood, and technical quality descriptors.",
    model="meta/llama-3.1-70b-instruct",
)

AESTHETIC_VALIDATOR = AgentRole(
    name="Aesthetic Validator",
    goal="Review and refine the image prompt for quality, coherence, and SDXL-Turbo optimization",
    backstory="Specialist in diffusion model prompt quality. Removes ambiguity, adds style anchors, "
              "and ensures the prompt will produce the intended visual output.",
    model="meta/llama-3.1-8b-instruct",
)


async def run_visual_art_crew(task: str) -> Dict[str, Any]:
    """
    Visual Art Generation crew:
      1. Creative Director — writes the optimized image prompt
      2. Aesthetic Validator — refines it for SDXL-Turbo
      3. Image generation dispatch — sends to NVIDIA NIM SDXL-Turbo
    """
    # Import moved inside function to prevent circular dependency if any
    from app.services.image_service import generate_image

    crew = Crew(
        name="Visual Art Generation",
        agents=[CREATIVE_DIRECTOR, AESTHETIC_VALIDATOR],
        process="sequential",
    )
    crew_result = await crew.kickoff(task)

    # The final agent output is the optimized image prompt
    image_prompt = crew_result.get("final_output", task)

    # Dispatch to real image generation service
    from app.services.image_service import generate_image
    image_result = await generate_image(image_prompt)

    crew_result["image_output"] = image_result
    crew_result["image_data"] = image_result.get("image_data")
    crew_result["service_type"] = "visual_art_generation"

    return crew_result


# ─────────────────────────────────────────────────────────────────────────────
# Crew runner — top-level dispatch for /v1/agents/run
# ─────────────────────────────────────────────────────────────────────────────

CREW_REGISTRY = {
    "research": "research",
    "neural_audio_synthesis": "neural_audio",
    "audio": "neural_audio",
    "visual_art_generation": "visual_art",
    "image_gen": "visual_art",
    "custom": "custom",
}


async def run_research_crew(topic: str, process: str = "sequential") -> Dict[str, Any]:
    crew = Crew(
        name="Research Crew",
        agents=[RESEARCHER, ANALYST, SYNTHESIZER],
        process=process,
    )
    return await crew.kickoff(f"Research and analyze: {topic}")


async def run_custom_crew(
    task: str,
    roles: List[Dict[str, str]],
    process: str = "sequential",
) -> Dict[str, Any]:
    agents = [
        AgentRole(
            name=role.get("name", "Agent"),
            goal=role.get("goal", "Complete the assigned task"),
            backstory=role.get("backstory", "AI assistant"),
            model=role.get("model", "meta/llama-3.1-8b-instruct"),
        )
        for role in roles
    ]
    crew = Crew(name="Custom Crew", agents=agents, process=process)
    return await crew.kickoff(task)


async def run_crew(
    task: str,
    crew_type: str,
    process: str = "sequential",
    roles: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Top-level crew dispatcher. Called by /v1/agents/run.

    crew_type options:
      - "research"                → Research Crew (LLM pipeline)
      - "neural_audio_synthesis"  → Audio Engineer + Tone Analyst + Riva TTS
      - "audio"                   → Alias for neural_audio_synthesis
      - "visual_art_generation"   → Creative Director + Validator + SDXL-Turbo
      - "image_gen"               → Alias for visual_art_generation
      - "custom"                  → Custom roles (requires roles parameter)
    """
    resolved = CREW_REGISTRY.get(crew_type.lower(), "research")

    if resolved == "neural_audio":
        return await run_neural_audio_crew(task)
    elif resolved == "visual_art":
        return await run_visual_art_crew(task)
    elif resolved == "custom" and roles:
        return await run_custom_crew(task, roles, process)
    else:
        return await run_research_crew(task, process)
