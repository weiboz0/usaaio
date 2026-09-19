# Plan 022 — C12 p20 K-means Near-Tie Erratum

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task.

## Goal

Repair C12 practice p20 so numerically equivalent K-means inertias select one deterministic lowest-seed winner, document the shipped correction, and restore authoritative local CI without changing the exercise's dataset, estimator, curriculum metadata, or schedule.

## Architecture

The student-facing contract and Session 6 will define one shared near-tie relation using `atol=1e-10` and `rtol=1e-8`.
The solution will expose one private selector named `_lowest_seed_near_minimum`, owned and called by `kmeans_stability_audit`; it will filter all inertias equivalent to the minimum under that relation, then select the eligible row with the smallest seed.
Synthetic regressions will execute that solution-owned selector—not a test-local reimplementation or a live K-means run—and discriminate the full rule from raw `argmin`, exact-equality filtering, either missing tolerance term, a strict boundary, over-broad eligibility, first-eligible selection, and largest-seed tie-breaking.

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

- [ ] Add statement-contract assertions requiring the exact p20 formula `eligible(i) iff abs(inertia[i] - minimum) <= 1e-10 + 1e-8 * abs(minimum)` and the phrase “numerically smallest seed”; do not accept the pre-repair grader-note tolerance and generic “smaller seed” wording as sufficient. Also require Session 6 to teach that numerical-objective near-ties use the declared tolerance before the deterministic secondary key.
- [ ] Require `p20_solution.ipynb` to place `import numpy as np`, the notebook's only definitions of shared `ATOL = 1e-10` and `RTOL = 1e-8`, and the private selector `_lowest_seed_near_minimum(seeds, inertias, *, atol, rtol)` in a dedicated standalone-executable code cell with no live audit invocation. The selector returns the selected row index, and its body must use the supplied keyword parameters as `np.isclose(..., atol=atol, rtol=rtol)`.
- [ ] Pin the exact production dataflow inside `kmeans_stability_audit`: `best_index = _lowest_seed_near_minimum(seeds, inertias, atol=ATOL, rtol=RTOL)` followed by `best_seed = int(seeds[best_index])`; reject an ignored/decoy helper call, hard-coded index, or second selection path. The ordinary solution regression must execute the actual notebook through the existing `_execute_solution` mechanism.
- [ ] Locate and execute the selector's dedicated production code cell in an isolated test namespace; apply mutant source transforms only to an in-memory copy of that cell, then judge every mutant solely against these deterministic fixture expectations—not against a live K-means run or its thread-sensitive answer check:

```python
ascending_seeds = np.array([20260804, 20260805, 20260806], dtype=np.int64)
permuted_seeds = np.array([20260805, 20260804, 20260806], dtype=np.int64)
near_one = np.array([1.0 + 5e-11, 1.0, 2.0], dtype=np.float64)
relative_required = np.array([1000.0 + 5e-6, 1000.0, 2000.0], dtype=np.float64)
absolute_required = np.array([5e-11, 0.0, 2.0], dtype=np.float64)
inclusive_boundary = np.array([1e-10, 0.0, 2.0], dtype=np.float64)
outside_boundary = np.array([1000.0 + 2e-5, 1000.0, 2000.0], dtype=np.float64)
permuted_near_tie = np.array([1.0, 1.0 + 5e-11, 2.0], dtype=np.float64)
```

- [ ] With `ascending_seeds`, require returned indices `0, 0, 0, 0, 1` and mapped seeds `20260804`, `20260804`, `20260804`, `20260804`, `20260805` for the first five inertia fixtures respectively; with `permuted_seeds` and `permuted_near_tie`, require returned index `1` and mapped seed `20260804`.
- [ ] Prove the fixture contract kills raw `argmin`, exact-equality filtering, `rtol=0`, `atol=0`, strict-`<` boundary eligibility, over-broad/all-candidate eligibility, first-eligible selection, and largest-eligible-seed selection deterministically.
- [ ] Preserve Plan 018's exact five registered classical mutation tests; p20 is a focused regression, not a sixth registered mutation.
- [ ] Commit the failing regression contract separately or retain exact RED command/output in the post-execution report.

## Task 2 — Teach and implement the deterministic tie policy

- [ ] In Session 6, teach that numerically equivalent objectives must be compared using a declared tolerance before a deterministic secondary key is applied; present this as the numerical-objective refinement of the existing exact-tie rules.
- [ ] Place the teaching in a new late subsection without inserting cells before or renaming/reordering the three coverage-map-pinned anchors under headings 2, 5, and 6; keep their `cell_ordinal` values unchanged so no coverage-map or roadmap edit is needed.
- [ ] In p20, replace “exact inertia tie” with this precise rule:

```text
eligible(i) iff abs(inertia[i] - minimum) <= 1e-10 + 1e-8 * abs(minimum)
```

Then choose the eligible candidate with the numerically smallest seed.

- [ ] In the solution-owned private selector called by `kmeans_stability_audit`, implement the equivalent NumPy policy and return the selected row index:

```python
minimum = float(np.min(inertias))
candidates = np.flatnonzero(
    np.isclose(inertias, minimum, atol=atol, rtol=rtol)
)
best_index = int(candidates[np.argmin(seeds[candidates])])
return best_index
```

The only production call is `best_index = _lowest_seed_near_minimum(seeds, inertias, atol=ATOL, rtol=RTOL)`; `best_seed` is then `int(seeds[best_index])`.

- [ ] Update the answer check to require `best_index == 0` and `best_seed == 20260804` while retaining every existing shape, dtype, inertia, agreement, dictionary-key, and interpretation assertion.
- [ ] Add `ERRATA.md` recording the former raw-`argmin` behavior (including that bitwise ties at lower thread counts selected first seed `20260804` and still failed the old `20260805` assertion), the numerical cause, the corrected rule, the corrected expected seed, the affected statement/solution/lesson, and that siblings p21 and p30 were audited and are immune: p21 fixes its primary run by index, while p30 selects deterministic hand-computed NumPy WCSS.
- [ ] Regenerate `book1/curriculum/material-inventory.yaml` with `PATH=/home/chris/.local/bin:$PATH uv run python -m tools.audit_curriculum --root book1`; do not hand-edit generated hashes.
- [ ] Commit the content repair.

## Task 3 — Verification phase

- [ ] Run the exact focused contract tests:

```bash
PATH=/home/chris/.local/bin:$PATH uv run pytest -q \
  tests/test_c12_statement_contracts.py \
  tests/test_c12_solution_regressions.py
```

- [ ] Execute Session 6 and p20 solution from the Book 1 root without `--inplace`, and verify their source SHA-256 hashes remain unchanged.
- [ ] Execute p20 solution in fresh Jupyter kernels spanning `OMP_NUM_THREADS=1,2,4,8` (at least eight executions total, with repeated 4- and 8-thread runs); all runs must select `best_index == 0`, `best_seed == 20260804`, and pass the answer check.
- [ ] Confirm p20 remains a core, 65-minute integrative practice and that no manifest, schedule, difficulty, or timing field changed.
- [ ] Run Book 1 hygiene, tolerance, integration, material-inventory freshness, and `git diff --check`.
- [ ] Run the mandatory `scripts/ci-local.sh` from a clean worktree.
- [ ] Run the four-way content-review gate on the exact verified head, blind-solving p20 from the statement before reading the solution.
- [ ] Resolve every `[OPEN]` finding and rerun affected checks plus full CI after material changes.

## Task 4 — Report and ship

- [ ] Before implementation, record all plan-review rounds and the passing four-way gate in this section; append all four content-review verdicts after implementation.
- [ ] Complete the post-execution report with RED/GREEN evidence, the thread-matrix fresh-kernel results, p21/p30 immunity, the pre-existing TODO ledger gap for shipped Plan 020/in-flight Plan 021, full-CI results, provenance, and exact changed paths.
- [ ] Add Plan 022's shipped erratum status to `TODO.md` without changing other deferred work.
- [ ] After content-review resolutions, the post-execution report, generated inventory, and `TODO.md` are final, commit them and run `scripts/ci-local.sh` again on the clean branch tip; this is the authoritative final CI for shipping.
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

### Round 1 — exact commit `845590a` (2026-09-19)

- `[claude-self]` **REJECT** — the synthetic witness was not bound to the actual notebook implementation, did not require the relative-tolerance term, and the ship sequence omitted final clean-tip CI after report/TODO/review edits.
- `[codex]` **REJECT** — confirmed those three blockers with live evidence: raw `argmin` could false-green on the fixed dataset; the `5e-11` fixture was satisfied by absolute tolerance alone; and workflow-required final CI was ordered too early.
- `[fable]` **APPROVE WITH NITS** — independently confirmed the diagnosis and core policy; requested a relative-term-sensitive fixture and documentation that sibling p30 is immune.
- `[glm]` **APPROVE WITH NITS** — independently reproduced thread-dependent winners and raised the implementation-binding issue, Session 6 contract/anchor preservation, thread-matrix verification, roster recording, and fuller erratum history.

Round 1 did not reach consensus and therefore did not authorize implementation.
This revision closes every blocking or substantive finding by binding tests to a solution-owned selector, adding relative-required and outside-boundary fixtures, pinning Session 6 teaching, preserving coverage-map anchors, testing the OpenMP failure axis, naming the inventory generator, recording p30's immunity in the report, and adding final clean-tip CI.

### Round 2 — revised plan

Exact commit `f41b812` reached consensus on 2026-09-19:

- `[claude-self]` **APPROVE** — fixture mathematics, anchor preservation, and lifecycle ordering verified.
- `[codex]` **APPROVE WITH NITS** — requested a permuted-seed witness for the secondary key and an inclusive-boundary witness.
- `[fable]` **APPROVE WITH NITS** — requested fixture-only mutant oracles, an absolute-term witness, explicit timing preservation, and p21 immunity.
- `[glm]` **APPROVE WITH NITS** — independently confirmed the same absolute-term/oracle gaps and requested an exact selector name plus TODO-ledger disclosure.

Although Round 2 formally passed, this revision incorporates all cheap semantic hardening rather than deferring it to implementation.
Because the reviewed commit changed, implementation remains paused pending a fresh exact-commit Round 3.

### Round 3 — final hardened plan

Exact commit `6f66f0e` did not reach consensus on 2026-09-19:

- `[claude-self]` **REJECT** — accepted the external production-dataflow finding: a helper call alone did not prove its result owned `best_index`.
- `[codex]` **REJECT** — required an exact assignment from the helper, parameter use rather than hard-coded tolerance literals, and an explicit return contract.
- `[fable]` **APPROVE WITH NITS** — verified the full fixture/mutant matrix and requested an isolated selector cell plus parameter plumbing.
- `[glm]` **APPROVE WITH NITS** — independently confirmed parameter-plumbing/return ambiguity and requested exact statement literals and thread-matrix outcomes.

This revision closes the blocker by pinning a dedicated selector cell, shared constants, parameterized `np.isclose`, an integer index return, and the exact helper-to-`best_index`-to-`best_seed` dataflow.
It also prevents a pre-repair statement-contract false green and makes fresh-kernel expectations explicit.

### Round 4 — exact dataflow confirmation

Exact commit `0574806` reached consensus on 2026-09-19:

- `[claude-self]` **APPROVE** — exact selector dataflow, RED literals, verification, and lifecycle ordering verified.
- `[codex]` **APPROVE WITH NITS** — confirmed the Round-3 blocker is closed and requested only the stale “both rounds” wording fix.
- `[fable]` **APPROVE WITH NITS** — independently executed the full fixture/mutant matrix and requested a standalone NumPy namespace plus explicit index assertions.
- `[glm]` **APPROVE WITH NITS** — independently reproduced thread-dependent winners and requested a standalone selector import and single shared tolerance definitions.

All nits are resolved in this review-record update without changing scope or architecture.
The four-way plan gate is passed and implementation is authorized.

## Content Review

Pending implementation and full verification.

## Post-execution report

Pending implementation.
