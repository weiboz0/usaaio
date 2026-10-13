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

**Order.** Teaching order is Book 1 `teaching_order`, then Book 2 units in folder order.
Inside a unit, notebooks are ordered: `lesson.ipynb` (overview), `lessons/*.ipynb` by file name (B2-019's `00-book1-bridge.ipynb` comes first), `review.ipynb`, practice statements by number, then practice solutions by number.
Mock tests come after their book's units (D6).
Book 2 counts a callee as already explained when Book 1 explains it; Book 1 never counts Book 2.

**Harness cells are outside the ladder.** First use (rules 1–3 and the D3 cards) is computed over non-harness code only (D1 rule 4).
A callee that appears only in harness code needs no explanation anywhere.

1. **Book-first.** The first non-harness use of a callee carries a full comment: what it returns or does, in plain words, with the meaning of each argument used. It goes on the same line when the line stays within 80 columns; otherwise in a comment block directly above the statement.
2. **New signature.** A later use that adds a *semantic* keyword or call mode carries a comment on the new element only, e.g. `# keepdims=True keeps the summed axis as length 1`.
   The trigger set is fixed in `tools/checks/api_comments_baseline.yaml` under `semantic_keywords`. It holds `axis`, `dim`, `keepdim`/`keepdims`, `replace`, `key`, `reduction`, `generator`, `dtype`, `device`, `bias`, `indexing`, `return_counts`, `ddof`, `full_matrices`, `size`, `p` and `weights`, plus positional-count changes for `arange`, `linspace`, `normal`, `zeros`/`ones`/`full`, `randint` and `split`.
   Styling keywords (`label`, `color`, `alpha`, `linewidth`, `zorder`, `marker`, `title`, `figsize`, `fontsize`, `ls`/`lw`) are out of rule 2.
   Task 1 may add keywords, with each one recorded in the plan.
3. **Unit-first reminder.** In each later unit, the first non-harness use of a callee is reminded in one of two ways:
   - inline, as a reminder of six words or fewer that names the callee, e.g. `# np.linalg.solve: solve Ax = b`;
   - or as an entry in the unit card's "Also used here" part (D3).

   Two kinds of callee are exempt from rule 3:
   - **graduated callees**, listed under `graduated` in the baseline YAML: the everyday array, plotting and Python calls explained in F1–F5 and used in at least three earlier units, such as `np.array`, `np.zeros`, `.sum`/`.mean`/`.max`/`.min`/`.reshape`/`.copy`/`.astype`, `np.random.default_rng`/`.normal`, `plt.subplots`/`.plot`, `zip`/`sorted`/`enumerate`/`next`/`any`/`all` and `ValueError`. Rule 1 still applies at their first use, and rule 2 still applies.
   - **self-describing callees**, listed under `no_reminder`, such as `torch.cuda.is_available`, `math.isfinite` and `ax.set_xlabel`.

   Task 1 records the real per-rule counts from the check, not the survey's.
4. **Harness code.** Harness code is test or checker code that the student runs but does not write. It is marked in one of two ways:
   - a whole cell whose first line is `# Checks: <what this cell verifies>`;
   - a contiguous block that starts `# Boilerplate: <what it does>` and ends with a blank line, used for the book-root/path-finding idiom.

   Calls inside harness code are exempt from rules 1–3 and do not count as first use.
   The marker is allowed only in these places:
   - practice-statement check cells;
   - solution notebooks' answer-check and assert-only cells;
   - mock-test paper-provided setup and self-check cells (byte-identical in the paper and its solution), and solution answer-pin cells (`ANSWER = …; assert …`). Probe code the student must write (for example r2-001 p01 cells 3, 5 and 7) is not harness. The check tests "paper-provided" mechanically: a mock-statement `# Checks:` cell must appear as a code cell of the matching `solutions/pNN_solution.ipynb`, byte for byte apart from trailing newlines;
   - the `# Boilerplate:` block, anywhere. Only calls in the named idiom's callee set (`named_idioms.<id>.callees` in the baseline YAML) are harness inside the block; any other call there, such as `torch.set_num_threads(1)`, still falls under rules 1–3.

   The check rejects a `# Checks:` marker in `lesson.ipynb`, `lessons/*.ipynb` or `review.ipynb`. Lesson cells that teach through asserts, for example C8 lesson 04 cells 3–7, follow rules 1–3.
   The path-finding idiom is explained once in full at its first appearance in a lesson (C4 lesson 01), as an ordinary rule-1 comment block, and is listed as the named idiom `book-root-finder` in the baseline.

Baseline callees never need a comment. They are the Python built-ins and the string, list and dict methods in the course baseline (Calculus AB plus basic Python), listed under `baseline` and seeded from the survey's `BASE_BUILTINS` and `BASE_METHODS`.

### D2 — Existing comments are never removed or reworded

The user's rule is absolute.
An added comment may sit next to an existing one. When an existing comment already explains the call (D4), nothing is added.
D5(b) enforces this mechanically.

### D3 — Per-unit API card

Each unit's overview `lesson.ipynb` gets one markdown cell, appended at the end of the notebook, headed "Code in this unit". It has two parts:

- **New in this unit:** each book-first callee of the unit with a one-line meaning.
- **Also used here (met earlier):** each rule-3 callee that is not reminded inline, with a reminder of six words or fewer and the unit where it was first explained.

`review.ipynb`, where it exists (25 units), gets a copy of the same card at its end, under "Code you met in this unit".
The cards are drafted from the check's first-use table and edited by hand for wording.
The check verifies four things:
- every book-first callee of the unit is in its "New" part;
- every "Also used" entry is a real rule-3 callee of that unit;
- no card names a harness-only callee;
- the review copy has the same entries as the overview card.

### D4 — CI check `api-comments`

There is a new module, `tools/checks/api_comments.py`.

**Wiring:**
- It is registered in `tools/cli.py` `SUBCOMMANDS` as `api-comments-check`.
- It runs per book in the `scripts/ci-local.sh` step-5 loop, over the whole book like its sibling checks. It only parses code, so it takes seconds per book and needs no scope interface. `tools/ci_scope.py` is unchanged.

**How it parses notebooks:**
- Code cells are parsed with `ast`.
- A cell containing an IPython magic or shell line (`%`, `!`) is rejected outright, not blanked. Current units and mocks have none, so the rule is preventive.
- Comments come from `tokenize` on the original source, so a `#` inside a string is not a comment. `# %%` is an ordinary comment.
- Import aliases are resolved with the existing `tools/checks/tolerance.py` machinery (`_import_aliases` / `_resolved_name`), extended rather than duplicated.

**Call-bound evidence: a call counts as explained only if one of these holds:**
- **(a) Comment on the same line:** a comment on the call's line names the callee (its last dotted component, e.g. `solve`, `argmax`) or, for rule 2, the new keyword.
- **(b) Comment block directly above:** a comment block directly above the statement does the same.
- **(c) Markdown cell nearby (rules 1 and 3 only):** the markdown cell immediately before or after the code cell, or the second cell before it, contains the exact dotted name or `.method(` in backticks, outside LaTeX math.
- **(d) Unit card (rule 3 only):** the unit card's "Also used here" lists the callee.

A comment that does not name the callee or keyword does not count. This closes the survey's false "explained" match, where an unrelated comment sat next to `np.zeros_like`.

**Bare methods:**
- The method-to-library-family table in the baseline YAML resolves bare methods such as `.fit`, `.view` and `.sum` where the receiver's type is known.
- A bare method whose receiver is still unknown is keyed by name only.

**What fails the check:**
- an unexplained rule 1, 2 or 3 site;
- a misplaced `# Checks:` marker;
- a card mismatch (D3);
- in statement notebooks, any rule-2-only comment, and any comment the check counts as call evidence (D4 (a)/(b)) that names an identifier the student must define. In statement notebooks only rules 1 and 3 apply, and each added comment is one line (D7).
  Pre-existing scaffold instructions such as `# YOUR CODE HERE (call standardize)` (C4 p08) are not call evidence, so they are untouched by this rule. The stricter rule, that no *added* statement comment may name a required identifier, is enforced by `scripts/verify-comment-only.py` (D5(f)), which knows which comments are new.
  Required identifiers are extracted from the statement: names in `` `def name(` `` or `` `class Name` `` spans; backticked names after "Implement", "Define" or "Write"; and `def`/`class` stubs whose body is `...`, `pass` or `raise NotImplementedError`.
  The same extractor is shared by the check and the verifier.

**Waivers:**
- Waivers live in `tools/checks/api_comments_waivers.yaml`, as path, cell, callee and a one-line reason.
- The denominator is rule-subject sites: rule 1, plus rule 2, plus rule 3 after graduation.
- Waivers must stay at or below 2% of rule-subject sites. The check prints both numbers.

**Tests** cover:
- pass and fail fixtures for each rule;
- alias resolution;
- the markdown-before and markdown-after windows;
- the LaTeX false match;
- harness markers (an allowed location, a lesson rejection, the boilerplate block);
- graduated and no-reminder callees;
- the statement restrictions;
- the waiver cap;
- card checks;
- first use computed across the whole book.

### D5 — Comment-only invariance

`scripts/verify-comment-only.py --base <ref>` compares each notebook on the branch with its counterpart at `<ref>`.

- **(a) Code unchanged:** every pre-existing code cell, matched by cell id, has an identical `ast.dump(ast.parse(source))`. Docstrings are not allowed as the vehicle for an explanation, because they change the AST.
- **(b) Comments preserved:** every comment token on `<ref>` is still present on the branch, in order, in the same cell. This is a subsequence check over `tokenize` COMMENT tokens taken from the original source. Nothing is removed or reworded.
- **(c) Markdown unchanged:** pre-existing markdown cells are byte-identical. New cells must start with a marker:
  - `<!-- api-card -->` for D3 cards;
  - `<!-- api-teach -->` for D6 markdown;
  - `# api-teach` as the first line of D6 code cells.
- **(d) Cell structure:** pre-existing cells keep their ids and their relative order.
  - Cells that any test or the Plan 019 inventory references by index keep their indices. Task 1 lists them, for example C4 lesson 01 cell 22 and r1-001 p09 cells 3 and 2/14.
  - D3 cards are appended at the end. D6 teaching cells are inserted only after the last index-referenced cell of their notebook.
  - New cells get fresh ids, and `nbformat.validate` passes.
  - Student notebooks keep empty outputs.
- **(e) Data and seeds untouched:** data, seeds and answer keys are covered by the existing generated-artifact `--check`s, solution execution and mutation checks.
- **(f) No hints in statements:** in statement and mock-statement notebooks, every added comment is one line and names no identifier the student must define (D4's extractor).

The verifier runs in Task 5 and in the content gate. It is not added to `ci-local.sh`, because on `main` after the squash merge it has no base to compare against.

### D6 — The 12 mock-only callees, and prose-mandated calls

The survey scanned only code cells. Task 1 also scans statement markdown and `theory/*.md` for callees that the statement prose requires. That is how `.view` and `nn.ModuleList` slipped through: r2-001 p01 requires them in prose (cells 4 and 6), yet no unit notebook uses them.

| Callee | Mock use | Treatment | Teaching location |
|---|---|---|---|
| `json.loads` | r2-001 p01 statement, provided code | Rule-1 comment in the statement. A teaching cell is a bonus, since students read this line but never write it. | `09-C4` lesson 01 (data loading), a D6 cell after cell 22 |
| `Tensor.view` | r2-001 p01, prose-mandated | Teaching cell | `13-C7-pytorch/lessons/01-tensors-and-inheritance.ipynb`, beside `.reshape` (contiguity note) |
| `torch.nn.ModuleList` | r2-001 p01, prose-mandated | Teaching cell | `B2-019` lesson 04 (stacking attention blocks) |
| `torch.nn.GELU` | r2-001 p02 solution | Teaching cell | `B2-020` lesson 03, where GELU is already named in prose |
| `torch.optim.lr_scheduler.OneCycleLR` | r2-001 p02 solution | Teaching cell | `15-C8` lesson 04 (optimizers) |
| `torch.fft.fftfreq`, `torch.fft.fft2`, `torch.meshgrid` | r2-001 p04 solution (FFT texture features) | Teaching cell | `B2-024/lessons/04-semi-supervised-pseudo-labeling.ipynb` (feature step); `torch.meshgrid` may instead go in lesson 05 §3 "grid operator" |
| `numpy.pad` | r1-001 p05 solution | Teaching cell | `01-F1` lesson on arrays (`lessons/01-arrays-and-indexing.ipynb`) |
| `sklearn.preprocessing.RobustScaler` | r1-001 p09 solution | Teaching cell | `09-C4` lesson 02 (kNN and scaling), next to `StandardScaler` |
| `.copy_` | r1-001 p08 statement, provided code | Rule-1 one-line comment in the statement | — |
| `tempfile.TemporaryDirectory` | r1-001 p09 solution, infrastructure | Rule-1 comment in the solution only | — |
| `shutil.copy2`, `subprocess.run` | r1-001 p09 solution, infrastructure | Rule-1 comment in the solution only; not exam content | — |

Each teaching cell is a marked markdown-and-code pair (D5(c)). It goes before any trailing answer section of its notebook (`tools/publish.py` `answer_regions`), so it is not swallowed into the answers; in C4 lesson 01 that means after cell 22 and before the closing answers. It adds no concept tag and changes no practice item or answer.
Prerequisite and coverage checks work on manifest concept tags, not callees, so they are unaffected.
Any further prose-mandated callee that Task 1 finds is added to this table and reviewed in the content gate.

### D7 — Comment wording standard

- Write in plain words and the present tense. Say what the call returns or does, e.g. `# np.argmax: index of the largest entry`.
- Name the meaning of the arguments actually used, not every parameter.
- Use the book's notation: shapes as `(n, d)` and the same variable names.
- No URLs, and no "see the docs".
- Keep inline comments within 80 columns. The PDF code column is narrower than ruff's 100 columns, and code wraps there (`code-overflow: wrap`). Anything longer goes in a block above.
- In statement notebooks:
  - Comments explain provided code only.
  - One line each, and only rules 1 and 3.
  - Never name an identifier the student must define, and never hint at the approach.

### D8 — Test-coupled notebook text

Some tests read notebook source by cell index, or match literal substrings: the Plan 019 marker tests, mutation targets, and statement-contract tests.

- Task 1 records which notebooks and cells are referenced this way.
- The protected notebook `book1/units/10-C5-embeddings/lessons/01-tokens-and-embeddings.ipynb` is not edited. Its path matches the guard's protected "token" category, and its only exception is the byte-pinned Plan 031 rename. Its book-first callees are explained in the C5 card's "New in this unit" part instead. The check accepts that for this one path, which is listed in the waivers file with reason `guard-protected`; it does not count toward the cap. Unit-first reminders still apply in C5's other notebooks.
- An added comment must never land inside a substring that a test or mutation target matches. Where it would, the comment goes in a block above the statement. Tests are not edited to accommodate comments.

### D9 — Dispatch and batching

- **Tooling (Tasks 1–2):** one Opus subagent.
- **Annotation (Task 3):** Opus subagents, in teaching order. Each works from the check's failure list.
  - F1 is its own first batch. Its results settle the baseline, graduated and no-reminder lists before the rest fan out.
  - After F1, batches of 3–4 units.
  - A batch annotates its units' lessons, statements and solutions. This is annotation of existing code, not authoring or solving, so the statement/solution session separation does not apply.
  - Each batch reruns the check, D5, and the targeted tests for its units before committing.
- **Cards and D6 teaching cells (Task 4):** one Opus author.

## Implementation tasks

- [x] **Task 1 — Inventory.**
  - Remap the survey to the post-031 paths.
  - Run the check in report mode and record real per-rule counts per unit and book. Report the rule-2 count for `size`, `dtype` and `device` separately, so the list can be trimmed if it reads as noise.
  - Scan statement prose for prose-mandated callees (D6).
  - List cell-index and substring couplings (D8).
  - Settle the semantic-keyword, graduated and no-reminder lists, and record them in this plan.
- [x] **Task 2 — Tooling.**
  - `tools/checks/api_comments.py`, the baseline and waiver YAMLs, and `scripts/verify-comment-only.py`.
  - Tests (D4), `cli.py` `SUBCOMMANDS` registration, and the `ci-local.sh` step-5 loop.
  - The check starts in report mode (prints, exits 0). Task 5 switches it to enforcing.
- [ ] **Task 3 — Annotate** units in teaching order with rules 1–4: F1 first, then the rest of Book 1, then Book 2, then the mock tests (rule 1 in statements and solutions; the D6 infrastructure comments).
- [ ] **Task 4 — Cards and teaching cells.** Add the API cards (D3) and the D6 teaching cells, then regenerate the material inventories and course structure with their tools.
- [ ] **Task 5 — Verification phase.**
  - `api-comments` runs in enforcing mode and passes for both books. Record the waiver count against its cap.
  - `scripts/verify-comment-only.py --base main` passes, (a)–(f).
  - `scripts/ci-local.sh --all-books` is ALL GREEN on a clean tip. That covers solution execution, hygiene, the register, mutation checks, both publish audits (including the solution-isolation fingerprints) and the pre-merge guard.
  - Rebuild the editions. Spot-check that comments wrap readably in the print edition's code blocks, and record page-count deltas.
- [ ] **Task 6 — Content gate, post-execution report, PR, `pre-merge-guard --pr`, squash-merge.**

**Content-gate duties for this plan.** There is no blind solving, because no problem or answer changes. Each reviewer:
- reads every added comment in statement and mock-statement notebooks (the leak surface);
- reads a random sample of at least 60 other added comments for accuracy against D7;
- reads all cards and D6 teaching cells;
- reviews the tooling.

## Out of scope

- Rewriting or removing existing comments or prose (D2).
- The difficulty-ladder recommendations; the user decides those separately.
- Any change to answers, data, seeds, or practice statements beyond comments.
- Editing the guard-protected C5 tokens notebook (D8).
- The verification-phase rule is satisfied by Task 5. This plan ships no new units or mock tests.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Round 1

- `[self]` Should Fix: test-coupled text. Tests index notebook cells (Plan 019 marker tests, statement contracts), and mutation targets match substrings, so inserted cells or same-line comments could break them. Resolved by D5(d) and D8.
- `[sol]` REJECT.
  - [FIXED] M1: the protected C5 tokens notebook cannot be edited. Resolved by D8: excluded from editing, card carries its explanations, listed as a `guard-protected` waiver.
  - [FIXED] M2: D5 contradicted the D6 code cells. Resolved by marked D6 code cells, with pre-existing cells matched by id (D5(a), (c), (d)).
  - [FIXED] M3: "explained" was not tied to the call. Resolved by D4's call-bound evidence: the comment must name the callee or keyword; the harness marker is restricted by location; reviewers read every statement comment.
  - [FIXED] M4: the D6 owner table was missing. The table is now in D6.
  - [FIXED] S5: the parser boundary. Magic and shell lines are rejected, comments are tokenized from the original source, and `# %%` is an ordinary comment.
- `[fable]` APPROVE WITH NITS, conditional on M1 and M2.
  - [FIXED] M1: rule 3 contradicted the card, and was the main source of noise. Resolved by the two-part card plus the graduated and no-reminder lists (D1, D3).
  - [FIXED] M2: the harness exemption. Resolved: it is outside first use, restricted by location, and has a block form for boilerplate (D1 rule 4).
  - [FIXED] S1: rule-2 trigger set (D1). S2: D6 table, including prose-mandated callees. S3: the statement restrictions plus the gate reads every statement comment (D4, D7, Task 6). S4: the waiver denominator (D4). S5: the markdown window before and after, backticked exact names outside LaTeX, and reuse of `tolerance.py` (D4). S6: wiring, the verifier not in `ci-local.sh`, and fingerprints (D4, D5, Task 5).
  - [FIXED] N1: no-reminder list. N2: an 80-column inline limit, readable wrapping in place of "no overfull lines". N3: fresh ids and `nbformat.validate`. N4: the bridge notebook's order. N5: F1 as the first batch. N6: `.view` and `ModuleList` reclassified as prose-mandated.

### Round 2

- `[sol]` REJECT.
  - [FIXED] Must Fix: index preservation in D5(d) contradicted the D6 insertion. Now only index-referenced cells keep their indices.
  - [FIXED] Must Fix: the CLI registry is `SUBCOMMANDS`.
  - [FIXED] Should Fix: scope interface. The check runs over the whole book in step 5; `ci_scope.py` is unchanged.
- `[fable]` APPROVE WITH NITS. All round-1 findings resolved.
  - [FIXED] S1: the statement rule is base-free, with identifier extraction defined (D4).
  - [FIXED] S2: the mock harness location is narrowed to paper-provided setup and answer-pin cells (D1 rule 4).
  - [FIXED] Nits: the B2-024 owner is named; D5(d) reworded; the `.view` notebook named; `size`/`dtype`/`device` counted separately; C5 reminders still apply.
- `[self]` APPROVE.

### Round 3

- `[sol]` REJECT.
  - [FIXED] Blocker: the base-free identifier rule failed on an existing scaffold comment, `# YOUR CODE HERE (call standardize)` in C4 p08 line 58, and the plan's "no existing comment" claim was false. The check's rule is narrowed to comments it counts as call evidence. The full no-added-hint rule moves to the base-aware verifier (D5(f)). The false claim is removed.
  - Round-2 items verified resolved.

### Round 4

- `[sol]` APPROVE WITH NITS. The D4 and D5(f) split is confirmed, and the C4 p08 scaffold comment cannot count as call evidence. [FIXED] Nit: Task 5 now says "(a)–(f)".
- `[fable]` APPROVE. It confirmed the commits since round 2; no open findings.
- `[self]` APPROVE.
- **Gate passed** (3/3, no `[OPEN]` items).

## Implementation notes

### Task 1 — Inventory (2026-10-12, report mode, tip f60cd23)

**Survey remap.**
The pre-031 survey worklist is superseded by the check itself.
`python -m tools.checks.api_comments --root bookN [--unit ID] [--findings] [--csv FILE]` prints the per-unit table below and the open sites with post-031 paths (0-based cell indices), so Task 3 batches work from that list, not from `snippet-survey/worklist.csv`.
The check's counts differ from the survey's on purpose: evidence must name the callee (D4), harness is opt-in by marker, and rule 2 fires only on the fixed trigger set.
Until Task 3 adds the `# Checks:` / `# Boilerplate:` markers, harness code is counted as ordinary code, so rule-3 counts below include check-cell calls (`np.isclose`, `np.array_equal`, `torch.allclose`, ...) that the markers will remove.

**Real per-rule counts** (rule-subject sites; "open" = no call-bound evidence yet; "exempt" = graduated or no-reminder rule-3 sites, outside the denominator).

| unit | r1 | r1 open | r2 | r2 open | r3 | r3 open | r3 exempt |
|---|---|---|---|---|---|---|---|
| F1-scientific-python | 96 | 65 | 11 | 10 | 0 | 0 | 0 |
| F2-vectors | 17 | 14 | 2 | 2 | 14 | 11 | 6 |
| F3-multivar-calculus | 12 | 12 | 2 | 2 | 23 | 22 | 6 |
| F4-matrices | 16 | 15 | 0 | 0 | 20 | 18 | 10 |
| F5-probability | 13 | 13 | 2 | 2 | 22 | 21 | 21 |
| C1-ml-fundamentals | 12 | 10 | 3 | 3 | 18 | 16 | 20 |
| C2-linear-models | 19 | 19 | 3 | 3 | 24 | 24 | 36 |
| C3-gradient-descent | 6 | 6 | 0 | 0 | 19 | 19 | 23 |
| C4-classical-ml-practice | 42 | 26 | 3 | 3 | 20 | 19 | 27 |
| C5-embeddings | 14 | 7 | 3 | 3 | 22 | 13 | 23 |
| C6-neural-networks | 5 | 4 | 1 | 1 | 10 | 10 | 25 |
| F6-svd-spectral | 7 | 5 | 2 | 2 | 22 | 19 | 30 |
| C7-pytorch | 31 | 16 | 9 | 9 | 7 | 7 | 20 |
| F7-kernels-convex-optimization | 7 | 7 | 0 | 0 | 16 | 16 | 17 |
| C8-neural-training | 44 | 37 | 7 | 7 | 40 | 38 | 30 |
| C9-dimensionality-reduction | 4 | 4 | 5 | 5 | 58 | 56 | 37 |
| C10-cnn-transfer | 22 | 15 | 6 | 6 | 58 | 52 | 27 |
| C11-competition-craft | 18 | 16 | 0 | 0 | 29 | 29 | 20 |
| C12-classical-models | 19 | 13 | 1 | 1 | 37 | 34 | 27 |
| r1-001 (rule 1 only) | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| B2-019-attention-transformers | 26 | 26 | 16 | 16 | 51 | 50 | 22 |
| B2-020-language-transformers | 22 | 22 | 3 | 3 | 38 | 38 | 10 |
| B2-021-cross-modal-transformers-vision | 27 | 27 | 4 | 4 | 57 | 55 | 9 |
| B2-022-probabilistic-latent-models | 31 | 23 | 4 | 4 | 71 | 69 | 16 |
| B2-023-generative-models-diffusion | 11 | 10 | 2 | 2 | 78 | 71 | 14 |
| B2-024-gpu-scientific-ml-capstone | 30 | 29 | 3 | 3 | 91 | 85 | 16 |
| r2-001 (rule 1 only) | 8 | 8 | 0 | 0 | 0 | 0 | 0 |

| book | rule-subject sites | rule 1 | rule 2 | rule 3 | open (r1 / r2 / r3) | graduated / no-reminder exempt | waiver cap (2%) |
|---|---|---|---|---|---|---|---|
| Book 1 | 929 | 410 | 60 | 459 | 793 (310 / 59 / 424) | 320 / 85 | 18.6 |
| Book 2 | 573 | 155 | 32 | 386 | 545 (145 / 32 / 368) | 85 / 2 | 11.5 |

By notebook kind, Book 1 sites sit in lessons (r1 270, r2 34, r3 307), solutions (67 / 26 / 101), statements (r1 66, r3 51) and review (r1 1); Book 2 in lessons (76 / 14 / 207), solutions (69 / 18 / 160) and statements (r1 2, r3 19).
Every unit also reports "missing API card" until Task 4.

**Rule 2 for `size` / `dtype` / `device`** (reported separately, D1): Book 1 1 / 16 / 1, Book 2 0 / 5 / 5.
All three stay in the trigger set for now; `dtype` carries most of the weight (`np.array(..., dtype=int)`, `torch.tensor(..., dtype=torch.float64)`), which is a genuine new call mode.
Rule-2 elements overall: Book 1 `axis` 17, `dtype` 16, `dim` 5, positional modes 9, `keepdims` 3, `ddof` 2, one each of `p`, `size`, `return_counts`, `indexing`, `full_matrices`, `keepdim`, `generator`, `device`.

**Prose-mandated callees (D6).**
The scan covered every practice-statement and mock-problem markdown cell plus `book*/mocktests/*/theory/*.md`, looking for backticked calls not used in any unit's code.
It confirmed `Tensor.view` (r2-001 p01 cell 4) and `torch.nn.ModuleList` (r2-001 p01 cell 6), already in D6.
The other hits are attributes (`.T`, `.shape`, `.data`, `.weight`, `.requires_grad`), student-defined methods (C7 p06 `.apply`/`.twice`/`.label`), banned calls quoted in prose (C11 p10 `np.random.permutation`), or calls a unit already uses (`np.char.capitalize` in C11 p18 code, `torch.cuda.max_memory_allocated` in B2-024 lesson 01).
No new D6 rows from prose.
The check's mock rule-1 list adds two mock-first callees that the survey's 12 did not name (needs a D6 decision):
- `.copy_` — r1-001 `problems/p08.ipynb` cell 5 (provided code in a statement; a one-line rule-1 comment is enough, since Book 2 units use it later);
- `tempfile.TemporaryDirectory` — r1-001 `solutions/p09_solution.ipynb` cell 14, infrastructure beside `shutil.copy2` / `subprocess.run` (rule-1 comment in the solution only).

**Settled lists** (in `tools/checks/api_comments_baseline.yaml`; F1's Task 3 batch may still trim or extend them, D9).
- `semantic_keywords`: the D1 set — `axis`, `bias`, `ddof`, `device`, `dim`, `dtype`, `full_matrices`, `generator`, `indexing`, `keepdim`, `keepdims`, `key`, `p`, `reduction`, `replace`, `return_counts`, `size`, `weights` — plus four keywords added during Task 3: `bins` and `density` (`np.histogram` / `plt.hist`), `minlength` (`np.bincount`) and `ord` (`np.linalg.norm`).
- `positional_callees`: `arange`, `full`, `linspace`, `normal`, `ones`, `randint`, `split`, `zeros`, plus `where` (added at the content gate, so the three-argument `np.where` / `torch.where` after a one-argument use, or the reverse, is a new mode). A positional mode counts as explained when the comment names the callee or one of the `positional_words` (`start`, `stop`, `step`, `num`, `low`, `high`, `loc`, `scale`, `shape`, `size`, `fill`, `sections`, `mean`, `std`); otherwise existing comments such as `# start 2, step 3, stop excluded` would not count.
- `graduated` (exempt from rule 3 once used in 3 earlier units): `.all`, `.argmax`, `.astype`, `.copy`, `.integers`, `.max`, `.mean`, `.min`, `.normal`, `.plot`, `.reshape`, `.sum`, `.tolist`, `ValueError`, `all`, `any`, `enumerate`, `next`, `np.abs`, `np.allclose`, `np.arange`, `np.argmax`, `np.array`, `np.asarray`, `np.isclose`, `np.linspace`, `np.max`, `np.maximum`, `np.mean`, `np.ones`, `np.random.default_rng`, `np.sqrt`, `np.sum`, `np.where`, `np.zeros`, `plt.plot`, `plt.subplots`, `sorted`, `zip`; later batches added `.round`, `AssertionError`, `np.all`, `np.argmin`, `np.array_equal`, `np.full`, `np.round` and `np.sort` (47 in all).
Not all are book-first in F1–F5: `all` and `enumerate` are book-first in C1, `.all` in C2, `next` in C4, `sorted` in C5, `any` in F7 and `AssertionError` in C12; the rest are book-first in F1–F5.
`graduation_units` is 3 (D1): a graduated callee is exempt from rule 3 only in a unit that comes after three earlier units using it, so its second and third units still need a reminder (inline or card). It had been lowered to 1 after the F1 batch; the content gate restored 3. The 85 rule-3 sites reopened by that and by the boilerplate scope fix (below) are closed by card "Also used here" entries; two `torch.set_num_threads` sites got inline reminders.
- `no_reminder`: `.legend`, `.set_title`, `.set_xlabel`, `.set_xlim`, `.set_ylabel`, `.set_ylim`, `math.isfinite`, `plt.figure`, `plt.legend`, `plt.show`, `plt.tight_layout`, `plt.title`, `plt.xlabel`, `plt.ylabel`, `torch.cuda.is_available`.
- `baseline`: the survey's `BASE_BUILTINS` and `BASE_METHODS`, unchanged.
- `method_families`: receivers built by a lower-case `np.` / `torch.` / `pd.` function are typed `ndarray` / `Tensor` / `DataFrame`; on a typed receiver a baseline method name is keyed per family (`ndarray.append` is not `list.append`). `keyed` (non-baseline methods split per family) starts empty; everything else is keyed by name (`.sum`, `.view`).
- `mock_rules: [1]`: mocks apply rule 1 only, as Task 3 describes.
- Named idiom `book-root-finder`: first explained at C4 lesson 01 cell 22.

### D8 — test couplings to notebook text

All indices are 0-based (Python list indexing); no test uses 1-based indices.
The pins below are encoded in `scripts/verify-comment-only.py` `INDEX_PINNED`, or enforced by its generic rules.

**Cell-index references** (Plan 019 inventory `tests/fixtures/plan019-path-inventory.yaml` via `test_integration.py` `_plan019_assert_live_migration_cells`, and `test_clean_checkout.py`). Each cell must keep its index and still contain `USAAIO_BOOK_ROOT` or `book_root`; none may contain `pyproject.toml`.
- r1-001: `problems/p05` 1, `problems/p07` 1, `problems/p09` 3, `solutions/p05_solution` 1, `p07_solution` 1, `p09_solution` 2 and 14.
- `09-C4/lessons/01-pandas-and-data-loading` 22 (D6 `json.loads` teaching cell goes after it; the notebook ends in an open `## Checkpoint Answers` section from cell 33).
- `10-C5`: lessons 02 and 03 cell 1; practice p05, p07–p10, p13, p14, p16–p20 (statement and solution) cell 1; p11, p12 cell 2. Lesson 01 (tokens) is guard-protected and pinned in `test_scope.py`.
- `16-C9`: lesson 03 cell 1; practice p07, p09, p14 cell 1; p12 cell 2.
- `17-C10`: lessons 02 and 03 cell 1; statements p08, p09, p11, p12, p15, p16, p19 cell 1; p14, p17 cell 2; solutions p08, p09, p11, p12, p14–p17, p19 cell 2.
- Negative indices: solutions in B2-019, B2-020, 19-C12 (`cells[-2]` is `### Answer check`, `cells[-1]` the assert cell); B2-020/022/023 check tests require the failure at `len(cells)-1`; B2-021–B2-024 solutions allow only code after the last `### Answer check`; capstone `cells[-1]` must be code; r2-001 p02/p04/p05's last code cell is the `test_call_count` check. So no new cell goes after `### Answer check` in any solution (verifier rule).
- `cells[0]` header checks: B2-020 solutions, B2-021–B2-024 student surfaces (B2-024 solutions too), and `verify-register.py`'s first markdown cell of every Book 1 practice notebook. Nothing is inserted at the front.
- B2-022/B2-023 latent and generative checks read `code_cells[0]` and `code_cells[1]`; no code cell may be inserted before or between them.

**Literal-substring and mutation targets, by notebook** (comments must not repeat, split or trail these; where a comment is needed it goes in a block above, D8):
- `15-C8/practice/p16_solution` cell 3: the five-line block from `optimizer.zero_grad(set_to_none=True)  # PLAN017_MUTATION_TARGET: C8-p16-zero-grad` to `loss.backward()`; marker cell 5; `model.eval()\n    with torch.no_grad():\n        predictions =` verbatim.
- `15-C8/practice/p23_solution` cell 3: `optimizer.step()  # PLAN017_MUTATION_TARGET: C8-p23-optimizer-step`.
- `15-C8/practice/p14_solution`, `p21_solution`: the `loss=…`/`gradient/=…`/`grad/=len(y)` literals (count 1 each).
- `15-C8` statements p05–p10, p14, p15, p21: the statement code from its probe marker (`probe_p05 =`, …, `rng_p21 =`) to the end must appear verbatim in the solution, so any comment added there must be mirrored identically in the solution.
- `15-C8` cell-id matches: `p04-m1`, `p10-c2`, lesson 03 `c11s3015`, lesson 04 `c11s4010`/`c11s4016` plus literals over all cells (`torch.Generator(device="cpu")`, `generator=data_generator`, …).
- `17-C10/practice/p10_solution` cell 4 and `p27_solution` cells 2 and 8: `PLAN017_MUTATION_TARGET` lines; p27's move mutation pastes into the next code cell after the verifier (cell 5).
- `19-C12/practice/p07`, `p08`, `p10`, `p13`, `p29_solution` cell 2: two-line `# PLAN018_MUTATION_TARGET: …` comment plus code line; markers count 1.
- `19-C12/practice/p20_solution`: the `_lowest_seed_near_minimum` cell; anchors `np.isclose(inertias, minimum, atol=atol, rtol=rtol)`, `atol=atol`, `rtol=rtol`, `np.argmin(seeds[candidates])` must stay unique — no comment may contain them.
- `19-C12/practice/p22_solution`: no comment may contain `0.2` (also `0.25`, `10.2`).
- `19-C12` lessons 01–03 tests read `str(cell["source"])`: keep the stored source representation (verifier rule).
- `B2-019` solutions p03, p06–p10, p15, p17, p24: replacement literals (`np.sqrt(X.shape[-1])`, `scores = (q @ k.T) / np.sqrt(q.shape[1])`, `masked_scores = scores + mask` four-line block, `return heads.transpose(0, 2, 1, 3).reshape(b, n, h * d_h)`, …); the first cell containing the literal is mutated, so no earlier comment may quote one. Statements p09/p17 forbid `nn.Embedding`; p02 forbids `before simplifying`. Lessons 00 and 04 (D6 `ModuleList` target) are executed with pinned values: teaching code must not consume the random generator.
- `B2-020` solutions p07, p11, p18–p21, p24: whole-function literals (`def update_embedding_table…`, `def apply_mlm_mask…`, `def shift_targets…`, …) with count 1 — no comment inside these functions.
- `B2-021` solutions p17–p20, p24: fragment literals inside functions (`optimizer.step()`, `loss.backward()`, `torch.cat((decoder,skip),dim=1)`, `torch.bmm(adjacency_float,nodes)/degree`, …), one AST definition per function; lesson 02's first `atol=1e-6, rtol=1e-6`. Statements forbid comment lines matching `(?im)^#{1,4}\s*(solution|answer)\b`.
- `B2-024` solutions p18–p22, p26, p27: exact literals (`Z = torch.cat([features(xl), features(pool)])`, `losses = train_inverse(…)`, …); `assert capstone_data.test_call_count(...) == N` lines take no trailing comment; no comment may mention `final_test_score(` before its first call. Lesson 01's tail from `## 10.` is markdown-only.
- r2-001 solutions p01–p05: anchors in `test_r2_001_checks.py` (`return torch.tril(torch.ones(n, n, dtype=torch.bool))`, the `table[:, 0::2] = torch.sin(p * omega)` pair, `total = recon_mean + beta * kl_mean`, the `test_call_count` asserts, …) must stay unique; asserts that end in `\n` take no trailing comment.

**Generic couplings.**
- No code cell may contain `pyproject.toml` (Plan 019 live rule); no comment may contain `# tol-exempt:`, `# SOLUTION` or `answer_key`.
- Lesson and review notebooks often end in an open `## Checkpoint Answers` / `Self-quiz answers` section (`tools/publish.py` `answer_regions`); the D3 card must open with its own unnumbered `## ` heading to close it. The check and the verifier both enforce this.
- B2-019–B2-024 lessons count `^## N. ` headings over all cells (comments included): D6 markdown cells add no headings (verifier rule), and no code comment may start `## 1.`.
- B2-021 cell ids must be unique across all solutions; 36 nbformat-4.4 notebooks (F3 and F5 practice p01–p18 solutions) carry no ids, and new cells there must not add one (verifier rule).
- Material inventories hash cell sources: Task 4 regenerates `book*/curriculum/material-inventory.yaml` with `python -m tools.audit_curriculum --root bookN`.
- Statement A–E option lines, `## Accelerator extension` placement and scope anchors key on markdown only; code comments are safe there.

### Task 2 — Tooling

- `tools/checks/api_comments.py`, registered as `api-comments-check` and run in the `ci-local.sh` step-5 loop; ~6 s for Book 1 and ~8 s for Book 2 (which rescans Book 1 first).
- `tools/checks/tolerance.py`'s `_canonical_module` / `_import_aliases` / `_resolved_name` gained an optional module map, a `passthrough` flag and longest-dotted-prefix canonical names; the tolerance check's behaviour is unchanged.
- Report mode: `enforce: false` in `tools/checks/api_comments_baseline.yaml`; Task 5 flips that one value.
- Waivers: `tools/checks/api_comments_waivers.yaml` holds only the D8 `guard-protected` entry for the C5 tokens notebook (0 counted waivers). Its rule-1 sites are explained by the C5 card's "New" part; today 6 of its 7 book-first callees are already explained in nearby markdown, `repr` is not.
- `scripts/verify-comment-only.py --base <ref>` implements D5 (a)–(f) plus the D8 rules above; passes against `main` (0 changed notebooks).
- Tests: `tests/test_api_comments.py` (36) and `tests/test_verify_comment_only.py` (22).
- Design choices beyond the text: the unit card is never markdown evidence (c), only (d); in statements only the single comment line directly above a statement counts as block evidence (the one-line rule); a stale waiver is a finding; a `graduated` entry that no notebook calls is a finding.

### Content-gate tooling fixes

- Receiver typing follows execution order: a call sees only the bindings made before it, and an assignment binds at its end position, so `names = []` … `names.append(…)` … `names = torch.tensor(names)` keys the append as a list append, not `Tensor.append`. Re-binding a name to a literal (`[]`, `{}`, a string, …) clears its type; any other unknown value keeps the earlier type (`x = x.reshape(…)`).
- The false `ndarray.append` (F1) and `Tensor.append` (B2-024) card entries this caused are gone.
- Mock-statement `# Checks:` markers must sit on paper-provided cells (D1 rule 4). r1-001 p09 cells 1, 3 and 6 are not mirrored in `p09_solution` (its setup imports more, renames `FEATURES` and runs a different contract loop), so their markers were removed; their calls are not book-first, so no rule-1 comment is needed.
- `# Boilerplate:` blocks exempt only `named_idioms.book-root-finder.callees` (`os.environ.get`, `pathlib.Path`, `pathlib.Path.cwd`, `.resolve`, `.is_file`, `.is_dir`, `next`). The data-module loader calls (`importlib.util.*`) and `torch.set_num_threads` in those blocks are ordinary calls again; their unit-first sites are reminded inline or in the B2-022/023/024 cards.

## Content Review

## Post-execution report
