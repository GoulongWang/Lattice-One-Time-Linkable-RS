# Table A -- Parameter sets and rejection-sampling constants

| Parameter Set | N | q | ceil(log2 q) | h | l | v | k | kappa | beta | sigma | M_c | Security (bits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lrs-1024 | 1024 | 2^40 - 195 | 40 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 | 5.67 | TBD |
| lrs-2048 | 2048 | 2^40 - 195 | 40 | 1 | 4 | 1 | 6 | 45 | 1 | 44802 | 5.67 | TBD |

Notes: q = 2^40 - 195 (prime, == 5 mod 8) reused for all sets; every N is a
power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.
M_c is the single joint rejection-sampling constant; E[attempts] = M_c.
Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.
All sets satisfy the correctness constraints (q==5 mod 8; M_c > 1, finite).
