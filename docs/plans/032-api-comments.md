# Plan 032 — Explain Library Calls Where Students First Meet Them

## Goal

A student reading any code cell should never need to search the web to learn what a library call does.
Every non-baseline function or method is explained in a code comment where the book first uses it.
Later uses that add a new argument or call mode get a comment about the new element.
The first use in each later unit gets a short reminder.

User directives (2026-10-12):

- "review the code snippets … if any new methods called in the first several times, but no comment on the code about what it does at all. make sure students don't need to search for the method to understand what it does."
- "not only first use case, some following up use cases with different parameters may also need comment to help smooth the learning process."
- "do not remove any existing comments."
- The user chose option C, the tiered approach, over first-occurrence-only (A) and comment-everything (B).

## Branch and baseline

- Branch: `feature/plan-032-api-comments`, from `main` at 69fb6db (Plan 031 merged as #36). All paths use the `NN-<code>-<slug>` folders.
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.
- Survey input: `scratchpad/snippet-survey/` (pre-031 paths; remapped by Task 1). It found 338 of 546 distinct callees unexplained at first use. Its worklist has 220 book-first rows, 75 high-signal new-signature rows and 693 unit-first rows, plus 12 callees used only in mock tests.

## Decisions

### D1 — The four comment rules (option C)

Teaching order is Book 1 `teaching_order`, then Book 2 units in folder order.
Inside a unit, notebooks are ordered: `lesson.ipynb` (overview), `lessons/*.ipynb` by file name, `review.ipynb`, practice statements by number, practice solutions by number.
Mock tests come after their book's units and get their own pass (D6).

1. **Book-first.** The first time a callee appears in the book (Book 1 and Book 2 separately; Book 2 counts Book 1 as already taught only for callees Book 1 explains), the call carries a full comment: what it returns or does, in plain words, including the meaning of each argument used. One line where possible; a comment block on the line(s) above when it does not fit in 100 characters.
2. **New signature.** A later use that adds a keyword argument, a positional-argument count that changes meaning (e.g. `np.arange(a, b, step)` after `np.arange(n)`), or a call mode (method vs function form, `axis=`, `keepdims=`, `dim=`, `replace=False`, `key=`, `reduction=`) carries a comment on the new element only, e.g. `# keepdims=True keeps the summed axis as length 1`.
3. **Unit-first reminder.** The first use of a non-baseline callee in each later unit carries a reminder of six words or fewer, e.g. `# np.linalg.solve: solve Ax = b`. A unit whose overview carries the callee in its API card (D3) satisfies this rule for every notebook of that unit.
4. **Harness cells.** Test and checker code that the student runs but does not write (`assert`, `check_*`, `_test_*`, path-finding boilerplate) gets one cell-level comment at the top saying what the cell checks, instead of per-call comments. Rules 1–3 do not apply inside a cell that starts with that note (`# Checks:` prefix).

Baseline callees that never need a comment: the Python built-ins and string/list/dict methods in the course baseline (Calculus AB + basic Python), listed in `tools/checks/api_comments_baseline.yaml` (seeded from the survey's `BASE_BUILTINS`/`BASE_METHODS`).

### D2 — Existing comments are never removed or reworded

The user rule is absolute.
An added comment may sit next to an existing one; when an existing comment already explains the call, nothing is added.
Enforced mechanically by D5(b).

### D3 — Per-unit "New in this unit" API card

Each unit's overview notebook (`lesson.ipynb`, present in every unit) gets one markdown cell titled "New code in this unit": a short table of the callees the unit introduces (book-first) with a one-line meaning each.
The review notebook (where one exists) gets the same table under "Code you met in this unit" for revision.
Cards are generated from the check's first-use table (D4) and hand-edited for wording; the check verifies that every book-first callee of the unit appears in its card.

### D4 — CI check `api-comments`

New module `tools/checks/api_comments.py`, run per book from `scripts/ci-local.sh` (scope-aware like the other content checks: a scoped run checks the changed units but computes first-use from the whole book).

- Parse every code cell with `ast` (cell magics and shell lines blanked), resolve import aliases, and collect call sites with their callee name, keyword set and positional count.
- "Explained" means: a comment on the same line, on a contiguous comment block directly above the statement, or (rule 1 only) a markdown cell among the three preceding cells that names the callee in backticks.
- Fails on: a book-first call without explanation (rule 1); a new-signature call without a comment naming the new keyword or mode (rule 2); a unit-first call without a comment or API-card entry (rule 3); a unit card missing a book-first callee (D3).
- Receiver-type ambiguity (bare methods such as `.fit`, `.view`, `.sum`) is resolved by an explicit table in the baseline file mapping method name → library family; unresolved bare methods are treated by name only.
- A committed allowlist `tools/checks/api_comments_waivers.yaml` records each deliberate exemption with a one-line reason. The waiver list must stay under 2% of call sites checked; the check prints its size.
- Tests: fixtures for each rule's pass and fail, alias resolution, harness-cell exemption, waiver handling, card check, scoped vs full first-use.

### D5 — Comment-only invariance

Notebooks change only by added comments and added markdown cells.

- (a) For every code cell, `ast.dump(ast.parse(cleaned_source))` is identical on `main` and the branch. Docstrings are not allowed as the vehicle (they change the AST).
- (b) Every comment token on `main` is still present on the branch, in order, in the same cell (a subsequence check over `tokenize` COMMENT tokens). No removal, no rewording.
- (c) Markdown cells on `main` are byte-identical; new markdown cells are only the D3 cards and the D6 teaching cells, recognisable by a fixed first-line marker.
- (d) Cell count changes only by the added markdown cells; code cells keep their ids and order; outputs stay empty in student notebooks.
- (e) Data files, seeds and answer keys unchanged (the existing generated-artifact `--check`s and solution-execution steps cover this).

Implemented as `scripts/verify-comment-only.py --base main`, run in Task 5 and by the content gate.

### D6 — The 12 mock-only callees

Twelve callees appear in mock tests but in no unit notebook:

- r1-001: `numpy.pad` (p05 solution), `sklearn.preprocessing.RobustScaler`, `shutil.copy2`, `subprocess.run` (p09 solution).
- r2-001: `json.loads` (p01 **statement**), `Tensor.view`, `torch.nn.ModuleList` (p01 solution), `torch.nn.GELU`, `torch.optim.lr_scheduler.OneCycleLR` (p02 solution), `torch.fft.fftfreq`, `torch.meshgrid`, `torch.fft.fft2` (p04 solution).

- Callees in **statement** notebooks (provided code the student reads, e.g. `json.loads` in r2-001 p01) get a rule-1 comment in the statement and are taught in the unit that owns the closest concept, as a short lesson code cell with comment plus a sentence of prose.
- Callees only in **solution** notebooks that a student could reasonably need (`np.pad`, `RobustScaler`, `nn.ModuleList`, `nn.GELU`, `.view`, `OneCycleLR`, `torch.fft.fftfreq`, `torch.fft.fft2`, `torch.meshgrid`) are taught the same way in their owning unit.
- Infrastructure callees in solutions (`shutil.copy2`, `subprocess.run`) get a rule-1 comment in the solution only; they are not exam content.
- Each new lesson cell is a markdown + code pair with the D5(c) marker; it does not add a concept tag and does not change any practice or answer.

The owning unit for each callee is fixed in Task 1's mapping table and reviewed in the plan gate.

### D7 — Comment wording standard

- Plain words, present tense, says what the call returns or does, e.g. `# np.argmax: index of the largest entry`.
- Names the meaning of arguments actually used, not every parameter of the API.
- Uses the book's notation (shapes as `(n, d)`, the same variable names).
- No URLs, no "see the docs".
- Fits within the 100-column ruff limit; otherwise a block above the statement.
- In statement notebooks, comments explain provided code only and never hint at the solution.

### D8 — Dispatch and batching

- Tooling (Tasks 1–2): one Opus subagent.
- Annotation (Task 3): Opus subagents in batches of 3–4 units, in teaching order, working from the check's failure list. A batch annotates lessons, statements and solutions of its units; this is annotation of existing code, not authoring or solving, so the statement/solution session separation does not apply. Each batch re-runs the check and D5 for its units before committing.
- Teaching cells and cards (Task 4): one Opus author.

## Implementation tasks

- [ ] **Task 1 — Inventory.** Remap the survey worklist to the post-031 paths; produce the D6 owning-unit table; record counts per rule and per unit in this plan.
- [ ] **Task 2 — Tooling.** `tools/checks/api_comments.py`, baseline and waiver YAMLs, `scripts/verify-comment-only.py`, tests, wiring into `scripts/ci-local.sh` (both books) and `tools/ci_scope.py`. Initially the check runs in report mode; Task 5 flips it to enforcing.
- [ ] **Task 3 — Annotate** units in teaching order (rules 1–4), Book 1 then Book 2, then the mock tests (rule 1 in statements; D6).
- [ ] **Task 4 — API cards and D6 teaching cells**, then regenerate generated artifacts (material inventory, course structure) through their tools.
- [ ] **Task 5 — Verification phase.**
  - `api-comments` in enforcing mode passes for both books; waiver count recorded.
  - `scripts/verify-comment-only.py --base main` passes (D5 a–d).
  - `scripts/ci-local.sh --all-books` ALL GREEN on a clean tip (solution execution, hygiene, register, publish audits, pre-merge guard).
  - Rebuild the editions and spot-check that comments render inside the code-block width in the print edition (no overfull code lines); record page-count deltas.
  - Content-gate reviewers each audit a random sample of at least 60 added comments for accuracy (D7) and for statement hints.
- [ ] **Task 6 — Post-execution report, PR, `pre-merge-guard --pr`, squash-merge.**

## Out of scope

- Rewriting existing comments or prose (forbidden by D2).
- The difficulty-ladder recommendations (separate, user decides).
- Any change to answers, data, seeds or practice statements beyond comments.
- The verification-phase rule is satisfied by Task 5. This plan ships no new units or mock tests.

## Plan Review

## Implementation notes

## Content Review

## Post-execution report
