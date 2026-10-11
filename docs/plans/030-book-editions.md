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
Set B, the exam register, stays answer-free outside the Teacher's Edition.
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
- **`<details>` answers:** 74 lesson and review notebooks hide checkpoint and self-quiz answers in `<details><summary>…</summary>…</details>`. Pandoc would print their bodies inline. The publisher therefore parses every `<details>` block in a markdown cell:
  - in `student-print`, it replaces the block with one line: "Answers: open this notebook, or see the Teacher's Edition";
  - in `student`, it replaces it with a reference, and the body moves to the answers appendix;
  - in `teacher`, it renders the body inline in an "Answers" panel.

  An unclosed or nested `<details>` fails the build.

Notebooks are committed without outputs, so the PDFs show code without outputs.
Executing notebooks for the PDFs is out of scope.
Figures referenced by relative path are copied into the Quarto project.

**D4. Handouts, syllabus, and mock-test PDFs follow py4kids' `build-pdf.sh` role.**
`scripts/build-pdf.sh --book <id>` keeps its `--list-inputs` contract and the containment protections: the noncanonical root and symlinks.
It compiles through lualatex with a kept log, as py4kids does, and writes:

- `output/<book>/syllabus.pdf` from `<book>/docs/course-structure.md`, the readable course structure. `syllabus.md`'s canonical YAML block is not reader-facing.
- `output/<book>/handouts/<unit>.pdf`: one handout per unit, with that unit's practice statement notebooks in order, and `<details>` handled as in `student-print`. Book 1 gains these per-unit handouts.
- `output/<book>/mocktests/<test>-paper.pdf`: `test.md`, then the items in `manifest.yaml` problem order. Each item's `theory/pNN.md` precedes its `problems/pNN.ipynb` (r2-001 interleaves them).
- `output/<book>/mocktests/<test>-solutions.pdf`: `solutions/answers.md`, `rubric.md` (root), and `solutions/pNN_solution.ipynb` in problem order. This is the real layout of both `r1-001` and `r2-001`, and the tests use both.

Each script owns and replaces only its own files in `output/<book>/`, as in py4kids.
`<book>/build/` keeps the intermediate files.
The per-source build outputs and the exact-cardinality check are replaced by this contract.
`docs/designs/000-project-design.md` §3.8, the Book 2 "book-local collection" sentence, and the line on what Quarto writes under `<book>/build/` are updated to say this.
Design 000 is not a governance file.

**D5. The audit.**
`tools/publish_audit.py` (`python -m tools.publish_audit --book <id>`) checks each built edition's generated project, `.tex`, and log:

1. **Chapters.** Every live unit (a `manifest.yaml` is present) appears as a chapter, in `publication.yaml` order. In the answer key, every unit with a selected practice appears.
2. **Source isolation.**
   - Chapter lists:
     - no student edition lists a solution notebook outside the selected answers;
     - no student edition lists any mock-test material;
     - the `answer-key` lists only selected solutions.
   - Content check (py4kids' `publish_audit.py` approach): every student edition's generated chapter files are scanned for fingerprints. The fingerprints are normalized lines of 40 or more characters that do not occur in the matching statement source. They come from:
     - (a) every solution notebook's cells;
     - (b) every mock `solutions/` file and every `rubric.md`;
     - (c) every `<details>` body.

     A fingerprint found anywhere in `student-print`, or outside the answers appendix in `student`, is an error.
3. **Glyphs.** A "Missing character" entry in any LaTeX log is an error (py4kids' `pdf_glyphs.py` rule). This covers every PDF either script builds: editions, syllabus, handouts, and mock papers and solutions.
4. **References.** Undefined references or labels in the draft-mode log are errors.
5. **Glossary.** The glossary is a superset of the concepts the book introduces.
6. **Page counts** are recorded and produce warnings only.

**D6. CI routing (py4kids `ci_scope.py`, narrowed for cost).**
`scripts/ci-local.sh` runs `build-pdf.sh` for every book on every run.
It runs `build-book.sh` plus the audit for a book only when the change set touches that book's publication inputs:

- `<book>/publication.yaml`, `<book>/front-matter/`, or `<book>/back-matter/`;
- `tools/publish*.py`, `tools/publish_theme/`, `tools/books.py`, or `scripts/build-book.sh`;
- `books.yaml`, `pyproject.toml`, or `uv.lock`.

Ordinary unit content changes do not trigger the multi-thousand-page renders.
Their leak and glyph risks are still covered:

- `build-pdf.sh` renders every unit's handouts on every run;
- the publisher's source-isolation unit tests run on every run.

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
- [ ] **Task 3 — Publisher, theme, and `build-book.sh`.** It begins with the D8 pilot (C3, all four editions). The pilot includes a code cell containing `−`, `≈`, and `½` to prove the DejaVu fallback. The plan records the pilot numbers and the volume decision before the full build.
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
  - each audit rule, with a planted solution chapter in a student edition, solution code planted inside an ordinary student unit chapter, a planted `<details>` body, a planted `rubric.md` line, and a planted "Missing character" log line;
  - the CI routing decision, as a pure function over a list of changed paths. It must cover staged, unstaged, and untracked changes, and fall back to rendering everything when `origin/main` is missing. It also covers an ordinary unit-content change that does not trigger the editions.
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

## Content Review

## Post-execution report
