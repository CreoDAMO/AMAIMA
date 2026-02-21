import os
import time
import hashlib
import base64
import logging
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

FHE_ENABLED = os.getenv("FHE_ENABLED", "true").lower() == "true"

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    logger.warning("TenSEAL not available - FHE operations will be disabled")


class FHEScheme(str, Enum):
    BFV = "BFV"
    CKKS = "CKKS"


@dataclass
class FHEKeyInfo:
    key_id: str
    scheme: FHEScheme
    poly_modulus_degree: int
    created_at: float
    security_level: int = 128
    noise_budget_initial: int = 0
    public_key_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EncryptedPayload:
    payload_id: str
    scheme: FHEScheme
    key_id: str
    ciphertext_b64: str
    shape: List[int]
    created_at: float
    noise_budget: int = 0
    operations_performed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FHEEngine:
    CKKS_PARAMS = {
        "light": {
            "poly_modulus_degree": 8192,
            "coeff_mod_bit_sizes": [60, 40, 40, 60],
            "global_scale": 2**40,
        },
        "standard": {
            "poly_modulus_degree": 16384,
            "coeff_mod_bit_sizes": [60, 40, 40, 40, 40, 60],
            "global_scale": 2**40,
        },
    }

    BFV_PARAMS = {
        "light": {
            "poly_modulus_degree": 4096,
            "plain_modulus": 1032193,
        },
        "standard": {
            "poly_modulus_degree": 8192,
            "plain_modulus": 1032193,
        },
    }

    def __init__(self):
        self._contexts: Dict[str, Any] = {}
        self._key_info: Dict[str, FHEKeyInfo] = {}
        self._encrypted_store: Dict[str, Any] = {}
        self._operation_log: List[Dict[str, Any]] = []
        self._stats = {
            "contexts_created": 0,
            "encryptions": 0,
            "decryptions": 0,
            "homomorphic_ops": 0,
            "total_compute_ms": 0.0,
        }

    @property
    def available(self) -> bool:
        return TENSEAL_AVAILABLE and FHE_ENABLED

    def generate_context(
        self,
        scheme: FHEScheme = FHEScheme.CKKS,
        security_level: str = "light",
        generate_galois: bool = True,
        generate_relin: bool = True,
    ) -> Tuple[str, FHEKeyInfo]:
        if not self.available:
            raise RuntimeError("FHE engine not available")

        start = time.time()
        key_id = hashlib.sha256(f"{scheme}-{time.time()}-{os.urandom(16).hex()}".encode()).hexdigest()[:16]

        if scheme == FHEScheme.CKKS:
            params = self.CKKS_PARAMS.get(security_level, self.CKKS_PARAMS["light"])
            ctx = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=params["poly_modulus_degree"],
                coeff_mod_bit_sizes=params["coeff_mod_bit_sizes"],
            )
            ctx.global_scale = params["global_scale"]
            if generate_galois:
                ctx.generate_galois_keys()
        else:
            params = self.BFV_PARAMS.get(security_level, self.BFV_PARAMS["light"])
            ctx = ts.context(
                ts.SCHEME_TYPE.BFV,
                poly_modulus_degree=params["poly_modulus_degree"],
                plain_modulus=params["plain_modulus"],
            )

        if generate_relin:
            ctx.generate_relin_keys()

        ctx_bytes = ctx.serialize(save_secret_key=True)
        pk_hash = hashlib.sha256(ctx_bytes[:256]).hexdigest()[:12]

        info = FHEKeyInfo(
            key_id=key_id,
            scheme=scheme,
            poly_modulus_degree=params["poly_modulus_degree"],
            created_at=time.time(),
            security_level=128,
            public_key_hash=pk_hash,
            metadata={
                "security_level_name": security_level,
                "galois_keys": generate_galois,
                "relin_keys": generate_relin,
                "keygen_ms": round((time.time() - start) * 1000, 2),
                "context_size_bytes": len(ctx_bytes),
            },
        )

        self._contexts[key_id] = ctx
        self._key_info[key_id] = info
        self._stats["contexts_created"] += 1

        logger.info(f"FHE context created: {key_id} scheme={scheme} poly_degree={params['poly_modulus_degree']}")
        return key_id, info

    def _get_context(self, key_id: str):
        ctx = self._contexts.get(key_id)
        if ctx is None:
            raise ValueError(f"No FHE context found for key_id={key_id}")
        return ctx

    def encrypt_vector(self, key_id: str, values: List[float]) -> EncryptedPayload:
        if not self.available:
            raise RuntimeError("FHE engine not available")

        start = time.time()
        ctx = self._get_context(key_id)
        info = self._key_info[key_id]

        if info.scheme == FHEScheme.CKKS:
            enc = ts.ckks_vector(ctx, values)
        else:
            int_values = [int(v) for v in values]
            enc = ts.bfv_vector(ctx, int_values)

        enc_bytes = enc.serialize()
        payload_id = hashlib.sha256(f"{key_id}-{time.time()}-{len(values)}".encode()).hexdigest()[:16]

        payload = EncryptedPayload(
            payload_id=payload_id,
            scheme=info.scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[len(values)],
            created_at=time.time(),
            metadata={
                "encrypt_ms": round((time.time() - start) * 1000, 2),
                "ciphertext_size_bytes": len(enc_bytes),
                "plaintext_element_count": len(values),
                "expansion_ratio": round(len(enc_bytes) / (len(values) * 8), 1) if values else 0,
            },
        )

        self._encrypted_store[payload_id] = {"enc": enc, "size": len(values)}
        self._stats["encryptions"] += 1
        return payload

    def decrypt_vector(self, key_id: str, payload_id: str) -> List[float]:
        if not self.available:
            raise RuntimeError("FHE engine not available")

        start = time.time()
        self._get_context(key_id)
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"No encrypted payload found for payload_id={payload_id}")

        enc = stored["enc"]
        element_count = stored.get("size", 1)
        result = enc.decrypt()
        result = result[:element_count]

        self._stats["decryptions"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._log_operation("decrypt", key_id, payload_id, elapsed)
        return result

    def homomorphic_add(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        return self._binary_op("add", key_id, payload_a, payload_b)

    def homomorphic_multiply(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        return self._binary_op("multiply", key_id, payload_a, payload_b)

    def homomorphic_add_plain(self, key_id: str, payload_id: str, plain_values: List[float]) -> EncryptedPayload:
        return self._plain_op("add_plain", key_id, payload_id, plain_values)

    def homomorphic_multiply_plain(self, key_id: str, payload_id: str, plain_values: List[float]) -> EncryptedPayload:
        return self._plain_op("multiply_plain", key_id, payload_id, plain_values)

    def homomorphic_dot_product(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        start = time.time()
        stored_a = self._encrypted_store.get(payload_a)
        stored_b = self._encrypted_store.get(payload_b)
        if stored_a is None or stored_b is None:
            raise ValueError("Encrypted payloads not found")

        result = stored_a["enc"].dot(stored_b["enc"])
        result_id = hashlib.sha256(f"dot-{payload_a}-{payload_b}-{time.time()}".encode()).hexdigest()[:16]
        self._encrypted_store[result_id] = {"enc": result, "size": 1}
        self._stats["homomorphic_ops"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._stats["total_compute_ms"] += elapsed
        self._log_operation("dot_product", key_id, result_id, elapsed)

        enc_bytes = result.serialize()
        return EncryptedPayload(
            payload_id=result_id,
            scheme=self._key_info[key_id].scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[1],
            created_at=time.time(),
            operations_performed=1,
            metadata={"operation": "dot_product", "compute_ms": elapsed},
        )

    def homomorphic_negate(self, key_id: str, payload_id: str) -> EncryptedPayload:
        start = time.time()
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"Payload {payload_id} not found")

        result = -stored["enc"]
        size = stored.get("size", 1)
        result_id = hashlib.sha256(f"neg-{payload_id}-{time.time()}".encode()).hexdigest()[:16]
        self._encrypted_store[result_id] = {"enc": result, "size": size}
        self._stats["homomorphic_ops"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._stats["total_compute_ms"] += elapsed

        enc_bytes = result.serialize()
        return EncryptedPayload(
            payload_id=result_id,
            scheme=self._key_info[key_id].scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size],
            created_at=time.time(),
            operations_performed=1,
            metadata={"operation": "negate", "compute_ms": elapsed},
        )

    def homomorphic_sum(self, key_id: str, payload_id: str) -> EncryptedPayload:
        start = time.time()
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"Payload {payload_id} not found")

        result = stored["enc"].sum()
        result_id = hashlib.sha256(f"sum-{payload_id}-{time.time()}".encode()).hexdigest()[:16]
        self._encrypted_store[result_id] = {"enc": result, "size": 1}
        self._stats["homomorphic_ops"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._stats["total_compute_ms"] += elapsed

        enc_bytes = result.serialize()
        return EncryptedPayload(
            payload_id=result_id,
            scheme=self._key_info[key_id].scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[1],
            created_at=time.time(),
            operations_performed=1,
            metadata={"operation": "sum", "compute_ms": elapsed},
        )

    def _binary_op(self, op: str, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        start = time.time()
        stored_a = self._encrypted_store.get(payload_a)
        stored_b = self._encrypted_store.get(payload_b)
        if stored_a is None or stored_b is None:
            raise ValueError("Encrypted payloads not found")

        enc_a = stored_a["enc"]
        enc_b = stored_b["enc"]
        size = stored_a.get("size", 1)

        if op == "add":
            result = enc_a + enc_b
        elif op == "multiply":
            result = enc_a * enc_b
        else:
            raise ValueError(f"Unknown operation: {op}")

        result_id = hashlib.sha256(f"{op}-{payload_a}-{payload_b}-{time.time()}".encode()).hexdigest()[:16]
        self._encrypted_store[result_id] = {"enc": result, "size": size}
        self._stats["homomorphic_ops"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._stats["total_compute_ms"] += elapsed
        self._log_operation(op, key_id, result_id, elapsed)

        enc_bytes = result.serialize()
        return EncryptedPayload(
            payload_id=result_id,
            scheme=self._key_info[key_id].scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size],
            created_at=time.time(),
            operations_performed=1,
            metadata={"operation": op, "compute_ms": elapsed},
        )

    def _plain_op(self, op: str, key_id: str, payload_id: str, plain_values: List[float]) -> EncryptedPayload:
        start = time.time()
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"Payload {payload_id} not found")
        enc = stored["enc"]
        size = stored.get("size", len(plain_values))

        info = self._key_info[key_id]
        if info.scheme == FHEScheme.BFV:
            plain_values = [int(v) for v in plain_values]

        if op == "add_plain":
            result = enc + plain_values
        elif op == "multiply_plain":
            result = enc * plain_values
        else:
            raise ValueError(f"Unknown operation: {op}")

        result_id = hashlib.sha256(f"{op}-{payload_id}-{time.time()}".encode()).hexdigest()[:16]
        self._encrypted_store[result_id] = {"enc": result, "size": size}
        self._stats["homomorphic_ops"] += 1
        elapsed = round((time.time() - start) * 1000, 2)
        self._stats["total_compute_ms"] += elapsed

        enc_bytes = result.serialize()
        return EncryptedPayload(
            payload_id=result_id,
            scheme=self._key_info[key_id].scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size],
            created_at=time.time(),
            operations_performed=1,
            metadata={"operation": op, "compute_ms": elapsed},
        )

    def _log_operation(self, op: str, key_id: str, result_id: str, elapsed_ms: float):
        self._operation_log.append({
            "operation": op,
            "key_id": key_id,
            "result_id": result_id,
            "elapsed_ms": elapsed_ms,
            "timestamp": time.time(),
        })
        if len(self._operation_log) > 1000:
            self._operation_log = self._operation_log[-500:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.available,
            "tenseal_available": TENSEAL_AVAILABLE,
            "fhe_enabled_env": FHE_ENABLED,
            "active_contexts": len(self._contexts),
            "active_payloads": len(self._encrypted_store),
            "supported_schemes": [s.value for s in FHEScheme],
            "security_level_bits": 128,
            "quantum_resistant": True,
            "lattice_basis": "RLWE",
            **self._stats,
            "recent_operations": self._operation_log[-10:],
        }

    def get_key_info(self, key_id: str) -> Optional[FHEKeyInfo]:
        return self._key_info.get(key_id)

    def list_keys(self) -> List[FHEKeyInfo]:
        return list(self._key_info.values())

    def serialize_context(self, key_id: str, include_secret_key: bool = False) -> str:
        ctx = self._get_context(key_id)
        ctx_bytes = ctx.serialize(save_secret_key=include_secret_key)
        return base64.b64encode(ctx_bytes).decode()

    def cleanup_context(self, key_id: str) -> bool:
        if key_id in self._contexts:
            del self._contexts[key_id]
            payloads_to_remove = [
                pid for pid, enc in self._encrypted_store.items()
            ]
            if key_id in self._key_info:
                del self._key_info[key_id]
            return True
        return False


fhe_engine = FHEEngine()
