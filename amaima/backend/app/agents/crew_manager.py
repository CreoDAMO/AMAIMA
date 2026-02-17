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
            messages.append({"role": "user", "content": f"Context from previous agent: {context}\n\nTask: {task}"})
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
            results = await asyncio.gather(*tasks)
            results = list(results)

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
    agents = []
    for role in roles:
        agents.append(AgentRole(
            name=role.get("name", "Agent"),
            goal=role.get("goal", "Complete the assigned task"),
            backstory=role.get("backstory", "AI assistant"),
            model=role.get("model", "meta/llama-3.1-8b-instruct"),
        ))

    crew = Crew(name="Custom Crew", agents=agents, process=process)
    return await crew.kickoff(task)
