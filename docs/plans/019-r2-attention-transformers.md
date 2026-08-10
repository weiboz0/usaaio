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
class BookCatalog:
    repo_root: Path
    books: tuple[BookSpec, ...]

    def by_id(self, book_id: str) -> BookSpec: ...

def load_book_catalog(repo_root: str | Path) -> BookCatalog: ...
```

The loader accepts exactly `books_version` and `books`, resolves roots beneath the repository, and rejects duplicate IDs/numbers/roots, unknown or cyclic dependencies, absolute or escaping paths, symlinks, missing required book files, undeclared `book*/` roots, and legacy root content paths.
Existing domain loaders receive one `BookSpec.root`; they never search the repository root or sibling book.
CLI commands add a global `--book {book1,book2}` selector and `--all` where aggregation is defined.

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

## Permanent verification requirements

1. Registry mutations reject missing, duplicate, cyclic, escaping, symlinked, or undeclared book roots.
2. Legacy-path mutations reject any root-level content tree or fallback load.
3. Book-local discovery proves Book 1 commands never inspect Book 2 artifacts and vice versa.
4. Cross-book import mutations reject unqualified, undeclared, later-layer, cyclic, or ownership-changing references.
5. Clean-checkout path tests cover notebook execution, generated documents, PDFs, references, mock tests, and pre-merge collision discovery.
6. Layer-boundary mutations preserve all prior Book 1/Round 2 ownership, evidence, compute, and coverage checks.
7. Schedule mutations cover local/global numbering, exact reconciliation, stale final marker, and cross-book leakage.
8. Five answer-affecting mutations remove scaling, mask after softmax, concatenate the wrong head axis, omit positional addition, and reverse residual/LayerNorm order.

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
- Edits to `AGENTS.md`, `docs/development-workflow.md`, `docs/content-review-gate.md`, or `docs/architecture/decisions.md`.

## Task 0 — Pin the atomic filesystem contract in failing tests

**Files:**

- Create: `tests/test_books.py`
- Create: `tests/test_book_isolation.py`
- Modify: `tests/test_integration.py`
- Modify: `tests/test_model.py`
- Modify: `tests/test_schedule.py`
- Modify: `tests/test_scope.py`

- [ ] Write `test_catalog_rejects_legacy_root_and_escaping_book_roots` with a minimal two-book temporary repository.
- [ ] Write a mutation matrix for duplicate IDs/numbers/roots, dependency cycles, symlink roots, undeclared `book3/`, and missing required files.
- [ ] Write `test_book1_results_are_byte_identical_after_valid_book2_fixture` across syllabus, schedule, inventory, renderer, answer key, and PDF input discovery.
- [ ] Write `test_cross_book_import_requires_registry_dependency_and_qualified_owner`.
- [ ] Write clean-checkout producer-to-consumer assertions for every path moved in Task 2.
- [ ] Run:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache uv run pytest -q \
  tests/test_books.py tests/test_book_isolation.py tests/test_integration.py \
  tests/test_model.py tests/test_schedule.py tests/test_scope.py
```

Expected: existing Book 1 tests pass; new registry and isolation tests fail only because `books.yaml`, `tools/books.py`, and migrated roots do not exist.

- [ ] Commit:

```bash
git add tests/test_books.py tests/test_book_isolation.py tests/test_integration.py \
  tests/test_model.py tests/test_schedule.py tests/test_scope.py
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
- [ ] Keep current repository consumers on their existing root during this preparatory commit; only temporary fixture roots exercise the new registry API.
- [ ] Implement strict dependency ordering, root containment, symlink rejection, required-file validation, undeclared-book rejection, and legacy-root detection as separately callable checks.
- [ ] Add CLI argument parsing for `--book` and `--all` behind the registry API without switching live command dispatch until Task 2.
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

**Files:**

- Create: `books.yaml`
- Create: `book2/syllabus.md`
- Create: `book2/curriculum/{course-schedule,coverage-map,material-inventory,official-topics,source-manifest}.yaml`
- Create: `book2/mocktests/blueprint.yaml`
- Create: `book2/docs/course-structure.md`
- Modify: `.gitignore`
- Move: `syllabus.md` → `book1/syllabus.md`
- Move: `curriculum/` → `book1/curriculum/`
- Move: `units/` → `book1/units/`
- Move: `mocktests/` → `book1/mocktests/`
- Move: Book 1 learner documents → `book1/docs/`
- Move: tracked reference analysis to `book1/reference/` or `book2/reference/` by round
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
- Modify: `scripts/build-pdf.sh`
- Modify: `scripts/fetch-reference.sh`
- Modify: `scripts/verify-register.py`
- Modify: `scripts/ci-local.sh`
- Modify: `scripts/pre-merge-guard.sh`
- Modify: every existing `tests/test_*.py` path consumer and fixture path named by `rg -l 'syllabus.md|units/|curriculum/|mocktests/|reference/' tests`

- [ ] Use `git mv` for every tracked source and generated artifact so history remains traceable.
- [ ] Update `.gitignore` for `book1/build/`, `book2/build/`, and book-local raw reference mounts without allowing raw papers into Git.
- [ ] Create the exact two-record `books.yaml` registry.
- [ ] Partition coverage, topic, and source contracts deterministically: Round 1 rows into Book 1, Round 2 rows into Book 2, and only referenced source metadata into each book.
- [ ] Preserve `nlp-word-embeddings` as a partial Book 2 bridge whose destination is `book1:C8-embeddings`.
- [ ] Create an empty Book 2 inventory, planned assessment blueprint, and six-unit roadmap with no B2 material rows or coverage credit.
- [ ] Create `book2/curriculum/course-schedule.yaml` with `schedule_version: 1`, `book: 2`, `status: planned`, and an empty `weeks` list accepted only while Book 2 has no live manifest; Task 4 replaces it before the B2 manifest becomes live.
- [ ] Change every loader entry point to accept a registered `BookSpec.root`; remove repository-root and sibling-book fallback discovery.
- [ ] Add CLI selection before subcommands:

```text
usaaio-tools --book book1 schedule-check
usaaio-tools --book book2 schedule-check
usaaio-tools --all prereq-check
```

- [ ] Define `--all` as registry-order iteration with book-qualified diagnostics and a nonzero exit when any book fails.
- [ ] Make Book 1 schedule, mock, PDF, overlap, inventory, and renderer consumers enumerate only `book1/`.
- [ ] Make Book 2 consumers enumerate only `book2/` and resolve Book 1 imports through `books.yaml`.
- [ ] Update the pre-merge guard to detect collisions inside each registered root and reject forbidden legacy roots.
- [ ] Update CI to run registry validation, each book independently, cross-book imports, aggregate reports, and legacy-path rejection.
- [ ] Assert root legacy paths are absent, are not symlinks, and cannot be recreated without failing CI.
- [ ] Search for forbidden literals:

```bash
rg -n '(^|["'"'` ])(units|curriculum|mocktests|reference)/|Path\("syllabus\.md"\)' \
  tools scripts tests
```

Expected: no active producer or consumer depends on a legacy root path, and every existing Book 1 check is green from `book1/` before the atomic commit.

- [ ] Run the complete existing pytest suite, all Book 1 CLI checks, registry/import checks, generated-document freshness, PDF build, and both CLI smoke routes.
- [ ] Commit:

```bash
git status --short
git add -A -- books.yaml book1 book2 syllabus.md curriculum units mocktests reference \
  tools scripts tests docs .gitignore
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
- [ ] Assert the same 19 units, 149 concepts, 437 practices, 69 lesson sessions, 40 schedule weeks, and `r1-001` assessment namespace.
- [ ] Compare every Book 1 manifest and notebook blob hash under `4cc3894:units/` with its `book1/units/` destination; the move may change paths but not notebook or manifest bytes.
- [ ] Build Book 1 PDFs and assert the same source notebook set and output count.
- [ ] Run Book 1 solution execution, answer-key, hygiene, prerequisite, coverage, schedule, overlap, PDF, and renderer checks.
- [ ] Commit:

```bash
git add book1/curriculum book1/docs docs/audits tests
git commit -m "test: prove Book 1 cutover equivalence"
```

## Task 4 — Implement the independent Book 2 schedule route

**Files:**

- Create: `tests/fixtures/two-books-valid/`
- Modify: `tools/checks/schedule.py`
- Modify: `tools/render_course_structure.py`
- Modify: `tools/cli.py`
- Modify: `scripts/ci-local.sh`
- Test: `tests/test_book2_schedule.py`
- Test: `tests/test_schedule.py`

- [ ] Extend the existing schedule checker and course-structure renderer as book-parameterized APIs; do not create parallel Book 2 checker or renderer implementations.
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
- Create: `scripts/generate_attention_data.py`

- [ ] The statement author creates the bridge, five lessons, overview, review, generator, and all 24 final student statements without solution outlines.
- [ ] Every path and identifier matches the content and evidence tables above.
- [ ] Create the manifest only after all declared statement-side paths exist.
- [ ] Record `compute.policy: cpu`, seed `20260808`, exact minutes, sessions, imports, concept tags, and solution paths.
- [ ] Run hygiene, manifest, import, coverage-tag, time-budget, and lesson-order checks without executing student notebooks.
- [ ] Commit:

```bash
git add book2/units/B2-019-attention-transformers
git commit -m "feat: teach attention and Transformer mechanics"
```

## Task 6 — Blind-solve all 24 practices

**Files:**

- Create: `book2/units/B2-019-attention-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`

- [ ] Dispatch a separate fresh Sol session with only the committed statements and no author outline.
- [ ] Require fixed probes, explicit tolerances, pinned variables, and a final `### Answer check` in every solution.
- [ ] Execute all solutions fresh in deterministic sorted order.
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

- [self] Pending amended-plan review.
- [sol] Pending amended-plan review.
- [glm] Pending amended-plan review.
- [fable] Pending amended-plan review.

The earlier `[deepseek]` round reviewed the superseded shared-root plan and provides no verdict for this amendment.

## Content Review

Not started.

## Post-execution report

Not started.
