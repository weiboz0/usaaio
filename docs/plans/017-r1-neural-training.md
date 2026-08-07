# Plan 017 — Round 1 Neural Training Completion

## Goal

Implement `docs/designs/017-r1-neural-training.md` as the second ordered Round 1 tranche from
Plan 015.
Ship one coherent loss-to-training unit, complete C7 CNN training, resolve C7's capacity
non-conformance without weakening standards, and reduce the checker-derived Round 1 gap set from
15 neural/classical rows to the five classical rows owned by Plan 018.

## Branch and baseline

- Branch: `feature/plan-017-r1-neural-training`.
- Base: merged Plan 016 commit `708a851` on `origin/main`.
- Baseline: 17 units, 130 concepts, 383 practices, 57 lesson sessions, 91
  lesson/review/overview notebooks, 857 unit notebooks, 14,767 manifested minutes, and 15,007
  scheduled minutes.
- The branch was created before this plan and design were drafted.

## Scope

### New C11 unit

Create double-length `C11-neural-training` with prerequisites
`F4-multivar-calculus`, `C3-gradient-descent`, `C5-neural-networks`, and `C6-pytorch`.
It owns exactly:

- `softmax`;
- `cross-entropy-loss`;
- `manual-backpropagation`;
- `autograd-training`;
- `torch-optimizers`;
- `trained-mlp`;
- `batch-normalization`;
- `dropout`.

Ship five 90-minute sessions, one overview, one 60-minute review, and 24 paired practices and
solutions totaling 1,390 practice minutes.

### C7 completion

Make `C11-neural-training` the prerequisite boundary for C7, add `cnn-training`, and ship a
fourth 90-minute training session.
Rewrite C7-p10, C7-p24, and C7-p27 as 120-minute capstones that preserve their current objectives
and add honest model-training evidence.
Update C7 to double-length with four sessions, 27 practices, and final lesson/practice/review
minutes of 345/960/60.

### Curriculum evidence and schedule

Promote these ten knowledge points to `covered` with exact evidence:

1. `softmax`;
2. `cross-entropy-loss`;
3. `backpropagation-by-hand`;
4. `pytorch-autograd-and-optimizer-training`;
5. `multilayer-perceptron-model`;
6. `fully-connected-network-from-scratch`;
7. `batch-normalization`;
8. `dropout`;
9. `pytorch-deep-learning-programming`;
10. `convolutional-neural-network-basics`.

Remove `P015-R1-NEURAL-TRAINING` and the C7/C6 neural extension notices only when their consumer
rows are fully evidenced.
Regenerate the audit, roadmap, material inventory, and a 35-week prerequisite-valid course
schedule with C11 after C6 and before C7.

## Pinned problem contract

Every C11 statement names its time budget and grades every concept tag.
Set A is p01–p06, Set B is p07–p16, and Set C is p17–p24.

| Ids | Type | Difficulty | Minutes each | Primary concept contract |
|---|---|---|---:|---|
| p01 | MC, five options | intro | 20 | stable softmax and shift invariance |
| p02 | MC, five options | intro | 20 | cross-entropy / negative log likelihood |
| p03 | MC, five options | intro | 20 | backpropagation dependency and gradient shape |
| p04 | MC normal form, five options | intro | 20 | inverted-dropout train/eval behavior |
| p05 | constrained coding | intro | 30 | stable NumPy softmax |
| p06 | constrained coding | intro | 30 | categorical cross-entropy from logits via log-sum-exp |
| p07 | constrained coding | core | 45 | manual local gradients and accumulation |
| p08 | constrained coding | core | 45 | autograd gradients against hand values |
| p09 | constrained coding | core | 45 | optimizer lifecycle and parameter movement |
| p10 | constrained coding | core | 45 | deterministic trained MLP contract |
| p11 | proof/derivation | core | 50 | softmax Jacobian and fused CE gradient |
| p12 | proof/derivation | core | 50 | complete two-layer manual backpropagation |
| p13 | proof/derivation | core | 50 | BatchNorm forward and backward identities |
| p14 | integrative | core | 80 | stable softmax plus cross-entropy implementation |
| p15 | integrative | core | 80 | NumPy MLP forward/backward/update training |
| p16 | integrative | core | 80 | PyTorch autograd and optimizer training loop |
| p17 | scenario | core | 70 | trained-MLP learning-curve diagnosis |
| p18 | scenario | core | 70 | BatchNorm/dropout mode audit |
| p19 | scenario | advanced | 70 | autograd/optimizer debugging |
| p20 | scenario | advanced | 70 | trained MLP regularization ablation |
| p21 | challenge | advanced | 100 | stable fused softmax-CE plus finite differences |
| p22 | challenge | advanced | 100 | multi-layer backpropagation by hand |
| p23 | challenge | advanced | 100 | complete deterministic PyTorch training |
| p24 | challenge | advanced | 100 | BatchNorm/dropout trained-network ablation |

The table totals exactly 1,390 practice minutes.
The minimum honest coverage sets are:

- `softmax`: p01, p05, p11, p14, p21;
- `cross-entropy-loss`: p02, p06, p11, p14, p21;
- `manual-backpropagation`: p03, p07, p12, p15, p22;
- `autograd-training`: p08, p16, p19, p23;
- `torch-optimizers`: p09, p16, p19, p23;
- `trained-mlp`: p10, p15, p17, p20, p23, p24;
- `batch-normalization`: p13, p18, p20, p24;
- `dropout`: p04, p18, p20, p24.

C7-p10, C7-p24, and C7-p27 each grade `cnn-training` and retain their existing concept
deliverables.
C7-p10 certifies selective optimizer updates, C7-p24 joins hand shape tracing to construction
and training, and C7-p27 audits mode/trainability/graph controls across real train/eval steps.

## Out of scope

- Plan 018 owns logistic regression, SVM, decision trees, ensembles, and k-means.
- Round 2 owns attention/transformers, advanced vision, generative models, NLP training, and GPU
  capstones.
- No mock-test statement or answer key changes.
- No raw reference paper, verbatim past-problem text, student data, secret, local cache, or
  generated runtime dataset enters the diff.
- No dependency beyond the repository's pinned NumPy/PyTorch/Jupyter stack is added.
- Governance files `AGENTS.md`, `docs/development-workflow.md`,
  `docs/content-review-gate.md`, and `docs/architecture/decisions.md` are not modified.
- Student's t-test and importance sampling remain optional and non-required.

## Phase 0 — Pin the failing contract

### Files

- `tests/test_integration.py`
- `tests/test_audit_curriculum.py`
- `tests/test_prereq_coverage.py`
- `tests/test_scope.py`

### Work

1. Pin baseline-to-final counts at 18 units, 139 concepts, 407 practices, 63 lesson sessions,
   99 lesson/review/overview notebooks, and 913 unit notebooks.
2. Pin final manifested totals at 5,280 lesson + 10,915 practice + 865 review = 17,060 minutes
   and scheduled totals at 17,300 minutes.
3. Require C11 to be double-length with exactly five 90-minute sessions and 24 distinct practice
   ids/paths.
4. Require C7 to be double-length with four sessions, 27 distinct practices, `cnn-training`, and
   prerequisite closure through C11.
5. Require the ten target rows to become checker-derived `covered`, with no missing modality,
   `keep`, exact destinations, non-empty anchors, and required practice evidence.
6. Require the planned-unit queue to exclude `P015-R1-NEURAL-TRAINING` and the remaining Round 1
   gap ids to equal the five Plan 018 topics exactly.
7. Require a 35-week schedule: Semester 1 remains 16 weeks / 7,915 minutes; Semester 2 is 19
   weeks / 9,385 minutes; C11 finishes before C7 starts and the mock/debrief remain last.

### Verification

- Run the focused tests and capture the expected failures for missing C11/C7 content and stale
  generated evidence.
- Confirm failures are on the new contract, not unrelated baseline regressions.

## Phase 1 — Establish curriculum ownership and unit shapes

### Files

- `syllabus.md`
- `units/C11-neural-training/manifest.yaml`
- `units/C7-cnn-transfer/manifest.yaml`
- `docs/unit-standards.md`
- `TODO.md`

### Work

1. Add the nine concepts and unique owners exactly as designed.
2. Add C11's double-length unit contract and repair the pre-existing duplicate C6 `prereqs` key
   while touching the canonical syllabus block.
3. Change C7's prerequisite boundary to C11, add the fourth session/minute totals, add
   `cnn-training`, and retain exactly 27 practice entries.
4. Convert the C7 standards note from unresolved non-conformance to a recorded resolution based
   on the substantive fourth session; record that C5 remains a standard 22-problem unit because
   training moved to C11.
5. Register Plan 017 as active without marking it complete.

### Verification

- Run the Phase 1 ownership/model subset from
  `tests/test_model.py`, `tests/test_prereq_coverage.py`, and `tests/test_integration.py`; those
  assertions pass while the final artifact/count assertions remain intentionally red until
  Phases 2–5.
- `python3 -m tools.cli prereq-check .`
- `python3 -m tools.cli coverage-check .` must remain red only for intentionally missing C11/C7
  artifacts until later phases.

## Phase 2 — Build the C11 teaching spine

### Files

- `units/C11-neural-training/lesson.ipynb`
- `units/C11-neural-training/lessons/01-softmax-and-cross-entropy.ipynb`
- `units/C11-neural-training/lessons/02-manual-backpropagation.ipynb`
- `units/C11-neural-training/lessons/03-numpy-mlp-training.ipynb`
- `units/C11-neural-training/lessons/04-pytorch-autograd-and-optimizers.ipynb`
- `units/C11-neural-training/lessons/05-batchnorm-and-dropout.ipynb`
- `units/C11-neural-training/review.ipynb`

### Work

1. Dispatch lesson drafting to a fresh GPT-5.6-sol content session.
2. Teach every formula and API before it appears in a practice, from the Calculus AB + basic
   Python baseline plus declared prerequisites.
3. Include at least two fully worked exam-register examples, unit-wide pitfalls, exam
   connections, forward links, checkpoints, and collected answers.
4. Make numerical stability, tensor shapes, gradient accumulation, optimizer ordering,
   mode/state behavior, and deterministic evaluation explicit contracts.
5. Keep all training CPU-small, seeded, and free of downloads.

### Verification

- Fresh-execute all seven C11 teaching/review/overview notebooks in an isolated Jupyter config.
- Run hygiene, prerequisite, inventory parsing, and warning-strict nbformat validation on them.
- Manually trace every practice prerequisite to a preceding lesson anchor.

## Phase 3 — Author the 24 C11 student statements

### Files

- `units/C11-neural-training/practice/p01.ipynb` through `p24.ipynb`
- `units/C11-neural-training/manifest.yaml`

### Work

1. Dispatch statements to a fresh GPT-5.6-sol content session using the pinned table, not an
   answer outline.
2. Use exact identifiers, shapes, allowed APIs, zero-point bans, reasoning requirements, and
   explicit time budgets.
3. For stochastic training tasks, pin seed `20260804`, data generation, initialization,
   batching order, tolerances, and robust success invariants.
4. Prevent answer leakage: no solution prose, answer key, executed output, verifier observation,
   or unguarded helper reveals a scored result.
5. Keep every concept tag answer-affecting and every problem original.

### Verification

- `python3 -m tools.cli hygiene-check .`
- `python3 -m tools.cli prereq-check .`
- `python3 -m tools.cli coverage-check .` may remain red only for missing paired solutions.
- Structural scripts assert exact titles, types, sets, difficulty tags, ids, paths, time budgets,
  concept coverage, seeds, bans, and absence of stored outputs.

## Phase 4 — Blind-solve C11 in a separate fresh session

### Files

- `units/C11-neural-training/practice/p01_solution.ipynb` through `p24_solution.ipynb`

### Work

1. Dispatch all solutions to a separate fresh GPT-5.6-sol session that receives only the final
   student statements and repository conventions, never statement-author outlines or draft
   answers.
2. Record the blind result before adding each explanatory solution and executable check.
3. Use fixed seeds, explicit `atol`/`rtol`, independent recomputation, and a final
   `### Answer check` containing executable assertions.
4. Never relax a statement contract to fit a proposed solution; return a contradiction to the
   statement phase for correction and re-solve it blind.

### Verification

- Fresh-execute all 24 solutions in isolated kernels.
- Run answer-check permanence, tolerance, hygiene, register, prerequisite, and coverage checks.
- Confirm statements remain output-free and solution files alone contain answer material.

## Phase 5 — Complete C7 training and resolve capacity

### Files

- `units/C7-cnn-transfer/lesson.ipynb`
- `units/C7-cnn-transfer/lessons/04-cnn-training-and-fine-tuning.ipynb`
- `units/C7-cnn-transfer/review.ipynb`
- `units/C7-cnn-transfer/practice/p10.ipynb`
- `units/C7-cnn-transfer/practice/p24.ipynb`
- `units/C7-cnn-transfer/practice/p27.ipynb`
- paired p10/p24/p27 solution notebooks
- `units/C7-cnn-transfer/manifest.yaml`

### Work

1. Dispatch the lesson and three final statements to a fresh GPT-5.6-sol content session.
2. Preserve each rewritten problem's existing scored objective and add a separable, substantive
   training objective; do not use decorative tags.
3. Blind-solve the three final statements in another fresh GPT-5.6-sol session before solution
   access, using the same independence rules as Phase 4.
4. Use tiny synthetic CPU data, no pretrained-weight download, no network access, and robust
   loss/parameter/buffer invariants.

### Verification

- Fresh-execute the new C7 lesson, changed overview/review, and all three changed solutions.
- Run a corruption test that wrong optimizer ordering, uncommitted predictions, parameter
  leakage, or mode misuse fails the real answer check.
- Run focused prerequisite/coverage tests proving four sessions + 27 practices is a compliant
  double-length unit and `cnn-training` has three distinct practices.

## Phase 6 — Promote evidence and regenerate the schedule

### Files

- `curriculum/coverage-map.yaml`
- `curriculum/material-inventory.yaml`
- `docs/audits/015-coverage-audit.md`
- `docs/curriculum-roadmap.md`
- `docs/course-structure.md`
- `syllabus.md`
- relevant audit/integration/scope tests

### Work

1. Add exact primary/secondary lesson anchors and honest practice evidence for all ten targets.
2. Remove `P015-R1-NEURAL-TRAINING` only after its eight owned rows are covered.
3. Regenerate the audit and roadmap; assert the Round 1 gap set is exactly the five Plan 018
   classical topics and no completed neural unit remains in a pending extension table.
4. Regenerate material inventory after every final notebook change.
5. Expand the course to 35 weeks without altering Semester 1: S1 is 7,915 minutes over 16 weeks,
   S2 is 9,385 minutes over 19 weeks, and total scheduled time is 17,300 minutes.
6. Keep strict order C5 → C6 → C11 → C7 and keep the mock/debrief at the final gate.

### Verification

- `python3 tools/audit_curriculum.py --check`
- `python3 tools/render_curriculum_roadmap.py --check`
- material-inventory check mode
- focused schedule arithmetic and prerequisite-order tests
- `python3 -m tools.cli scope-check .` with only Round 2 warnings and the five explicit Plan 018
  Round 1 warnings.

## Phase 7 — Named verification phase

This phase is mandatory because the plan ships and changes teaching units.

1. Fresh-execute all 27 changed/new solution notebooks and all changed/new
   lesson/review/overview notebooks in isolated Jupyter kernels.
2. Confirm every solution reproduces its statement contract and final answer check.
3. Run statement hygiene, warning-strict nbformat validation for all changed notebooks, manifest
   validation, blueprint conformance, overlap scan, prerequisite closure, practice coverage,
   scope, answer-key, tolerance, inventory, audit-freshness, roadmap-freshness, and PDF build.
4. Run focused tests first, then `scripts/ci-local.sh` from a clean commit.
5. Confirm exact final corpus values: 18 units, 139 concepts, 407 practices, 63 lesson sessions,
   99 lesson/review/overview notebooks, 913 unit notebooks, 17,060 manifested minutes, and 17,300
   scheduled minutes.
6. Confirm no ignored runtime dataset, model artifact, raw reference, secret, or stored student
   output is tracked.

## Phase 8 — Four-way content gate, report, and shipping

1. Self-review blind-solves all 27 changed/new statements before solution access.
2. In one parallel dispatch, run fresh read-only reviewers on exact Claude Opus 5,
   GPT-5.6-terra, and exact GLM-5.2.
3. Require each reviewer to blind-solve all 27 statements, inspect lessons as a Calculus AB +
   basic Python student, review tooling changes, and record findings in `## Content Review`.
4. Resolve every `[OPEN]` finding and rerun affected solutions/checks; conduct delta review to
   four-way consensus.
5. Write the post-execution report with exact artifacts, deviations, reviewer divergence,
   execution evidence, limitations, and remaining Plan 018 scope.
6. Mark Plan 017 complete in `TODO.md`, run a final clean-commit `scripts/ci-local.sh`, push, open
   a PR, run `scripts/pre-merge-guard.sh --pr`, and squash-merge.

## Acceptance criteria

- The four-way plan-review gate passes before implementation begins.
- C11 and C7 satisfy the exact structural, timing, authorship, and practice contracts above.
- All ten neural knowledge points are checker-derived `covered`; the Round 1 gap set contains
  exactly the five Plan 018 classical topics.
- C7 is substantively four-session/double-length and no longer a recorded non-conformance.
- C5 remains a standard 22-problem unit and is not overloaded.
- All 27 changed/new solutions and all changed teaching notebooks fresh-execute cleanly.
- The four-way content gate passes with no `[OPEN]` finding.
- Final `scripts/ci-local.sh` and PR-aware pre-merge guard pass from the shipping commit.
- The branch is squash-merged through a PR; no direct main commit occurs.

## Plan Review

### Review 1 — self (2026-08-07)

- **Verdict:** APPROVED.
- `[self] [FIXED]` Phase 1 originally named the whole integration files as if every final artifact
  assertion should pass before notebooks existed.
  The verification contract now distinguishes the passing ownership/model subset from the
  deliberately red Phase 0 end-state tests.
- `[self] [FIXED]` C11-p06 originally used ambiguous “clipped/stable” wording.
  The pinned contract now requires cross-entropy from logits through log-sum-exp, consistent with
  the stable derivation in Session 1.
- `[self]` Recomputed the exact deltas independently: C11 contributes 1,900 minutes; C7 contributes
  393; 14,767 + 2,293 = 17,060 manifested and 15,007 + 2,293 = 17,300 scheduled.
  The notebook/count deltas are likewise internally consistent.
- `[self]` The selected C11-plus-C7 design closes the eight planned-unit rows and the two adjacent
  existing-unit modalities named by the canonical queue without entering Plan 018 or Round 2.
  C7 satisfies the existing double-length standard substantively rather than by label alone.
- No open self-review finding remains.

## Content Review

Content-review findings are recorded here during Phase 8.

## Post-Execution Report

Completed during Phase 8 before shipping.
