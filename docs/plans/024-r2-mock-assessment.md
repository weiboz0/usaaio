# Plan 024 — Round 2 Blueprint and Mock Test r2-001

## Goal

Make Book 2's final assessment live:
- replace the planned version-1 Book 2 blueprint skeleton with a real Round 2 blueprint;
- generalize the mock-test tooling to Book 2 without changing any Book 1 result;
- ship `book2/mocktests/r2-001`, an original two-day, 300-point Round 2 mock test.

Plan 019 reserved Plan 024 for this ("must be replaced by Plan 024 before an R2 assessment becomes live").

## Branch and baseline

- Branch: `feature/plan-024-r2-mock-assessment`.
- Baseline: `main` after Plan 029 (B2-024) merges; this branch merges that `main` before Task 1. The plan gate may run earlier.
- Roster and dispatch: Plan 026's `AGENTS.md`: 3-way (`[self]` / `[sol]` / `[fable]`) gates, with Opus subagents for statements, solutions, and tooling.

## Shape evidence (structure only)

`book2/reference/analysis.md` records the Round 2 2026 shape:
- two in-person days, 300 printed points, 5 problems, 26 gradable sub-parts, no printed duration;
- each day pairs one long scaffolded non-open-ended arc with open-ended model-building tasks;
- day 1 has a 90-point arc plus a 70-point open-ended task;
- day 2 has a 50-point arc plus open-ended tasks of 40 and 50 points;
- open-ended work carries 160/300.

The blueprint encodes this structure, not the 2026 topics.
Fidelity review judges shape only. r2-001's day-1 arc is a fully taught synthesis; the gate record should note that Round 2 arcs typically introduce one fresh mechanism, so r2-002 and later should lean that way.
In particular, analysis.md has no Round 2 style notes, and Task 1 adds a short structure-only "Round 2 shape notes" section to it.

**Provenance (public repo).** Every r2-001 problem is original and differs from its 2026 counterpart in its central object:

| Slot | 2026 central object | r2-001 central object (taught basis) |
|---|---|---|
| d1-arc | linear attention, relative positions, time-series transformer | a causal Transformer language model end to end: masked-attention cost, multi-head parameter ledger, sinusoidal positions, causal-LM shifted targets and perplexity, tiny model training (B2-019 + B2-020) |
| d1-open | single-source force-field reconstruction | two-source heat localization: the Gaussian heat-kernel forward model is defined in the statement (B2-022 Gaussians + B2-024 inverse-problem workflow) |
| d2-arc | diffusion models | VAE and ELBO with a KL weight β (B2-022 Sessions 2, 4, 5 teach KL, ELBO, reparameterization, and β weighting) |
| d2-open (40) | image-shape classification | semi-supervised texture-patch classification with 5% labels (B2-024 Session 4) |
| d2-open (50) | mixture-function parameter regression | sum of `K = 2` Lorentzian peaks; the basis `a/(1+((x−c)/w)²)` is defined in the statement (B2-024 Session 6 workflow) |

The pre-committed resemblance test is that each slot differs in basis function, forward model, or central mechanism.
P5 is the closest sibling of a 2026 task. A different basis family (Lorentzian, not Gaussian), a different `K`, and different sampling are judged sufficient now, not deferred to the gate.

Provenance is executable:
- Before the content gate, the gitignored local corpus `book2/reference/r2-2026/` is copied from the main checkout into the worktree, uncommitted, so `overlap-scan` runs for real. Immediately after the copy, `git status --porcelain --untracked-files=all` must show no `book2/reference/r2-2026/` path (a hard check in a public repo), and the copy is deleted after the gate.
- The self reviewer compares every statement and generator against the local index and rationale.
- A skipped automated scan is reported separately; it is never treated as a pass.

## Taught closure

Every r2-001 sub-part carries only existing Book 2 or imported Book 1 concept ids; no new vocabulary id is introduced.
- **P1** uses `attention-complexity`, `attention-mask`, `causal-self-attention`, `multi-head-attention`, `sinusoidal-positional-encoding`, `transformer-block`, `learned-token-embedding`, `causal-language-modeling`, and `language-transformer`.
- **P3** uses `kl-divergence`, `gaussian-reparameterization`, and `variational-autoencoder`. β is the KL weight taught in B2-022 Session 5.
- **P2, P4, P5** use the B2-024 open-ended concepts; P2 also uses `multivariate-gaussian`.
- Any task-specific formula (the heat kernel, the Lorentzian basis, the β-VAE loss) is stated in full, with conventions, in the statement.
- The student baseline stays Calculus AB plus Books 1–2.

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
day_duration_minutes: 240      # external assumption; Round 2 durations are not printed
texture:
  problem_count: {min: 4, max: 6}
  subparts: {min: 22, max: 32}
  open_ended_points_share: {min: 0.45, max: 0.60}   # 2026: 160/300
sections:                      # order fixed; each carries day and kind
  - {id: d1-arc, day: 1, kind: scaffolded-arc, points: {min: 80, max: 100}, subparts: {min: 10, max: 16}, problems: {min: 1, max: 1}}
  - {id: d1-open, day: 1, kind: open-ended, points: {min: 60, max: 80}, problems: {min: 1, max: 1}}
  - {id: d2-arc, day: 2, kind: scaffolded-arc, points: {min: 40, max: 60}, subparts: {min: 6, max: 10}, problems: {min: 1, max: 1}}
  - {id: d2-open, day: 2, kind: open-ended, points: {min: 80, max: 100}, problems: {min: 2, max: 2}}
default_anchors: {d1-arc: 90, d1-open: 70, d2-arc: 50, d2-open: [40, 50]}
default_time_budget:           # per day; each day sums to day_duration_minutes
  1: {d1-arc: 120, d1-open: 120}
  2: {d2-arc: 80, d2-open: 160}
topic_distribution:            # points per Book 2 syllabus cluster; targets sum to 300
  attention-transformers: {target: 50, min: 30, max: 90}
  language-transformers: {target: 30, min: 0, max: 60}
  cross-modal-vision: {target: 10, min: 0, max: 30}
  probabilistic-latent-models: {target: 40, min: 20, max: 60}
  generative-models: {target: 10, min: 0, max: 30}
  capstone: {target: 160, min: 120, max: 180}
difficulty_mix: {intro: {min: 0.10, max: 0.30}, core: {min: 0.35, max: 0.60}, advanced: {min: 0.20, max: 0.40}}
default_difficulty_draw: {intro: 0.20, core: 0.45, advanced: 0.35}
provenance_rules: {original_share_min: 0.9}
arc_rotation:                  # r2-NNN uses index (NNN-1) mod 3
  - {d1: [attention-transformers, language-transformers], d2: [probabilistic-latent-models]}
  - {d1: [cross-modal-vision, attention-transformers], d2: [generative-models]}
  - {d1: [language-transformers, attention-transformers], d2: [probabilistic-latent-models, generative-models]}
# Open-ended families are constrained by taught closure: B2-024 teaches exactly these three.
# This is a closure constraint, not a mirror of 2026; blueprint-check enforces that each
# open-ended problem's concepts include one of them. Widen when Book 2 grows.
open_ended_families: [scientific-ml-inverse-problems, semi-supervised-pseudo-labeling, mixture-parameter-regression]
```

## r2-001 instantiation (rotation index 0; default anchors)

The test has 5 problems, 25 gradable entries, 300 points, and 160 open-ended points (share 0.533).
Each entry has exactly one cluster.

| Problem | Day / section | Points | Entries | Cluster | Difficulty |
|---|---|---:|---:|---|---|
| P1 causal-LM arc | 1 / d1-arc | 90 | 14 | attention-transformers 60, language-transformers 30, split by entry | per entry |
| P2 two-source heat localization | 1 / d1-open | 70 | 1 | capstone | advanced |
| P3 VAE/ELBO with β | 2 / d2-arc | 50 | 8 | probabilistic-latent-models | per entry |
| P4 texture-patch SSL | 2 / d2-open | 40 | 1 | capstone | core |
| P5 Lorentzian-peak regression | 2 / d2-open | 50 | 1 | capstone | core |

Cluster totals are attention 60, language 30, cross-modal 0, probabilistic-latent 50, generative 0, and capstone 160, all within the blueprint ranges.

Difficulty draw (intro 0.20 / core 0.45 / advanced 0.35):
- Open-ended: P2 advanced 70, P4 core 40, P5 core 50.
- The 140 arc points split as intro 60, core 45, advanced 35, set entry by entry by the author and checked by blueprint-check.
- Totals: intro 60, core 135, advanced 105.

**Open-ended scoring (gradable).** Grading re-executes the notebook under `SEED=20261101` and reads the single `final_test_score` output (the point estimate).
Each task's points split 60% test score and 40% writeup.

Test-score tiers use B = the committed baseline score and R = the committed reference-solution score, both printed in the statement. Calibration must establish that R beats B by a stated margin at the frozen seed: for lower-is-better metrics `R ≤ 0.8·B`, and for P4 `R ≥ B + 0.05`.
Let `g = |B − R|`. The tiers are gap-relative, so they stay strictly ordered whenever R beats B:
- **Lower-is-better metrics** (P2 position error, P5 parameter error):
  - 100% of the 60% when the score is ≤ `R + 0.25g`;
  - 60% when < `B`;
  - 25% when < `B + 0.25g`;
  - otherwise 0.
- **Higher-is-better** (P4 accuracy): the mirrored tiers: 100% when ≥ `R − 0.25g`, 60% when > `B`, 25% when > `B − 0.25g`, otherwise 0.

The writeup is 10% each for Approach, Alternatives considered, Evaluation (with the bootstrap CI), and Limitations, graded against the B2-024 rubric descriptors.
All three open-ended tasks follow B2-024's protocol: train/validation/locked test, one `final_test_score`, `baseline_score`, and `StepBudget`.
They are `optional-colab-l4`, with CPU reference solutions under 20 s and an `Accelerator extension`.

**Open-ended answer keys.** Each P2/P4/P5 manifest entry's `answer_key` is a string `metric=<name>; direction=<lower|higher>; B=<value>; R=<value>; tiers=<full>,<partial60>,<partial25>`. The three cutoffs are the tier thresholds defined above in that order (the otherwise-zero tier needs no cutoff), and every number is written with 4 significant digits. `tests/test_r2_001.py` also checks that the three cutoffs equal the formulas evaluated at the marker's B and R. `solutions/answers.md` carries the identical marker, so `answerkey-check` compares them as it does for theory items. `tests/test_r2_001.py` also verifies the numbers: it re-executes each reference solution and asserts that its single `final_test_score` point estimate equals R and that `baseline_score(task)` equals B, both to a stated tolerance.

## Implementation tasks

### Task 1 — Live Book 2 blueprint and tooling

**Files:**
- `book2/mocktests/blueprint.yaml`
- `book2/reference/analysis.md` (adds the structure-only Round 2 shape notes)
- `tools/model.py`: parse the optional mock-manifest problem field `day: int` and the Book 2 manifest fields `day_duration_minutes` and `time_budget: {day: {section: minutes}}`
- `tools/checks/blueprint.py`: a Book 2 branch in `_validate_manifest`:
  - day-scoped sections with a `kind`;
  - each entry's `day` equals its section's day;
  - per-section points, sub-part, and problem-count ranges;
  - `open_ended_points_share`;
  - each per-day time budget sums to `day_duration_minutes`;
  - the open-ended family rule;
  - Book 1 keys (`five_point_atom_share`, `programming_points_share`, `draws_on_clusters`, `duration_minutes`, the `integrative-arc` special case) read only for Book 1.
  The planned-skeleton branch is deleted.
- `tools/checks/new_mocktest.py`: Book 2 uses the blueprint's `default_anchors`, `default_time_budget`, `arc_rotation`, and `default_difficulty_draw`, so instantiation is zero-choice; Book 1 constants are unchanged.
- `tools/checks/schedule.py`: accept `final_assessment: {kind: r2-mock, status: live, test: r2-001, after_book_week: 37}` only when the named manifest exists; still accept the planned marker only while no `r2-*` manifest exists.
- `tools/checks/answerkey.py` and `tools/checks/overlap.py`: verify Book 2 discovery under the flat layout; change them only if a failing test shows they need it.
- `book2/curriculum/course-schedule.yaml`
- `docs/mocktest-generation.md`: add a Book 2 section covering the pipeline, the manifest extension (`day`, per-day `time_budget`, `day_duration_minutes`), and the default rule. It is not a governance file.
- New tests: `tests/test_blueprint_book2.py`, `tests/test_new_mocktest_book2.py`; schedule tests extended.

**Layout:** flat, like `r1-001`: `test.md`, `theory/`, `problems/`, `solutions/` (with `answers.md`), `data/`, `rubric.md`, `manifest.yaml`. Days live in the manifest's `day` field and in `test.md` (Day 1 and Day 2 sections), so hygiene, answer-key, and PDF discovery work unchanged.

Steps:
- [x] Write failing tests first:
  - the live Book 2 blueprint validates;
  - in a copied fixture, each new rule rejects a violating r2 manifest;
  - Book 1 `blueprint-check` output and every `r1-001` check result are byte-identical before and after;
  - `new-mocktest --book book2 r2-001` scaffolds the flat layout with default anchors;
  - the schedule marker rules hold;
  - hygiene fails on an executed output or a solution placed in an `r2-*` `problems/` notebook.
- [x] Implement, regenerate any generated artifacts, and commit.

### Task 2 — Author r2-001

- [x] An Opus subagent authors a scratch bundle:
  - `test.md`, `theory/`, `problems/`, `data/` (seeded generators and `r2_001_data.py`, which follows B2-024's data-module conventions), and `rubric.md`;
  - the manifest's non-answer fields.
  Every task-specific formula is defined in the statement.
- [x] Every threshold, plus the B and R scores, is calibrated at `SEED=20261101` with stated margins. The calibration script asserts the R-versus-B inequality for each open-ended task, so the tiers are strictly ordered. Every CPU reference solution must run in < 20 s, with timings recorded.
- [x] Hash the bundle.

### Task 3 — Blind solutions, publish, verify

- [x] A separate fresh Opus session blind-solves from the hash-verified bundle only:
  - `solutions/answers.md` for theory;
  - solution notebooks with a final `### Answer check`;
  - open-ended reference approaches with writeups.
  Ambiguities are pinned to the solver's choice and recorded.
- [x] Publish `book2/mocktests/r2-001/` with its final manifest and answer keys. Add an r2-001 20-second solution-timeout glob in `scripts/ci-local.sh` step 3.
- [x] Add `tests/test_r2_001.py`, covering:
  - hygiene;
  - blueprint conformance;
  - `answerkey-check` reproduction;
  - generator `--check`;
  - the one-call protocol;
  - the exact file inventory.

### Task 4 — Answer-check integrity (lightweight)

- [x] Write `tests/test_r2_001_checks.py` with named wrong implementations:
  - P1: causal mask omitted; targets not shifted; positional encoding sin/cos swapped.
  - P3: KL sign flipped; β applied to reconstruction instead of KL (run at the statement's β ≠ 1, where it is detectable).
  - Each open-ended task: a leakage mutant and a protocol mutant (`final_test_score` called twice), detected at named seams as in B2-024.
- [x] Wire the suite into `ci-local.sh` step 7. This is a correctness check, not anti-cheat.

### Task 5 — Verification, content gate, report, merge

- [x] Verification phase:
  - `uv run usaaio-tools --book book2` for blueprint-check, answerkey-check, overlap-scan (run against the copied local corpus), hygiene, tolerance, and layer-boundary;
  - the `--all` aggregate checks;
  - `git diff --check`.
- [x] `scripts/ci-local.sh`, on a clean tip with caches removed: ALL GREEN.
- [x] 3-way blind content gate, with fidelity judged on shape:
  - Sol solves P1 entries 1–7 and P3;
  - Fable solves P1 entries 8–14 and P4;
  - Self solves P2 and P5 and does the provenance comparison against the local index and rationale.
- [ ] Post-execution report, `TODO.md` (Plan 024 shipped; Book 2 complete), push, PR, `pre-merge-guard --pr`, squash-merge without deleting local history refs, and `main` equals `origin/main`.

## Out of scope

- r2-002 and later mock tests; Book 1 mock tests.
- Any change to B2-019–B2-024 teaching content.
- GPU-required tasks; pretrained weights; any copying or close paraphrase of past-paper text.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Review 1 — self (2026-10-10)
- **Verdict**: Approve with suggestions.

### Review 1 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the live schedule marker fails `schedule.py`. → Response: `schedule.py` and its tests are added to Task 1.
2. `[FIXED]` Must Fix: one entry cannot split points across clusters. → Response: every entry has a single cluster; P4 and P5 are capstone only.
3. `[FIXED]` Must Fix: day subtrees bypass hygiene discovery. → Response: flat layout plus a manifest `day` field; a hygiene test is added.
4. `[FIXED]` Must Fix: KV caching and GQA are untaught; the heat and Lorentzian formulas need definitions. → Response: the d1 arc is now a fully taught causal-LM arc, and every task formula is defined in its statement.
5. `[FIXED]` Should Fix: open-ended scoring contract. → Response: tiered B/R thresholds, re-execution under the seed, and the writeup split.
6. `[FIXED]` Should Fix: provenance review must be executable. → Response: the local corpus is copied into the worktree before the gate; skips are reported separately.
7. `[FIXED]` Nit: pin the `day` field. → Response: Task 1 specifies the model.py parsing and the checker rules.

### Review 1 — Fable (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: taught closure for P1, β, and the heat operator. → Response: the "Taught closure" section lists the exact concept tags; formulas are defined in-statement; β is taught in B2-022 Session 5.
2. `[FIXED]` Must Fix: split clusters. → Response: as Sol 2; cross-modal and generative are left at 0 for r2-001.
3. `[FIXED]` Should Fix: enumerate the tooling changes. → Response: Task 1 lists every key, field, and file; `default_anchors` and `default_time_budget` are added to the blueprint.
4. `[FIXED]` Should Fix: layout ambiguity. → Response: the flat layout is pinned.
5. `[FIXED]` Should Fix: open-ended tiers. → Response: pinned (point estimate, B/R tiers, re-execution).
6. `[FIXED]` Should Fix: difficulty labels. → Response: P2 advanced, P4/P5 core, arc split 60/45/35.
7. `[FIXED]` Should Fix: `docs/mocktest-generation.md` is Book-1-only. → Response: a Book 2 section is added in Task 1.
8. `[FIXED]` Should Fix: no Round 2 register for fidelity. → Response: shape-only fidelity, plus structure-only notes added to `analysis.md`.
9. `[FIXED]` Should Fix: `open_ended_families` comment. → Response: the blueprint comment states it is a closure constraint, enforced, and to be widened later.
10. `[WONTFIX]` Nit: "AGENTS.md still says 4-way". → Response: `main`'s `AGENTS.md` (Plan 026) is 3-way with Opus dispatch (lines 15, 31, 82).
11. `[WONTFIX]` Nit: dispatch should be codex. → Response: same evidence; Plan 026 routes statements, solutions, and tooling to Opus.
12. `[FIXED]` Nit: pre-commit the resemblance test. → Response: stated under "Provenance".
13. `[FIXED]` Nit: GQA mutant. → Response: GQA is removed; P1 mutants are replaced.

### Review 2 — self (2026-10-10)
- **Verdict**: Approve after fixes.

### Review 2 — Fable (2026-10-10)
- **Verdict**: Approve with nits. Withdrew round-1 nits 10–11 after checking `AGENTS.md`.
1. `[FIXED]` Nit: tier ordering needs calibration inequalities. → Response: gap-relative tiers plus an asserted R-versus-B margin.
2. `[FIXED]` Nit: the β mutant must run at β ≠ 1.
3. `[FIXED]` Nit: arc-novelty note recorded for later mock tests.
4. `[FIXED]` Nit: an explicit `git status` check after the corpus copy; the copy is deleted after the gate.

### Review 2 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the 1.25× tiers can overlap. → Response: gap-relative tiers `R + 0.25g`, `B`, `B + 0.25g` (mirrored for P4), strictly ordered whenever R beats B; calibration asserts `R ≤ 0.8·B` (P4: `R ≥ B + 0.05`).
2. `[FIXED]` Should Fix: open-ended answer-key representation. → Response: a `metric/B/R/tiers` marker in both the manifest and `answers.md`; `test_r2_001.py` re-executes the reference solutions and verifies R and B.
3. `[FIXED]` Nit: "All four tasks" → "All three open-ended tasks".
- Open dependency noted: B2-024's taught closure is re-checked after Plan 029 merges (Task 1 baseline).

### Review 3 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Approve with nits.
1. `[FIXED]` Nit: the `tiers=<four cutoffs>` marker was ambiguous. → Response: field order, direction, three cutoffs, 4-significant-digit precision, and a test check against the formulas.

### Review 3 — self (2026-10-10)
- **Verdict**: Approve.

**Gate result:** 3-way consensus (Fable approved at round 2; Sol at round 3; self). Implementation is authorized once Plan 029 merges and this branch merges that `main`; B2-024's taught closure is re-checked at Task 1.

## Content Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`). Fidelity is judged on shape. The local corpora were copied uncommitted for a real `overlap-scan`, and `git status` showed no reference paths.

### Review 1 — self (2026-10-10)
- **Provenance**: compared every r2-001 slot against the local 2026 index summaries; each differs in central object:
  - P1: causal LM, not linear attention.
  - P2: two-source scalar heat kernel, not a single-source vector field.
  - P3: β-VAE, not diffusion.
  - P4: grayscale texture patches with scanner shift, not RGB shapes. Same family, forced by taught closure.
  - P5: K = 2 Lorentzian, not an 11-parameter exponential/log/trig/linear mixture.
- **Overlap scan**: with the corpus present, it first failed on four **B2-023** notebooks. Their only shared 8-word shingles were standard DDPM formulas in LaTeX. → Fixed in `tools/checks/overlap.py` (1dc54a1): LaTeX math spans are stripped on the artifact side; a prose-detection test is added. Book 1 and Book 2 scans pass against their corpora, and Book 1 output is identical to `main`.
- **PDF build**: Book 2's branch built units only. → `build-pdf.sh` now renders r2-* mock tests to `build/mocktests/<test>/<subdir>/` (1127b3f). This is a deviation: the plan had assumed discovery worked unchanged.
- **Verdict**: Approve with suggestions.

### Review 1 — Sol, `gpt-6-sol` (2026-10-10)
- **Blind answers**: P1 1.1–1.7 (B/35; 73,728; C/65; 4d²+4d and 8,544; 18,712; D; 0.3456) and P3 3.1–3.6 all match the keys; 3.7/3.8 match on re-execution.
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: P4 gave full credit to a labelled-only head (0.985). → Response (e2ae9bd): P4 now has a scanner shift between the labelled rows and the pool/test. The best labelled-only probe of seven reaches 0.6475; the pool-using reference reaches 0.9900. New B = 0.4850, R = 0.9900, tiers 0.8638 / 0.4850 / 0.3588. A regression test keeps labelled-only ≤ full-credit cutoff − 0.15. Batch statistics on test/validation inside `predict` count as fitting.
2. `[FIXED]` Must Fix: P1.13 key versus reproduction (1.130). → Response: the key stays 1.132 (Fable reproduced it exactly). The worked text records this machine's 1.130, and the answers/rubric state that the platform-dependent last digit is within the 0.03 tolerance.
3. `[FIXED]` Should Fix: arc rotation was bypassable via manifest metadata. → Response: derived from the test number; a mismatch needs `arc_deviation_reason`; tests added.
4. `[FIXED]` Should Fix: section semantics and negative budgets. → Response: open-ended entries must be programming/open-ended and arc entries may not be; per-day budgets must be positive ints; tests added.

### Review 1 — Fable (2026-10-10)
- **Blind answers**: P1 1.8–1.14 all match (including 1.13 = 1.132 reproduced exactly); P4 own CNN self-training scored 0.9075 (on the original data).
- **Verdict**: Approve with nits.
1. `[FIXED]` Should Fix: the P1.13 worked text was stale. → Response: as Sol 2.
2. `[WONTFIX]` Nit: inline-math stripping weakens shingle alignment across inline math. → Response: pdftotext already mangles reference math, so aligning inline symbols would re-create notation false positives; prose is still detected (test).
3. `[FIXED]` Nit: acknowledge that the noise-free corpus makes validation perplexity an implementation certificate. → Response: one sentence in Part 1.14.
4. `[FIXED]` Nit: P4 tier calibration. → Response: superseded by the Sol 1 redesign.

### Review 2 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Reject.
1. `[WONTFIX]` Must Fix: the student-visible generator exposes the seeded scanner-B offset, so a reader can reconstruct it and score 0.9475 without the pool. → Response: recovering hidden generation parameters from the provided source is cheating, not a flaw in the assessed material. Anti-cheat machinery is out of scope by user directive (2026-08-28), and datasets must be produced by visible seeded generators (`AGENTS.md`). The statement and rubric now state the rule plainly: using the generator to recover scanner or generation parameters or any held-back label is a protocol violation scoring 0, like the existing bans on `simulate` and test-batch statistics. No obfuscation is added.
2. `[FIXED]` Should Fix: "certificate" overstated what validation perplexity proves. → Response: reworded as "a useful check … not by itself a proof of correctness".
- Confirmed closed: P1.13 key consistency; the validator Should Fixes (rotation, section forms, budgets).

### Review 3 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Approve. Under the stated rule, honest solvers need the pool (a labelled-only probe scores 0.5675; the best recorded is 0.6475; full-credit cutoff 0.8638). The p01 wording fix was verified.

### Review 2 — Fable (2026-10-10)
- **Verdict**: Approve with nits. Its own P4 attempts on the redesigned data scored 0.3575 (naive self-training, 0 tier), 0.7975 and 0.8025 (60% tier), against the reference 0.9900 (100%). The tiers discriminate, and validation tracks the test ordering.
1. `[FIXED]` Nit: `day_time_budget` holds raw YAML values. → Response: a field comment says blueprint-check validates them.
2. `[WONTFIX]` Nit: the 60% tier spans labelled-only and weakly pool-using scores. → Response: a property of the gated gap-relative scheme; recorded as a consideration for r2-002 (a fourth tier or a labelled-only anchor).
3. `[WONTFIX]` Nit: rubric wording for the weaker alternative already labels 0.9250 as the test score.

### Review 2 — self (2026-10-10)
- **Verdict**: Approve.

**Gate result:** 3-way consensus (Sol round 3, Fable round 2, self).

## Post-execution report

**Shipped:** Book 2's final assessment is live.
- `book2/mocktests/blueprint.yaml` is the version-1 live Round 2 blueprint; the planned skeleton and its checker branch are removed.
- `book2/mocktests/r2-001` is an original two-day, 300-point mock test: 5 problems and 25 entries; P1 causal-LM arc 90, P2 heat localization 70, P3 β-VAE arc 50, P4 texture SSL 40, P5 Lorentzian regression 50; 160 points open-ended.
- `course-schedule.yaml` carries the live marker `final_assessment: {kind: r2-mock, status: live, test: r2-001, after_book_week: 37}`.
- **Book 2 is complete:** units B2-019 through B2-024 plus its final assessment.

**Tooling (Book 1 results byte-identical; verified by diffing check output against `main`):**
- `tools/model.py` gains the mock-manifest `day`, `day_duration_minutes`, and per-day `time_budget`.
- `tools/checks/blueprint.py` gains a Round 2 branch:
  - day-scoped sections and kinds;
  - section semantics;
  - points, sub-part, and problem ranges;
  - the open-ended share;
  - positive per-day budgets;
  - arc rotation derived from the test number;
  - open-ended family closure.
- `new_mocktest.py`: zero-choice Book 2 scaffolding.
- `schedule.py`: the live marker requires its manifest.
- `overlap.py`: LaTeX math spans are stripped from artifact text before shingling. This fixed four false positives on standard DDPM notation in B2-023.
- `build-pdf.sh`: Book 2 renders its mock tests.
- `docs/mocktest-generation.md` has a Book 2 section; `analysis.md` has structure-only Round 2 shape notes.

**Dispatch:**
- An Opus author wrote the bundle; a separate fresh Opus session blind-solved all 25 entries from student-facing files only. Every answer matched the author's keys.
- An Opus implementer did Tasks 1, 3 and 4 (9db06af, f849068, 935874a, 36362f3).
- The orchestrator fixed the PDF build (1127b3f) and the overlap scan (1dc54a1).
- An Opus fixer did the content-gate round-1 fixes (e2ae9bd); the orchestrator did eee1479 and 28fd5fd.

**Publication fixes from blind solving:**
- the Lorentz generator's post-rounding separation check;
- R taken from the published reference solutions;
- P4 seam wording for feature pipelines;
- `.detach()` in P1.12.

**Deviations:**
- `build-pdf.sh` needed a Book 2 mock-test branch; the plan assumed discovery worked unchanged.
- `overlap.py` changed, as allowed by the plan's "only if a failing test shows they need it".
- P4 was redesigned in the content gate: a scanner shift makes the pool necessary. The best labelled-only probe of seven scores 0.6475; the reference scores 0.9900.
- A student-visible generator could reveal the shift. This is handled as a stated protocol rule (score 0), not by obfuscation, per the anti-cheat directive.

**Final open-ended keys:**
- P2: B = 0.04810, R = 0.001541, tiers 0.01318 / 0.04810 / 0.05974.
- P4: B = 0.4850, R = 0.9900, tiers 0.8638 / 0.4850 / 0.3588.
- P5: B = 0.01711, R = 0.005272, tiers 0.008231 / 0.01711 / 0.02007.

**Verification:**
- Focused suites: 183 + 22 + 13 passed.
- Full pytest: 1615 passed plus two fixed or transient failures, then re-verified.
- `overlap-scan` with the local corpora present: PASS for both books, and `git status` showed no reference paths.
- r2-001 solutions run in 7.6–13.2 s.
- The final authoritative CI is recorded below.

**Content gate:**
- Three-way consensus: Sol over three rounds, Fable over two, self.
- Provenance: self compared every slot against the local 2026 index summaries, and the automated scan passed.

**For r2-002:**
- Introduce one fresh mechanism in the day-1 arc.
- Consider a fourth scoring tier, or anchoring the 60% tier at the best labelled-only probe.
