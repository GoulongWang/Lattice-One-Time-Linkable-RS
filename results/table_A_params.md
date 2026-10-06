# Table A -- Parameter sets and rejection-sampling constants

| Parameter Set | N | q | ceil(log2 q) | h | l | v | k | kappa | beta | sigma | M_z (tag) | M_c (ring) | M_total | Security (bits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lrs-1024 | 1024 | 2^40 - 195 | 40 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 | 14.835 | 5.67 | 20.505 | TBD |
| lrs-2048 | 2048 | 2^40 - 195 | 40 | 1 | 4 | 1 | 6 | 45 | 1 | 44802 | 14.835 | 5.67 | 20.505 | TBD |

Notes: q = 2^40 - 195 (prime, == 5 mod 8) reused for all sets; every N is a
power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.
Two independent rejection-sampling loops run per signature: M_z guards the
linkable tag's response (Algorithm 3 lines 9-13); M_c is the joint constant
over the ring response z_j||z_c,j (lines 15-21). E[attempts] = M_z + M_c = M_total.
Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.
All sets satisfy the correctness constraints (q==5 mod 8; M_c > 1, finite).
