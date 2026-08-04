# Plan 005 — Teaching Units Tranche 1: F1 + F2 + C1

> **For agentic workers:** per-task commits; drafting dispatches to parallel
> `general-purpose` subagents per `CLAUDE.md ## Agent dispatch`.

**Goal:** Ship the first three units of the suggested order — `F1-scientific-python`, `F2-vectors`, `C1-ml-fundamentals` — each as lesson notebook + practice set + manifest, passing all five plan-004 checks, teachable by a Calculus AB + basic Python student with zero outside material.

**Architecture:** Per unit: `units/<id>/lesson.ipynb` (narrative + worked examples + inline checkpoints), `units/<id>/practice/pNN.ipynb` (student) + `pNN_solution.ipynb` per problem, `units/<id>/manifest.yaml` (plan-004 schema). Manifest-first TDD analogue: write the manifest, run coverage-check RED (missing files), draft to GREEN.

**Tech Stack:** deps added to the project: `jupyter-core`-level execution via `nbclient` + `jupyter` (needed by ci-local step 3 the moment solutions exist — this plan adds the dep), numpy, matplotlib (F1/F2 content), scikit-learn + pandas NOT yet (C1 teaches concepts with numpy-built examples; sklearn arrives with C4).

## Global Constraints

- Syllabus is law: each unit teaches EXACTLY its `teaches` list (prereq-check enforces manifest==syllabus); `concepts_used` ⊆ baseline ∪ ancestors' teaches.
- Accessibility: lesson text assumes Calc AB + basic Python + declared prereqs ONLY. Every new concept gets: motivation → definition → worked example → checkpoint exercise.
- Hygiene: student notebooks contain no outputs/solutions; solutions run top-to-bottom clean, seeded (`np.random.default_rng(SEED)` with SEED literal per notebook).
- Practice coverage: every taught concept exercised by ≥1 problem (coverage-check); target 6-9 practice problems per unit, each tagging 1-3 concepts.
- Public repo: all content original; no verbatim past-test text.
- Style: problems follow blueprint style_rules register (imperative task statements, exact identifiers for code tasks) so unit practice doubles as exam-form training.

---

### Task 1: Manifests first (all three units)

**Step 0 (deps):** `uv add jupyter nbclient ipykernel numpy matplotlib` (ipykernel registers the kernel `jupyter execute` needs); commit pyproject/uv.lock separately ("chore: notebook execution + content deps").

**Files:** `units/F1-scientific-python/manifest.yaml`, `units/F2-vectors/manifest.yaml`, `units/C1-ml-fundamentals/manifest.yaml`

Practice ids are unit-prefixed per the plan-004 schema example (`F1-p01`, `F2-p03`, `C1-p08`); file paths stay `practice/pNN.ipynb`. `prereq_units`: F1 `[]`, F2 `[F1-scientific-python]`, C1 `[F1-scientific-python]` (== syllabus).

Practice maps (id → concepts, the load-bearing coverage decisions):

F1 (8 concepts): p01 [numpy-arrays, array-indexing-slicing]; p02 [elementwise-ops, broadcasting]; p03 [broadcasting, vectorization]; p04 [aggregation-axis]; p05 [random-seeding]; p06 [matplotlib-basics]; p07 [vectorization, aggregation-axis] (integrative: loops-banned rewrite).
- concepts_used: baseline python only.

F2 (8 concepts): p01 [vectors-and-norms]; p02 [distance-metrics, vectors-and-norms]; p03 [dot-product, cosine-similarity]; p04 [unit-vectors, orthogonality-orthonormality]; p05 [projection, residuals]; p06 [projection, cosine-similarity] (NumPy implementation, no-loops constraint); p07 [orthogonality-orthonormality, dot-product] (by-hand proof-style).
- concepts_used: baseline + F1 teaches.

C1 (9 concepts): p01 [supervised-vs-unsupervised, clustering-concept] (multi-part: p01a MC on task classification, p01b short-answer on what clustering finds without labels — both concepts substantively exercised, not token-mentioned); p02 [train-test-split]; p03 [overfitting, bias-variance-intuition]; p04 [accuracy-precision-recall]; p05 [f1-score, class-imbalance]; p06 [f1-macro] (compute from a confusion table with NumPy); p07 [bias-variance-intuition, overfitting] (MC); p08 [class-imbalance, accuracy-precision-recall] (scenario analysis).
- concepts_used: baseline + F1 teaches (metrics computed with numpy arrays).

**Steps:** write manifests → `uv run usaaio-tools prereq-check` must PASS (manifest==syllabus) → `coverage-check` must FAIL RED with missing-file errors (proves the check drives drafting) → commit ("feat: unit manifests for F1/F2/C1 (coverage RED)").

---

### Task 2: Draft F1 (dispatch subagent 1)

Lesson `lesson.ipynb` (~10 sections): why arrays beat lists; creating arrays; dtype/shape; indexing+slicing (incl. boolean/fancy); elementwise ops; broadcasting rules (the 3-step rule, worked shape examples); vectorization (rewrite-the-loop exercises, exam API-ban context); axis aggregations; RNG + seeding discipline; matplotlib line/scatter/hist + labels. Checkpoints after each section.
Practice per the Task-1 map: student notebook = statement + starter cells + `# YOUR CODE HERE`; solution notebook = full worked solution + brief explanation, seeded, runs clean.

### Task 3: Draft F2 (dispatch subagent 2, parallel with Task 2)

Lesson: vectors as data points (ties to F1 arrays); norms/distance — Euclidean (why √Σx²; triangle intuition) AND Manhattan, so `distance-metrics` earns its plural; dot product (algebraic + geometric, cos link); cosine similarity; unit vectors + normalization; orthogonality/orthonormality; projection + residual (the picture, the formula, the NumPy one-liner). By-hand and NumPy work mixed; p07 is proof-style (reasoning-required register).

### Task 4: Draft C1 (dispatch subagent 3, parallel)

Lesson: the learning-from-data framing; supervised vs unsupervised vs clustering; train/test discipline (why holding out data matters); overfitting (memorization-vs-simple-rule demo: a lookup-table classifier vs a single threshold on seeded 1-D data, train/test scores computed with plain numpy — deliberately NO curve-fitting API, keeping the closure free of regression concepts); bias-variance INTUITIVE treatment (explicit scope note); metrics — accuracy, precision, recall, F1, macro-F1 (confusion-matrix arithmetic, worked examples); class imbalance (why accuracy lies; the 99%-negative demo). MC practice items use exactly five options A-E; the student notebook records the choice as a variable (e.g. `answer_p01 = "?"`) with the correct letter appearing ONLY in the solution notebook (hygiene-safe capture).

### Notebook conventions (paste VERBATIM into all three drafting prompts)

- nbformat 4, kernelspec python3; first cell: `import numpy as np` (+`import matplotlib.pyplot as plt` where used); solutions set `SEED = 20260804` and `rng = np.random.default_rng(SEED)`.
- Lesson section headers: `## N. Title`; each section ends with `### Checkpoint N` (1-3 quick exercises, answers inline-collapsed at lesson end, not in checkpoint cells).
- Practice student notebooks: title cell `# <unit> — Practice pNN`, problem statement, starter cells with `# YOUR CODE HERE` (code) or `answer_pNN = "?"` (MC/short-answer); NO outputs, NO solution text.
- Solution notebooks: same title + ` — Solution`, complete worked code + 2-4 sentence explanation per part; must run top-to-bottom clean.
- Cross-unit references use syllabus concept ids/titles ("as covered in F1-scientific-python"), NEVER internal section numbers of concurrently-drafted lessons.
- Prose must not use vocabulary surface forms outside the unit's closure (accessibility sweep enforces; per-unit allowlist documents deliberate exceptions).

---

### Task 4b: Enrichment pass (USER-DIRECTED scope amendment, 2026-08-04)

Mid-plan the user directed increased practice variety and lesson depth; the bar is now
codified in `docs/unit-standards.md` (created by this amendment) and applies here
retroactively. For EACH of F1/F2/C1, a follow-up drafting pass must:
1. Extend practice to 10-14 problems meeting the mandated type mix (≥2 exam-style MC,
   ≥3 constrained coding, ≥1 proof-style, ≥1 integrative multi-part, ≥1 scenario,
   ≥1 challenge) with difficulty tags; update the manifest maps accordingly
   (prereq/coverage checks re-run after).
2. Deepen lessons: add Common Pitfalls, Exam Connections, Going Deeper sections and
   ≥2 fully worked exam-style examples; raise checkpoints to ≥2 per section.
3. Update estimated_minutes.
This amendment is user-authorized scope expansion (recorded verbatim in the gate record);
the content gate reviews the ENRICHED units against docs/unit-standards.md.

### Task 5: Verification phase (NAMED — design §2 rule)

**Scenarios:** all five checks × three units; solution execution; accessibility sweep.

Design-§2 clause mapping for UNITS (the clause's wording targets mock tests; each item is
satisfied in unit-appropriate form or explicitly deferred — never silently dropped):
- *solutions reproduce the answer key* → every solution notebook ends with an
  `### Answer check` assert cell verifying its computed results against expected values;
  execution passing = answers reproduced (units have no manifest answer_key field).
- *manifests validate* → prereq/coverage checks below (they load and validate manifests).
- *PDF builds* → mock-test papers only; remains `SKIP (plan 011)` in ci-local — explicit
  deferral, stated here per the design's exemption pattern.
- *difficulty/timing budget stated* → each unit manifest gains an informational
  `estimated_minutes: {lesson: N, practice: N}` field (loader ignores unknown keys;
  documented as advisory for the tutor).

**Acceptance criteria (exact):**
1. `uv run usaaio-tools prereq-check` → PASS (no drift, no untaught use).
2. `uv run usaaio-tools coverage-check` → PASS (was RED after Task 1; GREEN proves every taught concept has practice + all files exist).
3. `uv run usaaio-tools hygiene-check` → PASS (student notebooks clean).
4. `uv run usaaio-tools blueprint-check` / `overlap-scan` → vacuous-pass / PASS (no mocktests yet; overlap runs on corpus).
5. `bash scripts/ci-local.sh` → ALL GREEN, executing every `*_solution.ipynb` (22 notebooks) top-to-bottom including their `### Answer check` assert cells (this plan adds `jupyter`+`nbclient` deps and un-defers ci-local step 3 reality).
5b. Scripted spot check: every solution notebook contains ≥1 `assert` in its final cell (`grep`-level scan) — the unit-form answer-key reproduction criterion.
6. Accessibility sweep (scripted): lessons scanned with an id→surface-form map (e.g. `dot-product` → "dot product") for mentions outside baseline ∪ prereq-closure ∪ own-teaches, with a documented per-unit allowlist for deliberate colloquial uses (C1 may say "variance"/"varies" in the bias-variance scope note — the allowlist entry cites the scope note). Zero UNALLOWED hits. Substrings of own concept ids (e.g. "variance" inside bias-variance-intuition's own section) are excluded by the map construction. The formal check remains reviewer duty 8.
**Fixtures:** none beyond the real repo; the units ARE the fixtures for the tooling's first live run.

### Task 6: Ship

Content gate (4-way; duties: solve practice blind, verify solutions, accessibility as Calc AB reader, coverage quality — not token mentions). Post-exec report; TODO update **including the roadmap renumbering** (mock test moves to plan 011; tranches 006=F4+F3+F5, 007=C4+C2+C3, 008=C5+C6, 009=C7+C8, 010=F6+C9+C10; add roadmap item 012=course-structure doc mapping units to semesters/weeks with pacing from estimated_minutes — user context: formal multi-semester course). The renumbering step MUST also: (a) update `scripts/ci-local.sh`'s `PENDING (plan 006)` and `SKIP (plan 006)` strings to `plan 011`, and add a permanent step-3 line scanning every `*_solution.ipynb` final cell for `assert` (the 5b criterion becomes CI, so future edits can't silently drop answer checks) so answer-key reproduction and PDF-build ownership stay attached to the mock-test plan; (b) record the ownership reassignment in this plan's post-exec report (plan 004's doc stays as history). *Why this is not a judgment fork:* units-before-mock-test is entailed, not chosen — prereq-check requires every unit a mock problem cites to have a shipped manifest, and the blueprint's topic distribution spans clusters taught across all 16 units, so r1-001 cannot pass CI until the full roster ships. Final ci-local; push; PR; guard; squash-merge.

---

## Out of scope

- Units beyond F1/F2/C1 (tranches 006-010); mock tests (011); PDF rendering (with 011).
- sklearn/pandas/torch deps (arrive with the units that teach them).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` F1 p05 listed "sampling-free intro" — not a vocabulary id; manifest
   validation would fail. Trimmed to `[random-seeding]`.
2. `[FIXED]` C1's overfitting demo used numpy polyfit — a closure leak toward
   linear-regression (taught in C2, not an ancestor). Replaced with a
   memorization-vs-threshold demo in plain numpy.
3. `[FIXED]` MC answer capture in notebooks was unspecified vs hygiene rules →
   answer-variable convention with the letter only in the solution notebook.
4. `[NOTED]` Verified all three practice maps cover their full syllabus teaches lists
   (8+8+9 concepts) with exact vocabulary ids.

### Review 2 — [fable] Independent Fable 5, fresh context (2026-08-04)

- **Verdict**: APPROVE WITH NITS (raced self-review commit; its #1/#2 = self items 1/2,
  already fixed — the polyfit demo was replaced entirely, superseding the black-box option)
3. `[FIXED]` Zero-hits sweep unsatisfiable → id→surface-form map + documented per-unit
   allowlist; zero UNALLOWED hits.
4. `[FIXED]` Drafter coordination underspecified → verbatim notebook-conventions block
   added (kernel, SEED, headers, checkpoints, MC capture, no cross-lesson internals).
5. `[FIXED]` Manhattan added under distance-metrics.
6. `[FIXED]` C1 p01 multi-part (p01a MC + p01b short-answer).

### Review 3 — [codex] Codex GPT-5.5 (2026-08-04)

- **Verdict**: REJECT ×2 → design clarified, re-verdict requested
1. `[FIXED]` Verification phase vs design-§2 literal clauses → unit-form mapping added
   (assert-cell answer checks + criterion 5b; manifests via checks; estimated_minutes
   timing budget), and the design's PDF clause — whose §1/§3.4 scope is printable TEST
   papers — clarified in designs/000 (not a governance file) to say so explicitly.
   Units are notebook-native; mock-test plans carry the PDF obligation.

### Review 3 round 3 — [codex]

- **Verdict**: APPROVE WITH NITS
- `[NOTED]` Process concern recorded openly: the design's §2 PDF clause was clarified
  mid-review to resolve a live blocker. Mitigants: the amendment matches the design's own
  §1/§3.4 scope (reviewer-verified consistency), designs/000 is not governance-protected,
  and the change is visible in this plan's gate record + the PR diff for the user to see.
- `[NOTED]` ci-local plan-006→011 strings: planned in Task 6, correctly not yet landed.

### Review 4 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: REJECT (raced fixes; its #1/#3 already fixed) → re-verdict requested
2. `[FIXED]` BLOCKER: renumbering orphaned plan-004's "plan 006" ownership strings →
   Task 6 now updates ci-local's PENDING/SKIP strings to plan 011 and records the
   reassignment; rationale added for why the ordering is entailed, not a judgment fork.
4. `[FIXED]` ipykernel added to the dep list.
6. `[FIXED]` Dep-add got an explicit Task 1 Step 0.
7. `[FIXED]` Practice ids unit-prefixed per schema example.
8. `[FIXED]` prereq_units enumerated.
9. `[FIXED]` Notebook count fixed at 22.

### Review 4 round 2 — [glm]

- **Verdict**: APPROVE WITH NITS — all 9 fixes verified in-file; design edit judged sound.
- `[FIXED]` Assert-scan permanence → Task 6 wires it into ci-local step 3.

**GATE RESULT: PASS — 4/4** ([claude-self], [fable], [codex], [glm]); no open blockers.

## Verification record (Task 5, 2026-08-04)

- prereq / coverage / hygiene / blueprint / overlap: all PASS.
- ci-local ALL GREEN executing all 65 solution notebooks (+9 session, 3 overview,
  3 review notebooks verified by drafters); assert scan: 65/65 solutions end with
  answer-check asserts (criterion 5b).
- Accessibility sweep (id→surface-form map, closure-aware): 2 hits, both benign and
  allowlisted with justification — F1 "vector" = substring of its own
  "vectorization" concept; C1 "matrix" = the fixed compound "confusion matrix"
  (metrics domain, no linear algebra used). Zero unallowed hits.
- v2 type-mix compliance per drafter reports: F1 21 / F2 21 / C1 23 problems, every
  floor met (F1's constrained-coding count reaches 6 via two honestly-flagged
  dual-counted challenge problems — gate to judge); difficulty spreads ≈30/45/25;
  every concept ≥3 problems.

## Content Review

### Review 1 — [claude-self] inline (2026-08-04)

- **Verdict**: Approved with suggestions
1. Verification record above is the evidence base (all checks PASS, 65/65 solutions
   execute with asserts, accessibility sweep clean after two justified allowlist entries).
2. `[NOTED]` F1's constrained-coding floor relies on dual-counting two challenge
   problems — deferred to the external reviewers' judgment as flagged by the drafter.
3. `[NOTED]` The three units were drafted before the Fable-statements/sol-solutions
   split took effect; the gate's blind-solving compensates for the missing
   independent-solution-author property this once.

### Review 2 — [codex] Codex GPT-5.6-terra (2026-08-04)

- **Verdict**: Changes requested → fixed, re-verdict requested
1. `[FIXED]` C1 difficulty spread 26/52/22 (core-heavy) → honest retag of C1-p06
   (macro-F1 from a GIVEN table = mechanical drill, comparable to intro p04) →
   30/48/22, matching the F1/F2 profile the reviewer accepted.
2. `[NOTED]` All 9 blind solves matched official solutions; all 4 numeric normal-form
   MCs recomputed and matched; worked examples + pitfalls hand-traced clean in three
   sampled sessions; F1 dual-counting judged acceptable.
3. `[NOTED]` Reviewer's sandbox lacked the gitignored corpus + jupyter — verbatim
   comparison and notebook execution are covered by the local verification record
   (overlap-scan PASS against the real corpus; 65/65 solutions executed by ci-local).

### Review 3 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: Approved with suggestions
1. `[FIXED]` F1/C1 manifests lacked `type:` tags (floors drafter-asserted only) →
   backfilled on all 44 entries from the drafter rosters; F2 already had them.
2. `[FIXED]` estimated_minutes lesson totals added to F2/C1 (F1 already had one).
3. `[FIXED]` C1 review summary row now uses the `bias-variance-intuition` syllabus id;
   review.ipynb re-executed clean.
4. `[WONTFIX]` Kernelspec display-name drift ("Python 3 (ipykernel)" vs "Python 3") and
   C1's statement-before-imports cell order — cosmetic; all notebooks execute clean;
   normalizing 100+ notebooks risks churn for zero behavior change. Convention doc rules
   on future tranches.
5. `[NOTED]` All 6 blind solves matched; concept ≥3 recount clean; difficulty tags honest
   in all 6 sampled; constrained-coding contracts verified real in 5 sampled problems.
