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
- Sessions: `01-pandas-and-data-loading` (DataFrames, CSV loading, selecting/filtering, to-NumPy bridge — the exam's starter-code idiom, paraphrased), `02-knn-and-scaling` (kNN from first principles with F2 distances THEN sklearn's KNeighborsClassifier; why feature scaling changes neighbors — worked distortion example; standardization via F5 variance), `03-pipelines-and-validation` (train/test discipline recap from C1 → Pipeline(StandardScaler, KNN); cross-validation; choosing k honestly via held-out evaluation — C1 vocabulary (`train-test-split`, `overfitting`) only; exam-contract and hidden-test PROTOCOL material belongs to C10 (its `prediction-function-contract`/`hidden-test-protocol` ids) — Going Deeper pointer by unit id, no C10 content here).
- 18–20 problems. Datasets: seeded generator scripts writing small CSVs to the unit's practice/data/ (committed; tiny), plus sklearn's built-in loaders where natural.
- BANS: no other supervised models (no trees/SVM/logistic — untaught), no "regression" vocabulary yet (C2 not a prereq)... EXCEPT C4's closure genuinely lacks C2: keep all tasks classification-only.

**C2-linear-models** (prereqs [F3, F4, C1]; teaches: linear-regression, mse-loss, l1-regularization, l2-regularization, sparsity)
- Sessions: `01-linear-regression-and-mse` (the model ŷ = Σ X w in component form AND the F3 map view; MSE as the sum-of-squares from F4; evaluating/differentiating for GIVEN parameters — fitting itself deferred to C3, per the syllabus scoping; residual geometry via F2), `02-regularization-and-sparsity` (L2 and L1 penalties added to MSE; gradient/subgradient intuition at the kink; why L1 zeroes coefficients and L2 shrinks — the exam's concept-MC territory; worked normal-form MC in that register).
- 18–20 problems. **C2 fitting-fence (explicit):** ALLOWED — evaluating/differentiating losses at given weights; penalty geometry; given-weight-sequence paths (ALL path weights are SUPPLIED in the statement — students evaluate and reason, never derive or select weights); and **closed-form 1-D or decoupled minimization by Calc AB calculus** (e.g. minimize (w−a)² + λ|w| by case analysis at the kink — this is the honest device that DEMONSTRATES L1 zeroing rather than asserting it; baseline calculus, not "fitting"). BANNED — iterative updates, training loops, normal equations, matrix inversion, `np.linalg` (C3 owns iteration).

**C3-gradient-descent** (prereqs [F4, C2]; teaches: loss-surfaces, gradient-descent, learning-rate, stochastic-gd)
- Sessions: `01-surfaces-and-descent` (loss surfaces as F4 landscapes; the descent step w ← w − η∇L; convergence on quadratic bowls; divergence when η too big — worked oscillation demo), `02-learning-rates-and-stochasticity` (step-size sweeps; descent on the C2 MSE putting the pieces together — THE payoff: fit the linear model end-to-end; mini-batch/stochastic descent as noisy-but-cheap gradients, seeded comparisons full-vs-stochastic).
- 16–18 problems (floors permit 16 only via dual-tagging — target 18).

**C2/C3 shared-notation pin (both drafter prompts verbatim):** MSE = (1/n)·Σᵢ(ŷᵢ−yᵢ)²; model ŷᵢ = Σₖ X_ik·w_k + b with an EXPLICIT bias symbol b (no augmented-column trick); descent step w ← w − η∇L with symbol η named "learning rate"; symbols w, b, η, n consistently. C3's payoff task must consume C2's exact forms.

Accessibility: C4 owns sklearn/pandas vocabulary; C2 owns regression/MSE/regularization; C3 owns descent/learning-rate. NO neural/perceptron/deep vocabulary anywhere (C5's); C4 must not use regression terms; kNN appears in C2/C3 only as "as covered in C4-classical-ml-practice" references if at all.

## Tooling touch (Task 1b — the filed 006 follow-up)

Extend `tools/checks/overlap.py`: scan `units/*/practice/*.ipynb` sources (markdown + code) against the corpus alongside mock manifests. **Channel spec (gate-refined):** units use the SHINGLE channel ONLY (no tf-idf cosine — topically-similar teaching material makes cosine false-positive-prone; 006's manual scan precedent was shingle-only); line-level boilerplate filtering (import lines, rng/SEED lines) applied BEFORE shingling; unit hits are ERRORS (units cannot be "adapted"); loud-skip semantics unchanged. Boilerplate filtering applies BEFORE shingling for units and before BOTH channels for mock texts. Tests: `test_overlap_scans_unit_practice`, `test_overlap_boilerplate_exempt`, `test_overlap_units_shingle_only`, `test_overlap_loud_skip_preserved` (regression: corpus/tool absent → exit-3 skip with remedy, BEFORE any scanning). Dispatch: gpt-5.6-sol (implementation coding).

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

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS
1. `[NOTED]` C2-without-fitting is the tranche's pedagogical tightrope — the plan's
   devices (evaluate/differentiate at given weights, penalty geometry, given-sequence
   regularization paths) mirror what the shipped C2 syllabus narrative promised;
   reviewers asked to probe for thinness.
2. `[NOTED]` C4's prereqs in-plan ([C1, F1, F2, F5]) verified == syllabus (F5 was added
   at the plan-003 gate for scaling variance).
3. `[NOTED]` C4's committed-small-CSV device is new (prior units generated data inline);
   flagged for reviewer judgment vs the datasets-from-scripts rule — the generator
   scripts ARE committed and the CSVs are small and regenerable.

## Content Review

(Pre-PR gate findings land here.)
