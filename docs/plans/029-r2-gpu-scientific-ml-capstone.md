# Plan 029 — Round 2 GPU Scientific Modeling Capstone

## Goal

Ship `book2:B2-024-gpu-scientific-ml-capstone` as the final, double-length Round 2 teaching unit.
It closes `gpu-colab-l4-workflow`, `open-ended-experiment-design`, `open-ended-model-evaluation`, `semi-supervised-pseudo-labeling`, `scientific-ml-inverse-problems`, and `mixture-parameter-regression` in every modality each coverage-map row requires.
It also adds the `optional-colab-l4` compute policy that Design 019 defines but the tooling does not yet accept.

## Branch and baseline

- Branch: `feature/plan-029-gpu-scientific-ml-capstone`.
- Baseline: `main` after Plan 028 (B2-023) merges; this branch merges that `main` before Task 1 starts.
- Book 1 is an imported prerequisite only; no Book 1 file changes.
- Roster: 3-way (`[self]` / `[sol]` / `[fable]`) per `AGENTS.md`.

## Scope and curricular boundary

The canonical owner is the existing roadmap row `B2-024-gpu-scientific-ml-capstone`.
The unit is the Round 2 open-ended capstone.
The reference analysis (`book2/reference/analysis.md`) records that open-ended model building carries 160/300 points in Round 2 2026, across an inverse problem, image-shape classification, and mixture-function parameter regression.
This unit teaches the workflow and the three task families with original problems.
It contains no past-paper text and no paraphrase close enough to identify a past problem, and every task carries its own data generator.

**Compute contract.** Design 019 (`docs/designs/019-r2-book-architecture.md`, "Compute contract") defines three policies: `cpu`, `optional-colab-l4`, and `gpu-required`.
This unit uses `cpu` and `optional-colab-l4` only, never `gpu-required`.
An `optional-colab-l4` practice has:

- a device-agnostic solution that CI executes on CPU within 20 s (the local correctness path);
- a statement section headed `Accelerator extension` that gives the larger Colab L4 configuration (data size, model width, steps) and what to observe.

CI never runs the accelerator extension.
The lessons teach the GPU branch with code guarded by `torch.cuda.is_available()`, so every lesson executes on CPU, and say explicitly which outputs only appear on a GPU.

**Real pretrained pipelines.** Design 019 states "No required lesson depends on opaque pretrained-weight downloads."
Running a real latent-diffusion pipeline on a Colab L4 (the hand-off promised in Plan 028) therefore appears only as Session 1's forward-only "going deeper" topic.
That topic is a markdown-only guide: no executed code, not assessed, and no download in CI.

All data is literal or produced by committed, seeded generators.
No web download, torchvision dataset, pretrained model, opaque checkpoint, or student data is allowed.
No solution needs a sandbox; there is no anti-cheat machinery (user directive, 2026-08-28).

### Owned concepts

B2-024 owns exactly six Book 2 concepts, matching its knowledge points:

1. `gpu-colab-l4-workflow` — Session 1.
2. `open-ended-experiment-design` — Session 2.
3. `open-ended-model-evaluation` — Session 3.
4. `semi-supervised-pseudo-labeling` — Session 4.
5. `scientific-ml-inverse-problems` — Session 5.
6. `mixture-parameter-regression` — Session 6.

### Direct prerequisites

Unit prerequisites (`prereq_units`, in this order):
`book1:F1-scientific-python`, `book1:F3-matrices`, `book1:F4-multivar-calculus`, `book1:F5-probability`, `book1:C1-ml-fundamentals`, `book1:C2-linear-models`, `book1:C3-gradient-descent`, `book1:C5-neural-networks`, `book1:C6-pytorch`, `book1:C7-cnn-transfer`, `book1:C10-competition-craft`, `book1:C11-neural-training`, `book1:C12-classical-models`, `B2-023-generative-models-diffusion`.

B2-023 is a schedule-order predecessor; no Book 2 concept is used. The mixture bumps are one-dimensional, so `book1:gaussian-distribution` covers them, and `multivariate-gaussian` and B2-022 are not prerequisites. The coverage-map row `mixture-parameter-regression` keeps `multivariate-gaussian` in `depends_on` unchanged: that field records the roadmap dependency, and it is satisfied transitively because B2-023 requires B2-022, which ships earlier in Book 2.
Task 1 rewrites the planned row's `prerequisites` to exactly this 14-unit list: B2-020, B2-021 and B2-022 are dropped and C5 is added. Its test asserts the new list.

The live syllabus entry, manifest, and notebook metadata use this exact ordered `concept_prerequisites` list:

```text
book1:numpy-arrays
book1:broadcasting
book1:random-seeding
book1:matrix-multiplication
book1:invertibility-via-rank
book1:gradient
book1:sum-of-squares-gradients
book1:expectation
book1:variance
book1:variance-of-sums
book1:independence
book1:covariance
book1:gaussian-distribution
book1:sampling-simulation
book1:train-test-split
book1:overfitting
book1:accuracy-precision-recall
book1:class-imbalance
book1:linear-regression
book1:mse-loss
book1:l2-regularization
book1:gradient-descent
book1:learning-rate
book1:stochastic-gd
book1:relu-activation
book1:mlp-architecture
book1:torch-tensors
book1:nn-module
book1:requires-grad
book1:parameter-counting
book1:convolution
book1:cnn-training
book1:hidden-test-protocol
book1:metric-driven-iteration
book1:writeup-quality
book1:colab-coding-submission
book1:cpu-and-gpu-round-boundary
book1:softmax
book1:cross-entropy-loss
book1:torch-optimizers
book1:autograd-training
book1:trained-mlp
book1:k-means
book1:lloyd-algorithm
```

No notebook or practice may carry a concept tag outside this list or the six owned concepts; in particular `book1:tensor-shape-tracing` is forbidden as a tag.
Lessons must reference every listed concept so `concepts_used` stays honest.
Task 3 extends the Book 2 `imports:` allowlist with every Book 1 unit and concept above that is not already imported, and lists the additions.

### Evaluation protocol (all model-building practices)

Every model-building practice (p16–p22, p26, p27) uses three immutable splits from its generator: `train_rows()`, `val_rows()`, and a locked test set.
- Learners may iterate, tune, and select only on train and validation.
- The test set is reachable only through `final_test_score(predict_fn, n_boot=1000, alpha=0.05)` in the unit's data module. It returns the stated metric together with its seeded percentile-bootstrap CI over test examples, computed inside the same call. Each solution calls it exactly once, after all fitting and selection.
- The answer check asserts one call, after training, and asserts that neither validation nor test rows entered training (checked at the practice's named seam; see Task 4).
- Baselines are fixed: each is computed by committed code in the data module (`baseline_score(task)`) at the frozen seed, and the statement prints the resulting number.

### Taught in this unit (not in the baseline, Book 1, or earlier Book 2 units)

- **Device placement and mixed precision (Session 1).**
  - The device-agnostic pattern `device = "cuda" if torch.cuda.is_available() else "cpu"`, moving the model and every batch with `.to(device)`, and device-mismatch errors.
  - `torch.autocast(device_type, dtype)`: `bfloat16` on L4, `float16` with a gradient scaler as the alternative, and `amp_dtype=None` (no autocast) as the CI path. Running `bfloat16` on CPU is shown for correctness only; on CPUs without native bf16 support it can be slower than `float32`.
  - CPU and L4 configurations are one config dict passed to the same code path, so the never-executed accelerator extension cannot drift from what CI runs.
  - Memory arithmetic with `book1:parameter-counting`: bytes per element, and fp32 master weights, fp32 gradients, two fp32 Adam moments, and activations.
- **Resumable training (Session 1).** Checkpointing the model, optimizer, step, and RNG states (`torch.get_rng_state`, and the CUDA state when present). Batch sampling uses the global `torch` RNG, so restoring it restores the sampler, and a resumed run reproduces the uninterrupted run's next-step loss under `torch.equal`.
- **Bootstrap confidence intervals (Session 3).** Percentile bootstrap over test examples with a seeded generator; paired comparison across shared seeds and examples. Why `Var(mean of n iid) = σ²/n` follows from `book1:variance-of-sums` and `book1:independence`.
- **Pseudo-labeling and cluster-then-label (Session 4).**
  - Confidence-thresholded, class-balanced pseudo-label selection and confirmation bias.
  - Cluster-then-label: `book1:k-means` on frozen features, with clusters labelled by majority of the labelled points.
  - Validation drawn only from labelled data.
- **Inverse problems (Session 5).**
  - Forward/observation operator, ill-posedness, and Tikhonov regularization as ridge regression (`book1:l2-regularization`).
  - The nonlinear field operator is linearized by discretization:
    - fix a 9×9 grid of candidate source positions on `[0,1]²`;
    - `A[i, j]` is the field magnitude at sensor `i` from a unit source at grid node `j`;
    - solve for a nonnegative-clipped grid density;
    - the source estimate is the density-weighted centroid of the top-3 nodes, and its strength is their total mass.
  - 81 grid unknowns from 8 sensors is heavily underdetermined. Session 5 says so explicitly as the motivation for regularization and for learned inversion; the p19 statement prints the baseline number it must beat.
  - The closed form `(AᵀA + λI)⁻¹Aᵀy`, derived from `book1:sum-of-squares-gradients` and `book1:invertibility-via-rank`.
  - Learned inversion trained on simulated pairs; physics-residual checks.
- **Mixture-function parameter regression (Session 6).**
  - Functions that are sums of exactly `K = 3` one-dimensional Gaussian bumps. The generator enforces center separation ≥ 3 × the largest width and positive weights. Label switching (non-identifiability under permutation).
  - Canonicalization by sorting on the center.
  - Permutation-invariant loss and evaluation; a least-squares baseline fitted with Adam (`lr=0.02`, 500 steps) from a fixed initialization: evenly spaced centers, equal weights, median width.

### Six-session teaching spine

| Session | File | Required teaching surface |
|---:|---|---|
| 1 | `01-gpu-workflow-on-colab-l4.ipynb` | device-agnostic code; device mismatches; autocast and dtype choice; memory arithmetic and batch sizing; out-of-memory triage; resumable checkpoints with RNG state; the Colab L4 session plan (time budget, restart procedure, saving to persistent storage, submission checklist), building on `book1:colab-coding-submission` and `book1:cpu-and-gpu-round-boundary` |
| 2 | `02-experiment-design-under-budget.ipynb` | hypotheses, baselines and ablations; fixed compute budgets; seeds and repeated runs; held-out discipline (`book1:hidden-test-protocol`); an experiment log; deciding what to run next (`book1:metric-driven-iteration`) |
| 3 | `03-evaluating-open-ended-models.ipynb` | metric choice; bootstrap CIs; paired comparisons; ablation tables; robustness to noise and shift; model-family comparison; writing the evaluation section (`book1:writeup-quality`) |
| 4 | `04-semi-supervised-pseudo-labeling.ipynb` | limited-label regimes; supervised baseline; confidence-threshold self-training; class balance (`book1:class-imbalance`); cluster-then-label; confirmation bias; leakage-safe validation; a tiny synthetic image-shape trace |
| 5 | `05-scientific-inverse-problems.ipynb` | forward operators (a single-source inverse-square field in 2-D, measured at sensors); ill-posedness and noise; Tikhonov; learned inversion from simulated pairs; physics residual and coverage of the source domain; open-ended workflow |
| 6 | `06-mixture-parameter-regression.ipynb` | mixture functions; identifiability and canonicalization; a least-squares baseline by gradient descent; a learned regressor from sampled values to parameters; permutation-invariant evaluation; open-ended workflow |

Each session has 6–10 substantive sections, at least two checkpoints per section with collected answers, common pitfalls, exam connections, and one forward-only "going deeper" topic.
Session 1's deeper topic is the markdown-only real-pipeline guide described above.

### Exact practice ledger

Statements are unexecuted and solution-free.
Coding and training statements pin shapes, dtypes, seeds, permitted data, and tolerances.
Every solution ends with `### Answer check`.
`L4` in the compute column means `optional-colab-l4`; every other practice is `cpu`.

| ID | Set | Type | Difficulty | Min | Compute | Primary scored contract |
|---|---|---|---:|---:|---|---|
| p01 | A | mc-normal-form | intro | 20 | cpu | from a literal parameter count and activation element count, compute the ratio of training memory with `bfloat16` activations to all-`float32` training memory as `a/b` (`gcd(a,b)=1`, `b>0`). Counted tensors: fp32 master weights, fp32 gradients, two fp32 Adam moments, and activations. Select normalized `a+b` from exactly five A–E choices |
| p02 | A | mc | intro | 20 | cpu | identify the cause of, and the fix for, a device-mismatch traceback |
| p03 | A | mc | intro | 20 | cpu | choose the baseline and the single ablation that test a stated hypothesis |
| p04 | A | mc | core | 20 | cpu | apply a confidence threshold and per-class cap to a literal probability table |
| p05 | A | mc | core | 20 | cpu | identify which loss is permutation-invariant for mixture parameters |
| p06 | B | constrained-coding | intro | 50 | L4 | implement `get_device()`, `move_batch(batch, device)` and `train_step(model, batch, optimizer, device, amp_dtype)` with autocast, verified on CPU |
| p07 | B | constrained-coding | core | 50 | L4 | implement `save_checkpoint(path, model, optimizer, step)` and `load_checkpoint(path, model, optimizer)` including the global `torch` RNG state; a resumed run must reproduce the uninterrupted next-step loss (`torch.equal`) |
| p08 | B | constrained-coding | core | 50 | cpu | implement `bootstrap_ci(metric_fn, y_true, y_pred, n_boot, alpha, generator)` (percentile) and `paired_bootstrap_diff(...)` |
| p09 | B | constrained-coding | core | 50 | cpu | implement `select_pseudo_labels(probs, threshold, max_per_class)` returning indices and labels, class-balanced and deterministic on ties |
| p10 | B | constrained-coding | core | 50 | cpu | implement `forward_field(source_xy, strength, sensors_xy)`, `grid_operator(grid_xy, sensors_xy)` building `A`, and `tikhonov_solve(A, y, lam)` using `torch.linalg.solve` |
| p11 | B | constrained-coding | core | 50 | cpu | implement `mixture_function(x, weights, centers, widths)` for `K = 3` and `canonicalize(params)` (sort by center) |
| p12 | B | constrained-coding | advanced | 50 | cpu | implement `run_ablation(configs, train_fn, seeds)` returning a per-config mean ± sample-std table under a fixed step budget |
| p13 | B | proof | core | 45 | cpu | derive the Tikhonov minimizer `(AᵀA + λI)⁻¹Aᵀy` and prove it is unique for `λ > 0` |
| p14 | B | proof | core | 45 | cpu | prove that permuting mixture components leaves the function unchanged, and that sorting by strictly distinct centers gives a unique canonical parameter vector |
| p15 | B | proof | core | 45 | cpu | prove `Var(mean) = σ²/n` for iid runs, and show that a paired difference has lower variance when the runs are positively correlated |
| p16 | C | integrative | core | 65 | L4 | train a small CNN (the statement describes the 8×8 shape dataset itself) with the p06/p07 helpers: checkpoint at step k, resume, and certify the loss decrease and resume equality on CPU with `amp_dtype=None`; accelerator extension for L4 |
| p17 | C | integrative | advanced | 65 | L4 | semi-supervised shape classification on 8×8 synthetic images with 30 labelled examples: certify that self-training beats the fixed labelled-only baseline's test accuracy by a stated margin, with selection on labelled validation only |
| p18 | C | integrative | advanced | 65 | cpu | cluster-then-label with `k-means` (k = 3) on frozen features from a labelled-only CNN. A cluster with no labelled member takes the label of the nearest labelled-class centroid in the frozen feature space, and majority ties go to the lowest class index. Compare it with threshold pseudo-labels; certify that cluster-then-label beats the fixed baseline by a stated margin, and report its comparison with the threshold method |
| p19 | C | integrative | advanced | 65 | L4 | learned inversion: train an MLP on simulated sensor→source pairs; certify that the final test source-position error is below the fixed grid-Tikhonov baseline score, and that the physics residual is below a stated bound |
| p20 | C | integrative | advanced | 65 | L4 | train an amortized regressor from 32 sampled function values to the 9 canonical parameters, then refine each prediction with 100 LS steps initialized at the regressor's output. Certify that this pipeline's final test permutation-invariant error is below the fixed-init LS baseline score (500 steps). Also report the raw regressor's error, which may lose to per-sample fitting; the lesson says so honestly |
| p21 | C | integrative | core | 65 | cpu | produce an evaluation report for two model families: bootstrap CIs, a paired comparison across shared seeds, an ablation table, and robustness to an input-noise shift |
| p22 | C | integrative | core | 65 | cpu | run a budgeted experiment campaign (hypothesis → configs → results → decision) within a fixed total step budget and log it |
| p23 | C | scenario | core | 55 | cpu | plan a Colab L4 session for a stated task: memory and time budget, OOM triage order, checkpoint cadence, restart procedure, submission checklist |
| p24 | C | scenario | core | 55 | cpu | evaluate a supplied validation results table (per-seed scores, bootstrap CIs, one ablation) to decide which differences are real, then choose the next experiments under a time limit while avoiding hidden-test overfitting |
| p25 | C | scenario | core | 55 | cpu | diagnose when pseudo-labeling hurts (confirmation bias, imbalance) from a literal training trace, and choose a remedy |
| p26 | C | challenge | advanced | 55 | cpu | open-ended inverse-problem mini-competition: build any valid approach within the budget (≤ 2,000 optimizer steps, counted by a provided `StepBudget` wrapper, and < 15 s wall-clock); beat the committed baseline score on the locked test set; write the rubric writeup |
| p27 | C | challenge | advanced | 55 | cpu | open-ended mixture-parameter mini-competition with the same budget, baseline, and writeup deliverables |
| p28 | C | challenge | advanced | 55 | cpu | audit a results report for test-set reuse, seed cherry-picking, an invalid CI, and leakage; write the corrected report |

The ledger has 28 practices: 5 MC, 7 constrained coding, 3 proof, 7 integrative, 3 scenario, and 3 challenge (1,370 practice minutes).
The difficulty spread is 4 intro / 16 core / 8 advanced. The intro share (14%) is below the ~30% guide by design: this is the capstone. Siblings shipped about 21%.

The writeup rubric for p26/p27 has four required subsections:
- **Approach**: the model, its features, and why.
- **Alternatives considered**: at least two, each with the evidence that ruled it out.
- **Evaluation**: the validation protocol, the single final test score with a bootstrap CI, and the comparison with the baseline.
- **Limitations**: at least one failure mode and how it would be tested.
Every owned concept has at least three direct practices:

| Concept | Direct practices |
|---|---|
| `gpu-colab-l4-workflow` | p01, p02, p06, p07, p16, p23 |
| `open-ended-experiment-design` | p03, p12, p22, p24 |
| `open-ended-model-evaluation` | p08, p15, p21, p24, p28 |
| `semi-supervised-pseudo-labeling` | p04, p09, p17, p18, p25 |
| `scientific-ml-inverse-problems` | p10, p13, p19, p26 |
| `mixture-parameter-regression` | p05, p11, p14, p20, p27 |

### Seven-week schedule and coverage

Append a seven-week Book 2 ledger after B2-023's final review (Book 2 week 30):

| Book week | Global week | Allocation | Minutes |
|---:|---:|---|---:|
| 31 | 71 | bridge 30; Session 1; p01, p02, p06, p07 | 260 |
| 32 | 72 | Session 2; p03, p12, p16, p23 | 280 |
| 33 | 73 | Session 3; p08, p15, p21, p22, p24 | 370 |
| 34 | 74 | Session 4; p04, p09, p17, p18, p25 | 345 |
| 35 | 75 | Session 5; p10, p13, p19, p28 | 305 |
| 36 | 76 | Session 6; p05, p11, p14, p20, p26, p27 | 380 |
| 37 | 77 | review 60 | 60 |

The unit totals 2,000 scheduled minutes (bridge 30, six 90-minute sessions, practices 1,370, review 60) and 1,970 manifested minutes, which is 33.3 h, inside the row's 30–40 h estimate.
After this unit Book 2 is **37 weeks / 10,270 scheduled minutes** with `final_assessment.after_book_week: 37`.
Audit rendered hours rebaseline by +32.83 h manifested and +33.33 h scheduled from the post-Plan-028 values.
Task 1 restates the resulting ranges from the merged `main` before writing tests.

Promote exactly these coverage rows from `missing` to `covered` and set each row's `modalities_missing: []`.
Each row needs evidence for exactly the modalities its coverage-map row lists, with a lesson anchor per modality:

| Row | Required modalities | Primary practices |
|---|---|---|
| `gpu-colab-l4-workflow` | implementation, model-training, competition-workflow | p06, p07; p16; p23 |
| `semi-supervised-pseudo-labeling` | theory, implementation, model-training, competition-workflow | p04; p09; p17, p18; p25 |
| `scientific-ml-inverse-problems` | theory, implementation, model-training, competition-workflow | p13; p10; p19; p26 |
| `open-ended-experiment-design` | model-training, competition-workflow | p22, p12; p24 |
| `open-ended-model-evaluation` | model-training, competition-workflow | p21; p28, p24 |
| `mixture-parameter-regression` | theory, implementation, model-training, competition-workflow | p14, p05; p11; p20; p27 |

If a row on the merged `main` lists modalities different from this table, Task 1 updates the table to match the row before writing tests.

## Implementation tasks

### Task 1 — `optional-colab-l4` policy, registration, and schedule contract

**Files:**

- `tools/checks/layer_boundary.py`
- `tools/model.py` (only if parsing must change)
- `book2/curriculum/coverage-map.yaml`
- `docs/curriculum-roadmap.md` and `docs/audits/015-coverage-audit.md` (both regenerated)
- create `tests/test_compute_policy.py` and `tests/test_b2_024_plan.py`

Steps:

- [x] Write failing tests for `optional-colab-l4` in a copied Book 2 fixture. The policy is accepted only when:
  - the practice has a local solution path (the CPU correctness path);
  - the statement contains an `Accelerator extension` heading.
  The tests also show that `gpu-required` is still rejected (unsupported here), that unknown policies are rejected, and that `cpu` behavior is unchanged byte for byte on the shipped Book 2.
- [x] Implement the minimal `_check_compute` change.
- [x] Write failing tests for the existing B2-024 `planned_units` row:
  - the exact prerequisite sequence;
  - the six `provisional_concepts`;
  - the double-length standard (6 sessions, 28 practices);
  - the six rows staying `missing`.
  Also prove, in a copied fixture, the seven-week ledger after B2-023 (`after_book_week: 37`, 10,270 scheduled minutes) and that duplicate, misordered, missing-session, minute-mismatched, or before-week-31 allocations are rejected.
- [x] Update only the existing planned row (prerequisites rewritten to the 14-unit list; `provisional_concepts` set) and regenerate the roadmap and audit. The "rows stay `missing`" assertions are rewritten in Task 3 when the rows are promoted. Run `PATH=/home/chris/.local/bin:$PATH uv run pytest -q tests/test_compute_policy.py tests/test_book2_schedule.py tests/test_b2_024_plan.py` and commit.

### Task 2 — Author lessons, statements, and generators

- [x] Dispatch authoring to an Opus subagent per `AGENTS.md ## Agent dispatch`. It writes, in a temporary directory outside `book2/units/`:
  - the bridge, overview, six lessons, and review;
  - the 28 statements;
  - `scripts/generate_capstone_data.py` with `data/capstone_data.py`.
- [x] The generator produces four seeded datasets:
  - 8×8 synthetic shape images (3 classes) with noise, position jitter, and stroke-width variation, in two disjoint families:
    - `shapes_supervised` for p16: 600 labelled train, 150 validation, 150 test;
    - `shapes_ssl` for p17/p18: 30 labelled train, 30 labelled validation, 600 unlabelled, 300 test. It is tuned so the labelled-only baseline lands at most 0.85 test accuracy at the frozen seed.
    The unlabelled pool's labels are never exposed by any accessor.
  - inverse-problem pairs (2-D source position in `[0.1, 0.9]²` and strength → noisy field magnitudes at 8 fixed sensors): 800 train, 200 validation, and 200 test;
  - mixture-function samples (`K = 3` bumps, 32 x-values, canonical parameters): 800 train, 200 validation, and 200 test;
  - two literal results tables for p24/p28.
  It exposes immutable split ID tuples, a canonical per-row SHA-256 map, `final_test_score(predict_fn)`, `baseline_score(task)`, and a `StepBudget` optimizer wrapper. It has a `--check` mode, and it never stores trained weights or metrics.
- [x] Model-building statements (p16–p22, p26, p27) follow the evaluation protocol above and name one clean-row seam each, so leakage checks can hash clean rows there:
  - p16, p17, p19 and p20: the model's first `forward`;
  - p18: the frozen feature extractor's `features(x)`;
  - p21 and p22: the `fit(train_x, train_y)` call of the compared models;
  - p26 and p27: the `fit` entry point the statement requires every approach to expose.
- [x] Every `optional-colab-l4` statement carries an `Accelerator extension` section: the larger L4 configuration, given as a replacement config dict for the same code path.
- [x] CPU budgets, pinned in the statements:
  - p16: CNN `Conv(1→8,3)`, ReLU, `Conv(8→16,3)`, ReLU, linear head to 3 classes; 600 rows; 300 mini-batch steps (batch 64).
  - p17: the same CNN; 3 self-training rounds of 150 steps each.
  - p18: the p16 CNN trained on labelled data only (150 steps), then k-means with k = 3 and 20 Lloyd iterations.
  - p19: MLP `8→64→64→3`; 1,500 full-batch Adam steps.
  - p20: MLP `32→128→128→9`; 1,500 full-batch Adam steps.
  - p21 and p22: MLPs no wider than 64 on the inverse-problem pairs dataset; ≤ 2,000 total steps. All comparisons, bootstrap CIs, ablations and robustness checks are computed on validation. The single `final_test_score` call scores only the final selected model (p21: the chosen family; p22: the chosen configuration).
  - p26 and p27: within `StepBudget(2000)`.
  Every solution must run well under 20 s on CPU, measured in Task 3.
- [x] Certification margins are set from the frozen-seed run with comfortable slack. Two are pinned here:
  - p17 and p18 must beat the baseline by at least 0.03 absolute test accuracy;
  - p20's margin below the baseline is taken from the frozen-seed run, not assumed positive; if the refined pipeline cannot clear the baseline with slack, the LS refinement steps are adjusted before publication and the change is recorded;
  - p19, p20, p26 and p27 must beat their committed baseline scores.
- [x] The open-ended challenges (p26, p27) fix a held-out set, a score function, a stated baseline score, a step budget, and a required writeup following the four-part rubric (Approach, Alternatives considered, Evaluation, Limitations). Any approach that beats the baseline within budget is correct. The solution gives one reference approach plus the writeup.
- [x] Bundle allowlist checks (as in Plans 027/028), then a SHA-256 manifest outside the bundle.

### Task 3 — Blind-author solutions, publish, and execute

- [x] Dispatch a separate fresh Opus subagent for solutions with only the hash-verified bundle. One solution per statement, no stored outputs, final `### Answer check`, `SEED=20261022`. Statement ambiguities found are fixed in the statements and listed in the report.
- [x] Publish atomically, mirroring Plans 027 and 028:
  - the `capstone` concept cluster in the syllabus, plus the live unit entry;
  - clear `provisional_concepts`;
  - the unit tree with its manifest; each practice row declares `compute.policy` as in the ledger, with `compute.seed: 20261022`;
  - the schedule, coverage promotion per the table, and the imports allowlist;
  - the double-length roster;
  - the path inventory and its guard SHA;
  - the 20-second solution-timeout glob;
  - regenerated artifacts.
- [x] Execute every solution without `--inplace` and record elapsed times (<20 s each). Commit `tests/test_b2_024_statements.py`, covering hygiene, the ledger, coverage, generator `--check`, headers, an `Accelerator extension` heading in every L4 statement, and the exact file inventory.

### Task 4 — Answer-check integrity (lightweight)

- [x] Write `tests/test_capstone_checks.py`. For every listed function, the untouched solution passes and the named wrong variant fails:
  - `move_batch`: the model moved but the batch left behind;
  - `load_checkpoint`: RNG state not restored;
  - `bootstrap_ci`: resampling predictions without the matching labels;
  - `select_pseudo_labels`: `>` versus `>=` at the threshold, or the per-class cap ignored;
  - `tikhonov_solve`: `+λ` dropped;
  - `canonicalize`: sorting by weight instead of center;
  - `run_ablation`: population std instead of sample std;
  - `train_step`: autocast omitted when `amp_dtype=torch.bfloat16`, detected by the output dtype on CPU.
  In addition:
  - p16, p17, p19 and p20 (whose statements require a named training function with an optimizer) get a no-op optimizer-step mutant.
  - Every model-building practice gets a leakage mutant (validation or test rows reaching training), detected at its named seam with the check armed only during fitting.
  - Every model-building practice gets a protocol mutant (`final_test_score` called twice, or before fitting).
- [x] This is a correctness check only; anti-cheat is out of scope. Wire the suite into `scripts/ci-local.sh` step 7 and commit.

### Task 5 — Verification, content gate, report, merge

- [x] Verification phase:
  - the focused suites and the generator `--check`;
  - the per-book checks (prereq, coverage, scope, schedule, tolerance, hygiene, layer-boundary);
  - the `--all` aggregate checks;
  - the audit and roadmap `--check`;
  - `git diff --check`.
- [x] `scripts/ci-local.sh` ALL GREEN.
- [x] 3-way blind content gate:
  - Sol solves p01, p10, p13, p19 and p26.
  - Fable solves p04, p08, p14, p17 and p27.
  - Self solves p07, p11, p15, p20 and p23, and also reviews the ledger, coverage, and accessibility. Self also checks provenance: the generator specifics are compared against the local reference index and rationale (where present on this machine) as well as `analysis.md`, to confirm the task families are original and not close paraphrases.
  Resolve every `[OPEN]` finding and re-review after material changes.
- [x] Write the verdicts and the post-execution report, and add Plan 029 to `TODO.md`.
- [ ] Rerun CI on the clean tip, push, open the PR, run `pre-merge-guard --pr`, squash-merge without deleting local history refs, and verify `main` equals `origin/main`.

## Out of scope

- The Round 2 assessment (Plan 024, reserved by Plan 019).
- The `gpu-required` policy and any task that cannot run on CPU.
- Executed pretrained-weight downloads or model hubs (the real-pipeline guide stays markdown-only).
- Past-paper text or close paraphrase.
- Changes to Book 1 or to the B2-019–B2-023 units.

## Plan Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Review 1 — self (2026-10-09)
- **Verdict**: Approve with suggestions. Plans 027/028 review lessons were applied up front.

### Review 1 — Sol, `gpt-6-sol` (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: prerequisite closure missed `mlp-architecture`, `relu-activation`, and `linear-regression`. → Response: C5 added; concept list expanded (also `l2-regularization`, `trained-mlp`, `parameter-counting`, `stochastic-gd`, `accuracy-precision-recall`).
2. `[FIXED]` Must Fix: repeated selection against held-out data reuses the test set. → Response: an "Evaluation protocol" with train/validation/locked test, and `final_test_score` called once after fitting.
3. `[FIXED]` Must Fix: optimizer and `forward` mutants don't fit p18/p21/p26/p27. → Response: a named seam per practice; optimizer mutants limited to p16/p17/p19/p20; protocol mutants added.
4. `[FIXED]` Should Fix: baseline linearization and attainable thresholds undefined. → Response: the grid-Tikhonov construction is pinned; baselines are committed code at the frozen seed; margins come from the frozen run.

### Review 1 — Fable (2026-10-09)
- **Verdict**: Approve with nits (conditional on Must Fix 1–3).
1. `[FIXED]` Must Fix: inverse-problem `A` undefined. → Response: a 9×9 candidate-grid operator, Tikhonov density, and top-3 centroid read-out.
2. `[FIXED]` Must Fix: variable `K`. → Response: `K = 3`, enforced separation, and a pinned LS baseline initialization and steps.
3. `[FIXED]` Must Fix: SSL headroom. → Response: generator difficulty tuned to a baseline ≤ 0.85; a 0.03 margin; p18's certification defined.
4. `[FIXED]` Should Fix: pin CPU budgets. → Response: per-practice sizes and steps.
5. `[FIXED]` Should Fix: CPU bf16 honesty. → Response: `amp_dtype=None` CI path; bf16-on-CPU for correctness only; L4 extension as a config dict for the same code.
6. `[FIXED]` Should Fix: concept-tag gaps; `multivariate-gaussian` unused. → Response: tags added; `multivariate-gaussian` and B2-022 dropped.
7. `[FIXED]` Should Fix: planned-row prerequisites. → Response: Task 1 explicitly rewrites them to the 14-unit list.
8. `[FIXED]` Should Fix: p26/p27 gradability. → Response: `StepBudget` plus wall-clock limit, committed baseline, four-part writeup rubric.
9. `[FIXED]` Should Fix: p07 exact resume. → Response: global RNG for sampling; `torch.equal`.
10. `[FIXED]` Should Fix: p01 memory model. → Response: the counted tensors are enumerated.
11. `[FIXED]` Nits: the missing-row tests are rewritten in Task 3; autocast-omitted mutant; p16 describes its dataset; provenance compared against the local index and rationale; intro share noted.

### Review 2 — self (2026-10-09)
- **Verdict**: Approve after fixes. Checked `layer_boundary.py`: each coverage claim needs ≥ 3 qualifying primary practices across its modalities. All six rows now satisfy it, and Plans 027/028 already did.

### Review 2 — Fable (2026-10-09)
- **Verdict**: Approve with nits.
1. `[FIXED]` Should Fix: p20 baseline may beat an amortized regressor. → Response: the certified pipeline is regressor + 100-step LS refinement against fixed-init LS; the raw regressor is reported honestly.
2. `[FIXED]` Should Fix: p16 vs the 600-row pool. → Response: a disjoint `shapes_supervised` family for p16; pool labels are never exposed.
3. `[FIXED]` Nits: p18 empty-cluster and tie rule; p21/p22 dataset named; p19 underdetermination motivation and printed baseline; rubric wording unified to four parts.

### Review 2 — Sol, `gpt-6-sol` (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: p16 had no 600-row labelled split. → Response: `shapes_supervised` (600/150/150).
2. `[FIXED]` Must Fix: `open-ended-model-evaluation` had only 2 primary practices. → Response: p24 added under competition-workflow (p21, p28, p24).
3. `[FIXED]` Should Fix: mixture `depends_on` on `multivariate-gaussian`. → Response: retained as roadmap metadata, satisfied transitively through B2-023 → B2-022.
4. `[FIXED]` Should Fix: p21/p22 split usage. → Response: everything on validation; one test call for the final selected model.

### Review 3 — self (2026-10-09)
- **Verdict**: Approve after fixes.

### Review 3 — Fable (2026-10-09)
- **Verdict**: Approve with nits.
1. `[FIXED]` Nit: a bootstrap CI is impossible from a one-call scalar. → Response: `final_test_score` returns the metric plus a seeded bootstrap CI in the same call (same as Sol 1).
2. `[FIXED]` Nit: p20's margin comes from the frozen-seed run.
3. `[FIXED]` Nit: the p18 centroid is computed in the frozen feature space.

### Review 3 — Sol, `gpt-6-sol` (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the locked-test API cannot produce the rubric's CI. → Response: the single call returns the metric and its CI.
2. `[FIXED]` Must Fix: p24 is not genuinely an evaluation practice. → Response: p24 now first evaluates a supplied validation results table (per-seed scores, CIs, an ablation) to decide which differences are real.

### Review 4 — self (2026-10-09)
- **Verdict**: Approve.

### Review 4 — Fable (2026-10-09)
- **Verdict**: Approve. Implementer note: record the observed frozen-seed margins (p17/p18 accuracy gaps; p19/p20/p26/p27 baseline gaps) in the post-execution report.

### Review 4 — Sol, `gpt-6-sol` (2026-10-09)
- **Verdict**: Approve. No findings.

**Gate result:** 3-way consensus at round 4 (b99e1c4); implementation authorized after Plan 028 merges and this branch merges that `main`.

## Content Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`).

### Review 1 — self (2026-10-10)
- **Blind answer**: p15 pairing ratio `1 − ρ = 0.25`; sd(D̄) = 8.165e-4, so 0.0015 is 1.84 sd, not beyond 2 sd. Matches the solution.
- **Verdict**: Approve.

### Review 1 — Sol, `gpt-6-sol` (2026-10-10)
- **Blind answers**: p01 E (13/18 → 31); p10 grid operator plus one solve; p13 PD and completed square; p19 and p26 approaches. All agree.
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the L4 extensions were not pure config-dict replacements. → Response: p06, p07, p16, p17, p19 and p20 solutions read every device/precision/size/data knob from one config dict. Each supplied cell defines `CPU_CONFIG` with exactly `L4_CONFIG`'s keys. CPU outputs are byte-identical before and after (b37aba8), and non-default branches were smoke-run on CPU.
2. `[FIXED]` Should Fix: p10 said the unregularized normal equations may have no solution. → Response: they are always consistent, with infinitely many solutions.
3. `[FIXED]` Should Fix: the heading check accepted a fenced example. → Response: `_outside_fenced_code` follows CommonMark fences; failing-first tests added.

### Review 1 — Fable (2026-10-10)
- **Blind answers**: p04 B; p08 all four probes exact; p14 permutation/canonicalization proof; p17 test 0.8867 (identical trace); p27 a different valid approach (0.00431 < 0.00907). All agree.
- **Verdict**: Approve with nits.
1. `[FIXED]` Should Fix: Lesson 6 undercounted p27's budget (validation `predict` also spends steps). → Response: 1,500 + 100 + 100 = 1,700; Checkpoint 6B reworked; p27's Budget bullet updated.
2. `[FIXED]` Nits: p06 batch naming; p09 "row 9 paired with row 6"; p26 reports the mean physics residual (ungraded).
3. `[WONTFIX]` Nits: p18's CI lower bound sits below the 0.84 bar, stated as frozen-seed only; p21's dummy `y_true` is clearly specified; the baseline call before the budget costs about 1 s of 15.

### Review 2 — self (2026-10-10)
- **Verdict**: Approve.

### Review 2 — Fable (2026-10-10)
- **Verdict**: Approve with nits. Re-ran p06/p07/p17/p19/p20 from scratch: outputs identical to round 1; every `L4_CONFIG` has exactly `CPU_CONFIG`'s keys.
1. `[FIXED]` Nit: p17 "third-round" → "final-round" (L4 has four rounds).
2. `[WONTFIX]` Nit: p19 shows the constructor signature twice; it is consistent.

### Review 2 — Sol, `gpt-6-sol` (2026-10-10)
- **Verdict**: Approve with nits.
1. `[FIXED]` Nit: p07's answer check hard-coded `k == 20`, which would fail on an L4 rerun. → Response: it now asserts `k == CONFIG["checkpoint_every"] == N`; p07 re-executed.

**Gate result:** 3-way consensus on the final head.

## Post-execution report

**Shipped:** `book2/units/B2-024-gpu-scientific-ml-capstone`, the final Book 2 teaching unit.
- Double-length: bridge, overview, six 90-minute sessions, review, and 28 practices.
- 2,000 scheduled / 1,970 manifested minutes. Book 2 is now 37 weeks / 10,270 scheduled minutes with `after_book_week: 37`.
- Hours: 620.75–660.75 manifested / 627.75–667.75 scheduled.
- Six coverage rows are covered: `gpu-colab-l4-workflow`, `open-ended-experiment-design`, `open-ended-model-evaluation`, `semi-supervised-pseudo-labeling`, `scientific-ml-inverse-problems`, `mixture-parameter-regression`.
- The `optional-colab-l4` compute policy is now accepted by `layer_boundary.py`. It requires a local solution path plus an `Accelerator extension` heading outside fenced code; `gpu-required` stays rejected.

**Imports added to the Book 2 allowlist:**
- units: C3, C10, C12;
- concepts: invertibility-via-rank, sum-of-squares-gradients, overfitting, accuracy-precision-recall, class-imbalance, linear-regression, l2-regularization, gradient-descent, learning-rate, stochastic-gd, parameter-counting, hidden-test-protocol, metric-driven-iteration, writeup-quality, colab-coding-submission, cpu-and-gpu-round-boundary, trained-mlp, k-means, lloyd-algorithm.

**Dispatch and commits:**
- An Opus author wrote the bundle; a separate fresh Opus session blind-solved all 28 practices. Statement pins from the blind solve: p23 framing, p25 per-round counts, and the p26/p27 iterative-solver budget rule.
- An Opus implementer: ea55c05, 44d549a, a4e9403, c7a4c57.
- Content-gate fixes: b37aba8, f4524fa.

**Deviations, recorded and accepted by the gate:**
- p17 certifies noisy-student self-training. Plain threshold self-training gave no reliable 0.03 gain, and a noise-only ablation is required for honest attribution.
- p18's cluster-then-label (conv1 pre-ReLU features) clears its bar at the frozen seed only, which the lesson and statement say openly.
- Inverse targets are (x, y, q) with a position-only metric; strength is checked through the physics residual.
- A `simulate()` helper was added for accelerator scaling.
- `final_test_score`'s `task` argument is keyword-only.

**Observed frozen-seed margins (Fable's plan-gate note):**
- p17 +0.077 and p18 +0.063 test accuracy over the 0.81 baseline (bar 0.84).
- p19 0.0103 against the 0.2137 baseline.
- p20 0.0046 against 0.0091.
- p26 about 0.007 against 0.2137.
- p27 0.0046 against 0.0091.

**Verification:**
- Focused suites pass, including `test_capstone_checks.py` (50 passed) and `test_compute_policy.py`.
- Full pytest: 1516 passed before the final attention-digest repair, which was then verified.
- After the round-1 fixes, CPU outputs were byte-identical.
- Solutions run in 3.1–13.5 s.
- Final authoritative CI is recorded below.

**Content gate:**
- Three-way blind consensus in round 2. All 15 blind-solved practices agreed with the solutions.
- Main fix: config-dict accelerator paths, so `L4_CONFIG` is a pure replacement for `CPU_CONFIG`. Also fixed: p10's normal-equations explanation, the fenced-heading loophole, and Lesson 6's budget arithmetic.

**Provenance:** original problems and synthetic generators. They mirror the Round 2 task families structurally only (inverse problem, semi-supervised imaging, mixture regression), as the coverage map requires.
