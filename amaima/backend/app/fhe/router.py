import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.fhe.engine import fhe_engine, FHEScheme
from app.fhe.service import fhe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/fhe", tags=["FHE - Fully Homomorphic Encryption"])


class KeygenRequest(BaseModel):
    scheme: str = Field(default="CKKS", description="FHE scheme: CKKS (real numbers) or BFV (integers)")
    security_level: str = Field(default="light", description="Security preset: light or standard")
    generate_galois_keys: bool = Field(default=True, description="Generate Galois keys for rotations")
    generate_relin_keys: bool = Field(default=True, description="Generate relinearization keys")


class EncryptRequest(BaseModel):
    key_id: str = Field(..., description="FHE context key ID from keygen")
    values: List[float] = Field(..., description="Values to encrypt")


class ComputeRequest(BaseModel):
    key_id: str = Field(..., description="FHE context key ID")
    operation: str = Field(..., description="Operation: add, multiply, dot_product, add_plain, multiply_plain, negate, sum")
    payload_a: str = Field(..., description="First encrypted payload ID")
    payload_b: Optional[str] = Field(default=None, description="Second encrypted payload ID (for binary ops)")
    plain_values: Optional[List[float]] = Field(default=None, description="Plaintext values for plain ops")


class DecryptRequest(BaseModel):
    key_id: str = Field(..., description="FHE context key ID")
    payload_id: str = Field(..., description="Encrypted payload ID to decrypt")


class DrugScoringRequest(BaseModel):
    qed_values: List[float] = Field(..., description="QED drug-likeness scores")
    plogp_values: List[float] = Field(..., description="Penalized logP values")
    weights: Optional[List[float]] = Field(default=None, description="QED weights (default 0.6)")


class SimilaritySearchRequest(BaseModel):
    query_embedding: List[float] = Field(..., description="Query vector")
    candidate_embeddings: List[List[float]] = Field(..., description="Candidate vectors to compare")


class SecureAggregationRequest(BaseModel):
    datasets: List[List[float]] = Field(..., description="Multiple datasets to aggregate privately")


class VectorArithmeticRequest(BaseModel):
    vector_a: List[float] = Field(..., description="First vector")
    vector_b: List[float] = Field(..., description="Second vector")
    operations: List[str] = Field(default=["add", "multiply", "dot_product"], description="Operations to perform")
    scheme: str = Field(default="CKKS", description="FHE scheme: CKKS or BFV")


class SecureVoteRequest(BaseModel):
    votes: List[int] = Field(..., description="Vote values (candidate indices)")
    num_candidates: int = Field(..., description="Number of candidates")


def _check_fhe():
    from app.fhe.engine import TENSEAL_AVAILABLE, FHE_ENABLED
    if not fhe_engine.available:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "FHE engine not available",
                "tenseal_installed": TENSEAL_AVAILABLE,
                "fhe_enabled": FHE_ENABLED,
                "message": "Set FHE_ENABLED=true and install tenseal to activate homomorphic encryption",
            },
        )


@router.get("/status")
async def fhe_status():
    return {
        "subsystem": "AMAIMA FHE (Fully Homomorphic Encryption)",
        "version": "1.0.0",
        "cryptographic_backend": "Microsoft SEAL (via TenSEAL)",
        "lattice_basis": "Ring Learning With Errors (RLWE)",
        "post_quantum_secure": True,
        "security_level_bits": 128,
        "supported_schemes": {
            "CKKS": {
                "description": "Approximate arithmetic on real/complex numbers",
                "use_cases": ["Encrypted ML inference", "Secure embeddings", "Private scoring"],
                "poly_modulus_degrees": [8192, 16384],
            },
            "BFV": {
                "description": "Exact arithmetic on integers",
                "use_cases": ["Secure voting", "Private counting", "Encrypted databases"],
                "poly_modulus_degrees": [4096, 8192],
            },
        },
        "supported_operations": [
            "encrypt", "decrypt",
            "homomorphic_add", "homomorphic_multiply",
            "homomorphic_dot_product", "homomorphic_negate", "homomorphic_sum",
            "add_plain", "multiply_plain",
        ],
        "high_level_services": [
            "encrypted_drug_scoring",
            "encrypted_similarity_search",
            "encrypted_secure_aggregation",
            "encrypted_vector_arithmetic",
            "encrypted_secure_vote",
        ],
        "engine_stats": fhe_engine.get_stats(),
    }


@router.post("/keygen")
async def generate_keys(req: KeygenRequest):
    _check_fhe()
    try:
        scheme = FHEScheme(req.scheme)
        key_id, info = fhe_engine.generate_context(
            scheme=scheme,
            security_level=req.security_level,
            generate_galois=req.generate_galois_keys,
            generate_relin=req.generate_relin_keys,
        )
        return {
            "key_id": key_id,
            "scheme": info.scheme.value,
            "poly_modulus_degree": info.poly_modulus_degree,
            "security_level_bits": info.security_level,
            "public_key_hash": info.public_key_hash,
            "quantum_resistant": True,
            "metadata": info.metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encrypt")
async def encrypt_data(req: EncryptRequest):
    _check_fhe()
    try:
        payload = fhe_engine.encrypt_vector(req.key_id, req.values)
        return {
            "payload_id": payload.payload_id,
            "scheme": payload.scheme.value,
            "key_id": payload.key_id,
            "shape": payload.shape,
            "ciphertext_preview": payload.ciphertext_b64[:80] + "...",
            "ciphertext_size_bytes": payload.metadata.get("ciphertext_size_bytes", 0),
            "expansion_ratio": payload.metadata.get("expansion_ratio", 0),
            "encrypt_ms": payload.metadata.get("encrypt_ms", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compute")
async def homomorphic_compute(req: ComputeRequest):
    _check_fhe()
    try:
        if req.operation == "add":
            if not req.payload_b:
                raise ValueError("payload_b required for add")
            result = fhe_engine.homomorphic_add(req.key_id, req.payload_a, req.payload_b)
        elif req.operation == "multiply":
            if not req.payload_b:
                raise ValueError("payload_b required for multiply")
            result = fhe_engine.homomorphic_multiply(req.key_id, req.payload_a, req.payload_b)
        elif req.operation == "dot_product":
            if not req.payload_b:
                raise ValueError("payload_b required for dot_product")
            result = fhe_engine.homomorphic_dot_product(req.key_id, req.payload_a, req.payload_b)
        elif req.operation == "add_plain":
            if not req.plain_values:
                raise ValueError("plain_values required for add_plain")
            result = fhe_engine.homomorphic_add_plain(req.key_id, req.payload_a, req.plain_values)
        elif req.operation == "multiply_plain":
            if not req.plain_values:
                raise ValueError("plain_values required for multiply_plain")
            result = fhe_engine.homomorphic_multiply_plain(req.key_id, req.payload_a, req.plain_values)
        elif req.operation == "negate":
            result = fhe_engine.homomorphic_negate(req.key_id, req.payload_a)
        elif req.operation == "sum":
            result = fhe_engine.homomorphic_sum(req.key_id, req.payload_a)
        else:
            raise ValueError(f"Unknown operation: {req.operation}")

        return {
            "result_payload_id": result.payload_id,
            "operation": req.operation,
            "scheme": result.scheme.value,
            "computed_on_encrypted_data": True,
            "no_decryption_required": True,
            "compute_ms": result.metadata.get("compute_ms", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decrypt")
async def decrypt_data(req: DecryptRequest):
    _check_fhe()
    try:
        values = fhe_engine.decrypt_vector(req.key_id, req.payload_id)
        return {
            "values": [round(v, 8) for v in values],
            "element_count": len(values),
            "key_id": req.key_id,
            "payload_id": req.payload_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/keys")
async def list_keys():
    _check_fhe()
    keys = fhe_engine.list_keys()
    return {
        "active_keys": [
            {
                "key_id": k.key_id,
                "scheme": k.scheme.value,
                "poly_modulus_degree": k.poly_modulus_degree,
                "security_level_bits": k.security_level,
                "public_key_hash": k.public_key_hash,
                "created_at": k.created_at,
            }
            for k in keys
        ],
        "total": len(keys),
    }


@router.post("/drug-scoring")
async def encrypted_drug_scoring(req: DrugScoringRequest):
    _check_fhe()
    try:
        result = fhe_service.encrypted_drug_scoring(
            qed_values=req.qed_values,
            plogp_values=req.plogp_values,
            weights=req.weights,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity-search")
async def encrypted_similarity_search(req: SimilaritySearchRequest):
    _check_fhe()
    try:
        result = fhe_service.encrypted_similarity_search(
            query_embedding=req.query_embedding,
            candidate_embeddings=req.candidate_embeddings,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/secure-aggregation")
async def encrypted_secure_aggregation(req: SecureAggregationRequest):
    _check_fhe()
    try:
        result = fhe_service.encrypted_secure_aggregation(datasets=req.datasets)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector-arithmetic")
async def encrypted_vector_arithmetic(req: VectorArithmeticRequest):
    _check_fhe()
    try:
        scheme = FHEScheme(req.scheme)
        result = fhe_service.encrypted_vector_arithmetic(
            vector_a=req.vector_a,
            vector_b=req.vector_b,
            operations=req.operations,
            scheme=scheme,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/secure-vote")
async def encrypted_secure_vote(req: SecureVoteRequest):
    _check_fhe()
    try:
        result = fhe_service.encrypted_secure_vote(
            votes=req.votes,
            num_candidates=req.num_candidates,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo")
async def run_fhe_demo():
    _check_fhe()
    try:
        result = fhe_service.run_comprehensive_demo()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
