# Plan 019 — Atomic Two-Book Cutover and Attention Foundations

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task, with specification and code-quality review after every task.

**Goal:** Atomically migrate the existing Round 1 course into a complete `book1/` root, establish a complete and independently verifiable `book2/` root, and ship `book2/units/B2-019-attention-transformers`.

**Architecture:** A strict top-level `books.yaml` registry is the only discovery entry point.
Each book owns its syllabus, curriculum, units, mock tests, references, learner documentation, and build outputs; shared tools accept an explicit book or validate all registered books.
Book 2 imports qualified Book 1 prerequisites without duplicating ownership.

**Tech Stack:** Python 3.12, dataclasses, PyYAML, pytest, Jupyter notebooks, NumPy, PyTorch, Ruff, shell CI, and Git history-preserving moves.

---

## Branch, baseline, and amendment state

- Branch: `feature/plan-019-attention-transformers`.
- Main baseline: `9c57116bd648534b20833d5e421c9256b85322fd`, Design 019 / PR #21.
- Architecture amendment: `88806b7`, approved by the user on 2026-08-10.
- Current Book 1 baseline: 19 units, 149 Book 1 concepts, 437 unit practices, one `r1-001` mock, and 40 weeks.
- Book 2 target baseline: 30 missing or partial required or bridge Round 2 knowledge points.
- Pre-amendment commits through `4cc3894` implemented a shared-root model and are quarantined WIP.
  Execution refactors them into the approved two-root architecture; their earlier review verdicts do not satisfy this plan gate.
- No filesystem migration or Phase 2 implementation resumes until the amended four-way plan gate closes.

## Final canonical tree

```text
books.yaml
book1/
  syllabus.md
  curriculum/{course-schedule,coverage-map,material-inventory,official-topics,source-manifest}.yaml
  units/
  mocktests/{blueprint.yaml,r1-001/}
  reference/
  docs/course-structure.md
  build/
book2/
  syllabus.md
  curriculum/{course-schedule,coverage-map,material-inventory,official-topics,source-manifest}.yaml
  units/B2-019-attention-transformers/
  mocktests/blueprint.yaml
  reference/
  docs/course-structure.md
  build/
tools/
scripts/
docs/{architecture,audits,designs,plans,reviews}/
```

Root-level `syllabus.md`, `curriculum/`, `units/`, `mocktests/`, and `reference/` are forbidden after the cutover.
There are no compatibility symlinks, fallback reads, copied source trees, or dual writes.

## Canonical registry and API

Create `tools/books.py` with these public contracts:

```python
@dataclass(frozen=True)
class BookSpec:
    id: str
    number: int
    root: Path
    depends_on: tuple[str, ...]

@dataclass(frozen=True)
class BookImports:
    source_book: str
    units: tuple[str, ...]
    concepts: tuple[str, ...]

@dataclass(frozen=True)
class BookCatalog:
    repo_root: Path
    books: tuple[BookSpec, ...]

    def by_id(self, book_id: str) -> BookSpec: ...

def load_book_catalog(repo_root: str | Path) -> BookCatalog: ...
def validate_book_root(book: BookSpec) -> list[str]: ...
def load_book_imports(book: BookSpec) -> BookImports: ...
def resolve_qualified_import(catalog: BookCatalog, importer: BookSpec, identity: str) -> Path: ...
```

`load_book_catalog()` accepts exactly `books_version` and `books` and validates only registry structure: duplicate IDs/numbers/roots, unknown or cyclic dependencies, absolute or escaping roots, symlinks, undeclared `book*/` roots, and forbidden legacy roots.
It does not inspect the contents of an unselected sibling book.
`validate_book_root()` validates the selected book's required tracked files: `syllabus.md`, the five named curriculum YAML files, `mocktests/blueprint.yaml`, and `docs/course-structure.md`.
`units/` and `reference/` are required tracked directories, seeded with `.gitkeep` when empty; `build/` is generated, ignored, and may be absent before a build.
`load_book_imports()` reads the selected book's persisted syllabus `imports` block; `books.yaml` authorizes the source-book dependency edge while that block authorizes the exact unit and concept symbols.
Existing domain loaders receive one `BookSpec.root`; they never search the repository root or an unselected sibling book.
CLI keeps `--root` as the repository containing `books.yaml`, requires exactly one of `--book` or `--all`, resolves the selection before dispatch, and passes `BookSpec.root` to each domain check.
`--book book1` validates only Book 1 content; `--book book2` additionally loads only its declared Book 1 imports; `--all` validates every book in dependency order.

## Book ownership and cross-book imports

`book1/syllabus.md` owns exactly the existing 149 concepts and 19 units.
`book2/syllabus.md` initially owns exactly these eleven concepts and `B2-019-attention-transformers`:

```text
matrix-transpose
query-key-value-attention
scaled-dot-product-attention
attention-mask
causal-self-attention
multi-head-attention
sinusoidal-positional-encoding
attention-complexity
transformer-residual-layernorm
position-wise-feed-forward
transformer-block
```

Book 2 declares imports from `book1` for units `[C6-pytorch, C7-cnn-transfer, C8-embeddings, C11-neural-training]` and concepts `[softmax, matrix-multiplication, broadcasting, variance, torch-tensors, nn-module, torch-optimizers, autograd-training]`.
At the registry boundary, diagnostics use qualified identities such as `book1:C6-pytorch` and `book1:softmax`.
Within a book, existing local IDs remain unchanged.

## Book 2 program and B2-019 content contract

The six planned Book 2 units remain:

1. `B2-019-attention-transformers` — Attention and Transformer Mechanics.
2. `B2-020-language-transformers` — Language Transformers.
3. `B2-021-cross-modal-transformers-vision` — Cross-modal Transformers and Advanced Vision.
4. `B2-022-probabilistic-latent-models` — Probabilistic Latent Models.
5. `B2-023-generative-models-diffusion` — Generative Models and Diffusion.
6. `B2-024-gpu-scientific-ml-capstone` — GPU Scientific Modeling Capstone.

All 30 Round 2 targets occur in exactly one planned-unit membership.
The partial `nlp-word-embeddings` row remains an explicit cross-book bridge to `book1:C8-embeddings` until Plan 020 supplies model-training evidence.

B2-019 contains a 30-minute Book 1 bridge diagnostic, five 90-minute lessons, 24 practices totalling 1,120 minutes, and a 60-minute review.
The Book 2 schedule totals 1,660 minutes across local weeks 1–6 and display weeks 41–46.

| Book week | Global week | Allocation |
|---:|---:|---|
| 1 | 41 | bridge 30; Session 1 90; p01, p02, p06, p13 = 135 |
| 2 | 42 | Session 2 90; p03, p04, p07, p08, p14 = 185 |
| 3 | 43 | Session 3 90; p05, p09, p10, p15, p16, p21, p23 = 330 |
| 4 | 44 | Session 4 90; p11, p17, p18, p22 = 235 |
| 5 | 45 | Session 5 90; p12, p19, p20, p24 = 235 |
| 6 | 46 | review 60; planned future R2 final assessment marker |

### Teaching surfaces

| Session | Book-local path | Required surface |
|---:|---|---|
| 0 | `lessons/00-book1-bridge.ipynb` | diagnose imported softmax, matrix, broadcasting, tensor, and autograd prerequisites without re-owning them |
| 1 | `lessons/01-query-key-value-and-scaled-dot-product.ipynb` | matrix transpose, Q/K/V, scale, stable row softmax, weighted values |
| 2 | `lessons/02-self-attention-and-masks.ipynb` | sequence shapes, padding masks, causal masks before softmax |
| 3 | `lessons/03-multi-head-position-and-cost.ipynb` | head projections/concat, sinusoidal position, exact time and score-memory cost |
| 4 | `lessons/04-attention-module-and-tiny-training.ipynb` | tested PyTorch attention module and seeded causal training task |
| 5 | `lessons/05-transformer-blocks-and-architecture.ipynb` | pre-norm residual block, feed-forward sublayer, encoder/decoder roles |

### Exact practice ledger

| ID | Type | Minutes | Primary contract |
|---|---|---:|---|
| p01 | MC | 20 | identify Q/K/V roles and a valid attention row |
| p02 | MC normal form | 20 | exact scaled score and softmax weight |
| p03 | MC | 20 | scaled self-attention with Q=K=V, output shape, interaction |
| p04 | MC | 20 | causal versus padding masks before softmax |
| p05 | MC | 20 | positional encoding and permutation equivariance |
| p06 | constrained coding | 50 | stable NumPy scaled-dot-product attention |
| p07 | constrained coding | 50 | batched scaled self-attention transpose contract |
| p08 | constrained coding | 50 | additive causal mask with forbidden weights zero |
| p09 | constrained coding | 50 | sinusoidal table plus pinned embedding probes |
| p10 | constrained coding | 50 | derive then implement head split/concatenation |
| p11 | constrained coding | 50 | PyTorch attention module with scale and mask |
| p12 | constrained coding | 50 | pre-norm residual/feed-forward block |
| p13 | proof | 45 | variance control by division by sqrt(d_k) |
| p14 | proof | 45 | causal dependence only on positions at or before i |
| p15 | proof | 45 | multi-head projection and concatenation dimensions |
| p16 | proof | 45 | score time and memory scaling in n, d, h |
| p17 | integrative | 65 | seeded causal predictor with positional input |
| p18 | integrative | 65 | from-scratch attention mask audit |
| p19 | integrative | 65 | encoder recurrence and LayerNorm ordering |
| p20 | integrative | 65 | encoder/decoder/cross-attention Q/K/V sources |
| p21 | integrative | 65 | exact cost under fixed length/dimension budgets |
| p22 | scenario | 55 | choose and justify mask policy |
| p23 | challenge | 55 | reconstruct two heads and certify memory budget |
| p24 | challenge | 55 | repair residual/norm/mask bug |

Every coding statement pins shapes, dtypes, seed `20260808`, allowed and banned APIs, fixed probes, and explicit `atol` and `rtol`.
Student notebooks contain no solutions or executed output.
Every solution executes top-to-bottom and ends in `### Answer check` assertions.

### Coverage evidence

| Knowledge point | Modalities | Direct practices |
|---|---|---|
| attention-mechanism-foundations | theory, derivation, implementation | p01, p02, p13, p06 |
| self-attention | theory, derivation, implementation | p03, p14, p07, p08 |
| multi-head-attention | theory, derivation, implementation | p10, p23, p15 |
| positional-encoding | theory, implementation | p05, p09, p17 |
| attention-complexity-analysis | theory, derivation | p21, p16, p23 |
| attention-from-scratch | theory, implementation, model-training | p18, p11, p17 |
| transformer-architecture-foundations | theory, derivation, implementation | p20, p19, p12, p24 |

Each modality has a primary lesson anchor and at least one primary practice.
Each covered knowledge point has at least three distinct qualifying practices.
Every Book 2-owned concept has at least three direct practice tags.

| Owned concept | Required direct practice tags |
|---|---|
| matrix-transpose | p02, p06, p07 |
| query-key-value-attention | p01, p02, p06 |
| scaled-dot-product-attention | p02, p03, p06, p07, p11, p13, p18 |
| attention-mask | p04, p08, p18, p22 |
| causal-self-attention | p04, p08, p14, p17 |
| multi-head-attention | p10, p15, p23 |
| sinusoidal-positional-encoding | p05, p09, p17 |
| attention-complexity | p16, p21, p23 |
| transformer-residual-layernorm | p12, p19, p24 |
| position-wise-feed-forward | p12, p19, p24 |
| transformer-block | p12, p19, p20, p24 |

## Permanent verification requirements

1. Registry mutations reject missing, duplicate, cyclic, escaping, symlinked, or undeclared book roots.
2. Legacy-path mutations reject any root-level content tree or fallback load.
3. Book-local discovery proves a Book 1 command succeeds unchanged when Book 2 content is missing or corrupt, while a Book 2 command reads only its selected root plus its exact declared Book 1 imports.
4. Cross-book import mutations reject unqualified, undeclared, later-layer, cyclic, or ownership-changing references.
5. A `git archive HEAD` verifier covers notebook execution, generated documents, nonzero PDF outputs, references, mock tests, ignore rules, and pre-merge collision discovery without untracked legacy artifacts.
6. Layer-boundary mutations preserve all prior Book 1/Round 2 ownership, evidence, compute, and coverage checks.
7. Schedule mutations cover local/global numbering, exact reconciliation, stale final marker, and cross-book leakage.
8. Five answer-affecting mutations remove scaling, mask after softmax, concatenate the wrong head axis, omit positional addition, and reverse residual/LayerNorm order.
9. The PR guard translates pre-cutover `origin/main` Book 1 paths into their post-cutover namespace before collision checks and rejects any untranslatable legacy addition.

## Execution ownership

- Orchestration, migration mapping, generated evidence, and reports: active Codex session.
- Tooling and tests: fresh GPT-5.6-sol implementation sessions.
- Lesson content and all 24 statements: fresh GPT-5.6-sol session.
- All 24 solutions: separate fresh GPT-5.6-sol session that receives only final statements.
- Plan gate after the 2026-08-09 cutoff: `[self]`, `[sol]`, `[glm]`, `[fable]`.
- Content gate uses the same post-cutoff roster.

## Out of scope

- Rewriting pedagogical content inside existing Book 1 notebooks.
- Changing existing Book 1 IDs, answers, schedules, or CPU policy.
- Compatibility symlinks, duplicate roots, fallback reads, or dual writes.
- Plans 020–024 content, an R2 mock, Student's t-test, importance sampling, raw contest text, student data, opaque weights, or external required downloads.
- Changes to review rosters or lifecycle policy in `docs/development-workflow.md` or `docs/content-review-gate.md`.

The user explicitly authorized the structure-only updates to `AGENTS.md` and `docs/architecture/decisions.md` on 2026-08-10 after the first amended-plan gate identified their old root layout as a blocker.

## Task 0 — Pin the atomic filesystem contract in failing tests

**Files:**

- Create: `tests/test_books.py`
- Create: `tests/test_book_isolation.py`
- Create: `tests/test_clean_checkout.py`
- Create: `tests/test_reference_migration.py`
- Modify: `tests/test_integration.py`
- Modify: `tests/test_model.py`
- Modify: `tests/test_schedule.py`
- Modify: `tests/test_scope.py`

- [ ] Write `test_catalog_rejects_legacy_root_and_escaping_book_roots` with a minimal two-book temporary repository.
- [ ] Write a mutation matrix for duplicate IDs/numbers/roots, dependency cycles, symlink roots, undeclared `book3/`, and missing required files.
- [ ] Write `test_book1_results_are_byte_identical_after_valid_book2_fixture` across syllabus, schedule, inventory, renderer, answer key, and PDF input discovery.
- [ ] Write `test_book1_selection_does_not_validate_missing_or_corrupt_book2_content` and the converse dependency-scoped Book 2 import test.
- [ ] Write `test_cross_book_import_requires_registry_dependency_and_qualified_owner`.
- [ ] Write clean-checkout producer-to-consumer assertions for every path moved in Task 2.
- [ ] Write shell/static mutations that reject repository-root `find units`, `for dir in units mocktests`, repository-root `Path("syllabus.md")`, and any checker invoked without a selected `BookSpec.root`; do not use a zero-match literal search that would also reject valid book-local `root / "units"` joins.
- [ ] Write PR-union fixtures for an old-layout `origin/main`, including a colliding new `units/C13-*`, a noncolliding old Book 1 unit, and an untranslatable legacy addition.
- [ ] Write local-reference migration fixtures for mixed tracked/ignored R1 and R2 corpora, shared cache, outlines, unexpected entries, reruns, and proof that raw files remain ignored.
- [ ] Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_books.py tests/test_book_isolation.py tests/test_clean_checkout.py \
  tests/test_reference_migration.py tests/test_integration.py \
  tests/test_model.py tests/test_schedule.py tests/test_scope.py
```

Expected: existing Book 1 tests pass; new registry and isolation tests fail only because `books.yaml`, `tools/books.py`, and migrated roots do not exist.

- [ ] Commit:

```bash
git add tests/test_books.py tests/test_book_isolation.py tests/test_integration.py \
  tests/test_clean_checkout.py tests/test_reference_migration.py tests/test_model.py \
  tests/test_schedule.py tests/test_scope.py
git commit -m "test: pin atomic two-book roots"
```

## Task 1 — Implement the registry API against isolated fixtures

**Files:**

- Create: `tools/books.py`
- Modify: `tools/model.py`
- Modify: `tools/cli.py`
- Test: `tests/test_books.py`
- Test: `tests/test_book_isolation.py`

- [ ] Implement `BookSpec`, `BookCatalog`, and `load_book_catalog()` exactly as specified above.
- [ ] Implement `BookImports`, selected-root validation, exact persisted symbol allowlists, and qualified import resolution as separate APIs; dependency edges alone never authorize arbitrary symbols.
- [ ] Keep current repository consumers on their existing root during this preparatory commit; only temporary fixture roots exercise the new registry API.
- [ ] Implement strict dependency ordering, root containment, symlink rejection, undeclared-book rejection, and legacy-root detection in catalog loading; keep selected content validation separately callable.
- [ ] Implement and unit-test a reusable mutually exclusive `--book` / `--all` parser helper while preserving `--root` as the repository root; do not attach it to the live parser or switch dispatch until Task 2.
- [ ] Run registry and isolation fixtures and confirm every named mutation fails for its intended diagnostic.
- [ ] Run the existing Book 1 model and CLI suites to prove this preparatory API changes no live behavior.
- [ ] Commit:

```bash
git add tools/books.py tools/model.py tools/cli.py tests/test_books.py tests/test_book_isolation.py
git commit -m "feat: add strict book registry API"
```

## Task 2 — Atomically move both books and cut over every consumer

No commit is allowed between the first live `git mv` and the final green verification in this task.
If any consumer cannot be migrated, stop with the uncommitted move set intact and resolve the plan before committing.
Do not use reset, checkout, clean, or deletion as rollback; the last committed revision is the recovery anchor, and work resumes by repairing the preserved move set.

**Files:**

- Create: `books.yaml`
- Create: `book2/syllabus.md`
- Create: `book2/curriculum/{course-schedule,coverage-map,material-inventory,official-topics,source-manifest}.yaml`
- Create: `book2/units/.gitkeep`
- Create: `book2/reference/.gitkeep`
- Create: `book2/mocktests/blueprint.yaml`
- Create: `book2/docs/course-structure.md`
- Create: `scripts/migrate-reference-layout.sh`
- Create: `scripts/verify-clean-checkout.sh`
- Modify: `.gitignore`
- Move: `syllabus.md` → `book1/syllabus.md`
- Move: four same-named curriculum YAML files → `book1/curriculum/`
- Move and rename: `curriculum/sources.yaml` → `book1/curriculum/source-manifest.yaml`
- Move: `units/` → `book1/units/`
- Move: `mocktests/` → `book1/mocktests/`
- Move: `docs/course-structure.md` → `book1/docs/course-structure.md`
- Move and split: `reference/analysis.md` → book-local Round 1 and Round 2 derived analyses
- Modify: `AGENTS.md`
- Modify: `docs/architecture/decisions.md`
- Modify: `docs/designs/000-project-design.md`
- Modify: `docs/README.md`
- Modify: `docs/curriculum-architecture.md`
- Modify: `docs/curriculum-roadmap.md`
- Modify: `TODO.md`
- Modify: `tools/model.py`
- Modify: `tools/cli.py`
- Modify: `tools/checks/answerkey.py`
- Modify: `tools/checks/blueprint.py`
- Modify: `tools/checks/coverage.py`
- Modify: `tools/checks/hygiene.py`
- Modify: `tools/checks/layer_boundary.py`
- Modify: `tools/checks/new_mocktest.py`
- Modify: `tools/checks/overlap.py`
- Modify: `tools/checks/prereq.py`
- Modify: `tools/checks/schedule.py`
- Modify: `tools/checks/scope.py`
- Modify: `tools/checks/tolerance.py`
- Modify: `tools/audit_curriculum.py`
- Modify: `tools/render_course_structure.py`
- Modify: `tools/render_curriculum_roadmap.py`
- Modify: `tools/verify_training_mutations.py`
- Modify: `tools/verify_classical_mutations.py`
- Modify: `units/C7-cnn-transfer/lessons/02-resnet-reading.ipynb` before its move, only for book-root resolution
- Modify: `scripts/build-pdf.sh`
- Modify: `scripts/fetch-reference.sh`
- Modify: `scripts/verify-register.py`
- Modify: `scripts/ci-local.sh`
- Modify: `scripts/pre-merge-guard.sh`
- Modify: every existing `tests/test_*.py` path consumer and fixture path named by `rg -l 'syllabus.md|units/|curriculum/|mocktests/|reference/' tests`
- Modify: `tests/test_book2_schedule.py`
- Modify: `tests/test_layer_boundary.py`

- [ ] Build on the committed WIP through `4cc3894`; do not revert it.
  Rewrite or delete every superseded shared-root expectation explicitly, including the existing `tests/test_book2_schedule.py` imports of nonexistent parallel Book 2 modules.
- [ ] In Task 2, reduce that pre-amendment schedule file to green tests for the registered, empty `status: planned` Book 2 skeleton.
  Task 4 then adds the six-week staged/live policy cases as new failing tests before implementing them; no skip or missing-module sentinel is permitted.
- [ ] Use `git mv` for every tracked source and generated artifact so history remains traceable.
- [ ] Before moving `reference/`, run the migration script in dry-run mode.
  It accepts only `.gitkeep`, `analysis.md`, `r1-*`, `r2-*`, `cache/`, and `outlines-*`; it refuses unknown entries, moves ignored `r1-*`, the shared cache, and the existing Round 1 outlines under Book 1, moves ignored `r2-*` under Book 2, leaves no root `reference/`, and never stages raw files.
- [ ] Translate every existing `.gitignore` rule, including Book 1/Book 2 build and raw-reference rules, all C10 generated CSVs, and R1 mock held-out/student/solution artifacts.
  Add `git check-ignore` assertions for every protected generated path under its new book root and prove the corresponding source files are not accidentally ignored.
- [ ] Create the exact two-record `books.yaml` registry.
- [ ] Partition coverage, topic, and renamed source-manifest contracts deterministically: shared-foundation and Round 1 exit rows into Book 1, Round 2 exit rows into Book 2, and only referenced source metadata into each book.
- [ ] Preserve `nlp-word-embeddings` as a partial Book 2 bridge whose destination is `book1:C8-embeddings`.
- [ ] Preserve covered `nlp-tokenization` as a Book 2 exit row with qualified evidence owned by `book1:C8-embeddings`; neither bridge re-owns Book 1 concepts.
- [ ] Create an empty Book 2 inventory and a planned assessment blueprint with exactly `blueprint_version: 1`, `book: 2`, `target: round-2`, `status: planned`, `assessment_prefix: r2-`, and qualified `derived_from` metadata.
  Planned blueprint mode is valid only while no `r2-*` manifest exists, grants no conformance credit, and must be replaced by Plan 024 before an R2 assessment becomes live.
- [ ] Create the six-unit roadmap with no B2 material rows or coverage credit.
- [ ] Create `book2/curriculum/course-schedule.yaml` with `schedule_version: 1`, `book: 2`, `status: planned`, and an empty `weeks` list accepted only while Book 2 has no live manifest; Task 4 replaces it before the B2 manifest becomes live.
- [ ] Change every loader entry point to accept a registered `BookSpec.root`; remove repository-root and sibling-book fallback discovery.
- [ ] Rename every `sources.yaml` consumer and fixture to `source-manifest.yaml`, including scope checks, integration tests, diagnostics, and syllabus/document prose.
- [ ] Make mock discovery derive `r{BookSpec.number}-*` and reject wrong-round assessment directories instead of hard-coding `r1-*`.
- [ ] Add CLI selection before subcommands:

```text
usaaio-tools --book book1 schedule-check
usaaio-tools --book book2 schedule-check
usaaio-tools --all prereq-check
```

- [ ] Attach the parser helper so live commands now require exactly one of `--book` or `--all`; keep `--root` as the repository root and reject using `--all` for commands without aggregate semantics.

- [ ] Define `--all` as registry-order iteration with book-qualified diagnostics and a nonzero exit when any book fails.
- [ ] Set notebook execution CWD to the selected book root.
  Change only the C7 cache-resolution cell to read the injected `USAAIO_BOOK_ROOT`; preserve every other existing Book 1 notebook byte and prohibit repository-root fallbacks.
- [ ] Make Book 1 schedule, mock, PDF, overlap, inventory, and renderer consumers enumerate only `book1/`.
- [ ] Make Book 2 consumers enumerate only `book2/` and resolve Book 1 imports through `books.yaml`.
- [ ] Parameterize `scripts/build-pdf.sh` by selected book and write only beneath that book's `build/`.
  Book 1 retains its existing mock source set; Book 2 discovers student-facing unit notebooks and must fail, not pass vacuously, when a live unit yields zero PDF sources or outputs.
- [ ] Update the pre-merge guard to normalize a pre-cutover `origin/main` namespace (`units`, `mocktests`, syllabus, curriculum, and references) into Book 1 before computing the prospective merge union.
  Detect translated unit/mock/roadmap collisions, allow the known baseline migration, and reject any new or untranslatable legacy addition.
- [ ] Update CI to run registry validation, each book independently, cross-book imports, aggregate reports, and legacy-path rejection.
- [ ] Apply the user-authorized structure-only governance migration: make `AGENTS.md`, `docs/architecture/decisions.md`, Design 000, the docs index, curriculum architecture, roadmap prose, and live TODO paths name `books.yaml` plus the two complete book roots.
  Do not change reviewer rosters, lifecycle policy, or unrelated decisions.
- [ ] Assert root legacy paths are absent, are not symlinks, and cannot be recreated without failing CI.
- [ ] Inventory path literals as a review aid, then rely on Task 0's structural/static and runtime mutations to distinguish invalid repository-root access from valid book-local joins:

```bash
rg -n '(^|["'"'` ])(units|curriculum|mocktests|reference)/|Path\("syllabus\.md"\)' \
  tools scripts tests .gitignore
```

Expected: every match is either a selected book-root join, a translated pre-cutover guard fixture, or an intentional negative mutation; no repository-root content access remains.

- [ ] Run the complete existing pytest suite, all Book 1 CLI checks, registry/import checks, generated-document freshness, PDF build, and both CLI smoke routes.
- [ ] Commit:

```bash
git status --short
git add -A -- books.yaml book1 book2 syllabus.md curriculum units mocktests reference \
  tools scripts tests docs AGENTS.md TODO.md .gitignore
git commit -m "refactor: split curriculum into complete book roots"
```

## Task 3 — Rebuild generated Book 1 evidence and prove clean-checkout equivalence

**Files:**

- Modify: `book1/curriculum/material-inventory.yaml`
- Modify: `book1/docs/course-structure.md`
- Modify: `docs/audits/015-coverage-audit.md`
- Modify: shared aggregate roadmap/report outputs
- Test: `tests/test_audit_curriculum.py`
- Test: `tests/test_integration.py`

- [ ] Regenerate Book 1 inventory and learner documents from `book1/` only.
- [ ] Generate the shared curriculum roadmap by reading both registered books in dependency order; preserve book-qualified ownership and never treat the aggregate output as a third source of truth.
- [ ] Assert the same 19 units, 149 concepts, 437 practices, 69 lesson sessions, 40 schedule weeks, and `r1-001` assessment namespace.
- [ ] Compare every Book 1 manifest and notebook blob hash under `4cc3894:units/` with its `book1/units/` destination.
  The sole allowed notebook delta is the C7 cache-resolution cell: compare all other cells byte-for-byte and prove the changed cell differs only by replacing repository-root discovery with `USAAIO_BOOK_ROOT`.
- [ ] Execute the existing R1 mock solution from Book 1 CWD so its unchanged `mocktests/r1-001/...` local path resolves within the selected root.
- [ ] Build Book 1 PDFs and assert the same source notebook set and output count.
- [ ] Run Book 1 solution execution, answer-key, hygiene, prerequisite, coverage, schedule, overlap, PDF, and renderer checks.
- [ ] Commit:

```bash
git add book1/curriculum book1/docs docs/audits tests
git commit -m "test: prove Book 1 cutover equivalence"
```

## Task 4 — Implement the book-parameterized schedule route

**Files:**

- Create: `tests/fixtures/two-books-valid/`
- Modify: `tools/checks/schedule.py`
- Modify: `tools/render_course_structure.py`
- Modify: `tools/cli.py`
- Modify: `scripts/ci-local.sh`
- Modify: `tests/test_book2_schedule.py`
- Test: `tests/test_schedule.py`

- [ ] Replace the pre-amendment test's imports of `tools.checks.book2_schedule` and `tools.render_book2_structure`; those modules remain forbidden.
- [ ] Keep one parser, reconciliation engine, dispatcher, and renderer module, with explicit `Book1SchedulePolicy` and `Book2SchedulePolicy` validators behind the shared API.
  Book 1 policy preserves its 40-week semesters, 450–500 minute rule, and mock/debrief ending; Book 2 policy supports local/global numbering, `bridge-diagnostic`, 6-week staging, and a planned future-assessment marker.
- [ ] Install the exact six-week schedule as `status: staged` before the manifest exists.
  In staged state, validate schema, local/global sequence, allowed kinds, explicit allocation minutes, the 1,660-minute ledger, uniqueness, and final marker, but grant no coverage and reject staged schedules once any live Book 2 manifest exists.
- [ ] Task 5 changes the schedule atomically to `status: live`; live mode requires full manifest path/ID/minute reconciliation and rejects missing content.
- [ ] Validate local weeks 1–6, display weeks 41–46, all 1,660 minutes, every practice exactly once, and the planned final marker after local week 6.
- [ ] Mutate local/global numbering, allocation minutes, duplicate/omitted practice IDs, stale final marker, unknown kinds, and cross-book unit references.
- [ ] Assert Book 1 schedule bytes and rendered output are unchanged by a valid Book 2 fixture.
- [ ] Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_book2_schedule.py tests/test_schedule.py tests/test_book_isolation.py
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache \
  uv run usaaio-tools --book book2 schedule-check
```

- [ ] Commit:

```bash
git add tools scripts tests book2/curriculum book2/docs
git commit -m "feat: add independent Book 2 schedule"
```

## Task 5 — Author B2-019 statements and teaching surfaces

**Files:**

- Create: `book2/units/B2-019-attention-transformers/manifest.yaml`
- Create: `book2/units/B2-019-attention-transformers/lesson.ipynb`
- Create: `book2/units/B2-019-attention-transformers/review.ipynb`
- Create: six notebooks under `book2/units/B2-019-attention-transformers/lessons/`
- Create: `practice/p01.ipynb` through `practice/p24.ipynb`
- Create: `book2/units/B2-019-attention-transformers/scripts/generate_attention_data.py`
- Modify: `book2/curriculum/course-schedule.yaml`

- [ ] The statement author creates the bridge, five lessons, overview, review, generator, and all 24 final student statements without solution outlines.
- [ ] Every path and identifier matches the content and evidence tables above.
- [ ] The bridge diagnoses all eight imported concepts and links every failure to its qualified Book 1 owner/remediation unit, including variance, `nn.Module`, and optimizer fluency.
- [ ] Create the manifest only after all declared statement-side paths exist.
- [ ] In the same commit that makes the manifest live, change the schedule from `staged` to `live` and require exact manifest reconciliation for all 24 practice IDs and minutes.
- [ ] Record `compute.policy: cpu`, seed `20260808`, exact minutes, sessions, imports, concept tags, and solution paths.
- [ ] Run hygiene, manifest, import, coverage-tag, time-budget, and lesson-order checks without executing student notebooks.
- [ ] Commit:

```bash
git add book2/units/B2-019-attention-transformers book2/curriculum/course-schedule.yaml
git commit -m "feat: teach attention and Transformer mechanics"
```

## Task 6 — Blind-solve all 24 practices

**Files:**

- Create: `book2/units/B2-019-attention-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`

- [ ] Dispatch a separate fresh Sol session with only the committed statements and no author outline.
- [ ] Require fixed probes, explicit tolerances, pinned variables, and a final `### Answer check` in every solution.
- [ ] Execute all solutions fresh in numeric ID order `p01` through `p24`.
- [ ] Run statement/solution source isolation and answer-register checks.
- [ ] Commit:

```bash
git add book2/units/B2-019-attention-transformers/practice/*_solution.ipynb
git commit -m "feat: add independently solved attention practices"
```

## Task 7 — Close Book 2 coverage and answer-affecting mutations

**Files:**

- Create: `tools/verify_attention_mutations.py`
- Create: `tests/test_attention_mutations.py`
- Modify: `book2/curriculum/coverage-map.yaml`
- Modify: `book2/curriculum/material-inventory.yaml`
- Modify: `book2/docs/course-structure.md`
- Modify: shared aggregate audit outputs
- Modify: `scripts/ci-local.sh`

- [ ] Promote exactly the seven B2-019 rows to covered and leave all later targets missing or partial.
- [ ] Attach exact lesson anchors, modalities, practices, shipped concepts, and evidence concepts from the tables above.
- [ ] Regenerate Book 2 inventory, structure, and aggregate reports only after the complete manifest is valid.
- [ ] Implement the five source/cell mutations named in Permanent verification.
- [ ] Prove every mutation fails its intended answer check while the untouched corpus passes.
- [ ] Commit:

```bash
git add tools scripts tests book2/curriculum book2/docs docs/audits
git commit -m "test: lock Book 2 attention evidence"
```

## Task 8 — Full verification, four-way content gate, and report

**Files:**

- Modify: `docs/plans/019-r2-attention-transformers.md`

- [ ] Mount local raw reference corpora only at `book1/reference/` and `book2/reference/` when overlap checks require them; never stage raw files.
- [ ] Build Book 1 into `book1/build/` from exactly its pre-cutover mock source set and assert its established nonzero PDF count.
- [ ] Build exactly 32 nonexecuted student-facing B2-019 PDFs into `book2/build/units/B2-019-attention-transformers/`: overview, bridge plus five lessons, review, and 24 practices; zero discovered Book 2 outputs is a failure.
- [ ] Run `scripts/verify-clean-checkout.sh`, which extracts `git archive HEAD` into a fresh temporary directory, supplies no untracked legacy content, runs registry/CLI/document/PDF checks there, asserts ignored generated files remain untracked, and removes only its validated temporary directory.
- [ ] Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/ci-local.sh
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/pre-merge-guard.sh --pr
```

Expected: every Book 1, Book 2, cross-book, notebook, mutation, PDF, inventory, renderer, overlap, and clean-checkout check passes with no plan-dependent skip.

- [ ] Run the post-cutoff content gate with `[self]`, `[sol]`, `[glm]`, and `[fable]` blind checks.
- [ ] Resolve every `[OPEN]` finding and rerun affected checks.
- [ ] Write the post-execution report with exact commits, commands, notebook counts, build counts, warnings, and reviewer verdicts.
- [ ] Commit:

```bash
git add docs/plans/019-r2-attention-transformers.md
git commit -m "docs: record atomic two-book execution"
```

## Task 9 — Publish and merge

- [ ] Push the branch and create a PR using the configured SSH origin and `.gh-token`.
- [ ] Run `scripts/pre-merge-guard.sh --pr` after the PR exists.
- [ ] Confirm the PR union contains no legacy roots, plan/unit collisions, raw references, secrets, or student data.
- [ ] Squash-merge from outside the worktree so the primary `main` checkout does not conflict.

```bash
git push -u origin feature/plan-019-attention-transformers
GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) \
  gh pr create --base main --head feature/plan-019-attention-transformers
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache \
  bash scripts/pre-merge-guard.sh --pr
PR_NUMBER=$(GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) \
  gh pr view feature/plan-019-attention-transformers --repo weiboz0/usaaio --json number --jq .number)
cd /tmp && GH_TOKEN=$(cat /home/chris/workshop/usaaio/.gh-token) \
  gh pr merge "$PR_NUMBER" --repo weiboz0/usaaio --squash --delete-branch
```

## Plan Review

- Round 1 pinned `891c913` and did not close:
  - [self] REJECT — source-manifest rename, learner-document ownership, and reference split were underspecified.
  - [sol] REJECT — eight blockers covering path-sensitive notebooks, ignored references, selected-book isolation, persisted import authority, merge-union translation, governance, ignore rules, and non-vacuous Book 2 builds.
  - [glm] REJECT — three blockers covering superseded schedule tests, book-specific schedule policy, and a blind legacy-path scan.
  - [fable] APPROVE WITH NITS — raised the same source/schedule/governance issues plus required-file, staged-schedule, import, CLI, and bridge precision.
- Round 2 reviews the consolidated amendment and the user's explicit governance authorization:
  - [self] APPROVE — all first-round findings are mapped to named files, contracts, negative mutations, and verification; schedule arithmetic revalidated at 1,660 minutes with p01–p24 exactly once.
  - [sol] Pending fresh review.
  - [glm] Pending fresh review.
  - [fable] Pending fresh review.

The earlier `[deepseek]` round reviewed the superseded shared-root plan and provides no verdict for this amendment.

## Content Review

Not started.

## Post-execution report

Not started.
