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

Content gate (4-way; duties: solve practice blind, verify solutions, accessibility as Calc AB reader, coverage quality — not token mentions). Post-exec report; TODO update **including the roadmap renumbering** (mock test moves to plan 011; tranches 006=F4+F3+F5, 007=C4+C2+C3, 008=C5+C6, 009=C7+C8, 010=F6+C9+C10). The renumbering step MUST also: (a) update `scripts/ci-local.sh`'s `PENDING (plan 006)` and `SKIP (plan 006)` strings to `plan 011` so answer-key reproduction and PDF-build ownership stay attached to the mock-test plan; (b) record the ownership reassignment in this plan's post-exec report (plan 004's doc stays as history). *Why this is not a judgment fork:* units-before-mock-test is entailed, not chosen — prereq-check requires every unit a mock problem cites to have a shipped manifest, and the blueprint's topic distribution spans clusters taught across all 16 units, so r1-001 cannot pass CI until the full roster ships. Final ci-local; push; PR; guard; squash-merge.

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

## Content Review

(Pre-PR gate findings land here.)
