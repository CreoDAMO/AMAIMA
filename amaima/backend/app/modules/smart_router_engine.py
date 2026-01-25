import yaml
import hashlib
from typing import Dict, Any, Tuple, List

# Load configuration from YAML file
with open("amaima/backend/amaima_config.yaml", "r") as f:
    config = yaml.safe_load()

router_config = config.get("router", {})

def _calculate_complexity(query: str) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Analyzes the query to determine its complexity level.
    This is a placeholder for a more sophisticated implementation.
    """
    length = len(query)
    reasons = []
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
) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Selects the best model based on the complexity level.
    """
    model_mapping = router_config.get("model_mapping", {})
    base_level = complexity_level.replace("BORDERLINE_", "")
    model = model_mapping.get(base_level, router_config.get("default_model"))
    score = 0.9  # Placeholder score
    reasons = [
        {"code": "COST_EFFICIENT", "label": "Optimal cost/performance selected"}
    ]

    # Upscale model for borderline cases
    if "BORDERLINE" in complexity_level:
        current_index = list(model_mapping.keys()).index(base_level)
        if current_index + 1 < len(model_mapping):
            next_level = list(model_mapping.keys())[current_index + 1]
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

    # 2. Select Model
    model_fit_score, model, model_reasons = _select_model(complexity_level)

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

    decision = {
        "query_hash": hashlib.sha256(query.encode()).hexdigest(),
        "complexity_level": complexity_level,
        "model": model,
        "execution_mode": execution_mode,
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
        "simulated": simulate,
    }

    if simulate:
        decision["execution"] = "none"
        decision["confidence_scope"] = "explanatory"
    else:
        # Log the decision for non-simulation routes to the database
        from .observability_framework import log_decision_to_db
        import asyncio

        asyncio.create_task(log_decision_to_db(query, decision))

    return decision
