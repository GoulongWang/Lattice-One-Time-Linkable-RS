# Table A -- Parameter sets and rejection-sampling constants

| Parameter Set | N | ceil(log2 q) | h | l | v | k | kappa | beta | sigma | M1 | M2 | E[attempts]=M1*M2 | Security (bits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lrs-512 | 512 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 22401 | 2.989 | 3.828 | 11.44 | TBD |
| lrs-1024 | 1024 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 | 2.989 | 3.828 | 11.44 | TBD |
| lrs-2048 | 2048 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 44802 | 2.989 | 3.828 | 11.44 | TBD |

Notes: q = 2^32 - 99 (prime, == 5 mod 8) reused for all sets; every N is a
power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.
Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.
All sets satisfy the correctness constraints (q==5 mod 8; M1,M2 > 1, finite).
