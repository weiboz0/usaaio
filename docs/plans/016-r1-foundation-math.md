# Plan 016 — Round 1 Foundation, Workflow, and Mathematical Completion

> **Required execution skill:** Use `superpowers:subagent-driven-development` to execute
> this plan phase by phase, with a fresh statement-author session and a separate blind
> solution-author session for every content batch.

**Goal:** Close the first Plan 015 Round 1 tranche by shipping honest instruction and
practice for scientific plotting/workflow, conditional probability and concentration,
closed-form regression, PCA derivation/implementation, kernels, and convex optimization.
The result must reduce the corresponding Plan 015 Round 1 gaps to checker-derived
`covered`, extend the single shared course schedule, and preserve the Round 1 exit without
creating duplicate Round 1/Round 2 materials.

**Architecture:** Deepen F1, C10, F5, C2, and C9 where the missing concept belongs, and add
one coherent new `F7-kernels-convex-optimization` unit for the kernel/convexity arc.
F5 becomes an explicitly double-length unit; the checker will enforce that label's
session/problem bands.  Every new concept is committed atomically across the canonical
syllabus, owner manifest, lesson/review, at least three honest practices, coverage evidence,
inventory, roadmap, and schedule.

**Tech stack:** Python 3.12, NumPy, matplotlib, seaborn, PyYAML, nbformat, Jupyter, pytest,
Ruff, the `usaaio-tools` CLI, deterministic curriculum renderers, and GitHub Actions/local
CI.  All commands use
`PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache
UV_PROJECT_ENVIRONMENT=/home/chris/workshop/usaaio/.venv` in the isolated worktree.

## Authority and pinned design

This plan implements `docs/designs/016-r1-foundation-math.md` and the first ordered tranche
in `docs/plans/015-layered-curriculum.md`.
The official topic taxonomy and coverage-map modalities remain authoritative; this plan may
add evidence but may not weaken a required modality or merge distinct topics into a vague
tag.
The implementation starts from `main` at `0f5d3bb`, where Plans 014 and 015 are both merged.

## Scope

### Shipped concept owners

| Owner | New concepts | Final sessions / practices | Manifest minutes |
|---|---|---:|---:|
| F1 | `seaborn-programming` | 4 / 24 | 310 lesson + 515 practice + 50 review = 875 |
| C10 | `colab-markdown-solution-authoring`, `markdown-code-snippets`, `markdown-math-formulae`, `colab-coding-submission`, `cpu-and-gpu-round-boundary` | 4 / 24 | 335 + 610 + 55 = 1,000 |
| F5 | `conditional-probability`, `bayes-rule`, `hoeffding-inequality` | 5 / 25 | 415 + 650 + 55 = 1,120 |
| C2 | `linear-regression-estimator-derivation`, `ols-rank-identifiability-and-pseudoinverse` | 3 / 24 | 260 + 590 + 55 = 905 |
| C9 | `pca-centered-covariance-eigenproblem-derivation`, `numpy-pca-class-from-scratch`, `pca-black-box-insufficiency` | 4 / 24 | 340 + 600 + 60 = 1,000 |
| F7 | `positive-semidefinite-matrices`, `kernel-validity`, `convex-sets`, `convex-functions`, `first-order-optimality`, `lagrangians`, `optimization-duality` | 4 / 20 | 340 + 640 + 45 = 1,025 |

The pinned net addition is 2,300 manifested minutes: F1 +175, C10 +170, F5 +400,
C2 +275, C9 +255, and F7 +1,025.
The expected repository totals are 14,647 manifested minutes and 14,887 scheduled minutes,
laid out as a prerequisite-valid 31-week course near eight hours per week.

### Out of scope

- Plan 017 neural-network training, softmax/cross-entropy, BatchNorm, and dropout content.
- Plan 018 logistic regression, SVM, trees, ensembles, and k-means content.
- Any Round 2 extension or GPU-training capstone; C10 teaches only the official round
  boundary and submission implications.
- New mock tests, raw past-paper text, student data, and optional Student's t-test or
  importance-sampling material.
- Resolving C5/C7 capacity, decorative-tag checking, session-order checking, intra-repo
  overlap tooling, stale-output cleanup outside changed notebooks, or broad CI lint policy.

## Non-negotiable content contracts

1. Student notebooks contain no solutions and no executed outputs.  Each changed or new
   solution is blind-authored from the final student notebook in a fresh session, uses a
   fixed seed where randomness exists, declares explicit `atol` and `rtol`, stores no
   outputs, and ends with `### Answer check`.
2. A concept tag is present only when that concept changes a separately scored deliverable.
   Each new concept has at least three distinct practice ids and paths.
3. Kernel validity uses the finite-Gram PSD quantifier, distinguishes mathematical proof
   from sampled numerical evidence, and does not require strict positive definiteness for
   repeated inputs.
4. Strong duality and KKT claims state their convex/affine and regularity assumptions.
   Convexity proofs use Jensen/line restrictions and first-order conditions, not untaught
   Hessian machinery.
5. Regression distinguishes full-column-rank uniqueness from existence, forbids blind
   `inv(X.T @ X)`, and treats the pseudoinverse solution as minimum norm in the deficient
   case.
6. PCA centers data, states the covariance denominator consistently, compares repeated
   eigenspaces by projectors/subspaces rather than eigenvector signs or order, and exposes a
   reusable `NumpyPCA` fit-state contract without sklearn/scipy PCA.
7. Hoeffding exercises state boundedness, independence, interval width, one- versus
   two-sided constants, and when a bound above one is merely vacuous.

## Phase 0 — Baseline, collision, and fail-first contracts

### Files

- Modify `tests/test_prereq_coverage.py`.
- Modify `tools/checks/coverage.py`.
- Modify `TODO.md` only to register Plan 016 as active.

### Steps

1. Confirm the branch is `feature/plan-016-r1-foundation-math`, both local reference index
   symlinks resolve, `scripts/pre-merge-guard.sh` passes, and the baseline full CI is green.
   Record exact commands and counts in the post-execution report.
2. Add fail-first fixtures proving a syllabus unit with `length: double` fails below four or
   above six lesson sessions and below 24 or above 30 practices; a compliant 4–6/24–30
   fixture passes.  A normal unit remains governed by existing policy and this change does
   not retroactively legalize C7.
3. Run the focused tests and capture the expected red output before changing the checker:

   ```bash
   uv run pytest tests/test_prereq_coverage.py -q
   ```

4. Implement the smallest checker change by joining loaded syllabus unit metadata to the
   corresponding manifest.  Count `estimated_minutes.lesson_sessions` and distinct practice
   ids/paths; issue actionable errors naming the unit, observed count, and required band.
5. Rerun the focused test green, then run `ruff check tools/checks/coverage.py
   tests/test_prereq_coverage.py`.

### Acceptance

- Red-before-green evidence is recorded.
- `length: double` is enforceable rather than documentary.
- Existing coverage semantics and the 290-test baseline remain intact.

## Phase 1 — Canonical ownership and manifest skeleton

### Files

- Modify `syllabus.md`.
- Modify `units/F1-scientific-python/manifest.yaml`.
- Modify `units/C10-competition-craft/manifest.yaml`.
- Modify `units/F5-probability/manifest.yaml`.
- Modify `units/C2-linear-models/manifest.yaml`.
- Modify `units/C9-dimensionality-reduction/manifest.yaml`.
- Create `units/F7-kernels-convex-optimization/manifest.yaml`.
- Modify `pyproject.toml` and `uv.lock` for a pinned seaborn dependency.
- Add/modify exact ownership regression tests in `tests/test_integration.py` or the narrowest
  existing curriculum-contract test module.

### Steps

1. Add the 21 concept ids to the canonical concept vocabulary and exactly one owner each.
   Correct `seaborn-programming` dependencies from the provisional pandas edge to NumPy and
   matplotlib.  Set F7 prerequisites exactly to `F3-matrices`, `F4-multivar-calculus`,
   `F6-svd-spectral`, and `C3-gradient-descent`.
2. Add fail-first assertions for owner uniqueness, exact prerequisite edges, F5
   `length: double`, the final session/problem counts, and the pinned minute totals.
3. Extend manifests with the problem records specified below.  Until notebooks exist,
   `coverage-check` must fail for missing paths; do not weaken that failure.
4. Add and lock seaborn, then run the focused contract tests, manifest validation, and
   `prereq-check`.

### Acceptance

- All 21 concepts exist in the shipped syllabus and have one owner.
- F7 sits after all four prerequisites and before Plan 018's future SVM consumer.
- The expected intermediate failure is missing notebook evidence, not schema or ownership
  drift.

## Phase 2 — F1 and C10 workflow content

### Files

- Create `units/F1-scientific-python/lessons/04-seaborn-with-arrays.ipynb`.
- Create statement notebooks `units/F1-scientific-python/practice/p22.ipynb` through
  `p24.ipynb`; create their separately authored `_solution.ipynb` files.
- Modify `units/F1-scientific-python/overview.ipynb` and `review.ipynb`.
- Create `units/C10-competition-craft/lessons/04-colab-markdown-round-policy.ipynb`.
- Modify C10 statements and blind solutions `practice/p15`, `p17`, and `p18`.
- Modify `units/C10-competition-craft/overview.ipynb` and `review.ipynb`.

### F1 problem contract

- `F1-p22` (25 min, constrained coding): labeled array-oriented `sns.histplot`, bins and
  deterministic axes checks.
- `F1-p23` (30 min, constrained coding): `sns.scatterplot` with explicit axes, labels,
  legend/style semantics, and NumPy inputs.
- `F1-p24` (40 min, integrative): diagnose and repair a reproducible seaborn comparison,
  including a justified matplotlib boundary.

### C10 rewrite contract

- `C10-p15` becomes a Colab Markdown authoring/repair scenario with separately scored text,
  fenced-code, inline/display-math, and authoring-workflow deliverables.
- `C10-p17` becomes an advanced mixed-cell submission audit that grades Colab coding,
  Markdown snippets/formulae, restart/run-all discipline, and output/file contracts.
- `C10-p18` becomes a round-policy audit that grades the Round 1 CPU versus Round 2 L4/GPU
  boundary without teaching the later GPU workflow.

### Steps and acceptance

1. A GPT-5.6-sol statement author creates lessons/statements only, following the exact
   contracts and leaving no answer leakage or outputs.
2. Inline review checks headings, API constraints, separate scored deliverables, and that
   all five C10 concepts receive at least three honest problem tags across the rewritten
   problems (subparts may support modalities but do not fake distinct practice ids; if three
   ids are insufficient for a concept, redistribute honest deliverables among the three
   rather than inventing a fourth problem).
3. A fresh GPT-5.6-sol session blind-solves only the finalized statements and writes the
   six solution notebooks.
4. Run the changed solutions through fresh Jupyter execution, answer/register/tolerance and
   hygiene checks, then run focused unit coverage.

## Phase 3 — F5 probability and concentration content

### Files

- Create `units/F5-probability/lessons/04-conditional-probability-and-bayes.ipynb`.
- Create `units/F5-probability/lessons/05-hoeffding-inequality.ipynb`.
- Create statements `units/F5-probability/practice/p20.ipynb` through `p25.ipynb` and their
  separately blind-authored solutions.
- Modify `units/F5-probability/overview.ipynb` and `review.ipynb`.

### Problem contract

- `F5-p20`: conditional-probability joint-table normal form.
- `F5-p21`: constrained empirical conditioning and Bayes implementation.
- `F5-p22`: proof/derivation using total probability and Bayes, with a base-rate trap.
- `F5-p23`: Hoeffding normal-form calculation with assumption and constant checks.
- `F5-p24`: seeded simulation versus the theoretical Hoeffding envelope.
- `F5-p25`: integrative conditional/Bayes/concentration decision problem.

### Steps and acceptance

Use separate GPT-5.6-sol statement and blind-solution sessions.
Review denominators, zero-probability conditioning, direction of Bayes updates, boundedness,
independence, widths, tail constants, union bounds, and vacuous bounds.
Fresh-execute all six solutions and run F5 register, tolerance, hygiene, prerequisite,
coverage, and double-length tests.

## Phase 4 — C2 regression and C9 PCA content

### Files

- Create `units/C2-linear-models/lessons/02-normal-equations-rank-pseudoinverse.ipynb`.
- Rename the existing C2 regularization lesson from `02-*` to `03-*` and update every path,
  inventory, schedule, or coverage reference.
- Create C2 statements `practice/p19.ipynb` through `p24.ipynb` and blind solutions; modify
  overview/review.
- Create `units/C9-dimensionality-reduction/lessons/02-pca-covariance-and-numpy-class.ipynb`.
- Rename existing C9 lessons `02-*` to `03-*` and `03-*` to `04-*`, updating all references.
- Create C9 statements `practice/p20.ipynb` through `p24.ipynb` and blind solutions; modify
  overview/review.

### C2 problem contract

- `C2-p19`: derive full-rank normal equations from MSE and prove residual orthogonality.
- `C2-p20`: implement `ols_full_rank(X, y)` with `np.linalg.solve`; ban `inv`, `pinv`,
  `lstsq`, sklearn, and statsmodels; test coefficient and residual contracts.
- `C2-p21`: integrative exact normal-system derivation and controlled numerical check.
- `C2-p22`: prove full column rank iff the Gram matrix is positive definite/invertible and
  reject the false shortcut `n > p`.
- `C2-p23`: implement `ols_pinv` for full- and rank-deficient cases.
- `C2-p24`: characterize the nullspace family and minimum-norm pseudoinverse solution.

### C9 problem contract

- `C9-p20`: derive the centered covariance eigenproblem from directional variance.
- `C9-p21`: prove covariance/SVD equivalence while handling sign and repeated eigenspaces.
- `C9-p22`: implement `NumpyPCA.fit` and `transform` with `mean_`, `components_`,
  `explained_variance_`, and `explained_variance_ratio_`; ban sklearn/scipy PCA.
- `C9-p23`: extend with `fit_transform`, `inverse_transform`, and reconstruction checks;
  integrate all three targets.
- `C9-p24`: rank-deficient and repeated-eigenvalue challenge using subspace/projector
  comparisons.

### Steps and acceptance

Use one statement-author session per unit and fresh blind-solution sessions.
Use seed `20260804` where PCA randomness is needed and explicit `rtol=0` plus task-specific
`atol`.
Fresh-execute all eleven solutions and run changed-unit register, tolerance, hygiene,
prerequisite, and coverage checks.

## Phase 5 — F7 kernels and convex optimization unit

### Files

- Create `units/F7-kernels-convex-optimization/overview.ipynb` and `review.ipynb`.
- Create lessons:
  - `lessons/01-psd-matrices-and-kernels.ipynb`;
  - `lessons/02-kernel-proofs-and-counterexamples.ipynb`;
  - `lessons/03-convex-sets-functions-and-optimality.ipynb`;
  - `lessons/04-lagrangians-duality-and-certificates.ipynb`.
- Create statements `practice/p01.ipynb` through `p20.ipynb` and, in separate fresh
  sessions, all corresponding solutions.

### Session contract

1. Quadratic-form/eigenvalue PSD tests, Gram matrices, feature maps, and the finite-Gram
   definition of a valid kernel; explicitly build on F6 rather than claiming PSD is absent.
2. Kernel closure rules, polynomial examples, proof versus finite testing, and constructive
   negative-eigenvalue counterexamples.
3. Convex sets/functions, Jensen and line-restriction proofs, first-order supporting-plane
   inequalities, and local-to-global optimality.
4. Constrained problems, Lagrangian sign conventions, primal/dual bounds, complementary
   slackness, and KKT certificate reading under stated assumptions.

### Practice register

`p01` PSD MC; `p02` kernel-quantifier MC; `p03` convex-set MC; `p04` convex-quadratic
normal form; `p05` `psd_report`; `p06` `poly2_gram`; `p07` negative-eigen witness; `p08`
affine-halfspace convex combinations; `p09` Jensen gaps; `p10` `kkt_residuals`; `p11`
Gram/kernel proof; `p12` quadratic convexity/supporting-gradient proof; `p13` polynomial
kernel proof/refutation; `p14` constrained quadratic/KKT/dual integration; `p15` sampled
validity versus proof scenario; `p16` local descent versus global convexity scenario; `p17`
kernel closure/feature-map challenge; `p18` constrained dual/zero-gap challenge; `p19`
segment/Jensen drill; `p20` weak-duality/activity/slackness drill.

The distribution is exactly four MC/normal-form, six coding, two proof, two integrative,
two scenario, two challenge, and two drills; six intro, nine core, and five advanced.

### Steps and acceptance

Dispatch lessons/statements in bounded batches to GPT-5.6-sol; no solution author receives
the statement author's outline or intermediate answers.
Review every proof direction, sign convention, quantifier, and assumption inline before
blind solving.
Fresh-execute all 20 solutions and require all seven concepts to have at least three honest
practice ids, including both proof/refutation and computational evidence where required.

## Phase 6 — Evidence promotion, inventory, roadmap, and schedule

### Files

- Modify `curriculum/coverage-map.yaml` only from inspected final notebooks/manifests.
- Regenerate `curriculum/material-inventory.yaml`.
- Regenerate `docs/audits/015-coverage-audit.md`.
- Regenerate `docs/curriculum-roadmap.md`.
- Modify `docs/course-structure.md` to a 31-week prerequisite-valid schedule.
- Modify `TODO.md` to mark Plan 016 complete and leave Plans 017–018 as the next R1 queue.
- Modify this plan's post-execution report.

### Steps

1. For each of the 21 targets, name exact lesson heading/cell anchors and primary practice
   ids for every required modality.  Do not promote from plan prose or a solution alone.
2. Run the audit and roadmap renderers in write mode, inspect the diff, then run both in
   `--check` mode.  The inventory must include every new/renamed notebook and no stale path.
3. Extend rather than compress the calendar.  Recompute totals from manifests; expected
   values are 14,647 manifested and 14,887 scheduled minutes, 383 unit practices, 57 lesson
   sessions, and 17 units.  If content-driven minute estimates differ, reconcile the
   manifests, arithmetic, and design explicitly rather than silently changing one source.
4. Confirm every Plan 016 target is checker-derived `covered`, the overall acknowledged
   Round 1 gap count has fallen by exactly the number of targets that were not already
   covered, and no unrelated row regresses.

## Phase 7 — Named verification phase

Run from a clean commit, in this order:

```bash
uv run pytest tests/test_prereq_coverage.py tests/test_integration.py -q
uv run python tools/audit_curriculum.py --check
uv run python tools/render_curriculum_roadmap.py --check
uv run usaaio-tools prereq-check
uv run usaaio-tools coverage-check
uv run usaaio-tools scope-check
uv run usaaio-tools tolerance-check
uv run usaaio-tools hygiene-check
uv run usaaio-tools overlap-scan
bash scripts/ci-local.sh
git diff --check
```

Additionally, run fresh Jupyter execution for every changed/new solution and every changed
lesson/review/overview before the full CI; fallback cell execution is not fresh-kernel
evidence and must be reported separately if the environment blocks Jupyter.

Acceptance requires full green CI, zero stale generated artifacts, zero missing/duplicate
register entries, no student outputs or answer leakage, explicit tolerances, and exact final
counts reconciled to the manifests.

## Phase 8 — Four-way content gate and delivery

1. Run the required four-way content-review gate from a clean implementation commit:
   active-session self-review, GPT-5.6-sol, GPT-5.6-terra, and GLM-5.2.
   Every reviewer reads the final diff, checks source/solution isolation, blind-solves a
   risk-selected sample across all six owners, and returns one verdict.
2. Record every finding below as `[reviewer] [OPEN|FIXED|WONTFIX]`; fix all blockers and
   rerun affected verification.  The gate passes only at 4/4 with no `[OPEN]` finding.
3. Populate the post-execution report with delivered files/counts, source boundary,
   fail-first evidence, fresh execution evidence, full-CI output, review verdicts, and any
   divergence from the pinned design.
4. Push the feature branch, open a PR, fetch `origin/main`, run
   `bash scripts/pre-merge-guard.sh --pr`, squash-merge, and verify the squash commit on
   `main`.  Never merge if CI or the PR-aware guard fails.

## Plan Review

### Review 1 — self-review

- **Verdict:** APPROVE.
- `[self] [FIXED]` The first draft carried incorrect final corpus counts.  The
  arithmetic is now derived from the Plan 015 baseline: 343 + 40 = 383 practices and
  47 + 10 = 57 lesson sessions.
- `[self] [FIXED]` The verification list named a nonexistent `manifest-check`
  subcommand.  It now invokes only actual CLI checks and leaves full manifest/schema
  validation to the focused tests and `scripts/ci-local.sh`.
- `[self]` Scope, ownership, prerequisite closure, double-length enforcement,
  author/solver isolation, exact content contracts, named verification, content gate,
  shipping lifecycle, and 2,300-minute schedule extension are explicit and mutually
  consistent.  No open finding remains.

### Review 2 — GPT-5.6-sol

- **Status:** pending.

### Review 3 — GPT-5.6-terra

- **Status:** pending.

### Review 4 — GLM-5.2

- **Status:** pending.

**GATE RESULT: PENDING.** No implementation may start before 4/4 approval.

## Content Review

Pending implementation and the named verification phase.

## Post-Execution Report

Pending implementation, verification, review, PR, and squash merge.
