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
    `nbconvert --to html` as a TEMPORARY build with a loud plan note (decision recorded here:
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
    problems/*.ipynb (student register ONLY — solutions never rendered) to
    `mocktests/r1-NNN/build/` (gitignored); ci runs it for every mocktest dir and fails on
    render errors. ci-local.sh lines "PENDING (plan 011)" and "SKIP (plan 011)" replaced by
    real invocations.

## Task 1 — Instantiate (orchestrator inline)

`uv run usaaio-tools new-mocktest r1-001 --date 2026-08-06`. Zero free choices
(docs/mocktest-generation.md): section points 50/45/90/65/50 = 300; arc rotation index 0 →
clusters [nlp-embeddings, linear-algebra, numpy]; difficulty draw {intro .23, core .45,
advanced .32}; 9 problems; 180 min. Slot specs (one paragraph per gradable sub-part) drafted
in this plan → recorded as `spec:` fields in the manifest. Section shape mirrors the 2026
texture: P1-P2 concept-block MC (8 MC sub-parts), P3-P4 math-computation, P5 the integrative
arc (embeddings → similarity → SVD → low-rank, ~7 sub-parts — OUR OWN arc on fresh data,
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
rendered artifacts spot-opened); status flipped draft→final at the end of the gate;
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

- P1 (concept-block, 25 pts, 5 MC × 5): supervised-vs-unsupervised task identification;
  overfitting from a learning-curve description; train-test-split leakage scenario;
  f1-macro vs accuracy on imbalance; clustering-concept vs classification. Units C1/C4.
- P2 (concept-block, 25 pts, 3 MC): feature-hierarchy depth ordering from described
  activation statistics (C7 register, NO image); requires-grad audit reading (C6);
  cosine-similarity range/meaning (C8/F2). All five-option.
- P3 (math-computation, 20 pts, 2 sub-parts): tanh-derivative chain evaluation at a point
  (F4, normal form); weighted-sum variance with the 1/√C conclusion on FRESH numbers
  (C5/F5 register, reasoning required).
- P4 (math-computation, 25 pts, 2 sub-parts): 2×2 eigen by hand via the dependent-rows
  route (F6, normal form); bottleneck parameter count at a fresh width (C7, no numel,
  reasoning required).
- P5 (integrative-arc, 90 pts, ~7 sub-parts): OUR arc on a fresh committed text corpus
  (seeded generator): tokenize/dedup semantics → embed via cached GloVe → stack W →
  row-normalize (no np.linalg on that sub-part) → S = WWᵀ + one theory sub-part
  (range/symmetry, reasoning) → SVD of W (np.linalg.svd allowed) → spectral-from-SVD with
  the thin/full distinction → rank-r error curve from the tail identity + a budget
  question. Units C8/F6/C9/F2/F3.
- P6 (engineering, 20 pts, 2 sub-parts): NumPy constrained coding — broadcasting
  normalization + masked argmax retrieval with ban clauses (F1/C8 register).
- P7 (engineering, 25 pts, 3 sub-parts): torch inference engineering — fresh DenseLayer-
  style module to spec with registered frozen params; parameter counting no-numel;
  truncation/freezing audit on resnet50 (cached weights; C6/C7 register).
- P8 (engineering, 20 pts, 2 sub-parts): perceptron/region membership build (C5 register,
  NumPy, fresh geometry) + step/ReLU piecewise function construction with bans.
- P9 (open-ended-notebook, 50 pts): fresh seeded tabular theme (pick: urban tree health
  from street-census features — not apiary, not medical), 600/200 split, kNN-only,
  f1-macro, predict-function contract, summary-cell rubric. C10 register verbatim.

## Plan Review

(4-way gate verdicts land here.)

## Content Review

(Pre-PR gate findings land here.)
