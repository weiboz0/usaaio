# Plan 010 — Teaching Units Tranche 6: F6 + C9 + C10 (curriculum completion)

> **For agentic workers:** the proven 006-009 cycle verbatim (per-task commits; Fable drafts
> lessons + statements, outlines to `reference/outlines-010/<unit>.md` (gitignored); gpt-5.6-sol
> blind-solves per unit; reconciliation before the gate; amended statements → blind re-solve;
> proofs carry numeric anchors + claim-by-claim rubric; ban-register = core set + closers; narration MUST match printed
> output; regex prose edits forbidden — read every sentence after mechanical changes; numpy
> isclose contract = stated atol + rtol=0 for fixed anchors; opencode gate reviews dispatch
> PER-UNIT against staged `.gate10-executed/` copies).

**Goal:** Ship `F6-svd-spectral` (double-length), `C9-dimensionality-reduction`, and
`C10-competition-craft` — **completing all 16 syllabus units.**

## Deps (Task 0)

NONE new. sklearn/pandas/matplotlib already installed (C4); F6/C9 are NumPy-register;
umap is CONCEPT-ONLY (no install — the syllabus id is `umap-concept`). Task 0 collapses into
Task 1.

## Shared notation pin (all three drafter prompts verbatim — the cross-unit-pin lesson)

Eigenpairs written (λ, q) with `S q = λ q`; symmetric spectral form `S = Q Λ Qᵀ`, eigenvalues
sorted DESCENDING. SVD written `W = U Σ Vᵀ` with singular values σ descending (matching
`np.linalg.svd` output order); `np.linalg.svd(W, full_matrices=False)` is the DEFAULT taught call, with
`full_matrices=True` taught alongside it for whole-space spectral work (see bridge below).
The bridge fact (taught in F6-03, consumed by C9), stated in BOTH forms (gate blocker —
thin U cannot span the Gram matrix's null space): for `S = W Wᵀ` with W (n, d), n > d:
(i) THIN form (`full_matrices=False`, U (n, d)): U's columns are the eigenvectors of the d
(at most) NONZERO eigenvalues λᵢ = σᵢ²; the remaining n − d eigenvalues of S are 0 and their
eigenvectors are NOT in thin U. (ii) FULL form (`full_matrices=True`, U (n, n)): Q = U with
λ = σ² zero-padded to length n gives the complete spectral decomposition S = Q Λ Qᵀ.
F6-03 teaches the thin/full distinction explicitly (shape table both ways); the F6-05
capstone's spectral-from-SVD uses the FULL form with zero-padding, verified against eigh
via INVARIANTS, never column-by-column (gate blocker — the zero eigenvalue has multiplicity
n − d = 160, and degenerate eigenspaces differ by arbitrary orthogonal rotations that
sign-fixing cannot reconcile): the pinned comparisons are (i) reconstruction
`‖QΛQᵀ − S‖_F < tol`, (ii) eigen-equation residuals `‖S qᵢ − λᵢ qᵢ‖ < tol` for the top
nonzero pairs, and (iii) the top-k subspace projector `‖Q_k Q_kᵀ − Û_k Û_kᵀ‖_F < tol`.
Sign-fixing (per the pin below) is reserved for comparing INDIVIDUAL eigenvectors with
distinct, well-separated eigenvalues (the seeded matrices are constructed to keep the top
spectrum separated). Frobenius norm `‖A‖_F = sqrt((A*A).sum())`;
`‖W‖_F² = Σσᵢ²` (derived); rank-r truncation error identity `‖W − W_r‖_F² = Σ_{i>r} σᵢ²`
(Eckart–Young optimality STATED as fact, error identity DERIVED for the truncation itself).
C9 consumes C8's convention by name: embedding stack `W` (N, 100), rows = tokens,
unit-normalized, `S = W @ W.T`. NOTE: np.linalg is LEGAL from F6 onward for eigen/SVD calls
(`np.linalg.svd`, `np.linalg.eig`, `np.linalg.eigh`, `np.linalg.norm` where stated; NOTE
`eigh` returns eigenvalues ASCENDING — the pinned idiom is `vals[::-1]`/`vecs[:, ::-1]`
reorder to the descending convention, taught once in F6-02; gate finding). **Eigenvector/
singular-vector SIGN pin (gate finding): u and −u are both valid — individual-vector cross-route
comparisons (distinct, separated eigenvalues only — degenerate blocks use the invariant
comparisons pinned above) either compare absolute values or sign-fix first (largest-|entry|
component made positive), pinned once in F6-02 and reused verbatim** — the
C2/C5/C8 np.linalg bans were per-problem skill-forcing devices, not a curriculum ban — the
EXAM ITSELF scopes this per-problem (P5-4 bans np.linalg for hand-normalization while
P5-11 hints np.linalg.svd), so the flip mirrors the exam's own register; F6 statements say
explicitly which calls are allowed per problem, and F6's lesson 03 states the scoping
sentence once for students.

## Units

**F6-svd-spectral** (foundation, **double length**; prereqs [F3-matrices]; teaches:
eigenvalues-eigenvectors, spectral-decomposition, svd, singular-values, low-rank-approximation,
frobenius-norm)
- FIVE sessions (double-unit structure, two sittings: 01-03 / 04-05):
  `01-eigenvalues-and-eigenvectors` (direction preserved by a map — matrix-from-action recap;
  the 2×2 eigen condition DERIVED FROM F3's OWN VOCABULARY (gate finding — determinants are
  untaught): S q = λ q has a nonzero solution ⟺ (S − λI) is singular ⟺ its rows are linearly
  dependent (F3 linear-independence-span) ⟺ (a−λ)(d−λ) − bc = 0 via the proportionality
  cross-product; the resulting quadratic solved by Calc AB algebra; the expression ad−bc is
  then NAMED "the determinant" in a one-line vocabulary aside (taught-inline device, the
  argsort precedent); `np.linalg.eig`;
  eigenvalue signs/magnitudes as stretch factors; symmetric matrices get real eigenvalues +
  orthogonal eigenvectors — STATED fact, numerically verified),
  `02-spectral-decomposition` (S = Q Λ Qᵀ for symmetric S; reconstruction as Σ λᵢ qᵢqᵢᵀ
  (F3 outer-products); `np.linalg.eigh` for the symmetric case; energy interpretation),
  `03-svd` (any W = U Σ Vᵀ; singular values; the S = WWᵀ bridge DERIVED in component form —
  thin form for the nonzero spectrum, full form (zero-padded λ) for the complete spectral
  decomposition, per the pinned two-form bridge; `np.linalg.svd`; shapes for tall/wide
  matrices; thin-vs-full shape table),
  `04-frobenius-and-low-rank` (‖·‖_F from entries; ‖W‖_F² = Σσᵢ² derived COMPONENT-WISE from
  the SVD expansion W = Σₖ σₖ uₖvₖᵀ — squared entries summed, cross terms killed by the
  orthonormality of the uₖ/vₖ (dot products of unit vectors, F2's register; NO trace — trace
  is untaught in this curriculum, self-review catch); truncated W_r = U[:, :r] Σ_r V[:, :r]ᵀ; the
  error identity; storage arithmetic rN vs N²; Eckart–Young stated),
  `05-synthesis-capstone` (the full chain on a seeded (200, 40) matrix: W → S → SVD →
  spectral-from-SVD → rank-r sweep → error-vs-r curve; worked ‖S‖_F-in-terms-of-σ derivation
  (= sqrt(Σσᵢ⁴), the exam's P5-13 register taught GENERICALLY with the derivation route);
  worked normal-form MC).
- **24 problems** (the double-unit band is 24-30; 24 chosen deliberately to bound this
  three-unit tranche's reconciliation load — gate-reviewed): floors ≥4 MC (≥1 normal-form), ≥6 constrained,
  ≥2 proof (‖W‖_F² = Σσᵢ² via the component/orthonormality route; the rank-r error identity), ≥2 integrative,
  ≥2 scenario, ≥2 challenge (= 18) + 2 drills + 2 constrained + 2 MC. 6 concepts × 3 = 18 ≤ 24:
  NO dual-tags required (flag any used).
- estimated_minutes: lesson ~425 (5 × 85), practice ~560, review 45.
- Accessibility: F3 chain only. NO probability, NO ML vocabulary (foundation track).
  2×2 hand-eigen work stays at quadratic-formula level.

**C9-dimensionality-reduction** (prereqs [F6-svd-spectral, C8-embeddings, F5-probability,
C1-ml-fundamentals]; teaches: pca, truncated-svd-practice, umap-concept,
local-vs-global-structure)
- Sessions: `01-pca` (center the data — mean vector; direction of maximal variance; PCA via
  SVD of the CENTERED data matrix (route pinned: no covariance-eigendecomposition detour —
  σᵢ²/(n−1) ARE the component variances, stated + verified); variance-explained ratios;
  2-D projections plotted; sign-flip ambiguity TAUGHT (u and −u are the same axis — checks
  compare |loadings| or fix signs by convention); NO SKLEARN anywhere in C9 (gate finding:
  C4 is not in C9's prereq chain, so sklearn is outside the closure — verification is by
  numerical self-checks against the SVD route instead)),
  `02-truncated-svd-practice` (C8's W consumed by name: compress the embedding stack;
  rank-r error curves on real GloVe rows (cache header, C8 form — GENSIM_DATA_DIR only, unit
  stays torch-free); choosing r from an error budget; reconstruction quality on similarity
  rows S vs S_r),
  `03-maps-and-structure` (umap-concept AS CONCEPT: neighbor-graph intuition, "local
  neighborhoods preserved, global distances distorted" — stated-fact register with a
  PCA-vs-concept contrast on a seeded CURVED-MANIFOLD dataset (an S-curve-style parametric
  arc built in NumPy — a shape where local neighborhoods genuinely survive projection while
  global distances distort; a plain two-cluster blob would NOT demonstrate the taught
  concept — gate finding); local-vs-global-structure:
  which questions each view answers; reading 2-D maps critically — axes of a nonlinear map
  carry no units; NO umap library anywhere).
- 18 problems: floors = 18 exactly. 4 concepts × 3 = 12 ≤ 18: no dual-tags required.
- Ban registers: PCA problems ban sklearn OUTRIGHT (outside C9's prereq closure — gate
  finding) plus closers; gensim problems use the C8 cache header (torch-free strings).
- estimated_minutes: lesson 250, practice 430, review 45.

**C10-competition-craft** (prereqs [C4-classical-ml-practice]; teaches: notebook-discipline,
hidden-test-protocol, prediction-function-contract, metric-driven-iteration, writeup-quality)
- Sessions: `01-the-contract` (the graded-notebook model: runs top-to-bottom, defines ONE
  prediction function to a stated signature; the hidden-test protocol — you never see X_test;
  contract violations = zero (wrong return type/index/length); leakage traps (fitting scalers
  on all data, peeking at validation); the course's pinned contract device:
  `predict_labels(X_test) -> pd.Series` — FRESH name, never the exam's identifier),
  `02-metric-driven-iteration` (f1-macro from its confusion-matrix pieces (C4's
  accuracy-precision-recall extended to macro averaging — derived + computed); validation
  splits as the only honest signal; iterate: baseline → error analysis → feature change →
  re-validate; overfitting-to-validation warned as stated fact),
  `03-notebook-and-writeup` (notebook-discipline: seed pinning, cell order = execution order,
  no dead cells, deterministic re-run; writeup-quality: the approach/intuition/alternatives
  summary cell — a graded RUBRIC given and practiced; a full worked mini-competition:
  seeded synthetic tabular task end-to-end under the C10 harness).
- **The C10 harness (built by the drafter as unit infrastructure, seeded):** a generation
  script `units/C10-competition-craft/data/make_dataset.py` (SEED = 20260804) producing
  train.csv + a HELD-BACK test split regenerated at grading time by the solution notebooks
  (deterministic — the "hidden" test is hidden from the STUDENT register, not from ci);
  a grader cell pattern computing f1-macro of `predict_labels(X_test)`. kNN-only supervised
  model mirrors the exam's constraint GENERICALLY, enforced per-problem with the ban-register
  contract (gate finding): "any non-kNN supervised estimator scores zero" + named closers
  (LogisticRegression/RandomForest/GradientBoosting/SVC/MLP families, and re-implementing
  them by hand); any preprocessing allowed; sklearn/numpy/pandas/matplotlib imports only.
- 18 problems: floors = 18. 5 concepts × 3 = 15 ≤ 18: no dual-tags required. Scenario/challenge
  problems include contract-violation postmortems (why did this notebook score zero?) and a
  capped mini-iteration log exercise.
- estimated_minutes: lesson 250, practice 440, review 45.

**Orchestrator corpus duty:** at reconciliation, compare — explicit targets — F6-03/04/05 +
C9-02 vs the exam's p05-11..15 SVD arc (the σ⁴ Frobenius derivation and error-curve plot are
the taught patterns — fresh matrices (seeded synthetic (200, 40) in F6; GloVe rows in C9),
fresh deliverable structure, no isomorph of the exact 5-part chain in any single problem);
C10's harness + problems vs p09 (fresh SYNTHETIC dataset — never breast-cancer/medical-themed;
fresh function name predict_labels; same-register constraints are the teachable). Verdict
recorded in this plan.

> **CORPUS VERDICT (orchestrator, 2026-08-06): PASS — no isomorphs.**
> - vs p05-12 (spectral-from-SVD construction): F6 p13 delivers thin/full INVARIANT checks and
>   p14 a cross-route eigenvector comparison on a seeded 5×5 with known separated spectrum —
>   neither reproduces the exam's construct-Q-and-λ deliverable; the bridge itself is lesson
>   content (the sanctioned teachable).
> - vs p05-13 (‖S‖_F = √Σσ⁴ proof): taught as the capstone's WORKED example (generic route);
>   the assessed proofs are DIFFERENT identities (p15: ‖W‖²_F = Σσ²; p16: rank-r error).
> - vs p05-14/15 (Eckart-Young construction + error plot): our register STATES optimality and
>   assesses error computation via the tail identity — F6 p12/p18 deliver error ARRAYS with
>   identity-vs-direct cross-checks; C9 p07/p09 deliver certified compressions and budget→r*
>   DICTS with two-sided certificates, explicitly no plot deliverable; C9 p12's proof derives
>   the error value, never optimality. Fresh matrices throughout (seeded synthetic; fresh
>   10/24/48-word GloVe stacks).
> - C10 vs p09: apiary-telemetry synthetic dataset (never medical), fresh contract name
>   predict_labels, deterministic-regeneration harness; the kNN-only/f1-macro/hidden-test
>   REGISTER is the teachable, structurally re-instantiated.

Shared: A/B/C sets; ≈30/45/25; ≥2 checkpoints/section; pitfalls/exam-connections/going-deeper
unit-wide (F6 → C9 by id; C9 → C10 by id; C10 → mocktests). SEED = 20260804. All-NumPy float64
register (no torch anywhere in this tranche; C9-02's gensim cells use the C8 cache header).
Proof anchors asserted in code. isclose contract: stated atol + rtol=0.

## Tasks

1. Manifests ×3 (prereq PASS + coverage RED), commit. (No Task 0 — no new deps.)
2-4. Fable drafters ×3 (parallel — the shared notation pin makes F6/C9 concurrent-safe;
   C10 independent): lessons + statements + review + outlines (+ C10's data/make_dataset.py).
5-7. sol blind solvers ×3 (parallel, per-unit scope).
8. Reconciliation (+ re-solve rule) + corpus duty. **F6→C9 dependency check: if
   reconciliation amends F6's bridge/notation content, C9's statements are re-checked
   against the shared pin before the gate (gate finding).**
9. Verification phase (NAMED): five checks PASS, ci-local ALL GREEN (background), assert scan
   (atol+rtol=0 contract), accessibility sweep (F6: foundation-track — no ML/probability
   vocabulary; C9: torch-free strings; C10: sklearn-legal), estimated_minutes, C10 harness
   determinism check (two fresh runs of make_dataset.py byte-identical), **C10 leakage sweep:
   student-register notebooks never read/print the held-back split (the generator is
   student-visible; the protocol lives in the register — grep student notebooks for the
   test-split artifacts; gate finding). Harness determinism check ENUMERATES its compared
   outputs: train.csv bytes AND the regenerated held-back split bytes, both runs (gate
   finding).**
10. Ship: content gate (self + codex 5.6-terra + opus + glm PER-UNIT ×3; blind-solve ≥3/unit
   incl ≥1 proof; narration duty on staged .gate10-executed/), post-exec report, TODO tick,
   PR, guard, squash-merge.

**RECONCILIATION — C10 (2026-08-06): 18/18 AGREE.** MC keys B/C/C/D; every anchor matches the
outline exactly (p04 macro 11/15 → 26; p08 best_k=11 @ 0.810348; p11 161/261 < 81/100;
p12 0.60905/0.49739; p13 baseline 0.766582; p14 dead cells [3,6,8]; p15 3/6; p18 vocab + 2/6).
The solver's single flagged ambiguity (p17 iter-3 accepted flag) resolved to the outline's own
intended reading (False — re-sweep selected the incumbent, no state change). The organic
overfitting-to-validation finding (val-selected SIGNAL recipe 0.8199 val vs weaker heldout)
reproduced independently — treated as the designed feature. All 18 solutions re-executed
locally: 18/18 PASS. No amendments; re-solve rule not triggered.

**RECONCILIATION — F6 (2026-08-06): 24/24 AGREE.** MC keys D/C/D/C/B/B; every anchor matches
(p08 6.249336, p12 err_r2 3.438730, p13 padded spectrum = σ² exactly, p14 sign-fix
cross-route 8.7e-16, p15 19.399856 with the component route and no trace, p16 23.707935,
p17 top-frac 0.66068/k90=2, p18 r*=5 per the deliberately-near-threshold design, p20
460-floor → r=4/slack 8, p22 12.568605). All four solver-flagged ambiguities resolved to the
outline's own intended readings — no amendments, no re-solve. All 24 re-executed locally:
24/24 PASS.

**RECONCILIATION — C9 (2026-08-06): 18/18 AGREE. TRANCHE TOTAL 60/60 (project cumulative
281/281, still zero re-solves).** MC keys B/B/A/A; anchors exact (p11 17.7996567/0.50091797,
p12 2.07576657/28.63583422, p09 budget dict {0.20:11, 0.10:15, 0.02:21}, p13 r90=3, p14
spider single-word change @ 0.1100, p17 graph stats 1468/0/2). Both solver ambiguities
resolved to the outline's keyed readings (p16(i) neighbor-map with the original-space-confirm
caveat — the outline's intended best answer; p18's p2-with-caveat). All 18 re-executed
locally: 18/18 PASS. **F6→C9 dependency check (Task 8): PASS trivially — F6's reconciliation
produced zero amendments, so the shared bridge/notation pin is exactly what C9 drafted
against.** No amendments anywhere in the tranche; re-solve rule never triggered.

## Out of scope

011 mock test r1-001 (owns answer-key comparator + Quarto PDF build), 012 course map.
umap/plotly/any new dependency. Training neural nets (C10 is kNN-register per the exam).
F6 formal proofs of the spectral theorem / Eckart–Young optimality (stated facts; the
DERIVED pieces are the norm identities and the λ = σ² bridge).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-05)

- **Verdict**: APPROVE WITH NITS (amendment applied pre-gate)
1. `[FIXED-pre-gate]` The ‖W‖²_F = Σσ² derivation was routed "via trace(WᵀW)" — but trace is
   taught NOWHERE in the curriculum (grep-verified). Rerouted component-wise through the SVD
   expansion + orthonormality (F2/F3 register). Exactly the silently-assumed-concept class the
   gates exist to catch.
2. `[NOTED]` F6's 5-session/24-problem shape is the double-length answer; C9/C10 at 18 with
   floors exactly met; no dual-tags needed anywhere in the tranche (arithmetic verified:
   18≤24, 12≤18, 15≤18).
3. `[NOTED]` C10's "hidden" test is deterministic-regeneration — hidden from the student
   REGISTER, executable by ci; the honesty framing lives in the statement device.

### Review 2 — [fable] Independent Fable 5 (2026-08-05): APPROVE WITH NITS → all resolved
MAJOR 1: determinant untaught — 2×2 eigen route now derived from F3 linear-dependence
(singular ⟺ rows dependent ⟺ cross-product condition), det named in a one-line aside.
MAJOR 2: sklearn outside C9's prereq closure — sklearn REMOVED from C9 entirely (numerical
self-checks replace the cross-check cell). MINOR 3 raced the self-review trace fix (already
component-routed). MINOR 4: eigh-ascending → pinned [::-1] reorder idiom. NIT 5: 24-problem
wording corrected (bottom of the 24-30 double band, deliberate). NIT 6: claim-by-claim rubric
restored to the header contract.

**GATE RESULT: PASS — 4/4** (claude-self AWN pre-empted trace; fable AWN→resolved incl. two
majors; glm AWN→resolved; codex REJECT×3→APPROVE — thin/full bridge + degenerate-eigenspace
invariants, the tranche's hardest catches). Implementation may begin.

### Review 4c — [codex] re-verdict 2 (2026-08-05): REJECT → fixed
Remaining blocker: sign-fixing cannot reconcile the 160-fold-degenerate null-space bases
(arbitrary orthogonal rotations). → Capstone verification re-pinned to INVARIANTS
(reconstruction, eigen-equation residuals, top-k subspace projectors); sign-fixing scoped
to distinct-separated-eigenvalue vectors only; seeded matrices constructed with separated
top spectra. Third re-verdict requested.

### Review 4 — [codex] GPT-5.6-sol (2026-08-05): REJECT → fixed
BLOCKER: thin-SVD U (n, d) cannot supply the Gram matrix's full eigenbasis — bridge rewritten
in two pinned forms (thin = nonzero spectrum only; full_matrices=True + zero-padded λ = the
complete spectral decomposition); F6-03 teaches the distinction, the capstone uses the full
form. MAJORs on det-route and sklearn-gradeability raced the fable round (det-free derivation
already pinned; sklearn already REMOVED from C9 — moot). Task 9 strengthened per its (d/f):
kNN-only ban clause with named closers incl. hand-reimplementation; determinism check
enumerates both compared artifacts. Wording nit raced. Re-verdict requested.

### Review 3 — [glm] GLM 5.2 (2026-08-05): APPROVE WITH NITS → all resolved
S-curve vehicle pinned for umap-concept (two-cluster wouldn't demonstrate local-vs-global);
sign-fixing pin added for all cross-route eigenvector comparisons; np.linalg-flip phrasing
reconciled with C8's exam-register framing (the exam itself scopes per-problem: P5-4 vs
P5-11); F6→C9 reconciliation dependency check added to Task 8; C10 leakage sweep added to
Task 9. Trace nit raced the self-review fix (already component-routed).

## Content Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-06)

- **Verdict**: Approved
- Duties: all 14 lesson/review notebooks executed and staged (.gate10-executed/) — one
  staging-harness cwd artifact identified and corrected (C10 lessons read data/ relatively;
  nbclient needed resources.metadata.path — ci's jupyter execute was never affected);
  narration audit via exhaustive narrated-float-vs-output diffing on C10 (3 apparent misses
  all benign: two hand-computed worked fractions, one hypothetical checkpoint datum) plus
  anchor checks across F6/C9 (capstone r=5, C9 budget r*=17/0.1400, preservation
  0.9322/0.5877) — zero contradictions. Independent recomputes during reconciliation
  covered 9 problems incl. 4 proofs across the three units — all agree. Verification
  battery: five checks PASS, F6/C9/C10 register sweeps clean, 60/60 asserts, harness
  byte-identical on both enumerated artifacts.

### Review 2 — [codex] GPT-5.6-terra (2026-08-06)

- **Verdict**: Changes requested → **Approved** (re-verdict: p18 fix verified, no remaining findings)
- Blind-solve: 9/9 agree across all three units (incl. F6 p13's full-form invariant route,
  C9's budget dict, C10's postmortem).
1. `[FIXED]` [codex] Must Fix: C10 p18's key scored W-A2 = 0 (total 2) against the
   statement's explicit "judge on its own terms — a value is present" instruction. Notable
   failure mode: the drafter's outline AND the blind solver misread the statement
   IDENTICALLY, so reconciliation agreement masked the error — only an independent gate read
   caught it. → Key corrected to W-A2 = 1 / total 3 in definition + assert + prose cells
   (commit a0e8f49); re-executed PASS; outline annotated.

### Review 3 — [glm] GLM 5.2, per-unit F6 (2026-08-06)

- **Verdict**: Approved (3/3 blind-solves incl. the rank-r proof anchor to 1.8e-14; narration
  audit clean across all 5 lessons + review; foundation-register, bridge, invariant-scope,
  legality-line, and manifest checks all clean).
### Review 4 — [glm] GLM 5.2, per-unit C10 (2026-08-06)

- **Verdict**: Approved with suggestions (3/3 blind-solves; all spot-checks pass with
  independent anchor re-execution).
1. `[FIXED]` [glm] N: confusion_matrix onboarding — lesson 02 now carries the C4
   trust-but-test sentence (orientation verified on a hand-checkable example).
2. `[FIXED]` [glm] N: C1-vs-C4 phrasing drift — preamble now says "taught in C1 and
   practiced in C4". Lesson re-executed PASS, staged copy refreshed.

### (glm F6 finding, continued)
1. `[WONTFIX]` [glm] N: generic "dataset" wording in L04/L05 — ordinary English for a table
   of measurements; no ML register invoked, no prereq-closure issue (reviewer marked it
   optional).
