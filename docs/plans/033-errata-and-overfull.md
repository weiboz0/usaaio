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

- Replace "The **Kullback–Leibler divergence** of $Q$ from $P$ is" with "The **Kullback–Leibler divergence** is".
  The displayed formula follows, and the next sentence already gives the direction in the back-matter sense ("the average extra log-loss you pay for believing $Q$ when outcomes really come from $P$"). Removing the ambiguous phrase therefore removes the conflict without repeating that sentence. The rest of the cell stays byte-identical.
- Add `book2/units/B2-022-probabilistic-latent-models/ERRATA.md`.
- `tests/test_b2_022_statements.py` lists this lesson. The implementer confirms that no test pins the replaced phrase, and updates such a test only if one does.

### D3 — Item 3: fix at the publisher, guard in the audit

Fix the causes once in the shared publishing code (`tools/publish_theme/panels.lua`), not cell by cell, so that future content inherits the fix.
`panels.lua` is shared with `tools/publish_pdf.py` (syllabus, handouts and mock papers), so the change applies there too.

- **Table scope.** Pandoc's default traversal visits a cell's `Code` and `Str` inlines before it calls `Table`, so a `Table` callback cannot flag cells for the existing `Code` filter in time.
  - The fix is a new first filter table, prepended to the list that `panels.lua` returns: `{Table = function(t) … t:walk{Code = table_code, Str = table_str} … end}`.
  - `table_code` and `table_str` turn table-cell inlines into `RawInline` LaTeX themselves, so the later filter's `Code` never sees them.
  - Inlines outside tables go through the existing filter unchanged, apart from the global `.` rule below.
  - Tests run `quarto pandoc` (pandoc 3.4), not the system `pandoc`, and skip when Quarto is absent.
- **(a) Width for natural-width tables that would overflow.**
  - The `Table` callback assigns relative column widths only when two things hold:
    - every column has the default width;
    - the estimated natural width overflows: the sum, over columns, of the longest cell's character count, times 0.6 em at 10 pt, exceeds the text width (about 392 pt). Over-estimating only gives a fitting table `p` columns, which is the safe direction.
  - Widths are proportional to each column's longest cell, with a floor of `min(0.15, 0.5/ncols)` per column, renormalized to sum to 1. The `0.5/ncols` cap leaves half the width to the proportional share, so wide tables do not collapse to equal widths. Pandoc then emits wrapping `p` columns.
  - Tables that fit today keep their natural width, and tables with explicit widths are untouched.
  - This targets the only `in alignment` family in the logs: C9 p18, 9 boxes across the editions.
- **(b) Break points in code.**
  - **Everywhere:** allow a break after `.` when a letter or digit follows. For example, `np.linalg.eig` may now break as `np.` / `linalg` in running prose. This is accepted and listed under D4.
  - **In table cells only:** also allow a break before `.` and `(`, after `[`, and before `[` and `]`. This covers `labels[heldout][:48]`.
  - **In table cells only, always:** typeset code as `{\small\texttt{…}}`. The rule is deterministic, so there is no "if it still does not fit" condition.
- **(c) Plain text in table cells.**
  - The table-scoped `Str` rule allows a break after `/` when a letter or digit follows, and after `-` only with a letter or digit on both sides, so a leading minus is never stranded. This covers file names written as plain text, such as C2's escaped-backtick `` `lessons/02-normal-equations-rank-pseudoinverse.ipynb` ``.
  - **Digit-run break: a shipping decision, not a per-table rule.** It ships only if a box over 5 pt survives (a), (b), `\small` and the dash fallback. If it ships, it applies to every table cell in both books, breaking inside runs of 10 or more digits, and is listed under D4. Otherwise it is left out, and the report says so.
  - For the B2-024 p12 float tables, the preferred fix is separator dashes or `\small`, because a mid-number break with no continuation mark is ambiguous in an answer table. The report says which fix each table used.
  - The printed characters never change, and nothing is rounded.
- **Content edits are a fallback only.** They may change separator-line dash counts in a markdown table. They may also unescape a stray `` \` `` so that the text inside is code, as in the C2 overview. Words and numbers never change, and each edit is listed in the post-execution report.
- **Guard.**
  - `tools/publish_audit.py` parses each rendered edition's `latex-audit.log` inside the existing per-project loop, so scoped `build/publish-check` renders get the same rule. `build-book.sh` overwrites the log on each pass, so the parsed log is the final pass.
  - It reports the count of overfull `\hbox`es and the widest box with its TeX line. The chapter is found by scanning the kept `.tex` backwards from that line for `\chapter{…}`.
  - It fails when any box exceeds `audit.overfull_max_pt`, a key in `<book>/publication.yaml` set to `5` for both books. Boxes under 5 pt are not noticeable at the edition's margin.
  - `tools/books.py` `_AUDIT_KEYS` gains the key. `publication_config_errors` validates it as a positive number when present: zero, negative and non-numeric values are config errors. A missing key disables the check (report only).
  - It fails when a rendered edition has no `latex-audit.log`, so a missing log cannot bypass the threshold.
  - The `build-pdf.sh` logs (`build/pdf/**/*.log`) are also parsed against the same threshold. The implementer confirms that those logs record `Overfull` lines (not a batch/quiet run), and a test fixture with a planted `Overfull \hbox (6pt too wide)` in a `build/pdf` log must fail.
- **Acceptance.**
  - Every edition of both books, and every `build-pdf.sh` PDF, has no overfull box over 5 pt.
  - The count of boxes over 2 pt is reported before and after.
  - No edition's page count drifts beyond ±2%. Larger drift means a filter is over-reaching, and the implementer reports it.

### D4 — What does not change

- Code cells, answers, data, seeds and statement wording, other than the two erratum sentences.
- The editions' structure, edition table, theme fonts and page geometry.
- Accepted visible changes: inline code may break after `.` anywhere, code in table cells is set at `\small`, and overflowing natural-width tables wrap. If the digit-run break ships, long digit runs in table cells may also break.

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
    - the table-width assignment (`quarto pandoc` on a markdown fixture: an overflowing `lll` table becomes `p` columns; a table that fits keeps `l`; explicit widths are preserved);
    - the new code break points (`a.b`, the table-only `.`/`(`/`[`/`]` rules, `\small` in cells; plain-text `/` and `-` breaks in cells);
    - only if the digit-run break ships (D3 (c)): its book-wide rule. If it does not ship, the report records that and no test is added;
    - a wide table: the 9-column C8 p20 table and a 12-column fixture get feasible widths that sum to 1;
    - a `build/pdf` log with a planted `Overfull \hbox (6pt too wide)` fails the audit;
    - the audit parser and threshold: pass, fail, the widest box reported, the missing-key default, a missing log (fails), and `books.py` validation of the new key (accepts a positive number, rejects zero, negative and non-numeric values);
    - prose and code outside tables are unchanged by the filter.
  - Rebuild both books' editions, and record the before and after table of D3 buckets plus page counts in this plan.
- [ ] **Task 3 — Verification phase.**
  - `scripts/ci-local.sh --all-books` is ALL GREEN on a clean tip, including the publish audits with the new guard.
  - Render the pages for the C9 p18 table, the F6 unit-overview session table (`np.linalg.eig*`), the C2 overview row, the r2-001 p04 table, the 9-column C8 p20 table and the B2-024 p12 table, before and after the fix, and inspect them. The tables must sit inside the margin and stay readable.
  - Each content-gate reviewer gets the page images and the diff.
- [ ] **Task 4 — Post-execution report, `TODO.md` (move the three items to done), PR, `pre-merge-guard --pr`, squash-merge.**

## Out of scope

- Other `TODO.md` items: the ladder-audit recommendations, tag-honesty enforcement, etc.
- Restyling tables beyond the width fix, and any change to the editions' layout or fonts.
- Underfull boxes and sub-2 pt overfull boxes, which the guard only reports.
- This plan ships no new units or mock tests. Task 3 is its verification phase.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Round 1

- `[self]` APPROVE WITH NITS. [FIXED] `panels.lua` is shared with `publish_pdf.py`, so the handout, syllabus and mock PDFs are in the acceptance criteria.
- `[sol]` REJECT. Errata diagnosis: Item 1 CONFIRMED (six spans; no other cell among 5,285 scanned); Item 2 CONFIRMED.
  - [FIXED] Must Fix: `tools/books.py` `_AUDIT_KEYS` must accept and validate `overfull_max_pt` (D3 Guard, Task 2 tests).
  - [FIXED] Must Fix: the table-scope mechanism is now named. A prepended filter table whose `Table` callback walks the cells, because inlines are visited before `Table` (D3).
  - [FIXED] Should Fix: a missing `latex-audit.log` fails the guard.
- `[fable]` APPROVE WITH NITS, conditional on its Must Fix items.
  - [FIXED] M1: `_AUDIT_KEYS` (same as sol).
  - [FIXED] M2: rules did not cover all boxes over 5 pt. Added `[`/`]` code breaks in cells, plain-text `/`/`-` breaks in cells, and the escaped-backtick fallback (D3 (b), (c)).
  - [FIXED] M3: table-scope mechanism (same as sol).
  - [FIXED] S4: `\small` in cells is unconditional. S5: (a) applies only to overflowing default-width tables. S6: the digit break is the last resort, and dashes or `\small` are preferred for the float tables. S7: a missing key or `0` disables the check. S8: tests use `quarto pandoc`.
  - [FIXED] N9: the chapter comes from the kept `.tex`. N10: `build-pdf` logs are parsed too. N11: scoped renders are covered by the per-project loop. N12: the F6 table is added to the inspected pages. The D2 duplication nit is taken: the sentence becomes "The **Kullback–Leibler divergence** is".

### Round 2

- `[fable]` APPROVE WITH NITS. All round-1 findings are resolved.
  - [FIXED] S: the digit-run break is a ship-or-not decision, applied book-wide if shipped (D3 (c)).
  - [FIXED] S: the column floor is `min(0.15, 1/ncols)`, renormalized (7-column B2-023 table).
  - [FIXED] Nits: a leading minus is never stranded; the estimate uses 0.6 em; a planted fixture proves that the `build-pdf` logs are measured.
- `[sol]` REJECT on 85c7d0a. Round-1 items resolved; diagnosis verdicts unchanged.
  - [FIXED] Must Fix: the 15% floor was infeasible for wide tables (the 9-column C8 p20 table). The floor is now `min(0.15, 1/ncols)`, renormalized, with a wide-table test.
  - [FIXED] Should Fix: zero had two meanings. Now a missing key disables the check, and zero is a config error.
  - [FIXED] Should Fix: a planted `build/pdf` log fixture is in the Task 2 tests.

### Round 3

- `[fable]` APPROVE. No open findings.
- `[sol]` APPROVE WITH NITS.
  - [FIXED] Should Fix: with 7 or more columns, the `1/ncols` floor forced equal widths. The floor is now `min(0.15, 0.5/ncols)`, and C8 p20 is added to the rendered-page check.
  - [FIXED] Nit: both outcomes of the digit-run decision are explicit in the Task 2 tests and in D4.
- `[self]` APPROVE.
- **Gate passed** (3/3, no `[OPEN]` items). The 2-way errata diagnosis (inline plus `[sol]`) is CONFIRMED for both items.

## Implementation notes

### Task 1 — Errata (1a4870f, inline)

- C11 p12 solution: the six spans now use `\(…\)`; no other byte of the cell changed. The notebook executes clean.
- B2-022 lesson 02: the sentence is now "The **Kullback–Leibler divergence** is"; the notebook executes clean.
- Both units gained `ERRATA.md`. `tests/test_b2_022_statements.py` pins the unit's exact file list, so it now expects `ERRATA.md` (61 files). No test pinned the replaced phrase.

### Task 2 — Publisher fixes and guard (5f7ee98, Opus)

- `panels.lua`:
  - A prepended `Table` filter assigns widths to overflowing default-width tables, using a 6 pt-per-character estimate against 392 pt and a floor of `min(0.15, 0.5/ncols)` applied by repeated filling.
  - Table cells set code as `{\small\texttt{…}}` with the table-only break points, and plain text breaks after `/`, and after `-` with a letter or digit on both sides.
  - The global code rule breaks after `.`.
- `books.py` `_AUDIT_KEYS` validation; `publish_audit.py` rule 7 `check_overfull`, covering editions, scoped checks and the `build/pdf` logs; `audit.overfull_max_pt: 5` in both books.
- **Digit-run break: not shipped.** No box over 5 pt survived without it, and a test pins the decision.
- **Deviations:**
  - The global and table `.` rules skip a `.` between two digits, so `lr=0.05` never splits into `lr=0.` / `05`. Tested.
  - `theme.tex` gains `\DeclareTOCStyleEntry[pagenumberwidth=4em]{part}{part}`. Without it, the bold "Mock Tests" part entry in the table of contents made a 5.62 pt box (book1 teacher-vol3) and a 4.89 pt box (book2 teacher). This widens the page-number box only.
- **Content fallback edits (no words or numbers changed):**
  - C2 `lesson.ipynb` overview: unescaped `` \` ``, three rows;
  - B2-023 lessons/03 SNR table separator dashes;
  - B2-024 `p12.ipynb` table separator dashes.
- Both material inventories regenerated.

Before/after overfull buckets (> 40 / 10–40 / 2–10 / ≤ 2 pt), from a full rebuild of both books on the final code:

| Edition | Before | After |
|---|---|---|
| book1 student-print | 3/11/12/9 | 0/0/1/1 |
| book1 student-vol1, teacher-vol1 | 0/5/4/2 | 0/0/0/0 |
| book1 student-vol2, teacher-vol2 | 0/3/7/5 | 0/0/0/0 |
| book1 student-vol3 | 3/3/1/2 | 0/0/1/1 |
| book1 teacher-vol3 | 3/3/2/2 | 0/0/1/1 |
| book2 student-print, student | 0/9/9/5 | 0/0/5/7 |
| book2 teacher | 0/14/23/10 | 0/0/11/11 |
| answer keys, 31 build-pdf logs | 0 | 0 |

The widest remaining boxes are 3.82 pt (book1) and 4.81 pt (book2).

Page counts: book1 student-print 1024 → 1023 and student-vol2 470 → 468; book2 teacher 938 → 936; every other edition is unchanged (all within ±0.5%).

Tests:
- new `tests/test_publish_theme_tables.py` (10 tests, through `quarto pandoc`);
- 6 rule-7 tests in `test_publish_audit.py`;
- 10 config cases in `test_publication_config.py`;
- the related suites pass (327 + 89).

Page images, before and after, in `scratchpad/p033-pages/`: C9 p18, F6 overview, C2 overview, C8 p20, B2-024 p12, r2-001 p04.

## Content Review

Roster: `[self]` (Opus 5.5 inline), `[sol]` (codex gpt-6-sol, read-only), `[fable]` (Fable 5, read-only). Inputs: `git diff 8747b7c..HEAD` and the before/after page images in `scratchpad/p033-pages/`.

### Round 1

- `[self]` APPROVE. The fallback diffs change only separator dashes and three backtick escapes. The C9 p18 and B2-024 p12 after-pages sit inside the margin.
- `[sol]` APPROVE WITH NITS. A pandoc probe confirmed table scope, widths, break rules and special-character escaping; rule 7 parsed 52 of 52 log entries.
  - [FIXED] Nit: `overfull_max_pt: .inf` passed validation. It is now rejected as not finite, with a test case.
- `[fable]` APPROVE WITH NITS. 68 tests rerun; all 12 logs and 14 page images checked; nothing worse than before.
  - [WONTFIX] N1: the B2-024 p12 `config` column wraps `lr=` / `0.1`. Widening it (12 dashes, `scores` 27) made the `scores` cells overflow: the scoped audit failed at 14.96 pt, so the guard works. The original separator is kept; the column reads correctly.
  - [WONTFIX] N2: the plain-text `-` rule could split `1e-05` or an ISO date in a table cell. The reviewer's scan of every table row found none; the risk is latent only, and the 5 pt guard catches any overflow.
  - [WONTFIX] N3: `t:walk` also visits table captions. The books have none.
  - [FIXED] N4: the overfull regex now also matches `has occurred while \output is active` (running header or footer), reported with line 0, with a test.
- **Gate passed** (3/3, no `[OPEN]` items).

## Post-execution report
