# Plan 033 — Two Errata and Overfull Lines in the Editions

## Goal

Close the three content follow-ups in `TODO.md` that students can see:

1. C11 `practice/p12_solution.ipynb` prints raw LaTeX because its inline math lost its delimiters.
2. The B2-022 KL lesson names the direction of $\mathrm{KL}(P\|Q)$ in a way that conflicts with the back matter.
3. Lines in the PDF editions run into the margin, almost all inside tables.

User directive (2026-10-27): "fix items 1-3 with autopilot".

## Branch and baseline

- Branch: `feature/plan-033-errata-and-overfull`, from `main` at 60b1247 (after Plan 032).
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.

## Diagnosis

Items 1 and 2 are post-merge content bugs, so they follow the errata lifecycle.
The inline diagnosis is below.
The `[sol]` reviewer confirms or refutes it as a separate read-only duty in plan-gate round 1, which is the second leg of the 2-way diagnosis.

### Item 1 — C11 p12 solution delimiters

- File: `book1/units/18-C11-competition-craft/practice/p12_solution.ipynb`, markdown cell 1.
- Six inline-math spans are written with bare parentheses instead of `\(…\)`:
  `(A_j=\frac1{50}\sum_{i=1}^{50} I_{ji})`, `(I_{ji})`, `(E[I_{ji}]=1/2)`, `(M=\max_j A_j\ge A_1)`, `(E[M]\ge E[A_1]=1/2)`, `(E[M]>1/2)`.
  The same cell uses `\[…\]` for display math, so the backslashes were lost in authoring (`\(` → `(`).
- A scan of every markdown cell in both books (units and mock tests), looking for LaTeX commands outside `$…$`, `$$…$$`, `\(…\)`, `\[…\]` and backticks, finds this cell and no other.
- Impact: Jupyter shows the literal TeX, and the editions print it (the editions read notebooks with `-raw_tex`).
  Only the reasoning prose is affected; the answer, the code and the checks are unaffected.

### Item 2 — B2-022 KL direction wording

- File: `book2/units/B2-022-probabilistic-latent-models/lessons/02-kl-divergence.ipynb`, markdown cell 1.
- It says "The **Kullback–Leibler divergence** of $Q$ from $P$ is $\mathrm{KL}(P\,\|\,Q)=…$".
  Sources disagree on which way "of … from …" reads (Wikipedia, for example, calls $\mathrm{KL}(P\|Q)$ "the divergence of $P$ from $Q$"), so the phrase is at best ambiguous.
  The book's glossary and notation table avoid the phrase and say "the extra expected log loss from using $Q$ when the data follow $P$".
- The formula, the "expectation under $P$" reading in the next sentence, and every computation are correct.
- A search of Book 2's notebooks and markdown finds no other "divergence of $X$ from $Y$" phrasing.

### Item 3 — overfull boxes

Overfull `\hbox` counts in the final `latex-audit.log` of each edition on 60b1247, bucketed by width:

| Edition | > 40 pt | 10–40 pt | 2–10 pt | ≤ 2 pt |
|---|---:|---:|---:|---:|
| book1 student-print | 3 | 11 | 12 | 9 |
| book1 student-vol1 / teacher-vol1 | 0 | 5 | 4 | 2 |
| book1 student-vol2 / teacher-vol2 | 0 | 3 | 7 | 5 |
| book1 student-vol3 | 3 | 3 | 1 | 2 |
| book1 teacher-vol3 | 3 | 3 | 2 | 2 |
| book2 student-print / student | 0 | 9 | 9 | 5 |
| book2 teacher | 0 | 14 | 23 | 10 |

The syllabus, handout and mock-test PDFs (`build-pdf.sh`) report none.

Causes, from mapping each box to its TeX source:

- **(a) An `lll` longtable.** C9 `practice/p18.ipynb` and `p18_solution.ipynb` have a three-column pipe table with short separator lines. Pandoc then emits natural-width `l` columns, and the table is 51.5 pt too wide (three boxes per edition that contains it).
- **(b) Unbreakable `\texttt` in narrow `p` columns.** Lesson file names in the unit-overview session tables (`lessons/01-eigenvalues-and-eigenvectors.ipynb`), and code such as `parameter.requires_grad_(False)` and `r2_001_data.unlabelled_rows("texture")`. The Lua `Code` filter adds break points after `_ ( ) , : / + - =` and inside runs of 12 letters or digits, but never at `.` or before punctuation. Fragments such as `eigenvectors.ipynb` and `.requires_` therefore stay wider than the column.
- **(c) Long plain-text numbers in table cells.** For example, B2-024 `p12`/`p12_solution` tables of 17-digit floats (`0.05441953241825104`). Plain text has no break points.
- **(d) Sub-2 pt boxes.** They are not visible in print and are left alone.

## Decisions

### D1 — Item 1 fix

- Restore `\(`…`\)` around exactly the six spans. No other byte of the cell changes.
- Add `book1/units/18-C11-competition-craft/ERRATA.md` in the format of `book1/units/19-C12-classical-models/ERRATA.md`: the date, the plan, what was wrong, the fix, and "answers unaffected".

### D2 — Item 2 fix

- Replace "The **Kullback–Leibler divergence** of $Q$ from $P$ is" with "The **Kullback–Leibler divergence**, the extra expected log loss from using $Q$ when the data follow $P$, is".
  This is the back-matter wording, and the rest of the cell stays byte-identical.
- Add `book2/units/B2-022-probabilistic-latent-models/ERRATA.md`.
- `tests/test_b2_022_statements.py` lists this lesson. The implementer confirms that no test pins the replaced phrase, and updates such a test only if one does.

### D3 — Item 3: fix at the publisher, guard in the audit

Fix the causes once in the shared publishing code, not cell by cell, so that future content inherits the fix.

- **(a)** In `tools/publish_theme/panels.lua`, add a `Table` filter for LaTeX. When a table has 3 or more columns and every column has the default width, it assigns relative widths in proportion to each column's longest cell, with a floor per column, and the widths sum to the line width. Pandoc then emits `p` columns, which wrap. Tables that already have explicit widths are untouched.
- **(b)** In the `Code` filter, also allow a break after `.` when a letter or digit follows. Inside table cells only, also allow a break before `.` and `(`. If a fragment still cannot fit, typeset `\texttt` in table cells at `\small`, via a table-scoped wrapper rather than a global font change.
- **(c)** In the `Str` filter, inside table cells only, allow a break inside a run of 10 or more digits.
  The printed characters are unchanged, and nothing is rounded.
- **Content edits are a fallback only.** They may change markdown table layout (separator-line dash counts) and nothing else: no words or numbers change. Each such edit is listed in the post-execution report.
- **Guard.**
  - `tools/publish_audit.py` parses each edition's `latex-audit.log`. It reports the count of overfull `\hbox`es and the widest box, with its TeX line and chapter.
  - It fails when any box exceeds `audit.overfull_max_pt` from `<book>/publication.yaml`, set to `5` for both books. `5` is chosen because boxes under 5 pt are not noticeable at the edition's margin width.
  - Scoped publish checks apply the same rule to their render.
- **Acceptance.**
  - After the fix, every edition of both books has no overfull box over 5 pt.
  - The total count of boxes over 2 pt is reported before and after.
  - The `build-pdf.sh` PDFs stay at zero.
- **No page-count drift beyond ±2%** per edition. Larger drift means a filter is over-reaching, and the implementer reports it.

### D4 — What does not change

- Code cells, answers, data, seeds and statement wording, other than the two erratum sentences.
- The editions' structure, edition table, theme fonts and page geometry.

## Implementation tasks

- [ ] **Task 1 — Errata (D1, D2).**
  - Edit the two cells as JSON, preserving the notebook format.
  - Write both `ERRATA.md` files.
  - Regenerate `book1|book2/curriculum/material-inventory.yaml` with `uv run python -m tools.audit_curriculum --root <book>`.
  - Execute both notebooks.
  - Run the tests that reference C11 and B2-022.
  - Done inline: these are trivially scoped edits.
- [ ] **Task 2 — Publisher fixes and guard (D3).** Opus tooling subagent.
  - Make the Lua filter changes. Add the `publish_audit` overfull parser and threshold, and the `audit.overfull_max_pt` key in both `publication.yaml` files.
  - Unit tests in `tests/` for:
    - the table-width assignment (pandoc on a markdown fixture: `lll` becomes `p` columns; explicit widths are preserved);
    - the new code break points (`a.b`, and the table-only rules);
    - the digit-run breaks;
    - the audit parser and threshold: pass, fail, the widest box reported, and the missing-key default.
  - Rebuild both books' editions, and record the before and after table of D3 buckets plus page counts in this plan.
- [ ] **Task 3 — Verification phase.**
  - `scripts/ci-local.sh --all-books` is ALL GREEN on a clean tip, including the publish audits with the new guard.
  - Render the pages for the C9 p18 table, a unit-overview session table and the B2-024 p12 table, before and after the fix, and inspect them. The tables must sit inside the margin and stay readable.
  - Each content-gate reviewer gets the page images and the diff.
- [ ] **Task 4 — Post-execution report, `TODO.md` (move the three items to done), PR, `pre-merge-guard --pr`, squash-merge.**

## Out of scope

- Other `TODO.md` items: the ladder-audit recommendations, tag-honesty enforcement, etc.
- Restyling tables beyond the width fix, and any change to the editions' layout or fonts.
- Underfull boxes and sub-2 pt overfull boxes, which the guard only reports.
- This plan ships no new units or mock tests. Task 3 is its verification phase.

## Plan Review

## Implementation notes

## Content Review

## Post-execution report
