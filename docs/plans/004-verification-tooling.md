# Plan 004 — Verification Tooling Implementation Plan

> **For agentic workers:** Execute task-by-task with per-task commits. Implementation
> dispatches to `codex:codex-rescue` per `CLAUDE.md ## Agent dispatch` (tooling code).

**Goal:** Replace the six `usaaio-tools` CLI stubs with working checks — `prereq-check`, `coverage-check`, `hygiene-check`, `blueprint-check`, `overlap-scan`, `new-mocktest` — plus manifest validation, and wire them into `scripts/ci-local.sh` so the self-containedness and blueprint contracts become machine-enforced.

**Architecture:** One loader module (`tools/model.py`) parses the three data sources (syllabus canonical fence, blueprint, unit/mocktest manifests) into typed structures; each check is a pure function in its own module (`tools/checks/*.py`) returning a `Report` (ok, errors, warnings, skipped+remedy); `tools/cli.py` maps subcommands to checks and exits 0/1/3 (3 = loud skip). Checks never mutate anything.

**Tech Stack:** Python 3.12; deps added: `pyyaml` (manifests/syllabus), `nbformat` (hygiene), sklearn NOT added — overlap-scan's similarity uses lexical n-gram shingles + TF-IDF cosine implemented with stdlib `collections`/`math` (avoids a heavyweight dep for ~100 documents). `pdftotext` (poppler, already on this machine) via subprocess for corpus text; its absence triggers loud-skip.

## Global Constraints

- Contracts fixed by plan 003 (its post-exec follow-ups): transitive prereq closure; overlap-scan SKIPS LOUDLY naming `bash scripts/fetch-reference.sh` when `reference/*/index.yaml` or PDFs are absent; syllabus parser keys on the `<!-- syllabus-canonical -->` sentinel (exactly one literal occurrence — assert it); blueprint-check reads `{target,min,max}` points and applies `cluster_fold` before accounting; `length: double` is a valid unit field.
- Exit codes: 0 = pass, 1 = fail (merge blocker), 3 = skipped-with-remedy (ci-local treats 3 as pass but prints the remedy line).
- Checks must run green on the CURRENT repo state (no units, no mocktests yet): absent `units/`/`mocktests/r1-*` dirs are vacuous passes, not errors.
- Lint clean (`ruff`), tests via pytest with tmp-path fixtures; no test touches the real `reference/` corpus (fixtures fabricate mini corpora).

---

### Task 1: Data model + loaders (`tools/model.py`)

**Files:** Create `tools/model.py`; Test `tests/test_model.py`

**Interfaces (produces):**
```python
@dataclass Syllabus: baseline: set[str]; clusters: set[str]; concepts: dict[str, str]  # id->cluster
                     units: dict[str, Unit]   # Unit: id, track, title, prereqs, teaches, length
@dataclass Blueprint: raw dict access + typed: total_points, texture, sections, topic_distribution,
                      cluster_fold, difficulty_mix, provenance_rules
@dataclass UnitManifest: unit_id, concepts_taught, concepts_used, prereq_units, practice: list[PracticeProblem(id, concepts, path)]
@dataclass MockManifest: test id, blueprint_version, generation_parameters, problems: list[ManifestProblem(id, section, units, concepts, points, difficulty, type, answer_form, provenance, adapted_from, spec, answer_key, data)]
load_syllabus(root) -> Syllabus       # sentinel-fence parse; ValueError if sentinel count != 1
load_blueprint(root) -> Blueprint
load_unit_manifests(root) -> list[UnitManifest]     # units/*/manifest.yaml, [] if none
load_mock_manifests(root) -> list[MockManifest]     # mocktests/r1-*/manifest.yaml, [] if none
@dataclass Report: name; ok: bool; errors: list[str]; warnings: list[str]; skipped: str|None  # remedy text
```

Unit manifest schema (defined HERE, used by plan 005+ units):
```yaml
unit: F1-scientific-python
concepts-taught: [numpy-arrays, ...]      # must equal syllabus teaches for this unit
concepts-used: [variables-and-types, ...] # baseline or taught-by-ancestor ids
prereq-units: [..]                        # must equal syllabus prereqs for this unit
practice:
  - id: F1-p01
    concepts: [broadcasting, vectorization]   # exercised concepts
    path: practice/p01.ipynb
```

**Tests (exact names):** `test_load_syllabus_real_repo` (16 units, 105 concepts), `test_sentinel_must_be_unique`, `test_load_blueprint_real_repo` (targets sum 300), `test_missing_dirs_yield_empty_lists`, `test_unit_manifest_roundtrip` (tmp fixture).

---

### Task 2: prereq-check + coverage-check (`tools/checks/prereq.py`, `tools/checks/coverage.py`)

**prereq-check rules:**
1. Syllabus self-consistency: DAG acyclic; teaches/prereq refs resolve; every concept taught exactly once; concept clusters ∈ clusters.
2. Per unit manifest: `concepts-taught` == syllabus unit's teaches (exact set); `prereq-units` == syllabus prereqs; every id in `concepts-used` ∈ baseline ∪ teaches(transitive ancestors).
3. Per mock manifest: every problem `concepts` id ∈ ⋃ teaches(units listed in the problem's `units`, including transitive prereqs) — tested-only-if-taught; every listed unit has a shipped manifest in `units/`.

**coverage-check rules:** per unit manifest, every id in `concepts-taught` appears in ≥1 practice problem's `concepts`; every practice `path` exists; practice concept ids ∈ vocabulary.

**Tests:** `test_prereq_pass_on_real_syllabus`, `test_prereq_detects_cycle`, `test_prereq_detects_untaught_use`, `test_prereq_detects_manifest_syllabus_drift`, `test_mock_tested_only_if_taught`, `test_coverage_pass_and_gap`, `test_coverage_missing_practice_file`.

---

### Task 3: hygiene-check (`tools/checks/hygiene.py`)

Rules (student-facing notebooks: `mocktests/*/problems/*.ipynb` and any `units/*/practice/*student*.ipynb`):
1. No executed outputs (`cell.outputs == []`, `execution_count is None`).
2. No solution leakage markers: cells containing `# SOLUTION`, `answer_key`, or tag `solution` are forbidden in student notebooks.
3. Solutions notebooks (`solutions/*.ipynb`) are NOT checked here (they may contain outputs).

**Tests:** `test_hygiene_clean_notebook_passes`, `test_hygiene_flags_outputs`, `test_hygiene_flags_solution_marker`, `test_hygiene_vacuous_without_notebooks`.

---

### Task 4: blueprint-check (`tools/checks/blueprint.py`)

Per mock manifest, against the blueprint: points sum == total_points; per-section sums within `sections[].points` ranges (+ arc subparts range); subpart count within texture range; five-point-atom share ≥ min; programming share (points of `type: programming`) within range; problem_count within range; topic accounting — map each problem's concepts→clusters via syllabus, fold via `cluster_fold`, points per cluster within `{min,max}` (a problem's points split equally across its concepts' distinct folded clusters); difficulty bands (share of points per difficulty within band bounds); provenance — original share ≥ min, `adapted` requires `adapted-from`; every problem carries non-empty `spec` + `answer_key`; `data` entries name existing `generator_script` files.

**Tests:** `test_blueprint_pass_on_fixture_test`, `test_blueprint_flags_section_out_of_range`, `test_blueprint_flags_topic_distribution_breach`, `test_blueprint_flags_missing_adapted_tag`, `test_blueprint_vacuous_without_mocktests`.

---

### Task 5: overlap-scan (`tools/checks/overlap.py`)

1. Corpus: for each `reference/*/` dir with PDFs, extract text via `pdftotext` (subprocess) at scan time; also read `index.yaml` `text:` fields when present. Missing corpus/pdftotext → `Report.skipped` = remedy naming `bash scripts/fetch-reference.sh` (exit 3).
2. Mock problem text: concatenate manifest `spec` + student notebook/theory sources per problem.
3. Similarity: (a) 8-word shingle overlap count; (b) TF-IDF cosine (stdlib impl) between problem text and each reference sub-part text. Flag when shingles ≥ 2 OR cosine ≥ 0.35 (tunable constants at module top).
4. A flagged problem without `provenance: adapted` + matching `adapted-from` → error; with tag → warning (informational).

**Tests:** `test_overlap_skips_loudly_without_corpus`, `test_overlap_flags_near_copy_fixture`, `test_overlap_accepts_tagged_adaptation`, `test_overlap_passes_original_fixture` (fixtures build a fake reference dir with a small index.yaml; no real corpus).

---

### Task 6: new-mocktest scaffolder (`tools/checks/new_mocktest.py` or `tools/scaffold.py`)

`usaaio-tools new-mocktest r1-NNN`: refuses to overwrite; creates the directory skeleton per `docs/mocktest-generation.md` (test.md front-matter stub, empty `theory/ problems/ solutions/ data/`, `rubric.md` stub) and a `manifest.yaml` pre-filled by the DETERMINISTIC default rule (anchors 50/45/90/65/50, arc clusters by `NNN mod 3` rotation, difficulty draw {0.23,0.45,0.32}, problem_count 9, blueprint_version from blueprint, generated date from `--date YYYY-MM-DD` required arg — no clock access convention) with empty `problems: []` and a `# TODO drafts` note that ci-local's manifest validation reports as incomplete-but-not-failing until problems land (`status: draft` field; blueprint-check skips manifests marked `status: draft`, validates when `status: final`).

**Tests:** `test_new_mocktest_scaffolds_defaults` (r1-002 → rotation index 2), `test_new_mocktest_refuses_overwrite`, `test_draft_manifest_skipped_by_blueprint_check`.

---

### Task 7: CLI wiring + ci-local integration + integration tests

1. `tools/cli.py`: SUBCOMMANDS map to real functions; each prints its Report (errors→stderr) and exits 0/1/3; `--root` arg (default `.`) for tests.
2. `scripts/ci-local.sh` step 4 becomes real invocations (manifest validation happens inside prereq/blueprint checks):
   ```bash
   for c in prereq-check coverage-check hygiene-check blueprint-check overlap-scan; do
     uv run usaaio-tools "$c" || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }
   done
   ```
   (exit 3 = loud skip tolerated; step prints each report line.)
3. **Integration tests phase (named):** `tests/test_integration.py` — `test_ci_checks_green_on_current_repo` (runs all five checks against the real repo root, expects pass/vacuous/skip-3, never 1), `test_cli_exit_codes` (0/1/3 paths via fixtures), `test_full_pipeline_on_synthetic_test` (fixture mini-syllabus + scaffolded mocktest + one drafted problem → prereq+coverage+hygiene+blueprint all evaluated).
4. Update `docs/mocktest-generation.md` verification-map table (drop "plan 004" SKIPs), `CLAUDE.md` untouched (governance — no changes needed; SKIP language already says "until plan 004 ships").

**Acceptance criteria:** all named tests above exist and pass; `bash scripts/ci-local.sh` ALL GREEN on the repo (overlap-scan exit 3 loud-skip acceptable only when corpus absent — on THIS machine the corpus exists, so it must actually run and pass); ruff clean.

---

## Out of scope

- Quarto/PDF build (plan 006). Embedding-model similarity beyond TF-IDF (revisit only if TF-IDF proves insufficient during plan 006's gate — recorded here as the concrete trigger, not an unfiled deferral).
- Unit content (plan 005+). No governance-doc edits.
- **Verification-phase exemption:** not exempt — Task 7 IS the named integration-tests phase (this plan ships tooling; its tests are the verification).

## Plan Review

(4-way gate verdicts land here.)

## Content Review

(Code review findings land here.)
