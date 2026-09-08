# Table C1 -- Empirical correctness gate (Verify / Link / Non-link)

| Parameter Set | n | Trials | Verify | Link | Non-link | All pass | Retries mean | Theory M_c | Retries max |
|---|---|---|---|---|---|---|---|---|---|
| lrs-1024 | 4 | 100 | 100/100 | 99/99 | 99/99 | Yes | 6.0 | 5.67 | 34 |
| lrs-2048 | 2 | 100 | 100/100 | 99/99 | 99/99 | Yes | 6.5 | 5.67 | 51 |

Verify = honest signatures accepted; Link = same-signer pairs linked; Non-link = different-signer pairs not linked. 100% across all sets validates the bounded-norm parameter constraints. Retry mean tracks the single joint rejection-sampling constant M_c (Theory M_c column; ~constant across parameter sets since alpha is fixed).
