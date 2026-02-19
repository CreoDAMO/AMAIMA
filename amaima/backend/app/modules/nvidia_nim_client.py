import os
import hashlib
import json
import httpx
import logging
import time
from collections import OrderedDict
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PromptCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 600):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, model: str, messages: list, temperature: float, max_tokens: int) -> str:
        raw = json.dumps({"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, model: str, messages: list, temperature: float, max_tokens: int) -> Optional[Dict[str, Any]]:
        key = self._make_key(model, messages, temperature, max_tokens)
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if time.time() - entry["ts"] > self._ttl:
            self._cache.pop(key, None)
            self._misses += 1
            return None
        self._hits += 1
        self._cache.move_to_end(key)
        result = entry["data"].copy()
        result["cache_hit"] = True
        result["original_latency_ms"] = result.get("latency_ms", 0)
        result["latency_ms"] = 0.1
        return result

    def put(self, model: str, messages: list, temperature: float, max_tokens: int, data: Dict[str, Any]) -> None:
        key = self._make_key(model, messages, temperature, max_tokens)
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[key] = {"ts": time.time(), "data": data}

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0,
            "estimated_latency_savings_pct": round(self._hits / total * 25, 1) if total > 0 else 0,
        }

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0


_prompt_cache = PromptCache()

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


_NVIDIA_KEY_NAMES = [
    "NVIDIA_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "NIM_API_KEY",
    "NGC_API_KEY",
]

_RENDER_SECRETS_DIRS = ["/etc/secrets", "/app/etc/secrets"]


def _read_secret_file(name: str) -> Optional[str]:
    for secrets_dir in _RENDER_SECRETS_DIRS:
        path = os.path.join(secrets_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    val = f.read().strip()
                if val:
                    return val
            except Exception:
                pass
    return None


def get_api_key() -> Optional[str]:
    for name in _NVIDIA_KEY_NAMES:
        val = os.environ.get(name)
        if val:
            return val
    for name in _NVIDIA_KEY_NAMES:
        val = _read_secret_file(name)
        if val:
            return val
    return None


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
    use_cache: bool = True,
) -> Dict[str, Any]:
    if use_cache:
        cached = _prompt_cache.get(model, messages, temperature, max_tokens)
        if cached:
            logger.info(f"NIM cache hit for model={model}")
            return cached

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

    result = {
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
        "cache_hit": False,
    }

    if use_cache:
        _prompt_cache.put(model, messages, temperature, max_tokens, result)

    return result


async def chat_completion_stream(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
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
        "stream": True,
    }

    start_time = time.time()
    total_tokens = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{NVIDIA_NIM_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise RuntimeError(f"NVIDIA NIM API returned {response.status_code}: {body.decode()}")

            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        if line == "data: [DONE]":
                            elapsed_ms = (time.time() - start_time) * 1000
                            yield {
                                "event": "done",
                                "data": {
                                    "model": model,
                                    "total_tokens": total_tokens,
                                    "latency_ms": round(elapsed_ms, 2),
                                },
                            }
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                finish_reason = choices[0].get("finish_reason")
                                if content:
                                    total_tokens += 1
                                    yield {
                                        "event": "token",
                                        "data": {"content": content, "index": total_tokens},
                                    }
                                if finish_reason:
                                    yield {
                                        "event": "finish",
                                        "data": {"finish_reason": finish_reason},
                                    }
                        except json.JSONDecodeError:
                            continue


def get_cache_stats() -> Dict[str, Any]:
    return _prompt_cache.stats()


def clear_cache() -> None:
    _prompt_cache.clear()


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
