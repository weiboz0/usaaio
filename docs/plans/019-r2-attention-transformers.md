# Plan 019 — Book 2 Attention and Transformer Mechanics

## Goal

Implement the Book 2 foundation from Design 019 and ship `B2-019-attention-transformers`.
The plan establishes the two-book data and verification boundary, adds the independently scheduled Book 2 route, and closes all seven prerequisite Round 2 attention and Transformer knowledge points with prerequisite-closed, CPU-executable teaching material.

## Branch and baseline

- Branch: `feature/plan-019-attention-transformers`.
- Base: `9c57116bd648534b20833d5e421c9256b85322fd`, the squash merge of Design 019 / PR #21.
- Baseline: 19 Round 1 units, 437 unit practice problems, one `r1-001` mock, 40 frozen Round 1 weeks, and no Book 2 manifests, schedule, or assessment artifacts.
- Baseline verification: `scripts/ci-local.sh` passed on the Design 019 branch: 612 tests, 437 unit solutions, 8 mock solutions, 107 lesson/review/overview notebooks, answer-key/register/coverage/schedule checks, PDF build, and `pre-merge-guard --pr`.
- Baseline Round 2 gaps: the 30 missing or partial `round-2-extension` rows named in `docs/designs/019-r2-book-architecture.md`; this plan closes exactly the first seven attention/Transformer-foundation rows.

## Scope

### Book 2 contract migration

Add canonical Book 2 fields without changing Book 1 ownership or its 40-week schedule.

- Extend `tools.model.Unit` and the parsed syllabus record with `book`, `layer`, `round`, and `concept_prerequisites`.
  `Unit.prereqs` remains the unit-ID DAG; `concept_prerequisites` is a separate, explicit concept-ID dependency list.
- Extend `UnitManifest` and its parser with the matching `book`, `layer`, `round`, `track`, `concept_prerequisites`, `bridge_diagnostic`, `coverage_claims`, and per-task `compute` inventory; B2-019 declares `layer: round-2-extension` and `track: extension`.
  The bridge diagnostic declares its own `minutes: 30` and local path, so it is schedule-reconcilable without pretending to be a taught or owned lesson concept.
  Existing Book 1 syllabus rows and manifests receive the backward-compatible values `book: 1`, `round: 1`, `layer: round-1-core` or `shared-foundation`, and CPU task defaults; they may not make a Round 2 coverage claim.
- Add `B2-019-attention-transformers` to `syllabus.md` as a Book 2, Round 2 extension unit with unit prerequisites `[C6-pytorch, C7-cnn-transfer, C8-embeddings, C11-neural-training]` and concept prerequisites `[softmax, matrix-multiplication, broadcasting, variance, torch-tensors, nn-module, torch-optimizers, autograd-training]`.
- Promote the following Book 2-owned concepts before any Book 2 manifest references them:
  `matrix-transpose`, `query-key-value-attention`, `scaled-dot-product-attention`, `attention-mask`, `causal-self-attention`, `multi-head-attention`, `sinusoidal-positional-encoding`, `attention-complexity`, `transformer-residual-layernorm`, `position-wise-feed-forward`, and `transformer-block`.
- Atomically replace all three legacy planned-unit rows (`P015-R2-TRANSFORMERS-NLP`, `P015-R2-VISION-GEN`, and `P015-R2-CAPSTONE`) with the six Design 019 Book 2 delivery rows, preserving all 30 Round 2 targets and moving their destinations to `B2-019` through `B2-024`, except the deliberately partial `nlp-word-embeddings` bridge retained at `C8-embeddings` until Plan 020.
  Only the seven rows delivered here change to `coverage: covered`; their evidence is newly authored and their `destination` is `B2-019-attention-transformers`.

### Enforceable layer boundary

Add a fail-closed `layer-boundary-check` to the local suite.
It must reject a Book 1 artifact claiming a Round 2 knowledge point, a Book 2 manifest that teaches a non-syllabus or non-Book-2-owned concept, a mismatch between syllabus/manifest unit or concept prerequisite edges, an undeclared per-task compute policy or seed, and a coverage claim that fails to name newly taught evidence concepts or the coverage map's complete required modality set.
`evidence_concepts` must be a nonempty subset of `concepts_taught`.

The check also validates the Book 2 dependency order: a Book 2 coverage claim's `first_session` must be later than every in-unit Round 2 knowledge-point dependency, and an upstream Book 2 unit must already occur earlier in the Design 019 DAG.
It does not grant the Plan 020 embedding bridge early: `bridge_completion` stays unsupported until Plan 020 adds the only permitted partial-row rule.

### Book 2 schedule and rendering

Create `curriculum/book2-schedule.yaml` and a separate parser/validator/renderer.
It has `starts_after_global_week: 40`, `total_book_weeks: 6`, local `book_week: 1..6`, and exact `global_week: 41..46`; it never mutates `curriculum/course-schedule.yaml` or the Round 1 renderer.
Its required terminal metadata is `final_assessment: {kind: future-r2-mock, status: planned, after_book_week: 6}`; the parser rejects an absent, unknown, or final-week-violating marker but does not require an R2 mock before Plan 024 introduces one.
Whenever a later Book 2 plan extends `total_book_weeks`, its `after_book_week` must be updated to equal that new terminal local week; a permanent mutation rejects a stale value.
The Book 2 allocation vocabulary adds `bridge-diagnostic` alongside lesson/practice/review, and the B2-019 schedule reconciles its 1,660 minutes exactly: a 30-minute Book 1 bridge diagnostic, five 90-minute lessons, 1,120 practice minutes, and a 60-minute review.
The Book 2 landing/architecture document renders the Book 1 and Book 2 paths separately and labels every Book 2 entry `Round 2 extension`.

| Book week | Global week | Exact allocation |
|---:|---:|---|
| 1 | 41 | bridge diagnostic 30; Session 1 90; practice chunk 1, 135 minutes: p01, p02, p06, p13 |
| 2 | 42 | Session 2 90; practice chunk 2, 185 minutes: p03, p04, p07, p08, p14 |
| 3 | 43 | Session 3 90; practice chunk 3, 330 minutes: p05, p09, p10, p15, p16, p21, p23 |
| 4 | 44 | Session 4 90; practice chunk 4, 235 minutes: p11, p17, p18, p22 |
| 5 | 45 | Session 5 90; practice chunk 5, 235 minutes: p12, p19, p20, p24 |
| 6 | 46 | review 60; final-assessment-planned terminal marker |

### B2-019 unit

Create `units/B2-019-attention-transformers/` with an overview, a Book 1 bridge diagnostic, five lessons, 24 student practice notebooks, 24 separate solution notebooks, a review notebook, a manifest, and a seeded local data-generation script.
Every student notebook has no solution text or executed output; every solution executes fresh top-to-bottom and ends in `### Answer check` assertions.
All tasks use `compute.policy: cpu`, fixed seed `20260808`, and a local solution path; Plan 019 has no GPU, hosted inference, pretrained-weight, or external-download dependency.

| Session | File | Concept and required evidence surface |
|---:|---|---|
| 0 | `lessons/00-book1-bridge.ipynb` | diagnostic only: softmax, matrix products, broadcasting, PyTorch shape/autograd vocabulary; links to Book 1 and does not reteach or own these concepts |
| 1 | `lessons/01-query-key-value-and-scaled-dot-product.ipynb` | teach `matrix-transpose` for attention, then Q/K/V roles, `QK^T / sqrt(d_k)`, row-softmax, weighted values, numerical stability, hand derivation and NumPy implementation |
| 2 | `lessons/02-self-attention-and-masks.ipynb` | sequence self-attention shapes and padding/causal masks before softmax |
| 3 | `lessons/03-multi-head-position-and-cost.ipynb` | why permutation-equivariance needs position, sinusoidal encodings, projection/head split/concat/output projection, exact shape contracts, `O(n^2 d + n d^2)` time and `O(n^2)` score-memory derivation |
| 4 | `lessons/04-attention-module-and-tiny-training.ipynb` | tested PyTorch attention module, causal next-token synthetic task, optimizer/training trace, masks and scaling as answer-affecting contracts |
| 5 | `lessons/05-transformer-blocks-and-architecture.ipynb` | pre-norm residual block, position-wise feed-forward network, encoder/decoder attention roles, stacked-block architecture and shape/mask audit |

The unit owns exactly the eleven concepts named in the contract migration.
Its bridge diagnostic's `referenced_concepts` is a nonempty subset of the manifest's `concepts_used` list and is disjoint from `concepts_taught`.

### Exact practice ledger

Every statement includes one `**Time budget:**` equal to its manifest `minutes` value.
Coding problems pin all array/tensor shapes, dtypes, seed, allowed/banned APIs, fixed probes, and `atol`/`rtol`; no rubric may accept a visually plausible but numerically unchecked attention result.

| Id | Set | Type | Difficulty | Minutes | Primary scored contract |
|---|---|---|---|---:|---|
| B2-019-p01 | A | mc | intro | 20 | identify Q/K/V roles and a valid attention row |
| B2-019-p02 | A | mc-normal-form | intro | 20 | exact scaled dot-product score and softmax weight |
| B2-019-p03 | A | mc | core | 20 | self-attention as scaled dot-product attention with (Q=K=V): output shape and sequence interaction |
| B2-019-p04 | A | mc | intro | 20 | causal versus padding mask semantics before softmax |
| B2-019-p05 | A | mc | core | 20 | positional encoding and permutation-equivariance consequence |
| B2-019-p06 | B | constrained-coding | intro | 50 | stable NumPy scaled-dot-product attention with row checks |
| B2-019-p07 | B | constrained-coding | core | 50 | batched scaled self-attention shape/transpose implementation |
| B2-019-p08 | B | constrained-coding | core | 50 | additive causal mask with forbidden weights certified zero |
| B2-019-p09 | B | constrained-coding | core | 50 | sinusoidal position table added to pinned token embeddings, with fixed even/odd and output probes |
| B2-019-p10 | B | constrained-coding | advanced | 50 | prove the head split/concatenation shape contract, then implement multi-head attention without head-axis leakage |
| B2-019-p11 | B | constrained-coding | advanced | 50 | PyTorch attention module with explicit scale and mask contract |
| B2-019-p12 | B | constrained-coding | core | 50 | pre-norm residual/feed-forward Transformer block shape contract |
| B2-019-p13 | B | proof | core | 45 | derive why dividing scores by \(\sqrt{d_k}\) controls variance |
| B2-019-p14 | B | proof | core | 45 | derive causal-mask dependence only on positions \(\leq i\) |
| B2-019-p15 | B | proof | advanced | 45 | derive multi-head projection/concatenation dimensions |
| B2-019-p16 | B | proof | core | 45 | derive score-matrix time and memory scaling in \(n,d,h\) |
| B2-019-p17 | C | integrative | advanced | 65 | train a seeded tiny causal-attention predictor with positional input and certify loss/predictions |
| B2-019-p18 | C | integrative | core | 65 | audit a from-scratch scaled-dot-product attention module for padding/causal masks that catch post-softmax or wrong-axis masking |
| B2-019-p19 | C | integrative | advanced | 65 | derive and assemble a one-block encoder recurrence with residual and LayerNorm ordering audit |
| B2-019-p20 | C | integrative | advanced | 65 | trace encoder, decoder self-attention, and cross-attention Q/K/V sources through a Transformer-block composition |
| B2-019-p21 | C | integrative | core | 65 | compare exact attention cost under fixed length/dimension budgets |
| B2-019-p22 | C | scenario | core | 55 | choose causal/padding/bidirectional masking policy and justify it |
| B2-019-p23 | C | challenge | advanced | 55 | reconstruct a two-head result from pinned projections and values, then certify its score-memory budget |
| B2-019-p24 | C | challenge | advanced | 55 | diagnose and repair a real Transformer-block residual/norm/mask bug |

The practice total is exactly 1,120 minutes: 100 multiple-choice minutes, 350 constrained-coding minutes, 180 derivation/proof minutes, 325 integrative minutes, 55 scenario minutes, and 110 challenge minutes.

The manifest's direct knowledge-point evidence ledger is:

| Knowledge point | Required modalities | Direct evidence |
|---|---|---|
| `attention-mechanism-foundations` | theory, derivation, implementation | Session 1; p01/p02; p13; p06 |
| `self-attention` | theory, derivation, implementation | Session 2; p03; p14; p07/p08 |
| `multi-head-attention` | theory, derivation, implementation | Session 3; p10/p23; p15; p10/p23 |
| `positional-encoding` | theory, implementation | Session 3; p05; p09/p17 |
| `attention-complexity-analysis` | theory, derivation | Session 3; p21; p16/p23 |
| `attention-from-scratch` | theory, implementation, model-training | Session 4; p18; p11/p17; p17 |
| `transformer-architecture-foundations` | theory, derivation, implementation | Session 5; p20; p19; p12/p19/p24 |

Each coverage claim declares its complete modality list, first session, and Book 2-owned evidence concept(s).
`self-attention` explicitly includes `derivation`, resolving the Design 019 gate nit.
Each `evidence_by_modality` row names the listed lesson anchor with `role: primary`, and every claimed knowledge point has at least three distinct qualifying practice IDs across its modalities.
The exact `shipped_concepts` / `evidence_concepts` mapping is: attention foundations → `[query-key-value-attention, scaled-dot-product-attention]`; self-attention → `[scaled-dot-product-attention, causal-self-attention, attention-mask]`; multi-head → `[multi-head-attention]`; positional encoding → `[sinusoidal-positional-encoding]`; complexity → `[attention-complexity]`; from-scratch attention → `[scaled-dot-product-attention, causal-self-attention]`; Transformer architecture → `[transformer-block, transformer-residual-layernorm, position-wise-feed-forward]`.

The manifest must carry these minimum owned-concept practice tags; each list has three distinct paths and no tag is inferred from a unit-level claim:

| Owned concept | Required direct practice tags |
|---|---|
| `matrix-transpose` | p02, p06, p07 |
| `query-key-value-attention` | p01, p02, p06 |
| `scaled-dot-product-attention` | p02, p03, p06, p07, p11, p13, p18 |
| `attention-mask` | p04, p08, p18 |
| `causal-self-attention` | p04, p08, p14, p17 |
| `multi-head-attention` | p10, p15, p23 |
| `sinusoidal-positional-encoding` | p05, p09, p17 |
| `attention-complexity` | p16, p21, p23 |
| `transformer-residual-layernorm` | p12, p19, p24 |
| `position-wise-feed-forward` | p12, p19, p24 |
| `transformer-block` | p12, p19, p20, p24 |

### Permanent verification

1. Add model/parser tests for Book 1 defaults and explicit Book 2 fields, independently asserting that `prereqs` remains a unit DAG and `concept_prerequisites` is the manifest-matched concept DAG.
2. Add `tests/test_layer_boundary.py` with true mutations for Book 1/Round 2 leakage, wrong Book 2 owner, manifest/syllabus edge mismatches, a missing diagnostic, non-subset `evidence_concepts`, missing required modality, illegal early in-unit coverage ordering, missing seed, and a CPU task without a local solution path.
3. Add `tests/test_book2_schedule.py` for independent local/global week numbering, Book 1 byte-for-byte regression, final assessment semantics (including a stale `after_book_week` after an extension), renderer separation, and malformed Book 2 schedule fixtures.
4. Add `tools/verify_attention_mutations.py` with exactly five fail-closed answer-affecting mutations: remove the scale factor in p06, apply the causal mask after softmax in p08, swap the multi-head concatenation axis in p10, omit positional addition in p09, and reverse the residual/LayerNorm order in p24.
5. Extend `scripts/pre-merge-guard.sh` and its tests so its unit-name collision contract covers both legacy numeric IDs and `B2-NNN-*` IDs; wire the new layer-boundary, Book 2 schedule, attention mutation, inventory, PDF, prerequisite, coverage, and namespace-discovery checks into `scripts/ci-local.sh`; retain every existing Round 1 check unchanged.

## Out of scope

- No language-model pretraining/fine-tuning, trained embedding bridge, vision transformer, graph transformer, object detection, U-Net, VAE, GAN, diffusion, Stable Diffusion, GPU-only work, or R2 mock test; Plans 020–024 own those topics.
- No rewrite, re-label, schedule mutation, or Round 2 coverage credit for current Book 1 units or `r1-001`.
- No Student's t-test, importance sampling, raw contest material, student data, opaque pretrained weights, or external dataset downloads.
- No edits to `AGENTS.md`, `docs/development-workflow.md`, `docs/content-review-gate.md`, or `docs/architecture/decisions.md`.

## Execution ownership

- Planning, layer/schedule integration, evidence ledger, review recording, and post-execution report: inline.
- Lesson content and all 24 practice statements: fresh GPT-5.6-sol session.
- All 24 solutions: a separate fresh GPT-5.6-sol session that reads only finished statements, never their author outline or draft answers.
- Tooling, generators, and tests: GPT-5.6-sol implementation session.
- Plan gate: inline self-review, one fresh GPT-5.6-sol review, GLM-5.2 review, and a separate fresh DeepSeek V4 Flash review; all four run before implementation.
- Content gate: the same active rotation before PR: self, GPT-5.6-sol, GLM-5.2, and DeepSeek V4 Flash before 2026-08-09 16:00 America/Los_Angeles, with Fable 5 replacing DeepSeek only at or after that cutoff.

## Phase 0 — Pin the Book 2 boundary in failing tests

### Files

- `tests/test_model.py`
- `tests/test_scope.py`
- `tests/test_prereq_coverage.py`
- `tests/test_schedule.py`
- `tests/test_layer_boundary.py` (new)
- `tests/test_book2_schedule.py` (new)
- `tests/test_integration.py`

### Work

Write failing tests that require the exact Book 2 fields, explicit B2-019 syllabus/manifest ownership, the eleven-concept list, its four unit prerequisites and eight concept prerequisites, and the seven complete Round 2 coverage claims.
Add mutation fixtures that prove the layer checker rejects each failure enumerated in Permanent verification, including a `coverage_claims` row that says `self-attention: [theory, implementation]` but omits its required derivation, a `B2-019-*` collision that escapes the legacy guard, a claimed knowledge point with fewer than three distinct qualifying practice IDs, and an owned concept with fewer than three direct practice tags.
Pin the immutable Book 1 regression by comparing the checked-in `curriculum/course-schedule.yaml`, existing Round 1 manifests, and `r1-001` namespace behavior before and after a valid Book 2 fixture.
Add a roadmap mutation asserting that all 30 Round 2 targets occur in exactly one of the six B2 planned-unit membership rows, while retaining the documented partial `nlp-word-embeddings` destination exception at `C8-embeddings`, and that no `P015-R2-*` row remains.

Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_model.py tests/test_scope.py tests/test_prereq_coverage.py \
  tests/test_schedule.py tests/test_layer_boundary.py tests/test_book2_schedule.py \
  tests/test_integration.py
```

Expected before implementation: the new Book 2 tests fail only because the fields, checker, schedule route, and B2-019 artifacts do not exist.

Commit:

```bash
git add tests/test_model.py tests/test_scope.py tests/test_prereq_coverage.py \
  tests/test_schedule.py tests/test_layer_boundary.py tests/test_book2_schedule.py tests/test_integration.py
git commit -m "test: pin Book 2 attention boundary"
```

## Phase 1 — Implement canonical ownership and layer verification

### Files

- Modify: `tools/model.py`
- Modify: `tools/checks/scope.py`
- Create: `tools/checks/layer_boundary.py`
- Modify: `tools/cli.py`
- Modify: `scripts/ci-local.sh`
- Modify: `scripts/pre-merge-guard.sh`
- Modify: `syllabus.md`
- Modify: `curriculum/coverage-map.yaml`
- Modify: `curriculum/material-inventory.yaml` (generated metadata only)
- Modify: `docs/curriculum-roadmap.md` (generated)
- Modify: `tests/test_integration.py`

### Work

Implement strict typed parsing for the Book/layer/round, concept-DAG, bridge-diagnostic, coverage-claim, and compute-inventory fields.
Default only existing Book 1 records; reject missing fields on Book 2 records.
Implement the layer-boundary CLI/checker and call it from `ci-local.sh` before derived inventory/PDF checks.
Replace all three legacy `P015-R2-*` rows with six Book 2 planned-unit rows and add the eleven B2-019 concepts plus the B2-019 syllabus row without changing Book 1 ownership.
Move every missing target's destination to its corresponding B2 unit, except the partial `nlp-word-embeddings` row: it remains `disposition: extend-existing-unit`, `destination: C8-embeddings`, and partial until Plan 020 introduces its explicitly checked `bridge_completion` rather than violating the existing-unit disposition contract.
Generate the roadmap after its source coverage map changes and refresh the material inventory metadata when the canonical syllabus digest or concept count changes.
The Phase 1 inventory refresh must remain metadata-only: do not create a live B2-019 manifest, material row, or other B2 artifact entry before every manifest-declared notebook exists in Phase 3.

Run the Book/layer subset of the Phase 0 suite and:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_model.py tests/test_scope.py tests/test_prereq_coverage.py \
  tests/test_layer_boundary.py tests/test_integration.py \
  -k 'not test_ci_executes_book2_schedule_check and not test_ci_executes_attention_mutations'
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run python -m tools.audit_curriculum --check
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run usaaio-tools layer-boundary-check
```

Expected: all Phase 1 Book 2 parser/checker tests pass with the two Phase 2/4 CI-wiring assertions explicitly deselected; the material inventory reports the current canonical syllabus metadata but no live B2-019 manifest, schedule, coverage claim, material row, or other B2 artifact entry exists yet.

Commit:

```bash
git add tools/model.py tools/checks/scope.py tools/checks/layer_boundary.py tools/cli.py \
  scripts/ci-local.sh scripts/pre-merge-guard.sh syllabus.md curriculum/coverage-map.yaml \
  curriculum/material-inventory.yaml docs/curriculum-roadmap.md tests/test_integration.py
git commit -m "feat: enforce Book 2 curriculum boundaries"
```

## Phase 2 — Implement and fixture-test the independent Book 2 schedule route

### Files

- Create: `tools/checks/book2_schedule.py`
- Create: `tools/render_book2_structure.py`
- Create: `tests/fixtures/book2-schedule-valid/` (complete fixture root)
- Modify: `tools/cli.py`
- Modify: `scripts/ci-local.sh`
- Modify: `docs/curriculum-architecture.md`

### Work

Implement and test the Book 2 parser, validator, and renderer against dedicated temporary fixture roots only.
The fixture carries the six-week, 1,660-minute B2-019 ledger and a minimal valid manifest so schedule reconciliation is exercised before content authoring.
Require six contiguous local weeks, exact global-week offset after 40, reconciliation of every bridge-diagnostic/lesson/practice/review minute against its fixture manifest, and a Book 2 final-assessment rule that remains satisfiable before an R2 mock is introduced.
Make the renderer capable of rendering Book 1 and Book 2 as separate labelled paths; its Book 1 output must remain byte-identical.

Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q tests/test_book2_schedule.py tests/test_schedule.py
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache \
  uv run usaaio-tools --root tests/fixtures/book2-schedule-valid book2-schedule-check
```

Expected: valid fixture Book 2 rows render independently; malformed numbering, Book 1 mutation, or invalid final semantics fails. No live Book 2 schedule or landing page is written in this phase.

Commit:

```bash
git add tools/checks/book2_schedule.py tools/render_book2_structure.py tools/cli.py \
  scripts/ci-local.sh docs/curriculum-architecture.md tests/test_book2_schedule.py
git commit -m "feat: add independent Book 2 schedule"
```

## Phase 3 — Deliver B2-019 teaching and practice material

### Files

- Create: `units/B2-019-attention-transformers/manifest.yaml`
- Create: `units/B2-019-attention-transformers/lesson.ipynb`
- Create: `units/B2-019-attention-transformers/review.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/00-book1-bridge.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/01-query-key-value-and-scaled-dot-product.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/02-self-attention-and-masks.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/03-multi-head-position-and-cost.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/04-attention-module-and-tiny-training.ipynb`
- Create: `units/B2-019-attention-transformers/lessons/05-transformer-blocks-and-architecture.ipynb`
- Create: `units/B2-019-attention-transformers/practice/p01.ipynb` through `p24.ipynb`
- Create: `units/B2-019-attention-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`
- Create: `units/B2-019-attention-transformers/scripts/generate_attention_data.py`

### Work

Author the six teaching surfaces and exact 24-row practice ledger above.
The lessons teach every owned concept before a practice uses it, contain shape tables and explicit masks/scales, use fixed local synthetic data, and mark all Book 2 material visibly as `Round 2 extension`.
Create the manifest only after every declared overview, bridge, lesson, review, statement, solution, and generator path exists.
It contains the exact 24-row ledger, ownership/prerequisite fields, bridge-diagnostic minutes/path, and CPU task inventory, but leaves coverage claims for Phase 4 after all executable evidence has passed.
The statement author does not create solutions; the independent solution author blind-solves each final statement and writes executable checks with fixed probes and tolerances.

Run fresh execution in two independent passes:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache \
  uv run jupyter execute units/B2-019-attention-transformers/lesson.ipynb
find units/B2-019-attention-transformers -name '*_solution.ipynb' -print0 | \
  xargs -0 -n1 -I{} sh -c 'PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run jupyter execute "$1"' sh {}
```

Expected: every solution and lesson exits zero; student notebooks remain unexecuted and solution-free.

Commit statements and lessons separately from solutions:

```bash
git add units/B2-019-attention-transformers/manifest.yaml units/B2-019-attention-transformers/lesson.ipynb \
  units/B2-019-attention-transformers/review.ipynb units/B2-019-attention-transformers/lessons \
  units/B2-019-attention-transformers/practice/p[0-9][0-9].ipynb units/B2-019-attention-transformers/scripts
git commit -m "feat: teach attention and Transformer mechanics"
git add units/B2-019-attention-transformers/practice/*_solution.ipynb
git commit -m "feat: add verified attention solutions"
```

## Phase 4 — Close evidence and add answer-affecting mutations

### Files

- Create: `tools/verify_attention_mutations.py`
- Create: `tests/test_attention_mutations.py`
- Modify: `scripts/ci-local.sh`
- Create: `curriculum/book2-schedule.yaml`
- Modify: `curriculum/coverage-map.yaml`
- Modify: `curriculum/material-inventory.yaml` (generated)
- Modify: `docs/curriculum-roadmap.md` (generated)
- Create: `docs/book2-structure.md`
- Modify: `tests/test_audit_curriculum.py`
- Modify: `tests/test_integration.py`

### Work

Create `curriculum/book2-schedule.yaml` and generated `docs/book2-structure.md` from the now-complete B2-019 manifest.
Promote exactly the seven B2-019 knowledge-point rows to `covered`, attach the manifest's seven coverage claims with lesson anchors and direct theory/derivation/implementation/model-training practice evidence, set empty deficits, and retain every later Book 2 target as missing/partial.
Add the five real source/cell mutations specified above; each must make its intended answer check fail while the untouched corpus passes.
Regenerate inventory and roadmap only after the boundary checker accepts the complete manifest and live schedule.

Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_attention_mutations.py tests/test_audit_curriculum.py tests/test_integration.py
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run python tools/verify_attention_mutations.py
```

Expected: all five mutations fail closed and the normal B2-019 corpus passes.

Commit:

```bash
git add tools/verify_attention_mutations.py tests/test_attention_mutations.py scripts/ci-local.sh \
  curriculum/book2-schedule.yaml curriculum/coverage-map.yaml curriculum/material-inventory.yaml \
  docs/curriculum-roadmap.md docs/book2-structure.md \
  tests/test_audit_curriculum.py tests/test_integration.py
git commit -m "test: lock attention answer contracts"
```

## Phase 5 — Final verification, content gate, and report

### Files

- Modify: `docs/plans/019-r2-attention-transformers.md`

### Work

Run the full local gate with temporary local reference-corpus mounts only if required by overlap scan; do not stage them.
Run the mandatory four-way content gate with blind solution checks, record and resolve every `[OPEN]` finding, then write this plan's post-execution report with the exact commands, executed-notebook evidence, checker output, known nonfatal warnings, and implementation commits.

Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/ci-local.sh
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/pre-merge-guard.sh --pr
```

Expected: `ci-local: ALL GREEN` and `pre-merge-guard: OK`; any failure stops the plan rather than being documented as a success.

Commit:

```bash
git add docs/plans/019-r2-attention-transformers.md
git commit -m "docs: record Plan 019 execution report"
```

## Phase 6 — Publish and merge

### Work

Push the reviewed branch, open a PR, rerun the mandatory PR-union guard after the PR exists, and squash-merge only if it remains green.
The committed Phase 5 report records only evidence available before merge; the GitHub PR records the merge commit.

Run:

```bash
git push -u origin feature/plan-019-attention-transformers
GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) gh pr create --base main --head feature/plan-019-attention-transformers
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/pre-merge-guard.sh --pr
PR_NUMBER=$(GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) gh pr view feature/plan-019-attention-transformers --repo weiboz0/usaaio --json number --jq .number)
cd /tmp && GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) gh pr merge "$PR_NUMBER" --repo weiboz0/usaaio --squash --delete-branch
```

Expected: the PR guard reports `pre-merge-guard: OK`; the merged PR is the sole persistent merge record.

## Plan Review

- [self] APPROVE — substantive plan at `ad6f55a` has prerequisite-closed session order, exact 1,660-minute reconciliation, complete qualifying-practice and owned-concept tag ledgers, a non-overlapping Book 1/Book 2 boundary, and an executable verification phase.
- [sol] APPROVE — final delta at `695a41d`; corrected qualifying-practice modality placement and every cited practice's intersection with its shipped concepts.
- [glm] APPROVE WITH NITS — final delta at `ad6f55a`; bridge/subset, `track`, Book 2 layer, fixture-root, migration, and review-contract checks pass. Session 3 pacing remains for the content gate.
- [deepseek] APPROVE WITH NITS — final delta at `ad6f55a`; the evidence, mutation, schedule, and destination-exception enforcement contracts have no remaining blocker or concern.

## Content Review

Not started; this gate occurs after implementation and before the Plan 019 PR.

## Post-execution report

Not started.
