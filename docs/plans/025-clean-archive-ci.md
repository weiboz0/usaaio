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

Those eight unit-test failures stop CI before its final stage.
After they are repaired, `scripts/ci-local.sh` would expose a ninth downstream failure because it unconditionally invokes the Git-index-based pre-merge guard inside the historyless archive.

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
- `scripts/ci-local.sh`
- `TODO.md` only at shipping time
- this plan for gate records and the post-execution report

No teaching material, solution, manifest, curriculum inventory, generated document, Git ignore rule, governance file, `scripts/verify-clean-checkout.sh`, or `scripts/pre-merge-guard.sh` changes.

## Task 1 — Lock resource-aware regressions

- [ ] Retain the exact failing `scripts/verify-clean-checkout.sh` output as the RED witness: eight failures, 1,160 passes, one skip.
- [ ] Add a scope regression proving a structurally valid merged reconciliation is accepted when the inspected tree has no Git metadata.
- [ ] Convert the existing bad-squash ancestry regression into a real temporary Git repository so it still proves that an available but non-ancestor commit is rejected.
- [ ] Make the ignore-contract regression exercise the real tracked `.gitignore` with an isolated temporary Git metadata directory and explicit work tree; do not replace Git semantics with substring matching.
- [ ] Make the historical deferred-policy test skip with an explicit reason only when the current source tree has no Git metadata; it must still run the real historical script in a normal checkout.
- [ ] Make the overlap integration assertion require a completed scan when a reference index/PDF exists and require the exact `reference corpus absent` skip when the intentionally clean archive lacks that corpus.
- [ ] Add or retain negative witnesses showing that malformed reconciliation data, a real non-ancestor commit, wrong ignore patterns, and overlap errors still fail.
- [ ] Add a behavioral CI regression proving a normal Git checkout invokes `scripts/pre-merge-guard.sh`, while a source archive without Git metadata emits one exact resource-skip marker and continues to `ci-local: ALL GREEN`.
- [ ] Prove the no-Git path cannot be selected merely by an environment variable and that a failing pre-merge guard remains blocking whenever Git metadata exists.

## Task 2 — Separate unavailable history from failed ancestry

- [ ] In `tools/checks/scope.py`, probe whether the repository history is available before running `git merge-base --is-ancestor`.
- [ ] If no Git work tree exists, retain all reconciliation-document structure checks but omit only the unreconstructible ancestry query.
- [ ] If Git history exists, preserve the current rejection for a missing or non-ancestor squash commit.
- [ ] Do not use environment flags, dates, network access, or mutable repository state to choose the mode.

## Task 3 — Keep the pre-merge guard strict and resource-scoped

- [ ] In `scripts/ci-local.sh`, detect Git work-tree availability immediately before step 9.
- [ ] In a normal checkout, invoke `bash scripts/pre-merge-guard.sh` exactly as before and propagate every nonzero result.
- [ ] In a historyless source archive, do not invoke the index-based guard; emit the exact marker `SKIP pre-merge-guard: Git work tree unavailable in clean archive` and continue.
- [ ] Do not add a bypass environment variable, initialize Git metadata, or weaken `scripts/pre-merge-guard.sh` itself.
- [ ] Keep the real pre-PR lifecycle guard mandatory through `bash scripts/pre-merge-guard.sh --pr` in Task 5.

## Task 4 — Verification phase

This is a tooling/test-only plan and ships no unit or mock-test content, so the design section 2 content-verification requirements are exempt.

- [ ] Run focused scope, clean-checkout, historical-policy, integration, and curriculum-audit tests.
- [ ] Run all of `tests/test_scope.py`, `tests/test_clean_checkout.py`, `tests/test_historical_deferred_policy.py`, `tests/test_integration.py`, and `tests/test_audit_curriculum.py`.
- [ ] Run `ruff`, `git diff --check`, and the real `scripts/verify-clean-checkout.sh` with only the declared pretrained-cache mount.
- [ ] Confirm archive logs contain the raw-paper-absent overlap diagnostic, the exact pre-merge resource-skip marker, `ci-local: ALL GREEN`, and no `.git` directory.
- [ ] Run mandatory `scripts/ci-local.sh` on a clean branch tip with the local raw reference corpus available.
- [ ] Confirm normal-checkout CI runs the real pre-merge guard and that an injected nonzero guard result remains blocking.
- [ ] Run the four-way tooling/content review gate on the exact verified commit and resolve every open finding.

## Task 5 — Report and ship

- [ ] Record the passing four-way plan gate before implementation.
- [ ] Complete the post-execution report with the eight-test-failure RED witness, the ninth downstream guard witness, focused GREEN evidence, normal-checkout negative witnesses, archive mode evidence, full CI, and exact changed paths.
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

### Round 1 — exact commit `7e34e24` (2026-09-19)

- `[claude-self]` **REJECT** — the plan omitted the downstream archive failure at CI step 9, where the pre-merge guard requires a Git index.
- `[codex]` **REJECT** — independently identified the same contradiction between a no-`.git` success goal and unconditional `git ls-files` / index reads in `scripts/pre-merge-guard.sh`.
- `[fable]` **NO VERDICT** — the first job started a redundant full-suite reproduction and the bounded source-only retry did not finish after the gate was already rejected; both were cancelled before revision.
- `[glm]` **NO VERDICT** — the first job started a redundant full-suite reproduction and the bounded source-only retry did not finish after the gate was already rejected; both were cancelled before revision.

Round 1 did not reach consensus and did not authorize implementation.
This revision adds the ninth downstream failure, `scripts/ci-local.sh` to exact scope, behavioral normal/historyless guard witnesses, a fixed visible skip marker, and strict preservation of the real checkout and pre-PR guards.

### Round 2 — revised plan

Pending four-way review.

## Content Review

Pending implementation and verification.

## Post-execution report

Pending implementation.
