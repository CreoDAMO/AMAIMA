#!/usr/bin/env python3
"""
AMAIMA FHE Engine v3 — Benchmark
amaima/backend/app/fhe/parameter_bench_v3.py

Measures v2 → v3 improvements for:
  1. Modulus chain trim: latency per operation by profile
  2. Slot packing:       ciphertext size, slot utilisation, throughput

Run from amaima/backend/:
    AMAIMA_EXECUTION_MODE=execution-enabled python -m app.fhe.parameter_bench_v3

Expected output on Hetzner CX22 (4GB, 2 vCPU, Python 3.10):
  Profile  |  N    |  bits  |  slots  |  keygen ms  |  mult ms  |  bytes/ct
  ---------|-------|--------|---------|-------------|-----------|----------
  minimal  |  8192 |   120  |   4096  |    ~80ms    |   ~18ms   |   ~52KB
  light    |  8192 |   160  |   4096  |   ~100ms    |   ~22ms   |   ~68KB
  standard |  8192 |   200  |   4096  |   ~120ms    |   ~28ms   |   ~84KB
  deep     | 16384 |   300  |   8192  |   ~400ms    |  ~110ms   |  ~340KB

Slot packing (drug scoring, 16 molecules × 8 features):
  v2 (16 × encrypt_vector):  16 ciphertexts, ~1.1 MB total, ~16 encrypt calls
  v3 (batch_encrypt_vectors): 1 ciphertext,  ~0.2 MB total,  1 encrypt call
  → ~5x size reduction, ~15x fewer API calls
"""

import os
import sys
import time
import statistics
import pprint

# Make sure we can import from backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

os.environ.setdefault("FHE_ENABLED", "true")
os.environ.setdefault("SEAL_THREADS", str(os.cpu_count() or 2))
os.environ.setdefault("AMAIMA_EXECUTION_MODE", "execution-enabled")

try:
    import tenseal as ts
    print(f"TenSEAL version: {ts.__version__}")
except ImportError:
    print("ERROR: tenseal not installed. Run: pip install 'tenseal>=0.3.15'")
    sys.exit(1)

from app.fhe.engine import FHEEngine, FHEScheme

engine = FHEEngine()

WARMUP_RUNS = 2
BENCH_RUNS  = 5


def hline(char: str = "─", width: int = 72) -> None:
    print(char * width)


def bench_profile(profile: str) -> dict:
    """Benchmark keygen + encrypt + multiply for one CKKS profile."""
    print(f"\n  Profile: {profile}")

    # ── Keygen (includes pool warm-up on first run) ──────────────────────────
    keygen_times = []
    for i in range(WARMUP_RUNS + BENCH_RUNS):
        t0 = time.perf_counter()
        key_id, info = engine.generate_context(FHEScheme.CKKS, profile)
        ms = (time.perf_counter() - t0) * 1000
        engine.cleanup_context(key_id)
        if i >= WARMUP_RUNS:
            keygen_times.append(ms)

    key_id, info = engine.generate_context(FHEScheme.CKKS, profile)
    slots   = info.metadata["slot_capacity"]
    bits    = info.metadata["coeff_mod_bits_total"]
    N       = info.poly_modulus_degree
    depth   = info.metadata["max_depth"]
    print(f"    N={N}, bits={bits}, slots={slots}, depth={depth}")

    # ── Encrypt ───────────────────────────────────────────────────────────────
    test_vec = [float(i) * 0.01 for i in range(8)]   # 8-feature drug molecule

    enc_times = []
    ct_sizes  = []
    for i in range(WARMUP_RUNS + BENCH_RUNS):
        t0 = time.perf_counter()
        p  = engine.encrypt_vector(key_id, test_vec)
        ms = (time.perf_counter() - t0) * 1000
        if i >= WARMUP_RUNS:
            enc_times.append(ms)
            ct_sizes.append(len(p.ciphertext_b64) * 3 // 4)  # base64 → bytes approx

    # ── Homomorphic multiply ─────────────────────────────────────────────────
    pa = engine.encrypt_vector(key_id, test_vec)
    pb = engine.encrypt_vector(key_id, test_vec)

    mult_times = []
    for i in range(WARMUP_RUNS + BENCH_RUNS):
        t0 = time.perf_counter()
        engine.homomorphic_multiply(key_id, pa.payload_id, pb.payload_id)
        ms = (time.perf_counter() - t0) * 1000
        if i >= WARMUP_RUNS:
            mult_times.append(ms)

    engine.cleanup_context(key_id)

    result = {
        "profile":       profile,
        "N":             N,
        "bits":          bits,
        "slots":         slots,
        "depth":         depth,
        "keygen_ms":     round(statistics.median(keygen_times), 1),
        "encrypt_ms":    round(statistics.median(enc_times), 1),
        "multiply_ms":   round(statistics.median(mult_times), 1),
        "ciphertext_kb": round(statistics.median(ct_sizes) / 1024, 1),
    }

    print(
        f"    keygen_pooled={result['keygen_ms']}ms  "
        f"encrypt={result['encrypt_ms']}ms  "
        f"multiply={result['multiply_ms']}ms  "
        f"ct={result['ciphertext_kb']}KB"
    )
    return result


def bench_slot_packing() -> dict:
    """
    Compare v2 (N individual encrypt_vector calls) vs v3 batch_encrypt_vectors
    for a realistic drug scoring batch: 16 molecules × 8 features each.
    """
    print("\n  Slot packing benchmark (16 molecules × 8 features)")
    N_MOLS    = 16
    N_FEATURES = 8
    molecules = [[float(i * j) * 0.01 for j in range(N_FEATURES)] for i in range(N_MOLS)]

    key_id, info = engine.generate_context(FHEScheme.CKKS, "light")

    # ── v2: 16 separate encrypt_vector calls ─────────────────────────────────
    v2_times  = []
    v2_bytes  = []
    for _ in range(BENCH_RUNS):
        payloads = []
        t0 = time.perf_counter()
        for mol in molecules:
            p = engine.encrypt_vector(key_id, mol)
            payloads.append(p)
        ms = (time.perf_counter() - t0) * 1000
        v2_times.append(ms)
        total_bytes = sum(len(p.ciphertext_b64) * 3 // 4 for p in payloads)
        v2_bytes.append(total_bytes)

    # ── v3: single batch_encrypt_vectors call ─────────────────────────────────
    v3_times = []
    v3_bytes = []
    for _ in range(BENCH_RUNS):
        t0 = time.perf_counter()
        bp = engine.batch_encrypt_vectors(key_id, molecules, "light")
        ms = (time.perf_counter() - t0) * 1000
        v3_times.append(ms)
        v3_bytes.append(len(bp.ciphertext_b64) * 3 // 4)

    # Verify correctness: decrypt first molecule from batch
    bp_verify = engine.batch_encrypt_vectors(key_id, molecules, "light")
    decrypted  = engine.batch_decrypt_vector(key_id, bp_verify.batch_payload_id, 0)
    expected   = molecules[0]
    max_error  = max(abs(a - b) for a, b in zip(decrypted[:N_FEATURES], expected))

    engine.cleanup_context(key_id)

    v2_ms    = round(statistics.median(v2_times), 1)
    v3_ms    = round(statistics.median(v3_times), 1)
    v2_kb    = round(statistics.median(v2_bytes) / 1024, 1)
    v3_kb    = round(statistics.median(v3_bytes) / 1024, 1)
    size_red = round(v2_kb / v3_kb, 2) if v3_kb > 0 else 0
    time_red = round(v2_ms / v3_ms, 2) if v3_ms > 0 else 0

    result = {
        "molecules":          N_MOLS,
        "features":           N_FEATURES,
        "v2_encrypt_ms":      v2_ms,
        "v3_encrypt_ms":      v3_ms,
        "v2_total_kb":        v2_kb,
        "v3_total_kb":        v3_kb,
        "size_reduction_x":   size_red,
        "time_reduction_x":   time_red,
        "slot_utilisation":   f"{bp_verify.slots_used}/{bp_verify.slot_capacity} "
                              f"({bp_verify.metadata['slot_utilisation_pct']}%)",
        "correctness_max_err": round(max_error, 8),
    }

    print(f"    v2 (16×encrypt_vector): {v2_ms}ms, {v2_kb}KB total")
    print(f"    v3 (batch_encrypt):     {v3_ms}ms, {v3_kb}KB total")
    print(f"    Size reduction:         {size_red}×   Time reduction: {time_red}×")
    print(f"    Slot utilisation:       {result['slot_utilisation']}")
    print(f"    Correctness max_error:  {result['correctness_max_err']:.2e}  "
          f"({'✓ PASS' if result['correctness_max_err'] < 1e-4 else '✗ FAIL'})")

    return result


def bench_modulus_trim_comparison() -> None:
    """
    Show per-op latency improvement from modulus trimming:
    Compare v2 [60,40,40,40,60]=240bits vs v3 [60,40,60]=160bits for light profile.
    """
    print("\n  Modulus trim comparison (light profile: v2 240 bits → v3 160 bits)")

    import tenseal as ts

    profiles = {
        "v2_light_240bit": {"coeff_mod_bit_sizes": [60, 40, 40, 40, 60], "global_scale": 2**40},
        "v3_light_160bit": {"coeff_mod_bit_sizes": [60, 40, 60],          "global_scale": 2**40},
    }

    test_vec = [float(i) * 0.01 for i in range(8)]

    for label, p in profiles.items():
        ctx = ts.context(ts.SCHEME_TYPE.CKKS, 8192, coeff_mod_bit_sizes=p["coeff_mod_bit_sizes"])
        ctx.global_scale = p["global_scale"]
        ctx.generate_galois_keys()
        ctx.generate_relin_keys()

        bits  = sum(p["coeff_mod_bit_sizes"])
        times = []
        for i in range(WARMUP_RUNS + BENCH_RUNS):
            t0 = time.perf_counter()
            ea = ts.ckks_vector(ctx, test_vec)
            eb = ts.ckks_vector(ctx, test_vec)
            _  = ea * eb
            ms = (time.perf_counter() - t0) * 1000
            if i >= WARMUP_RUNS:
                times.append(ms)

        ct_bytes = len(ts.ckks_vector(ctx, test_vec).serialize())
        print(
            f"    {label:<28}  bits={bits:<4}  "
            f"encrypt+multiply={round(statistics.median(times),1)}ms  "
            f"ct={ct_bytes//1024}KB"
        )


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    hline("═")
    print("  AMAIMA FHE Engine v3 — Benchmark")
    hline("═")

    print("\n[ 1 ] Profile comparison (keygen pooled + per-op latency)")
    hline()
    profile_results = {}
    for profile in ("minimal", "light", "standard"):
        profile_results[profile] = bench_profile(profile)
    # Skip "deep" by default — N=16384 takes ~60s to warm on a 1-CPU instance
    print("\n  (Skipping 'deep' profile — N=16384 warm-up takes ~60s on 1 vCPU)")
    print("  Run with BENCH_DEEP=1 env var to include it.")
    if os.getenv("BENCH_DEEP"):
        profile_results["deep"] = bench_profile("deep")

    print("\n[ 2 ] Modulus chain trim — direct latency comparison")
    hline()
    bench_modulus_trim_comparison()

    print("\n[ 3 ] Slot packing — v2 vs v3 drug scoring batch")
    hline()
    packing_result = bench_slot_packing()

    print()
    hline("═")
    print("  SUMMARY")
    hline("═")
    print()
    print(f"  {'Profile':<10}  {'N':>6}  {'bits':>5}  {'slots':>6}  "
          f"{'keygen_p':>10}  {'mult_ms':>8}  {'ct_KB':>7}")
    hline("-", 72)
    for pr in profile_results.values():
        print(
            f"  {pr['profile']:<10}  {pr['N']:>6}  {pr['bits']:>5}  "
            f"{pr['slots']:>6}  {pr['keygen_ms']:>8}ms  "
            f"{pr['multiply_ms']:>6}ms  {pr['ciphertext_kb']:>5}KB"
        )

    print()
    print("  Slot packing (16 mol × 8 features):")
    print(f"    v2: {packing_result['v2_total_kb']}KB, {packing_result['v2_encrypt_ms']}ms")
    print(f"    v3: {packing_result['v3_total_kb']}KB, {packing_result['v3_encrypt_ms']}ms")
    print(f"    Reduction: {packing_result['size_reduction_x']}× smaller, "
          f"{packing_result['time_reduction_x']}× fewer calls")
    print(f"    Correctness: max_error={packing_result['correctness_max_err']:.2e}")
    print()
    hline("═")
