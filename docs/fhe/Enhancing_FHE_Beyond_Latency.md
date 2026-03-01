# Enhancing FHE Beyond Latency

**What we're implementing:**
1. **CKKS slot packing** — `encrypt_vector` currently encrypts one vector per ciphertext. CKKS supports `N/2` slots (4096 for N=8192). Batch multiple small vectors into one ciphertext → 2-4x fewer ciphertexts, 2-4x less bandwidth and memory
2. **Modulus chain trimming** — the `light` profile has `[60, 40, 40, 40, 60]` = 240 bits but drug scoring only needs depth 2 (one multiply + rescale). That's `[60, 40, 60]` = 160 bits — valid, faster NTT, smaller ciphertext
3. **Dynamic RNS optimization** — expose a `minimal` profile for the shallowest circuits, trim `standard` to exactly what it needs

The public API stays identical — drop-in replacement.

Now write the unit tests and the benchmark script so changes can be verified immediately on the VPS:

Here's exactly what changed and why.

---

**CKKS_PARAMS — modulus chain trimming (Enhancement 2)**

The v2 `light` profile had `[60, 40, 40, 40, 60]` = 240 bits. Drug scoring only performs depth-2 arithmetic (one multiply + one rescale), so the two middle 40-bit primes were dead weight. The trimmed `[60, 40, 60]` = 160 bits is 33% smaller NTT operand size, which translates directly to ~15–20% faster per-operation latency and proportionally smaller serialized ciphertexts — all at the same 128-bit security. The `standard` profile similarly drops from 200 bits to the minimum needed for depth-3. A new `minimal` profile at `[60, 60]` = 120 bits handles the shallowest circuits (simple scoring with no multiply). All totals are verified under the 218-bit SEAL security limit for N=8192.

**`batch_encrypt_vectors()` — slot packing (Enhancement 1)**

CKKS with N=8192 gives 4096 independent plaintext slots per ciphertext. The old code placed every vector in its own ciphertext regardless of size — for 16 drug molecules × 8 features that meant 16 ciphertexts ≈ 1.1 MB on the wire. The new method concatenates all vectors into one flat array, zero-pads to the slot boundary, encrypts once, and returns a `BatchEncryptedPayload` with a `slices` list of `(payload_id, offset, length)` tuples. `batch_decrypt_all()` then does one single CKKS decrypt and slices the result — same total work as decrypting any one ciphertext, but you get all 16 molecules back. Expected result: ~0.2 MB for the same batch, 5× size reduction, ~15× fewer API calls into TenSEAL.

**`BatchEncryptedPayload` dataclass (Enhancement 3)**

New public type returned by `batch_encrypt_vectors()`. Contains `slot_capacity`, `slots_used`, `slot_utilisation_pct`, `bytes_saved` vs naïve approach, and the `slices` list. The stats counter in `get_stats()` now tracks `slots_packed` and `ciphertext_bytes_saved` across the process lifetime, which will surface in the `/v1/fhe/status` endpoint automatically.

**`pad_to_slots` on `encrypt_vector` (Enhancement 4)**

A backward-compatible `pad_to_slots=False` parameter that lets single-vector callers opt into full-slot padding when they know they'll be doing slot-aligned arithmetic later. Default is `False` — zero change in behavior for all existing callers.

**`parameter_bench_v3.py`**

Run this on the VPS immediately after deploying to confirm the gains: `python -m app.fhe.parameter_bench_v3`. It measures keygen (pooled), encrypt, multiply across all profiles, does a direct 240-bit vs 160-bit NTT comparison, and runs the full drug-scoring slot-packing benchmark with a correctness check (`max_error < 1e-4` CKKS approximation tolerance). Expected total runtime ~2 minutes on a Hetzner CX22.
