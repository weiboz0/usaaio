# Plan 013 — Audit Remediation (fixes + vocabulary + assessment ceilings)

**Goal:** Close the corrective findings of the 2026-08 four-way audit (sol+Fable ×
syllabus+materials): the float-tolerance contract retrofit, the tranche-1 register
retrofit, five small defect fixes, four new vocabulary ids with their teaching+practice,
and six ceiling-raising items. (Enrichment tranche = plan 014, separate.)

> Cycle pins carried: sol drafts statements/sections, SEPARATE sol sessions blind-solve;
> reconciliation; no regex prose edits — read every sentence after mechanical changes;
> per-unit/per-scope opencode gate dispatch; measured claims beat plausible ones.

## Task 0 — Tolerance guard (tooling; sol; code-reviewed at the gate)

`tools/checks/tolerance.py` + CLI `tolerance-check` (wired into ci step 4): scan all
`units/*/practice/*_solution.ipynb` and `mocktests/*/solutions/*.ipynb` code cells; every
`np.isclose`/`np.allclose` call must state BOTH `atol` and `rtol` explicitly. Escape hatch:
a `# tol-exempt: <reason>` comment on the call line (the recorded C7-p18 WONTFIX gets one).
Exit 0/1/3 contract; pytest coverage incl. the escape.

## Task 1 — A1: the retrofit itself (sol, batched per unit; then orchestrator re-executes)

Script-assisted but VERIFIED per line (no blind regex): for each of the ~382 offending
call sites (fully-bare + atol-only; unit counts recorded in the audit), set the intended
contract: same-pipeline float64 anchors → `atol=<stated or 1e-9>, rtol=0`; deliberately
loose checks (e.g. simulation vs closed form) keep their intent explicit
(`atol=<band>, rtol=0` or a tol-exempt comment with reason). EVERY touched notebook
re-executed; **an assert that FAILS after tightening is a FINDING (possible real drift a
la plan-009), reported not silently widened.** Units: F2, C1, F1, C4, C2, F4, C5, C3, F3,
C7, C8, C6.

## Task 2 — A2-A6 small fixes (orchestrator inline where trivial, sol otherwise)

A2 C8-p11 statement de-corruption (restore `np.allclose`, relocate the gloss after the
sentence). A3 tranche-1 register retrofit (F1/F2/C1, 65 problems): Type/Difficulty/Concepts
headers; reasoning flags on 23 MC + 4 inverted flags fixed (flag means "derivation is
scored", never "work by hand"); zero-points ban clauses on every constrained item (F1
especially); MC options to the exam's `A.` form. A4 F5 ddof section (population vs sample,
np.var default, when each is right) + pitfall entry + fix C9's and C4's back-references.
A5 C8-p04 retag → cosine-similarity (manifest + spec text). A6: add "zero points" to the
~8 incomplete ban clauses (F3-p08/p09, F4-p09/p14/p17, F5-p14, C7-p17 numel, F6-p22
variant); remove C6-p19-solution's stray np.random.seed; C1 `lesson:` total + F1 `review:`
minutes keys; F1/F5 heading case normalized. All touched notebooks re-executed;
hygiene-check after.

## Task 3 — B: vocabulary (syllabus edit + sections + practice; the 100→105 gate precedent)

New ids (syllabus.md concepts + unit teaches lists + manifests):
- `tensor-shape-tracing` → C7 (prereqs in-chain): new lesson-02 subsection (channel/spatial
  arithmetic through kernel/stride/padding/downsampling; the exam's p08-2 register
  generically) + 3 practice problems (1 intro MC normal-form, 1 core constrained trace with
  run-the-model banned except a verification cell, 1 advanced mixed-stride trace).
- `tabular-feature-engineering` → C4: new lesson-02/03 subsection (create/transform/select
  predictors inside the leakage-safe pipeline; interactions; selection on train only) +
  3 problems (core pipeline-with-derived-feature; core select-k-on-train-only; advanced
  leaky-feature postmortem).
- `normal-form-answers` → C10 lesson-01 subsection (why gcd/sign normal forms exist; the
  decode discipline; worked decode table) + 3 problems (all short: decode drills at
  intro/core + one adversarial "which decode is unique" MC). Existing mc-normal-form
  problems across units get this id APPENDED to their concept lists where honest (the
  cross-tag is legal: prereq closure covers C10-ward? NO — C10 is late; append ONLY in
  C10's own problems; earlier units' items stay as-is, the id's ≥3 lives in C10).
- `api-constraint-compliance` → C10 lesson-01 subsection (reading ban lists; pricing;
  workaround-closure habits) + 3 problems (audit-a-submission×2, write-under-ban×1).
NOT taken: the parameter-counting split (B4) — RECORDED DECISION: retag cost across
C6/C7/mocktest manifests + blueprint cluster mapping outweighs tooling visibility; both
skills demonstrably exercised (C6-p04/p11/p12 hand-arithmetic; C7 audits).
Blueprint impact check: new ids need `clusters:` entries (competition-craft ×2 folds to
applied-ml; tensor-shape-tracing → cnn-vision; tabular-feature-engineering → applied-ml);
mocktest r1-001 manifest untouched (no retro-tagging).

## Task 4 — C: ceilings (6 new problems)

C5/perceptron: +1 core (realize a given half-plane from geometry) +1 advanced
(XOR-unrealizability argument — in-closure via decision-boundaries-geometric). C6/torch-
tensors: +1 core (dtype-promotion audit under contract) +1 advanced (from_numpy aliasing
bug hunt). C8/nearest-neighbor-search: +1 advanced (ties + self-exclusion adversarial
contract). C7/convolution: +1 advanced (multi-layer shape trace, nn.functional banned) —
NOTE: doubles as tensor-shape-tracing practice; dual-tag flagged.

## Task 5 — Statements/solutions cycle for Tasks 3-4 content

Sol drafter session(s) write sections+statements (+outlines to gitignored
reference/outlines-013/); SEPARATE sol sessions blind-solve; reconciliation; amended-
statement → re-solve rule; corpus duty (orchestrator): new problems vs exam items (shape-
trace vs p08-2; feature-eng vs p09; decode drills vs p02 register) — fresh data/numbers.

## Task 6 — Verification (NAMED)

Five checks + NEW tolerance-check PASS repo-wide; full ci ALL GREEN (all ~340 solutions,
mocktest, PDFs); accessibility sweeps unchanged-units clean; coverage-check proves the 4
new ids at ≥3.

## Task 7 — Ship

Content gate 4-way (self + codex terra + opus + glm ×2 by scope: retrofit+fixes /
new-content+tooling); blind-solve ≥3 new problems per reviewer incl. ≥1 proof-form;
register-verification duty on the tranche-1 retrofit (spot 10 of the 65). Post-exec
report, TODO, PR, guard, squash-merge.

## Out of scope

Plan 014 (enrichment: synthesis set, clinics, softmax/cross-entropy, bias-variance
callback, covariance/underfitting items). B4 (recorded above). Mock-test edits beyond
none. Watch-list topics.

## Plan Review

(4-way gate verdicts land here.)

## Content Review

(Pre-PR gate findings land here.)
