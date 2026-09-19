# Plan 025 — Clean-Archive CI Contract

## Goal

Make the repository's real `git archive HEAD` verifier complete successfully without a `.git` directory or raw past-paper corpus, while preserving every Git-history and overlap assertion when those resources are available in a normal checkout.

## Trigger and diagnosis

Plan 023 ran `scripts/verify-clean-checkout.sh` and exposed eight failures after 1,160 tests passed.
None came from Plan 023's historical cutover refactor.
They came from four older resource assumptions inside the supposedly historyless archive gate:

- the scope checker treated an unavailable Git repository as proof that the documented Plan 014 squash commit was not an ancestor;
- a `.gitignore` contract test invoked `git check-ignore` without supplying repository metadata;
- a historical-revision test invoked a Git-history-only script even when the archive had no history;
- one integration assertion required a local raw reference corpus even though the clean-archive design intentionally excludes raw past papers and treats the overlap check's loud skip as valid.

The fix must distinguish resource absence from a negative result.
It must not initialize `.git` inside the archive, copy raw past papers, weaken normal-checkout history checks, or turn real overlap findings into skips.

Plan 024 remains reserved by Plan 019 for the first live Round 2 assessment, so this unblocking tooling work uses Plan 025.

## Exact scope

**Create:**

- `docs/plans/025-clean-archive-ci.md`

**Modify:**

- `tools/checks/scope.py`
- `tests/test_scope.py`
- `tests/test_clean_checkout.py`
- `tests/test_historical_deferred_policy.py`
- `tests/test_integration.py`
- `TODO.md` only at shipping time
- this plan for gate records and the post-execution report

No teaching material, solution, manifest, curriculum inventory, generated document, Git ignore rule, governance file, or clean-checkout script changes.

## Task 1 — Lock resource-aware regressions

- [ ] Retain the exact failing `scripts/verify-clean-checkout.sh` output as the RED witness: eight failures, 1,160 passes, one skip.
- [ ] Add a scope regression proving a structurally valid merged reconciliation is accepted when the inspected tree has no Git metadata.
- [ ] Convert the existing bad-squash ancestry regression into a real temporary Git repository so it still proves that an available but non-ancestor commit is rejected.
- [ ] Make the ignore-contract regression exercise the real tracked `.gitignore` with an isolated temporary Git metadata directory and explicit work tree; do not replace Git semantics with substring matching.
- [ ] Make the historical deferred-policy test skip with an explicit reason only when the current source tree has no Git metadata; it must still run the real historical script in a normal checkout.
- [ ] Make the overlap integration assertion require a completed scan when a reference index/PDF exists and require the exact `reference corpus absent` skip when the intentionally clean archive lacks that corpus.
- [ ] Add or retain negative witnesses showing that malformed reconciliation data, a real non-ancestor commit, wrong ignore patterns, and overlap errors still fail.

## Task 2 — Separate unavailable history from failed ancestry

- [ ] In `tools/checks/scope.py`, probe whether the repository history is available before running `git merge-base --is-ancestor`.
- [ ] If no Git work tree exists, retain all reconciliation-document structure checks but omit only the unreconstructible ancestry query.
- [ ] If Git history exists, preserve the current rejection for a missing or non-ancestor squash commit.
- [ ] Do not use environment flags, dates, network access, or mutable repository state to choose the mode.

## Task 3 — Verification phase

This is a tooling/test-only plan and ships no unit or mock-test content, so the design section 2 content-verification requirements are exempt.

- [ ] Run focused scope, clean-checkout, historical-policy, integration, and curriculum-audit tests.
- [ ] Run all of `tests/test_scope.py`, `tests/test_clean_checkout.py`, `tests/test_historical_deferred_policy.py`, `tests/test_integration.py`, and `tests/test_audit_curriculum.py`.
- [ ] Run `ruff`, `git diff --check`, and the real `scripts/verify-clean-checkout.sh` with only the declared pretrained-cache mount.
- [ ] Confirm archive logs contain the raw-paper-absent overlap diagnostic and contain no `.git` directory.
- [ ] Run mandatory `scripts/ci-local.sh` on a clean branch tip with the local raw reference corpus available.
- [ ] Run the four-way tooling/content review gate on the exact verified commit and resolve every open finding.

## Task 4 — Report and ship

- [ ] Record the passing four-way plan gate before implementation.
- [ ] Complete the post-execution report with the eight-failure RED witness, focused GREEN evidence, normal-checkout negative witnesses, archive mode evidence, full CI, and exact changed paths.
- [ ] Add Plan 025's shipped status to `TODO.md` without changing unrelated entries.
- [ ] Commit final records and rerun authoritative clean-tip `scripts/verify-clean-checkout.sh` and `scripts/ci-local.sh`.
- [ ] Push, open a PR with `GH_TOKEN=$(cat .gh-token)`, run `bash scripts/pre-merge-guard.sh --pr`, and squash-merge.
- [ ] Return to `feature/plan-023-plan019-historical-cutover`, merge corrected `main`, rerun Plan 023 verification, and resume its gate and shipping lifecycle.

## Out of scope

- Plan 023's historical cutover implementation or records.
- Adding a Git repository to archive output.
- Copying raw past-test papers into a clean archive.
- Changing `.gitignore`, overlap thresholds, curriculum scope, or reconciliation policy.
- Any curriculum-content or generated-evidence change.

## Plan Review

Pending four-way review.

## Content Review

Pending implementation and verification.

## Post-execution report

Pending implementation.
