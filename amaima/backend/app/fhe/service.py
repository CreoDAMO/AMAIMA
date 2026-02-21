import time
import logging
import math
from typing import Dict, List, Any, Optional, Tuple

from app.fhe.engine import fhe_engine, FHEScheme, EncryptedPayload

logger = logging.getLogger(__name__)


class FHEService:

    def __init__(self):
        self.engine = fhe_engine

    def encrypted_drug_scoring(
        self,
        qed_values: List[float],
        plogp_values: List[float],
        weights: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        start = time.time()

        if weights is None:
            weights = [0.6] * len(qed_values)
            plogp_weights = [0.4] * len(plogp_values)
        else:
            plogp_weights = [1.0 - w for w in weights]

        key_id, key_info = self.engine.generate_context(FHEScheme.CKKS, "light")

        enc_qed = self.engine.encrypt_vector(key_id, qed_values)
        enc_plogp = self.engine.encrypt_vector(key_id, plogp_values)

        weighted_qed = self.engine.homomorphic_multiply_plain(key_id, enc_qed.payload_id, weights)
        weighted_plogp = self.engine.homomorphic_multiply_plain(key_id, enc_plogp.payload_id, plogp_weights)

        combined = self.engine.homomorphic_add(key_id, weighted_qed.payload_id, weighted_plogp.payload_id)

        decrypted_scores = self.engine.decrypt_vector(key_id, combined.payload_id)
        decrypted_scores = decrypted_scores[:len(qed_values)]

        elapsed = round((time.time() - start) * 1000, 2)
        self.engine.cleanup_context(key_id)

        return {
            "operation": "encrypted_drug_scoring",
            "scheme": "CKKS",
            "security_level": "128-bit (RLWE lattice)",
            "quantum_resistant": True,
            "molecule_count": len(qed_values),
            "composite_scores": [round(s, 6) for s in decrypted_scores],
            "best_molecule_index": int(max(range(len(decrypted_scores)), key=lambda i: decrypted_scores[i])),
            "best_score": round(max(decrypted_scores), 6),
            "operations_performed": {
                "encryptions": 2,
                "homomorphic_multiplications": 2,
                "homomorphic_additions": 1,
                "decryptions": 1,
            },
            "total_latency_ms": elapsed,
            "privacy_guarantee": "Computation performed entirely on RLWE ciphertexts using homomorphic operations",
        }

    def encrypted_similarity_search(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
    ) -> Dict[str, Any]:
        start = time.time()

        key_id, key_info = self.engine.generate_context(FHEScheme.CKKS, "light")

        enc_query = self.engine.encrypt_vector(key_id, query_embedding)

        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            enc_candidate = self.engine.encrypt_vector(key_id, candidate)
            dot_result = self.engine.homomorphic_dot_product(
                key_id, enc_query.payload_id, enc_candidate.payload_id
            )
            score = self.engine.decrypt_vector(key_id, dot_result.payload_id)
            similarities.append({
                "candidate_index": i,
                "similarity_score": round(score[0], 6),
            })

        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)

        elapsed = round((time.time() - start) * 1000, 2)
        self.engine.cleanup_context(key_id)

        return {
            "operation": "encrypted_similarity_search",
            "scheme": "CKKS",
            "security_level": "128-bit (RLWE lattice)",
            "quantum_resistant": True,
            "query_dimension": len(query_embedding),
            "candidates_searched": len(candidate_embeddings),
            "results": similarities,
            "best_match_index": similarities[0]["candidate_index"] if similarities else -1,
            "total_latency_ms": elapsed,
            "privacy_guarantee": "Dot products computed homomorphically on encrypted embeddings without plaintext access",
        }

    def encrypted_secure_aggregation(
        self,
        datasets: List[List[float]],
    ) -> Dict[str, Any]:
        start = time.time()

        key_id, key_info = self.engine.generate_context(FHEScheme.CKKS, "light")

        max_len = max(len(d) for d in datasets)
        padded = [d + [0.0] * (max_len - len(d)) for d in datasets]

        encrypted_datasets = []
        for dataset in padded:
            enc = self.engine.encrypt_vector(key_id, dataset)
            encrypted_datasets.append(enc)

        current = encrypted_datasets[0]
        for i in range(1, len(encrypted_datasets)):
            current = self.engine.homomorphic_add(
                key_id, current.payload_id, encrypted_datasets[i].payload_id
            )

        n = len(datasets)
        scale_factor = [1.0 / n] * max_len
        averaged = self.engine.homomorphic_multiply_plain(key_id, current.payload_id, scale_factor)

        decrypted_avg = self.engine.decrypt_vector(key_id, averaged.payload_id)
        decrypted_avg = decrypted_avg[:max_len]

        elapsed = round((time.time() - start) * 1000, 2)
        self.engine.cleanup_context(key_id)

        return {
            "operation": "encrypted_secure_aggregation",
            "scheme": "CKKS",
            "security_level": "128-bit (RLWE lattice)",
            "quantum_resistant": True,
            "num_participants": len(datasets),
            "vector_dimension": max_len,
            "aggregated_mean": [round(v, 6) for v in decrypted_avg],
            "operations_performed": {
                "encryptions": len(datasets),
                "homomorphic_additions": len(datasets) - 1,
                "homomorphic_multiplications": 1,
                "decryptions": 1,
            },
            "total_latency_ms": elapsed,
            "privacy_guarantee": "Aggregation computed on encrypted datasets; individual values never accessed in plaintext",
        }

    def encrypted_vector_arithmetic(
        self,
        vector_a: List[float],
        vector_b: List[float],
        operations: List[str],
        scheme: FHEScheme = FHEScheme.CKKS,
    ) -> Dict[str, Any]:
        start = time.time()

        key_id, key_info = self.engine.generate_context(scheme, "light")

        enc_a = self.engine.encrypt_vector(key_id, vector_a)
        enc_b = self.engine.encrypt_vector(key_id, vector_b)

        results = {}
        for op in operations:
            if op == "add":
                r = self.engine.homomorphic_add(key_id, enc_a.payload_id, enc_b.payload_id)
                dec = self.engine.decrypt_vector(key_id, r.payload_id)
                results["add"] = [round(v, 6) for v in dec[:len(vector_a)]]
            elif op == "multiply":
                r = self.engine.homomorphic_multiply(key_id, enc_a.payload_id, enc_b.payload_id)
                dec = self.engine.decrypt_vector(key_id, r.payload_id)
                results["multiply"] = [round(v, 6) for v in dec[:len(vector_a)]]
            elif op == "dot_product":
                r = self.engine.homomorphic_dot_product(key_id, enc_a.payload_id, enc_b.payload_id)
                dec = self.engine.decrypt_vector(key_id, r.payload_id)
                results["dot_product"] = round(dec[0], 6)
            elif op == "negate_a":
                r = self.engine.homomorphic_negate(key_id, enc_a.payload_id)
                dec = self.engine.decrypt_vector(key_id, r.payload_id)
                results["negate_a"] = [round(v, 6) for v in dec[:len(vector_a)]]

        elapsed = round((time.time() - start) * 1000, 2)
        self.engine.cleanup_context(key_id)

        plaintext_verification = {}
        for op in operations:
            if op == "add":
                plaintext_verification["add"] = [round(a + b, 6) for a, b in zip(vector_a, vector_b)]
            elif op == "multiply":
                plaintext_verification["multiply"] = [round(a * b, 6) for a, b in zip(vector_a, vector_b)]
            elif op == "dot_product":
                plaintext_verification["dot_product"] = round(sum(a * b for a, b in zip(vector_a, vector_b)), 6)
            elif op == "negate_a":
                plaintext_verification["negate_a"] = [round(-a, 6) for a in vector_a]

        return {
            "operation": "encrypted_vector_arithmetic",
            "scheme": scheme.value,
            "security_level": "128-bit (RLWE lattice)",
            "quantum_resistant": True,
            "vector_dimension": len(vector_a),
            "encrypted_results": results,
            "plaintext_verification": plaintext_verification,
            "operations_performed": operations,
            "total_latency_ms": elapsed,
            "privacy_guarantee": "All arithmetic performed on RLWE lattice ciphertexts via homomorphic evaluation",
        }

    def encrypted_secure_vote(
        self,
        votes: List[int],
        num_candidates: int,
    ) -> Dict[str, Any]:
        start = time.time()

        key_id, key_info = self.engine.generate_context(FHEScheme.BFV, "light")

        vote_vectors = []
        for vote in votes:
            v = [0] * num_candidates
            if 0 <= vote < num_candidates:
                v[vote] = 1
            vote_vectors.append(v)

        encrypted_votes = []
        for vv in vote_vectors:
            enc = self.engine.encrypt_vector(key_id, [float(x) for x in vv])
            encrypted_votes.append(enc)

        current = encrypted_votes[0]
        for i in range(1, len(encrypted_votes)):
            current = self.engine.homomorphic_add(
                key_id, current.payload_id, encrypted_votes[i].payload_id
            )

        tallies = self.engine.decrypt_vector(key_id, current.payload_id)
        tallies = tallies[:num_candidates]

        elapsed = round((time.time() - start) * 1000, 2)
        self.engine.cleanup_context(key_id)

        return {
            "operation": "encrypted_secure_vote",
            "scheme": "BFV",
            "security_level": "128-bit (RLWE lattice)",
            "quantum_resistant": True,
            "total_voters": len(votes),
            "num_candidates": num_candidates,
            "tallies": {f"candidate_{i}": int(t) for i, t in enumerate(tallies)},
            "winner": f"candidate_{int(max(range(len(tallies)), key=lambda i: tallies[i]))}",
            "operations_performed": {
                "encryptions": len(votes),
                "homomorphic_additions": len(votes) - 1,
                "decryptions": 1,
            },
            "total_latency_ms": elapsed,
            "privacy_guarantee": "Vote tallying performed via homomorphic addition on BFV ciphertexts",
        }

    def run_comprehensive_demo(self) -> Dict[str, Any]:
        start = time.time()
        results = {}

        results["ckks_arithmetic"] = self.encrypted_vector_arithmetic(
            vector_a=[1.5, 2.7, 3.14, 4.0],
            vector_b=[0.5, 1.3, 2.86, 6.0],
            operations=["add", "multiply", "dot_product", "negate_a"],
            scheme=FHEScheme.CKKS,
        )

        results["bfv_voting"] = self.encrypted_secure_vote(
            votes=[0, 1, 2, 0, 1, 0, 2, 1, 0, 0],
            num_candidates=3,
        )

        results["drug_scoring"] = self.encrypted_drug_scoring(
            qed_values=[0.82, 0.75, 0.91, 0.68],
            plogp_values=[0.45, 0.62, 0.38, 0.71],
        )

        results["similarity_search"] = self.encrypted_similarity_search(
            query_embedding=[0.1, 0.5, 0.3, 0.8],
            candidate_embeddings=[
                [0.2, 0.4, 0.3, 0.7],
                [0.9, 0.1, 0.2, 0.1],
                [0.15, 0.55, 0.28, 0.85],
            ],
        )

        results["secure_aggregation"] = self.encrypted_secure_aggregation(
            datasets=[
                [10.0, 20.0, 30.0],
                [15.0, 25.0, 35.0],
                [12.0, 22.0, 32.0],
            ],
        )

        total_elapsed = round((time.time() - start) * 1000, 2)

        return {
            "demo_name": "AMAIMA FHE Comprehensive Demo",
            "description": "Real fully homomorphic encryption using Microsoft SEAL via TenSEAL",
            "cryptographic_foundation": {
                "lattice_problem": "Ring Learning With Errors (RLWE)",
                "security_level": "128-bit post-quantum",
                "quantum_resistant": True,
                "schemes_demonstrated": ["CKKS (approximate real arithmetic)", "BFV (exact integer arithmetic)"],
                "key_properties": [
                    "Computations on encrypted data without decryption",
                    "Based on worst-case lattice hardness assumptions",
                    "Resistant to known quantum attacks (Shor, Grover)",
                    "IND-CPA secure under RLWE assumption",
                ],
            },
            "demos": results,
            "total_latency_ms": total_elapsed,
            "engine_stats": self.engine.get_stats(),
        }


fhe_service = FHEService()
