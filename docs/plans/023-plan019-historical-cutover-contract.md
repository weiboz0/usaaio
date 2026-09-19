# Plan 023 — Historical Plan 019 Cutover Contract

## Goal

Repair the Plan 019 integration regression so it proves the atomic two-book migration between pinned historical commits without byte-freezing every Book 1 notebook against legitimate later curriculum edits.

## Trigger and diagnosis

Plan 022 verification intentionally changed C12 Session 6 and p20.
`tests/test_integration.py::test_plan019_task3_every_book1_manifest_and_notebook_matches_pinned_cutover` then failed because it compares the current working tree to pre-cutover commit `4cc3894` and treats every notebook not changed by Plan 019 as permanently immutable.
That is broader than Plan 019 Task 3, whose contract is that the Plan 019 migration itself preserved Book 1 except for inventoried path-resolution cells.

The post-cutover reference is merge commit `ab795cd` (`Plan 019: split complete books and add attention foundations (#22)`).
With Git history available, the regression should compare `4cc3894:<old path>` to `ab795cd:book1/<path>`.
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

- [ ] Add a focused test for a helper that resolves the post-cutover Book 1 blob from pinned commit `ab795cd`, not from `BOOK1_ROOT` in the current worktree.
- [ ] Pin both historical commit constants and exact old/new path mapping (`<path>` to `book1/<path>`).
- [ ] Add a historyless-mode regression proving the historical byte/digest assertions are skipped when either pinned commit is unavailable while structural/path-resolution checks remain active.
- [ ] Capture RED against the current implementation before refactoring.

## Task 2 — Refactor the historical cutover proof

- [ ] Introduce small read-only helpers for commit availability and blob reads; no checkout, worktree mutation, or network access.
- [ ] When both commits exist, compare pre-cutover blobs from `4cc3894` with post-cutover blobs from `ab795cd` and retain the existing exact path counts, changed-cell set, structures, sources, and aggregate digest expectations.
- [ ] Never use current Book 1 notebook/manifest bytes in historical digest records when the pinned commits exist.
- [ ] In historyless mode, validate current destination existence plus the inventoried migrated cells' structural markers, but do not assert historical blob equality or historical aggregate digests that cannot be reconstructed.
- [ ] Preserve the 64-consumer inventory, changed-cell rules, PDF input-set test, and all other Plan 019 guards.

## Task 3 — Verification phase

This is a tooling/test-only plan and ships no unit or mock-test content, so the design §2 content-verification requirements are exempt.

- [ ] Run the focused new tests and the entire `tests/test_integration.py` suite.
- [ ] Run `tests/test_clean_checkout.py` and `tests/test_audit_curriculum.py` to cover archive and inventory consumers.
- [ ] Reproduce the Plan 022 scenario by applying its three notebook blobs in a temporary worktree or equivalent isolated fixture and prove the historical cutover test still passes.
- [ ] Run `ruff`, `git diff --check`, and mandatory `scripts/ci-local.sh` on a clean branch tip.
- [ ] Run the four-way tooling/content review gate on the exact verified commit and resolve every open finding.

## Task 4 — Report and ship

- [ ] Record the passing four-way plan gate before implementation.
- [ ] Complete the post-execution report with RED/GREEN, history-present/historyless evidence, the Plan 022 mutation witness, full-CI result, and exact paths.
- [ ] Add Plan 023's shipped status to `TODO.md` without changing unrelated entries.
- [ ] Commit final records and run authoritative clean-tip `scripts/ci-local.sh` again.
- [ ] Push, open a PR with `GH_TOKEN=$(cat .gh-token)`, run `bash scripts/pre-merge-guard.sh --pr`, and squash-merge.
- [ ] Return to `feature/plan-022-c12-kmeans-tie-erratum`, merge corrected `main`, and resume Plan 022 verification.

## Out of scope

- Any curriculum-content or generated-evidence change.
- Updating Plan 019's historical fixture values or weakening its exact migration-cell assertions.
- General Git-history abstraction outside this one integration contract.
- Plan 022 implementation or review records.

## Plan Review

Pending the mandatory four-way gate.

## Content Review

Pending implementation and verification.

## Post-execution report

Pending implementation.
