# Design 018 — Round 1 Classical Model Breadth

## Objective

Close the last five acknowledged Round 1 knowledge-point gaps as one prerequisite-closed model
system rather than five disconnected API demonstrations.
Students must be able to derive and train logistic regression, reason from margins to linear and
kernel support-vector machines, construct and regularize decision trees, distinguish bagging from
boosting, implement Lloyd's k-means algorithm, and choose among these families using their
assumptions rather than leaderboard folklore.

The tranche is complete only when all Round 1 knowledge points are checker-derived `covered`, the
planned Round 1 placeholder is replaced by a shipped unit, the schedule contains the new time
before the mock, and every statement/solution pair passes fresh execution and the four-way content
gate.

## Considered approaches

### Append each model to its nearest existing unit

Logistic regression is mathematically adjacent to C2, SVM consumes F7, and trees, ensembles, and
k-means fit the applied surface of C4.
That mapping is useful as a prerequisite graph, but distributing delivery across those three units
would make the comparison boundary implicit and would push C4 far beyond its three-session,
23-practice shape.
It would also obscure the shared fit/predict/evaluate lifecycle and repeat model-selection
scaffolding in several places.
This approach is rejected.

### Teach only sklearn estimators in C4

One applied lesson could fit `LogisticRegression`, `SVC`, `DecisionTreeClassifier`,
`RandomForestClassifier`, and `KMeans` quickly.
That would satisfy neither the official theory surface nor the repository's implementation and
model-training modalities.
It would leave sigmoid/log-loss gradients, margin and hinge reasoning, tree split construction,
ensemble mechanics, and Lloyd updates unowned.
This approach is rejected.

### Create one double-length C12 unit with explicit prerequisite handoffs

This is the selected design.
`C12-classical-models` follows C1, C2, C3, C4, and F7 and treats the five families as a coherent
progression:

1. probabilistic linear classification;
2. margin-based linear classification;
3. kernelized margin classification;
4. recursive partition models;
5. variance-reducing and bias-reducing ensembles;
6. centroid-based unsupervised learning and cross-family comparison.

The unit derives binary cross-entropy from scratch, then reuses C2/C3's linear-model and
optimization machinery, F7's kernel/duality foundation, and C4's pipeline/cross-validation
discipline without importing any undeclared C11 concept.
It gives every family a first-principles implementation or derivation, an actual fitted model, and
a comparison boundary.

## Curriculum placement

Create `C12-classical-models` in the Round 1 core track with prerequisites:

- `C1-ml-fundamentals` for supervised/unsupervised task framing and bias/variance;
- `C2-linear-models` for affine scores and loss functions;
- `C3-gradient-descent` for iterative optimization;
- `C4-classical-ml-practice` for sklearn pipelines and cross-validation;
- `F7-kernels-convex-optimization` for valid kernels, constrained optimization, and duality.

The explicit prerequisites are retained even where the graph is transitively redundant because
each names a distinct intellectual handoff.

C12 owns exactly these ten concepts:

- `logistic-regression`;
- `svm`;
- `margin-and-hinge-loss`;
- `decision-trees`;
- `tree-split-criteria`;
- `ensemble-learning`;
- `bagging-and-boosting`;
- `k-means`;
- `lloyd-algorithm`;
- `classical-model-comparison`.

## Six-session teaching spine

### Session 1 — Logistic regression as a trained linear classifier

Start from the affine score already taught in C2, derive odds, log-odds, the sigmoid map, and
binary cross-entropy directly from binary labels and predicted probabilities.
Derive the stable mean loss and gradient `X.T @ (p - y) / N`, train with deterministic gradient
descent, interpret the `0.5` decision threshold, and compare a NumPy implementation with sklearn.
The lesson distinguishes probability calibration from classification accuracy and treats perfect
separation as an optimization warning rather than an algebraic curiosity.

### Session 2 — Linear SVM, margins, hinge loss, and soft constraints

Define functional and geometric margin with labels in `{-1,+1}`, identify support vectors, and
derive the hard-margin constraints.
Move to the soft-margin primal and hinge loss, explain the role of `C`, and implement a vectorized
hinge objective plus a valid subgradient step.
The lesson uses small two-dimensional data so students can audit the separating hyperplane,
margin width, violations, and parameter movement directly.
It introduces the first explicit model-comparison axes by contrasting logistic probability and
calibration workflows with margin-based decisions; later sessions extend the same framework.

### Session 3 — Dual intuition and kernel SVM training

Reuse F7's Lagrangian sign convention, complementary slackness, and valid-kernel proofs to explain
why only support vectors contribute to the decision function.
Teach linear, polynomial, and RBF kernels, the interaction of `C` and `gamma`, feature scaling, and
the fitted `SVC` surface.
Students audit support-vector identities and compare a linear SVM with kernel SVM on seeded data;
they do not implement a general quadratic-programming solver.

### Session 4 — Decision trees from impurity to recursive prediction

Define Gini impurity and entropy, weighted child impurity, information gain, deterministic
tie-breaking, recursive splitting, leaf prediction, stopping rules, depth/min-sample controls, and
cost-complexity pruning intuition.
Build a small depth-limited classifier from scratch and compare it with
`DecisionTreeClassifier`.
The lesson makes axis-aligned geometry, scale insensitivity, and high-variance behavior explicit.

### Session 5 — Ensembles: voting, bagging, random forests, and boosting

Begin with majority/soft voting, then derive how bootstrap aggregation reduces variance and how
random feature subsets decorrelate trees.
Contrast that parallel construction with sequential boosting, including one exact AdaBoost weight
update and the weak-learner coefficient.
Train bagging/random-forest and boosting estimators, connect behavior to C1's bias/variance
trade-off, and state when probability averaging, voting, and additive scores differ.

### Session 6 — Lloyd's k-means and classical-model comparison

Define the within-cluster sum-of-squares objective, assignment and centroid-update steps, monotone
objective descent, convergence to a local rather than global optimum, initialization sensitivity,
`k-means++`, empty-cluster policy, scaling, and inertia.
Implement Lloyd's algorithm with deterministic tie-breaking and compare with sklearn `KMeans`.
Close with a scored comparison matrix spanning supervision, objective, geometry, scaling,
probability output, interpretability, nonlinear capacity, and validation method for every C12
family plus the already-shipped kNN and linear regression baselines.

## Knowledge-point closure

Every row retains exactly one destination, `C12-classical-models`.
The canonical evidence may reuse prerequisite concepts, but each new shipped concept is taught in
C12 and every modality receives direct C12 evidence.

| Knowledge point | `shipped_concepts` additions | Required C12 evidence |
|---|---|---|
| logistic-regression | logistic-regression | theory, implementation, model training |
| support-vector-machine | svm, margin-and-hinge-loss | theory, implementation, model training |
| decision-trees | decision-trees, tree-split-criteria | theory, implementation, model training |
| ensemble-learning | ensemble-learning, bagging-and-boosting | theory, implementation, model training |
| k-means-clustering | k-means, lloyd-algorithm | theory, implementation, model training |

`classical-model-comparison` is a unit-level synthesis concept and does not create a sixth
official knowledge-point row.

Removing `P015-R1-CLASSICAL-BREADTH` leaves no missing or partial Round 1 knowledge point.
The Round 2 capstone prerequisite that names the placeholder is retargeted to shipped
`C12-classical-models` in the same canonical-map change.

## Practice and timing contract

C12 is double-length with exactly 30 practices and six 90-minute sessions.
The practices comprise four five-option MC problems, one numeric normal-form MC problem, eight
constrained-coding tasks, four proof/derivations, four integrative arcs, four scenarios, and five
challenges.
Difficulty is exactly 9 intro, 14 core, and 7 advanced.
Every one of the ten taught concepts appears in at least three distinct statements, and every
official family has at least three direct model-training practices.

Practice minutes are explicit per problem:

- five MC at 20 minutes = 100;
- eight constrained-coding tasks at 55 minutes = 440;
- four proofs/derivations at 45 minutes = 180;
- four integrative arcs at 65 minutes = 260;
- four scenarios at 45 minutes = 180;
- five challenges at 50 minutes = 250.

The practice total is 1,410 minutes.
With 540 lesson minutes and a 60-minute review, the unit total is 2,010 minutes = 33.5 hours,
inside Plan 015's 32–48-hour range and within the shared six-session/30-practice double-length
ceiling.

The corpus moves from 18 to 19 units, 139 to 149 concepts, 407 to 437 unit practices, 63 to 69
lesson sessions, 99 to 107 lesson/review/overview notebooks, and 913 to 981 unit notebooks.
Manifested time moves from 16,625 to 18,635 minutes and scheduled time from 16,865 to 18,875
minutes, including the unchanged 180-minute mock and 60-minute debrief.

## Practice map

| Ids | Type / minutes | Primary contract |
|---|---|---|
| p01–p04 | five-option MC / 20 each | logistic, SVM, tree, and ensemble fundamentals |
| p05 | numeric normal-form MC / 20 | one Lloyd step and its reduced objective |
| p06–p13 | constrained coding / 55 each | stable sigmoid/loss, logistic training, hinge/subgradient, kernel SVC, split search, recursive tree, ensemble fit, Lloyd fit |
| p14–p17 | proof/derivation / 45 each | logistic gradient, margin/hinge/dual chain, impurity reduction, Lloyd monotonicity |
| p18–p21 | integrative / 65 each | logistic-vs-SVM, tree-to-ensemble, k-means diagnostics, full model benchmark |
| p22–p25 | scenario / 45 each | scaling/calibration, pruning/overfit, ensemble choice, clustering validity |
| p26–p30 | challenge / 50 each | separation audit, support-vector audit, tree construction, two-round AdaBoost, robust k-means |

Each coding or training answer check pins fixed probes, shape/dtype contracts, independent numeric
references, parameter or objective movement, explicit `atol`/`rtol`, and deterministic seeds.
No answer check accepts a self-consistent implementation as its own reference.

## Practice-before-instruction contract

C12's manifest records an optional `concept_sessions` mapping from each owned concept to the
first lesson session that teaches it, an `after_session` value for every practice, and `minutes`
for every practice.
The model/manifest validator checks that the mapping covers exactly `concepts_taught` and refers to
valid session numbers; it also requires each `after_session` value to be at least the latest
session implied by that practice's owned concept tags.
Every C12 schedule practice allocation lists exact `problem_ids`.
The schedule checker requires those lists to partition the manifest practices exactly once,
requires allocation minutes to equal the listed problems' minute sum, and rejects any listed
problem whose `after_session` has not already appeared earlier in flattened allocation order.
This explicit per-problem binding handles subtopics such as kernel SVMs that intentionally remain
inside the broader `svm` concept while being taught one session later.
This provides a generic, stronger successor to C11's handwritten pacing invariant rather than
relying on a handwritten C12 week list.

## Schedule extension

Keep Semester 1 unchanged at 16 weeks / 7,915 minutes.
Semester 2 extends from 19 to 24 weeks and from 8,950 to 10,960 minutes.
The total course extends from 35 to 40 weeks and 18,875 scheduled minutes.

C12 sessions occupy Weeks 34–39, one session per week.
All five prerequisites complete before the first C12 session.
Existing C10 instruction continues to cover regular Weeks 32–34, so every Week 1–39 retains one
to three lesson sessions.
The mock and debrief move together from Week 35 to final Week 40; C12's remaining practice and
review precede the mock in Week 40, and the review remains C12's final unit allocation.

The final schedule must preserve these machine-checked invariants:

- every week totals 450–500 minutes;
- Weeks 1–39 have one to three lesson sessions;
- Week 40 is the sole final-assessment exception;
- consecutive numbered sessions are chronological and no more than two weeks apart;
- prerequisites complete before dependent first instruction;
- every unit review is its final unit allocation;
- practice never exceeds concept-unlocked capacity where a manifest supplies
  `concept_sessions` and per-problem minutes;
- mock and debrief are the final two course allocations.

Weeks 34–40 require at least 3,150 minutes at the lower weekly bound.
Their two baseline weeks contribute 985 minutes and C12 adds 2,010, so the theoretical transfer
minimum is 155 minutes; moving the mock/debrief within that seven-week window does not change this
arithmetic.
The implementation instead transfers exactly 185 minutes from Weeks 17–33, producing 3,180
minutes in Weeks 34–40 and 7,780 in Weeks 17–33.
This leaves 30 minutes of late-window and 130 minutes of early-window slack rather than relying on
the knife-edge minimum, and does not assume that all 315 arithmetic surplus minutes are reachable
through prerequisite- and review-valid forward moves.
The reachability witness releases 115 minutes directly from Weeks 29–33, whose C7/C9/C10 windows
remain open, and propagates the remaining 70 minutes through the overlapping open-unit chain
F6/C6 → F7 → C11 → C9 before moving C9/C10 work into the late window.
Week 34 starts at the 500-minute ceiling and therefore must displace at least 90 minutes when C12
Session 1 arrives; Week 35 falls to 335 minutes after moving the assessment and adding Session 2,
so it must receive at least 115 minutes of unlocked practice.
The final allocation-level schedule, rather than this aggregate certificate, must prove every
weekly and per-problem ordering constraint.

The schedule checker, CLI help, and course-structure renderer must stop hard-coding Week 35.
It derives the unique final-assessment week from the schedule, requires that week to be the final
week, applies the lesson-session exception only there, and the renderer updates every owned week,
semester, milestone, and first-instruction region.

## Evidence and roadmap transition

For each of the five rows, Plan 018 records exact lesson anchors, at least one honest practice in
every required modality and at least three distinct qualifying practices overall, disposition
`keep`, empty deficits, and destination `C12-classical-models`.
The audit and roadmap are regenerated from the canonical map.
The Round 1 acknowledged gap set becomes empty; only Round 2 warnings remain.

`P015-R1-CLASSICAL-BREADTH` is removed from `planned_units` only after all five rows are
checker-derived covered.
The Round 2 capstone prerequisite is retargeted to `C12-classical-models`, preventing a dangling
planned-unit edge.

## Source and authorship boundary

All 30 statements are original.
Authors may use the committed derived reference analysis for register guidance but may not read or
copy raw past papers, verbatim past-problem text, student data, secrets, or ignored local
artifacts.
Statement and solution authors run in separate fresh sessions.
The blind solution author sees final student statements but never statement-author outlines or
draft answers.

Student notebooks contain no solutions or stored outputs.
Solutions use seed `20260804` where randomness is present, declare explicit tolerances, execute
top to bottom, and end with `### Answer check`.
No dataset download, network call, opaque model artifact, TensorFlow dependency, or GPU is used.

## Verification design

Fail-first tests pin the baseline/delta counts, exact C12 shape, concept/session ownership, all 30
problem contracts, target transition, schedule extension, prerequisite order, minutes, and empty
Round 1 gap boundary before content exists.

A permanent classical-model mutation runner copies five real C12 solution notebooks, applies one
exactly-once corruption per family, and requires the real final answer checks to reject:

- a wrong logistic mean-gradient factor in p07;
- a wrong signed-margin/hinge branch in p08;
- a maximum-impurity tree split in p10;
- a missing AdaBoost weight update in p29;
- a non-centroid Lloyd update in p13.

The runner fails closed when a target matches zero or multiple cells or a mutant executes
successfully.

The named verification phase executes all 30 solutions and all eight teaching/review/overview
notebooks in fresh Jupyter kernels, runs both register modes, kills all five mutations, regenerates
curriculum and schedule evidence, and finishes with `scripts/ci-local.sh`.
All four content reviewers solve all 30 statements blind before opening solutions.

## Out of scope

- Neural models, attention, transformers, NLP, advanced vision, generative models, and GPU
  workflows remain Round 2 or already-shipped prerequisites.
- General quadratic-programming solvers, full CART regression, XGBoost/LightGBM internals,
  density-based clustering, hierarchical clustering, mixture models, and statistical inference
  are not required for the five official gaps.
- Student's t-test and importance sampling remain optional, non-required candidates.
- The plan does not add or rewrite a mock test; it moves the existing `r1-001` gate later.
- The plan does not weaken unit standards, weekly schedule bands, coverage floors, or prerequisite
  closure to fit the new unit.
