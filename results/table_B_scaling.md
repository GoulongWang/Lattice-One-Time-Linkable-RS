# Table B -- Ring-size scaling (param set lrs-128: N=1024)

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.63 | 1.65 | 1.63 | 1.63 | 1.62 | 1.62 | 1.67 |
| Sign median (ms) | 50 | 687 | 363 | 1643 | 452 | 4024 | 7043 |
| Sign std (ms) | 136 | 502 | 775 | 1603 | 1930 | 2350 | 2923 |
| Verify (ms) | 18 | 35 | 68 | 135 | 272 | 553 | 1147 |
| Link (ms) | 14.4 | 14.4 | 14.5 | 14.6 | 14.7 | 15.0 | 15.8 |
| PK (KB) | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 54.0 | 75.2 | 117.8 | 202.8 | 372.8 | 712.8 | 1392.8 |
| Sign retries (mean) | 3.4 | 12.9 | 9.4 | 15.8 | 5.8 | 7.7 | 6.7 |

Environment: Linux-6.8.0-124-generic-aarch64-with-glibc2.35, Python 3.10.12, pure-NumPy reference.
Sign is dominated by Lyubashevsky rejection sampling (geometric retries, mean ~M1*M2=11.4), hence the large std; medians shown. Verify and Signature size scale linearly in n; KeyGen and Link are ~constant in n.
