# Plan 030 — Book Editions (py4kids publication practice)

## Goal

Build every Book 1 and Book 2 PDF the way `../py4kids` builds its books.
Each book gets several versions (editions): a lean print student book, a full student book, an answer key, and a teacher's edition.
Each book also gets a syllabus, per-unit practice handouts, and per-mock-test papers and solutions.
The PDFs land in a gitignored `output/<book>/` tree documented by a committed `output/README.md`.

User directive (2026-10-10): "follow the ../py4kids practice and content structure to generate pdfs for book1 and book2, pdfs should have different versions".

## Branch and baseline

- Branch: `feature/plan-030-book-editions`, from `main` at 19d18e6 (Plan 024 merged; Book 2 complete).
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.
- Reference implementation (read-only): `../py4kids` at 05d700f, especially:
  - `tools/publish.py` (`EDITIONS`, edition markers, Quarto project generation);
  - `tools/publish_audit.py`, `tools/publish_output.py`, `tools/books.py` (`publication_config_errors`);
  - `tools/publish_theme/` (`_quarto.yml`, `theme.tex`, `panels.lua`) and `tools/pdf_templates/`;
  - `scripts/build-book.sh`, `scripts/build-pdf.sh`, and `output/README.md`;
  - `docs/designs/010-publication-for-every-book.md`;
  - `python-concepts/{publication.yaml,front-matter/,back-matter/}`.

## Decisions

**D1. The content structure follows py4kids.**
Each book root gains:

- `<book>/publication.yaml`: the per-book publication config. It holds the chapter order, the unit running heads (for titles over 32 characters), the mock tests included in the Teacher's Edition, and the audit settings.
- `<book>/front-matter/`: `preface.md`, `how-to-use.md`, `for-teachers.md`, and `answer-key-intro.md`.
- `<book>/back-matter/`: `notation.md` (the math notation and symbol reference, which takes the place of py4kids' quick reference) and `glossary.md` (the defined terms of that book's concepts).

`books.yaml` gains `title`, `subtitle`, and `publication: true` for both books.
The titles are:

- Book 1: "Machine Learning for the AI Olympiad", subtitle "Round 1: Foundations, Models, and Practice".
- Book 2: "Deep Learning for the AI Olympiad", subtitle "Round 2: Transformers, Generative Models, and Open-Ended Modeling".

`tools/books.py` validates the new fields and `publication.yaml`, the way py4kids' `publication_config_errors` does.
The tools key on the `publication` flag, never on book ids.

**D2. Four editions, with py4kids names and usaaio semantics.**
`tools/publish.py` defines `EDITIONS` with the same four names.
Each PDF is `output/<book>/<book>-<edition>.pdf`.
If D8 splits an edition into volumes, the PDFs are `<book>-<edition>-vol<N>.pdf` instead.

**Selected answers** are defined by `publication.yaml` `student_answers:`, a manifest selector.
The default for both books is `{set: A}`: the Set A fundamentals practices (`docs/unit-standards.md`).
Sets B (exam register) and C (integration and challenge) stay answer-free outside the Teacher's Edition.
This replaces py4kids' odd-numbered rule, which has no meaning here.

| Edition | Label | Body |
|---|---|---|
| `student-print` | Student Book — Print Edition | Front matter, then for each unit: the overview (`lesson.ipynb`), the lessons (`lessons/*.ipynb`), the review (`review.ipynb`), and the practice statements. Practice notebooks print their markdown cells only, plus a one-line "Practice file: `units/<unit>/practice/pNN.ipynb`" pointer. Back matter. No answers of any kind (see D3 on `<details>`). |
| `student` | Student Book — Full Edition | Like print, but practice notebooks print every cell, including starter code. Adds an appendix, "Answers to Checkpoints and Selected Practice". For each unit it has the `<details>` checkpoint and review answers, then the selected-answer solutions. Each selected practice and each checkpoint points to its answer. |
| `answer-key` | Answer Key | A short intro, then one chapter per unit: the selected-answer solutions (the practice title, then the solution notebook's cells). |
| `teacher` | Teacher's Edition | The full student book plus `for-teachers.md`. `<details>` answers appear inline as a labelled "Answers" panel. Every practice is followed by its full solution. A final part holds every mock test listed in `publication.yaml`: the paper (D4 order), then `solutions/answers.md`, `rubric.md`, and `solutions/pNN_solution.ipynb` in problem order. |

Student editions read a `*_solution.ipynb` file only through the selected-answers path.
They never read mock-test material.
Edition-specific front-matter text uses py4kids' `<!-- edition: NAME -->` … `<!-- /edition -->` markers, filtered by the same rules: an unknown, nested, stray or unclosed marker fails the build.

**D3. Rendering follows the py4kids engine, with math enabled.**
`tools/publish.py` converts notebooks to Quarto chapters without executing them (`execute: enabled: false`).
It generates one Quarto book project per edition (and per volume) under `<book>/build/publish/<edition>/`.
`scripts/build-book.sh --book <id>` renders the editions in parallel, each with its own TeX and Quarto caches.
`BOOK_BUILD_PARALLEL=0` makes the renders sequential.
It runs two LaTeX draft-mode audit passes, then copies the PDFs to `output/<book>/`.

The theme copies py4kids':

- lualatex and `scrbook` on a 7 × 10 in page, with wrapped code and a TOC to depth 2;
- Atkinson Hyperlegible and Fira Mono with DejaVu fallback. Here they resolve from TeX Live through luaotfload by font name, not through fontconfig; Task 3 verifies this.

The deviations from py4kids:

- **Math:** `tex_math_dollars` stays on, because every lesson uses `$…$`. Raw `\begin{align}` blocks in markdown are passed through and spot-checked.
- **Index:** the index entries are the glossary terms. Each term is indexed at the start of the unit chapter that introduces its concept (coverage map). The editions with an index are `student-print`, `student`, and `teacher`.
- **Unit titles:** `publication.yaml` `chapters:` entries carry an explicit `title` and an optional `head`, for example `- {unit: C3-gradient-descent, title: "Optimization by Gradient Descent"}`. Manifests have no titles, and the overview H1s are inconsistent. The audit checks that the unit set matches the live units; titles come only from the config.
- **`<details>` answers:** 74 lesson and review notebooks hide checkpoint and self-quiz answers in `<details><summary>…</summary>…</details>`. Pandoc would print their bodies inline. The publisher therefore parses every `<details>` block in a markdown cell:
  - in `student-print`, it replaces the block with one line: "Answers: open this notebook, or see the Teacher's Edition";
  - in `student`, it replaces it with a reference, and the body moves to the answers appendix;
  - in `teacher`, it renders the body inline in an "Answers" panel.

  An unclosed or nested `<details>` fails the build.
- **Open answer sections** get the same three-edition treatment as `<details>` bodies (amendment, 2026-10-10; Task 2 author finding). Many lessons print checkpoint answers openly under a heading, so the rule also covers:
  - any markdown heading matching `(?i)^#+\s*(collected\s+)?((checkpoint|self-quiz|quiz)\s*\d*\s+)?answers\b`, which includes "Answers (open only when done)";
  - the section under such a heading, up to the next heading of the same or higher level, or the end of the notebook.

  The audit's fingerprint and provenance rules treat these bodies like `<details>` bodies.
  Each block gets a stable label of the form `<unit>-<notebook stem>-d<ordinal>`, so the appendix cross-references are deterministic.

The publisher strips every cell output during conversion. Twenty-three notebooks (8 lessons, 15 solutions) carry committed outputs; none are printed. The PDFs show code without outputs, and a converter test plants an output cell.
Executing notebooks for the PDFs is out of scope.
Figures referenced by relative path are copied into the Quarto project.

**D4. Handouts, syllabus, and mock-test PDFs follow py4kids' `build-pdf.sh` role.**
`scripts/build-pdf.sh --book <id>` keeps its `--list-inputs` contract and the containment protections: the noncanonical root and symlinks.
It renders from the publisher's shared converter output, so D3's `<details>` handling and output stripping apply; it never uses pandoc's native ipynb reader. It compiles through lualatex with a kept log, as py4kids does, and writes:

- `output/<book>/syllabus.pdf` from `<book>/docs/course-structure.md`, the readable course structure. `syllabus.md`'s canonical YAML block is not reader-facing.
- `output/<book>/handouts/<unit>.pdf`: one handout per unit, with that unit's practice statement notebooks in order, and `<details>` handled as in `student-print`. Book 1 gains these per-unit handouts.
- `output/<book>/mocktests/<test>-paper.pdf`: `test.md`, then the items in `manifest.yaml` problem order. Each item's `theory/pNN.md` precedes its `problems/pNN.ipynb` (r2-001 interleaves them). Several items share a file, so each source is rendered once, at its first occurrence in manifest order. The same rule applies to the solutions PDF and to the teacher's mock part. A test covers repeated file references.
- `output/<book>/mocktests/<test>-solutions.pdf`: `solutions/answers.md`, `rubric.md` (root), and `solutions/pNN_solution.ipynb` in problem order. This is the real layout of both `r1-001` and `r2-001`, and the tests use both.

Each script owns and replaces only its own files in `output/<book>/`, as in py4kids.
`<book>/build/` keeps the intermediate files.
The per-source build outputs and the exact-cardinality check are replaced by this contract.
`docs/designs/000-project-design.md` §3.8 ("Book 1 mock tests and every live Book 2 unit's student-facing collection") and the line on what Quarto writes under `<book>/build/` are updated to say this.
The current Quarto/typst path in `build-pdf.sh` is removed, along with its `.gitignore` cleanup and `test_book2_pdf_build_removes_only_new_quarto_gitignores`, so `build-pdf.sh` keeps a single renderer (the editions still render through Quarto, as in py4kids). That renderer is pandoc to `.tex` to lualatex, as in py4kids.
Design 000 is not a governance file.

**D5. The audit.**
`tools/publish_audit.py` (`python -m tools.publish_audit --book <id>`) checks each built edition's generated project, `.tex`, and log:

1. **Chapters.** The publisher writes `scope.json` into each generated project: `full`, or the explicit unit and mock-test lists of a scoped check. The audit takes the expected set from the build invocation, never from `scope.json` alone, and fails if the two disagree.
   - In a full build, every live unit (a `manifest.yaml` is present) appears as a chapter, in `publication.yaml` order. The teacher's mock part lists every mock test in `publication.yaml`.
   - In a scoped check, exactly the requested units and mock tests appear, in config order.
   - In either case, every unit in scope with a selected practice appears in the answer key.
   - A test covers a scoped project that is missing a requested unit, and a full build that is missing a live unit.
2. **Source isolation.**
   - Chapter lists:
     - no student edition lists a solution notebook outside the selected answers;
     - no student edition lists any mock-test material;
     - the `answer-key` lists only selected solutions.
   - Content check (this plan's own design; py4kids' `solution_leak` compares whole hidden cells instead): every student edition's generated chapter files are scanned for fingerprints. The fingerprints are normalized lines of 40 or more characters that do not occur in the matching statement source. They come from:
     - (a) every solution notebook's cells;
     - (b) every mock `solutions/` file and every `rubric.md`;
     - (c) every `<details>` body. These are fingerprinted against the source notebook with its `<details>` bodies removed; otherwise every body line would match its own source.

     A fingerprint found anywhere in `student-print`, or outside the answers appendix in `student`, is an error.
     This is defense in depth.
   - Structural provenance check (primary): the publisher writes a sidecar `provenance.json` for each generated chapter. It lists every emitted block's source (file, cell index, and kind: markdown, code, or `<details>` body). The audit holds its own rule table of allowed blocks per (edition, chapter); it never imports the publisher's edition rules. A `<details>` body, for example, is allowed in `student` only in the answers-appendix chapter. Tests plant both a forged sidecar entry (a disallowed block that is declared) and an undeclared block in the chapter text.
     - The audit re-derives, from the sources and its own rule table, which blocks each edition may emit. Any other emitted block is an error, whatever its length.
     - It then checks that each chapter's text is exactly the concatenation of its declared blocks plus the publisher's fixed scaffolding (headings, pointers, panel wrappers). This catches short leaks such as `return 42` or a one-letter `<details>` answer.
     - Tests plant a short solution cell and a short `<details>` body.
3. **Glyphs.** A "Missing character" entry in any LaTeX log is an error (py4kids' `pdf_glyphs.py` rule). This covers every PDF either script builds: editions, syllabus, handouts, and mock papers and solutions.
4. **References.** Undefined references or labels in the draft-mode log are errors.
5. **Glossary.** The glossary is a superset of the concepts the book introduces. "Introduced" means the union of the live manifests' `concepts_taught`, excluding `book1:`-qualified ids; this is a superset of the coverage map's `shipped_concepts`. Each glossary entry carries `<!-- concept: <id> -->`. A scoped check limits this to the concepts the in-scope units introduce.
6. **Page counts** are recorded and produce warnings only.

**D6. CI routing (py4kids `ci_scope.py`, narrowed for cost).**
`scripts/ci-local.sh` runs `build-pdf.sh` for every book on every run.
It runs `build-book.sh` plus the audit for a book only when the change set touches that book's publication inputs:

- `<book>/publication.yaml` (except a change that only adds `chapters:` entries, which routes to the scoped check of the added units), `<book>/front-matter/`, or `<book>/back-matter/`;
- `tools/publish*.py`, `tools/publish_theme/`, `tools/books.py`, or `scripts/build-book.sh`;
- `books.yaml`, `pyproject.toml`, or `uv.lock`.

A unit-content change does not trigger the full multi-thousand-page renders. Instead it triggers a **unit-scoped edition check**:

- `build-book.sh --book <id> --units <changed units>` generates all four editions restricted to the changed units, plus front and back matter. It renders them into `<book>/build/publish-check/` and runs the full audit (D5 rules 1–6, in scoped form).
- A unit-content change means a change to anything under `<book>/units/<unit>/`.
- A change to `<book>/curriculum/coverage-map.yaml` (the source of index placement and glossary coverage) routes to a scoped check of every unit whose introduced concepts changed, plus the glossary audit. If the changed rows cannot be attributed to units, the full edition build runs. A change that alters no unit's introduced concepts (for example, prerequisite rows only) runs the glossary audit alone. The routing tests cover a coverage-map-only change.
- A mock-test change (anything under `<book>/mocktests/<test>/`) adds `--mocktests <changed tests>`. The scoped check then generates the teacher's mock part for exactly those tests, which can be zero units plus one or more mock tests. It audits that part and confirms that no student edition contains it. A test covers a mock-only change set.
- The check uses the same publisher code path, so a changed lesson's rendering, glyphs and leak isolation are validated before shipping. It costs about the pilot's per-unit time.

The full edition PDFs in `output/` are rebuilt by `--all-books` before any release. Between releases they can lag content, as py4kids' gitignored PDFs do; `output/README.md` says so.

`scripts/ci-local.sh --all-books` renders every edition and is the release gate. Task 6 runs it.
The change set is the union of the committed diff against the merge-base with `origin/main` and the staged, unstaged, and untracked files.
If `origin/main` or the merge-base is unavailable, every book renders (fail-safe).
An unrouted book prints `INFO build-book: <book> unchanged (change-routed)`, not `SKIP`, so `SKIP` keeps its AGENTS.md meaning.

**D7. `output/`.**
`.gitignore` gains `output/**/*.pdf`, `output/**/*.log`, and `output/**/*.tex`.
`output/README.md` is committed in the py4kids table format: the files of each book, what each is, and the script that makes it.
It lists PDFs only and has no GitHub-release section; a release stays out of scope.

**D8. Scale: the pilot, the budget, and volumes.**
py4kids' largest book is 32 notebooks and about 430K characters of source. Its editions run 410 to 922 pages and build in about 20 minutes.
usaaio Book 1 has 544 student-facing notebooks (about 2.3M characters) plus 437 solutions; Book 2 has 197 plus 148.
Before the full build, Task 3 runs a pilot: one Book 1 unit (C3) through all four editions. It records pages and seconds per edition and extrapolates to both books, and the numbers go in this plan.
The budget per edition PDF is at most 1,200 pages and at most 30 minutes of render time.
An edition projected over budget is split into volumes along `publication.yaml` `volumes:`. These are contiguous unit ranges along curriculum parts; Book 1 splits naturally into Foundations (F1–F7) and Core (C1–C12).
The audit and `output/README.md` follow the split.

## Implementation tasks

All tooling goes to Opus subagents (`AGENTS.md` dispatch); front and back matter goes to an Opus author.
Tests go in `tests/`, failing first where practical.

- [ ] **Task 1 — Registry and publication config.**
  - `tools/books.py` requires exact registry keys. The new keys are added to the accepted set, and the old-format registries built in test fixtures (`tests/test_book_isolation.py`, `tests/test_books.py`, and the others found by grep) are migrated or stay valid. The noncanonical-root and symlink protections are kept.
  - `books.yaml` gets `title`, `subtitle`, and `publication: true`.
  - Add `<book>/publication.yaml` for both books.
  - Add the `tools/books.py` loader and validation (`publication_config_errors`).
  - Tests cover:
    - a missing or unknown key;
    - a chapter list that differs from the live units;
    - a running head missing for a title over 32 characters;
    - a mock test listed but absent.
- [ ] **Task 2 — Front and back matter (Opus author).** Write four front-matter files and two back-matter files per book.
  - `how-to-use.md` maps the course folders: unit lessons, practice, solutions only for teachers, and mock tests.
  - `how-to-use.md` names the reading-page conventions of these notebooks.
  - Edition markers apply where the editions differ.
  - The glossary covers each concept the book introduces (`<book>/curriculum/coverage-map.yaml`); each entry is a bold term plus a definition of 2 lines or fewer.
  - Notation follows the lessons' symbols.
  - No past-paper text.
  - Semantic line breaks.
- [ ] **Task 3 — Publisher, theme, and `build-book.sh`.** It begins with the D8 pilot (C3, all four editions). The pilot's build input (a fixture, not an edit to C3) adds a scratch code cell containing `−`, `≈`, and `½` to prove the DejaVu fallback. The pilot also times one handout (C3) and extrapolates to all 25 units. If the always-on handouts would cost more than 5 minutes per CI run, handouts are routed like editions (changed units only, all under `--all-books`). The plan records the pilot numbers and the volume decision before the full build.
  - Build `tools/publish.py` (`EDITIONS`, `output_stem`, `filter_edition_blocks`, notebook-to-chapter conversion, project generation for each edition), `tools/publish_theme/`, `tools/publish_output.py`, and `scripts/build-book.sh`.
  - Unit tests cover:
    - edition-marker filtering, ported from py4kids' tests;
    - each edition's chapter list for a fixture book;
    - print practice cells being markdown-only;
    - the `student_answers` selector;
    - the `<details>` handling in each edition, using a planted `<details>` cell, plus unclosed and nested failures;
    - the mock-paper order against `manifest.yaml`, using the interleaved r2-001 layout;
    - the index entries;
    - the teacher's mock-test part.
- [ ] **Task 4 — `build-pdf.sh` rework.** Produce the syllabus, handouts, and mock-test paper and solutions PDFs into `output/<book>/` (D4). Migrate every test that pins the old contract in the same commit:
  - the `--list-inputs` set pinned in `tests/test_integration.py`;
  - the `build-pdf.sh` cases in `tests/test_book_isolation.py` and `tests/test_clean_checkout.py`.

  - Keep `--list-inputs` and the noncanonical-root and symlink containment protections.
  - Add a failing-log glyph test for one handout render.
  - Rewrite `tests/test_integration.py::test_plan019_task3_book1_pdf_sources_match_the_pinned_r1_set` (Book 1 now has handouts), the `--list-inputs` fingerprints and fake-quarto cardinality tests in `tests/test_book_isolation.py`, and the exact `ci-local.sh` line in `tests/test_integration.py`.
  - Update design 000 §3.8 (D4).
- [ ] **Task 5 — Audit, CI routing, `output/README.md`, and `.gitignore`.** Implement D5–D7. Add tests for:
  - each audit rule, with a planted solution chapter in a student edition, solution code planted inside an ordinary student unit chapter, a planted `<details>` body, a planted `rubric.md` line, a `scope.json` that disagrees with the invocation scope, and a planted "Missing character" log line;
  - the CI routing decision, as a pure function over a list of changed paths. It must cover staged, unstaged, and untracked changes, and fall back to rendering everything when `origin/main` is missing. It also covers a unit-content change that routes to a unit-scoped check of exactly the changed units.
- [ ] **Task 6 — Verification phase.**
  - Run `scripts/ci-local.sh --all-books` on a clean tip, and run it once more without `--all-books` after cleaning `__pycache__`.
  - For each book, record in the post-execution report:
    - each edition's page count and render time;
    - the handout, syllabus, and mock PDFs produced.
  - Visually spot-check rendered pages with `pdftoppm -png -r 60`:
    - the title page, a TOC page, and a math-heavy lesson page per book, including one raw `\begin{align}` block;
    - a `<details>` checkpoint in `student-print`, `student` (appendix), and `teacher` (panel);
    - a practice page in `student-print` versus `student`;
    - an answer-key page;
    - a Teacher's Edition mock-test page.
  - Fix any overflow, broken math, or missing glyph found.
  - The gate reviewers receive these page images.
- [ ] **Task 7 — Post-execution report, `TODO.md`, PR, `pre-merge-guard --pr`, and squash-merge.**

## Out of scope

- Executing notebooks to put outputs or figures in the PDFs.
- A website, EPUB, or GitHub release of the PDFs.
- New lessons, practice, or mock-test content beyond the front and back matter.
- Changing any answer key, statement, or solution.
- Governance files (`AGENTS.md`, `docs/development-workflow.md`, `docs/content-review-gate.md`, `docs/architecture/decisions.md`).
- The verification-phase rule is satisfied by Task 6. This plan ships no new units or mock tests; its content (front and back matter) goes through the content gate.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Review 1 — self (2026-10-10)
- **Verdict**: Approve with suggestions.
1. `[FIXED]` Should Fix: `scripts/verify-staged-scope.py` (`pre-merge-guard`) rejects committed paths in its protected categories. These include any path containing `token`, `/build/` or `/students/`. → Every new committed path (test fixtures in particular) must avoid them. Fixture books are built under `tmp_path`, never under a committed `build/` directory.
2. `[FIXED]` Should Fix: scale. 1,326 unit notebooks feed the editions, so the Teacher's Edition may run to thousands of pages. → Task 6 records each edition's render time and page count. If an edition fails a LaTeX capacity limit, the publisher may split it into volumes (`<book>-<edition>-vol<N>.pdf`), and the audit and `output/README.md` follow the split.
3. `[FIXED]` Nit: `tests/test_integration.py` asserts the exact `ci-local.sh` build-pdf line, and `tests/test_book_isolation.py` and `tests/test_clean_checkout.py` exercise `build-pdf.sh`. → Tasks 4 and 5 update them to the new contract in the same commit as the script change.

### Review 1 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: mock answers live at `solutions/answers.md`. → Response: D2 and D4 corrected; tests use both real layouts.
2. `[FIXED]` Must Fix: a chapter-list leak audit is too narrow. → Response: D5 adds a generated-content fingerprint check; a test plants solution code in a student chapter.
3. `[FIXED]` Must Fix: the registry and PDF contract tests need a wider migration. → Response: Tasks 1 and 4 name the fixture registries, the pinned `--list-inputs` set, and the isolation and clean-checkout cases; root and symlink protections are kept.
4. `[FIXED]` Should Fix: glyph checks on every PDF. → Response: D5 rule 3 covers every PDF; build-pdf compiles through lualatex with a kept log; a failing-log test was added.
5. `[FIXED]` Should Fix: fail-safe routing. → Response: D6 takes the union of the committed diff and staged, unstaged and untracked changes, and renders everything when `origin/main` is missing; tests cover these cases.

### Review 1 — Fable (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: `<details>` answers would leak into the student editions. → Response: D3 adds a `<details>` policy for each edition; D5 adds a fingerprint check on `<details>` bodies; tests were added.
2. `[FIXED]` Must Fix: scale and CI time were unmeasured. → Response: D8 adds the C3 pilot, a budget of ≤ 1,200 pages and ≤ 30 min per PDF, and volume splitting. D6 narrows the routing to publication inputs, and `--all-books` is the release gate.
3. `[FIXED]` Must Fix: design 000 §3.8 and the pinned tests. → Response: D4 and Task 4 name the design edits and every test that gets rewritten.
4. `[FIXED]` Should Fix: mock paths and order. → Response: `solutions/answers.md` and `solutions/pNN_solution.ipynb`; the paper follows manifest problem order with theory interleaved; a test was added.
5. `[FIXED]` Should Fix: odd-numbered answers are meaningless here. → Response: the `student_answers: {set: A}` selector in `publication.yaml`.
6. `[FIXED]` Should Fix: the index had no source. → Response: glossary terms, indexed at the introducing unit.
7. `[FIXED]` Should Fix: font resolution. → Response: fonts come from TeX Live through luaotfload; the pilot includes a glyph-fallback cell.
8. `[FIXED]` Should Fix: audit tests. → Response: planted `<details>` and `rubric.md` cases were added.
9. `[FIXED]` Nit: the change-routed message is `INFO`, not `SKIP`.
10. `[FIXED]` Nit: `.gitignore` covers `output/**/*.log` and `*.tex`; the README lists PDFs only.
11. `[FIXED]` Nit: glossary entries are 2 lines or fewer, and the audit checks that the glossary covers the introduced concepts.
12. `[FIXED]` Nit: a raw `align` block was added to the spot-check list.

### Review 1 — self, follow-up
- Self findings 1–3 are `[FIXED]`:
  - protected-path avoidance is now a constraint on every new committed path, and the Task 1–5 implementers are told so;
  - D8 handles scale;
  - Task 4 names the test migrations.

### Review 2 — Fable (2026-10-10)
- **Verdict**: Approve with nits. All round-1 fixes were verified against the tree.
1. `[FIXED]` Should Fix: rule 2(c) was vacuous. → Response: `<details>` bodies are fingerprinted against the source with its bodies removed; the provenance check (Sol round 2) is primary.
2. `[FIXED]` Should Fix: unit titles had no source. → Response: `chapters:` entries carry `title` and `head`.
3. `[FIXED]` Should Fix: mock deduplication. → Response: first occurrence wins (same as Sol round 2, finding 3).
4. `[FIXED]` Should Fix: 23 notebooks carry outputs. → Response: the publisher strips all outputs, with a test.
5. `[FIXED]` Nits 5–11:
   - Set C is named.
   - The fingerprint design is attributed to this plan.
   - The design-000 quote is exact.
   - The pilot glyph cell is a fixture.
   - Handout cost is measured, with routing if it runs over 5 minutes.
   - `<details>` labels are stable.
   - Only one renderer remains (the typst path is removed).

### Review 2 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: content edits never re-render the editions. → Response: D6 adds a unit-scoped edition check (`build-book.sh --units`) that renders and audits all four editions for exactly the changed units on every run that touches them.
2. `[FIXED]` Must Fix: the ≥ 40-character fingerprints miss short leaks. → Response: D5 adds a structural provenance check (a sidecar `provenance.json`, re-derived allowed blocks, exact-concatenation check); the fingerprints remain as defense in depth; tests plant short leaks.
3. `[FIXED]` Should Fix: mock file deduplication. → Response: each file is rendered once, at its first occurrence in manifest order, in the paper, the solutions and the teacher part; a test was added.

### Review 3 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: mock-test edits had no edition check. → Response: D6 adds `--mocktests` to the scoped check, so a mock-only change renders and audits the teacher's mock part; a test was added.
2. `[FIXED]` Should Fix: the chapter audit ignored scope. → Response: D5 rule 1 uses an invocation-supplied scope cross-checked against `scope.json`, with distinct full and scoped expectations and tests for both.

### Review 3 — Fable (2026-10-10)
- **Verdict**: Approve with nits.
1. `[FIXED]` Should Fix: scoped runs vs. whole-book rules. → Response: rule 1 is scope-aware (Sol round 3, finding 2); rule 5 is limited to the in-scope units' concepts.
2. `[FIXED]` Should Fix: mock-only interface. → Response: `--mocktests` with zero units; a routing test (Sol round 3, finding 1).
3. `[FIXED]` Should Fix: new-unit plans would pay full renders. → Response: a change that only adds `chapters:` entries routes to the scoped check of the added units.
4. `[FIXED]` Nits 4–7:
   - The audit holds its own rule table, with forged-sidecar and undeclared-block tests.
   - Handouts use the shared converter.
   - The renderer wording is clarified.
   - Allowed blocks are derived per (edition, chapter).

### Review 4 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject. Round-3 findings were confirmed as fixed.
1. `[FIXED]` Must Fix: coverage-map edits were unrouted. → Response: D6 routes `coverage-map.yaml` changes to a scoped check of the affected units plus the glossary audit (full build if unattributable); a routing test was added.

### Review 4 — Fable (2026-10-10)
- **Verdict**: Approve with nits. All round-3 fixes were confirmed.
1. `[FIXED]` Nits 1–4: the "own rule table" wording; the sidecar sentence was moved; the scoped audit is "D5 rules 1–6 in scoped form"; a scope-disagreement test was added.

### Review 5 — Fable (2026-10-10)
- **Verdict**: Approve.
1. `[FIXED]` Nit: a coverage-map change that alters no introductions runs the glossary audit alone.

### Review 5 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Approve. No findings.

**Gate result:** 3-way consensus at round 5 (self, Sol and Fable all approve; no open blockers). Implementation is authorized.

### Implementation amendments (self, 2026-10-10)
- The Task 2 author found that many lessons, and most Book 2 lessons, print checkpoint answers openly under answer headings. D3 now covers these open answer sections exactly like `<details>` bodies; the D2 rule "no answers in `student-print`" holds unchanged. This is within the existing D2/D3 intent, not a scope expansion.
- The glossary's source of introduced concepts is pinned to the manifests' `concepts_taught`.
- Task 6 spot-check (self, 2026-10-11): `book2-student-print` printed 220 inline checkpoint answers from B2-021–024. They are paragraphs beginning `**Collected answers.**`, which neither the heading rule nor the audit recognized.
  - The answer-region rule now also covers paragraphs beginning `**Collected answers.**` or `**Collected checkpoint answers.**`, in both the publisher and the audit.
  - The audit also fails on any unexplained `Collected answers` line in `student-print`.
  - Book 1 `**Answer C.**`-style lines are worked-example solutions, which are taught content, and are left unchanged.

### D8 pilot and volume decision (Task 3, 2026-10-11)
- **Pilot:** C3 fixture plus the glyph cell, sequential, warm caches.

  | Edition | Pages | Seconds |
  |---|---|---|
  | `student-print` | 59 | 54 |
  | `student` | 76 | 62 |
  | `answer-key` | 8 | 32 |
  | `teacher` | 96 | 81 |

  The `−`, `≈` and `½` glyph cell rendered with 0 missing characters.
- **Projection:**
  - Book 1: print about 975 pages, Student about 1,330, Teacher about 1,860.
  - Book 2: print about 400, Student about 480, Teacher about 850.
  - All under 30 minutes at about 0.5 s per page.
- **Handout:** C3 renders in about 7 s, so 25 handouts take about 3–4 minutes, under the 5-minute threshold. Handouts stay always-on. Task 4 must reuse the theme's DejaVu fallback (`→` is missing in the plain template).
- **Volumes:** the Book 1 Student Book and Teacher's Edition split into three volumes:
  - F1–F7: Foundations.
  - C1–C6 + C11: Core Machine Learning and Neural Networks.
  - C7–C10 + C12: Applied Models and Competition Practice.

  The Book 1 print edition (981 pages) and Answer Key stay single PDFs, and Book 2 is unsplit.
- **First full builds:** every PDF is under 1,200 pages and 30 minutes. The largest are Book 2 teacher (900 pages, 961 s) and Book 1 print (981 pages, 837 s).
- **Deviation:** markdown is read with `-raw_tex`. C10 `p12_solution.ipynb` lost its `\(` delimiters, so its `\frac` prints literally. That is recorded in `TODO.md` as an erratum and not fixed here (content is out of scope).

## Content Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).
Blind solving does not apply: this plan adds no problems. The reviewers instead fact-check the front and back matter, hunt for leaks in the student-facing PDFs, and inspect sampled page images.

### Review 1 — self (2026-10-11)
- **Spot-check:**
  - Book 2 print: title page, practice pages, self-quiz pointer.
  - Book 1: TOC.
  - Book 1 student vol 2: answers appendix.
  - Book 1 teacher vol 2: lesson page.
  - Book 1 answer key: a page.
  - Book 2 teacher: the r2-001 rubric with math.
- **Leak scan:** a `pdftotext` scan of both print editions found 220 `Collected answers.` paragraphs printed in Book 2.
- **Verdict**: Approve after the fix.
1. `[FIXED]` Must Fix: the paragraph-form answer leak. → Response: f4d8a89 updates the publisher and the audit and adds a safety net; `grep -c` now returns 0 and the audits pass.
2. `[WONTFIX]` Nit: Atkinson Hyperlegible's distinctive zero looks slashed in the TOC. This is the py4kids font choice and is kept for consistency.

### Review 1 — Sol, `gpt-6-sol` (2026-10-11)
- **Leak hunt:** no solution or rubric text in the print editions, the student unit chapters, sampled handouts, or the papers. Both audits are OK.
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the KL direction wording in the Book 2 notation and glossary. → Response: rephrased as "the extra expected log loss from using Q when the data follow P" (0c12bb8). A search of the B2-022 notebooks found no matching "of Q from P" wording, so no lesson erratum is needed.
2. `[FIXED]` Should Fix: how-to-use said answers print openly in the student books. → Response: the edition blocks of both books now describe the pointers, the appendix, and the panels (0c12bb8).

### Review 1 — Fable (2026-10-11)
- **Verified:**
  - front-matter facts and the glossary's coverage and attribution (scripted);
  - edition markers;
  - the leak hunt across all student-facing PDFs;
  - 47 page images: math, overflow, glyphs, appendix cross-references;
  - the volume semantics.
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the Index is missing and raw `\printindex` prints in 10 editions (`-raw_tex` escapes the bare TeX). → Response: a raw `{=latex}` block, a regression test, and an audit rule; the glossary entries are no longer indexed.
2. `[FIXED]` Should Fix: the print pointer names the Teacher's Edition. → Response: it now says "the answers appendix of the full Student Book".
3. `[FIXED]` Should Fix: the false publication claim. → Response: "The course files are at github.com/weiboz0/usaaio; ask your teacher for the Answer Key and the full Student Book." (0c12bb8).
4. `[FIXED]` Should Fix: cramped syllabus and paper tables. → Response: relative column widths in `publish_pdf.py`.
5. `[FIXED]` Nit: every index entry also listed the glossary page. → Response: covered by fix 1. (4a79fde: the index prints, audit rule `check_scaffold_tex`, `widen_tables`, and both books rebuilt with the audits OK.)
6. `[FIXED]` Nit: the practice-file path prefix. → Response: how-to-use says the paths are relative to the book folder.
7. `[FIXED]` Nit: the practice-header example. → Response: a real header (`constrained coding`).

## Post-execution report
