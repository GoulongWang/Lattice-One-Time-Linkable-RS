# Table C1 -- Empirical correctness gate (Verify / Link / Non-link)

| Parameter Set | n | Trials | Verify | Link | Non-link | All pass | Retries mean (tag+ring) | Theory M_total | Retries max |
|---|---|---|---|---|---|---|---|---|---|
| lrs-1024 | 4 | 100 | 100/100 | 99/99 | 99/99 | Yes | 17.8 | 20.50 | 58 |
| lrs-2048 | 2 | 64 | 64/64 | 63/63 | 63/63 | Yes | 23.2 | 20.51 | 68 |

Verify = honest signatures accepted; Link = same-signer pairs linked; Non-link = different-signer pairs not linked. 100% across all sets validates the bounded-norm parameter constraints. Retry mean tracks the total of two independent rejection-sampling loops, M_z (tag) + M_c (ring) = M_total (Theory M_total column; both constants are ~constant across parameter sets since alpha is fixed).
