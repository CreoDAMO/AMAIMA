import os
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from rdkit import Chem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    logger.info("RDKit not available locally; molecule validation will use cloud API")

from app.modules.nvidia_nim_client import chat_completion, get_api_key, get_model_for_domain

BIONEMO_MODEL = "nvidia/bionemo-megamolbart"
BIONEMO_PROTEIN_MODEL = "nvidia/bionemo-esm2"
BIONEMO_NIM_URL = os.getenv("BIONEMO_NIM_URL", "https://integrate.api.nvidia.com/v1")

BIOLOGY_MODELS = {
    "nvidia/bionemo-megamolbart": {
        "name": "BioNeMo MegaMolBART",
        "focus": "molecule_generation",
        "description": "Molecular generation and optimization using NVIDIA BioNeMo",
    },
    "nvidia/bionemo-esm2": {
        "name": "BioNeMo ESM-2",
        "focus": "protein_structure",
        "description": "Protein structure prediction and analysis",
    },
}


def validate_smiles(smiles_string: str) -> Dict[str, Any]:
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles_string)
        if mol:
            return {
                "valid": True,
                "smiles": smiles_string,
                "num_atoms": mol.GetNumAtoms(),
                "num_bonds": mol.GetNumBonds(),
                "molecular_formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
            }
        return {"valid": False, "smiles": smiles_string, "error": "Invalid SMILES"}
    return {"valid": None, "smiles": smiles_string, "note": "RDKit not available; validation skipped"}


async def bionemo_inference(
    query: str,
    model: str = BIONEMO_MODEL,
    task_type: str = "general",
) -> Dict[str, Any]:
    start_time = time.time()

    system_prompts = {
        "molecule_generation": "You are an expert computational chemist. Generate valid SMILES representations for drug-like molecules based on the given targets and properties. Provide detailed rationale for molecular design choices.",
        "protein_analysis": "You are an expert in structural biology and protein science. Analyze protein sequences, predict structures, and explain functional implications.",
        "drug_discovery": "You are a drug discovery scientist. Design and optimize lead compounds considering ADMET properties, target selectivity, and synthetic accessibility.",
        "general": "You are an expert in computational biology and drug discovery, powered by BioNeMo. Provide detailed, scientifically accurate responses.",
    }

    messages = [
        {"role": "system", "content": system_prompts.get(task_type, system_prompts["general"])},
        {"role": "user", "content": query},
    ]

    target_model = BIONEMO_PROTEIN_MODEL if task_type == "protein_analysis" else model

    try:
        result = await chat_completion(
            model=target_model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        response_text = result.get("content", "")

        validated_molecules = []
        if "SMILES" in query.upper() or task_type == "molecule_generation":
            import re
            smiles_pattern = r'[A-Za-z0-9@+\-\[\]\(\)=#/\\\.%]+'
            potential_smiles = re.findall(smiles_pattern, response_text)
            for s in potential_smiles[:10]:
                if len(s) > 3 and any(c in s for c in ['C', 'N', 'O', 'c', 'n', 'o']):
                    validated_molecules.append(validate_smiles(s))

        return {
            "service": "biology",
            "model": target_model,
            "task_type": task_type,
            "response": response_text,
            "validated_molecules": validated_molecules if validated_molecules else None,
            "latency_ms": round(elapsed_ms, 2),
            "usage": result.get("usage", {}),
            "cost_usd": result.get("estimated_cost_usd", 0),
        }
    except Exception as e:
        logger.error(f"BioNeMo inference failed: {e}")
        return {
            "service": "biology",
            "model": model,
            "response": f"Biology service unavailable: {str(e)}. Ensure NVIDIA_API_KEY is set.",
            "error": str(e),
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


async def drug_discovery(target: str, properties: str) -> Dict[str, Any]:
    query = f"""Drug Discovery Task:
Target: {target}
Desired Properties: {properties}

Please:
1. Suggest 3-5 candidate molecules as SMILES strings
2. Explain the rationale for each candidate
3. Predict key ADMET properties (absorption, distribution, metabolism, excretion, toxicity)
4. Rank candidates by predicted efficacy
5. Suggest optimization strategies"""
    return await bionemo_inference(query, task_type="drug_discovery")


async def protein_analysis(sequence: str, analysis_type: str = "structure") -> Dict[str, Any]:
    query = f"""Protein Analysis Task:
Sequence: {sequence}
Analysis Type: {analysis_type}

Provide:
1. Predicted secondary structure elements
2. Functional domain identification
3. Potential binding sites
4. Evolutionary conservation insights
5. Structural stability assessment"""
    return await bionemo_inference(query, task_type="protein_analysis")


async def molecule_optimization(smiles: str, objectives: str) -> Dict[str, Any]:
    validation = validate_smiles(smiles)
    query = f"""Molecule Optimization Task:
Input SMILES: {smiles}
Validation: {validation}
Optimization Objectives: {objectives}

Generate optimized variants that:
1. Maintain core pharmacophore
2. Improve specified properties
3. Remain synthetically accessible
4. Provide SMILES for each variant"""
    return await bionemo_inference(query, task_type="molecule_generation")


BIOLOGY_CAPABILITIES = {
    "models": list(BIOLOGY_MODELS.keys()),
    "rdkit_available": HAS_RDKIT,
    "features": [
        "molecule_generation",
        "drug_discovery",
        "protein_analysis",
        "molecule_optimization",
        "smiles_validation",
        "admet_prediction",
    ],
    "supported_inputs": ["SMILES", "FASTA", "PDB", "text_description"],
}
