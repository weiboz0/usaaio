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

Task 2 also greps every remaining `units/` path join and every `.name`-as-id use in `tools/` and `scripts/`.
Publication, audit, register and scope are tested on a fixture book whose Book 1 folders carry the `NN-` prefix.
A new check, `unit-order`, enforces three rules:
- every Book 1 unit folder matches `^\d{2}-<id>$`;
- the `NN` prefixes are 01…19 with no gaps;
- `NN` equals the unit's first-appearance position in the schedule.

Within F and within C, the codes count up in that same order.
Book 2 units have no prefix, and the check does not apply to Book 2.

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
  - (c) Standalone prose codes matching `(?<![A-Za-z0-9_:-])(F[1-7]|C1[0-2]|C[1-9])(?![A-Za-z0-9_-])`. The trailing `-` exclusion keeps class (c) away from class (a) and (b) tokens. Class (c) applies only inside Book 1 and Book 2 prose (markdown cells and `.md` files).
- Tests prove that a second run is a no-op (idempotence). They also cover each swap and cycle member (`F3`↔`F4`, and `C5…C11`), and check that `C11-p16` and `C11-neural-training` each map exactly once. The script lists every bare-code hit with its context before applying. Ambiguous hits are excluded by an explicit allow/deny list kept in the script, and any hit outside a unit-reference context is reviewed by hand. The review list goes in the post-execution report.
- Renames the test files that carry unit codes: `test_c11_solution_regressions.py` becomes `test_c8_…`, and the same for any other code-named test.

`docs/plans/`, earlier `ERRATA.md` entries, and `TODO.md` history keep the old ids as written, since they are historical records.
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

**Plan 019's protected inventory is migrated, not regenerated.** `tests/fixtures/plan019-path-inventory.yaml` is pinned by digest in `scripts/pre-merge-guard.sh`. It also holds the token-notebook exception (its old and current paths plus a cell hash), which `scripts/verify-staged-scope.py` checks. The historical cutover tests in `tests/test_integration.py` (about 849–873) read the live tree through those paths.
Task 3 handles it as follows:
- The current-path fields move to the new folders.
- The historical old paths and the cell hash stay unchanged, and the exception is extended to accept the renamed path.
- The historical cutover tests resolve live paths through `unit_dir` while keeping their historical assertions.
- The guard digest is re-pinned in the same commit.
- The diff of the inventory and the guard is quoted in full in the post-execution report.

**D4. The book follows the teaching order.**
`book1/publication.yaml` `chapters:` lists the units in teaching order.
That is a change: Plan 030 used syllabus order, with C11 between C6 and C7.
`volumes:` is recomputed as three contiguous ranges in the new order, each projected to stay within Plan 030's budget of 1,200 pages per PDF.
The proposed ranges are 01–08, 09–14 and 15–19, adjusted by measured pages.
The front and back matter that name units (how-to-use, for-teachers, glossary unit tags, and the volume names in `output/README.md`) are rewritten by the D2 pass and then read once by hand.
The rewrite also covers the generated documents: `course-structure.md`, the roadmap, and the material inventory.

**D5. Scope boundaries.**
- No lesson, practice, solution, data, or mock-test wording changes except id and path tokens.
- Book 2 unit folders and ids are unchanged.
- Concept ids are unchanged; they are not unit ids.
- Practice ids (`p01` …) are unchanged.

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
  - `scripts/pre-merge-guard.sh`'s unit-collision logic (about lines 130–150) takes the leading number of a folder name, so for `03-F3-…` it would read `03`. Fix it to parse the code after an optional `NN-` prefix. Test the `--pr` union with the old layout on one side and the new on the other.
- [ ] **Task 3 — Apply the rename** with the D2 script, regenerate every generated artifact and pinned digest through its tool, and update `publication.yaml` (D4).
  - Rename code-named tests.
  - Add `docs/unit-renumbering.md` and point to it from `TODO.md` and `docs/README.md`.
- [ ] **Task 4 — Verification phase.**
  - Run `scripts/ci-local.sh --all-books` on a clean tip. It must end ALL GREEN, which includes notebook execution, the register (437/437), the mutation checks, both publish audits, and the pre-merge guard.
  - `git diff --stat -M main` must show the 19 folder renames as renames.
  - A content-invariance check: for every Book 1 notebook, the diff against `main` after undoing the mapping is empty.
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

## Content Review

## Post-execution report
