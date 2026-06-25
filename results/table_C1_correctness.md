# Table C1 -- Empirical correctness gate (Verify / Link / Non-link)

| Parameter Set | n | Trials | Verify | Link | Non-link | All pass | Retries mean (theory 11.4) | Retries max |
|---|---|---|---|---|---|---|---|---|
| lrs-light | 4 | 20 | 20/20 | 19/19 | 19/19 | Yes | 11.4 | 41 |
| lrs-128 | 4 | 16 | 16/16 | 15/15 | 15/15 | Yes | 7.1 | 26 |
| lrs-192 | 2 | 9 | 9/9 | 8/8 | 8/8 | Yes | 13.6 | 33 |

Verify = honest signatures accepted; Link = same-signer pairs linked; Non-link = different-signer pairs not linked. 100% across all sets validates the bounded-norm parameter constraints. Retry mean tracks the theoretical M1*M2 = 11.4.
