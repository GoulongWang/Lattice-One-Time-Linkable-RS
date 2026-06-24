# LRS Scheme — Implementation Feasibility Report & Benchmark

Reference (proof-of-concept) implementation of the lattice-based, commitment-tag
**Linkable Ring Signature** from *"Post-Quantum Linkable Ring Signatures Based on
Lattice"* (Guolong Wang, NCCU). Covers Setup / KeyGen / Sign / Verify / Link
(Algorithms 1–5) and produces a Raptor-style timing-and-size table.

## Feasibility verdict

**Implementable.** Every building block is standard lattice cryptography
(negacyclic ring arithmetic, discrete-Gaussian sampling, Lyubashevsky rejection
sampling, MLWE/MSIS commitments, Fiat-Shamir ring chaining). With the parameter
set fixed in Table 2 there are no open research questions left — only engineering
choices. This NumPy reference confirms the scheme runs end-to-end and is correct.

## Parameter set (thesis Table 2)

| q | N | h | l | v | k | κ | β | σ |
|---|---|---|---|---|---|---|---|---|
| 2³² − 99 (prime, ≡5 mod 8) | 1024 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 |

`q ≡ 5 (mod 8)` satisfies Lemma 1 (partial splitting of Xᴺ+1, d=2) so challenge
differences are invertible. Chosen just below 2³² so `⌈log₂ q⌉ = 32`, matching the
size accounting in the paper. Rejection constants computed from σ = α·T:
**M₁ ≈ 2.99, M₂ ≈ 3.83** (expected ~11 signing retries).

## Correctness (test_correctness.py)

All pass:
- genuine signature verifies (`Verify = 1`);
- tampered message rejected (`Verify = 0`);
- two signatures from the **same** key link (`Link = 1`);
- signatures from **different** keys do not link (`Link = 0`);
- measured sizes match the paper: 54.0 / 202.8 / 712.8 KB vs 54.1 / 202.9 / 712.9 KB.

## Benchmark table

| Users | 1 | 8 | 32 |
|---|---|---|---|
| KeyGen | 1.7 ms | 1.6 ms | 1.6 ms |
| Sign | 86 ms | 1623 ms | 5736 ms |
| Verify | 18 ms | 135 ms | 550 ms |
| PK | 4.0 KB | 4.0 KB | 4.0 KB |
| SK | 1.0 KB | 1.0 KB | 1.0 KB |
| Signature | 54.0 KB | 202.8 KB | 712.8 KB |

(Also rendered as `benchmark_table.png`.)

### How to read the timings
- **Sizes are the trustworthy headline numbers** — they reproduce the paper's
  formula to within rounding, validating Table 3.
- **Verify scales linearly in n** (≈ 17 ms × n), as expected from one AOS ring pass.
- **Sign is noisy and dominated by rejection-sampling retries** (geometric, mean
  ~M₁·M₂ ≈ 11 attempts, each re-running the whole ring chain). The numbers show
  relative scaling on an **unoptimised, pure-NumPy CPU reference**, not absolute
  speed. A C/Rust implementation with NTT-style multiplication would be 1–2 orders
  of magnitude faster; treat these as a functional baseline.

## Implementation notes
- Polynomial multiplication is exact NumPy int64 negacyclic convolution. Overflow
  analysis: every product is (full-range matrix entry ≈2³¹) × (short Gaussian or
  ternary vector), so partial sums stay below 2⁶³ — int64 is safe, no NTT required.
- Discrete Gaussian = rounded continuous normal (adequate for a PoC; a thesis-grade
  artifact may want a CDT/Karney sampler for constant-time guarantees).
- Hashes H (→ S_β^k) and H₂ (→ challenge space C) use SHAKE-256.

## Files
- `lrs.py` — the scheme (Setup/KeyGen/Sign/Verify/Link + sizing).
- `test_correctness.py` — correctness checks.
- `benchmark.py` — per-ring-size benchmark (`python3 benchmark.py <n> <reps>`).
- `make_table.py` — renders the table from `benchmark_results.json`.
- `benchmark_table.png / .md / .csv`, `benchmark_results.json` — outputs.

## Suggested next steps for the thesis
1. Replace the Gaussian sampler with a constant-time one and report it.
2. Optimise multiplication (partial NTT for d=2, or CRT over NTT-friendly primes)
   to obtain competitive Sign/Verify numbers.
3. Add a `Link` micro-benchmark column if you want to report linking cost.
4. Run a lattice estimator on (q,N,k,β,σ) to state the concrete security level.
