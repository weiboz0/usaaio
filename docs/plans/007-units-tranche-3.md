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
- **Target 20 problems** (6 concepts × ≥3 = 18 pair-minimum leaves zero slack at 18). Datasets: seeded generator scripts (source of truth, committed) writing tiny CSVs to practice/data/ (convenience-committed regenerable artifacts — not opaque blobs), plus sklearn's built-in loaders where natural.
- BANS: no other supervised models (trees/SVM/logistic — untaught); no "regression" vocabulary (C2 not a prereq); all tasks classification-only.

**C2-linear-models** (prereqs [F3, F4, C1]; teaches: linear-regression, mse-loss, l1-regularization, l2-regularization, sparsity)
- Sessions: `01-linear-regression-and-mse` (the model ŷ = Σ X w in component form AND the F3 map view; MSE as the sum-of-squares from F4; evaluating/differentiating for GIVEN parameters — fitting itself deferred to C3, per the syllabus scoping; residual geometry via F2 — reachable TRANSITIVELY through F3, which prereq-check's transitive-closure semantics [plan 004] accept), `02-regularization-and-sparsity` (L2 and L1 penalties added to MSE; gradient/subgradient intuition at the kink; why L1 zeroes coefficients and L2 shrinks — the exam's concept-MC territory; worked normal-form MC in that register).
- 18–20 problems. **C2 fitting-fence (explicit):** ALLOWED — evaluating/differentiating losses at given weights; penalty geometry; given-weight-sequence paths (ALL path weights are SUPPLIED in the statement — students evaluate and reason, never derive or select weights); and **closed-form 1-D or decoupled minimization by Calc AB calculus** (e.g. minimize (w−a)² + λ|w| by case analysis at the kink — this is the honest device that DEMONSTRATES L1 zeroing rather than asserting it; baseline calculus, not "fitting"). BANNED — iterative updates, training loops, normal equations, matrix inversion, `np.linalg` (C3 owns iteration).

**C3-gradient-descent** (prereqs [F4, C2]; teaches: loss-surfaces, gradient-descent, learning-rate, stochastic-gd)
- Sessions: `01-surfaces-and-descent` (loss surfaces as F4 landscapes; the descent step w ← w − η∇L; convergence on quadratic bowls; divergence when η too big — worked oscillation demo), `02-learning-rates-and-stochasticity` (step-size sweeps; descent on the C2 MSE putting the pieces together — THE payoff: fit the linear model end-to-end; mini-batch/stochastic descent as noisy-but-cheap gradients, seeded comparisons full-vs-stochastic).
- 16–18 problems (floors permit 16 only via dual-tagging, which must be flagged in the manifest and judged at the gate per the 006 policy — target 18 to avoid it).

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

### Review 2 — [fable] Independent Fable 5 (2026-08-04): APPROVE WITH NITS
All four concerns fixed in-plan: C2 fitting-fence with the 1-D analytic argmin device
(the honest L1-zeroing demonstration); C4 descoped from C10's ids (held-out evaluation
via C1 vocabulary); C2/C3 shared-notation pin; unit-overlap channel spec
(shingle-only, pre-shingle boilerplate filter, unit hits = errors).

### Review 3 — [codex] GPT-5.6-sol (2026-08-04): REJECT (raced the fable-fix commit)
Blocker (C4/C10 encroachment) already fixed by the fable round. Its two live items
fixed: supplied-weights wording made explicit; `test_overlap_loud_skip_preserved`
regression test + filter-before-both-channels wording added. Re-verdict: **APPROVE**, none remaining.

**GATE RESULT: PASS — 4/4** ([claude-self], [fable], [glm], [codex]); no open blockers.

### Review 4 — [glm] GLM 5.2 (2026-08-04): APPROVE WITH NITS
Fixed: F2-transitive reliance stated for C2 S01; C4 target 20 (coverage slack);
CSV policy stated (convenience-committed regenerable); EXCEPT phrasing cleaned;
C3 dual-tag flag-and-judge policy restated. Noted: .ipynb parsing unification
opportunity passed to the tooling task.

## Content Review

(Pre-PR gate findings land here.)

## Reconciliation record (Task 6, incremental)

### C2-linear-models (2026-08-04)
Solver (gpt-5.6-sol, blind) vs drafter outline: **18/18 agreement** — all letters
(C/B/C/C), the soft-threshold and ridge closed forms with anchors, path zero-counts,
scenario numbers ($4080 saved), the p18 parabola argument. One non-blocking ambiguity:
p04's w₁ indexing — solver assumed zero-based, which IS the drafter's intent (outline
uses row X_i1=(2,0)); statement clarified post-hoc ("zero-based: w[1]"), and since the
solver's stated assumption equals the clarified text, its solution stands as the valid
solve of the amended statement (re-solve rule satisfied by identity). Solver sandbox
lacked kernel sockets; all 18 re-executed LOCALLY exit 0.

### C3-gradient-descent + C4-classical-ml-practice (2026-08-04)
C3 solver vs outline: **18/18 agreement** (all letters A/B/B/C-109; contraction and
expected-batch-gradient proofs with exact anchors; the η=1/3 perpetual-bounce edge case;
divergence traces; schedule floors). C4 solver vs outline: **20/20 agreement** (all
letters B/B/B/D; both load-bearing tie-breaks — best_k=1 and best_k=7 smallest-wins;
the 3–2 vote squeaker; the peek-vs-honest 0.1333 gap; the standardization-does-NOT-flip
challenge). Zero ambiguity findings from either solver. Both sandboxes lacked kernel
sockets; ALL 38 solutions re-executed LOCALLY exit 0. coverage-check now PASSES
repo-wide (56/56 tranche-3 pairs). Tranche reconciliation total: **56/56**.

## Verification record (Task 7, 2026-08-04)

- prereq / coverage / hygiene / blueprint / overlap: all PASS — overlap-scan now
  covering unit practice per the Task 1b extension (nbformat deprecation warning noted,
  cosmetic).
- ci-local ALL GREEN: 177 solution notebooks executed (65+56+56), permanent assert scan
  clean, PENDING plan-011 line present.
- Accessibility sweep: 1 hit — C4's Going Deeper prose used "embedding vectors" (C8
  vocabulary) beside the allowed unit-id pointer → rephrased; re-sweep clean.
- Reconciliation: 56/56 tranche-wide (18+18+20), one statement clarification (C2 p04
  indexing, solver assumption == intent), zero re-solves required.

## Content Review

### Review 1 — [claude-self] inline (2026-08-04)

- **Verdict**: Approved with suggestions
1. Evidence base: verification record + 56/56 reconciliation; the fitting-fence and
   notation-pin were the design risks and both drafters' reports show compliance —
   external reviewers asked to audit both adversarially.
2. `[NOTED]` One accessibility leak (C4 "embedding vectors") caught by my sweep and
   fixed pre-gate; reviewers should hunt siblings.
3. `[NOTED]` The C2 p04 indexing clarification is the tranche's only statement
   amendment; recorded with the identity-re-solve rationale.

### Review 2 — [glm] GLM 5.2 (2026-08-04): **Approved**
6/6 blind solves matched (incl. all three unit proofs); v2 floors + concept coverage
verified; NO C2↔C3 notation drift (MSE 1/n, explicit b, η); datasets regenerated
byte-identical; overlap extension matches spec. Two cosmetic NITs only.

### Review 3 — [codex] GPT-5.6-terra (2026-08-04): Changes requested → fix landed
9/9 blind solves + 3/3 normal-forms matched; fitting-fence scan clean; manifests/tags
verified; lesson spot-checks consistent. BLOCKER: overlap-scan silently dropped corpus
parts with failed pdftotext conversion → `[FIXED]` failures channel + loud warnings +
`test_overlap_partial_pdftotext_failure_warns`; 61 tests green, ruff clean, real-repo
scan PASS. Re-verdict requested.
