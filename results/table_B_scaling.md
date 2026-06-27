# Table B -- Ring-size scaling

## Table B1 -- lrs-1024 (N=1024)

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.44 | 1.50 | 1.48 | 1.51 | 1.49 | 1.49 | 1.48 |
| Sign (mean) (ms) | 235 | 342 | 484 | 1047 | 1297 | 2607 | 6875 |
| Verify (ms) | 16 | 32 | 62 | 123 | 245 | 499 | 1020 |
| Link (ms) | 12.9 | 13.1 | 13.0 | 13.2 | 13.3 | 13.6 | 13.9 |
| PK (KB) | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 54.0 | 75.2 | 117.8 | 202.8 | 372.8 | 712.8 | 1392.8 |
| Sign retries (mean) | 6.8 | 6.8 | 6.0 | 7.4 | 4.9 | 5.0 | 6.6 |

## Table B2 -- lrs-2048 (N=2048)

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

Environment: Linux-6.8.0-124-generic-aarch64-with-glibc2.35, Python 3.10.12, pure-NumPy reference.
Sign is dominated by Lyubashevsky rejection sampling. A single joint rejection test over the stacked response (z || z_c) is used, with combined constant M_c ~ 5.67 (geometric retry mean), so per-signature time varies widely; arithmetic means over 8 reps shown. Verify and Signature size scale linearly in n; KeyGen and Link are ~constant in n.
