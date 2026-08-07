# Plan 018 — Round 1 Classical Model Breadth

## Goal

Implement `docs/designs/018-r1-classical-models.md` as the final Round 1 content tranche.
Ship one prerequisite-closed double-length `C12-classical-models` unit covering logistic
regression, linear/kernel SVMs, decision trees, ensembles, and k-means; close all five remaining
Round 1 knowledge-point rows; extend the canonical course schedule to Week 40; and leave no
checker-derived Round 1 gap.

## Branch and baseline

- Branch: `feature/plan-018-r1-classical-models`.
- Base: `c92773ed1f72da21d11d6319d1e6d2d78f491d76`, the squash merge of Plan 017 / PR #18.
- Baseline corpus: 18 units, 139 concepts, 407 practices, 63 lesson sessions, 99
  lesson/review/overview notebooks, 913 unit notebooks, 16,625 manifested minutes, and 16,865
  scheduled minutes over 35 weeks.
- Baseline verification: the byte-identical pre-squash tree passed `scripts/ci-local.sh` in
  2,172.52 seconds; the isolated Plan 018 worktree then passed 452 tests after read-only reference
  symlinks restored overlap-scan input.
- Baseline Round 1 gaps: exactly logistic regression, support-vector machines, decision trees,
  ensemble learning, and k-means clustering.

## Scope

### New C12 unit

Create `units/C12-classical-models/` with:

- `lesson.ipynb` as the overview/index;
- six 90-minute session notebooks;
- exactly 30 student statement notebooks;
- exactly 30 separate solution notebooks;
- `review.ipynb` with a 10–15-item self-quiz spanning all owned concepts;
- `manifest.yaml` with exact minutes, set/type/difficulty tags, `concept_sessions`, prerequisites,
  per-problem `after_session`, provenance, and statement/solution paths.

C12 is a Round 1 core, double-length unit with explicit prerequisites:

1. `C1-ml-fundamentals`;
2. `C2-linear-models`;
3. `C3-gradient-descent`;
4. `C4-classical-ml-practice`;
5. `F7-kernels-convex-optimization`.

It owns exactly these ten concepts:

1. `logistic-regression`;
2. `svm`;
3. `margin-and-hinge-loss`;
4. `decision-trees`;
5. `tree-split-criteria`;
6. `ensemble-learning`;
7. `bagging-and-boosting`;
8. `k-means`;
9. `lloyd-algorithm`;
10. `classical-model-comparison`.

### Six-session spine

| Session | File | Required teaching surface |
|---:|---|---|
| 1 | `01-logistic-regression.ipynb` | log-odds, sigmoid, stable BCE, mean gradient, deterministic NumPy training, sklearn comparison, separation/calibration |
| 2 | `02-linear-svm-margin-and-hinge.ipynb` | functional/geometric margin, hard/soft constraints, hinge loss, `C`, support vectors, vectorized subgradient training |
| 3 | `03-kernel-svm-and-dual-intuition.ipynb` | F7 dual/KKT handoff, support-vector decision function, linear/polynomial/RBF kernels, scaling, `C`/`gamma`, fitted `SVC` |
| 4 | `04-decision-trees.ipynb` | Gini/entropy, weighted impurity, information gain, tie-breaking, recursion, stopping/pruning, from-scratch depth-limited tree |
| 5 | `05-ensembles.ipynb` | voting, bootstrap aggregation, random forests, feature subsampling, AdaBoost update, bias/variance, fitted ensembles |
| 6 | `06-kmeans-and-model-comparison.ipynb` | WCSS objective, Lloyd assignment/update, descent/local optimum, initialization/empty clusters, NumPy and sklearn fits, comparison matrix |

Each session contains 6–10 substantive sections, at least two checkpoints per section, collected
checkpoint answers, and the unit-wide required worked examples, pitfalls, exam connections, and
going-deeper material.

The exact `concept_sessions` mapping is:

- Session 1: `logistic-regression`;
- Session 2: `svm`, `margin-and-hinge-loss`;
- Session 4: `decision-trees`, `tree-split-criteria`;
- Session 5: `ensemble-learning`, `bagging-and-boosting`;
- Session 6: `k-means`, `lloyd-algorithm`, `classical-model-comparison`.

Session 3 deepens the already introduced `svm` concept into the kernel case; its later practice
floor is represented by per-problem `after_session`, not by inventing a duplicate owned concept.

### Exact practice ledger

Every statement declares exactly one `**Time budget:**` matching its manifest `minutes` value.
Every coding or training problem pins identifiers, shapes, dtypes, permitted/banned APIs, fixed
probes, explicit tolerances, and answer-affecting concept tags.

| Id | Set | Type | Difficulty | Minutes | Primary scored contract |
|---|---|---|---|---:|---|
| C12-p01 | A | mc | intro | 20 | sigmoid/log-odds and the logistic decision rule |
| C12-p02 | A | mc | intro | 20 | signed margin, hinge activity, and support vectors |
| C12-p03 | A | mc | intro | 20 | weighted child impurity and split direction |
| C12-p04 | A | mc | intro | 20 | bagging versus boosting construction |
| C12-p05 | A | mc-normal-form | intro | 20 | one Lloyd assignment/update and reduced WCSS value |
| C12-p06 | A | constrained-coding | intro | 55 | stable sigmoid and mean binary-cross-entropy function |
| C12-p07 | B | constrained-coding | core | 55 | NumPy logistic gradient descent with loss and movement certificates |
| C12-p08 | B | constrained-coding | core | 55 | vectorized hinge objective and valid linear-SVM subgradient step |
| C12-p09 | B | constrained-coding | advanced | 55 | scaled kernel `SVC` fit with support-vector and prediction audit |
| C12-p10 | A | constrained-coding | intro | 55 | deterministic best-split search with fixed tie-breaking |
| C12-p11 | B | constrained-coding | core | 55 | depth-limited from-scratch classification tree fit/predict |
| C12-p12 | B | constrained-coding | core | 55 | seeded bagging or boosting fit with ensemble-state audit |
| C12-p13 | A | constrained-coding | intro | 55 | deterministic Lloyd implementation with objective trace |
| C12-p14 | B | proof | core | 45 | derive stable logistic mean gradient from BCE |
| C12-p15 | C | proof | advanced | 45 | margin/hinge/soft-primal and dual-support chain |
| C12-p16 | B | proof | core | 45 | prove weighted impurity reduction for a pinned split |
| C12-p17 | B | proof | core | 45 | prove each Lloyd step cannot increase WCSS |
| C12-p18 | C | integrative | advanced | 65 | train and compare logistic versus linear SVM under scaling |
| C12-p19 | C | integrative | advanced | 65 | grow a tree, bag it, and diagnose variance reduction |
| C12-p20 | C | integrative | core | 65 | k-means initialization/objective/stability arc |
| C12-p21 | C | integrative | advanced | 65 | leakage-safe benchmark across all five families |
| C12-p22 | C | scenario | intro | 45 | choose scaling, probability, or margin workflow |
| C12-p23 | C | scenario | core | 45 | diagnose tree overfit and select a pruning/control response |
| C12-p24 | C | scenario | core | 45 | choose voting, bagging, random forest, or boosting |
| C12-p25 | C | scenario | core | 45 | diagnose clustering validity, inertia, and initialization |
| C12-p26 | C | challenge | core | 50 | logistic perfect-separation and calibration audit |
| C12-p27 | C | challenge | advanced | 50 | kernel support-vector decision reconstruction |
| C12-p28 | C | challenge | core | 50 | construct and certify a tiny decision tree end to end |
| C12-p29 | C | challenge | core | 50 | exact two-round AdaBoost weight/coefficient ledger |
| C12-p30 | C | challenge | advanced | 50 | robust k-means empty-cluster/init comparison |

The exact distribution is five MC, eight constrained coding, four proof/derivations, four
integrative, four scenario, and five challenge problems; 9 intro, 14 core, and 7 advanced.
The exact practice-minute sum is 1,410.

### Concept coverage ledger

The manifest must give each owned concept at least these direct problem paths:

- `logistic-regression`: p01, p06, p07, p14, p18, p21, p22, p26;
- `svm`: p02, p08, p09, p15, p18, p21, p22, p27;
- `margin-and-hinge-loss`: p02, p08, p15, p18, p27;
- `decision-trees`: p03, p10, p11, p16, p19, p21, p23, p28;
- `tree-split-criteria`: p03, p10, p16, p23, p28;
- `ensemble-learning`: p04, p12, p19, p21, p24, p29;
- `bagging-and-boosting`: p04, p12, p19, p24, p29;
- `k-means`: p05, p13, p17, p20, p21, p25, p30;
- `lloyd-algorithm`: p05, p13, p17, p20, p30;
- `classical-model-comparison`: p18, p21, p22, p24, p25, p26.

Additional prerequisite tags are allowed only when they change a scored deliverable.
No practice may rely on an owned concept before the session named by `concept_sessions`.

The exact per-problem instruction floor is:

- after Session 1: p01, p06, p07, p14, p26;
- after Session 2: p02, p08, p18, p22;
- after Session 3: p09, p15, p27;
- after Session 4: p03, p10, p11, p16, p23, p28;
- after Session 5: p04, p12, p19, p24, p29;
- after Session 6: p05, p13, p17, p20, p21, p25, p30.

Each practice row records that floor as `after_session`.
It must be no earlier than the maximum `concept_sessions` value implied by the problem's owned
concept tags; the explicit value governs later-taught subtopics such as kernel SVMs.

For coverage-map evidence, use these direct modality ledgers (additional honest reuse is allowed):

| Official row | Theory | Implementation | Model training |
|---|---|---|---|
| logistic regression | p01, p14, p26 | p06, p07, p18 | p07, p18, p21 |
| support-vector machine | p02, p15, p27 | p08, p09, p27 | p09, p18, p21 |
| decision trees | p03, p16, p23 | p10, p11, p28 | p11, p19, p21 |
| ensemble learning | p04, p24, p29 | p12, p19, p29 | p12, p19, p21 |
| k-means clustering | p05, p17, p25 | p13, p20, p30 | p13, p20, p21 |

### Minutes and corpus deltas

C12 manifests:

- lesson = 540, `lesson_sessions = [90, 90, 90, 90, 90, 90]`;
- practice = 1,410, with every problem carrying its exact row value;
- review = 60;
- total = 2,010 minutes = 33.5 hours.

The final exact corpus is:

- 19 units;
- 149 concepts;
- 437 unit practices;
- 69 lesson sessions;
- 107 lesson/review/overview notebooks;
- 981 unit notebooks;
- 18,635 manifested minutes;
- 18,875 scheduled minutes, including the unchanged 180-minute mock and 60-minute debrief.

### Canonical evidence and schedule

Promote all five rows in `curriculum/coverage-map.yaml` to `covered` with destination
`C12-classical-models`, exact lesson anchors, direct practice evidence for theory,
implementation, and model training, empty deficits, and disposition `keep`.
Remove `P015-R1-CLASSICAL-BREADTH` only after the rows are covered.
Retarget the Round 2 capstone prerequisite from that placeholder to `C12-classical-models`.

Extend `curriculum/course-schedule.yaml` to 40 weeks:

- Semester 1 remains 16 weeks / 7,915 minutes;
- Semester 2 becomes 24 weeks / 10,960 minutes;
- C12 sessions 1–6 occur in Weeks 34–39;
- the existing mock and debrief move together to final Week 40;
- C12's last practice and 60-minute review precede the mock in Week 40;
- at least 155 minutes of existing practice move from Weeks 17–33 into Weeks 34–40, with no
  unit-minute change.

Week 34 begins at 500 minutes and must displace at least 90 minutes when C12 Session 1 is added.
Week 35 becomes 335 minutes after the mock/debrief move and Session 2 is added, so it must receive
at least 115 minutes of already unlocked practice.

Every week remains 450–500 minutes.
Weeks 1–39 contain one to three lesson sessions; Week 40 is the sole final-assessment exception.
The unique final assessment week is derived from the schedule rather than hard-coded as Week 35.

### Permanent verification

1. Generalize manifest-backed time-budget checking from the C11 unit id to every practice row
   carrying `minutes`; retain the separate closed-world C7 exception.
2. Add optional `concept_sessions` to the unit-manifest model.
   When present, keys must equal `concepts_taught`, values must be positive integers within the
   lesson-session count, every practice must tag at least one owned concept, and every practice
   must carry a valid `after_session` no earlier than its concept-derived floor.
3. Generalize schedule practice-order validation for manifests carrying `concept_sessions`,
   `after_session`, and complete per-problem minutes. Their schedule practice allocations must
   list exact `problem_ids`; the lists partition the manifest exactly once, allocation minutes
   equal the listed minute sums, and each problem follows its required session.
4. Derive the unique final-assessment week and reject absent, duplicate, non-final, or improperly
   ordered mock/debrief allocations.
5. Add `tools/verify_classical_mutations.py` with exactly five fail-closed real-answer-check
   mutations: p07 logistic mean factor, p08 signed hinge branch, p10 maximum-impurity split, p29
   missing AdaBoost weight update, and p13 non-centroid Lloyd update.
6. Wire the mutation runner into `scripts/ci-local.sh` without weakening the existing training
   mutation runner.

## Out of scope

- No Round 2 attention, transformer, NLP, advanced-vision, generative, or GPU content.
- No second mock and no rewrite of `r1-001`; only its scheduled week moves.
- No general QP solver, full CART regression, XGBoost/LightGBM internals, hierarchical/DBSCAN
  clustering, mixture models, statistical-inference unit, student's t-test, or importance
  sampling.
- No edits to `AGENTS.md`, `docs/development-workflow.md`,
  `docs/content-review-gate.md`, or `docs/architecture/decisions.md`.
- No raw reference paper, ignored artifact, secret, or student data may be read into authored
  content or committed.
- The plan does not weaken unit standards, coverage floors, schedule bands, prerequisite closure,
  fresh execution, or review gates.

## Execution ownership

- Planning, orchestration, evidence integration, schedule assembly, and review recording: inline.
- Lesson content and all 30 statements: GPT-5.6-sol content session.
- All 30 solutions: a separate fresh GPT-5.6-sol session that sees final statements but never the
  statement-author outline or draft answers.
- Tooling and tests: GPT-5.6-sol implementation session.
- Trivial generated-file updates and final report edits: inline.
- Plan and content gates: self, exact Claude Opus 5, GPT-5.6-terra, and exact GLM-5.2, matching
  the user-selected roster used for Plan 017.

## Phase 0 — Pin the failing contract

### Files

- `tests/test_model.py`
- `tests/test_schedule.py`
- `tests/test_scope.py`
- `tests/test_audit_curriculum.py`
- `tests/test_integration.py`
- `tests/test_verify_register.py`
- `tests/test_classical_mutations.py`

### Work

Write fail-first tests against the Plan 017 baseline that require:

1. exact final corpus counts and deltas listed above;
2. a `C12-classical-models` manifest with five exact prerequisites, ten exact owned concepts, six
   90-minute sessions, 30 exact practice rows, 1,410 practice minutes, and 60 review minutes;
3. the exact p01–p30 set/type/difficulty/minute/`after_session` ledger and concept-coverage ledger;
4. optional `concept_sessions` parsing, required `after_session` behavior, and all malformed or
   closure-invalid negative cases;
5. general manifest-minute versus statement-budget validation outside C11;
6. five coverage rows promoted to shipped C12 evidence and no remaining Round 1 warning;
7. removal of `P015-R1-CLASSICAL-BREADTH` and retargeting of the R2 capstone prerequisite;
8. 40 exact schedule weeks, C12 sessions in Weeks 34–39, mock/debrief in Week 40, totals
   7,915/10,960/18,875, every week 450–500, regular weeks with one to three lessons, prerequisite
   completion, review finality, and mock/debrief terminal ordering;
9. exact schedule `problem_ids` partitioning, minute reconciliation, and rejection when an
   individually named problem precedes its `after_session` even if aggregate minutes fit;
10. exactly five registered classical mutations, each resolving one file/cell/source replacement
    and failing closed on zero/multiple match or unexpected success.

The tests must fail for the missing unit/schema/evidence/schedule/mutation implementation, not for
an unrelated fixture or absent ignored corpus.

### Verification

- Run every new test by exact node id and capture the expected failure reason.
- Run `git diff --check`.
- Commit the red contract before content implementation.

## Phase 1 — Establish C12 ownership, schema, and schedule shape

### Files

- `syllabus.md`
- `units/C12-classical-models/manifest.yaml`
- `curriculum/coverage-map.yaml`
- `curriculum/course-schedule.yaml`
- `tools/model.py`
- `tools/checks/schedule.py`
- `scripts/verify-register.py`
- Phase 0 tests

### Work

1. Add the ten C12 concept definitions, prerequisite edges, Round 1 layer, and new unit mapping to
   the canonical syllabus without renaming shipped concepts.
2. Create the full 30-row manifest before notebooks exist, including exact metadata, minutes,
   paths, `concept_sessions`, `after_session`, and concept tags.
3. Implement strict optional `concept_sessions` parsing and general manifest-backed statement
   budget validation.
4. Extend the schedule to 40 weeks and rebalance allocations without changing any pre-existing
   unit total.
5. Replace the hard-coded final mock week with a derived unique final-assessment contract.
6. Add exact `problem_ids` to every C12 schedule practice chunk and implement generic exact-once,
   minute-sum, and per-problem instruction-order validation.
7. Stage the five canonical coverage rows and placeholder transition, but do not claim coverage
   until lesson/practice evidence exists.

### Verification

- Phase 0 model, manifest, schedule, and budget tests pass.
- `uv run usaaio-tools schedule-check` passes.
- A deliberate reversed session, post-review practice, early kernel-SVM problem hidden in an
  otherwise legal chunk, missing/duplicate problem id, wrong chunk minute sum, duplicate mock,
  and non-final mock mutation each fails for the intended reason.
- Exact arithmetic independently recomputes every unit, week, semester, and course total.

## Phase 2 — Build the six-session teaching spine

### Files

- `units/C12-classical-models/lesson.ipynb`
- `units/C12-classical-models/lessons/01-logistic-regression.ipynb`
- `units/C12-classical-models/lessons/02-linear-svm-margin-and-hinge.ipynb`
- `units/C12-classical-models/lessons/03-kernel-svm-and-dual-intuition.ipynb`
- `units/C12-classical-models/lessons/04-decision-trees.ipynb`
- `units/C12-classical-models/lessons/05-ensembles.ipynb`
- `units/C12-classical-models/lessons/06-kmeans-and-model-comparison.ipynb`
- `units/C12-classical-models/review.ipynb`

### Work

Author the exact design spine from the declared Calculus AB + basic Python baseline plus the five
manifest prerequisites.
Every symbol, API, split criterion, objective, seed, tie rule, and evaluation claim used later in
practice must first appear in executable teaching material.

The review notebook contains a concept summary, formula/API sheet, 10–15-item quiz spanning all
ten owned concepts, collected answers, and targeted practice-redo guidance.

### Verification

- Fresh-execute all eight notebooks in isolated Jupyter kernels.
- Assert exact session titles/order, required checkpoints, collected answers, unit-wide standards
  sections, fixed seeds, and absence of network/GPU/TensorFlow usage.
- Run prereq, hygiene, tolerance, and material-inventory checks.

## Phase 3 — Author the 30 student statements

### Files

- `units/C12-classical-models/practice/p01.ipynb` through `p30.ipynb`
- statement-focused integration/register tests

### Work

The statement author implements the exact ledger in this plan without writing solution outlines or
draft answer keys.
All content is original and derived-reference-only.

Each statement:

- is unexecuted and contains no solution or answer leakage;
- uses only taught/prerequisite concepts;
- declares its exact time budget and reasoning/coding contract;
- pins deterministic inputs and independent expected-output requirements;
- gives exactly A–E for MC and all gcd/sign rules for normal form;
- ends with student-facing placeholders only, never a solved output.

### Verification

- `python3 scripts/verify-register.py --statements-only` passes 437/437.
- Exact ledger and concept-floor tests pass.
- `uv run usaaio-tools hygiene-check`, `prereq-check`, `coverage-check`, `tolerance-check`, and
  `overlap-scan` pass.
- Student notebooks have no stored outputs.

## Phase 4 — Blind-solve C12 in a separate fresh session

### Files

- `units/C12-classical-models/practice/p01_solution.ipynb` through `p30_solution.ipynb`
- `tests/test_c12_solution_regressions.py`

### Work

Give the solution author only final statements, manifests, taught materials, and repository
solution conventions.
Do not provide statement-author notes, intermediate reasoning, expected answers, or mutation
replacement strings.

Every solution:

- runs top to bottom from a clean kernel;
- preserves the statement's exact probes and identifiers;
- derives its own reference rather than importing an answer artifact;
- uses explicit tolerances and deterministic seeds;
- ends with `### Answer check` containing executable assertions that reject self-consistent wrong
  implementations.

### Verification

- Fresh-execute all 30 solutions.
- `python3 scripts/verify-register.py` passes 437/437.
- Regression tests pin statement-probe equality, exact answer-check placement, no stored student
  outputs, and representative independent constants for each family.

## Phase 5 — Promote evidence and add permanent mutations

### Files

- `curriculum/coverage-map.yaml`
- `tools/verify_classical_mutations.py`
- `tests/test_classical_mutations.py`
- `scripts/ci-local.sh`
- `curriculum/material-inventory.yaml`
- `docs/audits/015-coverage-audit.md`
- `docs/curriculum-roadmap.md`
- `docs/course-structure.md`
- `TODO.md`

### Work

1. Bind exact lesson anchors and the declared modality ledger to each official row, proving at
   least one honest practice per required modality and at least three distinct practices overall.
2. Remove the Round 1 placeholder and retarget downstream planned prerequisites only after the
   coverage checker reports all five rows covered.
3. Implement the five exactly-once classical mutations against actual final answer-check cells.
4. Add the mutation runner to local CI alongside, not instead of, the neural training runner.
5. Regenerate material inventory, audit, roadmap, and course structure through official commands.
6. Require the audit/roadmap Round 1 gap set to be empty and planned-unit queue to begin with the
   Round 2 transformer/NLP tranche.
7. Leave Plan 018 unticked in `TODO.md` until the content gate and final CI pass.

### Verification

- `uv run python -m tools.verify_classical_mutations --root .` kills 5/5.
- Deleting, duplicating, or making any mutation ineffectual fails closed.
- Coverage, scope, audit, roadmap, schedule, and renderer freshness tests pass.
- Scope-check emits only Round 2 warnings.

## Phase 6 — Named verification phase

Run, inspect, and record:

1. fresh Jupyter execution of all 30 C12 solutions and all eight C12 teaching/review/overview
   notebooks;
2. `python3 scripts/verify-register.py` and `--statements-only`, both 437/437;
3. `uv run python -m tools.verify_training_mutations --root .`, 5/5;
4. `uv run python -m tools.verify_classical_mutations --root .`, 5/5;
5. focused Phase 0–5 tests plus full `uv run pytest -q`;
6. `uv run usaaio-tools schedule-check`, `prereq-check`, `coverage-check`, `scope-check`,
   `tolerance-check`, `hygiene-check`, `blueprint-check`, `overlap-scan`, and `answerkey-check`;
7. `uv run python -m tools.audit_curriculum --check`,
   `tools.render_curriculum_roadmap --check`, and `tools.render_course_structure --check`;
8. exact corpus, schedule, tracked-artifact, no-output, and no-secret assertions;
9. final clean-commit `bash scripts/ci-local.sh`, timed against the 2,172.52-second Plan 017
   baseline with a maximum allowed increase of 900 seconds.

Any fresh-kernel, mutation, coverage, schedule, PDF, or CI failure blocks the phase.

## Phase 7 — Four-way content gate, report, and shipping

1. Self-review blind-solves all 30 statements before solution access.
2. In one parallel dispatch, run fresh read-only exact reviewers on Claude Opus 5,
   GPT-5.6-terra, and exact GLM-5.2.
3. Require every reviewer to solve all 30 statements blind, inspect all six lessons as a Calculus
   AB + declared-prerequisite student, review tooling changes, and report exact findings.
4. Record every finding in `## Content Review`, resolve every `[OPEN]`, rerun affected notebooks
   and checks, and obtain exact-delta four-way consensus.
5. Complete `## Post-Execution Report` with artifacts, deviations, reviewer divergence, fresh
   execution, final timing, limitations, and the empty Round 1 gap boundary.
6. Mark Plan 018 complete in `TODO.md`, commit, run final clean-tip `scripts/ci-local.sh`, push,
   open a PR, run `scripts/pre-merge-guard.sh --pr`, and squash-merge.
7. Stop after merge and perform the user-requested Round 1 coverage review; do not begin Round 2
   content automatically.

## Acceptance criteria

- The four-way plan gate approves this plan before Phase 0 implementation begins.
- C12 satisfies the six-session/30-practice double-length standard without weakening it.
- Every one of the five official rows is checker-derived covered in theory, implementation, and
  model training, with at least three direct practices.
- The Round 1 missing/partial gap set is empty.
- The canonical placeholder is removed and downstream planned prerequisites resolve to shipped
  `C12-classical-models`.
- All 30 solutions and eight teaching notebooks fresh-execute cleanly.
- Both 5/5 mutation registries pass against real answer checks.
- The 40-week schedule reconciles 7,915/10,960/18,875 minutes, preserves weekly/session/prereq/
  review/practice-capacity invariants, and places mock/debrief last in Week 40.
- Final corpus values are exactly 19 units, 149 concepts, 437 practices, 69 lesson sessions, 107
  teaching/review/overview notebooks, 981 unit notebooks, and 18,635 manifested minutes.
- The four-way content gate has no `[OPEN]` finding.
- Final `scripts/ci-local.sh` and PR-aware pre-merge guard pass from the shipping commit.
- The branch squash-merges through a PR; no direct main commit occurs.

## Plan Review

### Round 1 — commit `5ce8e74`

- [self] [BLOCKER] The design reused C11 cross-entropy without declaring C11; derive binary
  cross-entropy wholly inside Session 1 instead.
- [self] [CONCERN] The claimed 240-minute schedule certificate mixed new-week and whole-unit
  totals; recompute the exact Week 34–40 pool.
- [terra] [BLOCKER] Aggregate unlocked minutes cannot prove that a particular kernel-SVM, tree,
  ensemble, or k-means problem follows its lesson; bind scheduled chunks to exact problems and
  enforce per-problem floors.
- [terra] [BLOCKER] The C11 dependency claim violates prerequisite honesty; remove it or add C11.
- [glm] [BLOCKER] The same undeclared C11 dependency would fail `prereq-check` if honestly tagged.
- [glm] [CONCERN] `concept_sessions` alone cannot distinguish Session-2 linear SVM from Session-3
  kernel SVM practice.
- [glm] [CONCERN] The schedule feasibility arithmetic and Week-34/35 displacement were incomplete.
- [glm] [NIT] The generic pacing wording implied C11's handwritten test would disappear.
- [glm] [NIT] `mc-normal-form` needed validator treatment. No change: it is already a registered,
  widely shipped type in `scripts/verify-register.py` and 18 existing manifests.
- [glm] [NIT] Monitor the 900-second CI-growth ceiling for ML-heavy notebooks. Retained as a hard
  performance regression limit; Phase 6 records actual timing.

Initial verdicts: self **REJECT**; Terra **REJECT**; GLM **REJECT**. The initial Opus run was
superseded before verdict so that the corrected commit, rather than a changing worktree, receives
the required exact-model review.

### Resolution

- Session 1 now derives BCE directly and expressly excludes undeclared C11 concepts.
- Every practice has an exact `after_session`; schedule practice allocations list exact
  `problem_ids`, partition the manifest once, reconcile minutes, and enforce order.
- The SVM split is explicit: `svm` begins in Session 2, while p09/p15/p27 require Session 3.
- The schedule certificate now proves that Weeks 34–40 need 3,150 minutes, takes 985 baseline plus
  2,010 new plus 155 shifted, and states the Week-34 displacement and Week-35 backfill bounds.
- Evidence modalities and all five mutation targets are now exact ledgers.

### Round 2 — corrected commit

Final exact-model verdicts are recorded here before Phase 0 begins.

## Content Review

Content-review findings are recorded here during Phase 7.

## Post-Execution Report

Completed during Phase 7 before shipping.
