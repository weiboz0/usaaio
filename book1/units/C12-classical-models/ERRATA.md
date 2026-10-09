# C12-classical-models Errata

## Practice p20: deterministic selection for near-tied K-means objectives

**Corrected:** 2026-09-19 (Plan 022)

The originally shipped solution selected the best run with raw `np.argmin(inertias)` while its
answer check required seed `20260805`.
At lower thread counts, bitwise-tied inertias caused `np.argmin` to select the first seed,
`20260804`, which still failed that old assertion.
At other thread counts, a different seed could come out lower by about `1e-14` (a last-bits difference) and win the raw `argmin`.

The cause was parallel floating-point reduction order, not a substantive difference in the
clustering: all eight runs recovered the same co-clustering partition, and their inertia spread
was about `7.105e-15`.

The corrected rule first finds the minimum inertia and declares index `i` eligible exactly when

`eligible(i) iff abs(inertia[i] - minimum) <= 1e-10 + 1e-8 * abs(minimum)`.

It then chooses the eligible candidate with the numerically smallest seed.
For the fixed p20 data this gives `best_index == 0` and `best_seed == 20260804`.

The affected materials are the p20 statement, the p20 solution, and Session 6's explanation of
deterministic selection for near-tied numerical objectives.

Sibling practices p21 and p30 were audited and are immune to this defect.
Practice p21 fixes its primary run by index instead of selecting a minimum objective across runs.
Practice p30 selects from deterministic, hand-computed NumPy WCSS values rather than
thread-dependent estimator reductions.
