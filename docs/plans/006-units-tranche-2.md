# Plan 006 — Teaching Units Tranche 2: F4 + F3 + F5 (math spine)

> **For agentic workers:** per-task commits. Dispatch per CLAUDE.md: Fable 5 drafts
> lessons + problem STATEMENTS; GPT-5.6-sol writes solutions BLIND from statements.

**Goal:** Ship `F4-multivar-calculus`, `F3-matrices`, `F5-probability` at the `docs/unit-standards.md` v2 semester-grade bar, passing all checks, with the new independent-solution-author process proving itself.

**Architecture:** identical to plan 005 (manifest-first RED→GREEN; session lessons + overview + review; A/B/C practice sets; same conventions block including title-then-imports, `SEED = 20260804`, answer-check asserts, per-session checkpoint answers; pitfalls/exam-connections/going-deeper satisfied UNIT-WIDE) **plus the model split**:

1. Fable drafters produce: `lessons/`, `lesson.ipynb` overview, `review.ipynb`, all STUDENT practice notebooks, and the manifest. They also write an answers-outline per problem to the SESSION SCRATCHPAD ONLY (never the repo) for reconciliation.
2. A GPT-5.6-sol agent per unit (codex-rescue, `--model gpt-5.6-sol`, write-enabled, scoped to that unit's `practice/*_solution.ipynb`) solves every problem FROM THE STUDENT NOTEBOOK ALONE and writes the solution notebooks incl. `### Answer check` asserts. Ambiguities it hits are reported as findings.
3. Orchestrator reconciles solver answers vs drafter outlines; disagreements are investigated and fixed BEFORE the content gate. Reconciliation results are recorded in this plan.

## Units

**F4-multivar-calculus** (prereqs [F2-vectors]; teaches: partial-derivatives, gradient, multivar-chain-rule, sum-of-squares-gradients, tanh-derivative)
- Sessions: `01-partials-and-the-gradient` (partials as slice-derivatives from Calc AB; gradient as the vector of partials; geometric meaning via F2 vectors; numeric verification by finite differences — F1 closure), `02-chain-rule-and-sums-of-squares` (multivar chain rule built from 1-D chain rule; gradients of component-form sum-of-squares expressions — the exam's canonical form; tanh derivative fully worked in the reasoning-required register).
- 16–20 problems. Constrained-coding tasks = implement gradients component-wise + finite-difference checkers (no autograd anywhere, obviously).

**F3-matrices** (prereqs [F2-vectors]; teaches: matrices-as-linear-maps, matrix-multiplication, rank, invertibility-via-rank, outer-products, matrix-from-action, gram-matrices, linear-independence-span)
- Sessions: `01-matrices-as-maps` (matrix as a machine acting on vectors; reconstructing a matrix FROM its action — the exam's signature pattern, taught generically without copying any specific past problem), `02-multiplication-and-gram-matrices` (row·col by hand → `@` in NumPy; note the exam sometimes BANS `@` — practice both ways; Gram matrix W·Wᵀ as all-pairs dot products), `03-rank-independence-and-outer-products` (linear independence/span operationally; rank as independent-direction count; invertibility-via-rank; outer products as rank-1 building blocks and minimal decompositions).
- 18–22 problems.

**F5-probability** (prereqs [F1-scientific-python]; teaches: random-variables, expectation, variance, independence, variance-of-sums, gaussian-distribution, sampling-simulation, covariance)
- Sessions: `01-random-variables-and-expectation` (RVs as seeded simulations first, then formal E[X]; linearity), `02-variance-and-independence` (variance definition + shortcut; independence; variance-of-sums with the product-variance corollary — the exam's weight-init derivation pattern, taught generically), `03-gaussian-simulation-covariance` (the Gaussian as the bell curve of sums; seeded simulation verifying every algebra claim; covariance defined + computed, pointing forward to C9 by id only).
- 16–20 problems.

Accessibility allowlists: F3 owns "matrix"; F4 may use F2 vector vocabulary; F5 owns "variance/expectation" etc. No SVD/eigen (F6), no ML terms, no regression/gradient-descent (C-track) anywhere.

## Tasks

1. **Manifests first** (orchestrator): three manifests with practice maps (concepts, set A/B/C, difficulty, type per entry — v2 floors: ≥4 MC w/ ≥1 numeric normal-form, ≥6 constrained coding, ≥2 proof, ≥2 integrative multi-part, ≥2 scenario, ≥2 challenge; every concept ≥3 problems; spreads ≈30/45/25). prereq-check PASS + coverage-check RED, commit.
2-4. **Draft F4 / F3 / F5** (3 parallel Fable agents): lessons + student notebooks + review per v2; answers-outline to scratchpad.
5. **Solve** (3 sequential-or-parallel 5.6-sol agents, one per unit): write all `*_solution.ipynb` blind from student notebooks; execute clean; report ambiguity findings.
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

## Content Review

(Pre-PR gate findings land here.)
