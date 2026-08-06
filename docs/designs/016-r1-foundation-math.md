# Design 016 — Round 1 Foundation, Workflow, and Mathematical Completion

## Objective

Close the first dependency-ordered Round 1 tranche from Plan 015 without duplicating the
curriculum or making planned topics look shipped before their evidence exists.
The delivered curriculum must teach and practice the official workflow, probability,
linear-estimator, PCA, kernel-validity, and convex-optimization targets needed before the
neural-training and classical-breadth tranches.

Plan 016 is complete only when the corresponding coverage-map rows are checker-derived
`covered`, the shipped syllabus owns every new concept exactly once, the course schedule
contains the added time, and all statement/solution notebooks pass the repository gates.

## Considered approaches

### Append new practices to every existing unit

This is mechanically simple but violates the 16–24 problem band.
`C10-competition-craft` already has 24 problems, `C4-classical-ml-practice` has 23, and the
other affected units are close enough that three new problems per target would overflow
several units.
This approach is rejected.

### Create one micro-unit per missing topic

This preserves existing units but fragments prerequisite arcs such as conditional
probability → Bayes and centered covariance → PCA eigensystem → NumPy class.
It would also duplicate existing regression, probability, PCA, and notebook-workflow
context.
This approach is rejected.

### Deepen existing units and add one coherent mathematical unit

This is the selected design.
Existing-unit targets are taught in added sessions and graded either by new practices where
the unit has honest capacity or by rewriting selected existing practices whose original
learning objectives can absorb the new concept honestly.
C10 stays at its existing 24-problem ceiling; F1 grows to 24; F5 becomes an honestly
double-length five-session/25-problem unit; C2 and C9 remain inside their declared bands.
Kernel validity and convex/constrained optimization form one new unit because no existing
unit owns that coherent arc and Plan 018's SVM work consumes it directly.

## Curriculum placement

### F1 scientific plotting extension

Seaborn remains in `F1-scientific-python`, but its provisional pandas dependency is
corrected to NumPy plus matplotlib so the taught order is honest.
The new shipped concept is `seaborn-programming` in the `python-scientific` cluster.
A 70-minute fourth session teaches array-oriented `histplot` and `scatterplot`, axes
contracts, deterministic styling, labels/legends, and when direct matplotlib is clearer.
The dependency and lesson do not claim the later tidy-DataFrame surface taught in C4.
Three new practices (`F1-p22`–`F1-p24`) grade the API and bring F1 to exactly 24 problems.
Seaborn becomes a pinned project dependency rather than an assumed local package.

### C10 Colab and Markdown workflow extension

`C10-competition-craft` receives a fourth session covering Colab text/code cells, Markdown
code fences, inline/display mathematics, coding submission checks, and the official Round 1
CPU versus Round 2 GPU/L4 boundary.
The five shipped concepts use the exact target ids
`colab-markdown-solution-authoring`, `markdown-code-snippets`,
`markdown-math-formulae`, `colab-coding-submission`, and
`cpu-and-gpu-round-boundary`.
Selected existing C10 problems are rewritten into authoring, repair, and submission-audit
tasks; the unit remains at 24 problems.
Generic notebook use, prose quality, or a passing mention of CUDA is not sufficient
evidence.

### F5 conditional probability, Bayes, and concentration

`F5-probability` receives two sessions with the arc conditional probability → total
probability → Bayes → empirical estimation, followed by Hoeffding's
bounded-independent-variable guarantee and simulation checks.
The concepts are `conditional-probability`, `bayes-rule`, and `hoeffding-inequality`.
Six new practices (`F5-p20`–`F5-p25`) grade each concept across theory/derivation and
implementation; multi-tagging is allowed only when every tagged concept changes the graded
answer.
F5 is marked double-length because it now has five sessions and 25 problems.
Plan 016 also makes the double-length session/problem ranges machine-enforceable so the
label cannot become the unenforced exception rejected during Plan 014.

### C2 estimator derivation and rank-deficient behavior

`C2-linear-models` receives a third session deriving
`X.T @ X @ w = X.T @ y` from mean-squared error, stating the full-column-rank uniqueness
condition, and treating the pseudoinverse as the minimum-norm rank-deficient solution.
The concepts use the exact target ids `linear-regression-estimator-derivation` and
`ols-rank-identifiability-and-pseudoinverse`.
Six new practices (`C2-p19`–`C2-p24`) bring C2 to exactly 24 problems and distinguish
solving normal equations from blindly inverting a Gram matrix, rank-based uniqueness,
minimum-norm pseudoinverse behavior, and controlled closed-form checks.

### C9 PCA derivation and reusable NumPy implementation

`C9-dimensionality-reduction` receives a fourth session deriving the centered covariance
eigenproblem, proving its SVD connection, and implementing a reusable NumPy
`NumpyPCA` class with `fit`, `transform`, `inverse_transform`, explained variance,
and deterministic component-sign handling.
The concepts use the exact target ids
`pca-centered-covariance-eigenproblem-derivation`, `numpy-pca-class-from-scratch`, and
`pca-black-box-insufficiency`.
Five new practices (`C9-p20`–`C9-p24`) bring C9 to exactly 24 problems and grade the
derivation, fit-state contract, covariance/SVD equivalence, reconstruction, degenerate
eigenspace behavior, and the reason a black-box sklearn call is insufficient.

### F7 kernel validity and convex optimization

Create `F7-kernels-convex-optimization`, owned in the shared-foundation layer, with
prerequisites `F3-matrices`, `F4-multivar-calculus`, `F6-svd-spectral`, and
`C3-gradient-descent`.
It replaces the provisional owner `P015-R1-MATH-KERNEL-OPT`.

The unit owns the seven provisional concepts already named by Plan 015:

- `positive-semidefinite-matrices`;
- `kernel-validity`;
- `convex-sets`;
- `convex-functions`;
- `first-order-optimality`;
- `lagrangians`;
- `optimization-duality`.

Four 80–90 minute sessions cover quadratic-form/eigenvalue PSD tests and Gram kernels;
closure rules and counterexamples; convex sets/functions and first-order optimality; and
constraints, Lagrangians, weak/strong duality intuition, and KKT-style certificate reading.
Strong-duality and KKT claims are restricted to the stated convex/affine setting and the
regularity condition used by the worked example; they are never asserted unconditionally.
The unit contains 20 practices in the standard A/B/C mix and a 45-minute review.
Four 85-minute lessons plus 640 practice minutes and the review total 1,025 minutes
(17.1 hours), inside Plan 015's 14–20 hour estimate.

## Evidence and promotion contract

Every new concept is added atomically to `syllabus.md`, its owning manifest, relevant lesson
and review notebooks, and at least three unit practices.
Each promoted coverage row names primary lesson anchors and primary practices for every
required modality.
Assessment references remain separate and cannot satisfy the three-practice floor.
`scope-check` must derive `covered`; authors do not store a practice shortfall or weaken a
modality to force green.

Statements and solutions are authored in separate sessions.
The blind solution author receives only the final student-facing notebook and declared
contract, not the statement author's outline or expected intermediate values.
Every solution runs top-to-bottom with a fixed seed where randomness exists, explicit
numeric tolerances, no stored outputs, and a final `### Answer check`.

## Scheduling

Plan 016 expands the course rather than compressing the current no-slack schedule.
Manifest lesson/practice/review minutes are recomputed after the notebook content settles,
then `docs/course-structure.md` is regenerated into a prerequisite-valid approximately
eight-hour weekly schedule.
Existing lessons and reviews are never displaced.
The pinned design estimates add 2,300 manifested minutes: F1 +175, C10 +170, F5 +400,
C2 +275, C9 +255, and F7 +1,025.
That produces 14,647 manifested and 14,887 scheduled minutes, which is planned as a
31-week course near eight hours per week rather than hidden inside the current 26 weeks.
The later Plans 017 and 018 extend this same schedule; they do not create separate Round 1
course copies.

## Verification

The implementation plan must include:

- fail-first contract tests for the exact new concept ownership and coverage promotions;
- statement hygiene and manifest/register checks;
- blind-solution execution for every changed or new solution notebook;
- inventory and roadmap regeneration followed by `--check` freshness runs;
- `prereq-check`, `coverage-check`, `scope-check`, tolerance, hygiene, overlap, and PDF gates;
- a four-way plan gate before content work and a four-way content gate before PR;
- full `scripts/ci-local.sh`, post-execution reporting, PR-aware pre-merge guard, and squash
  merge.

No Round 1 neural-training, classical-breadth, Round 2, or new mock-test content is in Plan
016.
