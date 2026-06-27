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

| Metric \ n      | 1    | 2     | 4     | 8     | 16    | 32    | 64     |
|-----------------|------|-------|-------|-------|-------|-------|--------|
| KeyGen (ms)     | 1.6  | 1.5   | 1.7   | 1.5   | 1.5   | 1.5   | 1.5    |
| Sign mean (ms)  | 376  | 581   | 779   | 1855  | 2429  | 7684  | 6757   |
| Verify (ms)     | 17   | 32    | 62    | 124   | 245   | 496   | 1017   |
| Link (ms)       | 13.1 | 13.1  | 13.1  | 13.2  | 13.3  | 13.6  | 14.0   |
| Public key (KB) | 4.00 | 4.00  | 4.00  | 4.00  | 4.00  | 4.00  | 4.00   |
| Secret key (KB) | 1.00 | 1.00  | 1.00  | 1.00  | 1.00  | 1.00  | 1.00   |
| Signature (KB)  | 54.00| 75.25 | 117.75| 202.75| 372.75| 712.75| 1392.75|

- **Verify and signature size scale linearly in `n`**; **KeyGen and Link are ~constant in `n`**.
- **Sign** is dominated by Lyubashevsky rejection sampling (geometric retries, mean
  ~11), so its means carry a large std (rejection counts are heavy-tailed); the
  underlying per-attempt cost tracks Verify.
- **Empirical correctness was 100%** across all three parameter sets (Verify / Link /
  Non-link), validating the bounded-norm parameter constraints.
- **Bottleneck:** negacyclic ring multiplication (`poly_mul`) accounts for ~95–96% of
  both Sign and Verify — the single target for an NTT-based speedup.

## Results at a glance (lrs-2048, ring size n)

| Metric \ n      | 1     | 2     | 4     | 8     | 16    | 32     | 64     |
|-----------------|-------|-------|-------|-------|-------|--------|--------|
| KeyGen (ms)     | 5.8   | 5.8   | 5.9   | 5.8   | 5.8   | 5.8    | 5.8    |
| Sign mean (ms)  | 1811  | 2326  | 3238  | 6863  | 7603  | 25650  | 53545  |
| Verify (ms)     | 61    | 120   | 237   | 470   | 945   | 1889   | 3813   |
| Link (ms)       | 50.7  | 51.0  | 51.2  | 51.1  | 51.2  | 51.6   | 52.1   |
| Public key (KB) | 8.00  | 8.00  | 8.00  | 8.00  | 8.00  | 8.00   | 8.00   |
| Secret key (KB) | 2.00  | 2.00  | 2.00  | 2.00  | 2.00  | 2.00   | 2.00   |
| Signature (KB)  | 112.00| 157.00| 247.00| 427.00| 787.00| 1507.00| 2947.00|

See `docs/RESULTS.md` for the full write-up.

## Notes

- Discrete Gaussian sampling uses a rounded continuous normal (fine for a PoC; a
  constant-time CDT/Karney sampler is recommended for a production artifact).
- Polynomial multiplication is exact `int64` negacyclic convolution (overflow-safe for
  these parameters); no NTT yet.
- This is research code for a thesis; it is **not** constant-time and not intended for
  production use.
