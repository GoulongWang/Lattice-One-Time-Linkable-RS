# Lattice-based One-Time Linkable Ring Signature — Implementation & Benchmarks
The scheme works over the ring `R_q = Z_q[X]/(X^N + 1)` and implements
Setup / KeyGen / Sign / Verify / Link (Algorithms 1–5). The code is a **correctness +
benchmark reference in pure NumPy** — its goal is to validate correctness and analyze
relative cost and scaling, *not* to achieve state-of-the-art absolute speed. An
optimized C/Rust implementation with NTT multiplication would be 1–2 orders of
magnitude faster.

## Repository layout

```
lrs.py                     # the scheme (Setup/KeyGen/Sign/Verify/Link) + size accounting
test_correctness.py        # end-to-end correctness checks

param_table.py             # Experiment A  -> results/table_A_params.*
benchmark_full.py          # Experiment B  -> results/benchmark_full.json
correctness_gate.py        # Experiment C1/C2 -> results/correctness_results.json
profile_bottleneck.py      # Experiment C3 -> results/profile_results.json
make_tables.py             # renders Tables B/C1/C3 (+ PNG) from the JSON above

docs/
  EXPERIMENT_PLAN.md             # the experiment plan (what/why)
  RESULTS.md                     # full results write-up, mapped to thesis sections
  implementation_performance.tex # ready-to-\input LaTeX chapter (Chinese, \section level)

results/                    # generated tables, plots and raw JSON (committed)
```

## Requirements
- Python 3.9+
```bash
pip install -r requirements.txt   # numpy, matplotlib
```

## 執行步驟
```bash
# 正確性檢查
python3 test_correctness.py

# Experiment A — parameter sets + rejection-sampling constants (Table A)
python3 param_table.py

# Experiment B — ring-size scaling (run once per ring size n; results merge into JSON)
#   args: <param_set> <n> [reps] [time_budget_s]
for n in 1 2 4 8 16 32 64; do python3 benchmark_full.py lrs-128 $n 8; done

# Experiment C1/C2 — correctness gate + rejection-retry distribution
#   args: <param_set> <n> [reps] [time_budget_s]
python3 correctness_gate.py lrs-light 4 20
python3 correctness_gate.py lrs-128  4 16
python3 correctness_gate.py lrs-192  2 12

# Experiment C3 — subroutine bottleneck profile
python3 profile_bottleneck.py lrs-128 8

# render all tables + the scaling plot from the JSON
python3 make_tables.py
```

All outputs land in `results/`. The scripts write per-(set, n) entries and **merge**
into the JSON, so the sweep can be built up across several short runs.

## Parameter sets

Security scales primarily with the polynomial degree `N`. The Gaussian width is set
to `σ = α·κ·√(lN)` with a fixed `α = 11`, so the rejection-sampling constants
`M1 ≈ 2.99`, `M2 ≈ 3.83` stay constant across sets (mean ~11 signing retries).
`q = 2^32 − 99` (prime, `≡ 5 mod 8`) is shared by all sets; since every `N` is a power
of two, Lemma 1 (partial splitting of `X^N+1`, `d=2`) holds throughout.

| Set        | N    | ⌈log₂q⌉ | l | k | κ | β | σ     | security |
|------------|------|---------|---|---|---|---|-------|----------|
| lrs-light  | 512  | 32      | 4 | 6 | 45| 1 | 22401 | TBD      |
| lrs-128    | 1024 | 32      | 4 | 6 | 45| 1 | 31680 | TBD      |
| lrs-192    | 2048 | 32      | 4 | 6 | 45| 1 | 44802 | TBD      |

> Concrete security (bits) via lattice-estimator / Core-SVP is left as future work.

## Results at a glance (lrs-128, ring size n)

| Metric \ n      | 1    | 8     | 32    | 64     |
|-----------------|------|-------|-------|--------|
| KeyGen (ms)     | 1.6  | 1.6   | 1.6   | 1.7    |
| Sign median (ms)| 50   | 1643  | 4024  | 7043   |
| Verify (ms)     | 18   | 135   | 553   | 1147   |
| Link (ms)       | 14.4 | 14.6  | 15.0  | 15.8   |
| Public key (KB) | 4.00 | 4.00  | 4.00  | 4.00   |
| Secret key (KB) | 1.00 | 1.00  | 1.00  | 1.00   |
| Signature (KB)  | 54.00| 202.75| 712.75| 1392.75|

- **Verify and signature size scale linearly in `n`**; **KeyGen and Link are ~constant in `n`**.
- **Sign** is dominated by Lyubashevsky rejection sampling (geometric retries, mean
  ~11), so its medians are noisy; the underlying per-attempt cost tracks Verify.
- **Empirical correctness was 100%** across all three parameter sets (Verify / Link /
  Non-link), validating the bounded-norm parameter constraints.
- **Bottleneck:** negacyclic ring multiplication (`poly_mul`) accounts for ~95–96% of
  both Sign and Verify — the single target for an NTT-based speedup.

See `docs/RESULTS.md` for the full write-up.

## Notes

- Discrete Gaussian sampling uses a rounded continuous normal (fine for a PoC; a
  constant-time CDT/Karney sampler is recommended for a production artifact).
- Polynomial multiplication is exact `int64` negacyclic convolution (overflow-safe for
  these parameters); no NTT yet.
- This is research code for a thesis; it is **not** constant-time and not intended for
  production use.
