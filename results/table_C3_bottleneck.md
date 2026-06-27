# Table C3 -- Subroutine bottleneck (direct instrumentation)

### Sign (wall 301.9 ms, lrs-1024 n=8)

| Subroutine | Time (ms) | % | Calls |
|---|---|---|---|
| poly_mul (ring mult) | 290.39 | 96.2 | 770 |
| SHAKE-256 hashing (H2) | 4.59 | 1.5 | 18 |
| Gaussian sampling | 1.2 | 0.4 | 34 |
| SHAKE-256 hashing (H) | 0.15 | 0.0 | 1 |
| other (glue/arith) | 5.55 | 1.8 |  |

### Verify (wall 126.2 ms, lrs-1024 n=8)

| Subroutine | Time (ms) | % | Calls |
|---|---|---|---|
| poly_mul (ring mult) | 119.91 | 95.0 | 320 |
| SHAKE-256 hashing (H2) | 2.1 | 1.7 | 8 |
| Gaussian sampling | 0.0 | 0.0 | 0 |
| SHAKE-256 hashing (H) | 0.0 | 0.0 | 0 |
| other (glue/arith) | 4.18 | 3.3 |  |

Negacyclic ring multiplication (poly_mul, the np.convolve core) dominates both Sign and Verify (~95%), identifying it as the single optimization target: an NTT-based multiplier (partial NTT for d=2, or CRT over NTT-friendly primes) would cut the bulk of the cost.
