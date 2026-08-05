# Plan 011 — Mock Test r1-001 + the two ci capstones

> **For agentic workers:** the proven content cycle adapts to test assembly (per-task
> commits; Fable drafts statements, outlines gitignored; gpt-5.6-sol blind-solves;
> reconciliation before the gate; measured claims beat plausible ones; isclose = stated
> atol + rtol=0; per-unit/per-section gate dispatch for opencode; no regex prose edits).

**Goal:** Ship `mocktests/r1-001` through the deterministic blueprint pipeline AND land the
two tools that turn ci's last stub lines green (answer-key reproduction; Quarto PDF build).

## Task 0 — Tooling (dispatch: codex gpt-5.6-sol per CLAUDE.md; tooling gets code review at the gate)

0a. **Quarto**: user-space install (official tarball → `~/.local/quarto`, symlink on PATH via
    `~/.local/bin`); PDF via the BUNDLED typst engine (`format: typst` — no TeX install).
    Record the version. If the download is blocked, record and fall back to
    `nbconvert --to html` as a TEMPORARY build (HTML, NOT a PDF — recorded honestly) with a loud plan note (decision recorded here:
    quarto+typst is the design-pinned route).
0b. **Answer-key reproduction comparator** (`tools/checks/answerkey.py` + CLI subcommand
    `answerkey-check`): for every final mocktest manifest problem with an `answer_key`,
    verify the solution artifact reproduces it — (i) MC letters/short strings: parse the
    canonical `answer: X` marker from `solutions/answers.md`; (ii) numerics: compare within
    stated tolerance from an `answer_tolerance` optional field (default exact for ints,
    atol=1e-9 rtol=0 for floats); (iii) pointer form `solutions/<file>#<cell-tag>`: execute
    nothing — READ the tagged cell's last `ANSWER = ...` literal (solution execution is
    already ci step 3; the comparator is a static cross-check, keeping it fast and
    order-independent). Exit contract: 0 pass / 1 fail / 3 loud-skip when no final mocktest
    manifests exist. Tests in tests/ (pytest), including a fixture mocktest.
0c. **PDF build wiring** (`scripts/build-pdf.sh` + ci step 5): quarto-render test.md +
    problems/*.ipynb (student register ONLY — solutions never rendered; **`execute: false`
    pinned in the render config — quarto executes notebooks by default, which would both
    slow ci and risk leaking outputs into the student PDF; gate finding**) to
    `mocktests/r1-NNN/build/` (gitignored); ci runs it for every mocktest dir and fails on
    render errors. ci-local.sh lines "PENDING (plan 011)" and "SKIP (plan 011)" replaced by
    real invocations. **Also update docs/mocktest-generation.md's verification map (its
answer-key row still says "PENDING (plan 006)" — stale plan number; gate finding).**

## Task 1 — Instantiate (orchestrator inline)

`uv run usaaio-tools new-mocktest r1-001 --date 2026-08-06`. Zero free choices
(docs/mocktest-generation.md): section points 50/45/90/65/50 = 300; arc rotation index 0 →
clusters [nlp-embeddings, linear-algebra, numpy]; difficulty draw {intro .23, core .45,
advanced .32}; 9 problems; 180 min. Slot specs (one paragraph per gradable sub-part) drafted
in this plan → recorded as `spec:` fields in the manifest. Section shape mirrors the 2026
texture: P1-P2 concept-block MC (8 MC sub-parts), P3-P4 math-computation, P5 the integrative
arc (embeddings → similarity → SVD → low-rank, 12 sub-parts per the slot spec — OUR OWN arc on fresh data,
never the exam's), P6-P8 engineering (numpy/torch-free-mix per clusters), P9 the 50-pt
open-ended notebook task (C10's register: hidden-test protocol, kNN-only, f1-macro,
predict-function contract — FRESH dataset theme, not apiary, not medical).
Manifest committed with `status: draft` → blueprint-check runs loud-draft until the gate.

## Task 2 — Statements (Fable drafters, parallel by section-group)

Three drafters: (A) P1-P4 theory/math statements, (B) P5 arc + P6-P8 engineering notebooks,
(C) P9 notebook task + data generators (seeded, committed scripts, small artifacts only).
Student register: complete runnable starter code; five-option MC; normal-form numerics;
reasoning-required flags; banned-API zero-point clauses; exact identifiers — style_rules
from blueprint.yaml are BINDING. Tested-only-if-taught: every concept id must be taught by
some unit (prereq-check enforces). Answers outline → reference/outlines-011/ (gitignored).

## Task 3 — Solutions (sol blind solvers, parallel; never read outlines)

solutions/ notebooks run top-to-bottom clean (fixed seeds); answers.md carries canonical
`answer: X` markers; every manifest answer_key must be reproduced (Task 0b's comparator is
the machine check).

## Task 4 — Reconciliation + two-direction similarity (orchestrator)

Per-problem reconciliation vs the outline (re-solve rule on amendments). Then BOTH
directions: (1) FIDELITY — structural comparison against reference/analysis.md style notes
+ per-section fidelity verdicts recorded here; (2) NO-DUPLICATION — overlap-scan against
the corpus (provenance tags where adapted) AND a manual isomorph pass against our own 319
unit problems (a mock test must not repeat unit practice either; targets: the P5 arc vs
C8/C9/F6 problems, P9 vs C10's harness problems).

## Task 5 — Verification (NAMED)

ci-local ALL GREEN with the two NEW checks live (answerkey-check real; PDF build real,
rendered artifacts spot-opened); **the draft→final manifest flip happens in Task 6 AFTER
the content gate passes (wording clarified — gate finding), with one final ci run at
final status before the PR**;
tooling pytest suite green; comparator loud-skip path exercised in tests.

## Task 6 — Ship

Content gate 4-way (self + codex 5.6-terra + opus + glm per-section×2 — theory+arc /
engineering+notebook): blind-solve ≥4 sub-parts per reviewer incl ≥1 proof-form and ≥1
programming; FIDELITY duty per docs/content-review-gate.md #7 (per-section verdicts);
tooling code review of Task 0 in the same round. Post-exec report, TODO tick, PR, guard,
squash-merge.

## Out of scope

012 course map. Additional mock tests (r1-002+ come free from the pipeline later).
Round 2 anything. Changing blueprint.yaml (any texture change is its own plan).

## Slot specs (Task 1 detail — drafted here, recorded in the manifest)

**Texture ledger (verified against blueprint invariants):** sub-parts
5+3+2+2+14+4+5+4+1 = **40** ∈ [33, 41] ✓; five-point atoms 30/40 = **0.75** ≥ 0.55 ✓
(P2's 3 + P3's 1 + P4's 1 + P5's 12 + P6-P8's 13); programming points
40(P5 code) + 20 + 25 + 20 + 50 = **155**/300 = 0.517 ∈ [0.45, 0.55] ✓; problem count 9 ✓;
arc sub-parts 14 ∈ [12, 16] ✓; section sums 50/45/90/65/50 = 300 = the anchors ✓.

**Cluster ledger (test-global, all within min/max):** ml-concepts 50 (P1) · calculus 5 (P2a) ·
probability-statistics 10 (P2b-c) · linear-algebra 60 (P3 15 + P5 45) · cnn-vision 15 (P4) ·
nlp-embeddings 15 (P5 first three) · numpy 50 (P5 30 + P6 20) · pytorch 45 (P7 25 + P8 20) ·
applied-ml 50 (P9). Sum 300 ✓.

**Difficulty ledger (point shares):** intro 70 (0.233 ∈ [.15,.30]) · core 135 (0.45 ∈
[.35,.55]) · advanced 95 (0.317 ∈ [.25,.40]) — per-sub-part bands assigned in the manifest.

- **P1** (concept-block, 50 = 5 MC × 10, the pinned 10-point-atom style, opening position):
  supervised-vs-unsupervised task identification; overfitting from a learning-curve
  description; train-test-split leakage scenario; f1-macro vs accuracy on imbalance;
  clustering-concept vs classification. Units C1/C4. All five-option A-E.
- **P2** (math-computation, 15 = 5+5+5): tanh-derivative chain evaluation at a point (F4,
  normal form, 5, calculus); weighted-sum variance setup (F5/C5, 5, prob-stat); the 1/√C
  conclusion on FRESH numbers (5, prob-stat, reasoning required).
- **P3** (math-computation, 15 = 5+10): eigenvalue check of a given pair (5, normal form);
  2×2 eigen by hand via the dependent-rows route (10, reasoning required). F6,
  linear-algebra.
- **P4** (math-computation, 15 = 5+10): receptive-field formula application on a fresh conv
  stack (5, normal form); bottleneck parameter count at a fresh width, no numel (10,
  reasoning required). C7, cnn-vision.
- **P5** (integrative-arc, 90 = 12×5 + 2×15, 14 sub-parts, later parts consume earlier):
  OUR arc on a fresh committed text corpus (seeded generator). Beats (5 pts each unless
  noted): 5.1 tokenize + census (code, nlp) · 5.2 dedup semantics (theory, nlp) · 5.3
  filter + embed via cached GloVe (code, nlp) · 5.4 stack W rows-are-tokens (code, numpy) ·
  5.5 row-normalize, np.linalg banned HERE (code, numpy) · 5.6 cosine range (theory,
  numpy) · **5.7 S = WWᵀ + symmetry/diagonal, 15 (theory, reasoning required, LA;
  provenance: adapted ← r1-2026-p05-6)** · 5.8 SVD of W, np.linalg.svd allowed (code, LA) ·
  5.9 thin-vs-full shapes (theory, LA) · 5.10 spectral-from-SVD, zero-padded λ (code, LA) ·
  **5.11 rank-r error identity derivation, 15 (proof, reasoning required, LA; provenance:
  adapted ← r1-2026-p05-14)** · 5.12 error-vs-r values from the tail identity (code,
  numpy) · 5.13 budget → r* with certificate (code, numpy) · 5.14 storage arithmetic
  (theory, LA). Units C8/F6/C9/F2/F3/F1.
- **P6** (engineering, 20 = 4×5, NumPy): broadcasting normalization; masked argmax
  retrieval; piecewise ReLU-combination function; seeded census — all with ban clauses +
  zero-point penalties, exact snake_case identifiers. F1/C5/C8 registers.
- **P7** (engineering, 25 = 5×5, torch): fresh My_CamelCase module to spec with registered
  frozen params; forward-pass shape contract; parameter count no-numel; resnet50 truncation
  build (cached weights); freezing audit. C6/C7 registers.
- **P8** (engineering, 20 = 4×5, torch): threshold-gate module; two-half-plane region
  detector wiring (fresh geometry); composed inference MLP with manual weights; parameter
  audit. C5/C6 registers (torch side — cluster pytorch).
- **P9** (open-ended-notebook, 50, 1 sub-part): fresh seeded tabular theme (urban tree
  health from street-census features — not apiary, not medical), 600/200 split, kNN-only +
  named closers, f1-macro, predict-function contract, run-clean + summary-cell rubric.
  C10 register. applied-ml.

**Provenance pre-commitment (gate finding):** the arc STRUCTURE is the blueprint's required
rotation texture, not a provenance event; sub-parts are original EXCEPT 5.7 and 5.11, which
mirror specific exam sub-part registers closely enough to carry `provenance: adapted` +
`adapted-from` tags up front. Original share 38/40 = 0.95 ≥ 0.7 ✓. Any reviewer may
escalate additional sub-parts to adapted at the gate.

**Deliverable ownership (gate finding):** `test.md` front matter + manifest `time_budget`
(20/25/55/45/35 = 180, the schema's advisory split) → Task 1 (orchestrator, from the
scaffolder template). `rubric.md` (per-problem partial credit) + `solutions/answers.md` →
Task 3 (solution side). PDF spot-check of test.md + problems → Task 5.

**Comparator binding rule (gate finding):** solution notebooks ASSERT their answer literal
in-cell (`ANSWER = <literal>` followed by an assert comparing ANSWER to the computed value
at the stated tolerance) so ci's solution-execution step binds literal↔computation; the
comparator then statically cross-checks manifest `answer_key` ↔ the tagged cell's literal
(cell metadata tag `answer:<problem-id>`) ↔ answers.md's `- <problem-id>: answer: <X>`
markers. Literal parse rule: plain int/float/str literals only (no np.* wrappers). A stale
literal therefore fails ci step 3 (the in-notebook assert), not just the comparator.

**Gate blind-solve sampling (recorded deviation from duty 1):** full 40-sub-part × 4-reviewer
blind solving is disproportionate; each reviewer blind-solves ≥8 sub-parts spanning all five
sections AND either the complete P5 chain or the complete P9 task. Recorded here as the
explicit sampling rule.

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-06)

- **Verdict**: APPROVE WITH NITS (amendments applied pre-gate)
1. `[FIXED-pre-gate]` P2's 25 points over 3 MC is not divisible — split pinned 10/10/5.
2. `[FIXED-pre-gate]` P5's "~7 sub-parts" contradicted the exam's 5-pt-atom texture —
   re-pinned as 12 sub-parts (9×5 + 3×15), the granularity blueprint-check's texture
   band expects.
3. `[VERIFIED]` Section sums 50/45/90/65/50 = 300 against the anchors; 8 total MC sub-parts
   matches the 2026 anchor; all named concepts spot-checked taught (dependent-rows eigen F6,
   bottleneck C7, GloVe C8, contract register C10).

### Review 2 — [fable] Independent Fable 5 (2026-08-06): REJECT → resolved
BLOCKER (sub-part texture 27 vs min 33; arc 7 vs min 12; atom share unreachable) → slot
specs REBUILT with full ledgers: 40 sub-parts, arc 14, atom share 0.75, concept-block
5×10-pt atoms. MAJORs: cluster ledger added (all floors/ceilings met — pytorch rebalanced
via P8-as-torch; cnn-vision 15 ≤ 20); deliverable ownership assigned (test.md/time_budget →
Task 1; rubric.md/answers.md → Task 3); comparator binding rule added (in-notebook assert
binds literal↔computation; tag + marker conventions pinned). MINORs: blind-solve sampling
recorded as an explicit deviation; provenance pre-commitment for 5.7/5.11 (adapted tags,
original share 0.95); nbconvert-fallback honesty note (HTML, not PDF).

### Review 3 — [glm] GLM 5.2 (2026-08-06): REJECT → resolved
Its texture/atomization/arithmetic majors raced the fable-round rebuild (verified addressed
by the ledgers — programming share 155 ≤ 165 with P5 code capped at 8×5). New fixes:
quarto `execute: false` pin (output-leak + ci-speed); docs/mocktest-generation.md stale
"plan 006" row updated in Task 0c; draft→final flip timing clarified (Task 6, post-gate,
final ci at final status).

## Content Review

(Pre-PR gate findings land here.)
