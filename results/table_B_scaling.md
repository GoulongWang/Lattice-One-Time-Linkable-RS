# Table B -- Ring-size scaling

## Table B1 -- lrs-1024 (N=1024)

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

## Table B2 -- lrs-2048 (N=2048)

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

Environment: macOS-26.5.2-arm64-arm-64bit, Python 3.11.9, pure-NumPy reference.
Sign is dominated by Lyubashevsky rejection sampling. A single joint rejection test over the stacked response (z || z_c) is used, with combined constant M_c ~ 5.67 (geometric retry mean), so per-signature time varies widely. Times are arithmetic means over the reps listed below; the mean (not the median) is reported because E[Sign] = M_c x per-attempt cost is what the theory predicts. Per-point medians are kept in benchmark_full.json. Verify and Signature size scale linearly in n; KeyGen and Link are ~constant in n.

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| reps (lrs-1024) | 30 | 30 | 30 | 30 | 30 | 30 | 30 |
| reps (lrs-2048) | 30 | 30 | 30 | 30 | 30 | 30 | 30 |
