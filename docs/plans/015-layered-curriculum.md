# Plan 015 — Layered Round 1 / Round 2 Curriculum Architecture

**Goal:** Turn the repository's strong 2026 Round-1-first course into one coherent,
machine-auditable USAAIO curriculum with two explicit exit paths: a Round 1 path and a
Round 2 extension path.
This plan inventories every official knowledge point and every shipped lesson/practice,
records whether the required theory, derivation, programming, and assessment depth exists,
and publishes the dependency-ordered content backlog.
It does **not** claim that planned topics are already taught and does **not** ship teaching
notebooks itself.

**Architecture decision:** use a single curriculum graph and shared set of materials, with
an explicit Round 1 stopping point and separately scheduled Round 2 extension units.
Do not maintain duplicate "R1" and "R2" versions of the same foundation lesson.
Round 2 units depend on the shared/R1 units and add only the new depth or topic family.

The current `syllabus.md` canonical YAML remains the executable **shipped-content
contract** consumed by `prereq-check` and `coverage-check`.
A new roadmap contract records required but unshipped knowledge points.
This separation is essential: adding a future concept to the current `concepts:` list would
correctly make CI demand an owning unit and at least three shipped practice problems.

## Decision hierarchy

Plan 015 applies this authority order when sources disagree or differ in granularity:

1. The current official syllabus defines required subject matter:
   `https://www.usaaio.org/syllabus` (retrieved 2026-08-05).
2. The current competition page defines the round boundary:
   `https://www.usaaio.org/2027-usa-na-aio` (retrieved 2026-08-05).
   Round 1 covers the named foundation/basic-coding/ML/PyTorch/deep-learning/CNN
   categories; Round 2 covers everything on the syllabus and may require GPUs.
3. Past papers and their rationale define observed depth and task texture, not the complete
   syllabus.
   Use the committed paraphrase in `reference/analysis.md` plus the local, gitignored
   `reference/r1-2026/index.yaml` and `reference/r2-2026/index.yaml` when present.
4. A pedagogical bridge may be added when it is prerequisite closure for a required topic.
   Bridges are labelled as such; they are not misreported as official syllabus bullets.
5. Optional enrichment stays optional.
   Adjacency to a required topic is not by itself a reason to make a topic required.

No raw past-paper text, raw source HTML, or student data is committed.
Committed evidence is paraphrase, source metadata, and file/problem identifiers only.

## Preliminary audit decisions this plan must preserve

These are scope decisions, not claims that the content has shipped.
The exhaustive audit may refine placement and prerequisites but may not silently reverse a
`required` decision that follows directly from the official syllabus.

| Question / knowledge family | Decision | Round / layer | Required completion |
|---|---|---|---|
| We teach a Gaussian distribution; should we also teach Student's t / a t-test? | **No, not as a required companion.** A Gaussian lesson needs conditional probability, Bayes' rule where used, and estimator/sampling distinctions; Student's t and hypothesis testing form a separate statistical-inference extension. | Optional enrichment | Record as optional; promote only if a later official source, paper, or chosen inference track needs it. |
| We teach linear regression; do we have the closed-form derivation? | **Current gap; required.** The official syllabus explicitly expects derivation of an estimator. | Round 1 | Derive normal equations from MSE, state rank/identifiability conditions, solve the full-column-rank case, explain pseudoinverse behavior, and compare the closed form with gradient descent. |
| Is importance sampling necessary? | **No current evidence makes it necessary.** It is neither an official named topic nor needed by the indexed 2026 R1/R2 arcs. | Optional enrichment | Keep out of required scope unless a later Monte Carlo, probabilistic-modeling, or official assessment dependency appears. |
| Markdown/Colab and the basic library surface | **Partial; audit explicitly.** | Round 1 | Verify markdown math/code communication and every named library. Add an honest seaborn target if it is absent; a matplotlib lesson does not cover seaborn by implication. |
| Affine transformations | **Potentially partial; audit separately from linear maps.** | Round 1 shared foundation | Cover the translation term, homogeneous-coordinate viewpoint where useful, composition, and the distinction between linear and affine maps. |
| Probability/statistics around the current F5 | **Partial; required expansion.** | Round 1 shared foundation, plus R2 bridge depth | R1: conditional probability, Bayes' rule, Hoeffding's inequality. R2 bridge: multivariate Gaussian/reparameterization and KL divergence where VAE/diffusion consumes them. Keep likelihood/MLE only where estimator derivations require it. |
| PCA after SVD | **Partial; required expansion.** | Round 1 | Derive the centered-covariance eigenproblem, connect it to SVD, implement a PCA class with NumPy, and test reconstruction/explained variance without black-box sklearn PCA. |
| Kernels / positive semidefiniteness | **Current gap; required.** | Round 1 mathematical foundation / SVM bridge | Teach PSD matrices, kernel validity, and at least one proof/counterexample workflow; incidental PSD language in another unit does not count. |
| Convex optimization | **Partial; required expansion.** | Round 1 | Convex sets/functions, first-order optimality, constrained formulation, Lagrangian intuition, and duality at the depth needed for linear/logistic models and SVM. |
| Classical ML breadth | **Current gap beyond kNN/linear regression.** | Round 1 | Logistic regression, SVM, decision trees, ensemble learning, and k-means, each with theory/programming and comparison boundaries. |
| Neural-network losses and training | **Current gap; required.** | Round 1 | Softmax, cross-entropy, forward propagation, backpropagation by hand, and a fully connected network from scratch. PyTorch autograd/optimizer use is taught only after the manual derivation, not used as a substitute for it. |
| Batch normalization and dropout | **Current gap as standalone knowledge points; required.** | Round 1 | Give each honest concept ownership and at least three practices under the repository coverage rule; do not assess BatchNorm behavior only under `layer-freezing` or `resnet-architecture` tags. |
| Transformers and NLP beyond embeddings | **Current gap; required for Round 2.** | Round 2 extension | Attention, multi-head/self-attention, positional encoding, transformer architecture, complexity, from-scratch implementation, NLP transformers, pre-training/fine-tuning, and application bridges to vision transformers and graph neural networks. |
| Advanced vision and generative AI | **Current gap; required for Round 2.** | Round 2 extension | Object detection, UNet, autoencoders, VAE, GAN, DDPM, and Stable Diffusion, with prerequisite closure and both theory/programming. |
| Scientific/open-ended modeling | **Observed Round 2 capability, not a single official bullet.** | Round 2 capstone | GPU workflow, inverse problems, mixture/parameter regression, experiment design, and open-ended model evaluation, taught as integration rather than as an unstructured topic dump. |

## Task 0 — Reconcile the concurrent Plan 014 branch before execution

Plan 015 is drafted from `main` at `7c729c7`; Plan 014 is concurrently active and is not a
source of shipped facts.
Before implementing any Plan 015 task:

1. Wait for Plan 014 to merge or be explicitly abandoned, then rebase Plan 015 on the
   resulting `origin/main`.
2. Recompute unit/problem/hour counts from manifests; never carry the draft's 109 concepts,
   337 unit-practice problems, 47 lesson sessions, or 199 scheduled hours as constants.
3. Audit Plan 014's final diff against these reconciliation rules:
   - its synthesis work is complementary and may become evidence in this audit;
   - `softmax` and `cross-entropy-loss` transfer to the neural-training content tranche,
     not to Plan 015's architecture implementation;
   - any graded BatchNorm behavior either receives a real concept id, honest teaching, and
     at least three practices, or is removed/deferred from Plan 014;
   - statements that Bayes, attention, KL, mixtures, or related R2 families are merely a
     future-risk watch-list are corrected: they are confirmed official/observed gaps, even
     when deferred for capacity;
   - no content is counted as covered merely because it appears in plan prose.
4. Append the reconciliation commit, final counts, and any changed ownership to this plan's
   post-execution report.

**Hard stop:** do not resolve a Plan 014 conflict by editing its active worktree or by
silently duplicating its files.

## Task 1 — Freeze the source taxonomy and round boundary

### Files

- Create `curriculum/sources.yaml`.
- Create `curriculum/official-topics.yaml`.
- Add schema fixtures under `tests/fixtures/curriculum/`.

`curriculum/sources.yaml` records stable source ids, URL/local-path metadata, retrieval or
competition date, authority (`official-syllabus`, `official-round-policy`, `past-paper`,
`design-rationale`), and whether the source is committed or local-only.
Do not copy source prose into this file.

`curriculum/official-topics.yaml` decomposes broad official bullets into atomic audit
targets without yet claiming coverage.
Every entry has:

```yaml
- id: linear-regression-estimator-derivation
  parent: supervised-learning
  source_refs: [official-syllabus-2026-08-05]
  required_for: [round-1, round-2]
  modalities: [theory, derivation]
```

Required fields are `id`, `parent`, `source_refs`, `required_for`, and `modalities`.
Allowed modalities are `theory`, `derivation`, `proof`, `implementation`, `model-training`,
and `competition-workflow`.
Atomic targets split only when the official expectation or prerequisite structure demands
distinct evidence; avoid turning every vocabulary word into a false standalone topic.

**Round rule:** a topic in a category explicitly listed for 2027 Round 1 is required for
both rounds.
The remaining official categories are Round-2 requirements.
Past-paper-only capabilities may be required for the corresponding round when their
repeated or integrative role justifies it; otherwise they are `bridge` or `optional`, never
quietly promoted to official status.

**Acceptance:** a reviewer can trace every bullet and every explicit example/expectation on
the official syllabus to one or more atomic ids, and every atomic id back to a source.

## Task 2 — Exhaustive shipped-material audit

### Files

- Create `tools/audit_curriculum.py` for inventory generation only.
- Create `docs/audits/015-coverage-audit.md` for the adjudicated findings.
- Create `curriculum/material-inventory.yaml` as generated, deterministic evidence.
- Add `tests/test_audit_curriculum.py`.

The inventory generator reads all current producers, not just concept tags:

- the canonical YAML in `syllabus.md`;
- every `units/*/manifest.yaml`;
- every unit overview, lesson-session, review, practice-statement, and practice-solution
  notebook;
- synthesis materials if Plan 014 ships them;
- every shipped mock manifest and its statement/solution notebooks;
- `docs/course-structure.md` for delivery-hour claims.

For notebooks, record path, cell/heading anchors, declared concept ids, relevant API tokens,
and problem identifiers.
Do not infer semantic coverage from keyword presence.
The generated inventory supplies candidates; the audit report records a human judgment for
each official atomic target across four independent dimensions:

| Dimension | Passing evidence |
|---|---|
| Theory | Definition, assumptions, interpretation, and boundary/counterexample where relevant. |
| Derivation/proof | The requested result is derived or proved, not merely stated or delegated to a library. |
| Programming | A student implements the core mechanism at the required abstraction level; black-box calls do not satisfy a from-scratch requirement. |
| Practice/assessment | At least three honest unit practices for a taught concept, including the required answer forms/depth; mock-only exposure is not teaching coverage. |

Each audit row carries `coverage: covered | partial | missing | optional`, exact lesson
anchors, practice ids, assessment ids, and a one-sentence consequence.
`covered` requires evidence in every modality required by the atomic target.
A nearby topic, a mention in a "Going deeper" section, a plan claim, or an unrelated concept
tag is insufficient.

Explicitly audit the examples that motivated this plan:

- F5: Gaussian vs conditional probability/Bayes/Hoeffding/estimation/t-distribution;
- C2: gradient view vs normal equations/OLS estimator/pseudoinverse conditions;
- F6/C9: SVD-only PCA vs covariance/eigenproblem derivation/from-scratch PCA;
- F6/classical ML: incidental PSD vs kernel-validity proof;
- C3/C5/C6: linear-model updates vs neural backprop/autograd/optimizer training;
- C7: BatchNorm mention/clinic vs a genuinely taught and practised concept;
- all official ML, transformer, NLP, vision, and generative families;
- importance sampling as an optional candidate, not a presumed gap.

The audit is exhaustive at the **atomic-target** level and corpus-wide at the evidence-search
level.
Record the exact count of notebooks/problems searched and the final covered/partial/missing/
optional totals in the post-execution report.

## Task 3 — Add the machine-readable layered roadmap contract

### Files

- Create `curriculum/coverage-map.yaml`.
- Extend `tools/model.py` with roadmap dataclasses/loaders.
- Create `tools/checks/scope.py`.
- Register `scope-check` in `tools/cli.py` and `scripts/ci-local.sh`.
- Add `tests/test_scope.py` and integration coverage in `tests/test_integration.py`.

The coverage map is the canonical planning contract, separate from the shipped syllabus.
Its top-level keys are `roadmap_version`, `layers`, `planned_units`, and
`knowledge_points`.

Layers are fixed to:

- `shared-foundation` — prerequisites used across the program;
- `round-1-core` — material needed before the Round 1 exit gate;
- `round-2-extension` — material added after the Round 1 gate;
- `optional-enrichment` — coherent but non-required material.

Each knowledge point records:

```yaml
- id: linear-regression-estimator-derivation
  layer: round-1-core
  requirement: required
  coverage: partial
  source_refs: [official-syllabus-2026-08-05]
  depends_on: [matrix-multiplication, gradient]
  shipped_concepts: [linear-regression, mse-loss]
  evidence:
    lessons: [units/C2-linear-models/lessons/01-linear-regression-and-mse.ipynb]
    practice_ids: []
    assessment_ids: []
  disposition: extend-existing-unit
  destination: C2-linear-models
  modalities_missing: [derivation]
  rationale: Current material teaches only the gradient view and explicitly omits normal equations.
```

Allowed `requirement` values are `required`, `bridge`, and `optional`.
Allowed `coverage` values are `covered`, `partial`, `missing`, and `optional`.
Allowed dispositions are `keep`, `extend-existing-unit`, `new-unit`, and `defer-optional`.

`planned_units` assigns stable provisional ids, titles, layers, prerequisites, owned
knowledge points, and an estimated hour **range**.
These ids are roadmap ids only; they do not enter `syllabus.md` or reserve future plan
numbers until a content plan actually branches and passes the collision guard.

`scope-check` fails on:

1. missing or duplicate official atomic targets;
2. unknown source, concept, layer, dependency, destination-unit, or evidence references;
3. a dependency cycle or a Round 1 point that depends on Round-2-only material;
4. an official required point labelled optional/deferred;
5. `covered` without every required modality and without shipped lesson/practice evidence;
6. `covered` concepts that are absent from the shipped `syllabus.md` contract;
7. `partial`/`missing` entries with no destination and missing-modality declaration;
8. planned concepts leaking into current `syllabus.md` or unit `teaches` lists before their
   teaching content and ≥3 practices ship;
9. two planned units claiming ownership of the same knowledge point.

Every failure mode gets a deliberately broken fixture proving a nonzero result.
`scope-check` reports gaps but treats an acknowledged `partial` or `missing` roadmap entry as
schema-valid; the purpose is to make debt explicit, not to block all work until the entire
multi-semester curriculum exists.
Semantic duplication cannot be proved from ids alone, so the curriculum review separately
checks that a Round 2 unit depends on shipped/shared teaching instead of rewriting it.

## Task 4 — Publish the student path and correct completion claims

### Files

- Create `docs/curriculum-architecture.md`.
- Create generated `docs/curriculum-roadmap.md` from `curriculum/coverage-map.yaml`.
- Update narrative text in `syllabus.md`; do not change its canonical concepts/units in
  this plan.
- Update `docs/course-structure.md`.
- Update `docs/unit-standards.md` only for layered-course applicability and any stale
  coverage wording not already corrected by Plan 014.
- Update `TODO.md` only at ship time.

`docs/curriculum-architecture.md` states the student-facing design:

```text
shared foundation -> Round 1 core -> R1 exit assessment
                            |
                            +-> Round 2 extension -> R2 capstone / GPU practice
```

The Round 1 exit path contains every topic officially assigned to Round 1, not merely topics
observed in the single fully indexed 2026 paper.
The Round 2 path reuses that foundation and adds the remaining official syllabus plus
observed R2 integration depth.
Students never need two versions of probability, linear algebra, or PyTorch fundamentals.

Correct the current prose so that:

- `syllabus.md` calls its YAML the shipped-content contract, not the complete official
  syllabus;
- `docs/course-structure.md` labels the existing 26-week/199-hour calendar as the currently
  shipped R1-first schedule and does not imply that the planned extensions fit into its zero
  slack;
- `TODO.md` no longer says Plan 010 made the curriculum complete or Plan 012 made the
  roadmap complete;
- generated roadmap tables show R1 and R2 exits, current status, destination, prerequisites,
  modality gaps, and estimated hours without presenting estimates as manifested time.

**Capacity rule:** Plan 015 may estimate ranges, but no follow-on content plan may append
material to a full unit or the zero-slack 26-week calendar without an explicit split,
replacement, or schedule extension.
The 16–24 practice band and ≥3-per-concept rule remain binding.

## Task 5 — Publish the dependency-ordered content tranches

The audit report and roadmap end with this ordered queue.
Do not reserve plan numbers in advance; the next plan takes the next free number after
running the collision guard.

1. **Round 1 mathematical completion:** conditional probability, Bayes, Hoeffding,
   closed-form linear-regression estimator, rank/pseudoinverse conditions, PCA eigenproblem
   and NumPy class, PSD/kernel proofs, convexity, constrained optimization, and duality.
2. **Round 1 neural-training completion:** softmax, cross-entropy, manual forward/backward
   propagation, fully connected network from scratch, then PyTorch autograd/optimizers;
   BatchNorm and dropout receive explicit concept ownership and practice.
3. **Round 1 classical-model breadth:** logistic regression, SVM, decision trees,
   ensembles, and k-means, with comparison and implementation exercises.
4. **Round 2 transformers and NLP:** self/multi-head attention, positional encoding,
   transformer architecture and complexity, from-scratch attention, NLP applications,
   pre-training, and fine-tuning.
5. **Round 2 advanced vision and generative modeling:** object detection, UNet,
   autoencoders/VAE, GAN, DDPM, and Stable Diffusion; multivariate Gaussian,
   reparameterization, and KL are taught before their consumers.
6. **Round 2 open-ended/GPU capstone:** inverse problems, image tasks, mixture-parameter
   estimation, experiment design, reproducibility, GPU workflow, and model evaluation.

Each future tranche must read the final Plan 015 coverage rows, own a closed prerequisite
slice, update both the shipped syllabus and roadmap atomically, add ≥3 honest practices per
new concept, and leave `scope-check` with fewer required partial/missing modalities.
It must not improve its numbers by merging distinct concepts into a vague tag.

## Task 6 — Verification (NAMED; docs + tooling, no teaching-content claim)

Run, in order:

```bash
python -m pytest tests/test_audit_curriculum.py tests/test_scope.py \
  tests/test_model.py tests/test_prereq_coverage.py tests/test_integration.py -q
python -m tools.cli scope-check
python -m tools.cli prereq-check
python -m tools.cli coverage-check
bash scripts/ci-local.sh
git diff --check
```

Acceptance requires:

- all roadmap/schema negative fixtures fail for the intended reason;
- the inventory generator is deterministic (`generate`, copy/hash, regenerate, compare);
- every official topic has a disposition and round assignment;
- every `covered` claim has exact shipped evidence and all required modalities;
- manual spot checks cover every `covered` row and every `partial` row, not a percentage
  sample;
- current prerequisite and ≥3-practice contracts remain green;
- the baseline overlap-scan may be reported separately as unavailable only when the local
  reference corpus is absent; in the execution worktree, copy/fetch is not substituted for
  evidence without recording which corpus was actually available;
- the existing 2026 R2 index is treated as light evidence and never generalized into a
  complete R2 syllabus by itself.

Because this plan changes tooling and curriculum-governance documentation but ships no
units, practices, or mock tests, no solution-notebook execution is newly required beyond
the existing `ci-local.sh` contract.

## Task 7 — Review and ship

1. Run the mandatory 4-way plan-review gate before implementation.
2. After implementation, run a 4-way review with two explicit scopes:
   - schema/tooling anti-vacuity and producer-to-consumer coverage;
   - curriculum judgments, round assignments, prerequisite systematics, and evidence
     accuracy.
3. Reviewers independently adjudicate at least the preliminary-decision rows above and
   reject unsupported `covered` claims.
4. Record source retrieval dates, final corpus counts, gap totals, Plan 014 reconciliation,
   verification output, and all review verdicts in the post-execution report.
5. Update `TODO.md`, open the PR, run `scripts/pre-merge-guard.sh --pr`, and squash-merge
   only with all gates green.

## Out of scope

- Authoring or modifying lesson, practice, solution, review, synthesis, or mock-test
  notebooks.
- Adding planned concepts/units to the shipped `syllabus.md` YAML before their content
  exists.
- Generating a Round 2 mock blueprint or mock test.
- Promising that the present 199-hour schedule can absorb the gaps without a capacity
  tradeoff.
- Making Student's t-tests, importance sampling, or other adjacent topics required without
  new evidence and a recorded scope decision.
- Reserving future plan numbers.

## Plan Review

**Status:** draft; 4-way gate not yet run.

## Post-Execution Report

Not started.
