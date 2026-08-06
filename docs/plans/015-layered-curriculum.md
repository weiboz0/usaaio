# Plan 015 — Layered Round 1 / Round 2 Curriculum Architecture

**Goal:** Turn the repository's strong 2026 Round-1-first course into one coherent,
machine-auditable USAAIO curriculum with two explicit exit paths: a Round 1 path and a
Round 2 extension path.
This plan inventories every official knowledge point and every shipped lesson/practice,
records its requirement class (`required`, `bridge`, or `optional`) separately from whether
the required theory, derivation, programming, and assessment depth exists,
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
   `https://www.usaaio.org/syllabus` (retrieved 2026-08-06).
2. The current competition page defines the round boundary:
   `https://www.usaaio.org/2027-usa-na-aio` (retrieved 2026-08-06).
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
| Neural-network losses and training | **Partial; completion required.** Manual forward propagation is covered; training is not. | Round 1 | Reuse the shipped forward-pass teaching, then add softmax, cross-entropy, backpropagation by hand, and a fully connected training loop from scratch. PyTorch autograd/optimizer use follows the manual derivation rather than substituting for it. |
| Batch normalization and dropout | **BatchNorm partial after Plan 014; dropout missing; both require completion.** | Round 1 | Give each honest concept ownership and at least three practices under the repository coverage rule; the existing BatchNorm controls clinic is useful theory evidence but does not cover derivation, implementation, or training. |
| Transformers and NLP beyond embeddings | **Current gap; required for Round 2.** | Round 2 extension | Attention, multi-head/self-attention, positional encoding, transformer architecture, complexity, from-scratch implementation, NLP transformers, pre-training/fine-tuning, and application bridges to vision transformers and graph neural networks. |
| Advanced vision and generative AI | **Current gap; required for Round 2.** | Round 2 extension | Object detection, UNet, autoencoders, VAE, GAN, DDPM, and Stable Diffusion, with prerequisite closure and both theory/programming. |
| GPU execution workflow | **Official Round 2 policy requirement.** | Round 2 capstone | Colab L4 setup, device movement, memory handling, and GPU training workflow. |
| Scientific/open-ended modeling | **Observed Round 2 capability, not a single official bullet.** | Round 2 capstone | Semi-supervised/pseudo-label learning, inverse problems, mixture/parameter regression, experiment design, and open-ended model evaluation, taught as integration rather than as an unstructured topic dump. |

## Task 0 — Reconcile the concurrent Plan 014 branch before execution

Plan 015 is drafted from `main` at `7c729c7`; Plan 014 is concurrently active and is not a
source of shipped facts.
Before implementing any Plan 015 task:

1. Wait for Plan 014 to merge or be explicitly abandoned, then rebase Plan 015 on the
   resulting `origin/main`.
2. Recompute unit/problem/hour counts from manifests; never carry the draft's 109 concepts,
   337 unit-practice problems, 47 lesson sessions, or 199 scheduled hours as constants.
3. Create `docs/audits/015-plan014-reconciliation.md` recording Plan 014's final commit
   **squash-merge commit on main** (or an explicit abandonment disposition), its delivered
   artifact counts, and the
   disposition of every overlapping topic.
   Audit the final diff against these reconciliation rules:
   - its synthesis work is complementary and may become evidence in this audit;
   - `softmax` and `cross-entropy-loss` transfer to the neural-training content tranche,
     not to Plan 015's architecture implementation;
   - if Plan 014 ships its short BatchNorm subsection/clinic under existing tags, record it
     as **partial evidence only**; it cannot make `batch-normalization` covered, and the
     neural-training content tranche still owns the real concept id and ≥3 practices;
   - Plan 014's historical "future-risk" wording does not control the new roadmap: Bayes,
     attention, KL, mixtures, and related families receive their official/observed status
     here without rewriting the already-reviewed Plan 014 record;
   - no content is counted as covered merely because it appears in plan prose.
4. `scope-check` validates that the reconciliation record exists, names a resolution state
   (`merged` or `abandoned`), and that a recorded Plan 014 squash commit is an ancestor of
   HEAD.
   `abandoned` requires the branch/PR reference, date, reason, and explicit owner decision;
   it does not make any proposed Plan 014 content evidence.
5. Append the reconciliation commit, final counts, and any changed ownership to this plan's
   post-execution report.

**Hard stop:** do not resolve a Plan 014 conflict by editing its active worktree or by
silently duplicating its files.
There is no time-based auto-abandonment: if Plan 014 remains active when execution reaches
this step, mark Plan 015 blocked and ask the owner to finish or explicitly abandon Plan 014.

## Task 1 — Freeze the source taxonomy and round boundary

### Files

- Create `curriculum/sources.yaml`.
- Create `curriculum/official-topics.yaml`.
- Add schema fixtures under `tests/fixtures/curriculum/`.

`curriculum/sources.yaml` records stable source ids, URL/local-path metadata, retrieval or
competition date, authority (`official-syllabus`, `official-round-policy`, `past-paper`,
`design-rationale`), a SHA-256 of a canonical JSON array containing only the manually
verified official heading/bullet paths used by the audit, the normalization method
(`official-topic-paths-v1`: Unicode NFC, whitespace collapse, source order), a mandatory
`review_after` date, and whether the supporting source is committed or local-only.
Only the short heading/bullet labels needed to reproduce the hash may be stored; do not copy
paragraph prose, examples, or past-problem text into this file.
The hash pins the dated snapshot used by this audit; CI does not claim that a live remote
page remains unchanged forever.
A later source refresh fetches the page explicitly, records a new dated source id/hash, and
re-adjudicates affected topics in a separate reviewed change.
`scope-check` fails after `review_after`, forcing a live source review at least once per
competition cycle rather than silently treating the snapshot as current forever.
The failure message names `curriculum/sources.yaml` and instructs the maintainer to open a
source-refresh change that repeats Task 1 and re-adjudicates affected rows; there is no
silent waiver for unrelated PRs.

`curriculum/official-topics.yaml` decomposes broad official bullets into atomic audit
targets without yet claiming coverage.
It first records the official category hierarchy and its round policy:

```yaml
categories:
  - id: machine-learning
    parent: null
    source_refs: [official-syllabus-2026-08-06, official-round-policy-2027-2026-08-06]
    required_for: [round-1, round-2]
  - id: supervised-learning
    parent: machine-learning
    source_refs: [official-syllabus-2026-08-06]
    required_for: [round-1, round-2]
  - id: deep-learning-foundation
    parent: null
    source_refs: [official-syllabus-2026-08-06, official-round-policy-2027-2026-08-06]
    required_for: [round-1, round-2]
  - id: transformers
    parent: null
    source_refs: [official-syllabus-2026-08-06, official-round-policy-2027-2026-08-06]
    required_for: [round-2]
```

Category ids correspond exactly to sibling headings on the official syllabus.
For example, `transformers` is not a child of `deep-learning-foundation` or `cnn-basics`.
Nested subcategories such as `supervised-learning` declare a `parent` edge and inherit every
round from the full category-ancestor chain; `scope-check` validates the category DAG before
validating atomic topics.
Every atomic entry then has:

```yaml
- id: ols-normal-equations-rank-and-pseudoinverse
  parent: supervised-learning
  source_refs: [official-syllabus-2026-08-06]
  required_for: [round-1, round-2]
  modalities: [theory, derivation]
```

Required fields are `id`, `parent`, `source_refs`, `required_for`, and `modalities`.
Allowed modalities are `theory`, `derivation`, `proof`, `implementation`, `model-training`,
and `competition-workflow`.
Atomic targets split only when the official expectation or prerequisite structure demands
distinct evidence; avoid turning every vocabulary word into a false standalone topic.

**Round rule:** an atomic topic inherits `required_for` from its exact parent category.
It may add a round supported by another source, but may never remove an inherited round.
Categories explicitly listed on the 2027 Round 1 page are required for both rounds;
the remaining sibling categories are Round-2 requirements.
Past-paper-only capabilities may be required for the corresponding round when their
repeated or integrative role justifies it; otherwise they are `bridge` or `optional`, never
quietly promoted to official status.

**Acceptance:** a reviewer can trace every bullet and every explicit example/expectation on
the official syllabus to one or more atomic ids, and every atomic id back to a hashed source
and exact parent category.

## Task 2 — Exhaustive shipped-material audit

### Files

- Create `tools/audit_curriculum.py` for inventory generation only.
- Create generated `docs/audits/015-coverage-audit.md` for the adjudicated findings.
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

For notebooks, record path, stable heading path plus cell ordinal, declared concept ids,
relevant API tokens, and problem identifiers.
The generator parses notebooks into an exact canonical semantic view.
For every cell, preserve only `cell_type`, Unicode-NFC/line-ending-normalized `source`, and
markdown attachment names plus byte hashes; ignore the notebook `metadata` object, cell
`metadata`, cell `id`, `execution_count`, and outputs entirely.
For YAML manifests, hash the complete parsed YAML object after recursive key sorting; no
field allowlist is used.
Heading paths recognize both ATX and Setext markdown headings after Unicode NFC
normalization.
Evidence anchors use `path + normalized heading path + cell ordinal within that heading`;
the human heading remains findable while the ordinal disambiguates repeated headings.
Input paths are sorted by POSIX relative-path bytes; parsed YAML is loaded with the
repository-pinned PyYAML version and emitted as canonical JSON with recursively sorted keys,
UTF-8, and fixed separators.
Do not infer semantic coverage from keyword presence.
`audit_curriculum.py` owns only `material-inventory.yaml`.
`render_curriculum_roadmap.py` is the sole writer of both generated Markdown documents.
The generated inventory supplies candidates; the audit report records a human judgment for
each official atomic target across its required modalities plus the overall practice rule:

| Dimension | Passing evidence |
|---|---|
| Theory | Definition, assumptions, interpretation, and boundary/counterexample where relevant. |
| Derivation | The requested calculation/result is derived, not merely stated or delegated to a library. |
| Proof | A validity, equivalence, bound, or counterexample claim is justified from stated assumptions. |
| Implementation | A student implements the core mechanism at the required abstraction level; black-box calls do not satisfy a from-scratch requirement. |
| Model training | A student executes and diagnoses the complete train/evaluate loop at the required manual or framework level. |
| Competition workflow | A student produces the required notebook/markdown/submission artifact under runtime, API, reproducibility, and evaluation constraints. |
| Practice/assessment | At least three honest unit practices for a taught concept, including the required answer forms/depth; mock-only exposure is not teaching coverage. |

Each audit row carries `requirement: required | bridge | optional`, independently carries
`coverage: covered | partial | missing`, and records exact lesson anchors, practice ids,
assessment ids, and a one-sentence consequence.
The human adjudication is stored once in `curriculum/coverage-map.yaml` (`rationale`,
`consequence`, typed evidence, and deficits); `docs/audits/015-coverage-audit.md` is generated
from that canonical data plus `material-inventory.yaml` and is never edited independently.
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
Record the exact count of notebooks/problems searched, the required/bridge/optional totals,
and the independent covered/partial/missing totals in the post-execution report.

## Task 3 — Add the machine-readable layered roadmap contract

### Files

- Create `curriculum/coverage-map.yaml`.
- Extend `tools/model.py` with roadmap dataclasses/loaders.
- Create `tools/checks/scope.py`.
- Create `tools/render_curriculum_roadmap.py`.
- Register `scope-check` in `tools/cli.py` and `scripts/ci-local.sh`.
- Add `tests/test_scope.py` and integration coverage in `tests/test_integration.py`.
- Extend `scripts/pre-merge-guard.sh --pr` to reject roadmap knowledge-point or planned-unit
  ownership collisions against the simulated `origin/main` union.

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
- id: ols-normal-equations-rank-and-pseudoinverse
  layer: round-1-core
  requirement: required
  coverage: partial
  source_refs: [official-syllabus-2026-08-06]
  depends_on: [matrix-multiplication, gradient]
  shipped_concepts: [linear-regression, mse-loss]
  evidence_by_modality:
    theory:
      lesson_anchors:
        - path: units/C2-linear-models/lessons/01-linear-regression-and-mse.ipynb
          heading: Linear regression
          cell_ordinal: 0
          role: primary
      practices:
        - {id: C2-p01, role: primary}
        - {id: C2-p02, role: primary}
        - {id: C2-p03, role: primary}
    derivation:
      lesson_anchors: []
      practices: []
  disposition: extend-existing-unit
  destination: C2-linear-models
  deficits:
    modalities_missing: [derivation]
  rationale: Current material teaches only the gradient view and explicitly omits normal equations.
```

Allowed `requirement` values are `required`, `bridge`, and `optional`.
Allowed `coverage` values are `covered`, `partial`, and `missing`.
Allowed dispositions are `keep`, `extend-existing-unit`, `new-unit`, and `defer-optional`.
`roadmap_version` is `1`; `scope-check` rejects unsupported versions.
Increment it only for a backward-incompatible schema change, not for ordinary coverage
updates.

`planned_units` assigns stable provisional ids, titles, layers, prerequisites, owned
knowledge points, provisional concept ids, a non-negative estimated hour **range** with
`max >= min`, and `schedule_action: split | replace | extend` for every Round-1 addition to
the current zero-slack calendar.
These ids are roadmap ids only; they do not enter `syllabus.md` or reserve future plan
numbers until a content plan actually branches and passes the collision guard.

`scope-check` fails on:

1. missing or duplicate official atomic targets;
2. unknown source, concept, layer, dependency, destination-unit, or evidence references;
3. a category cycle, unknown category parent, or category/topic whose `required_for` removes
   a round inherited from its full ancestor chain;
4. a Round-1-required point assigned to `round-2-extension`/`optional-enrichment`, owned by
   a Round-2 unit, or depending on Round-2-only material;
5. an official required point with `requirement: optional`, or any row using the removed
   `coverage: optional` value;
6. a dependency cycle;
7. `covered` without typed, existing inventory anchors and at least one distinct shipped
   unit-practice id for **each** required modality, or without at least three distinct
   shipped unit-practice ids in the union; mechanically, every cited practice's manifest
   concept tags must intersect `shipped_concepts`, and every lesson anchor must be under a
   unit whose `teaches` set intersects `shipped_concepts`; each accepted evidence record
   must declare `role: primary`, with the gate manually verifying that judgment row by row;
8. `covered` concepts that are absent from the shipped `syllabus.md` contract;
9. any violation of this exhaustive, checker-derived state rule:
   - `covered`: every required modality has accepted primary evidence and the union contains
     at least three distinct qualifying unit-practice ids;
   - `missing`: no required modality has accepted primary evidence and there are zero
     qualifying practice ids;
   - `partial`: every other combination, including taught-without-practice,
     practice-without-teaching, or only some modalities/depths covered;
   `modalities_missing` must exactly equal the required modalities lacking accepted evidence,
   while practice shortfall is computed as `max(0, 3 - distinct_qualifying_practices)` and
   is not a self-reported field;
10. `partial`/`missing` entries with no destination;
11. a planned unit's provisional concept id appearing in current `syllabus.md` or unit
    `teaches` lists before its teaching and ≥3 practices ship;
12. any knowledge point with zero or multiple destination owners across both existing-unit
    extensions and planned units;
13. a missing/invalid Plan 014 reconciliation record;
14. an invalid planned-unit hour range or a Round-1 addition without `schedule_action`.

Every failure mode gets a deliberately broken fixture proving a nonzero result, including
unrelated-but-valid lesson/practice references, an R1 target placed in an R2 unit, and a
`partial` row with an empty deficit set.
`scope-check` reports gaps but treats an acknowledged `partial` or `missing` roadmap entry as
schema-valid; the purpose is to make debt explicit, not to block all work until the entire
multi-semester curriculum exists.
The checker proves referential and modality completeness, not semantic truth; the gate's
row-by-row curriculum review remains responsible for whether an anchor honestly supports
the claimed knowledge point.
Semantic duplication cannot be proved from ids alone, so the curriculum review separately
checks that a Round 2 unit depends on shipped/shared teaching instead of rewriting it.

`audit_curriculum.py --check` regenerates the normalized material inventory in memory and
fails on a diff.
`render_curriculum_roadmap.py --check` does the same for both generated documents:
`docs/audits/015-coverage-audit.md` and `docs/curriculum-roadmap.md`.
Both commands are wired into `ci-local.sh`, so generated inventory, audit, and roadmap
evidence cannot go stale.
Normalization fixtures perturb every ignored notebook field and must leave the inventory
unchanged; changing cell source, attachment bytes, or any parsed manifest value must make
`--check` fail.
All input-order permutations must render identical bytes.
The merge gate is conjunctive: `scope-check` can validate an evidence reference while
`ci-local.sh` independently executes its solution notebook; either failure blocks merge.

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
- `docs/course-structure.md` labels the existing 26-week calendar using its recomputed
  post-Plan-014 hour total as the currently shipped R1-first schedule and does not imply
  that the planned extensions fit into its zero slack;
- `TODO.md` no longer says Plan 010 made the curriculum complete or Plan 012 made the
  roadmap complete;
- generated roadmap tables show R1 and R2 exits, current status, destination, prerequisites,
  modality gaps, and estimated hours without presenting estimates as manifested time.

**Capacity rule:** Plan 015 may estimate ranges, but no follow-on content plan may append
material to a full unit or the zero-slack 26-week calendar without an explicit split,
replacement, or schedule extension.
The generated roadmap recomputes the post-Plan-014 manifested/scheduled baseline from
manifests and `docs/course-structure.md`, sums ranges per layer, and reports the delta from
that recomputed value; it never carries the draft's 199-hour figure as a constant.
It does not reject expansion when `schedule_action: extend` makes that choice explicit.
The 16–24 practice band and ≥3-per-concept rule remain binding.

## Task 5 — Publish the dependency-ordered content tranches

The audit report and roadmap end with this ordered queue.
Do not reserve plan numbers in advance; the next plan takes the next free number after
running the collision guard.

1. **Round 1 foundation, workflow, and mathematical completion:** first close F1 seaborn
   and C10 Colab/Markdown/round-policy gaps; then add conditional probability, Bayes,
   Hoeffding, the closed-form linear-regression estimator with rank/pseudoinverse conditions,
   the PCA eigenproblem and NumPy class, PSD/kernel proofs, convexity, constrained
   optimization, and duality.
2. **Round 1 neural-training completion:** reuse the shipped manual forward-propagation
   prerequisite, then add softmax, cross-entropy, manual backpropagation, a trained fully
   connected network from scratch, complete C6 model training through PyTorch
   autograd/optimizers, and add C7 CNN training; BatchNorm and dropout receive explicit
   concept ownership and practice.
3. **Round 1 classical-model breadth:** logistic regression, SVM, decision trees,
   ensembles, and k-means, with comparison and implementation exercises.
4. **Round 2 transformers and NLP:** self/multi-head attention, positional encoding,
   transformer architecture and complexity, from-scratch attention,
   LayerNorm/residual/feed-forward block structure, C8 word-embedding training, NLP
   applications, pre-training, and fine-tuning, followed by vision-transformer and graph
   neural-network applications.
5. **Round 2 advanced vision and generative modeling:** object detection, UNet,
   autoencoders/VAE, GAN, DDPM, and Stable Diffusion; multivariate Gaussian,
   reparameterization, and KL are taught before their consumers.
6. **Round 2 open-ended/GPU capstone:** semi-supervised/pseudo-label image learning,
   inverse problems, mixture-parameter estimation, experiment design, reproducibility, GPU
   workflow, and model evaluation.

Each future tranche must read the final Plan 015 coverage rows, own a closed prerequisite
slice, update both the shipped syllabus and roadmap atomically, add ≥3 honest practices per
new concept, and leave `scope-check` with fewer required partial/missing modalities.
It must not improve its numbers by merging distinct concepts into a vague tag.

## Task 6 — Verification (NAMED; docs + tooling, no teaching-content claim)

Run, in order:

```bash
uv run pytest tests/test_audit_curriculum.py tests/test_scope.py \
  tests/test_model.py tests/test_prereq_coverage.py tests/test_integration.py -q
uv run python tools/audit_curriculum.py --check
uv run python tools/render_curriculum_roadmap.py --check
uv run usaaio-tools scope-check
uv run usaaio-tools prereq-check
uv run usaaio-tools coverage-check
bash scripts/ci-local.sh
git diff --check
```

Acceptance requires:

- all roadmap/schema negative fixtures fail for the intended reason;
- the inventory generator is deterministic over its documented normalized semantic view;
- CI freshness checks fail after a source notebook/manifest or roadmap mutation until the
  corresponding generated artifact is refreshed;
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
the existing `ci-local.sh` contract; that command still executes all existing solution
notebooks unchanged.

## Task 7 — Review and ship

1. Run the mandatory 4-way plan-review gate before implementation; do not begin Task 0 or
   later until all four verdicts are `APPROVE` or `APPROVE WITH NITS` with no open blocker.
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
   Immediately before merge, fetch `origin/main`, require the branch merge-base to equal
   that fresh base (GitHub's up-to-date-branch requirement), rerun the guard, and record the
   checked base SHA.
   If the base moves before merge or GitHub reports the branch stale, rebase and repeat the
   guard/review-sensitive checks; the local guard narrows the race but does not claim to
   replace server-side up-to-date enforcement.

## Out of scope

- Authoring or modifying lesson, practice, solution, review, synthesis, or mock-test
  notebooks.
- Adding planned concepts/units to the shipped `syllabus.md` YAML before their content
  exists.
- Generating a Round 2 mock blueprint or mock test.
- Promising that the recomputed current schedule can absorb the gaps without a capacity
  tradeoff.
- Making Student's t-tests, importance sampling, or other adjacent topics required without
  new evidence and a recorded scope decision.
- Reserving future plan numbers.

## Plan Review

### Round 1 — 2026-08-05 — **REJECT (resolved in Rounds 2–3 below)**

- **[claude-self] REJECT.** The first draft did not define a canonical notebook anchor,
  could not distinguish provisional concepts from partial coverage of shipped concepts, and
  did not enforce source freshness or exact round inheritance.
  Fixed by normalized semantic inventory, typed modality evidence/deficits, explicit
  category inheritance, source hashes, and generated-artifact freshness checks.
- **[codex] REJECT.** Blockers: generic evidence could self-attest `covered`; R1-required
  topics could be placed in R2; Plan 014's BatchNorm reconciliation was impossible after
  merge under Plan 015's no-notebook scope.
  Fixed by typed per-modality anchors + three distinct unit practices, layer/owner
  consistency checks, and treating Plan 014's BN clinic as partial evidence whose actual
  concept/practice completion remains with the neural-training tranche.
- **[fable] REJECT** (temporary independent GPT-5.6-sol replacement).
  Independently confirmed the same three blockers and added stale generated inventory/
  roadmap risk.
  Fixed by `audit_curriculum.py --check` and `render_curriculum_roadmap.py --check` in CI.
- **[glm] REJECT.** Valid blockers: reconciliation closure was unrecorded, partial rows
  could carry empty deficits, notebook normalization/anchors and source hashes were
  unspecified, and future roadmap ownership lacked merge-union protection.
  Fixed with a reconciliation artifact/ancestor check, exact deficit invariants,
  normalization/anchors/hashes, and an extended pre-merge guard.
  Its claim that transformer topics sit inside a Round-1 category was factually rejected:
  the official page presents `Transformers` as a sibling syllabus category; the revised
  hierarchy now makes that distinction machine-readable.

### Rounds 2–3 — 2026-08-05 — **PASS (4/4)**

- **[claude-self] APPROVE.** Rechecked the final category DAG, typed/primary evidence,
  exhaustive checker-derived coverage states, generated-document ownership/freshness,
  dynamic schedule baseline, and Plan 014 boundary; no open blocker.
- **[codex] REJECT → APPROVE.** Its second-round unrelated-evidence predicate and
  third-round incomplete coverage-state cross-product were fixed.
  Final re-verdict: no remaining findings.
- **[fable] REJECT → APPROVE WITH NITS** (temporary independent GPT-5.6-sol replacement).
  Its category-parent, generated-audit freshness, and `uv` command blockers were fixed;
  final schedule-label nit was fixed by removing the last hard-coded baseline.
- **[glm] REJECT → APPROVE.** Two adversarial rounds drove source/category normalization,
  evidence/state invariants, ownership/collision handling, source-review expiry, and
  deterministic generation.
  Final friendly re-verdict had only documentation nits: all modality evidence shapes and a
  single audit-document generator are now explicit; the refresh remediation and existing
  notebook-execution behavior are clarified.

**GATE RESULT: PASS — 4/4.** At gate time implementation remained blocked on Task 0 until
Plan 014 was merged or explicitly abandoned. Execution update, 2026-08-06: Plan 014 merged
at the squash commit recorded in `docs/audits/015-plan014-reconciliation.md`; the block is
resolved and the post-014 baseline was recomputed before implementation.

## Post-Execution Report

Not started.
