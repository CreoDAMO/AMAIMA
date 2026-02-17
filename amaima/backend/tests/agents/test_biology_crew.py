import pytest
from unittest.mock import AsyncMock, patch
from app.agents.biology_crew import (
    run_drug_discovery_crew,
    run_protein_analysis_crew,
    MOLECULE_GENERATOR,
    ADMET_PREDICTOR,
    LEAD_OPTIMIZER,
    SAFETY_REVIEWER,
)


@pytest.fixture
def mock_chat_completion():
    with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
        mock.return_value = {"content": "Generated molecule: CC(=O)Oc1ccccc1C(=O)O"}
        yield mock


class TestBiologyAgentRoles:
    def test_molecule_generator(self):
        assert MOLECULE_GENERATOR.name == "Molecule Generator"
        assert "drug-like molecules" in MOLECULE_GENERATOR.goal
        assert MOLECULE_GENERATOR.model == "meta/llama-3.1-70b-instruct"

    def test_admet_predictor(self):
        assert ADMET_PREDICTOR.name == "ADMET Predictor"
        assert "ADMET" in ADMET_PREDICTOR.goal

    def test_lead_optimizer(self):
        assert LEAD_OPTIMIZER.name == "Lead Optimizer"
        assert "efficacy" in LEAD_OPTIMIZER.goal

    def test_safety_reviewer(self):
        assert SAFETY_REVIEWER.name == "Safety Reviewer"
        assert SAFETY_REVIEWER.model == "meta/llama-3.1-8b-instruct"


class TestDrugDiscoveryCrew:
    @pytest.mark.asyncio
    async def test_run_drug_discovery_crew(self, mock_chat_completion):
        result = await run_drug_discovery_crew(
            "EGFR kinase",
            properties="high selectivity, low toxicity"
        )
        assert result["crew"] == "Drug Discovery Crew"
        assert result["process"] == "sequential"
        assert len(result["results"]) == 4
        expected_agents = ["Molecule Generator", "ADMET Predictor", "Lead Optimizer", "Safety Reviewer"]
        assert result["agents_used"] == expected_agents
        assert "final_output" in result
        assert result["total_latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_drug_discovery_default_properties(self, mock_chat_completion):
        result = await run_drug_discovery_crew("CDK4/6 inhibitor")
        assert result["crew"] == "Drug Discovery Crew"
        assert len(result["results"]) == 4

    @pytest.mark.asyncio
    async def test_drug_discovery_error_handling(self):
        with patch("app.agents.crew_manager.chat_completion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("NIM API unavailable")
            result = await run_drug_discovery_crew("test target")
            assert any("error" in r for r in result["results"])


class TestProteinAnalysisCrew:
    @pytest.mark.asyncio
    async def test_run_protein_analysis_crew(self, mock_chat_completion):
        result = await run_protein_analysis_crew("MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQQIAATGFHIIPGAFEPFYEPFQILPTY")
        assert result["crew"] == "Protein Analysis Crew"
        assert result["process"] == "sequential"
        assert len(result["results"]) == 2
        expected_agents = ["Structural Biologist", "Binding Site Predictor"]
        assert result["agents_used"] == expected_agents

    @pytest.mark.asyncio
    async def test_protein_analysis_short_sequence(self, mock_chat_completion):
        result = await run_protein_analysis_crew("ACDEFGH")
        assert result["crew"] == "Protein Analysis Crew"
        assert "final_output" in result
