# Plan 006 — Teaching Units Tranche 2: F4 + F3 + F5 (math spine)

> **For agentic workers:** per-task commits. Dispatch per CLAUDE.md: Fable 5 drafts
> lessons + problem STATEMENTS; GPT-5.6-sol writes solutions BLIND from statements.

**Goal:** Ship `F4-multivar-calculus`, `F3-matrices`, `F5-probability` at the `docs/unit-standards.md` v2 semester-grade bar, passing all checks, with the new independent-solution-author process proving itself.

**Architecture:** identical to plan 005 (manifest-first RED→GREEN; session lessons + overview + review; A/B/C practice sets; same conventions block including title-then-imports, `SEED = 20260804`, answer-check asserts, per-session checkpoint answers; pitfalls/exam-connections/going-deeper satisfied UNIT-WIDE) **plus the model split**:

1. Fable drafters produce: `lessons/`, `lesson.ipynb` overview, `review.ipynb`, all STUDENT practice notebooks, and the manifest. They also write an answers-outline per problem to **`reference/outlines-006/<unit>.md`** — inside the repo tree but under the `reference/*` gitignore (never committable; the pre-merge leak guard enforces), durable across sessions, readable by the orchestrator at reconciliation.
2. A GPT-5.6-sol agent per unit (codex-rescue, `--model gpt-5.6-sol`, write-enabled, scoped to that unit's `practice/*_solution.ipynb`) solves every problem FROM THE STUDENT NOTEBOOK ALONE and writes the solution notebooks incl. `### Answer check` asserts. **Assert semantics:** numeric normal-form MCs must assert the RECOMPUTED value AND the normal-form decode, not just the letter (letter-only asserts are tautological); concept MCs may letter-assert, with correctness carried by reconciliation — stated openly. **Proof-problem protocol:** every proof-style problem MUST include a concrete numeric instance whose values the solution's assert cell verifies (the computable anchor); the proof PROSE is reconciled claim-by-claim against the drafter's outline (same claims established, same assumptions invoked, each step sound) — any gap, extra assumption, or divergent claim is a finding; the content gate's blind-solve sample must include ≥1 proof per unit, judged directly by the reviewer (the 005 precedent: opus validated F2-p07's argument). Ambiguities are findings.
3. Orchestrator reconciles solver answers vs drafter outlines; disagreements are investigated and fixed BEFORE the content gate; **a problem whose statement is amended gets a blind RE-solve by the sol agent** (preserving the independent-author property). Reconciliation results are recorded in this plan. **Additional orchestrator duty at reconciliation (corpus-holder role):** structurally compare F3 session-01's matrix-from-action examples and problems against the local `reference/r1-2026/index.yaml` — no structural isomorph with renamed numbers of any specific past sub-part; record the comparison verdict here (external gate reviewers lack the gitignored corpus).

## Units

**F4-multivar-calculus** (prereqs [F2-vectors]; teaches: partial-derivatives, gradient, multivar-chain-rule, sum-of-squares-gradients, tanh-derivative)
- Sessions: `01-partials-and-the-gradient` (partials as slice-derivatives from Calc AB; gradient as the vector of partials; geometric meaning via F2 vectors; numeric verification by finite differences — F1 closure), `02-chain-rule-and-sums-of-squares` (multivar chain rule built from 1-D chain rule; gradients of component-form sum-of-squares expressions — the exam's canonical form; tanh derivative fully worked in the reasoning-required register).
- 18–20 problems (the v2 type floors sum to 18 disjoint; dual-type tagging allowed but must be flagged in the manifest and judged at the gate). Constrained-coding tasks = implement gradients component-wise + finite-difference checkers (no autograd). **Drafting bans:** the word "matrix", the `@` operator, "Jacobian" — component/indexed-sum forms only.

**F3-matrices** (prereqs [F2-vectors]; teaches: matrices-as-linear-maps, matrix-multiplication, rank, invertibility-via-rank, outer-products, matrix-from-action, gram-matrices, linear-independence-span)
- Sessions: `01-matrices-as-maps` (matrix as a machine acting on vectors; reconstructing a matrix FROM its action — the exam's signature pattern, taught generically without copying any specific past problem), `02-multiplication-and-gram-matrices` (row·col by hand → `@` in NumPy; the exam sometimes BANS `@` — practice both registers. **Banned-`@` register, exactly:** each such problem's zero-points clause names its banned identifiers from {`@`, `np.matmul`, `np.dot`, `.T`, loops}; the permitted route is elementwise multiply + broadcasting + axis sums (`(A[:, :, None] * B[None, :, :]).sum(axis=1)` style), mirroring the real exam's ban lists. Gram matrix W·Wᵀ as all-pairs dot products), `03-rank-independence-and-outer-products` (linear independence/span operationally; rank as independent-direction count; invertibility-via-rank; outer products as rank-1 building blocks and minimal decompositions).
- 18–22 problems.

**F5-probability** (prereqs [F1-scientific-python]; teaches: random-variables, expectation, variance, independence, variance-of-sums, gaussian-distribution, sampling-simulation, covariance)
- **Continuous-case fence:** all proofs discrete; continuous results (Gaussian facts, independence of functions of independent RVs) enter as STATED FACTS verified by seeded simulation; no Gaussian integral evaluation anywhere (not AB-evaluable). Avoid "dot product" vocabulary (F2 not a prereq) — use indexed sums.
- Sessions: `01-random-variables-and-expectation` (RVs as seeded simulations first, then formal E[X] in the discrete register; linearity), `02-variance-and-independence` (variance definition + shortcut; independence; variance-of-sums INCLUDING the weighted-sum identity Var[Σwᵢxᵢ] for independent zero-mean factors via the stated product-expectation fact E[XY]=E[X]E[Y] — the exam's initialization-derivation pattern, taught generically — F5 drafter prompt BANS the surface forms "weight"/"init"/"neural" (C5 vocabulary; describe as 'scaled sums of independent factors'); scalar scaling Var[wX]=w²Var[X] included. No new concept id: all within variance-of-sums + independence), `03-gaussian-simulation-covariance` (the Gaussian as the bell curve of sums; seeded simulation verifying every algebra claim; covariance defined + computed, pointing forward to C9 by id only).
- 18–20 problems (same floor arithmetic note as F4).

Accessibility allowlists: F3 owns "matrix"; F4 may use F2 vector vocabulary; F5 owns "variance/expectation" etc. No SVD/eigen (F6), no ML terms, no regression/gradient-descent (C-track) anywhere.

## Tasks

1. **Manifests first** (orchestrator): three manifests with practice maps (concepts, set A/B/C, difficulty, type per entry — v2 floors: ≥4 MC w/ ≥1 numeric normal-form, ≥6 constrained coding, ≥2 proof, ≥2 integrative multi-part, ≥2 scenario, ≥2 challenge; every concept ≥3 problems; spreads ≈30/45/25). prereq-check PASS + coverage-check RED, commit.
2-4. **Draft F4 / F3 / F5** (3 parallel Fable agents): lessons + student notebooks + review per v2 — **conventions block amended for v2: ≥2 checkpoint exercises per section** (005's "1-3" wording is superseded); F5's drafter prompt carries the Continuous-case fence verbatim; answers-outline to `reference/outlines-006/<unit>.md` (gitignored, durable).
5. **Solve** (3 sequential-or-parallel 5.6-sol agents, one per unit): write all `*_solution.ipynb` blind from student notebooks (PARALLEL — no cross-unit state); execute clean; return ambiguity findings as a uniform list: {problem id, ambiguity description, blocking: yes/no, assumption taken}.
6. **Reconcile** (orchestrator): solver vs outline; fix disagreements (statement bugs → Fable agent fixes; solution bugs → sol agent fixes); record all in this plan.
7. **Verification phase (NAMED)** — identical criteria to plan 005 Task 5 (all five checks PASS, ci-local ALL GREEN executing every solution + the permanent assert scan, accessibility sweep with the unit allowlists, estimated_minutes present). Design-§2 clause mapping as recorded in plan 005 (assert-based answer checks; PDFs are mock-test-only; timing budgets in manifests).
8. **Ship** — content gate (4-way: self, codex 5.6-terra, independent Opus, GLM; blind-solve sampling ≥3/unit), post-exec report, TODO tick, ci-local, PR, guard, squash-merge.

## Out of scope

- Other units (007–010), mock tests (011), course structure (012). sklearn/pandas/torch still deferred (arrive with C4/C6).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS
1. `[NOTED]` Blind-solve mechanics for MC: the sol agent derives its own answer and
   asserts ITS letter — divergence from the drafter's intended key is precisely what
   reconciliation (Task 6) detects. Proof-style: solver writes reasoning + numeric
   asserts. Scenario prose: solver writes model answers; reconciliation compares
   substance. Well-defined for all v2 types.
2. `[NOTED]` F5's Gaussian stays at AB level by design: simulation-first, density as
   "the histogram's limiting shape", no continuous E[X] integrals — discrete-first
   ordering carries the formal load. Reviewers asked to probe this.
3. `[NOTED]` F3 matrix-from-action originality line: teach the generic skill; the
   overlap-scan + fidelity duty police specific-problem resemblance, same as all
   exam-register training content.

### Review 2 — [fable] Independent Fable 5, fresh context (2026-08-04)

- **Verdict**: APPROVE WITH NITS → all findings fixed
1. `[FIXED]` Outline durability + MC assert semantics → outlines to gitignored
   `reference/outlines-006/` (leak-guard-protected, session-durable); numeric
   normal-form MCs must assert recomputed value + decode; concept-MC letter-assert
   tautology stated openly with reconciliation carrying correctness.
2. `[FIXED]` F3 structural-overlap enforcement → explicit orchestrator corpus-holder
   duty at reconciliation, verdict recorded in-plan.
3. `[FIXED]` Floors arithmetic → F4/F5 raised to 18-problem minimum; dual-tagging
   policy stated up front.
4. `[FIXED]` F5 continuous fence added (discrete proofs; stated-facts + simulation;
   no Gaussian integrals; no dot-product vocabulary).
5. `[FIXED]` F4 drafting bans ("matrix", `@`, "Jacobian") explicit.
6. `[FIXED]` Amended statements get blind re-solve.

### Review 3 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: APPROVE WITH NITS (verified all 21 teaches ids mapped to sessions; closure
  clean; split-author mechanics sound; verification phase complete vs 005 precedent)
1. `[FIXED]` F5 "weight-init" vocabulary leak risk → drafter-prompt ban on
   weight/init/neural surface forms; pattern renamed in-plan.
2. `[FIXED]` Sol-agent ambiguity findings → uniform format specified.
3. `[FIXED]` (raced) floors already at 18 minimum; outlines already durable.
4. `[FIXED]` Task 5 pinned to parallel.

### Review 4 — [codex] Codex GPT-5.6-sol (2026-08-04)

- **Verdict**: REJECT → all 5 findings fixed → **APPROVE** (verified each fix by line ref)

**GATE RESULT: PASS — 4/4** ([claude-self], [fable], [glm], [codex]); no open blockers.

## Content Review

(Pre-PR gate findings land here.)

## Reconciliation record (Task 6, incremental)

### F4-multivar-calculus (2026-08-04)
Solver (gpt-5.6-sol, blind) vs drafter outline: **18/18 agreement** — every MC letter
(p01 B, p02 B, p03 B, p04 B with value −6 and normal-form 5), every numeric result
(gradients, anchors, w_final ≈ (46.85, 4.51)), both proof anchors. One non-blocking
ambiguity (p18 tied minima at (±3, 0)); solver's row-major argmin assumption matches the
drafter's note. All 18 solutions execute exit 0. No statement amendments needed.

### F5-probability (2026-08-04)
Solver (gpt-5.6-sol, blind) vs drafter outline: **18/18 agreement** (letters B/B/C/E;
all numerics incl. Var[T]=19/4→23, σ_s=1/√C anchor, portfolio 0.8/1.6, covariance
pairing story). Three non-blocking ambiguities (inclusive bounds in p09; probability
encoding in p13; shared-vs-separate draws in p17) — solver assumptions all valid;
p09's inclusive-|z| reading yields 0.732 vs the drafter's rough ≈0.68 note (binomial
discreteness, not a disagreement — the statement's compare-in-one-sentence task stands).
Solver sandbox lacked kernel sockets; ALL 18 solutions re-executed LOCALLY exit 0.
No statement amendments needed.
