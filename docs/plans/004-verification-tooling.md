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
@dataclass MockManifest: test id, blueprint_version, generated, status ('draft'|'final', absent=final), generation_parameters, time_budget, problems: list[ManifestProblem(id, section, units, concepts, points, difficulty, type, answer_form, provenance, adapted_from, spec, answer_key, data)]
load_syllabus(root) -> Syllabus       # sentinel-fence parse; ValueError if sentinel count != 1
load_blueprint(root) -> Blueprint
load_unit_manifests(root) -> list[UnitManifest]     # units/*/manifest.yaml, [] if none
load_mock_manifests(root) -> list[MockManifest]     # mocktests/r1-*/manifest.yaml, [] if none
@dataclass Report: name; ok: bool; errors: list[str]; warnings: list[str]; skipped: str|None  # remedy text
```

Unit manifest schema (defined HERE, used by plan 005+ units):
```yaml
unit: F1-scientific-python
concepts_taught: [numpy-arrays, ...]      # must equal syllabus teaches for this unit
concepts_used: [variables-and-types, ...] # baseline or taught-by-ancestor ids
prereq_units: [..]                        # must equal syllabus prereqs for this unit
# snake_case keys throughout (matches the mock manifest + dataclasses)
practice:
  - id: F1-p01
    concepts: [broadcasting, vectorization]   # exercised concepts
    path: practice/p01.ipynb                  # student-facing (hygiene-checked)
    solution_path: practice/p01_solution.ipynb  # runs clean top-to-bottom; NOT hygiene-checked
```

Naming convention (hygiene relies on it): any notebook whose filename contains
`solution` is a solutions notebook; every other notebook under `practice/` or
`problems/` is student-facing.

**Tests (exact names):** `test_load_syllabus_real_repo` (structural invariants, not hardcoded counts: >=16 units, >=100 concepts, taught-exactly-once bijection holds), `test_sentinel_must_be_unique`, `test_load_blueprint_real_repo` (targets sum to total_points), `test_missing_dirs_yield_empty_lists`, `test_unit_manifest_roundtrip` (tmp fixture).

---

### Task 2: prereq-check + coverage-check (`tools/checks/prereq.py`, `tools/checks/coverage.py`)

**prereq-check rules:**
1. Syllabus self-consistency: DAG acyclic; teaches/prereq refs resolve; every concept taught exactly once; concept clusters ∈ clusters.
2. Per unit manifest: `concepts_taught` == syllabus unit's teaches (exact set); `prereq_units` == syllabus prereqs; every id in `concepts_used` ∈ baseline ∪ teaches(transitive ancestors).
3. Per mock manifest: every problem `concepts` id ∈ **baseline ∪** ⋃ teaches(units listed in the problem's `units`, including transitive prereqs) — tested-only-if-taught with pure-baseline questions allowed (they anchor the intro difficulty band); every listed unit has a shipped manifest in `units/`.

**coverage-check rules:** per unit manifest, every id in `concepts_taught` appears in ≥1 practice problem's `concepts`; every practice `path` AND `solution_path` exists; practice concept ids ∈ vocabulary.

**Tests:** `test_prereq_pass_on_real_syllabus`, `test_prereq_detects_cycle`, `test_prereq_detects_untaught_use`, `test_prereq_detects_manifest_syllabus_drift`, `test_mock_tested_only_if_taught`, `test_coverage_pass_and_gap`, `test_coverage_missing_practice_file`.

---

### Task 3: hygiene-check (`tools/checks/hygiene.py`)

Rules (student-facing notebooks: `mocktests/*/problems/*.ipynb` and `units/*/practice/*.ipynb`, in both cases EXCLUDING filenames containing `solution` — the Task 1 naming convention):
1. No executed outputs (`cell.outputs == []`, `execution_count is None`).
2. No solution leakage markers: cells containing `# SOLUTION`, `answer_key`, or tag `solution` are forbidden in student notebooks.
3. Solutions notebooks (`solutions/*.ipynb`) are NOT checked here (they may contain outputs).

**Tests:** `test_hygiene_clean_notebook_passes`, `test_hygiene_flags_outputs`, `test_hygiene_flags_solution_marker`, `test_hygiene_vacuous_without_notebooks`.

---

### Task 4: blueprint-check (`tools/checks/blueprint.py`)

Per mock manifest, against the blueprint: points sum == total_points; per-section sums within `sections[].points` ranges (+ arc subparts range); subpart count within texture range; five-point-atom share ≥ min; programming share (points of `type: programming`) within range; problem_count within range; topic accounting — **explicit dominant-cluster attribution**: each manifest problem carries a `cluster:` field (dominant cluster, post-fold — Task 7 adds it to the schema in docs/mocktest-generation.md); all the problem's points go to it, matching analysis.md's dominant-cluster methodology that produced the targets. blueprint-check validates `cluster ∈ fold(clusters(problem.concepts))` — for baseline-only problems (no clustered concepts) any distribution cluster is accepted; per-cluster point totals within `{min,max}`; difficulty bands (share of points per difficulty within band bounds); provenance — original share ≥ min, `adapted` requires `adapted-from`; every problem carries non-empty `spec` + `answer_key`; `data` entries name existing `generator_script` files; each problem's dominant `cluster` (post-fold) ∈ its section's `draws_on_clusters` (post-fold); `time_budget` values sum to `duration_minutes`.

**Tests:** `test_blueprint_pass_on_fixture_test`, `test_blueprint_flags_section_out_of_range`, `test_blueprint_flags_topic_distribution_breach`, `test_blueprint_flags_missing_adapted_tag`, `test_blueprint_flags_atom_share_breach`, `test_blueprint_flags_programming_share_breach`, `test_blueprint_flags_difficulty_band_breach`, `test_blueprint_flags_provenance_share_breach`, `test_blueprint_flags_invalid_dominant_cluster`, `test_blueprint_flags_section_cluster_violation`, `test_blueprint_flags_remaining_invariants_parametric` (subpart count, problem_count, missing spec/answer_key, missing generator_script, time-budget sum — one parametrized test, one broken fixture per invariant), `test_blueprint_vacuous_without_mocktests`.

---

### Task 5: overlap-scan (`tools/checks/overlap.py`)

1. Corpus: for each `reference/*/` dir with PDFs, extract text via `pdftotext` (subprocess) at scan time; also read `index.yaml` `text:` fields when present. Missing corpus/pdftotext → `Report.skipped` = remedy naming `bash scripts/fetch-reference.sh` (exit 3).
2. Mock problem text: concatenate manifest `spec` + the problem's `files:` list (optional manifest field, paths relative to the test dir, e.g. [problems/p05.ipynb, theory/p01.md] — Task 7 adds it to the schema); missing `files` ⇒ spec-only comparison with a warning.
3. Similarity: (a) 8-word shingle overlap count; (b) TF-IDF cosine (stdlib impl) between problem text and each reference sub-part text. Flag when shingles ≥ 2 OR cosine ≥ 0.35 (tunable constants at module top).
4. A flagged problem without `provenance: adapted` + matching `adapted-from` → error; with tag → warning (informational).

**Tests:** `test_overlap_skips_loudly_without_corpus`, `test_overlap_flags_near_copy_fixture`, `test_overlap_accepts_tagged_adaptation`, `test_overlap_passes_original_fixture` (fixtures build a fake reference dir with a small index.yaml; no real corpus).

---

### Task 6: new-mocktest scaffolder (`tools/checks/new_mocktest.py` or `tools/scaffold.py`)

`usaaio-tools new-mocktest r1-NNN`: refuses to overwrite; creates the directory skeleton per `docs/mocktest-generation.md` (test.md front-matter stub, empty `theory/ problems/ solutions/ data/`, `rubric.md` stub) and a `manifest.yaml` pre-filled by the DETERMINISTIC default rule (anchors 50/45/90/65/50, arc clusters by `(NNN-1) mod 3` rotation (r1-001 → index 0, the first entry — matching the canonical example; Task 7 fixes the ambiguous "index 1 ⇒ first entry" prose in mocktest-generation.md), difficulty draw {0.23,0.45,0.32}, problem_count 9, blueprint_version from blueprint, generated date from `--date YYYY-MM-DD` required arg — no clock access convention) with empty `problems: []` and `status: draft`. Semantics: absent `status` == `final` (a manifest can never dodge checking by omission); `status: draft` makes blueprint-check emit a LOUD warning line naming the manifest (never silent) while schema validation, prereq, coverage, and hygiene still run in full; `status: final` enables everything. Exit semantics with mixed manifests: blueprint-check's exit code is determined solely by the FINAL manifests' results (fail=1 beats all; all-pass with ≥1 draft = 0 with the warning line; no final manifests and ≥1 draft = 3).

**Tests:** `test_new_mocktest_scaffolds_defaults` (r1-002 → rotation index 1, second entry), `test_new_mocktest_rotation_wraps` (r1-004 → index 0, first entry), `test_new_mocktest_refuses_overwrite`, `test_draft_manifest_loud_skipped_by_blueprint_check`, `test_absent_status_treated_as_final`, `test_scaffold_time_budget_sums_to_duration`.

---

### Task 7: CLI wiring + ci-local integration + integration tests

1. `tools/cli.py`: SUBCOMMANDS map to real functions; each prints its Report (errors→stderr) and exits 0/1/3; `--root` arg (default `.`) for tests.
2. `scripts/ci-local.sh`: **step 3's execution glob narrows to solutions only** — `*/solutions/*.ipynb` plus `*/practice/*solution*.ipynb` (student-facing notebooks contain TODO cells by design and must not be executed; hygiene checks them instead), and adds the `PENDING (plan 006): answer-key reproduction` line; step 4 becomes real invocations (manifest validation happens inside prereq/blueprint checks):
   ```bash
   for c in prereq-check coverage-check hygiene-check blueprint-check overlap-scan; do
     uv run usaaio-tools "$c" || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }
   done
   ```
   (exit 3 = loud skip tolerated; step prints each report line.)
3. **Integration tests phase (named):** `tests/test_integration.py` — `test_ci_checks_green_on_current_repo` (runs all five checks against the real repo root and asserts each check's EXPLICIT status — pass, vacuous, or skip-3 with remedy — never 1, so silent errors can't hide), `test_cli_exit_codes` (0/1/3 paths via fixtures), `test_full_pipeline_on_synthetic_test` (fixture mini-syllabus + scaffolded mocktest + one drafted problem → prereq+coverage+hygiene+blueprint all evaluated), `test_ci_flags_draft_manifest_loudly` (a scaffolded-but-draft mocktest in a fixture repo produces the named loud-skip line from blueprint-check — the draft state is impossible to miss in CI output).
4. Update `docs/mocktest-generation.md`: verification-map table (drop "plan 004" SKIPs), manifest schema gains the per-problem `cluster:` field (dominant, post-fold) and documents the `status:` semantics; `CLAUDE.md` untouched (governance — no changes needed; SKIP language already says "until plan 004 ships").

**Acceptance criteria:** all named tests above exist and pass; `bash scripts/ci-local.sh` ALL GREEN on the repo (overlap-scan exit 3 loud-skip acceptable only when corpus absent — on THIS machine the corpus exists, so it must actually run and pass); ruff clean.

---

## Out of scope

- Quarto/PDF build (plan 006). Embedding-model similarity beyond TF-IDF (revisit only if TF-IDF proves insufficient during plan 006's gate — recorded here as the concrete trigger, not an unfiled deferral).
- **Answer-key reproduction** (design §3.1 second half: solution outputs must equal manifest `answer_key`) is OWNED BY PLAN 006, which ships the first solution notebooks (there is nothing to compare until then — blueprint-check already fails any final manifest lacking `answer_key`). Until 006 lands, ci-local step 3 prints an explicit `PENDING (plan 006): answer-key reproduction` line so the gap is visible in every CI run, and the verification map marks it pending. A wrong solution therefore cannot merge silently once notebooks exist: 006's named acceptance tests include the comparator.
- Unit content (plan 005+). No governance-doc edits.
- **Verification-phase exemption:** not exempt — Task 7 IS the named integration-tests phase (this plan ships tooling; its tests are the verification).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` Topic accounting originally split points equally across concept clusters,
   which would drift from the blueprint targets' own derivation (analysis assigned each
   sub-part ONE dominant cluster) → dominant-concept attribution: `concepts[0]` is the
   declared dominant concept and takes all the problem's points.
2. `[FIXED]` Unit-practice hygiene conventions were fuzzy → explicit naming rule
   (filename containing `solution` = solutions notebook), `solution_path` added to the
   unit-manifest practice schema, hygiene globs updated to match.
3. `[NOTED]` ci-local rc-capture snippet verified correct under `set -euo pipefail`
   (the `||` compound guards the non-zero exit; only rc==3 is tolerated).

### Review 2 — [fable] Independent Fable 5, fresh context (2026-08-04)

- **Verdict**: REJECT → all findings fixed, re-review requested
1. `[FIXED]` Split-attribution blocker → explicit per-problem `cluster:` field (dominant,
   post-fold), validated ∈ fold(clusters(concepts)); schema updated via Task 7.
2. `[FIXED]` Mock closure excludes baseline → baseline ∪ closure, with baseline-only
   problems allowed (intro band anchor); attribution for them defined via the explicit
   cluster field.
3. `[FIXED]` `*student*` glob dead code → filename-contains-`solution` convention pinned in
   the Task 1 schema, hygiene globs updated (raced my self-review fix; superseded).
4. `[FIXED]` Answer-key reproduction unowned → explicitly owned by plan 006 in Out of
   scope, with a PENDING line in ci-local until then.
5. `[FIXED]` status:draft semantics → absent=final; draft LOUD-skip (blueprint only);
   schema/prereq/coverage/hygiene still run.
6. `[FIXED]` Thin blueprint tests → four share/band/provenance breach tests +
   parametric remaining-invariants test added.
7. `[FIXED]` Integration test asserts per-check explicit status; rotation wrap test added.
8. `[FIXED]` Hardcoded counts → structural invariants.

### Review 3 — [codex] Codex GPT-5.5 (2026-08-04)

- **Verdict**: REJECT → all findings fixed, re-review requested
1. `[FIXED]` Answer-key gap — same as [fable] #4: plan-006 ownership + per-run PENDING
   line + blueprint-check already fails final manifests lacking answer_key. Nothing to
   compare exists before 006's notebooks.
2. `[FIXED]` Draft bypass — same as [fable] #5 + `test_ci_flags_draft_manifest_loudly`
   named; a lingering draft shouts in every CI run and cannot pass the content gate.
3. `[FIXED]` Draft-bypass test gap — the named test above.
4. `[NOTED]` Dominant-cluster attribution endorsed (now via explicit field).

### Review 4 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: APPROVE WITH NITS (1 blocker within) → all fixed
1. `[FIXED]` Rotation off-by-one vs canonical example → `(NNN-1) mod 3`; r1-001 → first
   entry; scaffold tests updated; Task 7 fixes the doc prose.
2. `[FIXED]` MockManifest gains `generated`, `status`, `time_budget` fields.
3. `[FIXED]` Parametric invariant tests added.
4. `[FIXED]` Section draws_on_clusters now enforced (dominant cluster ∈ section set).
5. `[FIXED]` Problem→file linkage: optional `files:` manifest field; spec-only + warning
   fallback.
6. `[FIXED]` `status` documented in the schema via Task 7.
7. `[FIXED]` Unit manifest keys unified to snake_case.
8. `[NOTED]` ci-local snippet verified; per-check echo adopted.
9. `[NOTED]` Overlap thresholds accepted; Report logs the hitting metric.
10. `[FIXED]` time_budget-sums-to-duration check added (cheap).

### Round 2 re-verdicts

- **[fable]** APPROVE WITH NITS → 3 nits fixed (solutions-only execution glob,
  solution_path coverage, mixed draft/final exit semantics) → **APPROVE** (verified).
- **[codex]** APPROVE.
- **[glm]** APPROVE WITH NITS round 1; all nits fixed.

**GATE RESULT: PASS — 4/4** ([claude-self], [fable], [codex], [glm]); no open blockers.

## Content Review

### Review 1 — [claude-self] inline (2026-08-04)

- **Verdict**: Approved with suggestions

1. `[FIXED]` Implementation included a ~100-line hand-rolled YAML-subset fallback parser
   in `tools/model.py` for the pyyaml-missing case — dead code (pyyaml is an unconditional
   dependency) with silent-divergence risk. Removed along with its `_strip_comment`
   helper; `_parse_yaml` now calls `yaml.safe_load` directly.
2. `[FIXED]` Two test files read `mocktests/blueprint.yaml`/`syllabus.md` via CWD-relative
   paths — anchored to `ROOT` (the fragility class most likely to explain the one
   unreproduced failure below).
3. `[FIXED]` Flake watch: `test_blueprint_flags_remaining_invariants_parametric
   [problem count…]` failed exactly once, never reproduced. [codex]'s analysis attributes
   it to the pre-fix CWD-relative fixture reads (stale path state), which the
   ROOT-anchoring in Review 1 item 2 already eliminated; the data path itself is
   deterministic. Closed on that mechanism.
4. Verified: 7 per-task commits; 52 tests pass ×3; ruff clean; ci-local ALL GREEN with
   all five checks executing for real (overlap-scan PASS against the local corpus,
   prereq/coverage vacuous-pass, hygiene vacuous, blueprint vacuous, PENDING plan-006
   line present).

### Review 2 — [codex] Codex GPT-5.5 (2026-08-04)

- **Verdict**: Changes requested → all fixed, re-verdict requested

1. `[FIXED]` BLOCKER: `problem_count` stripped the last hyphen segment, collapsing
   part-less ids (`r1-001-p01` → `r1-001`) — a valid 3-problem manifest could miscount
   as 1. → pNN-token regex derivation + `test_problem_count_handles_partless_ids`.
2. `[FIXED]` `status` accepted arbitrary text as final (`drfat` passed) →
   `_validated_status` raises on anything ≠ draft|final + `test_invalid_status_rejected`.
3. `[FIXED]` Flake mechanism identified (pre-fix CWD-relative reads) — closed above.
4. `[FIXED]` Dead `_split_top_level`/`_parse_scalar` remnants removed (+unused `ast`
   import). Suite now 54 tests, green; ci-local ALL GREEN.

### Review 3 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: Approved with suggestions (reviewed pre-codex-fix HEAD; overlapping items
  already fixed there: status strictness, dead helpers, p01-token counting)

1. `[FIXED]` `_corpus` demanded index.yaml; PDFs alone are a valid corpus per spec →
   signal now index.yaml OR PDFs.
2. `[FIXED]` Unknown `section`/`difficulty` escaped validation silently → explicit
   unknown-section/unknown-difficulty errors before accumulation.
3. `[FIXED]` (already) status strictness via `_validated_status`.
4. `[FIXED]` hygiene used `json.loads` with nbformat unused → `nbformat.reads`
   (+`ValueError` catch covering `NotJSONError`).
5. `[FIXED]` (already) dead helpers removed.
6. `[FIXED]` (already) dash-less id counting via pNN-token regex.
7. `[FIXED]` Stray dead blueprint load in `write_repo` removed.
8. `[NOTED]` O(n²) TF-IDF acceptable at corpus scale; `adapted-from`/`adapted_from`
   loader leniency kept as a deliberate schema bridge.

### Review 4 — [opus] Independent Opus, fresh context (2026-08-04)

- **Verdict**: Changes requested → all fixed, re-verdict requested
  (behavioral probes all passed: exit codes, draft semantics, rotation, hygiene,
  overlap remedy, baseline escape)

1. `[FIXED]` BLOCKER: five-point-atom share computed as POINTS share (0.40 for the real
   2026 texture) where blueprint/analysis define a COUNT share (24/37=0.65) — the gate
   rejected the artifact it was derived from. → count share;
   `test_atom_share_is_count_share_not_points_share`.
2. `[FIXED]` Arc rotation unsatisfiable for 2 of 3 rotations (static blueprint list) →
   integrative-arc validates against the manifest's declared `arc_clusters` (fallback:
   blueprint list); `test_arc_clusters_validated_from_manifest_rotation` covers both
   reject-static and accept-declared paths.
3. `[FIXED]` Raw tracebacks from CLI on loader failures → try/except → `ERROR <cmd>:` +
   exit 1; `data:`-as-list guarded with a proper error.
4. `[FIXED]` Flake record corrected: [codex]'s CWD mechanism disproved (uniform
   FileNotFoundError, not a single-case miss; 30+ runs incl. hash-seed variation and
   18-way concurrency all green) — recorded as UNREPRODUCED, not explained.
5. `[FIXED]` NITs: overlap dfs/shingle precompute hoisted out of the per-problem loop
   (~17s → sub-second); duration_minutes-vs-blueprint check added;
   `adapted_requires_tag` read from provenance_rules. Suite: 56 tests green.
