# Table C3 -- Subroutine bottleneck (direct instrumentation)

### Sign (wall 318.9 ms, lrs-128 n=8)

| Subroutine | Time (ms) | % | Calls |
|---|---|---|---|
| poly_mul (ring mult) | 305.2 | 95.7 | 770 |
| SHAKE-256 hashing (H2) | 6.35 | 2.0 | 18 |
| Gaussian sampling | 1.22 | 0.4 | 34 |
| SHAKE-256 hashing (H) | 0.2 | 0.1 | 1 |
| other (glue/arith) | 5.94 | 1.9 |  |

### Verify (wall 135.4 ms, lrs-128 n=8)

| Subroutine | Time (ms) | % | Calls |
|---|---|---|---|
| poly_mul (ring mult) | 127.92 | 94.5 | 320 |
| SHAKE-256 hashing (H2) | 2.9 | 2.1 | 8 |
| Gaussian sampling | 0.0 | 0.0 | 0 |
| SHAKE-256 hashing (H) | 0.0 | 0.0 | 0 |
| other (glue/arith) | 4.62 | 3.4 |  |

Negacyclic ring multiplication (poly_mul, the np.convolve core) dominates both Sign and Verify (~95%), identifying it as the single optimization target: an NTT-based multiplier (partial NTT for d=2, or CRT over NTT-friendly primes) would cut the bulk of the cost.
