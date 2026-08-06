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
| C10 | `colab-markdown-solution-authoring`, `markdown-code-snippets`, `markdown-math-formulae`, `colab-coding-submission`, `cpu-and-gpu-round-boundary` | 4 / 24 | 335 + 730 + 55 = 1,120 |
| F5 | `conditional-probability`, `bayes-rule`, `hoeffding-inequality` | 5 / 25 | 415 + 650 + 55 = 1,120 |
| C2 | `linear-regression-estimator-derivation`, `ols-rank-identifiability-and-pseudoinverse` | 3 / 24 | 260 + 590 + 55 = 905 |
| C9 | `pca-centered-covariance-eigenproblem-derivation`, `numpy-pca-class-from-scratch`, `pca-black-box-insufficiency` | 4 / 24 | 340 + 600 + 60 = 1,000 |
| F7 | `positive-semidefinite-matrices`, `kernel-validity`, `convex-sets`, `convex-functions`, `first-order-optimality`, `lagrangians`, `optimization-duality` | 4 / 20 | 340 + 640 + 45 = 1,025 |

The pinned net addition is 2,420 manifested minutes: F1 +175, C10 +290, F5 +400,
C2 +275, C9 +255, and F7 +1,025.
The expected repository totals are 14,767 manifested minutes and 15,007 scheduled minutes,
laid out as a prerequisite-valid 31-week course near eight hours per week.

### Canonical cluster and track assignments

F7's exact syllabus track is `foundation`.
The 21 new concept ids use the existing cluster vocabulary as follows; implementation may
not invent a new cluster or leave these choices to notebook authors.

| Cluster | New concept ids |
|---|---|
| `python-scientific` | `seaborn-programming` |
| `competition-craft` | `colab-markdown-solution-authoring`, `markdown-code-snippets`, `markdown-math-formulae`, `colab-coding-submission`, `cpu-and-gpu-round-boundary` |
| `probability-statistics` | `conditional-probability`, `bayes-rule`, `hoeffding-inequality` |
| `ml-concepts` | `linear-regression-estimator-derivation`, `ols-rank-identifiability-and-pseudoinverse`, `pca-centered-covariance-eigenproblem-derivation`, `numpy-pca-class-from-scratch`, `pca-black-box-insufficiency` |
| `linear-algebra` | `positive-semidefinite-matrices`, `kernel-validity`, `convex-sets` |
| `calculus-multivar` | `convex-functions`, `first-order-optimality`, `lagrangians`, `optimization-duality` |

### Atomic coverage targets

Plan 016 ships 21 syllabus concepts but promotes exactly 17 Plan 015 atomic coverage rows.
The mapping is pinned so concept ownership cannot be confused with roadmap status:

| Atomic target(s) | Shipped concept mapping |
|---|---|
| the five C10 targets with the same ids | their five one-to-one C10 concepts |
| `seaborn-programming` | `seaborn-programming` |
| `conditional-probability`, `bayes-rule`, `hoeffding-inequality` | the three one-to-one F5 concepts |
| `linear-regression-estimator-derivation`, `ols-rank-identifiability-and-pseudoinverse` | the two one-to-one C2 concepts |
| `pca-centered-covariance-eigenproblem-derivation`, `numpy-pca-class-from-scratch`, `pca-black-box-insufficiency` | the three one-to-one C9 concepts |
| `valid-kernel-positive-definite-proof` | `positive-semidefinite-matrices`, `kernel-validity` |
| `convex-sets-functions-and-optimality` | `convex-sets`, `convex-functions`, `first-order-optimality` |
| `constrained-optimization-lagrangian-duality` | `lagrangians`, `optimization-duality` |

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
- Modify `tests/test_model.py`.
- Modify `tools/model.py`.
- Modify `tools/checks/coverage.py`.
- Modify `.gitignore` to exclude project-local `.codex-buddy/` reviewer/runtime state.
- Modify `TODO.md` only to register Plan 016 as active.

### Steps

1. Confirm the branch is `feature/plan-016-r1-foundation-math`, both local reference index
   symlinks resolve, `scripts/pre-merge-guard.sh` passes, and the baseline full CI is green.
   Record exact commands and counts in the post-execution report.
2. Extend `UnitManifest` with parsed `lesson_sessions: list[int] | None` from
   `estimated_minutes.lesson_sessions`; keep the field optional for legacy/minimal
   non-double fixtures, reject malformed non-list/non-integer values in model tests, and
   make a missing value an actionable coverage error for a double-length unit.
3. Add fail-first fixtures proving a syllabus unit with `length: double` fails below four or
   above six lesson sessions and below 24 or above 30 practices; a compliant 4–6/24–30
   fixture passes.  Pin real F6 as a passing double-length regression, the final F5 shape as
   a fixture before its content exists, and a hypothetical C7 `length: double` with its
   current three sessions as failing.  Normal C7 remains its recorded non-conformance; the
   new logic runs only when `unit.length == "double"` and does not legalize normal overflow.
4. Run the focused tests and capture the expected red output before changing the checker:

   ```bash
   uv run pytest tests/test_model.py tests/test_prereq_coverage.py -q
   ```

5. Implement the smallest checker change by joining loaded syllabus unit metadata to the
   corresponding manifest.  Count `estimated_minutes.lesson_sessions` and distinct practice
   ids/paths; issue actionable errors naming the unit, observed count, and required band.
6. Rerun the focused tests green, then run `ruff check tools/model.py
   tools/checks/coverage.py tests/test_model.py tests/test_prereq_coverage.py`.
7. Add `.codex-buddy/` to `.gitignore`; reviewer prompts, session logs, and runtime scratch
   are local evidence and must never enter this public repository.

### Acceptance

- Red-before-green evidence is recorded.
- `length: double` is enforceable rather than documentary.
- All original 290 baseline tests still pass; new contract tests increase rather than
  replace that count.

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
- Modify `curriculum/coverage-map.yaml` for the controlled seaborn dependency and planned
  F7-owner conversion.
- Modify `tests/test_scope.py`.
- Modify `docs/unit-standards.md` so the double-length parenthetical names F5 and F6.
- Modify `tests/test_integration.py` for exact ownership and the named
  `test_f1_seaborn_array_only_boundary` regression.

### Steps

1. Add the 21 concept ids with the pinned clusters above to the canonical concept vocabulary
   and exactly one owner each.  Set F7 to `track: foundation` and prerequisites exactly to
   `F3-matrices`, `F4-multivar-calculus`, `F6-svd-spectral`, and
   `C3-gradient-descent`.
2. Make the controlled roadmap conversion explicit and fail-first tested:
   - change `seaborn-programming.depends_on` from pandas + matplotlib to
     `numpy-programming` + `matplotlib-pyplot-programming` and preserve the array-only
     rationale;
   - remove `P015-R1-MATH-KERNEL-OPT` from `planned_units`;
   - change all three F7 atomic rows from `new-unit`/the provisional id to
     `extend-existing-unit`/`F7-kernels-convex-optimization` and populate their exact
     shipped-concept mapping above;
   - replace the provisional math-unit prerequisite in `P015-R1-CLASSICAL-BREADTH` with
     `F7-kernels-convex-optimization`.
3. Add fail-first assertions for owner uniqueness, exact clusters/prerequisite edges, F5
   `length: double`, the final session/problem counts, and the pinned minute totals.
4. Extend manifests with the problem records specified below.  Until notebooks exist,
   `coverage-check` must fail for missing paths; do not weaken that failure.
5. Add and lock seaborn, then run the focused contract tests, manifest validation, and
   `prereq-check`.
6. Reconcile the narrative portion of `syllabus.md`, not only its YAML fence:
   - name both F5 and F6 as double-length;
   - add F7 and its kernel/convexity role to the foundation rationale;
   - state that C2 session 02 now ships the estimator derivation and rank/pseudoinverse
     bridges instead of calling them missing;
   - list all 17 units in the shipped topological order, with
     `... → C8 → F6 → F7 → C9 → C10` after F7's other prerequisites have appeared.

### Acceptance

- All 21 concepts exist in the shipped syllabus and have one owner.
- F7 sits after all four prerequisites and before Plan 018's future SVM consumer.
- No syllabus prose asserts that a Plan 016 concept is missing; the suggested order names
  all 17 shipped units; `docs/unit-standards.md` names F5 and F6 as double-length.
- The expected intermediate failure is missing notebook evidence, not schema or ownership
  drift.

## Phase 2 — F1 and C10 workflow content

### Files

- Create `units/F1-scientific-python/lessons/04-seaborn-with-arrays.ipynb`.
- Create statement notebooks `units/F1-scientific-python/practice/p22.ipynb` through
  `p24.ipynb`; create their separately authored `_solution.ipynb` files.
- Modify `units/F1-scientific-python/lesson.ipynb` and `review.ipynb`.
- Create `units/C10-competition-craft/lessons/04-colab-markdown-round-policy.ipynb`.
- Modify C10 statements and blind solutions `practice/p15`, `p17`, and `p18`.
- Modify `units/C10-competition-craft/lesson.ipynb` and `review.ipynb`.

### F1 problem contract

- `F1-p22` (25 min, constrained coding): labeled array-oriented `sns.histplot`, bins and
  deterministic axes checks.
- `F1-p23` (30 min, constrained coding): `sns.scatterplot` with explicit axes, labels,
  legend/style semantics, and NumPy inputs.
- `F1-p24` (40 min, integrative): diagnose and repair a reproducible seaborn comparison,
  including a justified matplotlib boundary.

The F1 root `lesson.ipynb`, all four session notebooks, `review.ipynb`, and p22–p24
statements/solutions prohibit `import pandas`, `from pandas`, `pd.`, and `DataFrame` use.
`tests/test_integration.py::test_f1_seaborn_array_only_boundary` scans that complete named
set.  Seaborn's internal dependency on pandas does not make the C4 pandas API
student-facing in F1.

### C10 rewrite contract

- `C10-p15` becomes a Colab Markdown authoring/repair scenario with separately scored text,
  fenced-code, inline/display-math, and authoring-workflow deliverables.
- `C10-p17` becomes an advanced mixed-cell submission audit that grades Colab coding,
  Markdown snippets/formulae, restart/run-all discipline, and output/file contracts.
- `C10-p18` becomes a round-policy audit that grades the Round 1 CPU versus Round 2 L4/GPU
  boundary without teaching the later GPU workflow.

Each rewritten problem preserves an honest, separately scored `writeup-quality` deliverable
and contains one separately scored deliverable for every new C10 concept:

| Practice | `writeup-quality` | existing model-selection evidence | Colab authoring | fenced code | Markdown math | coding submission | CPU/GPU boundary |
|---|---|---|---|---|---|---|---|
| `C10-p15` | approach + intuition paragraph | not a primary carrier | choose/repair text and code cells | repair a fenced function excerpt | derive and render one metric formula | required identifier + restart/run-all + download checks | identify and correct an illegal R1 GPU claim |
| `C10-p17` | approach + alternatives in the mini-competition writeup | preserve the bounded pipeline/validation choice, refit, and packaged prediction deliverables | assemble the mixed-cell response | render the `predict_labels` excerpt | render and explain the scored metric | portability, state-loss, output, and `.ipynb` preflight | write the R1 CPU declaration and contrast the R2 L4 allowance |
| `C10-p18` | corrected approach/alternatives section | audit and repair the pipeline, validation, bounded-selection, refit, and prediction path | repair wrong cell types in the flawed submission | repair its malformed fenced snippet | repair and interpret its malformed formula | audit identifiers, restart/run-all, file and download contract | diagnose the illegal GPU and state the exact round boundary |

The manifest tags the five new concepts plus existing `writeup-quality` on all three ids
only after the statement exposes these six scored rows.  This preserves the existing
three-practice `writeup-quality` and
`markdown-text-communication` evidence while satisfying the five new three-practice floors.
The rewritten problem budgets are pinned at 90 minutes for p15, 135 for p17, and 105 for
p18.  The manifest reserves 400 minutes for the other 21 practices and 330 for these three,
so C10 practice totals 730 minutes; the unit total is 1,120 and its Plan 016 increment is
290 minutes.  Authors may simplify subparts within these budgets but may not compress a
scored concept into a token mention.

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
   hygiene checks, then run focused unit coverage and
   `uv run pytest tests/test_integration.py -q -k f1_seaborn_array_only_boundary`.

## Phase 3 — F5 probability and concentration content

### Files

- Create `units/F5-probability/lessons/04-conditional-probability-and-bayes.ipynb`.
- Create `units/F5-probability/lessons/05-hoeffding-inequality.ipynb`.
- Create statements `units/F5-probability/practice/p20.ipynb` through `p25.ipynb` and their
  separately blind-authored solutions.
- Modify `units/F5-probability/lesson.ipynb` and `review.ipynb`.

### Problem contract

- `F5-p20`: conditional-probability joint-table normal form.
- `F5-p21`: constrained empirical conditioning and Bayes implementation.
- `F5-p22`: proof/derivation using total probability and Bayes, with a base-rate trap.
- `F5-p23`: Hoeffding normal-form calculation with assumption and constant checks.
- `F5-p24`: simulation with `SEED = 20260804` versus the theoretical Hoeffding envelope.
- `F5-p25`: integrative conditional/Bayes/concentration decision problem.

Session 05 teaches the event subadditivity/union-bound lemma
`P(A ∪ B) ≤ P(A) + P(B)` immediately before deriving the two-sided Hoeffding factor of
two from the upper- and lower-tail events.  This is an in-lesson prerequisite lemma under
`hoeffding-inequality`, not a new standalone syllabus concept.  p23 may grade that short
derivation; no problem may assume the union bound without this teaching anchor.

### Steps and acceptance

Use separate GPT-5.6-sol statement and blind-solution sessions.
Review denominators, zero-probability conditioning, direction of Bayes updates, boundedness,
independence, widths, tail constants, union bounds, and vacuous bounds.
Acceptance includes a lesson checkpoint deriving the two-sided constant through the taught
subadditivity lemma and a p23 solution that cites the same route.
Fresh-execute all six solutions and run F5 register, tolerance, hygiene, prerequisite,
coverage, and double-length tests.

## Phase 4 — C2 regression and C9 PCA content

### Files

- Create `units/C2-linear-models/lessons/02-normal-equations-rank-pseudoinverse.ipynb`.
- Rename the existing C2 regularization lesson from `02-*` to `03-*` and update every path,
  inventory, schedule, or coverage reference.
- Create C2 statements `practice/p19.ipynb` through `p24.ipynb` and blind solutions; modify
  `lesson.ipynb`/`review.ipynb`.
- Create `units/C9-dimensionality-reduction/lessons/02-pca-covariance-and-numpy-class.ipynb`.
- Rename existing C9 lessons in collision-safe order: move current `03-*` to `04-*`, then
  current `02-*` to `03-*`, then create the new `02-*`; use no forced overwrite and update
  all references.
- Create C9 statements `practice/p20.ipynb` through `p24.ipynb` and blind solutions; modify
  `lesson.ipynb`/`review.ipynb`.

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

- Create `units/F7-kernels-convex-optimization/lesson.ipynb` and `review.ipynb`.
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

| ID | Set | Type | Difficulty | Exact new-concept tags | Contract |
|---|---|---|---|---|---|
| p01 | A | MC, five options A–E | intro | `positive-semidefinite-matrices` | PSD classification |
| p02 | A | MC, five options A–E | intro | `kernel-validity` | kernel quantifier |
| p03 | A | MC, five options A–E | intro | `convex-sets` | convex-set witness |
| p04 | B | numeric normal-form MC, five options A–E | core | `convex-functions`, `first-order-optimality` | convex quadratic with reduced-fraction/gcd/sign contract |
| p05 | A | constrained coding | intro | `positive-semidefinite-matrices` | `psd_report` |
| p06 | B | constrained coding | core | `positive-semidefinite-matrices`, `kernel-validity` | `poly2_gram` |
| p07 | B | constrained coding | core | `positive-semidefinite-matrices`, `kernel-validity` | negative-eigen witness |
| p08 | A | constrained coding | intro | `convex-sets` | affine-halfspace convex combinations |
| p09 | B | constrained coding | core | `convex-functions` | Jensen gaps |
| p10 | B | constrained coding | advanced | `lagrangians`, `optimization-duality` | `kkt_residuals` |
| p11 | B | proof | core | `positive-semidefinite-matrices`, `kernel-validity` | Gram/kernel proof; `Reasoning is required` |
| p12 | B | proof | advanced | `positive-semidefinite-matrices`, `convex-functions`, `first-order-optimality` | quadratic convexity/supporting-gradient proof; `Reasoning is required` |
| p13 | C | integrative multi-part | core | `positive-semidefinite-matrices`, `kernel-validity` | compute polynomial Gram matrix, consume it in a feature-map proof, then consume both results to refute a perturbed kernel |
| p14 | C | integrative multi-part | advanced | `convex-sets`, `convex-functions`, `first-order-optimality`, `lagrangians`, `optimization-duality` | constrained quadratic → KKT → dual chain |
| p15 | C | scenario | core | `positive-semidefinite-matrices`, `kernel-validity` | sampled validity versus proof |
| p16 | C | scenario | core | `convex-functions`, `first-order-optimality` | local descent versus global convexity |
| p17 | C | challenge | advanced | `kernel-validity` | kernel closure/feature maps |
| p18 | C | challenge | advanced | `lagrangians`, `optimization-duality` | constrained dual/zero gap |
| p19 | A | drill | intro | `convex-sets`, `convex-functions` | segment/Jensen violations |
| p20 | B | drill | core | `lagrangians`, `optimization-duality` | weak duality/activity/slackness |

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
- Modify `tools/render_curriculum_roadmap.py`.
- Modify `tests/test_scope.py` for completed-tranche and disposition regressions.
- Modify `docs/course-structure.md` to a 31-week prerequisite-valid schedule.
- Modify `TODO.md` to mark Plan 016 complete and leave Plans 017–018 as the next R1 queue.
- Modify this plan's post-execution report.

### Steps

1. For each of the 17 atomic targets, name exact lesson heading/cell anchors and primary practice
   ids for every required modality.  Do not promote from plan prose or a solution alone.
   Once checker-derived coverage is `covered`, set all 17 dispositions to `keep`, including
   the three F7 rows, and add a scope regression that every covered row uses `keep`.
2. Update the roadmap renderer before regeneration:
   - remove F5, C2, and C9 from `MAJOR_EXISTING_UNIT_EXTENSIONS`, leaving only C7 and an
     8–12-hour subtotal;
   - delete the completed foundation/math tranche from `TRANCHE_QUEUE` so neural-training
     is first;
   - remove C10 and F1 from the sentence listing unestimated corrections;
   - replace the now-false "These four ranges" prose with the singular statement
     "This range is a renderer-owned editorial estimate, not a field in the canonical
     coverage map.";
   - add tests that no unit owning shipped Plan 016 concepts remains in the extension table
     and the queue begins with Round 1 neural-training completion.  Rebase the real-repo
     baseline/delta assertions to 14,767 / 15,007 minutes and the 8–12-hour remaining
     extension subtotal; update the unestimated-corrections text assertion; replace the
     six-tranche queue test with a five-tranche test led by neural training and remove its
     completed F5/C2/C9-extension assertions; assert the new singular estimate wording.
3. Run the audit and roadmap renderers in write mode, inspect the diff, then run both in
   `--check` mode.  The inventory must include every new/renamed notebook and no stale path.
4. Extend rather than compress the calendar.  Recompute totals from manifests; expected
   values are 14,767 manifested and 15,007 scheduled minutes, 383 unit practices, 57 lesson
   sessions, and 17 units.  If content-driven minute estimates differ, reconcile the
   manifests, arithmetic, and design explicitly rather than silently changing one source.
   Preserve a two-semester model as 16 weeks + 15 weeks: Semester 1 is Weeks 1–16,
   Semester 2 is Weeks 17–31, r1-001 plus debrief is in Week 31, and optional r1-002
   displaces C-set/challenge practice in Week 16 rather than adding time.
5. Confirm all 17 Plan 016 targets are checker-derived `covered`, the acknowledged Round 1
   gap count falls exactly from 32 to 15, no unrelated row regresses, the provisional F7
   planned unit is absent, and the Plan 018 classical node depends on shipped F7.  Confirm
   the renderer has no completed Plan 016 unit in its pending extension table, the queue
   begins with neural training, every covered disposition is `keep`, and the semester
   boundary plus both mock-test weeks are stated and prerequisite-valid.

## Phase 7 — Named verification phase

Run from a clean commit, in this order:

```bash
uv run pytest tests/test_model.py tests/test_prereq_coverage.py tests/test_scope.py \
  tests/test_integration.py -q
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
test -z "$(git status --porcelain)"
```

Additionally, run fresh Jupyter execution for every changed/new solution and every changed
lesson/review/root lesson index before the full CI.  A blocked fresh Jupyter run is a hard shipping
stop: fallback cell execution may aid diagnosis but cannot authorize the content gate, PR,
or merge.

Acceptance requires full green CI, zero stale generated artifacts, zero missing/duplicate
register entries, no student outputs or answer leakage, explicit tolerances, and exact final
counts reconciled to the manifests.

## Phase 8 — Four-way content gate and delivery

1. Run the required four-way content-review gate from a clean implementation commit:
   active-session self-review, Claude Opus 5 (`claude-opus-5`), GPT-5.6-terra, and
   GLM-5.2.
   Every reviewer reads the final diff, checks source/solution isolation, and blind-solves
   every changed or new student-facing statement before reading its solution.  Risk-selected
   deep checks may supplement but never replace the all-problem duty.  The same roster also
   conventionally code-reviews the `tools/` and `tests/` diff as required by
   `docs/content-review-gate.md`.
2. Record every finding below as `[reviewer] [OPEN|FIXED|WONTFIX]`; fix all blockers and
   rerun affected verification.  The gate passes only at 4/4 with no `[OPEN]` finding.
3. Populate the post-execution report with delivered files/counts, source boundary,
   fail-first evidence, fresh execution evidence, full-CI output, review verdicts, and any
   divergence from the pinned design.
4. After all content-gate fixes and report edits, commit the final tree and rerun the entire
   `bash scripts/ci-local.sh` plus `git diff --check`; focused affected checks are not a
   substitute.  Require `git status --porcelain` to be empty before push; ignored
   `.codex-buddy/` state is never staged.  This second clean-commit full run is the final
   shipping evidence.
5. Push the feature branch, open a PR, fetch `origin/main`, run
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
  shipping lifecycle, and 2,420-minute schedule extension are explicit and mutually
  consistent.  No open finding remains.
- `[self] [FIXED]` The consolidated external review exposed distinctions the first inline
  pass missed: 17 atomic targets versus 21 concepts, model support for session counts,
  C10's six-way evidence preservation, planned-node replacement, and a second final CI.
  The revised plan pins each contract explicitly; inline re-review finds no remaining
  contradiction.
- `[self] [FIXED]` Final path verification found draft references to nonexistent
  `overview.ipynb` files.  Every affected existing/new unit index is now correctly named
  `lesson.ipynb`, matching the shipped unit standard and repository layout.

### Review 2 — Claude Opus 5

- **First verdict:** REJECT.
- `[opus] [FIXED]` The roadmap renderer would have retained Plan 016's F5/C2/C9 estimates
  and tranche queue after shipping.  Phase 6 now updates the renderer, removes completed
  work, and pins freshness/queue regressions.
- `[opus] [FIXED]` Syllabus prose would still have called the C2 derivation missing, omitted
  F7 from the shipped path, and named only F6 as double-length.  Phase 1 now reconciles all
  narrative and standards text and asserts all 17 units appear.
- `[opus] [FIXED]` C10's three carrier problems were underbudgeted.  They now have explicit
  90/135/105-minute budgets, 730 total practice minutes, a 290-minute unit increment, and
  fully recomputed course totals.
- `[opus] [FIXED]` All 17 completed rows now pin disposition `keep`; F5 teaches the
  union-bound lemma used for the two-sided Hoeffding constant; both receive regression or
  content acceptance checks.
- `[opus] [FIXED]` `.codex-buddy/` is ignored, clean porcelain status is a shipping gate,
  the 31 weeks are pinned as 16 + 15 with mock weeks, and the content gate explicitly
  reviews Phase 0 tooling.
- `[opus] [FIXED]` The approve-with-nits re-review found stale "four ranges" renderer prose
  and underspecified old-total/six-tranche test updates.  Phase 6 now pins the singular
  wording plus every affected baseline, delta, unestimated-text, and five-tranche assertion.
- **Final verdict:** APPROVE WITH NITS; both nits are fixed above.

### Supplemental review — GPT-5.6-sol (pre-roster change)

- **First verdict:** REJECT.
- `[sol] [FIXED]` Phase 6 confused 21 syllabus concepts with 17 atomic coverage targets.
  The plan now pins the complete mapping and the expected Round 1 gap change 32 → 15.
- `[sol] [FIXED]` The three C10 rewrites could lose `writeup-quality` or acquire decorative
  new tags.  The target × practice matrix now preserves the existing objective and exposes
  six separately scored deliverables in each of p15, p17, and p18.
- `[sol] [FIXED]` The content gate used sampled blind solving and the shipping phase lacked
  a post-review full CI.  Every reviewer must now solve every changed/new statement, and a
  second clean-commit full CI is mandatory after all fixes/report edits.
- `[sol] [FIXED]` Cluster assignments, F7's `foundation` track, and the double-length
  model/loader data path are now fully specified.
- `[sol] [FIXED]` The approve-with-nit re-review noted that C10-p17/p18 are primary
  `end-to-end-model-selection` evidence.  Their bounded pipeline/validation, refit, and
  prediction deliverables are now explicitly preserved in the matrix.
- **Final verdict:** APPROVE WITH NITS; the sole nit is fixed above.

### Review 3 — GPT-5.6-terra

- **First verdict:** REJECT.
- `[terra] [FIXED]` Phase 0 now extends `UnitManifest`, validates malformed/missing session
  data, and pins F5/F6/C7 regressions with logic restricted to `length == "double"`.
- `[terra] [FIXED]` The plan now removes the provisional F7 node, converts its three atomic
  rows and exact concept mappings to shipped F7, updates the future classical prerequisite,
  and asserts 17—not 21—promotions.
- `[terra] [FIXED]` The seaborn pandas→NumPy/matplotlib dependency amendment and its
  taught-order regression are explicit Phase 1 work.
- `[terra] [FIXED]` The C10 evidence matrix and all-problem blind gate resolve the two
  remaining blockers.
- `[terra] [FIXED]` F7 now pins four five-option MCs, every set/type/difficulty, and p13 as
  an integrative chain rather than an extra proof.
- **Final verdict:** APPROVE.

### Review 4 — GLM-5.2

- **First verdict:** REJECT.
- `[glm] [FIXED]` C9 renames now use collision-safe `03→04`, `02→03`, create-new-02 order
  with no forced overwrite.
- `[glm] [FIXED]` C10 preserves three honest `writeup-quality` carriers; F7-p13 is pinned
  as integrative; F1 bans pandas APIs; F5-p24 uses `SEED = 20260804`; blocked fresh Jupyter
  is a hard stop; Sol/Terra dispatch models are explicit; and double-length logic is
  conditional on the syllabus label.
- `[glm] [FIXED]` The approve-with-nits re-review requested a named full-surface F1 pandas
  ban test, precise five-new-plus-one-existing C10 wording, and explicit F7 concept tags.
  All three are now pinned above.
- **Final verdict:** APPROVE WITH NITS; all nits are fixed above.

**GATE RESULT: PASS — 4/4.** The current roster is self APPROVE, Claude Opus 5 APPROVE
WITH NITS, GPT-5.6-terra APPROVE, and GLM-5.2 APPROVE WITH NITS.  Every blocker, concern,
and nit is fixed in the final plan; the earlier GPT-5.6-sol pass is supplemental only.

## Content Review

Pending implementation and the named verification phase.

## Post-Execution Report

Pending implementation, verification, review, PR, and squash merge.
