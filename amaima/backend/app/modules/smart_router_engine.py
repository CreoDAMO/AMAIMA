def calculate_execution_fit(query: str, length: int, patterns: list) -> tuple[float, str, list[dict]]:
    domain_real_time = any(term in query.lower() for term in ['real-time', 'trading']) or 'trading' in patterns
    interaction_real_time = any(term in query.lower() for term in ['step-by-step', 'live'])

    if domain_real_time and not interaction_real_time:
        mode = "batch_parallel"
        score = 0.88
        rationale = [{"code": "DOMAIN_REAL_TIME", "label": "domain context requires batch efficiency"}]
    elif interaction_real_time:
        mode = "streaming_real_time"
        score = 0.95
        rationale = [{"code": "INTERACTION_REAL_TIME", "label": "user intent for live response"}]
    else:
        mode = "parallel_min_latency"
        score = 0.80
        rationale = [{"code": "DEFAULT_OPTIMAL", "label": "balanced latency minimization"}]

    return score, mode, rationale

# In route_query (add to return dict)
execution_fit_score, execution_mode, execution_rationale = calculate_execution_fit(query, len(query), patterns)
result['execution_mode'] = execution_mode
result['execution_fit'] = round(execution_fit_score, 2)
result['reasons']['execution_reason'] = execution_rationale
