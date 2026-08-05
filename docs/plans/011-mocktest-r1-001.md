# Plan 011 — Mock Test r1-001 + the two ci capstones

> **For agentic workers:** the proven content cycle adapts to test assembly (per-task
> commits; gpt-5.6-sol drafts statements (user directive 2026-08-06), outlines gitignored;
> a SEPARATE gpt-5.6-sol session blind-solves;
> reconciliation before the gate; measured claims beat plausible ones; isclose = stated
> atol + rtol=0; per-unit/per-section gate dispatch for opencode; no regex prose edits).

**Goal:** Ship `mocktests/r1-001` through the deterministic blueprint pipeline AND land the
two tools that turn ci's last stub lines green (answer-key reproduction; Quarto PDF build).

## Task 0 — Tooling (dispatch: codex gpt-5.6-sol per CLAUDE.md; tooling gets code review at the gate)

0a. **Quarto**: user-space install (official tarball → `~/.local/quarto`, symlink on PATH via
    `~/.local/bin`); PDF via the BUNDLED typst engine (`format: typst` — no TeX install).
    Pin **quarto 1.6.42 exactly** + verify the tarball against its published sha256 checksum
    file; record both. If the download is blocked, record and fall back to
    `nbconvert --to html` as a TEMPORARY build (HTML, NOT a PDF — recorded honestly; the
    TEMPORARY build does NOT satisfy Task 5's PDF gate — merge blocks until quarto lands) (decision recorded here:
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
    manifests exist (ci-local's existing `|| {{ rc=$?; [[ $rc -eq 3 ]] || exit $rc; }}` pattern
handles the loud-skip under set -e). **Task 0b also extends tools/model.py's manifest schema
with the optional `answer_tolerance` field (schema change + tests), and the numeric
comparison parses the reproduced value from the SAME tagged answer cell's literal — one
parse site, documented in the tool's docstring.** Tests in tests/ (pytest), including a
fixture mocktest.
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
arc (embeddings → similarity → SVD → low-rank, 14 sub-parts per the slot spec — OUR OWN arc on fresh data,
never the exam's), P6-P8 engineering (numpy/torch-free-mix per clusters), P9 the 50-pt
open-ended notebook task (C10's register: hidden-test protocol, kNN-only, f1-macro,
predict-function contract — FRESH dataset theme, not apiary, not medical).
Manifest committed with `status: draft` → blueprint-check runs loud-draft until the gate.

## Task 2 — Statements (gpt-5.6-sol drafters — USER DIRECTIVE 2026-08-06 recorded in
CLAUDE.md dispatch: sol now drafts statements AND lesson content; statements/solutions run
in SEPARATE fresh codex sessions to preserve session-level blind independence — parallel
by section-group)

Three sol drafters: (A) P1-P4 theory/math statements, (B) P5 arc + P6-P8 engineering
notebooks, (C) P9 notebook task + data generators (seeded, committed scripts, small
artifacts only).
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
C8/C9/F6 PROBLEMS — none of which runs the full chain, by plan-010 design — **and explicitly
vs F6's capstone LESSON (the chain appears there as teaching; the mock arc must differ in
data domain (committed text corpus + GloVe vs seeded synthetic matrix), numbers, and
sub-part framing — recorded verdict required)**, P9 vs C10's harness problems).

**RECONCILIATION (2026-08-07): 40/40 AGREE.** P1-P4: 12/12 exact (MC keys C/D/B/E/A + C/D/C;
numerics 775/24, 1/13, {9,−2}, 160, −164). P5-P8: 27/27 (all anchors match — 131,648;
4,074,560/11,275; r*=3; corpus census 311/220). P9: methodological agreement (open task,
different valid recipes; exemplar val 0.7896 → heldout 0.6860 — the overfitting phenomenon
organically reproduced a third time). Solver-flagged gap (no f1→points mapping) closed: the
28 performance points map linearly over [0.55, 0.75] with the exemplar anchoring 19/28;
hard gates zero the problem. answers.md + rubric.md merged from fragments; all 40 answer_key
fields backfilled (p09 as pointer form); manifest flipped FINAL at the end of this task per
the gate ruling.

**FIDELITY VERDICTS (per-section, duty #7):** concept-block PASS (imperative register,
per-part reasoning/coding flags, five options A-E, 10-pt atoms, fresh scenarios);
math-computation PASS (normal-form decode instructions with gcd/sign constraints — the
distinctive USAAIO pattern present); integrative-arc PASS (single narrative journey, later
parts consume earlier variables explicitly, 14 sub-parts of exam-granularity atoms);
engineering PASS (exact snake_case/My_CamelCase identifiers, shape contracts, banned-API
zero-point clauses, complete runnable starters); open-ended-notebook PASS (hidden-test
protocol, single model family, contract function, summary-cell requirement — the 2026
P9 register). Style_rules checklist: all seven satisfied.

**NO-DUPLICATION VERDICT:** overlap-scan vs corpus: clean (0 errors; adapted-tagged
sub-parts warn as designed). Manual isomorph pass vs our 319 unit problems: the P5 arc's
data domain (committed fresh text corpus, 220-token GloVe stack) differs from every unit
problem and from F6's capstone (seeded synthetic (200,40) measurement matrix — different
domain, numbers, and deliverable framing; RECORDED VERDICT: not an isomorph); P7's width
88 / cut children[:6]+layer3[:2] grep-verified absent from units; P8 geometry fresh;
P9's street-tree theme distinct from C10's apiary. PASS both directions.

**PDF pipeline shakedown (recorded):** three real defects found and fixed while turning the
build green — test.md had no body (rendered empty), theory/*.md weren't rendered at all
(build-pdf extended), and quarto's typst path drops LaTeX \[ \]/\( \) delimiters
(statements converted to $-form; math verified present in every rendered PDF via pdftotext).

**VERIFICATION FINDING (recorded in-scope tooling fix):** with `files:` fields populated,
overlap-scan's mock path TF-IDF'd raw statement texts and fired ~10 false-positive ERRORs —
every one at shingles=0 (zero verbatim overlap) — because the blueprint's style_rules
MANDATE the exam's register boilerplate in every statement, and boilerplate dominates
cosine on short texts. The unit path already carries a boilerplate filter for the same
class (plan-004 design); the mock path lacked one. Fix dispatched (sol): mirror the unit
filter with a register-phrase constant citing style_rules; shingle scan stays raw
(verbatim protection unchanged); thresholds unchanged; regression tests. Justification:
this makes a NAMED phase's check meaningful for the register the blueprint itself mandates
— not new scope; the gate's tooling review covers it.

## Task 5 — Verification (NAMED)

ci-local ALL GREEN with the two NEW checks live (answerkey-check real; PDF build real,
rendered artifacts spot-opened); **the draft→final flip happens at the END of Task 4 (post-reconciliation, PRE-gate — gate
blocker: drafts exit-3-skip blueprint/answer-key validation, so ALL GREEN at draft status
never validates the real manifest; the gate must review the FINAL-status artifact with all
checks live)**;
tooling pytest suite green; comparator loud-skip path exercised in tests.

## Task 6 — Ship

Content gate 4-way (self + codex 5.6-terra + opus + glm ×2 grouped as theory+arc /
engineering+notebook — a SCOPE-cap application of the 010 timeout lesson, not a literal
per-section rule; each glm invocation stays inside the budget that failed at 3-unit scope): blind-solve ≥4 sub-parts per reviewer incl ≥1 proof-form and ≥1
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
40 (P5 code) + 20 (P6) + 20 (P7 code beats — p07-3 is theory) + 20 (P8) + 50 (P9) =
**150**/300 = 0.50 ∈ [0.45, 0.55] ✓; problem count 9 ✓;
arc sub-parts 14 ∈ [12, 16] ✓; section sums 50/45/90/65/50 = 300 = the anchors ✓.

**Cluster ledger (test-global, all within min/max; every problem's clusters drawn from its
SECTION's allowed list; cluster follows the row's CONCEPTS — gate rule):** ml-concepts 50
(P1) · calculus-multivar 15 (p02-1 + p04-2 — AT the 15 ceiling, noted) ·
probability-statistics 10 (p02-2/3) · linear-algebra 75 (P3 15 + p04-1 5 + P5 beats
6/7/8/9/10/11/14 = 55; ≤ 80) · nlp-embeddings 15 (p05-1..3) · numpy 40 (P5 beats
4/5/12/13 = 20 + P6 20; ≥ 35) · pytorch 35 (P7 beats 1/2/5 + P8 20; ≥ 30) · cnn-vision 10
(P7 beats 3/4) · applied-ml 50 (P9). Sum 300 ✓ — equals the spec table row-by-row.

**COMPLETE per-sub-part spec table (gate blocker: mocktest-generation.md requires full
specs in the plan BEFORE prose — Task 1 transcribes, zero free choices):**

| id | pts | diff | type / answer_form | cluster | concepts | prov |
|----|-----|------|--------------------|---------|----------|------|
| p01-1 | 10 | intro | theory / MC | ml-concepts | supervised-vs-unsupervised | orig |
| p01-2 | 10 | core | theory / MC | ml-concepts | overfitting | orig |
| p01-3 | 10 | core | theory / MC | ml-concepts | train-test-split | orig |
| p01-4 | 10 | core | theory / MC | ml-concepts | f1-macro, accuracy-precision-recall | orig |
| p01-5 | 10 | intro | theory / MC | ml-concepts | clustering-concept | orig |
| p02-1 | 5 | intro | theory / MC-normal-form | calculus-multivar | tanh-derivative, multivar-chain-rule | **adapted ← r1-2026-p04-1** |
| p02-2 | 5 | core | theory / short-answer | probability-statistics | variance-of-sums, independence | orig |
| p02-3 | 5 | core | theory / proof (reasoning req.) | probability-statistics | weight-init-variance, variance | **adapted ← r1-2026-p07-2** |
| p03-1 | 5 | intro | theory / MC-normal-form | linear-algebra | eigenvalues-eigenvectors | orig |
| p03-2 | 10 | core | theory / proof (reasoning req.) | linear-algebra | eigenvalues-eigenvectors, linear-independence-span | orig |
| p04-1 | 5 | intro | theory / MC-normal-form | linear-algebra | frobenius-norm | orig |
| p04-2 | 10 | core | theory / proof (reasoning req.) | calculus-multivar | sum-of-squares-gradients, partial-derivatives | orig |
| p05-1 | 5 | intro | programming / code | nlp-embeddings | tokenization | orig |
| p05-2 | 5 | intro | theory / short-answer | nlp-embeddings | tokenization | orig |
| p05-3 | 5 | core | programming / code | nlp-embeddings | gensim-usage, word-embeddings | orig |
| p05-4 | 5 | intro | programming / code | numpy | embedding-matrices, numpy-arrays | orig |
| p05-5 | 5 | core | programming / code | numpy | broadcasting, vectorization | orig |
| p05-6 | 5 | core | theory / short-answer | linear-algebra | cosine-similarity, unit-vectors | orig |
| p05-7 | 15 | advanced | theory / proof (reasoning req.) | linear-algebra | similarity-matrices, matrix-multiplication | **adapted ← r1-2026-p05-6** |
| p05-8 | 5 | core | programming / code | linear-algebra | svd | **adapted ← r1-2026-p05-11** |
| p05-9 | 5 | core | theory / short-answer | linear-algebra | svd, singular-values | orig |
| p05-10 | 5 | advanced | programming / code | linear-algebra | spectral-decomposition, svd | orig |
| p05-11 | 15 | advanced | theory / proof (reasoning req.) | linear-algebra | low-rank-approximation, frobenius-norm | **adapted ← r1-2026-p05-14** |
| p05-12 | 5 | core | programming / code | numpy | low-rank-approximation, vectorization | orig |
| p05-13 | 5 | core | programming / code | numpy | low-rank-approximation, aggregation-axis | orig |
| p05-14 | 5 | core | theory / short-answer | linear-algebra | low-rank-approximation | orig |
| p06-1 | 5 | intro | programming / code | numpy | broadcasting | orig |
| p06-2 | 5 | core | programming / code | numpy | nearest-neighbor-search, array-indexing-slicing | orig |
| p06-3 | 5 | core | programming / code | numpy | relu-activation, elementwise-ops | orig |
| p06-4 | 5 | intro | programming / code | numpy | random-seeding, aggregation-axis | orig |
| p07-1 | 5 | core | programming / code | pytorch | nn-module, custom-layers | orig |
| p07-2 | 5 | core | programming / code | pytorch | torch-tensors, manual-weights | orig |
| p07-3 | 5 | advanced | theory / numeric (no numel, reasoning req.) | cnn-vision | bottleneck-blocks, parameter-counting | orig |
| p07-4 | 5 | advanced | programming / code | cnn-vision | model-truncation, resnet-architecture | orig |
| p07-5 | 5 | core | programming / code | pytorch | layer-freezing, requires-grad | orig |
| p08-1 | 5 | intro | programming / code | pytorch | threshold-activation, nn-module | orig |
| p08-2 | 5 | core | programming / code | pytorch | decision-boundaries-geometric, manual-weights | orig |
| p08-3 | 5 | advanced | programming / code | pytorch | mlp-architecture, custom-layers | orig |
| p08-4 | 5 | core | programming / code | pytorch | parameter-counting | orig |
| p09 | 50 | advanced | programming / notebook | applied-ml | prediction-function-contract, hidden-test-protocol, metric-driven-iteration, knn, writeup-quality | orig |

**Difficulty ledger (from the table):** intro 65 (0.217 ∈ [.15,.30]) · core 135 (0.45 ∈
[.35,.55]) · advanced 100 (0.333 ∈ [.25,.40]).

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
- **P4** (math-computation, 15 = 5+10; clusters LA 5 + calculus-multivar 10 per the table):
  Frobenius norm of a small matrix (5, normal form, F6); sum-of-squares gradient derivation
  at a point — ∂/∂wⱼ of a squared-residual sum, evaluated (10, reasoning required, F4).
- **P5** (integrative-arc, 90 = 12×5 + 2×15, 14 sub-parts, later parts consume earlier):
  OUR arc on a fresh committed text corpus (seeded generator). Beats (**clusters/points/difficulty per THE SPEC TABLE above — authoritative; this prose
  names content only**): 5.1 tokenize + census · 5.2 dedup semantics · 5.3 filter + embed
  via cached GloVe · 5.4 stack W rows-are-tokens · 5.5 row-normalize (np.linalg banned
  HERE) · 5.6 cosine range · 5.7 S = WWᵀ + symmetry/diagonal (15, reasoning; adapted ←
  r1-2026-p05-6) · 5.8 SVD of W (np.linalg.svd allowed) · 5.9 thin-vs-full shapes ·
  5.10 spectral-from-SVD, zero-padded λ · 5.11 rank-r error identity derivation (15,
  proof; adapted ← r1-2026-p05-14) · 5.12 error-vs-r from the tail identity · 5.13
  budget → r* with certificate · 5.14 storage arithmetic.
  Units C8/F6/C9/F2/F3/F1.
- **P6** (engineering, 20 = 4×5, NumPy): broadcasting normalization; masked argmax
  retrieval; piecewise ReLU-combination function; seeded census — all with ban clauses +
  zero-point penalties, exact snake_case identifiers. F1/C5/C8 registers.
- **P7** (engineering, 25 = 5×5, clusters pytorch 15 + cnn-vision 10): fresh My_CamelCase
  module to spec with registered frozen params (pytorch); forward-pass shape contract
  (pytorch); bottleneck parameter count at a fresh width, no numel (cnn-vision — moved from
  P4); resnet50 truncation build, cached weights (cnn-vision); freezing audit (pytorch).
  C6/C7 registers.
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
`adapted-from` tags up front. Original share 35/40 = 0.875 ≥ 0.7 ✓ (three more sub-parts escalated to adapted at
implementation when overlap-scan flagged their register mirrors — p02-1 ← p04-1 tanh,
p02-3 ← p07-2 variance, p05-8 ← p05-11 SVD call; exactly the escalation valve the
pre-commitment reserved). Any reviewer may
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

**GATE RESULT: PASS — 4/4** (claude-self AWN pre-empted; fable REJECT→AWN→resolved;
glm REJECT→AWN→resolved; codex REJECT×4→APPROVE across five rounds — the spec table is now
manifest-grade). Implementation may begin.

### Review 9 — [codex] re-verdict 4 (2026-08-06): REJECT → fixed
Surviving duplicate P5 tagged block replaced wholesale; table sole authority; grep-clean.
Fifth verdict: **APPROVE**.

### Review 8 — [codex] re-verdict 3 (2026-08-06): REJECT → fixed
Cluster-follows-concepts enforced: p05-8/p05-14 → linear-algebra; the LA overflow this
caused (85 > 80) rebalanced by making p04-2 a calculus-multivar beat (sum-of-squares
gradient derivation, F4) — final ledger LA 75, numpy 40, calc 15 (at ceiling, noted).
Programming share corrected to 150 (p07-3 is theory). P5 prose bullets stripped of inline
cluster tags — the spec table is authoritative. Fourth re-verdict requested.

### Review 7 — [codex] re-verdict 2 (2026-08-06): REJECT → fixed
Live blocker: the Task-1 deferral contradicted mocktest-generation.md's specs-before-prose
rule → the COMPLETE 40-row per-sub-part spec table now lives in the plan (points/difficulty/
type/answer-form/cluster/canonical-concepts/provenance per row; Task 1 transcribes with
zero free choices). Cluster honesty: 5.6 retagged linear-algebra (cosine is F2/LA family),
5.8 tagged numpy on the exam's own p05-11 precedent — per-beat sums now equal the ledger
exactly (LA 75, numpy 50, margins restored). Difficulty ledger recomputed from the table
(65/135/100). Quarto pinned 1.6.42 exactly + published sha256. Its other specifics raced
prior fixes. Third re-verdict requested.

### Review 6 — [fable] re-verdict (2026-08-06): APPROVE WITH NITS → resolved
Independent re-derivation of all ledgers confirms; WONTFIX on the arc texture ACCEPTED
(blueprint-mandated rotation + recorded-verdict differentiation). Nit 1 raced the 5.14
retag; nit 2 (Task 1 said 12 vs the spec's 14) and nit 3 (canonical id calculus-multivar)
fixed.

### Review 5 — [glm] re-verdict (2026-08-06): APPROVE WITH NITS → resolved
All ledgers verified arithmetically in-range. NIT: per-beat P5 tags summed numpy 25/LA 50
vs the ledger's 30/45 (LA landing exactly at the 80 ceiling) → beat 5.14 retagged numpy
(float-counting register), restoring the ledger with margin (LA 75, numpy 50).

### Review 4 — [codex] GPT-5.6-sol (2026-08-06): REJECT → resolved
Blocker (live): P4's cnn-vision cluster violated math-computation's allowed-cluster list —
P4 rebuilt as linear-algebra (Frobenius + outer-product reconstruction), bottleneck count
moved to P7 (engineering allows cnn-vision); cluster ledger rebalanced (LA 75, pytorch 35,
cnn 10 — all in range). Blocker (stale): its 32-sub-part count predates the 40-sub-part
rebuild; the residue (per-sub-part manifest completeness) addressed via the Task-1
completion rule. Blocker 3 → **WONTFIX with reasoning**: the arc chain is the BLUEPRINT'S
required rotation texture and the exam's own shape (fidelity duty); plan-010's pin governed
UNIT problems, none of which runs the chain; Task 4 now explicitly compares the arc against
F6's capstone lesson with a recorded-verdict requirement. Major 4: draft→final flip moved
to end of Task 4 (pre-gate) so the gate reviews the final-status artifact with all checks
live. Major 5: answer_tolerance schema extension + single parse site + exit-3 pattern
specified. Major 7: glm grouping reworded as the scope-cap application it is. Minor 6:
quarto version+sha256 pin; fallback explicitly cannot satisfy the PDF gate. Re-verdict
requested.

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

**GATE RESULT: PASS — 4/4** (claude-self Approved; codex CR→Approved incl. the provenance
precedent ruling; glm ×2 both AWS-resolved; opus CR→CR→Approved-with-suggestions across
three rounds — 40/40 roster-wide blind-solve agreement, ~30 findings resolved, two live
comparator legs proven by corruption test). All [OPEN] items resolved.

### Review 2 — [codex] GPT-5.6-terra (2026-08-07)

- **Verdict**: Changes requested → **Approved** (re-verdict: precedent rationale accepted,
  40/40 markers verified under the universal leg, warnings-only drift detector confirmed;
  no remaining issues)
- Blind-solve: 19/19 match (the full P5 chain + samples across all sections).
1. `[WONTFIX-with-reasoning + FIXED-in-part]` [codex] Must Fix (provenance — more adapted
   tags on the P5 chain and P7/P8): partially RELITIGATES the plan gate's arc-texture ruling
   (fable ACCEPTED at re-verdict; codex APPROVED the plan carrying it): the arc journey is
   the blueprint's rotation-mandated texture and the engineering patterns are the exam
   REGISTER taught by units C5-C7 — register-instantiation with fresh data/geometry/numbers
   is what a mock test IS; per-sub-part tags for structural kinship would also break the
   0.7 original-share rule codex itself notes. FIXED-in-part: the kinship is now
   acknowledged HONESTLY at the right level — generation_parameters.arc_precedent +
   engineering_register_precedent entries record the structural/register lineage explicitly.
   Cross-reviewer note: glm's parallel review argues two EXISTING tags overstate lineage —
   the per-sub-part tag bar sits where the plan put it.
2. `[FIXED]` [codex] Must Fix (real tooling bug): answerkey-check skipped the marker leg for
   non-numeric keys — MC letters were never verified. → Universal marker leg + cell leg for
   notebook-backed problems (theory sub-parts have no cell — documented); tests added.
3. `[FIXED]` [codex] Should Fix: file-level semantic drift detection restored as a
   WARNING-only per-file-pair cosine at a higher threshold (never affects exit code) —
   keeps the granularity split while retaining paraphrase visibility.

### Review 3 — [glm] GLM 5.2, theory+arc (2026-08-07)

- **Verdict**: Approved with suggestions (6/6 blind-solves match incl. two proofs; fidelity
  PASS on all three in-scope sections with the section-anchor mirroring verified).
1. `[FIXED]` [glm] Register-change annotations: p02-1/p05-7/p05-11's adapted tags now carry
   register notes in their manifest spec fields (numeric-MC-from-proof; deepened-to-proof ×2).
2. `[FIXED]` [glm] p05-9 grader note added to rubric (full-SVD sigma stays (100,) — graders
   must not expect (220,)).

### Review 4 — [glm] GLM 5.2, engineering+notebook+tooling (2026-08-07)

- **Verdict**: Approved with suggestions (5/5 blind-solves incl. both P9 f1 values to 16
  digits; P9 methodology-honesty audit PASS; fidelity/tooling/leakage clean).
1. `[FIXED-by-precedent]` [glm] p08-2/3 provenance → covered by the
   generation_parameters.engineering_register_precedent entry recorded this round (the
   documented-rationale option the reviewer offered).
2. `[FIXED-in-tooling-round]` [glm] answerkey cell-leg coverage for prose-string keys →
   the universal-marker-leg fix in flight; the binding chain for notebook-backed answers is
   closed at ci execution by the in-cell asserts (documented in the tool).
3. `[FIXED]` [glm] P9 hidden-test honesty convention → DECISION RECORDED here: the held-back
   split is hidden from the STUDENT REGISTER by protocol (the C10-taught device), not by
   technical secrecy — the repo is public and the generator seeded by design (determinism is
   what makes grading reproducible); a real administration would distribute only the
   rendered problem package (build/ PDFs + problems/), which contains no generator flag
   documentation. 4. `[FIXED]` [glm] all 10 r1-001 notebooks nbformat-normalized.

### Review 5 — [opus] Independent Opus (2026-08-07)

- **Verdict**: Changes requested → **Approved with suggestions** (final confirmation at
  79055e6: all 14 p05 prompt bodies byte-identical to the student copy, rubric arithmetic
  verified, plan record complete; 2 cosmetic nits — trailing newline + instructor metadata
  on the 3 mirrored grader cells — fixed post-verdict)
- Blind-solve: 40/40 agree (the complete P5 arc + every section + all five proofs + an
  independent P9 campaign); executed the full battery itself incl. a corruption test of the
  comparator (now fails on both legs).
1. `[FIXED]` [opus] MF: four tautological answer cells in p05_solution → real computational
   binds (shape asserts; σ⁴-tail vs direct Frobenius to 1e-12 for r=1..4; empirical range;
   census facts). 2. `[FIXED]` MF: 23 quoted YAML numerics silently disabled the comparator's
   cell leg (demonstrated by corruption) → bare numerics, prose to spec/invariant lines.
3. `[FIXED]` MF: build-pdf unbound-variable crash on theory-less dirs → array-length guard.
4. `[FIXED]` MF: rubric/answers self-contradiction on the P9 mapping → stale text replaced.
5. `[FIXED]` SF: P9 band re-anchored (floor 0.68 > starter 0.674 → starter 0; exemplar 2;
   CV-recipe 9; 0.78+ full — second-round refinement after the 0.67 floor left the starter
   1 point). 6. `[FIXED]` SF: p01-1 tagged adapted ← r1-2026-p01-1 (share 0.817).
7. `[FIXED]` SF: overlap summary-stream (matching granularity — every tagged adaptation now
   surfaces) + all-hits reporting. 8/12. `[FIXED]` SF: student notebooks stripped of
   difficulty/concepts metadata; headers + totals normalized. 9. `[FIXED]` SF: p05-3
   filter made required-and-inspectable (mirrored into the solution copy after the
   re-verdict caught the one-sided edit). 10. `[FIXED]` SF: time_budget 15/25/65/40/35 +
   warm-cache instruction. 11. `[FIXED]` SF: protocol-equal methodology rubric.
13-16. `[FIXED]` NtH: p08-3 giveaway removed; fragments deleted; p05-7/11 prompts in
   $-math (mirrored both copies); p09 hermetic subprocess grading (tree clean after
   execution). Re-verdict's minors: floor arithmetic + stale --with-test citation `[FIXED]`.

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-07)

- **Verdict**: Approved
- Duties across Tasks 4-5 + this review: 40/40 reconciliation with per-anchor verification;
  independent recomputes incl. p02-2 (775/24 exact) and p04-2 (−164 — my first shortcut used
  the wrong residual convention and disagreed; recomputing from the statement's own
  definition confirmed the key, a useful reminder that the statement text is the contract);
  fidelity + no-duplication verdicts recorded with evidence; all five solution notebooks +
  answerkey-check + PDF build executed locally; ci-local ALL GREEN with zero stubs;
  leakage sweeps clean; the three PDF-shakedown fixes and two overlap-tool commits verified
  by behavior (scan PASS at 0 errors with honest adapted warnings, 70/70 tests).
