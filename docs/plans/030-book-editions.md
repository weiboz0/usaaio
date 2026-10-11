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

| Edition | Label | Body |
|---|---|---|
| `student-print` | Student Book — Print Edition | Front matter, then each unit's overview (`lesson.ipynb`), lessons (`lessons/*.ipynb`), review (`review.ipynb`), and practice statements. Practice notebooks print their markdown cells only, plus a one-line "Practice file: `units/<unit>/practice/pNN.ipynb`" pointer. Back matter. No answers. |
| `student` | Student Book — Full Edition | Like print, but practice notebooks print every cell, including starter code. Adds an "Answers to Selected Practice" appendix with the odd-numbered practice solutions. Each odd practice carries a reference to its answer. |
| `answer-key` | Answer Key | Short intro, then one chapter per unit with the odd-numbered practice solutions (the statement title, then the solution notebook's cells). |
| `teacher` | Teacher's Edition | The full student book, plus `for-teachers.md`. Each practice is followed by its full solution. A final part has every mock test from `publication.yaml`: the paper, then `answers.md`, `rubric.md`, and the solution notebooks. |

Student editions never read a `*_solution.ipynb` file except through the odd-numbered answers path.
They never read mock-test `solutions/` or `rubric.md`.
Edition-specific front-matter text uses py4kids' `<!-- edition: NAME -->` … `<!-- /edition -->` markers, filtered by the same rules (unknown, nested, stray or unclosed markers fail the build).

**D3. Rendering follows the py4kids engine, with math enabled.**
The pipeline:

- `tools/publish.py` converts notebooks to Quarto chapters without executing them (`execute: enabled: false`). It generates one Quarto book project per edition under `<book>/build/publish/<edition>/`.
- `scripts/build-book.sh --book <id>` renders the editions in parallel, each with its own TeX and Quarto caches. `BOOK_BUILD_PARALLEL=0` makes the renders sequential. It runs two LaTeX draft-mode audit passes, then copies the PDFs to `output/<book>/`.

The theme copies py4kids': lualatex, `scrbook`, a 7 × 10 in page, Atkinson Hyperlegible and Fira Mono with DejaVu fallback, wrapped code, a TOC to depth 2, and an index in the book editions.
One deliberate deviation: py4kids turns off `tex_math_dollars`; usaaio keeps it on, because every lesson uses `$…$` math.
Notebooks are committed without outputs, so the PDFs show code without outputs.
Executing notebooks for the PDFs is out of scope.
Figures referenced by relative path are copied into the Quarto project.
Lesson and practice cells keep their order; a cell tagged `hide-in-print`, if any exists, is dropped in `student-print` only.

**D4. Handouts, syllabus, and mock-test PDFs follow py4kids' `build-pdf.sh` role.**
`scripts/build-pdf.sh --book <id>` keeps the per-source rendering role and its `--list-inputs` contract. It writes:

- `output/<book>/syllabus.pdf`, from `<book>/docs/course-structure.md` (the readable course structure; `syllabus.md`'s canonical YAML block is not reader-facing).
- `output/<book>/handouts/<unit>.pdf`: one handout per unit, with that unit's practice statement notebooks concatenated in order (no solutions).
- `output/<book>/mocktests/<test>-paper.pdf`: `test.md`, the theory items, and the problem notebooks.
- `output/<book>/mocktests/<test>-solutions.pdf`: `answers.md`, `rubric.md`, and the solution notebooks.

Each script owns and replaces only its own files in `output/<book>/`, as in py4kids.
`<book>/build/` keeps the intermediate files.
The existing per-source build outputs and their exact-cardinality check may be replaced; their tests are updated to the new contract in the same task.

**D5. The audit.**
`tools/publish_audit.py` (`python -m tools.publish_audit --book <id>`) checks each built edition's generated project, `.tex`, and log:

1. Every live unit (`manifest.yaml` present) appears as a chapter, in `publication.yaml` order. In the answer key, every unit with an odd practice appears.
2. Source isolation:
   - No student edition's chapter list contains a solution notebook, except the odd-numbered answers in the `student` appendix.
   - No student edition contains mock-test material.
   - The `answer-key` contains only odd-numbered solutions.
3. A "Missing character" entry in the LaTeX log is an error. This is the py4kids `pdf_glyphs.py` rule.
4. Undefined references or labels in the draft-mode log are errors.
5. Page counts are recorded, but they produce warnings only.

**D6. CI routing follows py4kids.**
`scripts/ci-local.sh` step "PDF build" runs `build-pdf.sh` for every book on every run.
It runs `build-book.sh` plus the audit only for a book whose change set touches one of:

- that book root;
- `tools/`, `scripts/`, `books.yaml`, `pyproject.toml`, or `uv.lock`.

The change set is measured against `origin/main` (merge-base).
Otherwise CI prints `SKIP build-book: <book> unchanged`.
`scripts/ci-local.sh --all-books` forces every edition to render.
This SKIP is a permanent, change-routed skip, not a "plan unshipped" skip, and `output/README.md` says so.

**D7. `output/`.**
`.gitignore` gains `output/**/*.pdf`.
`output/README.md` is committed and follows the py4kids table format: each book's files, what each file is, and the script that makes it.
It has no GitHub-release section; publishing a release stays out of scope.

## Implementation tasks

All tooling goes to Opus subagents (`AGENTS.md` dispatch); front and back matter goes to an Opus author.
Tests go in `tests/`, failing first where practical.

- [ ] **Task 1 — Registry and publication config.**
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
  - The glossary covers each concept the book introduces (`<book>/curriculum/coverage-map.yaml`), one definition per line.
  - Notation follows the lessons' symbols.
  - No past-paper text.
  - Semantic line breaks.
- [ ] **Task 3 — Publisher, theme, and `build-book.sh`.**
  - Build `tools/publish.py` (`EDITIONS`, `output_stem`, `filter_edition_blocks`, notebook-to-chapter conversion, project generation for each edition), `tools/publish_theme/`, `tools/publish_output.py`, and `scripts/build-book.sh`.
  - Unit tests cover:
    - edition-marker filtering, ported from py4kids' tests;
    - each edition's chapter list for a fixture book;
    - print practice cells being markdown-only;
    - the odd-only answer selection;
    - the teacher's mock-test part.
- [ ] **Task 4 — `build-pdf.sh` rework.** Produce the syllabus, handouts, and mock-test paper and solutions PDFs into `output/<book>/` (D4). Update the existing build-pdf tests to the new contract, and keep `--list-inputs`.
- [ ] **Task 5 — Audit, CI routing, `output/README.md`, and `.gitignore`.** Implement D5–D7. Add tests for:
  - each audit rule, with a planted solution chapter in a student edition and a planted "Missing character" log line;
  - the CI routing decision, as a pure function over a list of changed paths.
- [ ] **Task 6 — Verification phase.**
  - Run `scripts/ci-local.sh --all-books` on a clean tip, and run it once more without `--all-books` after cleaning `__pycache__`.
  - For each book, record in the post-execution report:
    - each edition's page count and render time;
    - the handout, syllabus, and mock PDFs produced.
  - Visually spot-check rendered pages with `pdftoppm -png -r 60`:
    - the title page, a TOC page, and a math-heavy lesson page per book;
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

## Content Review

## Post-execution report
