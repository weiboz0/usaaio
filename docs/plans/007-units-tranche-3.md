# Plan 007 — Teaching Units Tranche 3: C4 + C2 + C3 (applied + linear models)

> **For agentic workers:** the plan-006 cycle verbatim (per-task commits; Fable drafts
> lessons + statements with outlines to `reference/outlines-007/<unit>.md`; gpt-5.6-sol
> blind-solves per unit; orchestrator reconciles before the gate; amended statements get
> blind re-solves; proof problems carry numeric anchors with claim-by-claim outline
> reconciliation).

**Goal:** Ship `C4-classical-ml-practice`, `C2-linear-models`, `C3-gradient-descent` at the v2 semester-grade bar, plus the filed tooling follow-up: `check_overlap` extended to unit practice.

**Architecture:** identical to plan 006 (manifest-first RED→GREEN; session lessons + overview + review; A/B/C sets with the amended ban-register contract — core set {`@`, `np.matmul`, `np.dot`, `.T`, loops} as minimum plus workaround-closers; ≥2 checkpoints/section; pitfalls/exam-connections/going-deeper unit-wide; conventions per F1–F5 precedent).

## Deps (Task 0)

`uv add scikit-learn pandas` — C4 teaches them (sklearn restricted to what C4's teaches cover: kNN + preprocessing/pipelines/CV; the exam's sklearn-only-kNN rule is taught as exam craft).

## Units

**C4-classical-ml-practice** (prereqs [C1, F1, F2, F5]; teaches: knn, feature-scaling, pandas-basics, csv-data-loading, sklearn-pipelines, cross-validation)
- Sessions: `01-pandas-and-data-loading` (DataFrames, CSV loading, selecting/filtering, to-NumPy bridge — the exam's starter-code idiom, paraphrased), `02-knn-and-scaling` (kNN from first principles with F2 distances THEN sklearn's KNeighborsClassifier; why feature scaling changes neighbors — worked distortion example; standardization via F5 variance), `03-pipelines-and-validation` (train/test discipline recap from C1 → Pipeline(StandardScaler, KNN); cross-validation; choosing k honestly; the exam's my_prediction contract + hidden-test craft, taught generically).
- 18–20 problems. Datasets: seeded generator scripts writing small CSVs to the unit's practice/data/ (committed; tiny), plus sklearn's built-in loaders where natural.
- BANS: no other supervised models (no trees/SVM/logistic — untaught), no "regression" vocabulary yet (C2 not a prereq)... EXCEPT C4's closure genuinely lacks C2: keep all tasks classification-only.

**C2-linear-models** (prereqs [F3, F4, C1]; teaches: linear-regression, mse-loss, l1-regularization, l2-regularization, sparsity)
- Sessions: `01-linear-regression-and-mse` (the model ŷ = Σ X w in component form AND the F3 map view; MSE as the sum-of-squares from F4; evaluating/differentiating for GIVEN parameters — fitting itself deferred to C3, per the syllabus scoping; residual geometry via F2), `02-regularization-and-sparsity` (L2 and L1 penalties added to MSE; gradient/subgradient intuition at the kink; why L1 zeroes coefficients and L2 shrinks — the exam's concept-MC territory; worked normal-form MC in that register).
- 18–20 problems. C2 practice evaluates/differentiates losses, reasons about penalty geometry, computes regularization paths on GIVEN weight sequences — no training loops (C3's job).

**C3-gradient-descent** (prereqs [F4, C2]; teaches: loss-surfaces, gradient-descent, learning-rate, stochastic-gd)
- Sessions: `01-surfaces-and-descent` (loss surfaces as F4 landscapes; the descent step w ← w − η∇L; convergence on quadratic bowls; divergence when η too big — worked oscillation demo), `02-learning-rates-and-stochasticity` (step-size sweeps; descent on the C2 MSE putting the pieces together — THE payoff: fit the linear model end-to-end; mini-batch/stochastic descent as noisy-but-cheap gradients, seeded comparisons full-vs-stochastic).
- 16–18 problems (floors permit 16 only via dual-tagging — target 18).

Accessibility: C4 owns sklearn/pandas vocabulary; C2 owns regression/MSE/regularization; C3 owns descent/learning-rate. NO neural/perceptron/deep vocabulary anywhere (C5's); C4 must not use regression terms; kNN appears in C2/C3 only as "as covered in C4-classical-ml-practice" references if at all.

## Tooling touch (Task 1b — the filed 006 follow-up)

Extend `tools/checks/overlap.py`: scan `units/*/practice/*.ipynb` sources (markdown + code) against the corpus alongside mock manifests, with a boilerplate exemption list (import lines, rng-seeding lines). Loud-skip semantics unchanged. Tests: `test_overlap_scans_unit_practice`, `test_overlap_boilerplate_exempt`. Dispatch: gpt-5.6-sol (implementation coding).

## Tasks

0. Deps (`uv add scikit-learn pandas`), commit.
1. Manifests ×3 (v2 floors: ≥4 MC w/ ≥1 numeric normal-form, ≥6 constrained coding, ≥2 proof, ≥2 integrative, ≥2 scenario, ≥2 challenge; every concept ≥3; ≈30/45/25) → prereq PASS + coverage RED, commit.
1b. Overlap tooling extension (sol agent) + tests green, commit.
2-4. Fable drafters ×3 (parallel): lessons + student statements + review + outlines.
5. sol blind solvers ×3 (parallel, per-unit scope).
6. Reconciliation (+ statement amendments → blind re-solves; record all).
7. Verification phase (NAMED): five checks PASS (overlap now covering units), ci-local ALL GREEN (all solutions incl. tranche 1-2), assert scan, accessibility sweep (closure-aware; C4/C2/C3 allowlists), estimated_minutes present.
8. Ship: content gate (self + codex 5.6-terra + opus + glm; blind-solve ≥3/unit incl ≥1 proof; lesson-vs-output verification duty), post-exec report, TODO tick, PR, guard, squash-merge.

## Out of scope

Units 008-010 (C5+C6 w/ torch, C7+C8, F6+C9+C10), mock test 011, course structure 012.

## Plan Review

(4-way gate verdicts land here; Codex slot on gpt-5.6-sol.)

## Content Review

(Pre-PR gate findings land here.)
