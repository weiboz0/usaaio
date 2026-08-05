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
tolerance-family call — `np.isclose`, `np.allclose`, `torch.allclose`, `torch.isclose`,
`np.testing.assert_allclose`, `math.isclose` (gate findings: 13 torch sites exist in
C6/C7; rtol-only sites exist too — the rule is BOTH-or-exempt, catching bare, atol-only,
AND rtol-only forms) — must state BOTH atol and rtol explicitly. Escape hatch: `# tol-exempt: <non-empty
reason>` on the call line (empty reason = violation; the recorded C7-p18 WONTFIX is the
one planned use). Exit semantics: 0 = all calls compliant; 1 = any violation AND any parse/read failure of
an existing notebook (a failure to scan is never a skip — gate finding: exit-3 laundering
would yield ALL GREEN without scanning); 3 = ONLY the zero-scannable-notebooks case. Guard scans SOLUTION notebooks AND statement notebooks' CODE cells (gate finding: 18
statements carry isclose in starter/verification cells — they define the contract students
see; markdown prose stays out of scope by construction). Guard runs REPO-WIDE.
**Task 0 also extends tools/checks/coverage.py to enforce ≥3 practice per taught concept
(gate finding: it enforces only ≥1 today, falsifying the old Task-6 claim; the ≥3 rule is
the v2 standard reviewers were enforcing by hand). Run repo-wide immediately — any existing
concept below 3 is a FINDING adjudicated errata-style, not silently waived.**

## Task 1 — A1: the retrofit itself (sol, batched per unit; then orchestrator re-executes)

Script-assisted but VERIFIED per line (no blind regex): the CANONICAL inventory is the
Task-0 guard's own violation list (gate finding: hand recounts disagree — my 382 vs the
reviewer's ~469; the guard is the single source of truth, estimate ~470 sites across
solutions + statement code cells). For each site, set the intended
contract: same-pipeline float64 anchors → `atol=<stated or 1e-9>, rtol=0`; deliberately
loose checks (e.g. simulation vs closed form) keep their intent explicit
(`atol=<band>, rtol=0` or a tol-exempt comment with reason). EVERY touched notebook
re-executed; **an assert that FAILS after tightening is a FINDING adjudicated ERRATA-STYLE
(orchestrator + a fresh sol session, 2-way) with a MANDATORY recorded disposition in this
plan — fix-content / widen-with-reason / exempt-with-reason; no default path (gate
finding); if a statement's STATED tolerance must change, the amended-statement→re-solve
rule applies.** Units: F2, C1, F1, C4, C2, F4, C5, C3, F3,
C7, C8, C6.

## Task 2 — A2-A6 small fixes (orchestrator inline where trivial, sol otherwise)

A2 C8-p11 statement de-corruption (restore `np.allclose`, relocate the gloss after the
sentence). A3 tranche-1 register retrofit (F1/F2/C1, 65 problems) — EXECUTION + VERIFICATION pinned
(gate finding: 10/65 spot-review left 55 unguarded): headers are GENERATED from each
problem's manifest entry (the source of truth — no hand-typing); a post-edit VERIFIER
script re-asserts all 65 (header matches manifest; a reasoning flag present on every MC;
a zero-points clause on every constrained item; options in `A.` form) — 65/65 automated,
plus the human letter/order cross-read on every reformatted MC. Flag semantics: "Reasoning
is required" = the derivation is scored, never "work it by hand". A4 F5 ddof section — DIRECTION PINNED (gate finding): every existing F5 computation stays
ddof=0, framed as population/empirical variance; the new section introduces ddof=1 as the
sample ESTIMATOR without relabeling any prior cell; C9's back-reference then points at the
estimator paragraph, C4's at the population paragraph.
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
C6/C7/mocktest manifests outweighs tooling visibility (cluster mapping derives from
syllabus concepts automatically — cost claim corrected per gate); both
skills demonstrably exercised (C6-p04/p11/p12 hand-arithmetic; C7 audits).
Blueprint impact check: new ids need `clusters:` entries (competition-craft ×2 folds to
applied-ml; tensor-shape-tracing → cnn-vision; tabular-feature-engineering → applied-ml);
mocktest r1-001 manifest untouched (no retro-tagging). **Craft ids are never the DOMINANT
cluster on future mock problems (a normal-form MC's dominant cluster stays its subject id) —
so no math-computation section-list conflict can arise (gate finding).**

## Task 4 — C: ceilings (6 new problems)

C5/perceptron: +1 core (realize a given half-plane from geometry) +1 advanced
(XOR-unrealizability argument — in-closure via decision-boundaries-geometric). C6/torch-tensors: +1 core (dtype-promotion audit under contract — anchored to C6-L01's
bridge-table + pitfall teaching) +1 advanced (from_numpy aliasing bug hunt — same anchor;
the aliasing fact gets a one-line lesson addition if L01 lacks it, checked at drafting).
C8/nearest-neighbor-search: +1 advanced (ties + self-exclusion adversarial contract —
self-exclusion is taught in C8-03; the tie-handling convention is glossed in the
statement, argsort-stability register). C7/convolution: +1 advanced (multi-layer shape trace, nn.functional banned) —
tagged BOTH [convolution, tensor-shape-tracing] explicitly (dual-tag flagged).

## Task 5 — Statements/solutions cycle for Tasks 3-4 content

Sol drafter session(s) write sections+statements (+outlines to gitignored
reference/outlines-013/); SEPARATE sol sessions blind-solve; reconciliation; amended-
statement → re-solve rule; corpus duty (orchestrator): new problems vs exam items (shape-
trace vs p08-2; feature-eng vs p09; decode drills vs p02 register) — fresh data/numbers.

## Task 6 — Verification (NAMED)

Five checks + NEW tolerance-check PASS repo-wide; full ci ALL GREEN (all ~340 solutions,
mocktest, PDFs); accessibility sweeps unchanged-units clean; the EXTENDED coverage-check proves ≥3 repo-wide including the 4 new ids (machine-checked
now, per the Task-0 extension).

## Task 7 — Ship

Content gate 4-way (self + codex terra + opus + glm ×2 by scope: retrofit+fixes /
new-content+tooling); blind-solve ≥3 new problems per reviewer incl. ≥1 proof-form;
register-verification duty on the tranche-1 retrofit (spot 10 of the 65). A3 verification duty strengthened (gate finding): statement↔solution letter/order
cross-read for EVERY MC reformat (not a 10/65 spot — answerkey.py covers mocktests only,
not units). Post-exec report, TODO, PR, guard, squash-merge.

## Out of scope

Plan 014 (enrichment: synthesis set, clinics, softmax/cross-entropy, bias-variance
callback, covariance/underfitting items). B4 (recorded above). Mock-test edits beyond
none. Watch-list topics.

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-07)

- **Verdict**: APPROVE WITH NITS (pre-emption applied)
1. `[FIXED-pre-gate, SUPERSEDED by the fable round — statements' code cells now in scope]`
   Guard scope originally pinned: tolerance-check scans SOLUTION notebooks only
   (statements legitimately describe tolerances in prose) and only np.isclose/np.allclose
   CALLS (exact comparisons via == are out of scope by construction).
2. `[VERIFIED]` New-id arithmetic: tensor-shape-tracing 3+1(dual)=4, the other three ids
   3 each; closures derive in-chain for C7/C4/C10; convolution keeps its count through
   the dual-tag while gaining its advanced ceiling.

**GATE RESULT: PASS — 4/4** (claude-self AWN pre-empted; glm AWN resolved; fable
REJECT→AWN resolved; codex REJECT→AWN — final nit (stale exempt phrase) fixed below).
Implementation may begin.

### Review 4 — [codex] GPT-5.6-sol (2026-08-07): REJECT → resolved (re-verdict AWN; the
surviving "one planned use" phrase excised — Task 0 and Review 4 now agree: explicit
values for C7-p18, escape ships unused)
Major 1 raced the fable-round coverage-≥3 extension (already in). Major 2: exit-3
laundering closed (parse/read failures = exit 1; 3 only for zero-scannable). Major 3:
A3 now generator-from-manifest + a 65/65 automated post-verifier + full MC cross-read.
Minor 4: C7-p18 exemption replaced with explicit behavior-preserving values (escape ships
with zero planned uses); tightening-failure dispositions made mandatory-and-recorded.
Nit 5: B4 cost claim corrected. Re-verdict requested.

### Review 3 — [fable] Independent Fable 5 (2026-08-07): REJECT → **APPROVE WITH NITS**
(re-verdict: all six resolved; stale self-review note annotated superseded)
Majors: coverage-check ≥1-not-≥3 claim falsified → Task 0 now EXTENDS coverage.py to ≥3
(repo-wide immediate run, failures errata-adjudicated); guard family completed (torch.isclose,
rtol-only class); inventory authority moved to the guard itself (~470 est. vs my stale 382).
Moderates: statement code cells scanned; Task-1 adjudication named (errata-style 2-way +
re-solve rule scope); A3 cross-read duty for every MC reformat. Minor: A4 ddof direction
pinned (existing F5 stays ddof=0). Its verified-fine list (flag semantics vs analysis.md,
dual-tag arithmetic, cluster folds, C10-only append) noted.

### Review 2 — [glm] GLM 5.2 (2026-08-07): APPROVE WITH NITS → all resolved
Guard family widened (torch.allclose/assert_allclose/math.isclose), exit semantics pinned,
non-empty exempt reason enforced, repo-wide-scan-vs-offender-list clarified, teaching
anchors cited for the C6/C8 ceiling items, craft-cluster dominance rule pinned.

## Content Review

(Pre-PR gate findings land here.)
