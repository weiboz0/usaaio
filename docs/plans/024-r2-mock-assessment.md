# Plan 024 — Round 2 Blueprint and Mock Test r2-001

## Goal

Make Book 2's final assessment live:
- replace the planned version-1 Book 2 blueprint skeleton with a real Round 2 blueprint;
- generalize the mock-test tooling to it without changing Book 1 behavior;
- ship `book2/mocktests/r2-001`, an original two-day, 300-point Round 2 mock test that covers B2-019 through B2-024.

Plan 019 reserved Plan 024 for this ("must be replaced by Plan 024 before an R2 assessment becomes live").

## Branch and baseline

- Branch: `feature/plan-024-r2-mock-assessment`.
- Baseline: `main` after Plan 029 (B2-024) merges; this branch merges that `main` before Task 1 starts. The design and plan gate may run earlier.
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.

## Shape evidence (structure only)

`book2/reference/analysis.md` records the Round 2 2026 shape:
- two in-person days, 300 printed points, 5 problems, 26 gradable sub-parts, no printed duration;
- each day pairs one long scaffolded non-open-ended arc with open-ended model-building tasks;
- day 1 has a 90-point 14-part arc plus a 70-point open-ended task;
- day 2 has a 50-point 9-part arc plus open-ended tasks of 40 and 50 points;
- open-ended work carries 160/300 points.

The blueprint encodes this structure, not the 2026 topics.

**Provenance rule (public repo).** Every r2-001 problem is original. The raw paper text and the local index (`book2/reference/r2-2026/`, gitignored) are never copied or closely paraphrased.

Each r2-001 arc and task must differ from its 2026 counterpart in its central object:
- **Day 1 arc.** The 2026 arc was linear attention, relative positions, and a time-series transformer. r2-001 uses **KV caching and grouped-query attention for causal decoding**: cache growth, per-token decode cost, a grouped-query KV-head memory ledger, and a tiny causal decoder whose cached and uncached logits must agree.
- **Day 1 open-ended task.** The 2026 task was single-source force-field reconstruction. r2-001 uses **two-source heat-release localization**: two point sources diffusing on a plate, with time-stamped temperatures at sensors.
- **Day 2 arc.** The 2026 arc was diffusion. r2-001 uses **β-VAEs and the ELBO**: Gaussian KL, reparameterization gradients, the β trade-off, and a tiny VAE with a rate–distortion certificate.
- **Day 2 open-ended tasks.** The 2026 tasks were image-shape classification and mixture-function regression. r2-001 uses:
  - semi-supervised **texture-patch classification** with 5% labels, 40 points;
  - **sum-of-Lorentzian-peaks parameter regression** with `K = 2`, 50 points.

Task 5's self review compares every r2-001 generator and statement against the local index and rationale; Sol and Fable compare against `analysis.md`.
Any resemblance beyond the shared structure gets an `adapted-from` tag or is rewritten.

## Blueprint v1 (live) — `book2/mocktests/blueprint.yaml`

```yaml
blueprint_version: 1
book: 2
target: round-2
status: live
assessment_prefix: r2-
derived_from: [book2:reference/analysis.md, book2:curriculum/official-topics.yaml]
total_points: 300
days: 2
day_duration_minutes: 240        # external assumption: not printed; one in-person day
texture:
  problem_count: {min: 4, max: 6}
  subparts: {min: 22, max: 32}
  open_ended_points_share: {min: 0.45, max: 0.60}   # 2026: 160/300 = 0.533
sections:                        # order fixed; day-scoped
  - {id: d1-arc, day: 1, kind: scaffolded-arc, points: {min: 80, max: 100}, subparts: {min: 10, max: 16}}
  - {id: d1-open, day: 1, kind: open-ended, points: {min: 60, max: 80}}
  - {id: d2-arc, day: 2, kind: scaffolded-arc, points: {min: 40, max: 60}, subparts: {min: 6, max: 10}}
  - {id: d2-open, day: 2, kind: open-ended, points: {min: 80, max: 100}, problems: {min: 2, max: 2}}
topic_distribution:              # points per Book 2 unit cluster; targets sum to 300
  attention-transformers: {target: 60, min: 40, max: 100}
  language-transformers: {target: 30, min: 0, max: 50}
  cross-modal-vision: {target: 20, min: 0, max: 50}
  probabilistic-latent-models: {target: 50, min: 30, max: 70}
  generative-models: {target: 20, min: 0, max: 40}
  capstone: {target: 120, min: 100, max: 160}
difficulty_mix: {intro: {min: 0.10, max: 0.30}, core: {min: 0.35, max: 0.60}, advanced: {min: 0.20, max: 0.40}}
provenance_rules: {original_share_min: 0.9}
arc_rotation:                    # default instantiation: r2-NNN uses index (NNN-1) mod 3
  - {d1: attention-transformers, d2: probabilistic-latent-models}
  - {d1: language-transformers, d2: generative-models}
  - {d1: cross-modal-vision, d2: probabilistic-latent-models}
open_ended_families: [scientific-ml-inverse-problems, semi-supervised-pseudo-labeling, mixture-parameter-regression]
```

Task 1 maps each Book 2 unit to its cluster through its syllabus `cluster`.
Task 1 also makes the cluster names above match the syllabus's actual Book 2 cluster ids. If any id differs, the blueprint uses the syllabus id and this plan's record states the mapping.

## r2-001 instantiation (rotation index 0)

- Total 300 points. Open-ended points 160 (share 0.533).
- 5 problems and 25 sub-parts, laid out across the two days as follows.

| Problem | Section | Points | Sub-parts | Clusters | Form |
|---|---|---:|---:|---|---|
| P1 KV-cached decoding | d1-arc | 90 | 14 (5–10 pts) | attention-transformers 60, language-transformers 30 | theory MC/short-answer/proof + constrained coding; later parts consume earlier results |
| P2 Heat-source localization | d1-open | 70 | 1 | capstone 70 | open-ended notebook: hidden test via `final_test_score`, step budget, four-part writeup |
| P3 β-VAE and the ELBO | d2-arc | 50 | 8 (5–10 pts) | probabilistic-latent-models 50 | theory + constrained coding + tiny training certificate |
| P4 Texture-patch SSL | d2-open | 40 | 1 | capstone 20, cross-modal-vision 20 | open-ended notebook |
| P5 Lorentzian-peak regression | d2-open | 50 | 1 | capstone 30, generative-models 20 | open-ended notebook: a learned regressor; P5(writeup) must compare against a diffusion- or VAE-based amortized alternative in the Alternatives section |

The 25 sub-parts are P1's 14, P3's 8, and one each for P2, P4 and P5.
P4 and P5 split their points across two clusters by their stated sub-skills.
The open-ended rubric awards each task's points as follows:
- 60% for the locked test score against tiered thresholds: beating the committed baseline earns full test-score credit; partial tiers are stated.
- 40% for the four-part writeup (Approach, Alternatives considered, Evaluation with CI, Limitations), using B2-024's rubric.

Difficulty draw targets intro 0.20 / core 0.45 / advanced 0.35, within the blueprint ranges.
Every open-ended task follows B2-024's evaluation protocol: train/validation/locked test, a single `final_test_score` call, `baseline_score`, and `StepBudget`.
Each is `optional-colab-l4`, with a CPU reference solution under 20 s plus an `Accelerator extension`.

## Implementation tasks

### Task 1 — Live Book 2 blueprint and tooling

**Files:**
- `book2/mocktests/blueprint.yaml`
- `tools/checks/blueprint.py`
- `tools/checks/new_mocktest.py`
- `tools/checks/answerkey.py`
- `tools/checks/overlap.py` (only if Book 2 discovery needs it)
- `book2/curriculum/course-schedule.yaml` (`final_assessment`)
- tests: `tests/test_blueprint_book2.py` (new), plus existing blueprint, new-mocktest, and schedule tests

Steps:
- [ ] Write failing tests first:
  - the live Book 2 blueprint validates;
  - a copied fixture r2 manifest is checked for day-scoped sections, per-section points and sub-part ranges, `open_ended_points_share`, the topic distribution, the difficulty mix, and the original share;
  - each violated rule is rejected;
  - Book 1's blueprint check and `r1-001` results are byte-identical;
  - `new-mocktest --book book2 r2-001` scaffolds `day1/` and `day2/` subtrees;
  - `final_assessment` moves from `kind: future-r2-mock, status: planned` to `kind: r2-mock, status: live, test: r2-001, after_book_week: 37`.
- [ ] Implement the minimal generalization: day-aware sections, a `kind` field, and the open-ended share. The planned-skeleton branch is removed together with the planned blueprint.
- [ ] Commit.

### Task 2 — Author r2-001

- [ ] Dispatch problem and statement authoring to an Opus subagent. It writes, in a scratch bundle:
  - `test.md` with per-day front matter;
  - `day1/` and `day2/`, each with `theory/`, `problems/` (statement notebooks), and `data/` (seeded generators);
  - `rubric.md`;
  - the manifest skeleton fields per the blueprint and the `docs/mocktest-generation.md` schema, extended with `day`.
- [ ] The open-ended tasks reuse B2-024's data-module conventions in a per-test `data/r2_001_data.py`, with:
  - immutable splits;
  - per-row SHA-256 hashes;
  - `final_test_score` with a bootstrap CI;
  - `baseline_score`;
  - `StepBudget`.
- [ ] Every scored threshold is calibrated at the frozen seed `SEED=20261101` with stated margins, and every CPU reference solution must run in < 20 s.
- [ ] Hash the bundle.

### Task 3 — Blind solutions, publish, verify

- [ ] Dispatch a separate fresh Opus session to blind-solve from the hash-verified bundle only:
  - theory answers go into `solutions/answers.md` per day;
  - solution notebooks get a final `### Answer check`;
  - open-ended tasks get one reference approach plus the writeup.
  Statement ambiguities are pinned to the solver's choice and recorded.
- [ ] Publish `book2/mocktests/r2-001/` with its final manifest, including `answer_key` fields, and regenerate any generated artifacts.
- [ ] Add a 20-second timeout glob for the r2-001 solutions in `scripts/ci-local.sh` step 3.
- [ ] Add `tests/test_r2_001.py`. It covers:
  - hygiene;
  - manifest-blueprint conformance;
  - answer-key reproduction via `answerkey-check`;
  - each generator's `--check`;
  - the open-ended protocol: one test call, after fitting;
  - the exact file inventory.

### Task 4 — Answer-check integrity (lightweight)

- [ ] Write `tests/test_r2_001_checks.py`. For each P1/P3 coding sub-part, a named wrong implementation fails its answer check:
  - P1: cache appended in the wrong order; grouped-query head mapping off by one; cached logits computed without the causal mask.
  - P3: the KL sign flipped; β applied to reconstruction instead of KL.
- [ ] For each open-ended task, add a leakage mutant and a protocol mutant (`final_test_score` called twice), detected as in B2-024.
- [ ] Wire the suite into `ci-local.sh` step 7. This is a correctness check, not anti-cheat.

### Task 5 — Verification, content gate, report, merge

- [ ] Verification phase:
  - `uv run usaaio-tools --book book2` for blueprint-check, answerkey-check, overlap-scan (it runs against the local reference corpus when present; a loud SKIP is acceptable only when the corpus is absent), and hygiene/tolerance/layer-boundary;
  - the `--all` aggregate checks;
  - `git diff --check`.
- [ ] `scripts/ci-local.sh`, on a clean tip with caches removed: ALL GREEN.
- [ ] 3-way blind content gate, including the fidelity duty against `analysis.md`. Assignments:
  - Sol solves P1 parts 1–7 and P3 fully;
  - Fable solves P1 parts 8–14 and P4;
  - Self solves P2 and P5 and does the provenance comparison against the local index and rationale.
  Resolve every `[OPEN]` finding.
- [ ] Write the post-execution report, add Plan 024 to `TODO.md` (marking Book 2 complete), push, open the PR, run `pre-merge-guard --pr`, squash-merge without deleting local history refs, and verify `main` equals `origin/main`.

## Out of scope

- r2-002 and later mock tests; Book 1 mock tests.
- Any change to B2-019–B2-024 teaching content.
- GPU-required tasks; pretrained weights; any copying of past-paper text.

## Plan Review

Pending.

## Content Review

Pending.

## Post-execution report

Pending.
