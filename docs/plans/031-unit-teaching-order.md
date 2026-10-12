# Plan 031 — Book 1 Units in Teaching Order

## Goal

Make Book 1's unit folders and unit codes follow the order the course teaches them.
Each folder gets a two-digit teaching-order prefix.
Each F/C code is renumbered so that F1–F7 and C1–C12 each count up in teaching order.

User directive (2026-10-12): "re-code the units to make them follow natural learning order, we can still mark them F and C, but present a natural order in the folder".
The user chose "Prefix + renumber" over the two alternatives: prefix only, or renumber only.

## Branch and baseline

- Branch: `feature/plan-031-unit-teaching-order`, from `main` at a575e3f (Plan 030 merged).
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.
- Book 2 folders (`B2-019` … `B2-024`) are already in teaching order and do not change.
  Book 2's `book1:`-qualified references are rewritten to the new codes.

## The mapping

The teaching order is the order of each unit's first appearance in `book1/curriculum/course-schedule.yaml`.

| Order | Old id | New id | New folder |
|---|---|---|---|
| 01 | `F1-scientific-python` | `F1-scientific-python` | `01-F1-scientific-python` |
| 02 | `F2-vectors` | `F2-vectors` | `02-F2-vectors` |
| 03 | `F4-multivar-calculus` | `F3-multivar-calculus` | `03-F3-multivar-calculus` |
| 04 | `F3-matrices` | `F4-matrices` | `04-F4-matrices` |
| 05 | `F5-probability` | `F5-probability` | `05-F5-probability` |
| 06 | `C1-ml-fundamentals` | `C1-ml-fundamentals` | `06-C1-ml-fundamentals` |
| 07 | `C2-linear-models` | `C2-linear-models` | `07-C2-linear-models` |
| 08 | `C3-gradient-descent` | `C3-gradient-descent` | `08-C3-gradient-descent` |
| 09 | `C4-classical-ml-practice` | `C4-classical-ml-practice` | `09-C4-classical-ml-practice` |
| 10 | `C8-embeddings` | `C5-embeddings` | `10-C5-embeddings` |
| 11 | `C5-neural-networks` | `C6-neural-networks` | `11-C6-neural-networks` |
| 12 | `F6-svd-spectral` | `F6-svd-spectral` | `12-F6-svd-spectral` |
| 13 | `C6-pytorch` | `C7-pytorch` | `13-C7-pytorch` |
| 14 | `F7-kernels-convex-optimization` | `F7-kernels-convex-optimization` | `14-F7-kernels-convex-optimization` |
| 15 | `C11-neural-training` | `C8-neural-training` | `15-C8-neural-training` |
| 16 | `C9-dimensionality-reduction` | `C9-dimensionality-reduction` | `16-C9-dimensionality-reduction` |
| 17 | `C7-cnn-transfer` | `C10-cnn-transfer` | `17-C10-cnn-transfer` |
| 18 | `C10-competition-craft` | `C11-competition-craft` | `18-C11-competition-craft` |
| 19 | `C12-classical-models` | `C12-classical-models` | `19-C12-classical-models` |

Eight codes change.
Two of them form a swap (F3 ↔ F4).
The other six form a cycle: old C5→C6, C6→C7, C7→C10, C10→C11, C11→C8, and C8→C5.
That is why the rename is applied in one simultaneous pass over a full mapping, never as sequential find-and-replace.

## Decisions

**D1. The unit id and the folder are separate.**
The unit id stays `<code>-<slug>` (for example `F3-multivar-calculus`).
It is what manifests, coverage maps, schedules, syllabus entries and `book1:` qualified references use.
The folder is `<NN>-<id>`.
`tools/books.py` gains one resolver, `unit_dir(book_root, unit_id)` and its inverse `unit_id_of(folder)`. Every consumer that builds `units/<unit-id>` or treats a folder name as an id is routed through it. Known sites:
- `tools/publish.py` (about lines 570–586) and `tools/publish_pdf.py` (about 106–109);
- `tools/publish_audit.py` (about 281–321) and `scripts/verify-register.py` (about 307–313);
- `tools/checks/scope.py` (about 885–899).

Further sites:
- `tools/ci_scope.py:200` takes `parts[1]` as the unit id. A prefixed folder would otherwise silently escalate every scoped route to `full`.
- `tools/audit_curriculum.py:355` is named here; it reads `manifest["unit"]`, which is fine.
- `tools/model.py` reads `raw["unit"]` from the manifest and does not depend on folder layout.

Task 2 also greps every remaining `units/` path join and every `.name`-as-id use in `tools/`, `scripts/` **and `tests/`**. Examples include `tests/test_c11_solution_regressions.py:11`, `tests/test_integration.py:461,1523,1533` and `tests/test_scope.py:2200`; each is routed through `unit_dir`.

**How `unit_dir` resolves.** It looks for `units/NN-<id>` or `units/<id>`. Exactly one must exist; zero or both is an error. Unprefixed fixture trees under `tmp_path` therefore keep working.
The `unit-order` check is keyed on the Book 1 book id from `books.yaml`, not applied to every root.
Publication, audit, register and scope are tested on a fixture book whose Book 1 folders carry the `NN-` prefix.
A new check, `unit-order`, enforces three rules:
- every Book 1 unit folder matches `^\d{2}-<id>$`;
- the `NN` prefixes are 01…19 with no gaps;
- `NN` equals the unit's first-appearance position in the schedule.

Within F and within C, the codes count up in that same order.
Book 2 units have no prefix, and the check does not apply to Book 2 (it is keyed on book id).

**D2. One mechanical rewrite, driven by the mapping.**
A committed one-shot script, `scripts/renumber-book1-units.py`, holds the table above as data.
It runs one pass and is kept, not deleted, so the rewrite can be reproduced and reviewed.
The pass:

- Renames the unit folders with `git mv`, so file history follows.
- Rewrites every full-id token with a single regex alternation over the old ids. Each match maps through the table, so an already-rewritten token can never be rewritten again. This covers:
  - every text file outside `docs/plans/`: notebooks (JSON source, including relative links such as `../../../../book1/units/<folder>/lesson.ipynb`), YAML, Markdown, Python, shell and fixtures;
  - folder paths, by rewriting `units/<old id>` to `units/<new folder>`.
- Rewrites three token classes in **one** combined alternation: every match is mapped once from the original text, and nothing rewritten is ever re-scanned. Later classes match only where earlier ones did not.
  - (a) Full ids: `<old code>-<slug>`.
  - (b) Practice and qualified ids that start with a code: `C11-p16`, `book1:C11-…`. These map the code part.
  - (c) Standalone codes matching `(?<![A-Za-z0-9_:-])(F[1-7]|C1[0-2]|C[1-9])(?![A-Za-z0-9_-])`. The trailing `-` exclusion keeps class (c) away from class (a) and (b) tokens. Where class (c) applies, and with which deny and accept contexts, is defined only by D6 (one rule).
- **Idempotence by migration state.** The mapping is not idempotent as text (`C11-p16` → `C8-p16` → `C5-p16`), so the script checks a state marker before it writes anything. The repository counts as migrated if `book1/curriculum/course-schedule.yaml` has `teaching_order:` or any `book1/units/NN-*` folder exists. If it is migrated, the script exits 0 and changes nothing; if it is half-migrated, it exits non-zero.
- Tests prove that a second run is a no-op and that a half-migrated tree (some prefixed folders, no `teaching_order`) exits non-zero without writing anything. They also cover each swap and cycle member (`F3`↔`F4`, and `C5…C11`), and check that `C11-p16` and `C11-neural-training` each map exactly once. The script lists every bare-code hit with its context before applying. Ambiguous hits are excluded by an explicit allow/deny list kept in the script, and any hit outside a unit-reference context is reviewed by hand. The review list goes in the post-execution report.
- Renames `test_c11_solution_regressions.py` to `test_c8_solution_regressions.py`. That is the only test whose name carries a changed code; `test_c12_*` keeps its name.

The script has an explicit exclusion list: `docs/plans/`, `TODO.md` and `**/ERRATA.md`. These are historical records and keep the old ids as written.
The live, still-open `TODO.md` items that name changed units are updated by hand, with the old code in parentheses. Examples are the C10 `p12_solution` erratum (now C11) and the C7/C5 capacity note.
A new `docs/unit-renumbering.md` holds the mapping table, and `TODO.md` and `docs/README.md` point to it.

**D3. Content and answers must not change.**
The rewrite changes identifiers and paths only.
Task 1 greps every data generator and solution for a seed, hash or file name derived from a unit id or folder name. Any found are pinned to their old values, so no dataset, answer key or tolerance changes.
The verification phase proves this:
- every solution notebook executes;
- the answer register (`verify-register.py`) passes 437/437;
- the mutation checks pass;
- r1-001's answer-key reproduction is unchanged.

Pinned digests (material inventories, test hashes) are regenerated through their own tools, never hand-edited, and each regeneration is named in the report.

**Plan 019's enforcement files are migrated by hand, by user directive.** The inventory has no generator, so "regenerate through its tool" cannot apply. The user's 2026-10-12 instruction to rename and renumber the units is the authorization for this edit to the Plan 019/023 cutover contract.
It also covers the token rule. `scripts/verify-staged-scope.py`'s `protected_category` flags any path containing `token`.
The existing Plan 019 check stays as is: it allows changes to cell 1 only, compared with `old_path` at the Plan 019 base.
A **second, separate** check is added for the Plan 031 rename. It compares the renamed notebook with the pre-rename path `book1/units/C8-embeddings/lessons/01-tokens-and-embeddings.ipynb` at the merge base. Every cell must be identical after the D2 mapping is undone; cell 0 legitimately contains `C8-embeddings` and `F3-matrices`. Tests cover a mapped-only change (accepted) and any other change (rejected).
Concretely, `validate_token_exception` changes in three ways:
- `token_path_exception` becomes a **list** of typed entries. Entry 1 is the existing Plan 019 entry (kind `plan019-cell1`), with its semantics unchanged.
- Entry 2 is kind `plan031-rename`. Its `old_path` is the C8 lesson path (entry 1's `new_path`, which makes a deliberate chain) and its `new_path` is the `10-C5-embeddings` path. It allows only differences that vanish once the D2 mapping is undone, in any cell, and also requires the pinned cell-1 hash.
- In `--protected-range`, which runs without `-M`, the old path shows as deleted. Each entry's `old_path` is added to the skipped deleted paths.

The token-exception tests in `tests/test_clean_checkout.py` (about lines 2011–2106) are extended to cover a list of entries and the chained entry.
They also cover how `test_permanent_protected_mode_rejects_future_token_path_change` is reconciled: only the mapped rename, judged at the merge base, is accepted. Any later edit to `10-C5-embeddings/lessons/01-tokens-and-embeddings.ipynb` is still rejected in `--protected-cached` and `--protected-diff` modes, and an explicit test shows it.
The `plan031-rename` check forward-maps the base notebook's cells with the script's own rewrite function and requires byte equality; it never inverts the branch side. The renamed `book1/units/10-C5-embeddings/lessons/01-tokens-and-embeddings.ipynb` therefore needs a second exception entry in `token_path_exception`, with its cell hash unchanged, accepted by `validate_token_exception`.
Both the verifier and the inventory are re-pinned (two sha256 values) in `scripts/pre-merge-guard.sh`. The fixtures read by `tests/test_integration.py` (about lines 838, 907, 1950) are updated to match.
In more detail: `tests/fixtures/plan019-path-inventory.yaml` is pinned by digest in `scripts/pre-merge-guard.sh`. It also holds the token-notebook exception (its old and current paths plus a cell hash), which `scripts/verify-staged-scope.py` checks. The historical cutover tests in `tests/test_integration.py` (about 849–873) read the live tree through those paths.
Task 3 handles it as follows:
- The current-path fields move to the new folders, including the `python_consumers` and `split_token_python_consumers` entry for the renamed `tests/test_c11_solution_regressions.py`.
- The historical old paths and the cell hash stay unchanged, and the exception is extended to accept the renamed path.
- The historical cutover tests resolve live paths through `unit_dir` while keeping their historical assertions.
- The guard digest is re-pinned in the same commit.
- The diff of the inventory and the guard is quoted in full in the post-execution report.

**D4. The book follows the teaching order.**
`book1/publication.yaml` `chapters:` lists the units in teaching order.
That is a change: Plan 030 used syllabus order, with C11 between C6 and C7.
`volumes:` is recomputed as three contiguous ranges in the new order, each projected to stay within Plan 030's budget of 1,200 pages per PDF.
The proposed ranges are 01–08, 09–14 and 15–19, adjusted by measured pages. The volume part titles are rewritten to fit the new ranges, since "Foundations" no longer fits a range that includes C1–C3. Page-count changes per volume are recorded. `tests/test_publication_config.py` fixtures are checked for any syllabus-order assumption.
The front and back matter that name units (how-to-use, for-teachers, glossary unit tags, and the volume names in `output/README.md`) are rewritten by the D2 pass and then read once by hand.
The rewrite also covers the generated documents: `course-structure.md`, the roadmap, and the material inventory.

**D5. Scope boundaries.**
- No lesson, practice, solution, data, or mock-test wording changes except id, code and path tokens.
- Book 2 unit folders and ids are unchanged.
- Concept ids are unchanged; they are not unit ids.
- **Practice ids carry the unit code** (`C7-p10`, schedule `problem_ids`, coverage keys, mutation markers like `C7-p10-frozen-update`). They are renamed with their unit (`C7-pNN` → `C10-pNN`, `C11-pNN` → `C8-pNN`, …) as token class (b).
  - Literal tables are updated too: `scripts/verify-register.py` `REGISTER_UNITS`, `C7_BUDGET_REGISTER` (renamed to its new code), and the `if unit == "C7-cnn-transfer"` guard; `tests/test_verify_register.py`'s `removeprefix("C7-")`; and the mutation tools' path literals and marker names (`tools/verify_training_mutations.py`, `tools/verify_classical_mutations.py`, and their tests).
  - Task 4 checks that the multiset of practice ids, with the mapping undone, equals `main`'s (437).

**D6. Token classes and context rules for the rewrite** (Fable round 1). The single alternation (D2) is ordered longest first:
1. full ids `<code>-<slug>`, including `book1:` qualified ids and the `book1/units/<id>` path segment at either relative depth (`../../../` or `../../../../`);
2. practice ids `<code>-pNN`;
3. lesson references `<code>-NN` (for example `F6-02`);
4. standalone codes.

Class 4 runs over every non-plan text file: Book 1 and Book 2 prose (about 45 bare Book 1 codes in Book 2), `tools/` (for example `tools/render_curriculum_roadmap.py` unit tuples and labels), `tests/`, and non-plan `docs/` (for example `docs/unit-standards.md`'s double-length list and the tests that quote it).
- **Deny contexts** (never rewritten):
  - matplotlib colour strings: `color=`, `"C0"`–`"C9"`, and `"C3--"`-style format strings;
  - the metric names `F1` in "F1 score", "macro-averaged F1" and `f1`.
- **Mechanical accept contexts:**
  - a bold or backticked id;
  - `X's`, `X Session N`, `X lesson NN`;
  - a parenthesized unit code;
  - glossary `*(X)*` tags;
  - `docs/unit-standards.md` and roadmap lists.
- **Residue:** every other hit is listed with its context and reviewed by hand. This includes the roughly 33 non-identity code-cell hits (comments, docstrings, `print` strings such as `# C6 course register`, and `(C6 Session 1)`). The full list goes in the post-execution report.

**D7. Paths built in notebook code.** Some code cells build unit paths from parts, for example `book_root / "units" / "C4-classical-ml-practice" / …`. Task 1 greps code cells for `"units" /`, `'units'` and `units/`. Each site is rewritten to the new folder name, since that string is a folder, not an id.
The book's printed "Practice file:" line (`tools/publish.py` and `tools/publish_audit.py`) prints the real **folder** path, `units/17-C10-cnn-transfer/practice/pNN.ipynb`.

**D8. Teaching order is declared, not inferred.** `book1/curriculum/course-schedule.yaml` gains `teaching_order:`, the 19 unit ids in folder order. `_parse_schedule` (`tools/checks/schedule.py`) currently accepts only `schedule_version`, `calendar`, `weeks` and `totals`. Task 2 adds `teaching_order` as an optional, Book 1-only key, with tests for present, absent, a wrong unit set, and Book 2 rejecting the key.
The `unit-order` check validates three things:
- the folder prefixes match this list;
- the list is consistent with the schedule: no unit appears in the schedule before an earlier-listed unit's first appearance;
- the F and C codes count up along the list.

The week-17 tie (C5-neural-networks and F6-svd-spectral both first appear in week 17) is resolved by allocation order within the week. That gives C6-neural-networks before F6, and it is now recorded explicitly in the list.
A later schedule change no longer forces a rename unless it changes this declared order.

## Implementation tasks

- [ ] **Task 1 — Inventory and seed safety.** Run the D2 script in `--dry-run` mode. It reports:
  - the counts per file class;
  - every bare-code hit with context;
  - every path-derived seed, hash or file name (D3).

  Record the dry-run summary in this plan before applying.
- [ ] **Task 2 — Tooling.**
  - Separate id from folder in `tools/books.py` (D1) and route every unit-path construction through it.
  - Add the `unit-order` check to `scripts/ci-local.sh` (manifest validation step).
  - Tests: a folder with a bad prefix, a gap, an order mismatch, and a Book 2 unit that is exempt.
  - `scripts/pre-merge-guard.sh` unit-collision check (about lines 113–150):
    - Strip `^[0-9]{2}-` and key on the code, so two `F3` folders still collide.
    - Assert that `NN` prefixes are unique.
    - In the `--pr` union, exclude any `origin/main` folder that is the rename source of a branch-side folder (from `git diff -M` or the script's mapping). Main's `F3-matrices` therefore does not collide with the branch's `03-F3-multivar-calculus`.
    - Test both a mixed-layout union and a genuine collision.
  - Route through `unit_dir` and `unit_id_of` every site Fable listed by file and line: `tools/publish_audit.py` (about 104, 311, 314, 386, 421, 623–624), `scripts/verify-register.py:308`, and `tools/books.py` `live_units` (which must return ids, not folders). `tools/publish.py` `UNIT_LABEL` must always receive the id.
- [ ] **Task 3 — Apply the rename** with the D2 script, regenerate every generated artifact and pinned digest through its tool, and update `publication.yaml` (D4).
  - Rename code-named tests.
  - Add `docs/unit-renumbering.md` and point to it from `TODO.md` and `docs/README.md`.
- [ ] **Task 4 — Verification phase.**
  - Run `scripts/ci-local.sh --all-books` on a clean tip. It must end ALL GREEN, which includes notebook execution, the register (437/437), the mutation checks, both publish audits, and the pre-merge guard.
  - `git diff --stat -M main` must show the 19 folder renames as renames.
  - Content-invariance checks, with the comparison defined exactly:
  - **What is compared:** every file under `book1/` and `book2/` on `main` against its counterpart on the branch, paired through the folder mapping.
  - **Transformation:** apply the D2 forward rewrite to the `main` side; files are paired through the folder mapping.
  - **Declared structural exceptions** (excluded, then reviewed by hand):
    - the `teaching_order:` key;
    - `book1/publication.yaml` `chapters:`/`volumes:`;
    - generated artifacts (`course-structure.md`, the roadmap, material inventories), which are regenerated and checked by `--check`;
    - the front-matter volume names.
  - `tools/`, `scripts/` and `tests/` are code changes, reviewed in the gate, not by this check.
  - (a) Round trip: applying the script's own forward rewrite to each `main` file gives exactly the branch file, byte for byte, apart from the declared structural exceptions. The diff is empty, with no residue; deny contexts are handled because the forward function never touches them.
  - (b) The diff with every `(F|C)\d+` token masked is empty.
  - (c) The sha256 of every `data/` file and every generated dataset is unchanged.
  - (d) The practice-id multiset check (D5) passes.
  - (e) The mutation checks are confirmed non-vacuous: every marker resolves to a real target.
  - Record the Book 1 edition page counts and volume ranges.
  - Spot-check rendered pages: the TOC, and one chapter opener per volume.
- [ ] **Task 5 — Post-execution report, PR, `pre-merge-guard --pr`, squash-merge.**

## Out of scope

- The code-snippet commenting pass (Plan 032), which follows this plan so it works on the final paths.
- Book 2 folder prefixes.
- Rewriting historical plan files.
- Any content edit beyond id and path tokens.
- The verification-phase rule is satisfied by Task 4. This plan ships no new units or mock tests.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Review 1 — self (2026-10-12)
- **Verdict**: Approve with suggestions.
1. `[FIXED]` Should Fix: bare-code rewriting is the riskiest step. "C1" and "F5" can occur outside unit references, for example in tables or in a variable `C1`. → D2 limits the rewrite to prose tokens, runs a dry-run listing first, and keeps an allow/deny list. Code cells are excluded from the bare-code pass unless the token sits inside a string that names a unit.
2. `[FIXED]` (upgraded to Must Fix by Sol, finding 4) Nit: `pre-merge-guard.sh` checks unit-ID collisions across branches. The check must treat the renamed folders (`NN-<id>`) correctly, and Task 2 must cover it.

### Review 1 — Sol, `gpt-6-sol` (2026-10-12)
- **Verdict**: Reject. The mapping was verified against the schedule.
1. `[FIXED]` Must Fix: id/folder coupling outside `books.py`. → Response: D1 names the `unit_dir`/`unit_id_of` resolver, every known site, a grep task, and a prefixed fixture test.
2. `[FIXED]` Must Fix: the bare-code regex hit hyphenated ids. → Response: D2 uses three token classes in one alternation, excludes trailing `-` from class (c), and adds idempotence, cycle and collision tests.
3. `[FIXED]` Must Fix: the Plan 019 inventory and exception. → Response: D3 migrates current paths, keeps the historical proof and hash, extends the exception, re-pins in the same commit, and quotes the diff.
4. `[FIXED]` Must Fix: the guard's collision parse. → Response: Task 2 parses the code after `NN-` and tests a mixed-layout `--pr` union.

### Review 1 — Fable (2026-10-12)
- **Verdict**: Reject. The mapping and the cycle were verified; one week-17 tie was noted.
1. `[FIXED]` Must Fix: practice ids carry the code. → Response: D5 renames them as class (b), updates the literal tables, mutation markers and tests, and adds a multiset check.
2. `[FIXED]` Must Fix: the two-pass double rewrite. → Response: a single longest-first alternation with four classes (D2/D6), plus idempotence and cycle tests (also Sol 2).
3. `[FIXED]` Must Fix: the Plan 019 enforcement files. → Response: D3 names a hand migration authorized by the user's directive, the second token exception, both re-pins, and the fixtures.
4. `[FIXED]` Must Fix: the guard's collision logic. → Response: strip the prefix, key on the code, require unique prefixes, exclude rename sources in the union, and test both cases.
5. `[FIXED]` Must Fix: path construction outside `books.py` and inside notebooks. → Response: every site is listed by file and line, `live_units` returns ids, and D7 handles paths built in code cells.
6. `[FIXED]` Should Fix: bare codes in tools, tests and docs. → Response: D6 class 4 covers them, with per-hit review.
7. `[FIXED]` Should Fix: ambiguous tokens. → Response: D6 deny contexts (colours, F1 metric), mechanical accept contexts, and a hand-reviewed residue listing the ~33 code-cell hits.
8. `[FIXED]` Should Fix: invariance was under-specified. → Response: Task 4 checks (a)–(e).
9. `[FIXED]` Should Fix: order inferred from the schedule. → Response: D8 declares `teaching_order:` with the tie-break recorded.
10. `[FIXED]` Should Fix: the printed practice path. → Response: D7 prints the folder path; page-count changes are recorded.
11. `[FIXED]` Nits 11–14: volume titles and the fixture check; one renamed test file and renamed register identifiers; links at both depths and Book 2 bare codes; lesson references as class 3.

### Review 2 — Sol, `gpt-6-sol` (2026-10-12)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: idempotence was undefined. → Response: a migration-state marker; an already-migrated repository is a no-op, a half-migrated one fails.
2. `[FIXED]` Must Fix: the token exception versus the verifier. → Response: a second, separate check compares with the pre-rename path at the merge base after undoing the mapping (all cells); the Plan 019 check is kept unchanged.
3. `[FIXED]` Must Fix: the schedule parser rejected `teaching_order`. → Response: it becomes an optional Book 1-only key in `_parse_schedule`, with tests.
4. `[FIXED]` Must Fix: the invariance comparison was ill-defined. → Response: the compared set, the transformation, and the declared structural exceptions are now stated.
5. `[FIXED]` Should Fix: D2 and D6 disagreed on scope. → Response: D6 is the single rule.

### Review 2 — Fable (2026-10-12)
- **Verdict**: Reject, on one narrow point. Every other round-1 response was verified against the repo.
1. `[FIXED]` Must Fix: `validate_token_exception` takes a single entry, requires a deletion, and requires byte-identical cells. → Response: D3 now specifies a typed exception list, a `plan031-rename` kind that accepts mapped-only differences plus the pinned cell-1 hash, the chained `old_path`, the deleted-path skip in `--protected-range`, and extended tests (same as Sol round 2, finding 2).
2. `[FIXED]` Should Fix: missing sites. → Response: `ci_scope.py:200` and `audit_curriculum.py:355` are named; `model.py` is noted as layout-agnostic.
3. `[FIXED]` Should Fix: split-part joins in Python. → Response: the grep covers `tests/`, and each site goes through `unit_dir`.
4. `[FIXED]` Should Fix: the resolver rule. → Response: exactly one of `NN-<id>` or `<id>` must exist; the check is keyed on book id.
5. `[FIXED]` Should Fix: the D2/D6 contradiction. → Response: D6 is the single rule (Sol round 2, finding 5).
6. `[FIXED]` Nits: `C7_BUDGET_IDS` does not exist and was removed; the inventory consumer entry is renamed; empty deny contexts are harmless.

### Review 3 — Sol, `gpt-6-sol` (2026-10-12)
- **Verdict**: Approve with nits.
1. `[FIXED]` Nit: a test for the half-migrated failure was added to D2.

### Review 3 — Fable (2026-10-12)
- **Verdict**: Approve with nits. The round-2 blocker was verified as resolved against the verifier code.
1. `[FIXED]` Should Fix: wrong test citation, and reconciling the permanent-protection test. → Response: the tests are in `test_clean_checkout.py`; later edits stay rejected, with an explicit test; the check forward-maps the base.
2. `[FIXED]` Should Fix: the exclusion-list contradiction. → Response: an explicit exclusion list, plus a hand update of the live `TODO.md` items.
3. `[FIXED]` Nit: the invariance direction. → Response: (a) is a forward round trip with byte equality and no residue.
4. `[WONTFIX]` Nits 4–5: informational; Book 2 has its own parser; `publish_audit`'s `LABEL` already accepts prefixes.

**Gate result:** 3-way consensus at round 3 (self, Sol and Fable approve; the remaining edits are text clarifications of their own nits). Implementation is authorized.

## Implementation notes

### Task 1 dry run (2026-10-12)

`python3 scripts/renumber-book1-units.py --dry-run` on the branch tip before the rename.

**Files rewritten per class** (828 total):
`book1` notebooks 431, `book1` YAML 18, `book1` Markdown 7, `book1` Python 1 (the C10 generator docstring);
`book2` notebooks 321, `book2` YAML 7, `book2` Markdown 2;
`tests/` 28, `tools/` 4, `scripts/` 2, `docs/` 5, `output/` 1, `.gitignore` 1.

**Rewritten tokens by class:** full ids as folders (`units/<id>` and `"units" / "<id>"`) 11,444;
full ids as ids 10,781; practice ids 1,131; lesson references 0 (every `<code>-NN` reference names an unchanged code);
overrides 11 (plus 1 identity override); bare codes 424 rewritten, 3 denied.

**Bare changed-code hits (428) by context class:**
glossary `*(X)*` 64; possessive `X's` 104; parenthesized 24; `X Session/lesson N` 13; bold/backtick 1;
`docs/unit-standards.md` 14; roadmap tool 4; residue 201 (hand-reviewed below); residue-deny 3.
23 hits sit in notebook code cells (comments, docstrings, `print` strings such as `# C6 course register` and `print("C11 review environment ready")`; one committed output line `matches C5 helper:` that is regenerated from the rewritten `print`).
Deny contexts (matplotlib `"C0"`–`"C9"` colours, `"C3--"` formats, the F1 metric) matched no changed code; they stay in the script as guards.

**Residue review (hand).** Every residue hit was read in context.
All are Book 1 unit references in prose, comments or test strings and are rewritten, except:
- **Denied (3):** `F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb` names a cosine-similarity matrix `C6` in a code cell (`C6 = G6 / ...`, `print(C6)`, `round(C6[0, 2], 4)`); it is a Python variable, kept as `C6`.
- **Overrides (same single pass):** `taught by units C5-C7;` → `taught by units C6, C7 and C10;` (r1-001 manifest; the old range is no longer contiguous);
  `shapes · F1–F3` → `shapes · F1, F2, F4` (notation heading);
  `drills of F1–F4` kept (same four units after the swap);
  `# F4-convention residual` → `# F3-convention residual` (code comment);
  `C7-budget-register` → `C10-budget-register` (register marker, D5);
  `F5, F6, C7, C11, C12` → `F5, F6, C8, C10, C12` (double-length roster stays ascending).
- **Kept mechanical, noted:** `everything C1–C9 built` (C9 lesson forward pointer) stays `C1–C9`; both endpoints are unchanged codes.
- Generated files (`material-inventory.yaml`, `course-structure.md`, `docs/audits/015-coverage-audit.md`, the roadmap) are regenerated by their tools after the rename, so their residue is informational.

Residue by file (code → new code × count, context):
  - `.gitignore`: C10->C11 ×2 (residue)
  - `book1/back-matter/notation.md`: F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/curriculum/coverage-map.yaml`: C10->C11 ×4 (residue); C5->C6 ×1 (residue); C6->C7 ×2 (residue); C7->C10 ×1 (residue); F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/curriculum/material-inventory.yaml`: C5->C6 ×6 (residue); C7->C10 ×2 (residue); C8->C5 ×6 (residue); F3->F4 ×6 (residue)
  - `book1/docs/course-structure.md`: C10->C11 ×1 (residue); C8->C5 ×3 (residue)
  - `book1/front-matter/for-teachers.md`: C10->C11 ×4 (residue); C11->C8 ×1 (residue); C5->C6 ×1 (residue); C6->C7 ×1 (residue); C7->C10 ×3 (residue); C8->C5 ×3 (residue); F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/mocktests/r1-001/problems/p08.ipynb`: C6->C7 ×1 (residue code)
  - `book1/mocktests/r1-001/rubric.md`: C10->C11 ×1 (residue)
  - `book1/mocktests/r1-001/solutions/p08_solution.ipynb`: C6->C7 ×1 (residue code)
  - `book1/syllabus.md`: C10->C11 ×2 (residue); C11->C8 ×1 (residue); C5->C6 ×1 (residue); C6->C7 ×1 (residue); C7->C10 ×1 (residue); C8->C5 ×2 (residue); F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/units/C10-competition-craft/data/make_dataset.py`: C10->C11 ×1 (residue)
  - `book1/units/C10-competition-craft/lessons/03-notebook-and-writeup.ipynb`: C10->C11 ×1 (residue)
  - `book1/units/C11-neural-training/lesson.ipynb`: C11->C8 ×1 (residue); C5->C6 ×2 (residue); C6->C7 ×2 (residue); C7->C10 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/units/C11-neural-training/lessons/01-softmax-and-cross-entropy.ipynb`: C7->C10 ×1 (residue)
  - `book1/units/C11-neural-training/lessons/02-manual-backpropagation.ipynb`: C5->C6 ×1 (residue)
  - `book1/units/C11-neural-training/lessons/04-pytorch-autograd-and-optimizers.ipynb`: C7->C10 ×1 (residue)
  - `book1/units/C11-neural-training/lessons/05-batchnorm-and-dropout.ipynb`: C7->C10 ×2 (residue)
  - `book1/units/C11-neural-training/review.ipynb`: C11->C8 ×1 (residue code)
  - `book1/units/C2-linear-models/lesson.ipynb`: F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `book1/units/C2-linear-models/lessons/01-linear-regression-and-mse.ipynb`: F3->F4 ×1 (residue); F4->F3 ×2 (residue)
  - `book1/units/C2-linear-models/lessons/03-regularization-and-sparsity.ipynb`: F4->F3 ×2 (residue)
  - `book1/units/C3-gradient-descent/lessons/01-surfaces-and-descent.ipynb`: F4->F3 ×3 (residue)
  - `book1/units/C3-gradient-descent/lessons/02-learning-rates-and-stochasticity.ipynb`: F4->F3 ×1 (accept-parenthesized code)
  - `book1/units/C3-gradient-descent/review.ipynb`: F4->F3 ×1 (residue)
  - `book1/units/C5-neural-networks/lesson.ipynb`: C6->C7 ×1 (residue)
  - `book1/units/C6-pytorch/lesson.ipynb`: C5->C6 ×1 (residue)
  - `book1/units/C6-pytorch/lessons/01-tensors-and-inheritance.ipynb`: C5->C6 ×1 (residue)
  - `book1/units/C6-pytorch/lessons/02-nn-module-and-custom-layers.ipynb`: C5->C6 ×4 (accept-possessive code); C5->C6 ×4 (residue); C5->C6 ×4 (residue code)
  - `book1/units/C6-pytorch/lessons/03-parameter-counting-and-inspection.ipynb`: C5->C6 ×1 (residue); C6->C7 ×1 (residue); C7->C10 ×2 (residue)
  - `book1/units/C6-pytorch/practice/p13.ipynb`: C5->C6 ×2 (accept-possessive code); C5->C6 ×1 (residue)
  - `book1/units/C7-cnn-transfer/lesson.ipynb`: C11->C8 ×2 (residue); C7->C10 ×1 (residue)
  - `book1/units/C7-cnn-transfer/lessons/01-convolution-and-feature-maps.ipynb`: C6->C7 ×1 (accept-session-or-lesson code); C5->C6 ×1 (residue); C6->C7 ×2 (residue); C6->C7 ×1 (residue code)
  - `book1/units/C7-cnn-transfer/lessons/02-resnet-reading.ipynb`: C6->C7 ×3 (residue)
  - `book1/units/C7-cnn-transfer/lessons/03-truncation-and-transfer.ipynb`: C10->C11 ×1 (residue); C6->C7 ×4 (residue); C8->C5 ×1 (residue)
  - `book1/units/C7-cnn-transfer/lessons/04-cnn-training-and-fine-tuning.ipynb`: C11->C8 ×1 (residue); C7->C10 ×1 (residue)
  - `book1/units/C8-embeddings/lessons/02-matrices-and-similarity.ipynb`: F3->F4 ×2 (residue)
  - `book1/units/C9-dimensionality-reduction/lesson.ipynb`: C8->C5 ×1 (accept-parenthesized code); C8->C5 ×1 (residue)
  - `book1/units/C9-dimensionality-reduction/lessons/03-truncated-svd-practice.ipynb`: C8->C5 ×2 (accept-possessive code); C8->C5 ×1 (residue)
  - `book1/units/F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb`: C6->C6 ×3 (residue-deny code)
  - `book1/units/F5-probability/lessons/03-gaussian-simulation-covariance.ipynb`: C5->C6 ×1 (residue)
  - `book1/units/F6-svd-spectral/lesson.ipynb`: F3->F4 ×1 (residue)
  - `book1/units/F6-svd-spectral/lessons/01-eigenvalues-and-eigenvectors.ipynb`: F3->F4 ×6 (residue); F3->F4 ×1 (residue code)
  - `book1/units/F6-svd-spectral/lessons/02-spectral-decomposition.ipynb`: F3->F4 ×3 (residue)
  - `book1/units/F6-svd-spectral/lessons/03-svd.ipynb`: F3->F4 ×3 (residue)
  - `book1/units/F6-svd-spectral/lessons/04-frobenius-and-low-rank.ipynb`: F3->F4 ×1 (residue)
  - `book1/units/F7-kernels-convex-optimization/lessons/01-psd-matrices-and-kernels.ipynb`: F3->F4 ×1 (residue)
  - `book2/curriculum/coverage-map.yaml`: C8->C5 ×1 (residue)
  - `book2/units/B2-020-language-transformers/lessons/00-book1-bridge.ipynb`: C8->C5 ×1 (residue)
  - `book2/units/B2-021-cross-modal-transformers-vision/lessons/00-book1-bridge.ipynb`: C11->C8 ×2 (residue); C6->C7 ×1 (residue); C7->C10 ×2 (residue); F3->F4 ×1 (residue)
  - `book2/units/B2-022-probabilistic-latent-models/lessons/00-book1-bridge.ipynb`: C11->C8 ×1 (residue)
  - `book2/units/B2-022-probabilistic-latent-models/lessons/03-autoencoders.ipynb`: C5->C6 ×1 (residue); C6->C7 ×1 (residue)
  - `book2/units/B2-023-generative-models-diffusion/lessons/00-book1-bridge.ipynb`: C11->C8 ×1 (residue)
  - `docs/audits/015-coverage-audit.md`: C10->C11 ×4 (residue); C5->C6 ×1 (residue); C6->C7 ×2 (residue); C7->C10 ×1 (residue); C8->C5 ×1 (residue); F3->F4 ×1 (residue); F4->F3 ×1 (residue)
  - `docs/curriculum-architecture.md`: C8->C5 ×1 (residue)
  - `output/README.md`: C10->C11 ×1 (residue); C6->C7 ×1 (residue)
  - `scripts/verify-register.py`: C7->C10 ×3 (residue)
  - `scripts/verify-staged-scope.py`: C8->C5 ×1 (residue)
  - `tests/test_audit_curriculum.py`: C8->C5 ×1 (residue)
  - `tests/test_schedule.py`: C11->C8 ×1 (residue)
  - `tests/test_scope.py`: C6->C7 ×4 (residue); C7->C10 ×5 (residue); C8->C5 ×9 (residue)
  - `tests/test_verify_register.py`: C7->C10 ×2 (residue)
  - `tools/checks/scope.py`: C8->C5 ×2 (residue)

**Exclusions:** `docs/plans/`, `TODO.md`, `**/ERRATA.md` (D2), the hand-migrated `tests/fixtures/plan019-path-inventory.yaml` (D3), the files that hold the mapping as data (the script, its test, the invariance check, `docs/unit-renumbering.md`), and **`docs/designs/`** (deviation, see below).
Deviation: `docs/designs/` is excluded as a historical record alongside `docs/plans/`.
Design 017 explains why `C11` was *not* renumbered ("sorts after `C10` lexically although the schedule places it between C6 and C7 … without renaming shipped C5–C10 directories"); a mechanical rewrite turns that paragraph false.
`docs/unit-renumbering.md` translates old codes for readers of designs and plans.

**Path-derived seeds, hashes and file names (D3): none.**
Every notebook seed is a literal constant; the only in-notebook digest (`C3-gradient-descent/practice/p19`, `TRANSCRIPT_DIGEST`) hashes transcript contents, not a path; data generators resolve output next to `__file__`; mock-test notebooks locate the book root by walking up from the working directory, independent of the unit folder name.
Data payloads under `data/` (CSV/JSON/TXT) have zero token hits and are never written.

**Notebook code-cell path joins (D7):** one — `C4-classical-ml-practice/lessons/01-pandas-and-data-loading.ipynb` `DATA_DIR = book_root / "units" / "C4-classical-ml-practice" / "practice" / "data"`, rewritten to the folder `09-C4-classical-ml-practice`.
The same folder-context rule rewrites 27 `BOOK1_ROOT / "units" / "<id>"` and `tmp_path / "units" / "<id>"` joins in `tests/`; Task 2 routes the live-tree ones through `unit_dir`.

**Script tests** (`tests/test_renumber_book1_units.py`, 26 cases): every swap/cycle member maps once (`F3`↔`F4`, `C5…C11`), simultaneous swap in one text, `C11-p16` and `C11-neural-training` each map exactly once, lesson references, folder contexts at both link depths and in JSON-escaped code joins, deny contexts, hyphenated non-codes, the residue deny, overrides, path mapping, apply-then-no-op idempotence, dry-run writes nothing, and both half-migrated states exit non-zero without writing.

## Content Review

## Post-execution report
