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

param_table.py             # Experiment A  -> results/table_A_params.{md,json}
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
for n in 1 2 4 8 16 32 64; do python3 benchmark_full.py lrs-1024 $n 8; done

# Experiment C1/C2 — correctness gate + rejection-retry distribution
#   args: <param_set> <n> [reps] [time_budget_s]
python3 correctness_gate.py lrs-1024  4 16
python3 correctness_gate.py lrs-2048  2 12

# Experiment C3 — subroutine bottleneck profile
python3 profile_bottleneck.py lrs-1024 8

# render all tables + the scaling plot from the JSON
python3 make_tables.py
```

All outputs land in `results/`. The scripts write per-(set, n) entries and **merge**
into the JSON, so the sweep can be built up across several short runs.

## Parameter sets

Security scales primarily with the polynomial degree `N`. The Gaussian width is set
to `σ = α·κ·√(lN)` with a fixed `α = 11`, so the rejection-sampling constants stay
constant across sets. Sign uses a single joint rejection test over the stacked
response (`z‖z_c`), with combined constant `M_c ≈ 5.67` (mean ~5-6 signing retries) —
cheaper in expectation than two separate tests (`M1·M2 ≈ 11.4`).
`q = 2^32 − 99` (prime, `≡ 5 mod 8`) is shared by all sets; since every `N` is a power
of two, Lemma 1 (partial splitting of `X^N+1`, `d=2`) holds throughout.

| Set        | N    | ⌈log₂q⌉ | l | k | κ | β | σ     | security |
|------------|------|---------|---|---|---|---|-------|----------|
| lrs-512  | 512  | 32      | 4 | 6 | 45| 1 | 22401 | TBD      |
| lrs-1024    | 1024 | 32      | 4 | 6 | 45| 1 | 31680 | TBD      |
| lrs-2048    | 2048 | 32      | 4 | 6 | 45| 1 | 44802 | TBD      |

> Concrete security (bits) via lattice-estimator / Core-SVP is left as future work.

## Results at a glance (lrs-1024, ring size n)
| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.44 | 1.44 | 1.48 | 1.51 | 1.49 | 1.49 | 1.44 |
| Sign (mean) (ms) | 213 | 313 | 484 | 1047 | 1297 | 2607 | 6513 |
| Verify (ms) | 16 | 31 | 62 | 123 | 245 | 499 | 1012 |
| Link (ms) | 12.8 | 12.9 | 13.0 | 13.2 | 13.3 | 13.6 | 13.8 |
| PK (KB) | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 54.0 | 75.2 | 117.8 | 202.8 | 372.8 | 712.8 | 1392.8 |
| Sign retries (mean) | 6.1 | 6.2 | 6.0 | 7.4 | 4.9 | 5.0 | 6.3 |

- **Verify and signature size scale linearly in `n`**; **KeyGen and Link are ~constant in `n`**.
- **Sign** is dominated by Lyubashevsky rejection sampling (geometric retries, mean
  ~11), so its means carry a large std (rejection counts are heavy-tailed); the
  underlying per-attempt cost tracks Verify.
- **Empirical correctness was 100%** across all three parameter sets (Verify / Link /
  Non-link), validating the bounded-norm parameter constraints.
- **Bottleneck:** negacyclic ring multiplication (`poly_mul`) accounts for ~95–96% of
  both Sign and Verify — the single target for an NTT-based speedup.

## Results at a glance (lrs-2048, ring size n)
| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 5.69 | 5.87 | 5.96 | 5.91 | 5.81 | 5.92 | 5.84 |
| Sign (mean) (ms) | 594 | 1468 | 2502 | 6499 | 6560 | 12222 | 20570 |
| Verify (ms) | 63 | 120 | 237 | 472 | 953 | 1905 | 3833 |
| Link (ms) | 51.0 | 51.3 | 51.4 | 51.6 | 52.2 | 51.9 | 52.5 |
| PK (KB) | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 |
| SK (KB) | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| Signature (KB) | 112.0 | 157.0 | 247.0 | 427.0 | 787.0 | 1507.0 | 2947.0 |
| Sign retries (mean) | 4.1 | 7.5 | 8.0 | 11.9 | 6.4 | 6.1 | 5.2 |

See `docs/RESULTS.md` for the full write-up.

## Notes

- Discrete Gaussian sampling uses a rounded continuous normal (fine for a PoC; a
  constant-time CDT/Karney sampler is recommended for a production artifact).
- Polynomial multiplication is exact `int64` negacyclic convolution (overflow-safe for
  these parameters); no NTT yet.
- This is research code for a thesis; it is **not** constant-time and not intended for
  production use.
