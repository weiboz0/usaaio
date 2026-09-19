# Plan 022 — C12 p20 K-means Near-Tie Erratum

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task.

## Goal

Repair C12 practice p20 so numerically equivalent K-means inertias select one deterministic lowest-seed winner, document the shipped correction, and restore authoritative local CI without changing the exercise's dataset, estimator, curriculum metadata, or schedule.

## Architecture

The student-facing contract and Session 6 will define one shared near-tie relation using `atol=1e-10` and `rtol=1e-8`.
The solution will filter all inertias equivalent to the minimum under that relation, then select the eligible row with the smallest seed.
An independent synthetic regression—not a live K-means run—will discriminate this rule from raw `argmin`, exact-equality filtering, and largest-seed tie-breaking.

## Tech stack

Jupyter notebooks, NumPy, scikit-learn, pytest, nbformat/nbclient, YAML material inventory, and the repository's local CI/content gates.

## Branch and baseline

- Branch: `feature/plan-022-c12-kmeans-tie-erratum`.
- Base: `862087e`, the current `origin/main` after Plan 020.
- Design commit: `8bac1d7`.
- Trigger: Plan 021's mandatory full CI failed while executing `book1/units/C12-classical-models/practice/p20_solution.ipynb` because the answer check required `best_seed == 20260805` after raw `np.argmin` selected a different one-ULP winner.

## Diagnosis

The inline diagnosis and a separate fresh GPT-5.6-sol read-only diagnosis agree:

- all eight runs recover one co-clustering partition;
- the inertia spread is approximately `7.105e-15`;
- fresh processes selected multiple best seeds under the same data and estimator contract;
- one- and two-thread runs often produce bitwise ties, while four- and eight-thread runs expose reduction-order differences;
- deterministic WCSS recomputation agrees across seeds.

This is parallel floating-point reduction noise, not substantive clustering instability.
The accepted design is `docs/designs/022-c12-p20-kmeans-tie-erratum.md`.

## Exact scope

**Create:**

- `book1/units/C12-classical-models/ERRATA.md`

**Modify:**

- `book1/units/C12-classical-models/lessons/06-kmeans-and-model-comparison.ipynb`
- `book1/units/C12-classical-models/practice/p20.ipynb`
- `book1/units/C12-classical-models/practice/p20_solution.ipynb`
- `tests/test_c12_statement_contracts.py`
- `tests/test_c12_solution_regressions.py`
- `book1/curriculum/material-inventory.yaml` (generated)
- `TODO.md` only at shipping time
- this plan file for review records and the post-execution report

## Task 1 — Lock the regression contract

- [ ] Add a statement-contract assertion requiring p20 to state both `atol=1e-10, rtol=1e-8` eligibility and lowest-seed selection.
- [ ] Add an independent helper/test in `tests/test_c12_solution_regressions.py` using:

```python
seeds = np.array([20260804, 20260805, 20260806], dtype=np.int64)
inertias = np.array([1.0 + 5e-11, 1.0, 2.0], dtype=np.float64)
```

- [ ] Prove RED against the shipped implementation: raw `np.argmin` selects `20260805`, while the required result is `20260804`.
- [ ] Add named mutants for exact-equality filtering and largest-eligible-seed selection; both must fail the regression.
- [ ] Preserve Plan 018's exact five registered classical mutation tests; p20 is a focused regression, not a sixth registered mutation.
- [ ] Commit the failing regression contract separately or retain exact RED command/output in the post-execution report.

## Task 2 — Teach and implement the deterministic tie policy

- [ ] In Session 6, teach that numerically equivalent objectives must be compared using a declared tolerance before a deterministic secondary key is applied.
- [ ] In p20, replace “exact inertia tie” with this precise rule:

```text
eligible(i) iff abs(inertia[i] - minimum) <= 1e-10 + 1e-8 * abs(minimum)
```

Then choose the eligible candidate with the numerically smallest seed.

- [ ] In the solution, implement the equivalent NumPy policy:

```python
minimum = float(np.min(inertias))
candidates = np.flatnonzero(
    np.isclose(inertias, minimum, atol=1e-10, rtol=1e-8)
)
best_index = int(candidates[np.argmin(seeds[candidates])])
```

- [ ] Update the answer check to require `best_index == 0` and `best_seed == 20260804` while retaining every existing shape, dtype, inertia, agreement, dictionary-key, and interpretation assertion.
- [ ] Add `ERRATA.md` recording the former raw-`argmin` behavior, the numerical cause, the corrected rule, the corrected expected seed, and the affected statement/solution/lesson.
- [ ] Regenerate `book1/curriculum/material-inventory.yaml`; do not hand-edit generated hashes.
- [ ] Commit the content repair.

## Task 3 — Verification phase

- [ ] Run the exact focused contract tests:

```bash
PATH=/home/chris/.local/bin:$PATH uv run pytest -q \
  tests/test_c12_statement_contracts.py \
  tests/test_c12_solution_regressions.py
```

- [ ] Execute Session 6 and p20 solution from the Book 1 root without `--inplace`, and verify their source SHA-256 hashes remain unchanged.
- [ ] Execute p20 solution in at least five fresh Jupyter kernels; all runs must select the same contract and pass.
- [ ] Run Book 1 hygiene, tolerance, integration, material-inventory freshness, and `git diff --check`.
- [ ] Run the mandatory `scripts/ci-local.sh` from a clean worktree.
- [ ] Run the four-way content-review gate on the exact verified head, blind-solving p20 from the statement before reading the solution.
- [ ] Resolve every `[OPEN]` finding and rerun affected checks plus full CI after material changes.

## Task 4 — Report and ship

- [ ] Append all four plan-review verdicts and all four content-review verdicts to this plan.
- [ ] Complete the post-execution report with RED/GREEN evidence, five-kernel results, full-CI result, provenance, and exact changed paths.
- [ ] Add Plan 022's shipped erratum status to `TODO.md` without changing other deferred work.
- [ ] Push the branch and open a PR using the configured SSH origin and `GH_TOKEN=$(cat .gh-token)`.
- [ ] Run `PATH=/home/chris/.local/bin:$PATH bash scripts/pre-merge-guard.sh --pr`.
- [ ] Squash-merge only after the guard and required PR checks pass; verify local `main` equals `origin/main`.
- [ ] Return to `feature/plan-021-cross-modal-vision`, rebase or merge the corrected `main` as appropriate, and resume Plan 021's full CI and content gate.

## Out of scope

- Any C12 manifest, concept, minutes, schedule, dataset, estimator-parameter, or practice-ledger change.
- Other C12 practices, lessons, or review notebooks.
- Adding p20 to the exact five registered Plan 018 classical mutations.
- Book 2 content or Plan 021 implementation changes.
- Governance documents.

## Plan Review

Pending the mandatory four-way gate.

## Content Review

Pending implementation and full verification.

## Post-execution report

Pending implementation.
