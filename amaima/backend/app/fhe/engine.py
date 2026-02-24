"""
AMAIMA FHE Engine v2
amaima/backend/app/fhe/engine.py

Bugs fixed vs v1:
  BUG 1 FIXED  cleanup_context() was a no-op that never deleted payloads → OOM leak
               Now uses per-key payload index for O(1) scoped deletion
  BUG 2 FIXED  generate_context() ran full keygen on every request (~200-600ms)
               Now backed by a singleton _ContextPool; pool hit ≈ 0ms
  BUG 3 FIXED  CKKS params: 'standard' used N=16384 (2x cost, unnecessary for depth≤4)
               New profiles: light=depth3/N=8192, standard=depth4/N=8192, deep=depth6/N=16384
  BUG 4 FIXED  No SEAL threading hints; NTT ran single-threaded
               Now reads SEAL_THREADS env var and sets OMP_NUM_THREADS accordingly
  BUG 5 FIXED  serialize(save_secret_key=True) serialised the private key just to hash it
               Now uses save_secret_key=False for the pk_hash derivation
  BUG 6 FIXED  _encrypted_store was an unbounded dict → grew forever
               Replaced with _LRUPayloadStore (default cap: 512 entries)

Expected latency improvement on existing CPU hardware, no Dockerfile changes:
  Context creation overhead:  200-600ms → ~0ms   (pool hit)
  Per-operation FHE:          ~500ms    → ~300ms  (N=8192 instead of N=16384)
  Combined on drug_scoring:   ~1,100ms  → ~350ms  (estimate, benchmark with parameter_bench.py)
"""

import os
import time
import hashlib
import base64
import logging
import threading
from collections import OrderedDict
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Environment ───────────────────────────────────────────────────────────────
FHE_ENABLED = os.getenv("FHE_ENABLED", "true").lower() == "true"

# Hint the SEAL C++ layer to parallelise NTT across cores.
# Set SEAL_THREADS=N in env; defaults to all available CPUs.
_seal_threads = int(os.getenv("SEAL_THREADS", str(os.cpu_count() or 4)))
os.environ.setdefault("OMP_NUM_THREADS", str(_seal_threads))

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
    logger.info(f"TenSEAL loaded — SEAL_THREADS={_seal_threads}")
except ImportError:
    TENSEAL_AVAILABLE = False
    logger.warning("TenSEAL not available — FHE operations will be disabled")


# ── Data classes (unchanged public API) ──────────────────────────────────────

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


# ── LRU payload store (BUG 6 fix) ────────────────────────────────────────────

_MAX_PAYLOADS = int(os.getenv("FHE_MAX_PAYLOADS", "512"))


class _LRUPayloadStore:
    """
    Thread-safe LRU dict for in-process ciphertext objects.
    Evicts the oldest entry when maxsize is exceeded, preventing unbounded growth.
    """

    def __init__(self, maxsize: int = _MAX_PAYLOADS):
        self._store: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._maxsize = maxsize

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            if len(self._store) > self._maxsize:
                evicted_key, _ = self._store.popitem(last=False)
                logger.debug(f"FHE LRU evicted payload {evicted_key}")

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            self._store.move_to_end(key)
            return self._store[key]

    def delete_many(self, keys: List[str]) -> int:
        removed = 0
        with self._lock:
            for k in keys:
                if k in self._store:
                    del self._store[k]
                    removed += 1
        return removed

    def __len__(self) -> int:
        return len(self._store)


# ── Singleton context pool (BUG 2 fix) ───────────────────────────────────────

class _ContextPool:
    """
    Maintains one warm TenSEAL context per (scheme, security_level) combination.

    Context creation (keygen + Galois keys + relin keys) costs 200–600 ms.
    In v1 this ran on *every* call to generate_context().
    Here it runs exactly once per combination for the lifetime of the process.

    Thread-safe. After warm(), contexts are read-only — TenSEAL operations on
    the same context object are safe to run from multiple threads concurrently.
    """

    def __init__(self):
        self._pool: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self.warmed = False

    @staticmethod
    def _pool_key(scheme: FHEScheme, level: str) -> str:
        return f"{scheme.value}:{level}"

    def _build(self, scheme: FHEScheme, level: str) -> Any:
        t0 = time.perf_counter()
        if scheme == FHEScheme.CKKS:
            p = FHEEngine.CKKS_PARAMS.get(level, FHEEngine.CKKS_PARAMS["standard"])
            ctx = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=p["poly_modulus_degree"],
                coeff_mod_bit_sizes=p["coeff_mod_bit_sizes"],
            )
            ctx.global_scale = p["global_scale"]
            ctx.generate_galois_keys()
            ctx.generate_relin_keys()
        else:
            p = FHEEngine.BFV_PARAMS.get(level, FHEEngine.BFV_PARAMS["standard"])
            ctx = ts.context(
                ts.SCHEME_TYPE.BFV,
                poly_modulus_degree=p["poly_modulus_degree"],
                plain_modulus=p["plain_modulus"],
            )
            ctx.generate_relin_keys()
        ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(f"FHE pool: built {scheme.value}/{level} in {ms}ms "
                    f"(N={p['poly_modulus_degree']})")
        return ctx

    def get(self, scheme: FHEScheme, level: str) -> Any:
        """Return warm context; builds lazily on first access."""
        if not TENSEAL_AVAILABLE:
            raise RuntimeError("TenSEAL not available")
        pk = self._pool_key(scheme, level)
        with self._lock:
            if pk not in self._pool:
                self._pool[pk] = self._build(scheme, level)
            return self._pool[pk]

    def warm_all(self) -> None:
        """Pre-build all standard contexts. Call from FastAPI startup_event."""
        if not TENSEAL_AVAILABLE:
            return
        for level in ("light", "standard"):
            self.get(FHEScheme.CKKS, level)
        for level in ("light", "standard"):
            self.get(FHEScheme.BFV, level)
        self.warmed = True
        logger.info("FHE context pool fully warmed — subsequent keygen calls cost ~0ms")


# Module-level singleton shared by all FHEEngine instances
_context_pool = _ContextPool()


# ── FHEEngine ─────────────────────────────────────────────────────────────────

class FHEEngine:
    """
    Homomorphic encryption engine for AMAIMA.
    All public methods preserve the same signature as v1 — drop-in replacement.
    """

    # BUG 3 FIX: depth-matched CKKS profiles
    # Rule: use the smallest N that supports your circuit depth.
    # Drug scoring pipeline: 2 multiplications → depth 2, N=8192 is sufficient.
    # N=16384 (v1 "standard") doubles every operation cost with no security benefit.
    CKKS_PARAMS = {
        "light": {                              # depth=3, drug scoring / embeddings
            "poly_modulus_degree": 8192,
            "coeff_mod_bit_sizes": [60, 40, 40, 40, 60],
            "global_scale": 2 ** 40,
        },
        "standard": {                           # depth=4, deeper pipelines
            "poly_modulus_degree": 8192,
            "coeff_mod_bit_sizes": [60, 40, 40, 40, 40, 60],
            "global_scale": 2 ** 40,
        },
        "deep": {                               # depth=6, AlphaFold2 / multi-layer
            "poly_modulus_degree": 16384,
            "coeff_mod_bit_sizes": [60, 40, 40, 40, 40, 40, 40, 60],
            "global_scale": 2 ** 40,
        },
    }

    BFV_PARAMS = {
        "light":    {"poly_modulus_degree": 4096, "plain_modulus": 1032193},
        "standard": {"poly_modulus_degree": 8192, "plain_modulus": 1032193},
    }

    def __init__(self):
        self._key_info: Dict[str, FHEKeyInfo] = {}
        # BUG 1 FIX: per-key payload index enables O(1) scoped cleanup
        self._key_payloads: Dict[str, set] = {}
        # BUG 6 FIX: bounded LRU store replaces unbounded dict
        self._encrypted_store = _LRUPayloadStore()
        self._operation_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._stats = {
            "contexts_created": 0,
            "pool_hits": 0,
            "encryptions": 0,
            "decryptions": 0,
            "homomorphic_ops": 0,
            "total_compute_ms": 0.0,
        }

    @property
    def available(self) -> bool:
        return TENSEAL_AVAILABLE and FHE_ENABLED

    def warm_pool(self) -> None:
        """Pre-warm all contexts. Call from FastAPI startup_event."""
        _context_pool.warm_all()

    # ── Context lifecycle ─────────────────────────────────────────────────────

    def generate_context(
        self,
        scheme: FHEScheme = FHEScheme.CKKS,
        security_level: str = "light",
        generate_galois: bool = True,
        generate_relin: bool = True,
    ) -> Tuple[str, FHEKeyInfo]:
        """
        BUG 2 FIX: returns a logical key_id backed by a pooled context.
        Keygen cost is ~0ms on pool hit; ~200-600ms only on the very first call
        per (scheme, security_level) combination for the process lifetime.
        """
        if not self.available:
            raise RuntimeError("FHE engine not available")

        t0 = time.perf_counter()
        ctx = _context_pool.get(scheme, security_level)   # ~0ms after first warm
        pool_ms = round((time.perf_counter() - t0) * 1000, 2)

        key_id = hashlib.sha256(
            f"{scheme}-{security_level}-{time.time()}-{os.urandom(8).hex()}".encode()
        ).hexdigest()[:16]

        param_map = self.CKKS_PARAMS if scheme == FHEScheme.CKKS else self.BFV_PARAMS
        params = param_map.get(security_level, param_map[
            "standard" if "standard" in param_map else next(iter(param_map))
        ])

        # BUG 5 FIX: save_secret_key=False — no need to serialise the private key
        pk_hash = hashlib.sha256(
            ctx.serialize(save_secret_key=False)[:256]
        ).hexdigest()[:12]

        info = FHEKeyInfo(
            key_id=key_id,
            scheme=scheme,
            poly_modulus_degree=params["poly_modulus_degree"],
            created_at=time.time(),
            security_level=128,
            public_key_hash=pk_hash,
            metadata={
                "security_level_name": security_level,
                "pool_hit_ms": pool_ms,
                "keygen_ms": 0 if pool_ms < 5 else round(pool_ms, 2),
                "pooled": True,
                "galois_keys": generate_galois,
                "relin_keys": generate_relin,
            },
        )

        with self._lock:
            self._key_info[key_id] = info
            self._key_payloads[key_id] = set()
            self._stats["contexts_created"] += 1
            if pool_ms < 5:
                self._stats["pool_hits"] += 1

        logger.debug(f"generate_context key={key_id} scheme={scheme} "
                     f"level={security_level} pool_ms={pool_ms:.1f}")
        return key_id, info

    def _get_context(self, key_id: str) -> Any:
        info = self._key_info.get(key_id)
        if info is None:
            raise ValueError(f"No FHE context for key_id={key_id}")
        level = info.metadata.get("security_level_name", "light")
        return _context_pool.get(info.scheme, level)

    def cleanup_context(self, key_id: str) -> bool:
        """
        BUG 1 FIX: v1 built payloads_to_remove from ALL store entries but never
        filtered by key_id and never called delete — so nothing was ever freed.

        v2 uses the per-key payload index to delete ONLY payloads owned by this
        key_id in O(len(owned_payloads)) time.
        """
        with self._lock:
            if key_id not in self._key_info:
                return False
            owned = list(self._key_payloads.get(key_id, set()))

        removed = self._encrypted_store.delete_many(owned)

        with self._lock:
            self._key_info.pop(key_id, None)
            self._key_payloads.pop(key_id, None)

        logger.debug(f"cleanup_context {key_id}: freed {removed}/{len(owned)} payloads")
        return True

    # ── Encrypt / Decrypt ─────────────────────────────────────────────────────

    def encrypt_vector(self, key_id: str, values: List[float]) -> EncryptedPayload:
        if not self.available:
            raise RuntimeError("FHE engine not available")

        t0 = time.perf_counter()
        ctx = self._get_context(key_id)
        info = self._key_info[key_id]

        enc = (ts.ckks_vector(ctx, values) if info.scheme == FHEScheme.CKKS
               else ts.bfv_vector(ctx, [int(v) for v in values]))

        enc_bytes = enc.serialize()
        pid = hashlib.sha256(
            f"{key_id}-{time.time()}-{len(values)}-{os.urandom(4).hex()}".encode()
        ).hexdigest()[:16]
        elapsed = round((time.perf_counter() - t0) * 1000, 2)

        payload = EncryptedPayload(
            payload_id=pid,
            scheme=info.scheme,
            key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[len(values)],
            created_at=time.time(),
            metadata={
                "encrypt_ms": elapsed,
                "ciphertext_size_bytes": len(enc_bytes),
                "plaintext_element_count": len(values),
                "expansion_ratio": round(len(enc_bytes) / (len(values) * 8), 1) if values else 0,
            },
        )

        self._encrypted_store.put(pid, {"enc": enc, "size": len(values)})
        with self._lock:
            if key_id in self._key_payloads:
                self._key_payloads[key_id].add(pid)
            self._stats["encryptions"] += 1

        return payload

    def decrypt_vector(self, key_id: str, payload_id: str) -> List[float]:
        if not self.available:
            raise RuntimeError("FHE engine not available")

        t0 = time.perf_counter()
        # Validate key still exists (doesn't need ctx for decrypt in TenSEAL)
        if key_id not in self._key_info:
            raise ValueError(f"No FHE context for key_id={key_id}")

        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"No encrypted payload for payload_id={payload_id}")

        result = stored["enc"].decrypt()
        result = result[:stored.get("size", len(result))]

        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        with self._lock:
            self._stats["decryptions"] += 1
        self._log_operation("decrypt", key_id, payload_id, elapsed)
        return result

    # ── Homomorphic operations (public API unchanged) ─────────────────────────

    def homomorphic_add(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        return self._binary_op("add", key_id, payload_a, payload_b)

    def homomorphic_multiply(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        return self._binary_op("multiply", key_id, payload_a, payload_b)

    def homomorphic_dot_product(self, key_id: str, payload_a: str, payload_b: str) -> EncryptedPayload:
        return self._binary_op("dot_product", key_id, payload_a, payload_b)

    def homomorphic_add_plain(self, key_id: str, payload_id: str, plain_values: List[float]) -> EncryptedPayload:
        return self._plain_op("add_plain", key_id, payload_id, plain_values)

    def homomorphic_multiply_plain(self, key_id: str, payload_id: str, plain_values: List[float]) -> EncryptedPayload:
        return self._plain_op("multiply_plain", key_id, payload_id, plain_values)

    def homomorphic_negate(self, key_id: str, payload_id: str) -> EncryptedPayload:
        t0 = time.perf_counter()
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"Payload {payload_id} not found")
        result = -stored["enc"]
        size = stored.get("size", 1)
        rid = self._new_pid("neg", payload_id)
        enc_bytes = result.serialize()
        self._encrypted_store.put(rid, {"enc": result, "size": size})
        self._register_payload(key_id, rid)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        self._record_stats(elapsed)
        self._log_operation("negate", key_id, rid, elapsed)
        return EncryptedPayload(
            payload_id=rid, scheme=self._key_info[key_id].scheme, key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size], created_at=time.time(), operations_performed=1,
            metadata={"operation": "negate", "compute_ms": elapsed},
        )

    def homomorphic_sum(self, key_id: str, payload_id: str) -> EncryptedPayload:
        t0 = time.perf_counter()
        stored = self._encrypted_store.get(payload_id)
        if stored is None:
            raise ValueError(f"Payload {payload_id} not found")
        result = stored["enc"].sum()
        rid = self._new_pid("sum", payload_id)
        enc_bytes = result.serialize()
        self._encrypted_store.put(rid, {"enc": result, "size": 1})
        self._register_payload(key_id, rid)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        self._record_stats(elapsed)
        self._log_operation("sum", key_id, rid, elapsed)
        return EncryptedPayload(
            payload_id=rid, scheme=self._key_info[key_id].scheme, key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[1], created_at=time.time(), operations_performed=1,
            metadata={"operation": "sum", "compute_ms": elapsed},
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _binary_op(self, op: str, key_id: str, pa: str, pb: str) -> EncryptedPayload:
        t0 = time.perf_counter()
        sa = self._encrypted_store.get(pa)
        sb = self._encrypted_store.get(pb)
        if sa is None or sb is None:
            raise ValueError(f"Encrypted payloads not found: {pa!r}, {pb!r}")

        ea, eb = sa["enc"], sb["enc"]
        size = sa.get("size", 1)

        if op == "add":
            result = ea + eb
        elif op == "multiply":
            result = ea * eb
        elif op == "dot_product":
            result = ea.dot(eb)
            size = 1
        else:
            raise ValueError(f"Unknown binary op: {op!r}")

        rid = self._new_pid(op, pa, pb)
        enc_bytes = result.serialize()
        self._encrypted_store.put(rid, {"enc": result, "size": size})
        self._register_payload(key_id, rid)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        self._record_stats(elapsed)
        self._log_operation(op, key_id, rid, elapsed)
        return EncryptedPayload(
            payload_id=rid, scheme=self._key_info[key_id].scheme, key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size], created_at=time.time(), operations_performed=1,
            metadata={"operation": op, "compute_ms": elapsed},
        )

    def _plain_op(self, op: str, key_id: str, pid: str, plain_values: List[float]) -> EncryptedPayload:
        t0 = time.perf_counter()
        stored = self._encrypted_store.get(pid)
        if stored is None:
            raise ValueError(f"Payload {pid!r} not found")
        enc = stored["enc"]
        size = stored.get("size", len(plain_values))
        info = self._key_info[key_id]
        if info.scheme == FHEScheme.BFV:
            plain_values = [int(v) for v in plain_values]
        result = (enc + plain_values) if op == "add_plain" else (enc * plain_values)
        rid = self._new_pid(op, pid)
        enc_bytes = result.serialize()
        self._encrypted_store.put(rid, {"enc": result, "size": size})
        self._register_payload(key_id, rid)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        self._record_stats(elapsed)
        return EncryptedPayload(
            payload_id=rid, scheme=info.scheme, key_id=key_id,
            ciphertext_b64=base64.b64encode(enc_bytes).decode(),
            shape=[size], created_at=time.time(), operations_performed=1,
            metadata={"operation": op, "compute_ms": elapsed},
        )

    def _new_pid(self, op: str, *parts: str) -> str:
        raw = f"{op}-{''.join(parts)}-{time.time()}-{os.urandom(4).hex()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _register_payload(self, key_id: str, pid: str) -> None:
        with self._lock:
            if key_id in self._key_payloads:
                self._key_payloads[key_id].add(pid)

    def _record_stats(self, elapsed_ms: float) -> None:
        with self._lock:
            self._stats["homomorphic_ops"] += 1
            self._stats["total_compute_ms"] += elapsed_ms

    def _log_operation(self, op: str, key_id: str, result_id: str, elapsed_ms: float) -> None:
        self._operation_log.append({
            "operation": op, "key_id": key_id,
            "result_id": result_id, "elapsed_ms": elapsed_ms,
            "timestamp": time.time(),
        })
        if len(self._operation_log) > 1000:
            self._operation_log = self._operation_log[-500:]

    # ── Introspection ─────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = dict(self._stats)
        return {
            "enabled": self.available,
            "tenseal_available": TENSEAL_AVAILABLE,
            "fhe_enabled_env": FHE_ENABLED,
            "active_contexts": len(self._key_info),
            "active_payloads": len(self._encrypted_store),
            "payload_store_cap": _MAX_PAYLOADS,
            "supported_schemes": [s.value for s in FHEScheme],
            "security_level_bits": 128,
            "quantum_resistant": True,
            "lattice_basis": "RLWE",
            "seal_threads": _seal_threads,
            "pool_warmed": _context_pool.warmed,
            **stats,
            "recent_operations": self._operation_log[-10:],
        }

    def get_key_info(self, key_id: str) -> Optional[FHEKeyInfo]:
        return self._key_info.get(key_id)

    def list_keys(self) -> List[FHEKeyInfo]:
        return list(self._key_info.values())

    def serialize_context(self, key_id: str, include_secret_key: bool = False) -> str:
        ctx = self._get_context(key_id)
        return base64.b64encode(ctx.serialize(save_secret_key=include_secret_key)).decode()


# Module-level singleton — import this everywhere
fhe_engine = FHEEngine()
