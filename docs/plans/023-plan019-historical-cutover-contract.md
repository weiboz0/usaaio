# Plan 023 — Historical Plan 019 Cutover Contract

## Goal

Repair the Plan 019 integration regression so it proves the atomic two-book migration between pinned historical commits without byte-freezing every Book 1 notebook against legitimate later curriculum edits.

## Trigger and diagnosis

Plan 022 verification intentionally changed C12 Session 6 and p20.
`tests/test_integration.py::test_plan019_task3_every_book1_manifest_and_notebook_matches_pinned_cutover` then failed because it compares the current working tree to pre-cutover commit `4cc3894` and treats every notebook not changed by Plan 019 as permanently immutable.
That is broader than Plan 019 Task 3, whose contract is that the Plan 019 migration itself preserved Book 1 except for inventoried path-resolution cells.

The pre-cutover reference is full commit `4cc38946548f618ac131d246bfd4191d20e4e7d8`.
The post-cutover reference is full squash-merge commit `ab795cdfb1ea6efcebce351ef7968f36435bffec` (`Plan 019: split complete books and add attention foundations (#22)`).
The quarantined pre-cutover commit is not an ancestor of the squash commit, so the implementation must read blobs directly and must not rely on ancestry, merge bases, or commit ranges.
With Git history available, the regression should compare `4cc38946548f618ac131d246bfd4191d20e4e7d8:<old path>` to `ab795cdfb1ea6efcebce351ef7968f36435bffec:book1/<path>`.
Later working-tree content is outside that historical proof.
Without those commits (for example, a source archive), the test cannot prove historical byte identity and must limit itself to current structural/path-resolution checks rather than hash the current curriculum as if it were the Plan 019 result.

## Exact scope

**Create:**

- `docs/plans/023-plan019-historical-cutover-contract.md`

**Modify:**

- `tests/test_integration.py`
- `TODO.md` only at shipping time
- this plan for review records and the post-execution report

No teaching material, solution, manifest, curriculum inventory, generated document, governance file, or Plan 022 file changes.

## Task 1 — Lock the regression behavior

- [ ] Add a focused test for a helper that resolves the post-cutover Book 1 blob from pinned full commit `ab795cdfb1ea6efcebce351ef7968f36435bffec`, not from `BOOK1_ROOT` in the current worktree.
- [ ] Pin both full historical commit constants and exact old/new path mapping (`<path>` to `book1/<path>`).
- [ ] Build one isolated clone that retains Git history for both pinned Plan 019 commits and replaces exactly these current Book 1 notebook blobs with their immutable Plan 022 source-commit `d653fcbf1fdcd46fd759bf2a03506d5368c17926` versions: `units/C12-classical-models/lessons/06-kmeans-and-model-comparison.ipynb`, `units/C12-classical-models/practice/p20.ipynb`, and `units/C12-classical-models/practice/p20_solution.ipynb`.
- [ ] Prove that exact fixture fails the current cutover regression before the refactor and passes the refactored regression afterward; a missing-helper-only RED is insufficient.
- [ ] Add separate historyless-mode regressions for unavailable pre-cutover commit and unavailable post-cutover commit using injectable commit/blob resolvers or an equivalent deterministic mechanism; do not destroy repository refs or rely on a fresh-init fixture that lacks both commits.
- [ ] In either historyless case, retain and mutation-test exactly these assertions: the fixture has 64 discovery rows plus three special consumers covering 67 unique notebook destinations; all 67 current Book 1 destinations exist; every inventoried cell index exists; every inventoried migrated cell contains `USAAIO_BOOK_ROOT` or `book_root` and does not contain top-level `pyproject.toml` discovery.
- [ ] Prove historyless mode still fails when one inventoried destination is deleted and when one inventoried path-resolution marker is corrupted.
- [ ] In historyless mode, explicitly skip the unreconstructible historical universe assertions: 991/20 path counts, full path-set digest, manifest digest, unchanged-notebook digest, changed-structure digest, and changed-source digest. Never derive those historical expectations from the current worktree.
- [ ] Emit an explicit mode marker in test output so archive logs state that only structural checks ran and why the historical proof was unavailable.

## Task 2 — Refactor the historical cutover proof

- [ ] Introduce small read-only helpers for commit availability and blob reads; no checkout, worktree mutation, or network access.
- [ ] When both commits exist, compare pre-cutover blobs from the pinned full pre-cutover SHA with post-cutover blobs from the pinned full squash SHA and retain the existing 991/20/67 counts, 64-entry discovery inventory, full path-set digest, changed-cell set, structures, sources, and all four aggregate record digests.
- [ ] Never use current Book 1 notebook/manifest bytes in historical digest records when the pinned commits exist.
- [ ] In historyless mode, inspect only the 67 paths named by the committed fixture, validate the retained destination/cell/marker assertions from Task 1, and do not enumerate the current Book 1 tree as a substitute historical path universe.
- [ ] Run the same 67 current-destination/cell/marker assertions unconditionally in history-present mode as well; the pinned commit-to-commit proof never replaces validation of the live migrated path-resolution cells.
- [ ] Preserve the 64-consumer inventory, changed-cell rules, PDF input-set test, and all other Plan 019 guards.

## Task 3 — Verification phase

This is a tooling/test-only plan and ships no unit or mock-test content, so the design §2 content-verification requirements are exempt.

- [ ] Run the focused new tests and the entire `tests/test_integration.py` suite.
- [ ] Run `tests/test_clean_checkout.py` and `tests/test_audit_curriculum.py` to cover archive and inventory consumers.
- [ ] Reproduce the exact Plan 022 three-blob RED/GREEN scenario in the isolated fixture and retain the command/output in the report.
- [ ] Run `scripts/verify-clean-checkout.sh` so the real repository's `git archive HEAD` path executes full CI without `.git`; a synthetic mini-repository alone is insufficient.
- [ ] Run `ruff`, `git diff --check`, and mandatory `scripts/ci-local.sh` on a clean branch tip.
- [ ] Run the four-way tooling/content review gate on the exact verified commit and resolve every open finding.

## Task 4 — Report and ship

- [ ] Record the passing four-way plan gate before implementation.
- [ ] Complete the post-execution report with RED/GREEN, history-present/historyless evidence, the Plan 022 mutation witness, full-CI result, and exact paths.
- [ ] Record three known limitations in the report: the pre-cutover SHA is currently retained by the stale `feature/plan-019-attention-transformers` ref and deleting that ref plus garbage collection would reduce full clones to historyless mode; the PDF input-set test intentionally freezes the R1 mock-test file list and must be revisited by the future r1-002/r1-003 plan; the TODO ledger currently jumps from Plan 019 because 020 is recorded only in its plan and 021/022 remain in flight.
- [ ] Add Plan 023's shipped status to `TODO.md` without changing unrelated entries.
- [ ] Commit final records and run authoritative clean-tip `scripts/ci-local.sh` again.
- [ ] Push, open a PR with `GH_TOKEN=$(cat .gh-token)`, run `bash scripts/pre-merge-guard.sh --pr`, and squash-merge.
- [ ] Return to `feature/plan-022-c12-kmeans-tie-erratum`, merge corrected `main`, and resume Plan 022 verification.

## Out of scope

- Design §2 content verification: this is a tooling/test-only plan and ships no unit or mock-test content.
- Any curriculum-content or generated-evidence change.
- Updating Plan 019's historical fixture values or weakening its exact migration-cell assertions.
- General Git-history abstraction outside this one integration contract.
- Plan 022 implementation or review records.

## Plan Review

### Round 1 — exact commit `02c8960` (2026-09-19)

- `[claude-self]` **REJECT** — accepted the independent findings that the exact Plan 022 three-blob RED witness and historyless negative mutations were underspecified.
- `[codex]` **REJECT** — required the same exact fixture to fail before and pass after, explicit retained/skipped historyless assertions, both missing-commit cases, and missing-destination/corrupt-marker negatives.
- `[fable]` **APPROVE WITH NITS** — independently verified the root cause, 67-path bijection, unchanged digest constants, and archive consumer; requested explicit confinement of all current-tree counts/digests.
- `[glm]` **APPROVE WITH NITS** — independently recomputed every pinned digest from the two commits; requested a real archive run, full SHA terminology, and documentation of the PDF-list/TODO limitations.

Round 1 did not reach consensus and did not authorize implementation.
This revision closes every finding with the exact three-path RED/GREEN fixture, full non-ancestral commit pins, an exhaustive historyless assertion partition and negative matrix, real archive CI, the tooling exemption, and known-limitations reporting.

### Round 2 — revised plan

Exact commit `e05816a` reached consensus on 2026-09-19:

- `[claude-self]` **APPROVE** — exact fixture, mode partition, negative matrix, scope, and lifecycle verified.
- `[codex]` **APPROVE WITH NITS** — confirmed all Round-1 blockers closed and requested an immutable Plan 022 source pin.
- `[fable]` **APPROVE WITH NITS** — independently verified all commit/digest premises and requested unconditional live 67-path checks, visible mode reporting, and ref-durability disclosure.
- `[glm]` **APPROVE WITH NITS** — independently recomputed every digest and requested an explicitly history-retaining fixture plus deterministic missing-commit injection.

All nits are resolved in this gate-record update without changing scope or architecture.
The four-way plan gate is passed and implementation is authorized.

## Content Review

Pending implementation and verification.

## Post-execution report

Pending implementation.
