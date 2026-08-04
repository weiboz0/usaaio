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

**Structure:** (1) intro + how-to-read; (2) ONE fenced ```yaml block — the canonical machine-readable syllabus; (3) narrative per track explaining sequencing rationale against `reference/analysis.md`.

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

Foundation track:
1. `F1-scientific-python` — [] — NumPy arrays, indexing, broadcasting, vectorization, aggregation, seeding, matplotlib.
2. `F2-vectors` — [] — vectors, norms, dot product, cosine similarity, projection, residuals, unit vectors.
3. `F3-matrices` — [F2] — matrices as linear maps, matmul, rank, outer products, matrix reconstruction from action, Gram matrices.
4. `F4-multivar-calculus` — [F2] — partial derivatives, gradient, multivariable chain rule, gradient of quadratic/MSE forms.
5. `F5-probability` — [] — random variables, expectation, variance, independence, variance of sums/products, Gaussian distribution, sampling.
6. `F6-svd-spectral` — [F3] — eigenvalues, spectral decomposition, SVD, singular values, low-rank approximation (Eckart-Young operationally), Frobenius norm.

Core track:
7. `C1-ml-fundamentals` — [F1] — supervised/unsupervised/clustering framing, train/test split, overfitting, bias-variance, accuracy/precision/recall/F1/f1-macro, class imbalance.
8. `C2-linear-models` — [F3, F4, C1] — linear regression, MSE, closed-form vs gradient view, L1/L2 regularization, sparsity intuition.
9. `C3-gradient-descent` — [F4, C2] — loss surfaces, gradient descent, learning rate, stochasticity (light).
10. `C4-classical-ml-practice` — [C1, F1] — kNN, distance metrics, feature scaling/preprocessing, pipelines, cross-validation, sklearn craft.
11. `C5-neural-networks` — [C3, F5] — perceptron, activations (threshold, tanh + its derivative, ReLU), MLP as function composition, geometric decision boundaries (half-planes/intersections), variance-preserving weight initialization.
12. `C6-pytorch` — [C5] — tensors, nn.Module subclassing, custom layers, manual weights, requires_grad, parameter counting.
13. `C7-cnn-transfer` — [C6] — convolution, feature maps and depth hierarchy, receptive fields, ResNet blocks (bottleneck arithmetic), truncation/freezing, transfer learning.
14. `C8-embeddings` — [F2, F3, F1] — tokenization, word embeddings, embedding matrices, similarity (Gram) matrices, nearest neighbors, gensim usage. (F3 required: similarity matrix = Gram matrix W·Wᵀ.)
15. `C9-dimensionality-reduction` — [F6, C8] — PCA as projection, truncated SVD in practice, UMAP conceptually, when local vs global structure matters.
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
  subparts: {min: 33, max: 41}         # 2026: 37; 2025: >=39 visible
  five_point_atom_share: {min: 0.55}   # 2026: 24/37 = 0.65
  programming_points_share: {min: 0.45, max: 0.55}   # 2026: 150/300
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
topic_distribution:                    # POINTS per cluster (must sum to total_points),
                                       # tolerance ±20 pts per cluster; values = 2026 observed
  linear-algebra: 60
  ml-concepts: 50
  numpy: 55
  pytorch: 50
  applied-ml: 50
  cnn-vision: 10
  nlp-embeddings: 15
  probability-statistics: 5
  calculus-multivar: 5
  # sums to 300 exactly; points not shares — shares rounded to 2dp sum to 1.01 (checkable
  # integers beat drifting floats)
difficulty_mix:                        # by points, from analysis difficulty profile
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

**Steps:** write file → verify YAML parses + topic_distribution sums to 1.0 → commit.

---

### Task 3: docs/mocktest-generation.md (replace stub)

**Files:** Modify: `docs/mocktest-generation.md`

**Required sections:**
1. **Pipeline** — the five stages (blueprint → instantiate → draft → verify → gate) with concrete commands; until plan 004 ships `new-mocktest`, instantiation is manual: copy the documented directory skeleton + manifest template.
2. **Manifest schema** for `mocktests/r1-NNN/manifest.yaml`: test id, blueprint_version, generation date + parameters (section point allocations chosen, clusters rotated into the arc, difficulty draw), per-problem entries (id, section, units drawn on, concept tags, points, difficulty, provenance original/adapted-from, answer-key values for solution verification), time budget per section.
3. **Drafting rules** — problem specs from the blueprint section styles; solutions authored as executable notebooks with fixed seeds; datasets via seeded generation scripts; student/solution notebook separation (hygiene).
4. **Verification map** — which ci-local check covers which blueprint field (blueprint-check ↔ texture/sections/topic_distribution; overlap-scan ↔ provenance; prereq-check ↔ taught-closure; coverage/hygiene; all SKIP-LOUDLY until plan 004).
5. **Review duties pointer** — content-gate fidelity review compares against `reference/analysis.md ## Style notes`.

**Steps:** write → commit.

---

### Task 4: Cross-consistency verification + ship

- [ ] Scratchpad Python check (not shipped): parse syllabus.md's fenced YAML + blueprint.yaml; assert (a) unit DAG acyclic, all refs resolve; (b) every concept taught exactly once; (c) all baseline/taught concept ids unique; (d) every blueprint cluster reference exists in the syllabus cluster set; (e) topic_distribution points sum to exactly total_points; (f) section point mins ≤ maxes and min-sums ≤ 300 ≤ max-sums; (g) transitive prereq closure — for each unit, its teaches-set may only rely on baseline + union of ancestors' teaches (verified per the concepts-used lists that unit manifests will declare later; here assert edge sanity: C8 includes F3, C5 reaches F3 via C2, C6 reaches F1 via C1).
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

## Content Review

(Pre-PR gate findings land here.)
