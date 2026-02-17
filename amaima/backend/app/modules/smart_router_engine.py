import yaml
import hashlib
import os
from typing import Dict, Any, Tuple, List

# Load configuration from YAML file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "amaima_config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

router_config = config.get("router", {})

BIOLOGY_KEYWORDS = [
    "drug", "protein", "molecule", "smiles", "fasta", "dna", "rna",
    "enzyme", "receptor", "binding", "pharmacophore", "admet",
    "molecular", "compound", "peptide", "genome", "mutation",
    "bionemo", "drug discovery", "lead optimization",
]

ROBOTICS_KEYWORDS = [
    "robot", "navigate", "navigation", "manipulate", "grasp",
    "autonomous", "slam", "path planning", "ros", "ros2",
    "actuator", "sensor", "lidar", "swarm", "drone",
    "humanoid", "amr", "isaac", "simulation", "kinematics",
]

VISION_KEYWORDS = [
    "image", "video", "visual", "scene", "camera", "detect",
    "object detection", "segmentation", "depth", "3d",
    "cosmos", "embodied", "spatial", "temporal",
    "recognize", "classify image", "analyze video",
]


def detect_domain(query: str) -> Tuple[str, float]:
    q_lower = query.lower()

    biology_score = sum(1 for kw in BIOLOGY_KEYWORDS if kw in q_lower)
    robotics_score = sum(1 for kw in ROBOTICS_KEYWORDS if kw in q_lower)
    vision_score = sum(1 for kw in VISION_KEYWORDS if kw in q_lower)

    scores = {
        "biology": biology_score,
        "robotics": robotics_score,
        "vision": vision_score,
        "general": 0,
    }

    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]

    if best_score == 0:
        return "general", 0.0

    confidence = min(best_score / 3.0, 1.0)
    return best_domain, confidence


def _calculate_complexity(query: str) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Analyzes the query to determine its complexity level.
    Includes domain-specific classification for biology, robotics, and vision.
    """
    length = len(query)
    reasons = []

    domain, domain_confidence = detect_domain(query)
    if domain != "general":
        reasons.append({"code": f"DOMAIN_{domain.upper()}", "label": f"Domain detected: {domain} (confidence: {domain_confidence:.2f})"})

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

    # Check for borderline cases
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
    Domain-specific queries route to specialized models when confidence is high enough.
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
        rationale = [
            {
                "code": "DOMAIN_REAL_TIME",
                "label": "Domain context requires batch efficiency",
            }
        ]
    elif interaction_real_time:
        mode = "streaming_real_time"
        score = 0.95
        rationale = [
            {"code": "INTERACTION_REAL_TIME", "label": "User intent for live response"}
        ]
    else:
        mode = "parallel_min_latency"
        score = 0.80
        rationale = [
            {"code": "DEFAULT_OPTIMAL", "label": "Balanced latency minimization"}
        ]

    return score, mode, rationale


def route_query(query: str, simulate: bool = False) -> Dict[str, Any]:
    """
    Routes a query to the most appropriate AI model.
    """
    # 1. Calculate Complexity
    complexity_score, complexity_level, complexity_reasons = _calculate_complexity(query)

    # 2. Detect Domain
    domain, domain_confidence = detect_domain(query)

    # 3. Select Model (domain-aware)
    model_fit_score, model, model_reasons = _select_model(complexity_level, domain, domain_confidence)

    # 3. Determine Execution Fit
    execution_fit_score, execution_mode, execution_reasons = calculate_execution_fit(
        query, len(query), []
    )

    # 4. Calculate Weighted Confidence
    weights = router_config.get("confidence_weights", {"complexity": 0.4, "model_fit": 0.35, "execution_fit": 0.25})
    overall_confidence = (
        (complexity_score * weights["complexity"])
        + (model_fit_score * weights["model_fit"])
        + (execution_fit_score * weights["execution_fit"])
    )

    # Production Safeguard Toggle
    execution_mode_env = os.getenv('AMAIMA_EXECUTION_MODE', 'decision-only')
    execution_mode_active = execution_mode_env == 'execution-enabled'

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
        "simulated": simulate or not execution_mode_active,
        "execution_mode_active": execution_mode_active,
        "decision_schema_version": "1.1.0"
    }

    if decision["simulated"]:
        decision["execution"] = "none"
        decision["confidence_scope"] = "explanatory"
        decision["output"] = "Simulation only - no execution." if not execution_mode_active else None
    else:
        # Log the decision for non-simulation routes to the database
        from .observability_framework import log_decision_to_db
        import asyncio

        asyncio.create_task(log_decision_to_db(query, decision))

    return decision
