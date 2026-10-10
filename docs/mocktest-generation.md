# Mock-Test Generation Pipeline

The repeatable procedure for producing every `book1/mocktests/r1-NNN/`.
Book 2 (Round 2) mock tests follow the same pipeline with the extensions in
[Book 2 (Round 2) mock tests](#book-2-round-2-mock-tests).
Authoritative inputs: `book1/mocktests/blueprint.yaml` (test spec) and `book1/syllabus.md`
(concept vocabulary + unit DAG).
Design rationale: `docs/designs/000-project-design.md §2b`.

## Pipeline

1. **Blueprint** — select Book 1 and read `book1/mocktests/blueprint.yaml` at its current `blueprint_version`.
   Changing the blueprint is a reviewed change like any other (plan + gates).
2. **Instantiate** — create the test skeleton and problem-spec sheet.
   Run `uv run usaaio-tools --book book1 new-mocktest r1-NNN --date YYYY-MM-DD`.

   ```
   book1/mocktests/r1-NNN/
   ├── test.md          # front matter: instructions, duration, points table
   ├── theory/          # theory question sources (Markdown + math)
   ├── problems/        # student-facing programming notebooks (no solutions/outputs)
   ├── solutions/       # solution notebooks + theory answer key (answers.md)
   ├── rubric.md        # per-problem scoring rubric incl. partial credit
   ├── data/            # generator scripts + small generated artifacts
   └── manifest.yaml    # see schema below
   ```

   **Default instantiation rule (deterministic):** unless the test's plan records a
   deliberate deviation, use exactly —
   - section points = the blueprint's 2026 anchors:
     concept-block 50, math-computation 45, integrative-arc 90, engineering 65,
     open-ended-notebook 50 (sums to 300);
   - arc clusters = position `(NNN - 1) mod 3` in the rotation list
     `[[nlp-embeddings, linear-algebra, numpy], [cnn-vision, pytorch, numpy],
     [applied-ml, probability-statistics, numpy]]` (r1-001 → index 0 ⇒ the first entry);
   - difficulty draw = the analysis-observed `{intro: 0.23, core: 0.45, advanced: 0.32}`;
   - problem count = 9.

   A fresh session generating `r1-NNN` from this doc + `blueprint.yaml` alone therefore
   has zero free choices at instantiation; any deviation is a recorded
   `generation_parameters` entry with a one-line reason.
3. **Draft** — write problems + solutions per spec (drafting rules below).
   Dispatch per `CLAUDE.md ## Agent dispatch`; parallel per-problem subagents are the norm.
4. **Verify** — `bash scripts/ci-local.sh` (verification map below).
5. **Gate** — the 3-way content-review gate (`docs/content-review-gate.md`), including the
   blind-solve and fidelity duties; fidelity compares against
   `book1/reference/analysis.md ## Style notes`.

## Manifest schema (`book1/mocktests/r1-NNN/manifest.yaml`)

```yaml
test: r1-001
blueprint_version: 1            # the version this test was generated against
generated: 2026-08-15           # date
status: final                   # final by default if absent; draft is loud in CI
generation_parameters:          # every choice made at instantiation, for repeatability
  section_points: {concept-block: 50, math-computation: 45, integrative-arc: 90,
                   engineering: 65, open-ended-notebook: 50}   # = the default anchors
  arc_clusters: [nlp-embeddings, linear-algebra, numpy]
  problem_count: 9
  difficulty_draw: {intro: 0.23, core: 0.45, advanced: 0.32}
duration_minutes: 180
total_points: 300
time_budget:                    # advisory minutes per section (sums to duration)
  concept-block: 20
  math-computation: 25
  integrative-arc: 55
  engineering: 45
  open-ended-notebook: 35
problems:
  - id: r1-001-p01-1            # one entry per gradable sub-part (pNN or pNN-M / pNN-Ma)
    section: concept-block
    units: [C1-ml-fundamentals] # syllabus units this sub-part draws on
    concepts: [supervised-vs-unsupervised]   # vocabulary ids only
    cluster: ml-concepts        # dominant cluster after cluster_fold; baseline-only may choose any distribution cluster
    points: 10
    difficulty: intro           # intro | core | advanced
    type: theory                # theory | programming
    answer_form: multiple-choice
    provenance: original        # original | adapted
    # adapted-from: r1-2026-p01-1   # required when provenance: adapted
    spec: >                     # the one-paragraph slot spec this problem was drafted from
      10-pt intro MC testing supervised-vs-unsupervised via task-identification
      distractors; five options; no code.
    answer_key: "C"             # value the solution notebook / answers.md must reproduce
    # answer_tolerance: 1e-6     # optional numeric absolute tolerance (rtol is always 0)
    files: [theory/p01.md]      # optional extra text scanned by overlap-scan; spec-only if absent
    # For data-backed problems:
    # data:
    #   generator_script: data/gen_p05.py
    #   seed: 20260815
```

Field rules:

- `concepts` come from the syllabus vocabulary only; `prereq-check` verifies the student
  is never tested on an untaught concept (tested-only-if-taught).
- `status` is `final` when absent. `status: draft` makes `blueprint-check` print a loud
  draft warning; final manifests determine the exit code, and drafts-only exits 3.
- `cluster` is required per problem for final manifests. It is the dominant
  topic-distribution cluster after applying `cluster_fold`.
- `answer_key` holds the canonical answer (choice letter, numeric value, or a pointer
  `solutions/<file>#<cell-tag>` for open-ended checks); solution execution must reproduce it.
- `data.generator_script` + `data.seed` make datasets reproducible without reading
  solution cells.

## Drafting rules

- **Problem specs first.** Each slot from instantiation gets a one-paragraph spec
  (section, units, concepts, points, difficulty, answer form, provenance mode) before any
  prose is written. Specs are drafted in the test's plan file and then **recorded
  permanently as a `spec:` field on each manifest problem entry**, so the manifest alone
  reconstructs what each slot was asked to be — the plan file is process history, not the
  source of truth.
- **Student/solution separation.** Student-facing notebooks contain no solutions and no
  executed outputs (hygiene-check). Solutions are separate notebooks that run
  top-to-bottom clean with `random-seeding` fixed.
- **Style compliance** per `blueprint.yaml style_rules` — five-option MC, normal-form
  numeric answers, exact identifiers, reasoning-required flags, banned-API zero-point
  clauses, complete runnable starter code.
- **Datasets** come from seeded generator scripts in `data/`; large artifacts are
  regenerated, not committed (only the script + small outputs are committed).
- **Provenance:** original by default; an adapted problem carries `provenance: adapted` +
  `adapted-from: <reference id>` (overlap-scan enforces; untagged similarity blocks merge).
- **Public repo:** never copy verbatim text from reference papers into any committed file.

## Verification map (ci-local step 4 ↔ blueprint)

| Check | Verifies |
|-------|----------|
| prereq-check | manifest schema shape; tested-only-if-taught closure over `units`/`concepts` |
| blueprint-check | `texture`, `sections` ranges, `topic_distribution` (after `cluster_fold`), `difficulty_mix` bands |
| overlap-scan | provenance rules vs the local Book 1 reference corpus; fetch with `bash scripts/fetch-reference.sh --book book1` |
| coverage-check | (units, not mock tests) every taught concept practiced |
| hygiene-check | student notebooks free of solutions/outputs |
| solution execution | every solutions/ notebook runs clean |
| answer-key reproduction | answerkey-check (plan 011) |
| PDF build | Quarto renders test.md + problems to `build/` |

## Book 2 (Round 2) mock tests

Authoritative inputs: `book2/mocktests/blueprint.yaml` (live since Plan 024) and `book2/syllabus.md`.
Shape evidence is structure only: `book2/reference/analysis.md ## Round 2 shape notes`.

### Pipeline

1. **Blueprint** — read `book2/mocktests/blueprint.yaml` at its current `blueprint_version`.
2. **Instantiate** — run `uv run usaaio-tools --book book2 new-mocktest r2-NNN --date YYYY-MM-DD`.
   The layout is flat, exactly as for Book 1 (`test.md`, `theory/`, `problems/`, `solutions/` with `answers.md`, `data/`, `rubric.md`, `manifest.yaml`).
   Days live in the manifest's per-entry `day` field and in `test.md`'s Day 1 and Day 2 sections, so hygiene, answer-key, overlap, and PDF discovery are unchanged.
3. **Draft** — the d1 arc, the d1 open-ended task, the d2 arc, and two d2 open-ended tasks.
   Every task-specific formula is defined in its statement.
4. **Verify** — `bash scripts/ci-local.sh`; r2 solutions run under the 20-second solution timeout.
5. **Gate** — the content-review gate; fidelity is judged on shape only.

### Default instantiation rule (zero-choice)

Unless the test's plan records a deliberate deviation, `new-mocktest` copies these blueprint keys:

- section points = `default_anchors`: d1-arc 90, d1-open 70, d2-arc 50, d2-open [40, 50];
- per-day time budget = `default_time_budget` (day 1: d1-arc 120, d1-open 120; day 2: d2-arc 80, d2-open 160), each day summing to `day_duration_minutes` (240);
- arc clusters = `arc_rotation[(NNN - 1) mod 3]`, recorded as `{d1: [...], d2: [...]}` with its `rotation_index`;
- difficulty draw = `default_difficulty_draw` (`{intro: 0.20, core: 0.45, advanced: 0.35}`);
- problem count = 5 (one per anchor).

### Manifest extension

```yaml
test: r2-001
blueprint_version: 1
status: final
generation_parameters:
  rotation_index: 0
  section_points: {d1-arc: 90, d1-open: 70, d2-arc: 50, d2-open: [40, 50]}
  arc_clusters: {d1: [attention-transformers, language-transformers], d2: [probabilistic-latent-models]}
  problem_count: 5
  difficulty_draw: {intro: 0.2, core: 0.45, advanced: 0.35}
day_duration_minutes: 240        # replaces Book 1's duration_minutes
total_points: 300
time_budget:                     # {"day": {section: minutes}}; each day sums to day_duration_minutes
  '1': {d1-arc: 120, d1-open: 120}  # day keys are quoted: manifests stay string-keyed
  '2': {d2-arc: 80, d2-open: 160}
problems:
  - id: r2-001-p01-1
    day: 1                       # must equal the section's day
    section: d1-arc
    # ...the Book 1 entry fields...
```

`blueprint-check` applies, for Book 2 only:
- each entry's `day` equals its section's day;
- per-section points, sub-part (entry), and problem-count ranges;
- texture: problem count, sub-part count, and `open_ended_points_share`;
- each day's time budget names exactly that day's sections and sums to `day_duration_minutes`;
- arc entries draw only on the rotation's clusters for their day;
- every open-ended entry carries one of `open_ended_families` (a taught-closure constraint);
- the shared topic, difficulty, provenance, and per-entry rules.
The Book 1 keys (`duration_minutes`, `five_point_atom_share`, `programming_points_share`, `draws_on_clusters`, the `integrative-arc` override) are read only for Book 1.

### Open-ended answer keys

An open-ended entry's `answer_key` is the marker
`metric=<name>; direction=<lower|higher>; B=<v>; R=<v>; tiers=<full>,<partial60>,<partial25>`,
with every number at 4 significant digits.
B is the committed baseline score and R the published reference solution's `final_test_score`, both at the test seed; `g = |B - R|`.
Lower-is-better cutoffs are `R + 0.25g`, `B`, `B + 0.25g`; higher-is-better cutoffs mirror them (`R - 0.25g`, `B`, `B - 0.25g`).
`solutions/answers.md` repeats the identical marker, so `answerkey-check` compares it like any theory key.

### Final-assessment marker

`book2/curriculum/course-schedule.yaml` carries `final_assessment: {kind: r2-mock, status: live, test: r2-NNN, after_book_week: <last week>}`.
`schedule-check` accepts it only when `mocktests/r2-NNN/manifest.yaml` exists, and accepts the old planned `future-r2-mock` marker only while no `r2-*` manifest exists.
