import yaml
import hashlib
import os
import re
from typing import Dict, Any, Tuple, List

# Load configuration from YAML file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "amaima_config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

router_config = config.get("router", {})

# ─────────────────────────────────────────────────────────────────────────────
# Keyword lists
# Priority-ordered: IMAGE_GEN and SPEECH are checked FIRST (before complexity
# scoring) because they must route to specialized services, not LLMs.
# ─────────────────────────────────────────────────────────────────────────────

# These patterns must trigger image_gen routing unconditionally.
IMAGE_GEN_PATTERNS = [
    r"\bgenerate\s+(an?\s+)?image\b",
    r"\bcreate\s+(an?\s+)?image\b",
    r"\bdraw\s+(an?\s+)?(me\s+)?(a|an)?\b",
    r"\brender\s+(an?\s+)?image\b",
    r"\btext.?to.?image\b",
    r"\bsdxl\b",
    r"\bstable\s+diffusion\b",
    r"\bpaint\s+(me\s+)?(a|an)\b",
    r"\bcreate\s+(a\s+)?picture\b",
    r"\bgenerate\s+(a\s+)?picture\b",
    r"\bvisualize\s+(this|a|an)\b",
    r"\bmake\s+(an?\s+)?image\b",
    r"\billustrate\b",
]

# These patterns must trigger speech/audio routing unconditionally.
SPEECH_PATTERNS = [
    r"\btext.?to.?speech\b",
    r"\bconvert\s+.{0,30}to\s+speech\b",
    r"\bspeak\s+(this|the|aloud)\b",
    r"\bread\s+aloud\b",
    r"\bnarrate\b",
    r"\bsynthesize\s+(voice|speech|audio)\b",
    r"\btts\b",
    r"\briva\s+tts\b",
    r"\bgenerate\s+(a\s+)?voice\b",
    r"\baudio\s+synthesis\b",
    r"\btranscribe\b",
    r"\bspeech.?to.?text\b",
    r"\basr\b",
    r"\bdictate\b",
    r"\brecognize\s+speech\b",
]

BIOLOGY_KEYWORDS = [
    "drug", "protein", "molecule", "smiles", "fasta", "dna", "rna",
    "enzyme", "receptor", "binding", "pharmacophore", "admet",
    "molecular", "compound", "peptide", "genome", "mutation",
    "bionemo", "drug discovery", "lead optimization",
    "folding", "alphafold", "structure prediction", "amino acid",
    "genmol", "molecule generation", "fragment", "scaffold",
    "qed", "docking", "ligand", "diffdock",
]

ROBOTICS_KEYWORDS = [
    "robot", "navigate", "navigation", "manipulate", "grasp",
    "autonomous", "slam", "path planning", "ros", "ros2",
    "actuator", "sensor", "lidar", "swarm", "drone",
    "humanoid", "amr", "isaac", "kinematics",
    "pick and place", "assembly", "grasping", "manipulation",
    "tool use", "industrial robot", "cumotion", "foundationpose",
]

VISION_KEYWORDS = [
    "analyze this image", "analyze the image", "describe this image",
    "what is in the image", "what do you see", "identify objects",
    "video analysis", "scene understanding", "object detection",
    "segmentation", "depth", "cosmos", "embodied", "spatial",
    "recognize", "classify image", "analyze video",
    "camera feed", "visual analysis",
]

SPEECH_KEYWORDS = [
    "speech", "voice", "audio", "transcribe", "transcription",
    "speak", "tts", "text to speech", "speech to text",
    "asr", "dictation", "microphone", "recording",
    "pronunciation", "synthesize voice", "riva",
]

AGENT_BUILDER_KEYWORDS = [
    "agent builder", "create workflow", "build agent", "workflow automation",
    "agent crew", "multi-agent", "orchestrate agents", "design workflow",
    "agent pipeline", "crew manager", "visual agent",
]

FHE_KEYWORDS = [
    "encrypted", "encrypt", "private", "privacy", "confidential",
    "homomorphic", "fhe", "secure computation", "zero trust",
    "classified", "sensitive", "protected", "ciphertext",
    "lattice", "rlwe", "post-quantum", "quantum resistant",
]


def _match_patterns(query: str, patterns: List[str]) -> bool:
    """Returns True if any regex pattern matches the query (case-insensitive)."""
    q_lower = query.lower()
    return any(re.search(p, q_lower) for p in patterns)


def detect_privacy_intent(query: str) -> bool:
    q_lower = query.lower()
    return any(kw in q_lower for kw in FHE_KEYWORDS)


def detect_domain(query: str) -> Tuple[str, float]:
    """
    Domain detection — IMAGE_GEN and SPEECH are checked via regex FIRST.
    If either matches, we return immediately with confidence 1.0.
    This ensures the smart router never falls through to a general LLM
    for these specialized service domains.
    """
    # ── Priority 1: Image Generation ─────────────────────────────────────────
    if _match_patterns(query, IMAGE_GEN_PATTERNS):
        return "image_gen", 1.0

    # ── Priority 2: Speech / Audio ────────────────────────────────────────────
    if _match_patterns(query, SPEECH_PATTERNS):
        return "speech", 1.0

    # ── Priority 3: Keyword-scored domains ───────────────────────────────────
    q_lower = query.lower()

    biology_score = sum(1 for kw in BIOLOGY_KEYWORDS if kw in q_lower)
    robotics_score = sum(1 for kw in ROBOTICS_KEYWORDS if kw in q_lower)
    vision_score = sum(1 for kw in VISION_KEYWORDS if kw in q_lower)
    speech_score = sum(1 for kw in SPEECH_KEYWORDS if kw in q_lower)
    agent_builder_score = sum(1 for kw in AGENT_BUILDER_KEYWORDS if kw in q_lower)

    scores = {
        "biology": biology_score,
        "robotics": robotics_score,
        "vision": vision_score,
        "speech": speech_score,
        "agent_builder": agent_builder_score,
        "general": 0,
    }

    best_domain = max(scores, key=lambda k: scores[k])
    best_score = scores[best_domain]

    if best_score == 0:
        return "general", 0.0

    confidence = min(best_score / 3.0, 1.0)
    return best_domain, confidence


def _calculate_complexity(query: str) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Analyzes the query to determine its complexity level.
    NOTE: Domain detection has already been resolved before this runs,
    so this function is only called for general/LLM-bound queries.
    """
    length = len(query)
    reasons = []

    domain, domain_confidence = detect_domain(query)
    if domain != "general":
        reasons.append({
            "code": f"DOMAIN_{domain.upper()}",
            "label": f"Domain detected: {domain} (confidence: {domain_confidence:.2f})"
        })

    if length > 100 or "architecture" in query or "trade-offs" in query:
        level = "EXPERT"
        score = 0.95
        reasons.append({"code": "TECHNICAL_DEPTH", "label": "High technical depth detected"})
    elif length > 50 or "python" in query or "function" in query:
        level = "ADVANCED"
        score = 0.85
        reasons.append({"code": "MULTI_STEP_LOGIC", "label": "Multi-step logic required"})
    else:
        level = "SIMPLE"
        score = 0.5
        reasons.append({"code": "GENERAL_QUERY", "label": "General query detected"})

    thresholds = router_config.get("borderline_threshold", [0.8, 0.9])
    if thresholds[0] <= score < thresholds[1]:
        level = f"BORDERLINE_{level}"

    return score, level, reasons


def _select_model(
    complexity_level: str,
    domain: str = "general",
    domain_confidence: float = 0.0,
) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Selects the best model based on complexity level and detected domain.
    For image_gen and speech domains, this is never called — those are
    handled directly in route_query() before model selection.
    """
    from app.modules.nvidia_nim_client import DOMAIN_TO_MODELS

    model_mapping = router_config.get("model_mapping", {})
    base_level = complexity_level.replace("BORDERLINE_", "")
    reasons = []

    if domain != "general" and domain_confidence >= 0.3:
        domain_models = DOMAIN_TO_MODELS.get(domain, {})
        model = domain_models.get("primary", model_mapping.get(base_level, router_config.get("default_model")))
        score = 0.95
        reasons.append({"code": "DOMAIN_ROUTED", "label": f"Routed to specialized {domain} model: {model}"})
    else:
        model = model_mapping.get(base_level, router_config.get("default_model"))
        score = 0.9
        reasons.append({"code": "COST_EFFICIENT", "label": "Optimal cost/performance selected"})

    if "BORDERLINE" in complexity_level:
        current_index = list(model_mapping.keys()).index(base_level)
        if current_index + 1 < len(model_mapping):
            next_level = list(model_mapping.keys())[current_index + 1]
            if domain == "general" or domain_confidence < 0.3:
                model = model_mapping[next_level]
            reasons.append(
                {"code": "BORDERLINE_UPSCALE", "label": "Upscaled model due to borderline complexity"}
            )

    return score, model, reasons


def calculate_execution_fit(
    query: str, length: int, patterns: list
) -> Tuple[float, str, List[Dict[str, str]]]:
    domain_real_time = (
        any(term in query.lower() for term in ["real-time", "trading"])
        or "trading" in patterns
    )
    interaction_real_time = any(
        term in query.lower() for term in ["step-by-step", "live"]
    )

    if domain_real_time and not interaction_real_time:
        mode = "batch_parallel"
        score = 0.88
        rationale = [{"code": "DOMAIN_REAL_TIME", "label": "Domain context requires batch efficiency"}]
    elif interaction_real_time:
        mode = "streaming_real_time"
        score = 0.95
        rationale = [{"code": "INTERACTION_REAL_TIME", "label": "User intent for live response"}]
    else:
        mode = "streaming"
        score = 0.80
        rationale = [{"code": "DEFAULT_OPTIMAL", "label": "Balanced latency minimization"}]

    return score, mode, rationale


def route_query(query: str, simulate: bool = False) -> Dict[str, Any]:
    """
    Routes a query to the most appropriate AI model or service.

    Execution order:
      1. Domain detection — IMAGE_GEN and SPEECH exit early with confidence 1.0
      2. If general domain: complexity scoring → model selection
      3. FHE intent detection (orthogonal — any domain can require FHE)
      4. Execution fit
      5. Decision assembly — NO simulation fallback in production
    """

    # ── Step 1: Domain detection (runs BEFORE complexity scoring) ─────────────
    domain, domain_confidence = detect_domain(query)

    # ── Step 2: Complexity + model selection (skipped for specialized domains) ─
    if domain in ("image_gen", "speech"):
        # These domains dispatch to dedicated services, not LLMs.
        # Set synthetic complexity/model values for the decision record.
        complexity_score, complexity_level = 0.9, "DOMAIN_SERVICE"
        complexity_reasons = [{"code": f"DOMAIN_{domain.upper()}", "label": f"Direct dispatch to {domain} service"}]
        from app.modules.nvidia_nim_client import DOMAIN_TO_MODELS
        domain_models = DOMAIN_TO_MODELS.get(domain, {})
        model = domain_models.get("primary", "nvidia/sdxl-turbo" if domain == "image_gen" else "nvidia/magpie-tts-multilingual")
        model_fit_score = 1.0
        model_reasons = [{"code": "SERVICE_DISPATCH", "label": f"Dispatching directly to {domain} service: {model}"}]
    else:
        complexity_score, complexity_level, complexity_reasons = _calculate_complexity(query)
        model_fit_score, model, model_reasons = _select_model(complexity_level, domain, domain_confidence)

    # ── Step 3: FHE intent (orthogonal — any query may require privacy) ────────
    privacy_required = detect_privacy_intent(query)
    if privacy_required:
        model_reasons.append({"code": "FHE_PRIVACY", "label": "Privacy intent detected — FHE encryption available"})

    # ── Step 4: Execution fit ─────────────────────────────────────────────────
    execution_fit_score, execution_mode, execution_reasons = calculate_execution_fit(query, len(query), [])

    # ── Step 5: Weighted confidence ───────────────────────────────────────────
    weights = router_config.get("confidence_weights", {"complexity": 0.4, "model_fit": 0.35, "execution_fit": 0.25})
    overall_confidence = (
        (complexity_score * weights["complexity"])
        + (model_fit_score * weights["model_fit"])
        + (execution_fit_score * weights["execution_fit"])
    )

    # ── Step 6: Execution mode guard ──────────────────────────────────────────
    # PRODUCTION NOTE: AMAIMA_EXECUTION_MODE must be set to 'execution-enabled'
    # in the environment. If it is not set, queries will not execute and you
    # will see "No response received". There is NO silent simulation fallback —
    # a missing env var raises a clear error so misconfiguration is visible.
    execution_mode_env = os.getenv("AMAIMA_EXECUTION_MODE", "")
    if execution_mode_env != "execution-enabled":
        raise EnvironmentError(
            "AMAIMA_EXECUTION_MODE is not set to 'execution-enabled'. "
            "Set this environment variable to enable real AI execution. "
            "Simulation mode has been removed from production routing."
        )

    decision = {
        "query_hash": hashlib.sha256(query.encode()).hexdigest(),
        "complexity_level": complexity_level,
        "model": model,
        "execution_mode": execution_mode,
        "domain": domain,
        "domain_confidence": round(domain_confidence, 2),
        "confidence": {
            "complexity": round(complexity_score, 2),
            "model_fit": round(model_fit_score, 2),
            "execution_fit": round(execution_fit_score, 2),
            "overall": round(overall_confidence, 2),
        },
        "reasons": {
            "complexity_reason": complexity_reasons,
            "model_reason": model_reasons,
            "execution_reason": execution_reasons,
        },
        "privacy_required": privacy_required,
        "fhe_available": True,
        "simulated": False,
        "execution_mode_active": True,
        "decision_schema_version": "2.0.0",
    }

    # Log the decision to the database
    from .observability_framework import log_decision_to_db
    import asyncio
    asyncio.create_task(log_decision_to_db(query, decision))

    return decision
