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
solutions totaling 1,040 practice minutes.
Its exact `concepts_used` list is `[numpy-arrays, array-indexing-slicing, elementwise-ops,
broadcasting, vectorization, aggregation-axis, random-seeding, matplotlib-basics,
partial-derivatives, gradient, multivar-chain-rule, gradient-descent, learning-rate,
stochastic-gd, loss-surfaces, expectation, variance, perceptron, activation-functions,
relu-activation, mlp-architecture, weight-init-variance, overfitting, l2-regularization,
python-inheritance, torch-tensors, nn-module, requires-grad, parameter-counting]`.

### C7 completion

Make `[C6-pytorch, C11-neural-training]` the explicit prerequisite boundary for C7, add
`cnn-training`, and ship a fourth 90-minute training session.
Expand C7-p10, C7-p24, C7-p26, and C7-p27 as 75-minute capstones that preserve separately scored
current objectives and add honest model-training evidence.
Update C7 to double-length with four sessions, 27 practices, and final lesson/practice/review
minutes of 345/875/60.
The practice recalibration is explicit: retain the old 672-minute aggregate, remove one combined
97-minute editorial allowance for the four replaced statements, and add 4 × 75 = 300 minutes,
giving 672 − 97 + 300 = 875.
The 97-minute value is a combined planning allowance from manual scope review, not four claimed
historical measurements and not per-problem manifest data.
The 30.97-hour executable tranche is 7.03 hours below Plan 015's combined 38–56-hour editorial
range for the planned neural unit plus C7 extension.
That range preceded problem-level calibration; the post-execution report must reconcile the
difference, and acceptance remains the ten exact modality/evidence contracts and fresh execution,
not padding content to an estimated hour floor.

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
Introduce `curriculum/course-schedule.yaml` as the canonical allocation and render the schedule
table/document from that data so CI checks the calendar rather than trusting prose arithmetic.

## Pinned problem contract

Every C11 statement names its time budget and grades every concept tag.
Set A fundamentals are p01–p03 and p05–p10.
Set B exam-register problems are p04 and p11–p13.
Set C integration/scenario/challenge problems are p14–p24.
Every owned concept has an answer-affecting Set A encounter: p01/p05 cover softmax, p02/p06
cross-entropy, p03/p07 manual backpropagation, p08 separately checks an autograd gradient and an
optimizer-driven parameter update, p07 checks a manual trained-MLP update, p09 BatchNorm, and p10
dropout.
Set membership is the concept-encounter progression and is tracked independently of difficulty
within the standard's allowed Set A intro/core and Set C integration/advanced bands.

| Ids | Type | Difficulty | Minutes each | Primary concept contract |
|---|---|---|---:|---|
| p01 | MC, five options | intro | 15 | stable softmax and shift invariance |
| p02 | MC, five options | intro | 15 | cross-entropy / negative log likelihood |
| p03 | MC, five options | intro | 15 | manual-backpropagation dependency order and gradient shape |
| p04 | numeric MC normal form, five options | intro | 15 | inverted-dropout expectation ratio as a reduced signed fraction with gcd constraint |
| p05 | constrained coding | intro | 25 | stable NumPy softmax |
| p06 | constrained coding | intro | 25 | categorical cross-entropy from logits via log-sum-exp |
| p07 | constrained coding | core | 35 | manual local gradients, accumulation, and one certified MLP update |
| p08 | constrained coding | core | 35 | autograd gradient against a hand value plus a separately certified optimizer update |
| p09 | constrained coding | core | 35 | BatchNorm forward implementation with batch/running statistics and affine parameters |
| p10 | constrained coding | core | 35 | inverted-dropout implementation with deterministic train/eval behavior |
| p11 | proof/derivation | core | 40 | softmax Jacobian and fused CE gradient |
| p12 | proof/derivation | core | 40 | complete two-layer manual backpropagation |
| p13 | proof/derivation | core | 40 | BatchNorm forward and backward identities |
| p14 | integrative | core | 60 | stable softmax plus cross-entropy implementation |
| p15 | integrative | core | 60 | NumPy MLP forward/backward/update training |
| p16 | integrative | core | 60 | PyTorch autograd and optimizer training loop |
| p17 | scenario | core | 50 | trained-MLP learning-curve diagnosis |
| p18 | scenario | core | 50 | BatchNorm/dropout mode audit |
| p19 | scenario | advanced | 50 | autograd/optimizer debugging |
| p20 | scenario | advanced | 50 | trained MLP regularization ablation |
| p21 | challenge | advanced | 70 | stable fused softmax-CE plus finite differences |
| p22 | challenge | advanced | 70 | multi-layer backpropagation by hand |
| p23 | challenge | advanced | 75 | complete deterministic PyTorch training |
| p24 | challenge | advanced | 75 | optimizer-controlled BatchNorm/dropout trained-network ablation |

The table totals exactly 1,040 practice minutes.
The 6/12/6 intro/core/advanced split is 25%/50%/25%, within the unit standard's deliberately
rough 30%/45%/25% target.
The matching five-point intro deficit/core excess keeps implementation/derivation prerequisites
in the middle band and avoids misclassifying a 35-minute gradient implementation as intro or
pushing it into challenge.
The minimum honest coverage sets are:

- `softmax`: p01, p05, p11, p14, p21;
- `cross-entropy-loss`: p02, p06, p11, p14, p21;
- `manual-backpropagation`: p03, p07, p12, p15, p22;
- `autograd-training`: p08, p16, p19, p23;
- `torch-optimizers`: p08, p16, p19, p23, p24;
- `trained-mlp`: p07, p15, p17, p20, p23, p24;
- `batch-normalization`: p09, p13, p18, p20, p24;
- `dropout`: p04, p10, p18, p20, p24.

The coverage-map promotion uses these exact primary practices for every newly closed modality;
pre-existing modalities retain their already registered C5/C6/C7 evidence:

| Knowledge point | Newly closed modality → primary practice |
|---|---|
| softmax | theory → C11-p01; derivation → C11-p11; implementation → C11-p05 |
| cross-entropy-loss | theory → C11-p02; derivation → C11-p11; implementation → C11-p06 |
| backpropagation-by-hand | theory → C11-p03; derivation → C11-p12; implementation → C11-p07 |
| pytorch-autograd-and-optimizer-training | implementation → C11-p08; model-training → C11-p16 |
| multilayer-perceptron-model | model-training → C11-p15 |
| fully-connected-network-from-scratch | model-training → C11-p15 |
| batch-normalization | derivation → C11-p13; implementation → C11-p09; model-training → C11-p24 |
| dropout | theory → C11-p04; implementation → C11-p10; model-training → C11-p24 |
| pytorch-deep-learning-programming | model-training → C11-p16 |
| convolutional-neural-network-basics | model-training → C7-p10 |

C7-p10, C7-p24, C7-p26, and C7-p27 each grade `cnn-training` and retain their existing concept
deliverables.
C7-p10 certifies selective optimizer updates, C7-p24 joins hand shape tracing to construction
and training, C7-p26 joins a general shape helper to a valid trained stack, and C7-p27 audits
mode/trainability/graph controls across real train/eval steps.

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

## Execution ownership

Before Phase 0, dispatch the `tools/`, `scripts/`, and tooling-test work in Phases 0, 1, 5, and
6 to a fresh GPT-5.6-sol tooling session as required by `AGENTS.md`.
The active orchestrator assembles the fail-first test contract, integrates the returned changes,
and runs verification; lesson/statement and blind-solution sessions remain separate.

## Phase 0 — Pin the failing contract

### Files

- `tests/test_integration.py`
- `tests/test_model.py`
- `tests/test_audit_curriculum.py`
- `tests/test_prereq_coverage.py`
- `tests/test_scope.py`
- `tests/test_schedule.py`
- `tests/test_training_mutations.py`

### Work

1. Pin baseline-to-final counts at 18 units, 139 concepts, 407 practices, 63 lesson sessions,
   99 lesson/review/overview notebooks, and 913 unit notebooks.
2. Pin final manifested totals at 5,280 lesson + 10,480 practice + 865 review = 16,625 minutes
   and scheduled totals at 16,865 minutes.
3. Require C11 to be double-length with exactly five 90-minute sessions and 24 distinct practice
   ids/paths.
   Assert exact equality with the pinned `concepts_used` list in Scope; prerequisite closure alone
   must not permit extra in-closure declarations.
   Extend the optional manifest practice schema with positive integer `minutes`; if any problem
   in a unit declares it, every problem must, ids/paths remain distinct, and the sum must equal
   `estimated_minutes.practice`.
   C11's exact 24-row minutes are the pinned table above.
4. Require C7's canonical syllabus entry to set `length: double`, four sessions, 27 distinct
   practices, `cnn-training`, and explicit prerequisites `[C6-pytorch, C11-neural-training]`.
   Require the exact `cnn-training` practice-id set
   `{C7-p10, C7-p24, C7-p26, C7-p27}` while preserving p10's
   layer-freezing/module/gradient/parameter-count contract, p24's tensor-shape trace, p26's
   convolution/shape-helper contract, and p27's layer-freezing/gradient-control contract.
5. Require the ten target rows to become checker-derived `covered`, with no missing modality,
   `keep`, the exact single destinations and `shipped_concepts` additions in the design table,
   non-empty anchors, and required practice evidence.
   Assert exact equality for every `(knowledge point, newly closed modality) → primary practice
   id` mapping in the pinned table; a same-concept substitute must fail the fixture.
6. Require the planned-unit queue to exclude `P015-R1-NEURAL-TRAINING` and the remaining Round 1
   gap ids to equal the five Plan 018 topics exactly.
7. Require a 35-week schedule: Semester 1 remains 16 weeks / 7,915 minutes; Semester 2 is 19
   weeks / 8,950 minutes; every week totals 450–500 minutes, C11 finishes before C7 starts, and
   the mock/debrief remain last.
8. Pin a fail-closed schedule consumer that accounts for every manifested lesson session exactly
   once, reconciles per-unit practice/review totals, enforces prerequisite completion before a
   dependent starts, and reconciles the mock/debrief with `r1-001`.
   Parse the rendered first-instruction region and require exact ordered equality with every
   shipped unit's canonical `(unit, first-instruction week)` allocation derived from
   `curriculum/course-schedule.yaml`; checking only the C5 → C6 → C11 → C7 subsequence is
   insufficient.
9. Pin a mutation-runner registry against the real solution notebooks and require zero-match,
   multi-match, non-failing-mutant, and wrong-failure-location fixtures to fail.
10. Pin the suggested syllabus order and its integration consumer to insert C11 between C6 and
    C7, and pin the C5 → C6 → C11 → C7 engineering-ladder narrative.
11. Measure one `708a851` clean-base `scripts/ci-local.sh` wall-clock baseline in a separate
    isolated worktree and project environment before fail-first tests alter the branch, and record
    it in the eventual post-execution report.
    The final full gate may add at most 900 seconds; if it exceeds that budget, reduce dataset/
    epoch sizes while preserving every numerical and mutation invariant rather than skipping a
    notebook or weakening an answer check.

### Verification

- Run the focused tests and capture the expected failures for missing C11/C7 content and stale
  generated evidence.
- Confirm failures are on the new contract, not unrelated baseline regressions.

## Phase 1 — Establish curriculum ownership and unit shapes

### Files

- `syllabus.md`
- `tools/model.py`
- `tools/checks/coverage.py`
- `units/C11-neural-training/manifest.yaml`
- `units/C7-cnn-transfer/manifest.yaml`
- `docs/unit-standards.md`
- `TODO.md`
- `tests/test_integration.py`
- `scripts/verify-register.py`
- `tests/test_verify_register.py`

### Work

1. Add the nine concepts and unique owners exactly as designed.
2. Add C11's double-length unit contract and the exact `concepts_used` list pinned in Scope to
   the canonical syllabus/manifest block; C6 remains unchanged.
3. Set C7's canonical `length: double`, change its prerequisites to
   `[C6-pytorch, C11-neural-training]`, add the fourth session/minute totals, add `cnn-training`,
   extend `concepts_used` with `softmax`, `cross-entropy-loss`, `autograd-training`,
   `torch-optimizers`, `batch-normalization`, and `dropout`, and retain exactly 27 practice
   entries.
   Keep C7's 875-minute practice total canonical at unit level.
   The four rewritten statements each name a 75-minute authoring/assessment budget, but C7 does
   not opt into the new per-problem manifest field because the unchanged 23 problems have no
   measured individual-minute evidence.
4. Preserve the full Plan 014 rejection history in the C7 standards note and append a recorded
   Plan 017 resolution rather than replacing that history.
   Explain why the new outcome differs from the rejected label-only attempt: C7 now has a real
   fourth 90-minute session and 27 practices, satisfying both double-length bands; its final
   1,280 minutes exceed the pre-plan 1,120-minute corpus maximum.
   Record that its 345 lesson minutes across four sessions are lighter than F5's 415/5, F6's
   425/5, and C11's 450/5, while F7 demonstrates that four sessions alone do not imply
   double-length because its 20 practices remain in the standard band.
   Also record that C5 remains a standard 22-problem unit because training moved to C11, update
   the double-length roster to F5, F6, C7, and C11, and correct the stale maxima claim by naming
   C10's 12 taught concepts as the concept maximum and C11's 1,040 practice minutes as the
   practice maximum.
5. Update the syllabus core rationale, double-length narrative, and suggested topological order,
   plus their exact integration assertions, so C11 appears between C6 and C7 and “the other
   double-length unit” is no longer asserted.
6. Implement the optional per-problem minute loader/coverage contract and fail-closed fixtures;
   units without any per-problem minutes remain backward-compatible.
7. Extend `scripts/verify-register.py`'s permanent register to C11.
   Require p01–p04 to expose exactly five labeled options A–E and the reasoning flag, require every
   C11 statement to carry a body line `**Time budget:** <minutes> minutes` matching its manifest
   value, and keep the existing metadata header schema exactly `{Type, Difficulty, Concepts}`;
   time is not a fourth header field.
   Add fail-closed fixtures in `tests/test_verify_register.py` for four-vs-five options, missing or
   wrong reasoning flag, missing/mismatched body budget, and an attempted fourth header field.
8. Register Plan 017 as active without marking it complete.
   Atomically replace the stale deferred C7/C5 capacity TODO with the resolved decision: C7 is a
   substantive four-session double-length unit, while C5 remains a compliant standard 22-problem
   unit because neural training moved to C11.

### Verification

- Run the Phase 1 ownership/model subset from
  `tests/test_model.py`, `tests/test_prereq_coverage.py`, and `tests/test_integration.py`; those
  assertions pass while the final artifact/count assertions remain intentionally red until
  Phases 2–5.
- `uv run pytest tests/test_verify_register.py -q`
- Do not run the repository-wide register yet: the Phase 1 C11 manifest intentionally precedes
  its Phase 3 statement files, so only temporary-fixture tests are green in this bounded window;
  the first corpus register run is required after all 24 statement paths exist.
- `uv run usaaio-tools prereq-check`
- `uv run usaaio-tools coverage-check` must remain red only for intentionally missing C11/C7
  artifacts until later phases.
- `uv run usaaio-tools scope-check` is expected to report exactly the eight provisional-concept
  collisions while the eight C11 concepts coexist with the still-planned neural unit; no other
  scope error is accepted before Phase 6 removes that planned row and promotes real evidence.

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

- `uv run usaaio-tools hygiene-check`
- `uv run usaaio-tools prereq-check`
- `uv run usaaio-tools coverage-check` may remain red only for missing paired solutions.
- Structural scripts assert exact titles, types, sets, difficulty tags, ids, paths, time budgets,
  concept coverage, seeds, bans, and absence of stored outputs.
- `uv run python scripts/verify-register.py`

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
- `units/C7-cnn-transfer/practice/p26.ipynb`
- `units/C7-cnn-transfer/practice/p27.ipynb`
- paired p10/p24/p26/p27 solution notebooks
- `units/C7-cnn-transfer/manifest.yaml`
- `scripts/verify-register.py`
- `tests/test_verify_register.py`
- `tools/verify_training_mutations.py`
- `tests/test_training_mutations.py`

### Work

1. Dispatch the lesson and four final statements to a fresh GPT-5.6-sol content session.
2. Preserve each rewritten problem's existing scored objective and add a separable, substantive
   training objective; do not use decorative tags.
3. Blind-solve the four final statements in another fresh GPT-5.6-sol session before solution
   access, using the same independence rules as Phase 4.
4. Use tiny synthetic CPU data, no pretrained-weight download, no network access, and robust
   loss/parameter/buffer invariants.
5. In the same phase as the four C7 rewrites, extend the register with an explicit literal map
   `{C7-p10, C7-p24, C7-p26, C7-p27} → 75` and require matching body-budget lines.
   Comment why this is deliberately separate from C11's manifest-driven mechanism: C7 has no
   honest historical per-problem minute data, so any future capstone-budget change must update
   both the statement and this exception map.
   Add fail-closed `tests/test_verify_register.py` fixtures for a missing required C7 id, a
   non-75 literal map value, and a statement body budget that disagrees with the literal map.

### Verification

- Fresh-execute the new C7 lesson, changed overview/review, and all four changed solutions.
- `uv run pytest tests/test_verify_register.py -q`
- `uv run python scripts/verify-register.py`
- Run the permanent mutation registry against the real solutions.
  It must apply these exactly-once corruptions and observe failure in the registered final answer
  check: C11-p16 moves `zero_grad` after `backward`; C11-p23 replaces `optimizer.step()` with a
  no-op; C7-p10 enables a forbidden frozen-parameter update; C7-p27 moves committed predictions
  below the marked verifier; and C7-p27 separately substitutes training mode for the registered
  evaluation/buffer audit.
  C7-p27 intentionally owns two distinct registered mutations, so these four notebooks produce
  five mutant executions in total.
- The runner copies notebooks to a temporary directory, applies source-level mutations only at
  registered sentinels, executes each mutant, and fails if a target resolves zero/multiple times,
  if execution succeeds, or if failure occurs before the expected answer-check/verifier cell.
- Run focused prerequisite/coverage tests proving four sessions + 27 practices is a compliant
  double-length unit and that the exact four ids
  `{C7-p10, C7-p24, C7-p26, C7-p27}` grade `cnn-training` while retaining every pinned original
  concept contract.

## Phase 6 — Promote evidence and regenerate the schedule

### Files

- `curriculum/coverage-map.yaml`
- `curriculum/material-inventory.yaml`
- `docs/audits/015-coverage-audit.md`
- `docs/curriculum-roadmap.md`
- `docs/course-structure.md`
- `docs/curriculum-architecture.md`
- `syllabus.md`
- `curriculum/course-schedule.yaml`
- `tools/model.py`
- `tools/cli.py`
- `tools/checks/schedule.py`
- `tools/render_course_structure.py`
- `tools/render_curriculum_roadmap.py`
- `tools/audit_curriculum.py`
- `scripts/ci-local.sh`
- `tests/test_schedule.py`
- `tests/test_scope.py`
- relevant audit/integration tests

### Work

1. Regenerate material inventory after every final notebook change, before writing coverage-map
   anchors, so every `(path, heading, cell_ordinal)` triple is validated against fresh data.
2. Add exact primary/secondary lesson anchors and honest practice evidence for all ten targets.
   Apply the exact single destinations and `shipped_concepts` additions from the design table;
   composite prose owners are forbidden.
3. Remove `P015-R1-NEURAL-TRAINING` only after its eight owned rows are covered.
   In the same atomic edit, replace that id with shipped `C11-neural-training` in the
   prerequisites of `P015-R2-TRANSFORMERS-NLP` and `P015-R2-VISION-GEN`; scope-check must reject
   any dangling planned-unit reference.
4. Make roadmap pending-state prose consumer-driven.
   Existing-unit extension rows are keyed to uncovered knowledge points, and tranche-queue rows
   are keyed to still-present `planned_units`; covering/removing the neural owners must suppress
   C7, only the obsolete C6 clause from the combined C6/C8 completion sentence, and the neural-
   tranche queue entry without a second manual status flag; the still-uncovered Round 2 C8 clause
   must remain.
   Only uncovered rows with an explicit editorial hour estimate enter the existing-unit table;
   suppress the table, subtotal, and scoped-delta prose completely when that estimated set is
   empty, and do not turn the unestimated C8 clause into a zero-hour table row.
   When only the unestimated C8 clause remains, render it as a self-contained sentence without
   the stale tail “so this is not a complete roadmap total,” which referred to the suppressed
   scoped-delta total.
5. Update `tests/test_scope.py` so a covered CNN-training row removes C7 from the rendered pending
   table and removal of `P015-R1-NEURAL-TRAINING` removes its queue entry; retain negative fixtures
   proving either item returns when its canonical owner is pending.
   Add a positive fixture proving the combined correction sentence retains its C8 clause while
   the Round 2 `nlp-word-embeddings` model-training row remains partial, plus a negative fixture
   proving that clause disappears only when that canonical row is covered; also assert the empty
   estimated-extension section is suppressed and C8 does not leak into it.
6. Regenerate the audit and roadmap; assert the Round 1 gap set is exactly the five Plan 018
   classical topics and no completed neural unit remains in a pending extension table.
7. Add `curriculum/course-schedule.yaml` with one allocation record per week and add
   sentinel-delimited generated regions to `docs/course-structure.md`.
   `tools/render_course_structure.py` owns the numeric course-model paragraph including per-week
   hours, semester arithmetic including averages/ranges, weekly table, both captured-output
   blocks in Section 5, summative-milestone/mock-week, and first-instruction/topological-order
   regions, each sentinel-delimited.
   Tests require the rendered milestone to place `r1-001` in Week 35 and require exact equality
   between the full rendered `(unit, first-instruction week)` sequence and the schedule-derived
   sequence for all shipped units, including `C5 → C6 → C11 → C7`; they also require the genuinely
   unrelated human-authored optional-mock, grading, and explanatory prerequisite prose outside
   the sentinels to remain byte-identical.
   The schedule checker must account for each manifested session exactly once by unit/session
   index, reconcile each unit's practice and review allocations exactly, reject unknown/duplicate
   allocations, require all prerequisite units to complete before a dependent unit's first
   session, enforce a 450–500-minute total for every week, and require the manifest-owned mock
   plus debrief to be the final scheduled events.
8. Expand the course to 35 weeks without altering Semester 1: S1 is 7,915 minutes over 16 weeks,
   S2 is 8,950 minutes over 19 weeks, and total scheduled time is 16,865 minutes.
   Reallocate all Semester 2 weeks from canonical data rather than carrying old rows forward;
   explicitly rebalance the old 449-minute Week 23 so every regenerated S2 row meets 450–500.
9. Keep strict completion/start order C5 → C6 → C11 → C7 and keep the mock/debrief at the final
   gate.
10. Change `tools/audit_curriculum.py` to obtain scheduled totals from the validated canonical
    schedule rather than a prose regex, and add `schedule-check` plus renderer `--check` to
    `scripts/ci-local.sh`.
11. Add the exact real-notebook command
    `uv run python -m tools.verify_training_mutations --root .` inside the existing manifest/
    content-check stage of `scripts/ci-local.sh`; fixture tests do not substitute for running the
    five registered mutations against the shipped solution notebooks.
    Add schedule and freshness checks inside their existing owning stages so the authoritative
    gate deliberately remains eight top-level stages and its `1/8`…`8/8` labels stay accurate.
12. Refresh `docs/curriculum-architecture.md`'s stale "current 26-week schedule" capacity claim
    to the validated 35-week calendar and state that its under-500 weekly margin is recovery
    buffer, not silently allocatable extension capacity; future content must replace work or
    extend the calendar explicitly.

### Verification

- `uv run python -m tools.audit_curriculum --check`
- `uv run python -m tools.render_curriculum_roadmap --check`
- `uv run python -m tools.render_course_structure --check`
- `uv run usaaio-tools schedule-check`
- `uv run python -m tools.verify_training_mutations --root .`
- material-inventory check mode
- `uv run pytest tests/test_schedule.py tests/test_scope.py tests/test_audit_curriculum.py -q`
- `uv run usaaio-tools scope-check` with only Round 2 warnings and the five explicit Plan 018
  Round 1 warnings.

## Phase 7 — Named verification phase

This phase is mandatory because the plan ships and changes teaching units.

1. Fresh-execute all 28 changed/new solution notebooks and all changed/new
   lesson/review/overview notebooks in isolated Jupyter kernels.
2. Confirm every solution reproduces its statement contract and final answer check.
3. Run statement hygiene, warning-strict nbformat validation for all changed notebooks, manifest
   validation, blueprint conformance, overlap scan, prerequisite closure, practice coverage,
   scope, schedule, answer-key, tolerance, training mutations, inventory, audit-freshness,
   roadmap-freshness, course-structure freshness, and PDF build.
4. Run focused tests first, then `scripts/ci-local.sh` from a clean commit.
5. Confirm exact final corpus values: 18 units, 139 concepts, 407 practices, 63 lesson sessions,
   99 lesson/review/overview notebooks, 913 unit notebooks, 16,625 manifested minutes, and 16,865
   scheduled minutes.
6. Confirm no ignored runtime dataset, model artifact, raw reference, secret, or stored student
   output is tracked.
7. Record final `scripts/ci-local.sh` wall time and require it to remain within the measured base
   plus 900 seconds, including all 28 solutions, teaching notebooks, and five mutant executions.

## Phase 8 — Four-way content gate, report, and shipping

1. Self-review blind-solves all 28 changed/new statements before solution access.
2. In one parallel dispatch, run fresh read-only reviewers on exact Claude Opus 5,
   GPT-5.6-terra, and exact GLM-5.2.
3. Require each reviewer to blind-solve all 28 statements, inspect lessons as a Calculus AB +
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
- The canonical schedule checker and renderer account for every minute and enforce prerequisite
  completion/start order; no schedule acceptance rests on handwritten prose.
- Optional per-problem manifest minutes are complete and sum-checked for C11; C7 retains its
  honest unit-level 875-minute total while each changed capstone states its 75-minute budget.
- The permanent mutation registry proves the actual training answer checks reject all five named
  corruption classes and fails closed on unresolved or unexpectedly passing mutants.
- All 28 changed/new solutions and all changed teaching notebooks fresh-execute cleanly.
- The four-way content gate passes with no `[OPEN]` finding.
- Final `scripts/ci-local.sh` and PR-aware pre-merge guard pass from the shipping commit.
- The branch is squash-merged through a PR; no direct main commit occurs.

## Plan Review

### Slot 1 — self (2026-08-07)

- **Verdict:** APPROVED.
- `[self] [FIXED]` Phase 1 originally named the whole integration files as if every final artifact
  assertion should pass before notebooks existed.
  The verification contract now distinguishes the passing ownership/model subset from the
  deliberately red Phase 0 end-state tests.
- `[self] [FIXED]` C11-p06 originally used ambiguous “clipped/stable” wording.
  The pinned contract now requires cross-entropy from logits through log-sum-exp, consistent with
  the stable derivation in Session 1.
- `[self]` Recomputed the final calibrated deltas independently: C11 contributes 1,550 minutes;
  C7 contributes 308; 14,767 + 1,858 = 16,625 manifested and
  15,007 + 1,858 = 16,865 scheduled.
  The notebook/count deltas are likewise internally consistent.
- `[self]` The selected C11-plus-C7 design closes the eight knowledge-point rows owned by the
  planned neural unit and the two adjacent existing-unit modalities named by the canonical queue
  without entering Plan 018 or Round 2.
  C7 satisfies the existing double-length standard substantively rather than by label alone.
- `[self]` Delta self-review independently re-summed the calibrated table to 1,040 minutes,
  verified 5,280 + 10,480 + 865 = 16,625, verified 8,950 Semester 2 minutes fit the enforced
  450–500 band over 19 weeks, and traced both Round 2 planned-unit edges to their required C11
  replacement.
- `[self]` The final contract also traces all ten single destinations and
  `shipped_concepts` additions through scope-check's anchor ownership rule, makes both C11/C7
  timing contracts explicit without fabricating C7 per-problem data, manifest-enforces C11's
  calibrated problem-minute sum, and uses only repository-valid `uv run` commands.
- `[self]` Final delta review confirms the Set partition is a disjoint cover of p01–p24, p08's
  two tags have separate executable assertions, verifier fixtures land in Phase 1 while corpus
  register runs wait until their target statements exist in Phases 3/5, and all exact-count/
  minute contracts remain unchanged.
- **Final delta verdict: APPROVE.**
- No open self-review finding remains.

### Slot 3 — GPT-5.6-terra (2026-08-07)

- **Initial verdict:** REJECT.
- `[terra] [FIXED]` The draft promised to retire C7/C6/neural pending prose but omitted the
  hard-coded producer `tools/render_curriculum_roadmap.py` and its exact `tests/test_scope.py`
  expectations.
  Phase 6 now changes both, keys extension/tranche output to canonical uncovered/planned owners,
  and requires negative reappearance fixtures.
- `[terra] [FIXED]` The 35-week schedule was prose with unnamed focused tests, so no durable
  consumer could reject missing/duplicated allocations or bad order.
  Phase 6 now adds canonical `curriculum/course-schedule.yaml`, a model/CLI checker, a renderer,
  exact schedule tests, audit integration, and CI wiring that reconcile every manifested and mock
  minute and enforce prerequisite completion before dependent start.
- `[terra] [FIXED]` Positive execution alone could not prove optimizer/update/freeze/commitment/
  mode contracts were answer-affecting.
  Phase 5 now adds a permanent exactly-once source-mutation runner against the real solution
  notebooks, five named corruptions, expected failure-cell checks, fail-closed fixtures, and CI
  execution.
- **Final verdict:** APPROVE.
- `[terra] [FIXED]` The delta review asked that CI name the real five-mutant command explicitly
  rather than allowing fixture-only tests to stand in for registry execution.
  Phase 6 and `scripts/ci-local.sh` now require
  `uv run python -m tools.verify_training_mutations --root .` verbatim.
- `[terra] [FIXED]` Final calibration added C7-p26 as a fourth training capstone but initially
  left verification at the generic three-problem floor and a stale design summary.
  Phase 0 and Phase 5 now require the exact four-id `cnn-training` set plus each problem's
  preserved original concept contract, and the design consistently names four expansions.
- `[terra] [FIXED]` The final renderer boundary initially byte-preserved the old prerequisite-
  order sentence, which would become false after inserting C11.
  The first-instruction/topological-order statement is now a generated sentinel region tested for
  `C5 → C6 → C11 → C7`; unrelated explanatory prose remains protected.
- `[terra] [FIXED]` Final equality fixtures now pin the exact C11 `concepts_used` list and every
  newly closed modality's primary practice id; prerequisite closure or a same-concept substitute
  cannot satisfy those contracts.
- `[terra] [FIXED]` The renderer test now compares the complete week-bearing first-instruction
  sequence for all shipped units with schedule-derived canonical data, not only a four-unit
  substring.
- `[terra] [FIXED]` Scope tests now prove the Round 2 C8 correction clause remains while its
  canonical row is partial and disappears only when that row becomes covered.
- `[terra] [FIXED]` Phase 5 now scopes both register files and requires negative fixtures for a
  missing C7 exception id, wrong literal value, and mismatched statement body budget.
- **Final delta verdict on `eb28228`: APPROVE.**

### Slot 4 — GLM-5.2 (2026-08-07)

- **Verdict:** APPROVED.
- `[glm] [FIXED]` The draft said Phase 1 would repair a duplicate C6 `prereqs` key, but the current
  merged `syllabus.md` has exactly one such key and the manifest correctly has one distinct
  `prereq_units` field.
  The phantom drive-by edit is removed and C6's contract remains unchanged.
- `[glm]` Independently verified the baseline counts and minutes, all Plan 017 arithmetic, C7
  prerequisite transitivity, the double-length bands, and the existence of referenced current
  producers/consumers; no blocker remains.
- `[glm] [FIXED]` The standards correction now names C11's final 1,040 practice minutes, not
  C10's pre-plan 730, as the post-plan practice maximum.
- `[glm] [FIXED]` The roadmap contract removes only the obsolete C6 clause from the combined C6/C8
  sentence and explicitly preserves the still-uncovered Round 2 C8 clause.
- `[glm] [FIXED]` C11-p24 now grades optimizer control as part of its trained-network ablation,
  giving `torch-optimizers` a fourth honest practice rather than leaving it at the three-practice
  floor.
- **Final delta verdict on `eb28228`: APPROVE.**

### Slot 2 — Claude Opus 5 (2026-08-07)

- **Initial verdict:** CHANGES REQUESTED.
- `[opus] [FIXED]` Removing `P015-R1-NEURAL-TRAINING` would leave dangling prerequisites in the
  two Round 2 planned units and make scope-check fail.
  Phase 6 now atomically retargets both edges to shipped `C11-neural-training` and requires a
  negative dangling-edge test.
- `[opus] [FIXED]` The draft C11 workload was a 1,900-minute corpus outlier and three C7 rewrites
  were 120-minute replacements presented as ordinary rewrites.
  The final contract calibrates C11 to 1,550 minutes with a 75-minute problem maximum, expands
  four C7 problems to 75 minutes with preserved separately scored subparts, records measured
  peer comparisons and the one-unit rationale, and yields a 1,858-minute / 30.97-hour tranche.
- `[opus] [FIXED]` C7's enforcement depended on a syllabus `length: double` field the draft did
  not name.
  Phase 1 now requires that exact canonical field, four sessions, and the existing 27-practice
  range.
- `[opus] [FIXED]` The phantom duplicate-C6 edit is removed, matching GLM's independent finding.
- `[opus] [FIXED]` C7 rewrites could tag C11 concepts without declaring them in `concepts_used`.
  Phase 1 now names the exact six foreign concepts used by the expanded training problems,
  including softmax and cross-entropy for the classifier loss.
- `[opus] [FIXED]` The schedule checker reconciled allocations but did not constrain workload.
  The canonical checker now rejects every week outside the explicit 450–500-minute band.
- `[opus] [FIXED]` The draft used explicit redundant prerequisites for C11 but relied on
  transitivity alone for C7.
  C7 now declares `[C6-pytorch, C11-neural-training]` explicitly.
- `[opus] [FIXED]` `cnn-training` sat exactly at the three-practice floor.
  C7-p26 is now the fourth substantive training problem and retains its existing shape-helper
  objective.
- `[opus] [FIXED]` Phase 1 now updates the standards roster to name all four double-length units.
- `[opus] [FIXED]` The final 6/12/6 difficulty split is honestly described as within the
  standard's rough target; C11-p07 is no longer labeled intro merely to tune percentages.
- `[opus] [FIXED]` The design now records why permanent id C11 sorts after C10 while explicit
  graph/schedule consumers place it between C6 and C7.
- `[opus] [FIXED]` The second review found system-`python3` and malformed positional-root commands
  that could not run in the repository environment.
  Every gate command now uses the authoritative `uv run` environment and correct CLI shape,
  including `uv run python -m tools.verify_training_mutations --root .`.
- `[opus] [FIXED]` Phase 1 now names the coupled suggested-order, engineering-ladder,
  double-length narrative, and `tests/test_integration.py` updates required when C11 enters the
  syllabus.
- `[opus] [FIXED]` The intermediate scope red state is explicit and bounded to the eight planned
  provisional concepts; any other scope error blocks the phase.
- `[opus] [FIXED]` C7 `concepts_used` now also names `softmax` and `cross-entropy-loss`, matching
  its trained classifier and loss-curve lesson.
- `[opus] [FIXED]` Semester 2 now uses 19 weeks rather than packing 8,950 minutes into 18 weeks;
  the 450–500-minute hard band retains durable headroom.
- `[opus] [FIXED]` Optional positive per-problem `minutes` are added to the manifest model for C11,
  whose 24 calibrated rows sum to its practice total.
  C7 retains an honest aggregate total instead of assigning invented equal durations to 23
  unchanged problems; its four changed statements still name 75-minute budgets.
- `[opus] [FIXED]` The ten rows now pin exactly one destination plus the precise
  `shipped_concepts` additions needed for every cross-unit lesson anchor.
- `[opus] [FIXED]` Phase 0 measures the clean `708a851` full-CI baseline and Phase 7 enforces a
  +900-second ceiling across the new notebooks and five mutant executions.
- `[opus] [WONTFIX]` The eight `ci-local.sh` stage labels are not renumbered because schedule,
  renderer, and mutation commands are deliberately inserted inside the existing generated-
  evidence and manifest/content stages rather than introduced as new top-level stages.
- `[opus] [FIXED]` The C7 standards resolution now corrects its stale corpus-maxima claims.
- `[opus] [FIXED]` C11-p04 is explicitly a numeric reduced-fraction normal-form problem with gcd/
  sign constraints.
- `[opus] [FIXED]` Phase 1 couples the unit-standards roster to the syllabus narrative and its
  exact integration assertions.
- `[opus] [FIXED]` The course-structure renderer owns sentinel-delimited numeric/table,
  summative-milestone/mock-week, and full week-bearing prerequisite-order regions; tests pin
  Week 35 and `C5 → C6 → C11 → C7`, while optional-mock, grading, and unrelated explanatory
  prose outside them is byte-preserved.
- `[opus] [FIXED]` C11-p09 and C11-p10 now provide explicit BatchNorm and dropout implementation
  practices, and the plan pins a primary practice for every newly closed modality across all ten
  promoted knowledge points.
- `[opus] [FIXED]` Set assignment now follows the unit standard by moving numeric-normal-form p04
  to Set B and integration/scenario/challenge p14–p24 to Set C.
- `[opus] [FIXED]` The exact C11 `concepts_used` list is pinned, tooling work is assigned to a
  fresh GPT-5.6-sol session, and Phase 1 atomically resolves the stale C7/C5 capacity TODO.
- `[opus] [FIXED]` Roster headings now use the mandatory slot identities rather than incorrectly
  numbering Terra, GLM, and Opus by chronological response order.
- `[opus] [FIXED]` Phase 1 now explicitly scopes its integration-test edits, and the roadmap
  renderer suppresses an empty estimated-extension section without inventing a C8 estimate.
- `[opus] [FIXED]` The exact C11 dependency list now includes `python-inheritance` for
  `nn.Module` subclasses and `matplotlib-basics` for loss-curve diagnosis.
- `[opus] [FIXED]` The C7 standards edit preserves Plan 014's rejected label-only history and
  records why a substantive fourth session plus the 27-practice band now changes the result.
- `[opus] [FIXED]` The C7 875-minute aggregate now exposes its combined calibration arithmetic;
  the renderer owns every schedule-derived numeric sentence/output block; the stale architecture
  capacity sentence is in scope; and inventory regeneration precedes anchor authoring.
- `[opus] [FIXED]` The schedule plan now rebuilds all of Semester 2 and explicitly eliminates the
  old 449-minute row; every owned C11 concept has a named Set A fundamentals encounter.
- `[opus] [FIXED]` The exact C11 vocabulary now includes `overfitting` and `l2-regularization`, and
  the permanent register enforces A–E MC options plus body-level time budgets without changing the
  three-field metadata header.
- `[opus] [FIXED]` The retained unestimated C8 sentence is self-contained when its estimated table
  and scoped-delta prose are suppressed.
- `[opus] [FIXED]` The estimate reconciliation now calls the 30–44-hour artifact the planned
  neural unit, not eight planned-unit rows.
- `[opus] [FIXED]` C11's register and its fail-closed fixtures land in Phase 1; the literal C7
  budget exception lands with the rewritten statements in Phase 5 and documents its asymmetric
  source of truth.
- `[opus] [FIXED]` C11-p08 now provides a 35-minute Set A task with separate assertions for the
  autograd gradient and optimizer update; p03 returns to a single manual-backpropagation concept.
- **Delta re-review verdict:** APPROVE.

## Content Review

Content-review findings are recorded here during Phase 8.

## Post-Execution Report

Completed during Phase 8 before shipping.
