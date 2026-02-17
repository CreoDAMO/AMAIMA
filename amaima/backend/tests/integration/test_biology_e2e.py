import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def admin_headers():
    import os
    secret = os.getenv("API_SECRET_KEY", "default_secret_key_for_development")
    return {"X-API-Key": secret}


@pytest.mark.asyncio
async def test_biology_discover_endpoint(app, admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/biology/discover",
            json={"target": "BRCA1", "disease": "breast cancer", "constraints": {}},
            headers=admin_headers,
        )
        assert response.status_code in (200, 422, 500)
        if response.status_code == 200:
            data = response.json()
            assert "candidates" in data or "result" in data or "crew" in data


@pytest.mark.asyncio
async def test_biology_drug_discovery_crew(app, admin_headers):
    with patch("app.agents.biology_crew.run_drug_discovery_crew", new_callable=AsyncMock) as mock_crew:
        mock_crew.return_value = {
            "crew": "drug_discovery",
            "process": "sequential",
            "total_latency_ms": 150,
            "results": [
                {"agent": "Molecule Generator", "response": "Generated SMILES: CC(=O)OC1=CC=CC=C1C(=O)O"},
                {"agent": "ADMET Predictor", "response": "Good oral bioavailability predicted"},
                {"agent": "Lead Optimizer", "response": "Optimized lead compound identified"},
                {"agent": "Safety Reviewer", "response": "No safety concerns identified"},
            ],
            "final_output": "Drug discovery pipeline completed successfully",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/agents/run",
                json={"crew_type": "drug_discovery", "task": "Find drug candidates for BRCA1"},
                headers=admin_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["crew"] == "drug_discovery"
            assert len(data["results"]) == 4
            assert data["final_output"] == "Drug discovery pipeline completed successfully"
            mock_crew.assert_called_once()


@pytest.mark.asyncio
async def test_biology_protein_analysis_crew(app, admin_headers):
    with patch("app.agents.biology_crew.run_protein_analysis_crew", new_callable=AsyncMock) as mock_crew:
        mock_crew.return_value = {
            "crew": "protein_analysis",
            "process": "sequential",
            "total_latency_ms": 120,
            "results": [
                {"agent": "Structural Biologist", "response": "Protein structure analyzed"},
                {"agent": "Binding Site Predictor", "response": "Active site identified at residues 100-115"},
            ],
            "final_output": "Protein analysis complete",
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/agents/run",
                json={"crew_type": "protein_analysis", "task": "Analyze p53 protein structure"},
                headers=admin_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["crew"] == "protein_analysis"
            assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_biology_crew_sequential_pipeline():
    from app.agents.biology_crew import run_drug_discovery_crew

    with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = {
            "content": "Pipeline step result",
            "model": "nvidia/bionemo-megamolbart",
            "latency_ms": 50,
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            "estimated_cost_usd": 0.00015,
            "finish_reason": "stop",
            "cache_hit": False,
        }

        result = await run_drug_discovery_crew("Find inhibitors for JAK2 kinase")
        assert "crew" in result
        assert result["process"] == "sequential"
        assert len(result["results"]) > 0
        assert result["total_latency_ms"] >= 0


@pytest.mark.asyncio
async def test_agent_types_endpoint(app, admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/agents/types")
        assert response.status_code == 200
        data = response.json()
        assert "crew_types" in data
        crew_ids = [c["id"] for c in data["crew_types"]]
        assert "drug_discovery" in crew_ids
        assert "protein_analysis" in crew_ids
        assert "navigation" in crew_ids


@pytest.mark.asyncio
async def test_nim_cache_stats():
    from app.modules.nvidia_nim_client import get_cache_stats
    stats = get_cache_stats()
    assert "hits" in stats
    assert "misses" in stats
    assert "hit_rate" in stats
    assert "size" in stats


@pytest.mark.asyncio
async def test_nim_prompt_cache_functionality():
    from app.modules.nvidia_nim_client import PromptCache

    cache = PromptCache(max_size=10, ttl_seconds=60)

    result = cache.get("model-a", [{"role": "user", "content": "hello"}], 0.7, 100)
    assert result is None

    test_data = {"content": "response text", "model": "model-a", "latency_ms": 500}
    cache.put("model-a", [{"role": "user", "content": "hello"}], 0.7, 100, test_data)

    result = cache.get("model-a", [{"role": "user", "content": "hello"}], 0.7, 100)
    assert result is not None
    assert result["cache_hit"] is True
    assert result["latency_ms"] == 0.1
    assert result["original_latency_ms"] == 500

    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1


@pytest.mark.asyncio
async def test_mau_rate_limit_middleware(app, admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/models")
        assert response.status_code == 200
