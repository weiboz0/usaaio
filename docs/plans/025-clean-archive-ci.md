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

- [x] Retain the exact failing `scripts/verify-clean-checkout.sh` output as the RED witness: eight failures, 1,160 passes, one skip.
- [x] Add a scope regression proving a structurally valid merged reconciliation is accepted when the inspected tree has no Git metadata.
- [x] Convert the existing bad-squash ancestry regression into a real temporary Git repository so it still proves that an available but non-ancestor commit is rejected.
- [x] Make the ignore-contract regression exercise the real tracked `.gitignore` with an isolated temporary Git metadata directory and explicit work tree; do not replace Git semantics with substring matching.
- [x] Make the historical deferred-policy test skip with an explicit reason only when the current source tree has no Git metadata; it must still run the real historical script in a normal checkout.
- [x] Make the overlap integration assertion require a completed scan when a reference index/PDF exists and require the exact `reference corpus absent` skip when the intentionally clean archive lacks that corpus.
- [x] Add or retain negative witnesses showing that malformed reconciliation data, a real non-ancestor commit, wrong ignore patterns, and overlap errors still fail.
- [x] Add a behavioral CI regression proving a normal Git checkout invokes `scripts/pre-merge-guard.sh`, while a source archive without Git metadata emits one exact resource-skip marker and continues to `ci-local: ALL GREEN`.
- [x] Prove the no-Git path cannot be selected merely by an environment variable and that a failing pre-merge guard remains blocking whenever Git metadata exists.
- [x] Cover an archive nested beneath an unrelated parent Git work tree and a corrupt local `.git` marker: the unrelated parent must not select the guard, while corrupt metadata at the archive root must fail loudly rather than select the skip.

## Task 2 — Separate unavailable history from failed ancestry

- [x] In `tools/checks/scope.py`, anchor the repository probe to the canonical inspected repository root before running `git merge-base --is-ancestor`; an unrelated enclosing repository is not history for the inspected tree.
- [x] If no Git work tree exists, retain all reconciliation-document structure checks but omit only the unreconstructible ancestry query.
- [x] If root-local Git metadata exists, preserve the current rejection for a missing or non-ancestor squash commit and fail loudly if that metadata is unusable.
- [x] Do not use environment flags, dates, network access, or mutable repository state to choose the mode.

## Task 3 — Keep the pre-merge guard strict and resource-scoped

- [x] In `scripts/ci-local.sh`, detect root-local Git work-tree availability immediately before step 9: canonical `git rev-parse --show-toplevel` must equal canonical `repo_root`; an enclosing parent work tree does not count, while any root-local `.git` file, directory, or symlink that cannot support the probe is an error rather than a skip.
- [x] In a normal checkout, invoke `bash scripts/pre-merge-guard.sh` exactly as before and propagate every nonzero result.
- [x] In a historyless source archive, do not invoke the index-based guard; emit the exact marker `SKIP pre-merge-guard: Git work tree unavailable in clean archive` and continue.
- [x] Do not add a bypass environment variable, initialize Git metadata, or weaken `scripts/pre-merge-guard.sh` itself.
- [x] Keep the real pre-PR lifecycle guard mandatory through `bash scripts/pre-merge-guard.sh --pr` in Task 5.

## Task 4 — Verification phase

This is a tooling/test-only plan and ships no unit or mock-test content, so the design section 2 content-verification requirements are exempt.

- [x] Run focused scope, clean-checkout, historical-policy, integration, and curriculum-audit tests.
- [x] Run all of `tests/test_scope.py`, `tests/test_clean_checkout.py`, `tests/test_historical_deferred_policy.py`, `tests/test_integration.py`, and `tests/test_audit_curriculum.py`.
- [x] Run `ruff`, `git diff --check`, and the real `scripts/verify-clean-checkout.sh` with only the declared pretrained-cache mount.
- [x] Confirm archive logs contain the raw-paper-absent overlap diagnostic, the exact pre-merge resource-skip marker, `ci-local: ALL GREEN`, and no `.git` directory.
- [x] Run mandatory `scripts/ci-local.sh` on a clean branch tip with the local raw reference corpus available.
- [x] Confirm normal-checkout CI runs the real pre-merge guard and that an injected nonzero guard result remains blocking.
- [x] Run the four-way tooling/content review gate on the exact verified commit and resolve every open finding.

## Task 5 — Report and ship

- [x] Record the passing four-way plan gate before implementation.
- [x] Complete the post-execution report with the eight-test-failure RED witness, the ninth downstream guard witness, focused GREEN evidence, normal-checkout negative witnesses, archive mode evidence, full CI, and exact changed paths.
- [x] Add Plan 025's shipped status to `TODO.md` without changing unrelated entries.
- [x] Commit final records and rerun authoritative clean-tip `scripts/verify-clean-checkout.sh` and `scripts/ci-local.sh`.
- [ ] Push, open a PR with `GH_TOKEN=$(cat .gh-token)`, run `bash scripts/pre-merge-guard.sh --pr`, and squash-merge.
- [ ] Return to `feature/plan-023-plan019-historical-cutover`, merge corrected `main`, rerun Plan 023 verification, and resume its gate and shipping lifecycle.

## Out of scope

- Plan 023's historical cutover implementation or records.
- Adding a Git repository to archive output.
- Copying raw past-test papers into a clean archive.
- Changing `.gitignore`, overlap thresholds, curriculum scope, or reconciliation policy.
- Any curriculum-content or generated-evidence change.
- Design section 2 content verification: this tooling/test-only plan ships no unit or mock-test content and instead uses the named tooling verification phase in Task 4.

## Plan Review

### Round 1 — exact commit `7e34e24` (2026-09-19)

- `[claude-self]` **REJECT** — the plan omitted the downstream archive failure at CI step 9, where the pre-merge guard requires a Git index.
- `[codex]` **REJECT** — independently identified the same contradiction between a no-`.git` success goal and unconditional `git ls-files` / index reads in `scripts/pre-merge-guard.sh`.
- `[fable]` **NO VERDICT** — the first job started a redundant full-suite reproduction and the bounded source-only retry did not finish after the gate was already rejected; both were cancelled before revision.
- `[glm]` **NO VERDICT** — the first job started a redundant full-suite reproduction and the bounded source-only retry did not finish after the gate was already rejected; both were cancelled before revision.

Round 1 did not reach consensus and did not authorize implementation.
This revision adds the ninth downstream failure, `scripts/ci-local.sh` to exact scope, behavioral normal/historyless guard witnesses, a fixed visible skip marker, and strict preservation of the real checkout and pre-PR guards.

### Round 2 — revised plan

Exact commit `bd65f0a` reached consensus on 2026-09-19:

- `[claude-self]` **APPROVE** — the ninth failure, strict normal-checkout behavior, archive-only skip, negative witnesses, and lifecycle are complete.
- `[codex]` **APPROVE** — confirmed the Round-1 blocker is closed without weakening the real guard.
- `[fable]` **APPROVE WITH NITS** — requested root-anchored Git detection that cannot inherit a parent repository and placement of the tooling exemption in `## Out of scope`.
- `[glm]` **APPROVE WITH NITS** — requested explicit behavior for enclosing repositories and corrupt root-local Git metadata; its tag-renaming nit was not adopted because the active project instructions require `[claude-self]` and `[codex]`.

All actionable nits are resolved in this gate-record update without changing scope or architecture.
The four-way plan gate is passed and implementation is authorized.

## Content Review

Exact implementation commit reviewed: `81321cc`.

- `[claude-self]` **APPROVE** — manual adversarial inspection confirmed that resource absence is explicit and narrow, while corrupt, mismatched, and available-but-negative Git evidence remains blocking.
- `[codex]` **APPROVE** — the independent GPT-5.6-terra review found no open findings and passed nine clean-checkout/guard/global-ignore witnesses plus eight scope Git-boundary witnesses.
- `[opus]` **APPROVE WITH NITS** — no blockers; suggested richer Git-probe diagnostics, removing a redundant canonicalization assignment, and additionally isolating ambient Git variables during bare-repository test setup.
- `[glm]` **APPROVE WITH NITS** — no blockers; suggested centralizing the overlap-corpus predicate and retaining Git-probe stderr in diagnostics.

Resolved findings:

- `[codex][FIXED]` Relative `--root` could previously select the historyless path from a real checkout; `56b4c4b` canonicalizes the root before changing directory and adds the discriminating regression.
- `[opus][FIXED]` Parent-repository and corrupt/partial root-local Git metadata could be confused; `772c261` anchors and isolates the probe, with both negative witnesses.
- `[opus][FIXED]` History absence lacked an explicit scope-check diagnostic, `merge-base` return codes were conflated, ignore behavior could inherit global excludes, and exported Git variables could poison probes; `81321cc` closes all four cases and adds behavioral witnesses.
- `[opus][WONTFIX]` and `[glm][WONTFIX]` The remaining diagnostic-detail and predicate-deduplication suggestions are non-blocking polish outside the correctness contract; current errors remain loud and all branches are behaviorally covered.

All four reviewers returned **APPROVE** or **APPROVE WITH NITS** on the exact verified implementation.
There are no `[OPEN]` findings.

## Post-execution report

### RED evidence

- The original real-archive run stopped with eight failures after `1,160 passed, 1 skipped`; failures were confined to Git-history, ignore, historical-policy, and absent-reference assumptions.
- Exercising the otherwise-unreached ninth stage in a historyless tree produced `fatal: not a git repository`, proving that the unconditional pre-merge guard was a second independent blocker.
- The first content review found that relative `--root` bypassed the real-checkout guard path; its trace witness was absent before `56b4c4b`.
- Ambient `GIT_DIR` / `GIT_WORK_TREE` poisoning initially broke two boundary witnesses; both became green only after the clean-environment probe in `81321cc`.

### Implemented contract

- `tools/checks/scope.py` now preserves every reconciliation structure check without history, emits one explicit ancestry-unavailable warning, and keeps missing, non-ancestor, corrupt, mismatched, and incomplete Git history blocking when Git metadata exists.
- `scripts/ci-local.sh` now canonicalizes `--root`, strips exported `GIT_*` variables from its Git probe and guard, invokes the real guard only for a matching root-local checkout, and emits the one exact archive skip marker otherwise.
- The four focused test modules plus the curriculum-audit suite now distinguish normal checkout, historyless archive, unrelated parent checkout, corrupt/partial metadata, ambient-environment poisoning, missing Git, unknown commits, guard failure, isolated ignore semantics, and overlap-resource modes.

### GREEN evidence

- Focused final suite: `392 passed, 2 warnings in 182.59s`; Ruff, Bash syntax, and `git diff --check` also passed.
- Real `git archive HEAD` verification with only `USAAIO_REFERENCE_CACHE` mounted: `1178 passed, 1 skipped, 20 warnings in 367.82s`; all notebooks executed; register verification was `437/437`; five training, five classical, and five attention mutations passed; Book 1 rendered 10 sources; Book 2 rendered 64 sources; the overlap step emitted the exact absent-corpus remedy; step 9 emitted `SKIP pre-merge-guard: Git work tree unavailable in clean archive`; final line was `ci-local: ALL GREEN`.
- Normal-checkout `scripts/ci-local.sh`: `1179 passed, 20 warnings in 337.78s`; all notebooks and mutation gates passed; the local overlap corpus was scanned; Book 1 rendered 10 sources; Book 2 rendered 64 sources; the real guard reported `pre-merge-guard: OK`; final line was `ci-local: ALL GREEN`.
- Negative tests prove an injected nonzero guard remains blocking and that no environment flag, parent repository, corrupt metadata, unknown commit, or incomplete history can select a false-success path.

### Changed paths

- `docs/plans/025-clean-archive-ci.md`
- `scripts/ci-local.sh`
- `tests/test_clean_checkout.py`
- `tests/test_historical_deferred_policy.py`
- `tests/test_integration.py`
- `tests/test_scope.py`
- `tools/checks/scope.py`
- `TODO.md` at shipping time

No teaching material, solution, manifest, curriculum inventory, generated evidence, ignore rule, or governance file changed.
The verified implementation is ready to ship.
