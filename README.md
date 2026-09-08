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

# Experiment C3 — subroutine bottleneck profile (optional; not run for the
# numbers below, so results/profile_results.json is absent by default)
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
`q = 2^40 − 195` (prime, `≡ 5 mod 8`) is shared by both sets; since every `N` is a power
of two, Lemma 1 (partial splitting of `X^N+1`, `d=2`) holds throughout.

| Set      | N    | q          | ⌈log₂q⌉ | l | k | κ | β | σ     | M_c  | security |
|----------|------|------------|---------|---|---|---|---|-------|------|----------|
| lrs-1024 | 1024 | 2^40 − 195 | 40      | 4 | 6 | 45| 1 | 31680 | 5.67 | TBD      |
| lrs-2048 | 2048 | 2^40 − 195 | 40      | 4 | 6 | 45| 1 | 44802 | 5.67 | TBD      |

> `poly_mul` multiplies exactly over `int64` via `np.convolve`. At `q = 2^40 − 195`,
> `N = 2048` the peak convolution magnitude is `2^60.8` against the `int64` ceiling of
> `2^63`, so the arithmetic is still exact but the margin is about 4×; `set_params()`
> estimates this bound and warns if a future `q`/`N` would exhaust it.

> Concrete security (bits) via lattice-estimator / Core-SVP is left as future work.

## Results at a glance (lrs-1024, ring size n)

Means over 30 reps per point, macOS arm64 / Python 3.11, single-threaded NumPy.

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.47 | 1.48 | 1.50 | 1.46 | 1.47 | 1.49 | 1.48 |
| Sign mean (ms) | 225 | 302 | 437 | 917 | 1531 | 2493 | 5410 |
| Sign std (ms) | 206 | 297 | 435 | 702 | 1278 | 2145 | 6185 |
| Verify (ms) | 16 | 32 | 62 | 122 | 244 | 491 | 1024 |
| Link (ms) | 12.8 | 12.9 | 13.0 | 13.1 | 13.1 | 13.4 | 13.8 |
| PK (KB) | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 59.0 | 80.2 | 122.8 | 207.8 | 377.8 | 717.8 | 1397.8 |
| Sign retries (mean) | 6.5 | 5.9 | 5.4 | 6.5 | 5.8 | 4.9 | 5.2 |

## Results at a glance (lrs-2048, ring size n)
| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 5.68 | 5.71 | 5.75 | 5.91 | 5.82 | 5.69 | 5.66 |
| Sign mean (ms) | 623 | 1040 | 1604 | 4130 | 5491 | 11553 | 17586 |
| Sign std (ms) | 631 | 836 | 1162 | 3893 | 4747 | 12249 | 15727 |
| Verify (ms) | 61 | 118 | 235 | 467 | 933 | 1872 | 3795 |
| Link (ms) | 50.3 | 50.1 | 51.8 | 50.4 | 50.7 | 51.0 | 51.8 |
| PK (KB) | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 |
| SK (KB) | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| Signature (KB) | 122.0 | 167.0 | 257.0 | 437.0 | 797.0 | 1517.0 | 2957.0 |
| Sign retries (mean) | 4.5 | 5.3 | 5.1 | 7.6 | 5.4 | 5.9 | 4.5 |

- **Verify and signature size scale linearly in `n`** (Verify ≈ 16.0 ms × n for lrs-1024,
  ≈ 59.3 ms × n for lrs-2048); **KeyGen and Link are ~constant in `n`**.
- **Sign is monotone in `n`** at 30 reps/point. It is dominated by Lyubashevsky rejection
  sampling (geometric retries, mean `M_c ≈ 5.67`), so its std stays comparable to its mean;
  dividing out the retry count leaves a per-attempt cost ≈ 1.0–1.2× Verify.
- **Empirical correctness was 100%** over 100 trials on each parameter set (Verify / Link /
  Non-link), validating the bounded-norm parameter constraints.

See `docs/RESULTS.md` for the full write-up.

## Notes

- Discrete Gaussian sampling uses a rounded continuous normal (fine for a PoC; a
  constant-time CDT/Karney sampler is recommended for a production artifact).
- Polynomial multiplication is exact `int64` negacyclic convolution (overflow-safe for
  these parameters, with ~4× margin at `q = 2^40 − 195`, `N = 2048`); no NTT yet.
- This is research code for a thesis; it is **not** constant-time and not intended for
  production use.
