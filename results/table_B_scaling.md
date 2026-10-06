# Table B -- Ring-size scaling

## Table B1 -- lrs-1024 (N=1024)

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

## Table B2 -- lrs-2048 (N=2048)

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

Environment: macOS-26.5.2-arm64-arm-64bit, Python 3.11.9, pure-NumPy reference.
Sign runs TWO independent Lyubashevsky rejection-sampling loops per signature: a tag loop (constant M_z ~ 14.83) guarding the linkable tag's response, then a ring loop (joint constant M_c ~ 5.67) over the stacked ring response (z || z_c). E[total attempts] = M_z + M_c ~ 20.5, so per-signature time varies widely. Times are arithmetic means over the reps listed below; the mean (not the median) is reported because E[Sign] = M_total x per-attempt cost is what the theory predicts. Per-point medians are kept in benchmark_full.json. Verify and Signature size scale linearly in n; KeyGen and Link are ~constant in n.

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| reps (lrs-1024) | 30 | 30 | 30 | 29 | 18 | 13 | 11 |
| reps (lrs-2048) | 21 | 16 | 11 | 9 | 6 | 4 | 5 |
