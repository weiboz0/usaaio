# Generated PDFs

This folder collects every PDF the repository builds (Plan 030).
The PDFs are built artifacts: git ignores them (`output/**/*.pdf`, `*.log` and `*.tex` in `.gitignore`), and only this README is committed.
Rebuild them with the scripts below; `scripts/ci-local.sh` runs both.

`build-pdf.sh` runs for every book on every CI run.
A book's editions (`build-book.sh`, then `python -m tools.publish_audit`) render only when the change set touches that book's publication inputs: its `publication.yaml`, `front-matter/` or `back-matter/`, the publisher (`tools/publish*.py`, `tools/publish_theme/`, `tools/books.py`, `scripts/build-book.sh`), `books.yaml`, `pyproject.toml` or `uv.lock`.
A change to one unit or mock test renders a scoped check of just that unit or test into `<book>/build/publish-check/` and leaves these PDFs alone; an unchanged book prints `INFO build-book: <book> unchanged (change-routed)`.
`scripts/ci-local.sh --all-books` renders every book's editions and is the release gate.
Between releases the edition PDFs here can therefore lag the content.

Each script owns its own files and replaces only those, so running one never deletes the other's PDFs.
`<book>/build/` keeps the intermediate files (Quarto projects, LaTeX logs, TeX).
Folders and PDF file names use the book id from `books.yaml`; the PDFs themselves show each book's title.

"Selected answers" are the Set A (fundamentals) practices, set by `student_answers:` in each book's `publication.yaml`.

## `output/book1/` — Machine Learning for the AI Olympiad (Round 1)

| File | What it is | Made by |
|---|---|---|
| `book1-student-print.pdf` | Student Book — Print Edition: lessons, reviews and practice statements (markdown only, with a pointer to each practice file); no answers of any kind | `scripts/build-book.sh --book book1` |
| `book1-student-vol1.pdf` | Student Book — Full Edition, Volume 1: Foundations and First Models (units 01–08: F1–F5, C1–C3), with starter code and an appendix of checkpoint answers and selected-practice solutions | `scripts/build-book.sh --book book1` |
| `book1-student-vol2.pdf` | Student Book — Full Edition, Volume 2: Practice, Embeddings, and Neural Networks (units 09–14: C4, C5, C6, F6, C7, F7) | `scripts/build-book.sh --book book1` |
| `book1-student-vol3.pdf` | Student Book — Full Edition, Volume 3: Training, Deep Models, and Competition Practice (units 15–19: C8–C12) | `scripts/build-book.sh --book book1` |
| `book1-answer-key.pdf` | Answer Key: the selected-practice solutions, one chapter per unit | `scripts/build-book.sh --book book1` |
| `book1-teacher-vol1.pdf` | Teacher's Edition, Volume 1: Foundations and First Models, with every answer inline and every practice solution | `scripts/build-book.sh --book book1` |
| `book1-teacher-vol2.pdf` | Teacher's Edition, Volume 2: Practice, Embeddings, and Neural Networks | `scripts/build-book.sh --book book1` |
| `book1-teacher-vol3.pdf` | Teacher's Edition, Volume 3: Training, Deep Models, and Competition Practice, ending with the `r1-001` mock test, its answers, rubric and solutions | `scripts/build-book.sh --book book1` |
| `syllabus.pdf` | The Round 1 course structure (`book1/docs/course-structure.md`) | `scripts/build-pdf.sh --book book1` |
| `handouts/<unit>.pdf` | One practice handout per unit: its practice statement notebooks, without answers | `scripts/build-pdf.sh --book book1` |
| `mocktests/r1-001-paper.pdf` | Mock test `r1-001`: `test.md`, then each problem file in manifest order | `scripts/build-pdf.sh --book book1` |
| `mocktests/r1-001-solutions.pdf` | Mock test `r1-001`: the answer key, rubric and solution notebooks | `scripts/build-pdf.sh --book book1` |

`build-book.sh` replaces `book1-*.pdf` (every edition is `<book>-<edition>[-vol<N>].pdf`); `build-pdf.sh` replaces `syllabus.pdf`, `handouts/` and `mocktests/`.

## `output/book2/` — Deep Learning for the AI Olympiad (Round 2)

| File | What it is | Made by |
|---|---|---|
| `book2-student-print.pdf` | Student Book — Print Edition: lessons, reviews and practice statements (markdown only, with a pointer to each practice file); no answers of any kind | `scripts/build-book.sh --book book2` |
| `book2-student.pdf` | Student Book — Full Edition: with starter code and an appendix of checkpoint answers and selected-practice solutions | `scripts/build-book.sh --book book2` |
| `book2-answer-key.pdf` | Answer Key: the selected-practice solutions, one chapter per unit | `scripts/build-book.sh --book book2` |
| `book2-teacher.pdf` | Teacher's Edition: every answer inline, every practice solution, and the `r2-001` mock test with its answers, rubric and solutions | `scripts/build-book.sh --book book2` |
| `syllabus.pdf` | The Round 2 course structure (`book2/docs/course-structure.md`) | `scripts/build-pdf.sh --book book2` |
| `handouts/<unit>.pdf` | One practice handout per unit: its practice statement notebooks, without answers | `scripts/build-pdf.sh --book book2` |
| `mocktests/r2-001-paper.pdf` | Mock test `r2-001`: `test.md`, then each problem file in manifest order (theory and programming parts interleaved) | `scripts/build-pdf.sh --book book2` |
| `mocktests/r2-001-solutions.pdf` | Mock test `r2-001`: the answer key, rubric and solution notebooks | `scripts/build-pdf.sh --book book2` |

`build-book.sh` replaces `book2-*.pdf`; `build-pdf.sh` replaces `syllabus.pdf`, `handouts/` and `mocktests/`.
