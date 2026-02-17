import os
import httpx
import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

NVIDIA_MODELS = {
    "meta/llama-3.1-8b-instruct": {
        "name": "Llama 3.1 8B Instruct",
        "provider": "Meta",
        "parameters": "8B",
        "context_window": 128000,
        "cost_per_1k_tokens": 0.0001,
        "domain": "general",
        "category": "language",
    },
    "meta/llama-3.1-70b-instruct": {
        "name": "Llama 3.1 70B Instruct",
        "provider": "Meta",
        "parameters": "70B",
        "context_window": 128000,
        "cost_per_1k_tokens": 0.00088,
        "domain": "general",
        "category": "language",
    },
    "meta/llama-3.1-405b-instruct": {
        "name": "Llama 3.1 405B Instruct",
        "provider": "Meta",
        "parameters": "405B",
        "context_window": 128000,
        "cost_per_1k_tokens": 0.005,
        "domain": "general",
        "category": "language",
    },
    "mistralai/mixtral-8x7b-instruct-v0.1": {
        "name": "Mixtral 8x7B Instruct",
        "provider": "Mistral AI",
        "parameters": "46.7B (8x7B MoE)",
        "context_window": 32768,
        "cost_per_1k_tokens": 0.0006,
        "domain": "general",
        "category": "language",
    },
    "google/gemma-2-9b-it": {
        "name": "Gemma 2 9B IT",
        "provider": "Google",
        "parameters": "9B",
        "context_window": 8192,
        "cost_per_1k_tokens": 0.0001,
        "domain": "general",
        "category": "language",
    },
    "mistralai/mixtral-8x22b-instruct-v0.1": {
        "name": "Mixtral 8x22B Instruct",
        "provider": "Mistral AI",
        "parameters": "141B (8x22B MoE)",
        "context_window": 65536,
        "cost_per_1k_tokens": 0.0012,
        "domain": "general",
        "category": "language",
        "description": "Large MoE model for balanced cost/performance on complex reasoning and domain analysis",
    },
    "nvidia/cosmos-reason2-7b": {
        "name": "Cosmos Reason 2 7B",
        "provider": "NVIDIA",
        "parameters": "7B",
        "context_window": 32768,
        "cost_per_1k_tokens": 0.0004,
        "domain": "vision",
        "category": "vision-language",
        "description": "Vision-language reasoning for physical AI, robot planning, embodied reasoning over images and video",
    },
    "nvidia/cosmos-predict2-14b": {
        "name": "Cosmos Predict 2.5 14B",
        "provider": "NVIDIA",
        "parameters": "14B",
        "context_window": 16384,
        "cost_per_1k_tokens": 0.001,
        "domain": "vision",
        "category": "world-model",
        "description": "Synthetic video generation from text/image/video prompts, future state prediction for robotics",
    },
    "nvidia/nemotron-nano-9b-v2": {
        "name": "Nemotron Nano 9B v2",
        "provider": "NVIDIA",
        "parameters": "9B",
        "context_window": 32768,
        "cost_per_1k_tokens": 0.0002,
        "domain": "general",
        "category": "language",
        "description": "Optimized for edge deployment, agentic AI with configurable thinking budget",
    },
    "nvidia/llama-3.1-nemotron-nano-vl-8b": {
        "name": "Nemotron Nano VL 8B",
        "provider": "NVIDIA",
        "parameters": "8B",
        "context_window": 32768,
        "cost_per_1k_tokens": 0.0003,
        "domain": "vision",
        "category": "vision-language",
        "description": "Vision-language understanding for multimodal reasoning tasks",
    },
    "nvidia/bionemo-megamolbart": {
        "name": "BioNeMo MegaMolBART",
        "provider": "NVIDIA",
        "parameters": "Encoder-Decoder",
        "context_window": 2048,
        "cost_per_1k_tokens": 0.0005,
        "domain": "biology",
        "category": "molecular",
        "description": "Molecular generation and optimization for drug discovery using SMILES representations",
    },
    "nvidia/bionemo-esm2": {
        "name": "BioNeMo ESM-2",
        "provider": "NVIDIA",
        "parameters": "650M",
        "context_window": 4096,
        "cost_per_1k_tokens": 0.0003,
        "domain": "biology",
        "category": "protein",
        "description": "Protein structure prediction, sequence analysis, and functional annotation",
    },
    "nvidia/isaac-gr00t-n1.6": {
        "name": "Isaac GR00T N1.6",
        "provider": "NVIDIA",
        "parameters": "VLA",
        "context_window": 8192,
        "cost_per_1k_tokens": 0.0008,
        "domain": "robotics",
        "category": "robotics-vla",
        "description": "Vision-language-action model for humanoid robot control, manipulation, and navigation",
    },
    "nvidia/alpamayo-1": {
        "name": "Alpamayo 1",
        "provider": "NVIDIA",
        "parameters": "VLA",
        "context_window": 8192,
        "cost_per_1k_tokens": 0.0006,
        "domain": "robotics",
        "category": "autonomous-vehicle",
        "description": "Reasoning VLA for autonomous vehicles, path planning, and scene understanding",
    },
}

COMPLEXITY_TO_MODEL = {
    "TRIVIAL": "meta/llama-3.1-8b-instruct",
    "SIMPLE": "meta/llama-3.1-8b-instruct",
    "MODERATE": "meta/llama-3.1-70b-instruct",
    "ADVANCED": "meta/llama-3.1-70b-instruct",
    "COMPLEX": "mistralai/mixtral-8x7b-instruct-v0.1",
    "EXPERT": "meta/llama-3.1-405b-instruct",
    "BORDERLINE_SIMPLE": "meta/llama-3.1-8b-instruct",
    "BORDERLINE_ADVANCED": "meta/llama-3.1-70b-instruct",
    "BORDERLINE_EXPERT": "meta/llama-3.1-405b-instruct",
    "BORDERLINE_ADVANCED_EXPERT": "meta/llama-3.1-405b-instruct",
}

DOMAIN_TO_MODELS = {
    "vision": {
        "primary": "nvidia/cosmos-reason2-7b",
        "secondary": "nvidia/llama-3.1-nemotron-nano-vl-8b",
        "world_model": "nvidia/cosmos-predict2-14b",
        "fallback": "meta/llama-3.1-70b-instruct",
    },
    "biology": {
        "primary": "nvidia/bionemo-megamolbart",
        "protein": "nvidia/bionemo-esm2",
        "fallback": "meta/llama-3.1-70b-instruct",
    },
    "robotics": {
        "primary": "nvidia/isaac-gr00t-n1.6",
        "autonomous": "nvidia/alpamayo-1",
        "fallback": "meta/llama-3.1-70b-instruct",
    },
    "general": {
        "primary": "meta/llama-3.1-70b-instruct",
        "edge": "nvidia/nemotron-nano-9b-v2",
        "fallback": "meta/llama-3.1-8b-instruct",
    },
}


def get_api_key() -> Optional[str]:
    return os.environ.get("NVIDIA_API_KEY")


def is_configured() -> bool:
    key = get_api_key()
    return key is not None and len(key) > 0


def get_model_for_complexity(complexity_level: str) -> str:
    return COMPLEXITY_TO_MODEL.get(complexity_level, "meta/llama-3.1-8b-instruct")


def get_model_for_domain(domain: str, task_type: str = "primary") -> str:
    domain_models = DOMAIN_TO_MODELS.get(domain, DOMAIN_TO_MODELS["general"])
    model_id = domain_models.get(task_type, domain_models.get("primary", domain_models["fallback"]))
    return model_id


def get_models_by_domain(domain: str) -> List[Dict[str, Any]]:
    result = []
    for model_id, info in NVIDIA_MODELS.items():
        if info.get("domain") == domain:
            result.append({"id": model_id, **info})
    return result


async def chat_completion(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
    stream: bool = False,
) -> Dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{NVIDIA_NIM_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )

    elapsed_ms = (time.time() - start_time) * 1000

    if response.status_code != 200:
        logger.error(f"NVIDIA NIM API error: {response.status_code} - {response.text}")
        raise RuntimeError(f"NVIDIA NIM API returned {response.status_code}: {response.text}")

    data = response.json()

    content = ""
    if data.get("choices") and len(data["choices"]) > 0:
        content = data["choices"][0].get("message", {}).get("content", "")

    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    model_info = NVIDIA_MODELS.get(model, {})
    cost_per_1k = model_info.get("cost_per_1k_tokens", 0.001)
    estimated_cost = (total_tokens / 1000) * cost_per_1k

    return {
        "content": content,
        "model": model,
        "latency_ms": round(elapsed_ms, 2),
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "estimated_cost_usd": round(estimated_cost, 6),
        "finish_reason": data["choices"][0].get("finish_reason", "stop") if data.get("choices") else "error",
    }


def list_available_models() -> List[Dict[str, Any]]:
    configured = is_configured()
    models = []
    for model_id, info in NVIDIA_MODELS.items():
        model_entry = {
            "id": model_id,
            "name": info["name"],
            "provider": info["provider"],
            "parameters": info["parameters"],
            "context_window": info["context_window"],
            "domain": info.get("domain", "general"),
            "category": info.get("category", "language"),
            "status": "available" if configured else "requires_api_key",
        }
        if "description" in info:
            model_entry["description"] = info["description"]
        models.append(model_entry)
    return models
