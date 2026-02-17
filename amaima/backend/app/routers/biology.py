from fastapi import APIRouter, Form, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/biology", tags=["biology"])


@router.post("/discover")
async def drug_discovery(
    target: str = Form(..., description="Drug target (e.g., protein, receptor)"),
    properties: str = Form(default="", description="Desired molecular properties"),
):
    from app.services.biology_service import drug_discovery as discover
    try:
        result = await discover(target, properties)
        return result
    except Exception as e:
        logger.error(f"Drug discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/protein")
async def analyze_protein(
    sequence: str = Form(..., description="Protein sequence (FASTA format)"),
    analysis_type: str = Form(default="structure", description="Analysis type: structure, function, binding"),
):
    from app.services.biology_service import protein_analysis
    try:
        result = await protein_analysis(sequence, analysis_type)
        return result
    except Exception as e:
        logger.error(f"Protein analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_molecule(
    smiles: str = Form(..., description="SMILES representation of molecule"),
    objectives: str = Form(default="improve binding affinity", description="Optimization objectives"),
):
    from app.services.biology_service import molecule_optimization
    try:
        result = await molecule_optimization(smiles, objectives)
        return result
    except Exception as e:
        logger.error(f"Molecule optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def biology_query(
    query: str = Form(..., description="General biology/chemistry query"),
    task_type: str = Form(default="general", description="Task type: general, molecule_generation, protein_analysis, drug_discovery"),
):
    from app.services.biology_service import bionemo_inference
    try:
        result = await bionemo_inference(query, task_type=task_type)
        return result
    except Exception as e:
        logger.error(f"Biology query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def biology_capabilities():
    from app.services.biology_service import BIOLOGY_CAPABILITIES
    return BIOLOGY_CAPABILITIES
