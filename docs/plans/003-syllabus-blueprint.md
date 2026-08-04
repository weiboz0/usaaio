# Plan 003 — Syllabus + Blueprint Implementation Plan

> **For agentic workers:** Execute task-by-task with per-task commits.

**Goal:** Ship the curriculum's skeleton — `syllabus.md` (concept vocabulary, Calc AB + Python baseline allowlist, unit DAG with foundation/core tracks) — and the mock-test generation contract — `mocktests/blueprint.yaml` v1 + the completed `docs/mocktest-generation.md` — all derived from `reference/analysis.md`.

**Architecture:** One source of truth per concern. `syllabus.md` holds the concept vocabulary and unit DAG as ONE embedded fenced YAML block (machine-readable, parsed by plan 004's `prereq-check`/`coverage-check`) followed by human narrative; two files would drift. `mocktests/blueprint.yaml` holds the Round 1 test specification with explicit tolerances (consumed by `blueprint-check`). `docs/mocktest-generation.md` replaces its stub with the operational pipeline, including the mock-test `manifest.yaml` schema.

**Tech Stack:** Markdown + YAML only; a throwaway scratchpad Python check for DAG consistency (no shipped tooling — plan 004 owns the real checks).

## Global Constraints

- Baseline is EXACTLY Calculus AB + basic Python (design §2a); anything else must be taught by a unit reachable in the DAG.
- Grounding: every parameter in the blueprint must trace to `reference/analysis.md` (n=1 2026 paper + 2025 structural metadata) — cite the analysis section inline as YAML comments. State printed-vs-inferred honestly.
- Public repo: no verbatim past-problem text anywhere (short technical terms/topic names fine).
- Semantic line breaks in Markdown; `docs/mocktest-generation.md` is NOT governance-listed and may be edited by this plan.
- Everything on branch `feature/plan-003-syllabus-blueprint`; both gates before merge.

---

### Task 1: syllabus.md

**Files:** Create: `syllabus.md`

**Structure:** (1) intro + how-to-read; (2) ONE fenced ```yaml block — the canonical machine-readable syllabus, **immediately preceded by the sentinel line `<!-- syllabus-canonical -->`**; plan 004's parser selects the fence that follows this sentinel (robust against future example fences elsewhere), and syllabus.md states this contract in its intro; (3) narrative per track explaining sequencing rationale against `reference/analysis.md` — narrative refers to concepts by their vocabulary ids so prose and YAML cannot drift silently.

**Embedded YAML schema:**

```yaml
syllabus_version: 1
baseline:   # the Calc AB + basic Python allowlist — concepts units may use WITHOUT teaching
  math: [algebra, functions-and-graphs, trigonometry-basics, limits, derivatives-1d,
         chain-rule-1d, integrals-1d, exponentials-and-logs]
  python: [variables-and-types, lists-dicts-sets, control-flow, functions,
           classes-basics, file-io-basics]
concepts:   # the full vocabulary; every unit concepts-taught/used and every problem tag
            # must come from this list (plan 004 enforces)
  - id: vectors-and-norms
    cluster: linear-algebra
  # … full vocabulary, one entry per concept, clusters matching analysis.md's topic table:
  # linear-algebra, ml-concepts, numpy, pytorch, probability-statistics, calculus-multivar,
  # cnn-vision, nlp-embeddings, applied-ml, python-scientific, competition-craft
units:
  - id: F1-scientific-python
    track: foundation
    title: Scientific Python and NumPy
    prereqs: []           # baseline only
    teaches: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization,
              elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
  # … all units, see the roster below
```

**Unit roster to encode** (id / prereqs / teaches-summary — the load-bearing decision, reviewers judge this):

Foundation track (F1 comes first; math-unit practice mixes by-hand and NumPy work, so
NumPy-heavy units declare F1):
1. `F1-scientific-python` — [] — NumPy arrays, indexing, broadcasting, vectorization, aggregation, seeding, matplotlib.
2. `F2-vectors` — [F1] — vectors, norms, distance, dot product, cosine similarity, projection, residuals, unit vectors.
3. `F3-matrices` — [F2] — matrices as linear maps, matmul, rank, invertibility (via rank), outer products, matrix reconstruction from action, Gram matrices.
4. `F4-multivar-calculus` — [F2] — partial derivatives, gradient, multivariable chain rule, gradients of sum-of-squares/component forms (matrix-free statement; MSE done componentwise).
5. `F5-probability` — [F1] — random variables, expectation, variance, independence, variance of sums/products, Gaussian distribution, sampling.
6. `F6-svd-spectral` — [F3] — eigenvalues, spectral decomposition, SVD, singular values, low-rank approximation (Eckart-Young operationally), Frobenius norm. **Flagged double-length unit** (heaviest load in the roster; lesson splits into two sittings).

Core track:
7. `C1-ml-fundamentals` — [F1] — supervised/unsupervised/clustering framing, train/test split, overfitting, bias-variance (intuitive treatment — rigorous variance deferred to F5-dependent units), accuracy/precision/recall/F1/f1-macro, class imbalance.
8. `C2-linear-models` — [F3, F4, C1] — linear regression, MSE, **gradient view only** (closed-form/normal equations out of scope — matrix inversion is deliberately not in the vocabulary; invertibility-via-rank in F3 covers the competition's reasoning needs), L1/L2 regularization, sparsity intuition.
9. `C3-gradient-descent` — [F4, C2] — loss surfaces, gradient descent, learning rate, stochasticity (light).
10. `C4-classical-ml-practice` — [C1, F1, F2] — kNN, distance metrics (F2 required: norms/distances), pandas basics (dataframes, CSV loading — the tooling-surface gap), feature scaling/preprocessing, pipelines, cross-validation, sklearn craft.
11. `C5-neural-networks` — [C3, F5] — perceptron, activations (threshold, tanh + its derivative, ReLU), MLP as function composition, geometric decision boundaries (half-planes/intersections), variance-preserving weight initialization.
12. `C6-pytorch` — [C5] — tensors, nn.Module subclassing, custom layers, manual weights, requires_grad, parameter counting.
13. `C7-cnn-transfer` — [C6] — convolution, feature maps and depth hierarchy, receptive fields, ResNet blocks (bottleneck arithmetic), truncation/freezing, transfer learning.
14. `C8-embeddings` — [F2, F3, F1] — tokenization, word embeddings, embedding matrices, similarity (Gram) matrices, nearest neighbors, gensim usage. (F3 required: similarity matrix = Gram matrix W·Wᵀ.)
15. `C9-dimensionality-reduction` — [F6, C8, F5, C1] — PCA (variance-maximization framing needs F5; projection framing needs F6), truncated SVD in practice, UMAP conceptually (C1 supplies the model-selection context), when local vs global structure matters.
16. `C10-competition-craft` — [C4] — notebook discipline (run-clean top-to-bottom), hidden-test protocols, prediction-function contracts, metric-driven iteration, write-up quality.

Acceptance criteria (Task 4 verifies): DAG is acyclic; every `teaches`/`prereqs` reference resolves; every concept in the vocabulary is taught by exactly one unit; every analysis.md "ceiling" topic (SVD/low-rank, init variance, ResNet surgery, CNN hierarchy, model-selection craft) maps to a unit; every cluster in the analysis topic table has ≥1 unit.

**Steps:** write file → scratchpad DAG check (below) → commit.

---

### Task 2: mocktests/blueprint.yaml

**Files:** Create: `mocktests/blueprint.yaml`

**Content (v1 — every value cited to analysis.md by comment):**

```yaml
blueprint_version: 1
derived_from: reference/analysis.md   # n=1 full paper (r1-2026) + r1-2025 structure
target: round-1
duration_minutes: 180                  # external (official schedule)
total_points: 300                      # printed
texture:                               # invariants (blueprint-check enforces)
  subparts: {min: 33, max: 41}         # 2026: 37; 2025: >=39 VISIBLE (pagination may hide
                                       # more — n=1 fully-counted sample; max is provisional)
  five_point_atom_share: {min: 0.55}   # 2026: 24/37 = 0.65
  programming_points_share: {min: 0.45, max: 0.55}   # 2026: ~150/300 INFERRED from
                                       # answer-form tagging, not a printed figure
  problem_count: {min: 3, max: 10}     # free parameter (3 in 2025, 9 in 2026)
sections:                              # required test texture, order fixed
  - id: concept-block
    points: {min: 40, max: 60}         # 2026: 50
    style: multiple-choice, 5 options A-E, 10-pt atoms, opening position
    draws_on_clusters: [ml-concepts]
  - id: math-computation
    points: {min: 20, max: 45}         # 2026: P2+P3+P4.1 = 30 (+MC-numeric style)
    style: short scaffolded problems; numeric normal-form MC or short-answer/proof
    draws_on_clusters: [linear-algebra, calculus-multivar, probability-statistics]
  - id: integrative-arc
    points: {min: 80, max: 100}        # 2026: 90 (15 parts)
    subparts: {min: 12, max: 16}
    style: one narrative dataset/model journey mixing theory + code sub-parts,
           later parts consume earlier results
    draws_on_clusters: [nlp-embeddings, linear-algebra, numpy]   # rotate per test
  - id: engineering
    points: {min: 50, max: 90}         # 2026: P6+P7+P8 = 65
    style: 2-3 problems; framework tasks with exact identifiers, shape contracts,
           API bans with zero-point clauses
    draws_on_clusters: [pytorch, cnn-vision, numpy]
  - id: open-ended-notebook
    points: {min: 40, max: 60}         # 2026: 50 (16.7%)
    style: Kaggle-style hidden-test task, single model-family constraint,
           run-clean notebook + written summary required
    draws_on_clusters: [applied-ml, competition-craft]
topic_distribution:                    # POINTS per cluster as {target, min, max};
                                       # targets sum to total_points exactly (integers, not
                                       # shares — 2dp shares round to 1.01). Tolerances are
                                       # per-cluster (±20 for targets >=50, else ±10) so small
                                       # clusters can't silently absorb a whole problem.
  linear-algebra: {target: 60, min: 40, max: 80}
  ml-concepts: {target: 50, min: 30, max: 70}
  numpy: {target: 55, min: 35, max: 75}
  pytorch: {target: 50, min: 30, max: 70}
  applied-ml: {target: 50, min: 30, max: 70}
  cnn-vision: {target: 10, min: 0, max: 20}
  nlp-embeddings: {target: 15, min: 5, max: 25}
  probability-statistics: {target: 5, min: 0, max: 15}
  calculus-multivar: {target: 5, min: 0, max: 15}
cluster_fold:                          # clusters problems may tag that fold into the
                                       # distribution above for blueprint-check purposes
  python-scientific: numpy
  competition-craft: applied-ml
cluster_aliases:                       # analysis.md topic-table row -> canonical cluster id
  "Linear algebra": linear-algebra
  "ML concepts": ml-concepts
  "NumPy implementation": numpy
  "PyTorch engineering": pytorch
  "Probability/statistics": probability-statistics
  "Calculus": calculus-multivar
  "CNN representations": cnn-vision
  "NLP/embeddings context": nlp-embeddings
  "Applied tabular ML": applied-ml
difficulty_mix:                        # per-band FLOORS/CEILINGS on point share (bands need
                                       # not partition — a test's actual shares sum to 1 by
                                       # construction; check: min-sum 0.75 <= 1 <= max-sum 1.25)
  intro: {min: 0.15, max: 0.30}        # baseline-reachable ~70/300 = 0.23
  core: {min: 0.35, max: 0.55}
  advanced: {min: 0.25, max: 0.40}
style_rules:                           # fidelity half of blueprint-check + reviewer duties
  - five-option MC (A-E)
  - numeric answers unique-decodable via normal forms (gcd/sign constraints)
  - exact function/class identifiers; snake_case functions, My_CamelCase modules
  - explicit per-part reasoning-required flags
  - banned-API lists with zero-point penalty clauses
  - complete runnable starter code; public datasets via stable URLs
provenance_rules:
  original_share_min: 0.7              # design: mixed, original default
  adapted_requires_tag: adapted-from
constraints:
  - every problem tags >=1 unit from syllabus.md; no concept outside taught closure
  - datasets generated by seeded scripts
```

**Steps:** write file → verify YAML parses + topic_distribution targets sum to exactly total_points → commit.

---

### Task 3: docs/mocktest-generation.md (replace stub)

**Files:** Modify: `docs/mocktest-generation.md`

**Required sections:**
1. **Pipeline** — the five stages (blueprint → instantiate → draft → verify → gate) with concrete commands; until plan 004 ships `new-mocktest`, instantiation is manual: copy the documented directory skeleton + manifest template.
2. **Manifest schema** for `mocktests/r1-NNN/manifest.yaml`: test id, blueprint_version, generation date + parameters (section point allocations chosen, clusters rotated into the arc, difficulty draw), per-problem entries (id, section, units drawn on, concept tags, points, difficulty, provenance original/adapted-from, answer-key values for solution verification, **dataset `generator_script` path + `seed`** so data are reproducible without reading solution cells), time budget per section.
3. **Drafting rules** — problem specs from the blueprint section styles; solutions authored as executable notebooks with fixed seeds; datasets via seeded generation scripts; student/solution notebook separation (hygiene).
4. **Verification map** — which ci-local check covers which blueprint field (blueprint-check ↔ texture/sections/topic_distribution; overlap-scan ↔ provenance; prereq-check ↔ taught-closure; coverage/hygiene; all SKIP-LOUDLY until plan 004).
5. **Review duties pointer** — content-gate fidelity review compares against `reference/analysis.md ## Style notes`.

**Steps:** write → commit.

---

### Task 4: Cross-consistency verification + ship

- [ ] Scratchpad Python check (not shipped): parse syllabus.md's sentinel-marked fenced YAML + blueprint.yaml; assert (a) unit DAG acyclic, all refs resolve; (b) every concept taught exactly once; (c) all baseline/taught concept ids unique; (d) every blueprint cluster reference (incl. cluster_fold keys/values and section draws_on_clusters) exists in the syllabus cluster set; (e) topic_distribution targets sum to exactly total_points, and each {min ≤ target ≤ max}; (f) section point mins ≤ maxes, min-sums ≤ 300 ≤ max-sums, and an exact-300 integer combination exists within the ranges; (g) transitive prereq closure edge sanity (C8→F3 present; C5 reaches F3 via C2; C6 reaches F1 via C1; C4→F2 present); (h) **ceiling-topic mapping** — for each analysis.md ceiling topic (truncated SVD/low-rank, variance-preserving init, ResNet internals, CNN feature hierarchy, model-selection craft) assert a unit teaches a matching concept id; (i) difficulty_mix band min-sum ≤ 1 ≤ max-sum.
- [ ] `bash scripts/ci-local.sh` → ALL GREEN.
- [ ] Content-review gate (4-way): duties — curriculum soundness (sequencing, unit scoping, nothing untaught-but-used, Calc AB accessibility of F-track entry points), blueprint fidelity to analysis.md (spot-check cited numbers), generation-doc completeness (could a fresh session produce r1-001 from it?).
- [ ] Post-execution report; tick TODO 003; final ci-local; push; PR; `pre-merge-guard.sh --pr`; squash-merge.

---

## Out of scope

- **Verification-phase exemption:** docs-only plan (no units, no mock tests, no tooling); the design-§2 named verification phase does not apply. Task 4's scripted consistency check + gates are the verification.
- Lesson content (plan 005+), real check tooling (plan 004), any r1-NNN test (plan 006).
- Round 2 blueprint.

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` topic_distribution as 2-decimal shares summed to 1.01 — switched to integer
   points per cluster (sums to exactly 300; matches how tooling should check it).
2. `[FIXED]` `C8-embeddings` used Gram matrices without declaring `F3-matrices` — edge added.
3. `[NOTED]` Verified transitive reachability for other suspected gaps: C5 reaches F3 via
   C2; C6 reaches F1 via C1's prereq; section min-sums 230 ≤ 300 ≤ max-sums 355.
4. `[NOTED]` Embedded-fenced-YAML choice accepted deliberately: one file, no drift; plan
   004 parses the first ```yaml fence; risk of a second stray fence handled by convention
   ("the FIRST fence is canonical") to be stated in syllabus.md itself.
   (Superseded by round 1: sentinel-line contract, see [codex] #5 / [glm] #4.)

### Review 2 — [fable] Independent Fable 5, fresh context (2026-08-04)

- **Verdict**: REJECT → all findings fixed, re-review requested

1. `[FIXED]` topic_distribution summed to 1.01 (raced the self-review fix; now integer
   points with per-cluster {target,min,max}).
2. `[FIXED]` C4 taught kNN/distance without F2 — edge added.
3. `[FIXED]` C2 "closed-form" needed matrix inversion taught nowhere — C2 scoped to
   gradient view explicitly; F3 gains invertibility-via-rank (covers the competition's
   is-it-invertible reasoning).
4. `[FIXED]` F4 quadratic forms → restated as sum-of-squares/component forms, matrix-free.
5. `[FIXED]` C9 PCA needed probability — F5 + C1 edges added with justification.
6. `[FIXED]` F-track NumPy practice — F1 declared for F2/F5 (F3/F6 reach F1 via F2);
   sequencing note added.
7. `[FIXED]` pandas used-but-never-taught — added to C4 teaches.
8. `[FIXED]` 11-vs-9 cluster mismatch — `cluster_fold` map added
   (python-scientific→numpy, competition-craft→applied-ml).
9. `[FIXED]` Flat tolerance vacuous for small clusters — per-cluster min/max encoded.
10. `[FIXED]` F6 overload — flagged as explicit double-length unit.
11. `[FIXED]` C1 bias-variance marked intuitive treatment.
12. `[FIXED]` subparts max n=1 fragility — comment added inline.

### Review 3 — [codex] Codex GPT-5.5 (2026-08-04)

- **Verdict**: REJECT → all findings fixed, re-review requested

1. `[FIXED]` Task 2/Task 4 still said "sums to 1.0" after the points switch —
   both updated to "targets sum to exactly total_points".
2. `[FIXED]` pandas gap — same as [fable] #7.
3. `[FIXED]` C9 prereqs under-specified — same as [fable] #5.
4. `[FIXED]` 150/300 marked as INFERRED from answer-form tagging, not printed.
5. `[FIXED]` Embedded-YAML extraction contract — sentinel line
   `<!-- syllabus-canonical -->` specified; syllabus.md states the contract;
   narrative must use vocabulary ids.
6. `[FIXED]` Task 4 checks extended: ceiling-topic mapping (h), cluster_fold/section
   cluster refs (d), exact-300 feasibility (f), difficulty band sum (i);
   generation-doc completeness confirmed as an explicit content-gate duty.

### Review 4 — [glm] GLM 5.2 (2026-08-04)

- **Verdict**: REJECT → all findings fixed, re-review requested

1. `[FIXED]` 1.01 sum — same as [fable] #1 (integer points + reconciled checks).
2. `[FIXED]` Ceiling-topic check added as Task 4(h).
3. `[FIXED]` difficulty_mix clarified as per-band floors/ceilings + band-sum check (i).
4. `[FIXED]` Fence ambiguity — sentinel contract, same as [codex] #5.
5. `[FIXED]` Cluster alias map (analysis.md row names → canonical ids) added to blueprint.
6. `[FIXED]` Manifest schema gains per-problem dataset `generator_script` + `seed`.
7. `[FIXED]` Exact-300 feasibility assertion added to Task 4(f).

## Content Review

(Pre-PR gate findings land here.)
