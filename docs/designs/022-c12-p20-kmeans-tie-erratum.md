# Design 022 — C12 p20 K-means Near-Tie Erratum

## Problem

`C12-classical-models` practice p20 compares eight one-initialization K-means runs.
All eight runs recover the same partition, but scikit-learn's parallel floating-point reduction can change the last bit of `inertia_` between fresh processes.
The shipped solution uses raw `np.argmin(inertias)` while its answer check requires seed `20260805`.
Full local CI therefore failed even though repeated runs were substantively identical.

The observed spread is about `7.105e-15`, far below the practice's declared comparison tolerances (`atol=1e-10`, `rtol=1e-8`).
Fresh-process diagnosis selected several different seeds while preserving one co-clustering partition.
The failure is a numerical tie-policy bug, not evidence of unstable clustering.

## Decision

Model selection uses the same explicit numerical equivalence relation already declared by the practice:

```text
abs(inertia[i] - minimum) <= 1e-10 + 1e-8 * abs(minimum)
```

Every seed satisfying that condition is an eligible near-tie candidate.
The candidate with the numerically smallest seed wins.
For the fixed p20 dataset, the deterministic result is seed `20260804`.

This policy is preferable to raw `argmin`, forced single-thread execution, or relaxing the final assertion:

- Raw `argmin` assigns meaning to insignificant reduction noise.
- Thread pinning hides the numerical contract instead of teaching it and remains platform-sensitive.
- Merely accepting several seeds leaves `best_index`, `best_seed`, and downstream agreement calculations nondeterministic.

## Teaching and content changes

Session 6 will teach tolerance-aware model selection before p20 uses it.
The student statement will replace “exact inertia tie” with the explicit `atol`/`rtol` eligibility rule and lowest-seed tie-break.
The solution will implement that rule and keep all existing estimator parameters, returned keys, shapes, dtypes, co-clustering logic, interpretation, and inertia checks.

A unit-local `ERRATA.md` will record the original failure, corrected semantics, and affected files.
This fills the repository's current unit-erratum location gap without changing governance documents.

## Verification design

The regression oracle is independent of scikit-learn and OpenMP scheduling:

```python
seeds = np.array([20260804, 20260805, 20260806])
inertias = np.array([1.0 + 5e-11, 1.0, 2.0])
```

Raw `argmin` and exact-equality filtering choose `20260805`; the required tolerance-aware policy chooses `20260804`.
Tests will also reject choosing the largest eligible seed and will pin the student-facing tolerance language.

The edited lesson and solution must execute from a clean Book 1 root without modifying source notebooks.
The p20 solution will be executed repeatedly in fresh Jupyter kernels.
Focused C12 checks and the complete `scripts/ci-local.sh` remain mandatory before merge.

## Scope

In scope:

- Session 6's numerical tie-policy explanation.
- p20 statement and solution.
- A unit-local erratum record.
- Focused statement/solution regressions.
- Regenerated Book 1 material inventory.

Out of scope:

- Estimator parameters, dataset generation, practice metadata, concepts, minutes, or schedule.
- Adding p20 to Plan 018's exact five registered classical mutation tests.
- Other Book 1 or Book 2 content.
- Governance-file changes.
