# Mock-Test Generation Pipeline

The repeatable procedure for producing every `mocktests/r1-NNN/`.
Authoritative inputs: `mocktests/blueprint.yaml` (test spec) and `syllabus.md`
(concept vocabulary + unit DAG).
Design rationale: `docs/designs/000-project-design.md §2b`.

## Pipeline

1. **Blueprint** — read `mocktests/blueprint.yaml` at its current `blueprint_version`.
   Changing the blueprint is a reviewed change like any other (plan + gates).
2. **Instantiate** — create the test skeleton and problem-spec sheet.
   Run `uv run usaaio-tools new-mocktest r1-NNN --date YYYY-MM-DD`.

   ```
   mocktests/r1-NNN/
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
5. **Gate** — the 4-way content-review gate (`docs/content-review-gate.md`), including the
   blind-solve and fidelity duties; fidelity compares against
   `reference/analysis.md ## Style notes`.

## Manifest schema (`mocktests/r1-NNN/manifest.yaml`)

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
| overlap-scan | provenance rules vs the local reference corpus; loud skip without corpus names `bash scripts/fetch-reference.sh` |
| coverage-check | (units, not mock tests) every taught concept practiced |
| hygiene-check | student notebooks free of solutions/outputs |
| solution execution | every solutions/ notebook runs clean |
| answer-key reproduction | PENDING (plan 006) |
| PDF build | Quarto renders test.md + problems to `build/` |
