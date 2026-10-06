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
constant across sets. **Sign runs two independent Lyubashevsky rejection-sampling
loops** (see "2026-09-08 fix" below): a tag loop guarding the linkable tag's response
`z = y + d·(r1-r2)` with constant `M_z ≈ 14.83`, followed by a ring loop with a single
joint rejection test over the stacked response (`z‖z_c`), combined constant
`M_c ≈ 5.67` (cheaper in expectation than two separate tests, `M1·M2 ≈ 11.4`). The two
loops are sequential and independent, so `E[Sign attempts] = M_z + M_c ≈ 20.5`.
`q = 2^40 − 195` (prime, `≡ 5 mod 8`) is shared by both sets; since every `N` is a power
of two, Lemma 1 (partial splitting of `X^N+1`, `d=2`) holds throughout.

| Set      | N    | q          | ⌈log₂q⌉ | l | k | κ | β | σ     | M_z (tag) | M_c (ring) | M_total | security |
|----------|------|------------|---------|---|---|---|---|-------|-----------|------------|---------|----------|
| lrs-1024 | 1024 | 2^40 − 195 | 40      | 4 | 6 | 45| 1 | 31680 | 14.83     | 5.67       | 20.50   | TBD      |
| lrs-2048 | 2048 | 2^40 − 195 | 40      | 4 | 6 | 45| 1 | 44802 | 14.83     | 5.67       | 20.50   | TBD      |

> `poly_mul` multiplies exactly over `int64` via `np.convolve`. At `q = 2^40 − 195`,
> `N = 2048` the peak convolution magnitude is `2^60.8` against the `int64` ceiling of
> `2^63`, so the arithmetic is still exact but the margin is about 4×; `set_params()`
> estimates this bound and warns if a future `q`/`N` would exhaust it.

> Concrete security (bits) via lattice-estimator / Core-SVP is left as future work.

## Results at a glance (lrs-1024, ring size n)

macOS arm64 (Apple M2) / Python 3.11, single-threaded NumPy. Reps/point vary (30 down
to 11 for large n) because Sign got ~3.6x slower once the tag rejection loop was added
and each point ran under a wall-clock budget; see `results/benchmark_full.json` for the
exact reps per point (row below).

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.64 | 1.70 | 1.64 | 1.63 | 1.69 | 1.63 | 1.64 |
| Sign mean (ms) | 361 | 589 | 647 | 1087 | 1954 | 4031 | 4779 |
| Sign std (ms) | 176 | 376 | 343 | 609 | 1604 | 2758 | 3464 |
| Verify (ms) | 21 | 38 | 73 | 140 | 278 | 555 | 1148 |
| Link (ms) | 14.5 | 14.4 | 14.4 | 14.4 | 14.6 | 14.9 | 15.6 |
| PK (KB) | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 59.0 | 80.2 | 122.8 | 207.8 | 377.8 | 717.8 | 1397.8 |
| Sign retries, tag (mean) | 12.2 | 17.0 | 12.4 | 14.9 | 12.5 | 17.0 | 14.5 |
| Sign retries, ring (mean) | 4.9 | 6.7 | 5.5 | 5.7 | 6.1 | 6.6 | 3.9 |
| Sign retries, total (mean) | 17.1 | 23.6 | 17.8 | 20.6 | 18.6 | 23.6 | 18.5 |
| reps | 30 | 30 | 30 | 29 | 18 | 13 | 11 |

## Results at a glance (lrs-2048, ring size n)
| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 6.41 | 6.55 | 6.34 | 6.43 | 6.34 | 6.44 | 6.45 |
| Sign mean (ms) | 1427 | 1760 | 3002 | 4646 | 6925 | 12492 | 16790 |
| Sign std (ms) | 828 | 939 | 1398 | 7210 | 4029 | 12302 | 10884 |
| Verify (ms) | 72 | 137 | 265 | 524 | 1059 | 2092 | 4285 |
| Link (ms) | 60.2 | 60.1 | 60.0 | 60.2 | 60.9 | 61.0 | 62.6 |
| PK (KB) | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 | 10.0 |
| SK (KB) | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| Signature (KB) | 122.0 | 167.0 | 257.0 | 437.0 | 797.0 | 1517.0 | 2957.0 |
| Sign retries, tag (mean) | 11.5 | 11.0 | 15.5 | 9.4 | 23.7 | 11.2 | 17.8 |
| Sign retries, ring (mean) | 5.9 | 5.9 | 6.5 | 7.2 | 4.8 | 5.5 | 3.6 |
| Sign retries, total (mean) | 17.4 | 16.9 | 22.0 | 16.7 | 28.5 | 16.8 | 21.4 |
| reps | 21 | 16 | 11 | 9 | 6 | 4 | 5 |

Both tables and `docs/RESULTS.md` are produced by `python3 make_tables.py` from
`results/benchmark_full.json`; per-point reps are limited by a wall-clock budget
(`results/benchmark_full.json` also stores every raw retry count for exact stats).

- **Verify and signature size scale linearly in `n`** (Verify ≈ 18 ms × n for lrs-1024,
  ≈ 65 ms × n for lrs-2048); **KeyGen and Link are ~constant in `n`**.
- **Sign is dominated by rejection sampling from TWO independent loops** (tag `M_z ≈ 14.83`
  + ring `M_c ≈ 5.67`, total `M_total ≈ 20.5`), so its mean and std are both large and
  comparable in size (geometric-retry noise), and it is ~3.6x slower than before the
  2026-09-08 fix (see below), which only ran the ring loop.
- **Empirical correctness was 100%** on every completed trial (Verify / Link / Non-link):
  100/100 for lrs-1024 n=4, 64/64 for lrs-2048 n=2 (see `docs/RESULTS.md` / Table C1);
  the retry means (17.8 and 23.2) are consistent with theory (`M_total ≈ 20.5`) given the
  geometric distribution's large variance and the modest trial counts.

### 2026-09-08 fix: tag response was missing its own rejection-sampling test

The thesis's Sign pseudocode (Algorithm 3) has **two separate** Lyubashevsky
rejection-sampling steps: line 13 restarts the linkable-tag response
`z = y + d·(r1-r2)` with its own constant `M_z`, independently of the later joint
ring-response test at line 21 (constant `M_c`, the only one this code previously
implemented). `lrs.py`'s `sign()` computed `z_tag` unconditionally and never rejected
it, so the tag's response distribution was not proven simulatable/independent of the
secret `r1-r2` the way Theorem 1 requires, and every "Sign retries" number published
before this fix (`M_c ≈ 5.67` only) undercounted the true expected work by a factor of
`M_total/M_c ≈ 3.6`.

The fix adds an inner acceptance loop around the tag's `y` sampling, using a new
constant `M_z`, derived the same way as the existing `M1`/`M2`/`M_c` (Theorem 1,
`σ = α·T`): the tag's center is `v = d·(r1-r2)` with `r1, r2 ∈ S_β^k` (ternary,
`β=1`), so by the triangle inequality on the same worst-case bound used for `M2`
(`T2 = κ√(kN)`, center `d·r`), `‖d·(r1-r2)‖ ≤ ‖d·r1‖ + ‖d·r2‖ ≤ 2·T2`, giving
`T_z = 2·T2`, `α_z = σ/T_z ≈ 4.49`, `M_z = exp(12/α_z + 1/(2α_z²)) ≈ 14.83` (same for
both parameter sets, since `α` is fixed). The tag loop is independent of and precedes
the ring loop (the tag `I` is hashed into the ring's Fiat-Shamir chain, so it must be
fixed first), so `E[Sign attempts] = M_z + M_c ≈ 20.5`, not `M_c ≈ 5.67`.

Validated with a clean 80-trial measurement isolating just the tag loop on first-time
signing (where `r1=r2` exactly, so `v=0` exactly and the accept probability is exactly
`1/M_z` on every attempt, independent of the realized response): empirical mean
**14.838** against theory `M_z = 14.835` — see `_LAST_RETRIES_TAG` /
`_LAST_RETRIES_RING` / `_LAST_RETRIES` (total) in `lrs.py` for the per-signature
instrumentation now exposed, and the "Sign retries, tag/ring/total" rows above for the
full-sweep confirmation.

See `docs/RESULTS.md` for the full write-up.

## Notes

- Discrete Gaussian sampling uses a rounded continuous normal (fine for a PoC; a
  constant-time CDT/Karney sampler is recommended for a production artifact).
- Polynomial multiplication is exact `int64` negacyclic convolution (overflow-safe for
  these parameters, with ~4× margin at `q = 2^40 − 195`, `N = 2048`); no NTT yet.
- This is research code for a thesis; it is **not** constant-time and not intended for
  production use.
