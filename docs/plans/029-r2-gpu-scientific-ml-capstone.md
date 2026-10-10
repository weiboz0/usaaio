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
`book1:F1-scientific-python`, `book1:F3-matrices`, `book1:F4-multivar-calculus`, `book1:F5-probability`, `book1:C1-ml-fundamentals`, `book1:C2-linear-models`, `book1:C3-gradient-descent`, `book1:C6-pytorch`, `book1:C7-cnn-transfer`, `book1:C10-competition-craft`, `book1:C11-neural-training`, `book1:C12-classical-models`, `B2-022-probabilistic-latent-models`, `B2-023-generative-models-diffusion`.

B2-023 is a schedule-order predecessor; no B2-023 concept is used.

The live syllabus entry, manifest, and notebook metadata use this exact ordered `concept_prerequisites` list:

```text
multivariate-gaussian
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
book1:class-imbalance
book1:mse-loss
book1:gradient-descent
book1:learning-rate
book1:torch-tensors
book1:nn-module
book1:requires-grad
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
book1:k-means
book1:lloyd-algorithm
```

No notebook or practice may carry a concept tag outside this list or the six owned concepts; in particular `book1:tensor-shape-tracing` is forbidden as a tag.
Lessons must reference every listed concept so `concepts_used` stays honest.
Task 3 extends the Book 2 `imports:` allowlist with every Book 1 unit and concept above that is not already imported, and lists the additions.

### Taught in this unit (not in the baseline, Book 1, or earlier Book 2 units)

- **Device placement and mixed precision (Session 1).**
  - The device-agnostic pattern `device = "cuda" if torch.cuda.is_available() else "cpu"`, moving the model and every batch with `.to(device)`, and device-mismatch errors.
  - `torch.autocast(device_type, dtype)`: `bfloat16` on CPU and L4, with a gradient scaler only for `float16` on CUDA.
  - Memory arithmetic: bytes per element; parameters, gradients and Adam state.
- **Resumable training (Session 1).** Checkpointing the model, optimizer, step, and RNG states (`torch.get_rng_state`, and the CUDA state when present). A resumed run reproduces the uninterrupted run's next-step loss.
- **Bootstrap confidence intervals (Session 3).** Percentile bootstrap over test examples with a seeded generator; paired comparison across shared seeds and examples. Why `Var(mean of n iid) = σ²/n` follows from `book1:variance-of-sums` and `book1:independence`.
- **Pseudo-labeling and cluster-then-label (Session 4).**
  - Confidence-thresholded, class-balanced pseudo-label selection and confirmation bias.
  - Cluster-then-label: `book1:k-means` on frozen features, with clusters labelled by majority of the labelled points.
  - Validation drawn only from labelled data.
- **Inverse problems (Session 5).**
  - Forward/observation operator, ill-posedness, and Tikhonov regularization.
  - The closed form `(AᵀA + λI)⁻¹Aᵀy`, derived from `book1:sum-of-squares-gradients` and `book1:invertibility-via-rank`.
  - Learned inversion trained on simulated pairs; physics-residual checks.
- **Mixture-function parameter regression (Session 6).**
  - Sum-of-Gaussian-bumps functions and label switching (non-identifiability under permutation).
  - Canonicalization by sorting on the center.
  - Permutation-invariant loss and evaluation; a gradient-based least-squares baseline.

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
| p01 | A | mc-normal-form | intro | 20 | cpu | from literal tensor shapes, compute the ratio of training memory in bytes with `bfloat16` activations to all-`float32` activations as `a/b` (`gcd(a,b)=1`, `b>0`); select normalized `a+b` from exactly five A–E choices |
| p02 | A | mc | intro | 20 | cpu | identify the cause of, and the fix for, a device-mismatch traceback |
| p03 | A | mc | intro | 20 | cpu | choose the baseline and the single ablation that test a stated hypothesis |
| p04 | A | mc | core | 20 | cpu | apply a confidence threshold and per-class cap to a literal probability table |
| p05 | A | mc | core | 20 | cpu | identify which loss is permutation-invariant for mixture parameters |
| p06 | B | constrained-coding | intro | 50 | L4 | implement `get_device()`, `move_batch(batch, device)` and `train_step(model, batch, optimizer, device, amp_dtype)` with autocast, verified on CPU |
| p07 | B | constrained-coding | core | 50 | L4 | implement `save_checkpoint(path, model, optimizer, step)` and `load_checkpoint(path, model, optimizer)` including RNG state; a resumed run must reproduce the uninterrupted next-step loss exactly |
| p08 | B | constrained-coding | core | 50 | cpu | implement `bootstrap_ci(metric_fn, y_true, y_pred, n_boot, alpha, generator)` (percentile) and `paired_bootstrap_diff(...)` |
| p09 | B | constrained-coding | core | 50 | cpu | implement `select_pseudo_labels(probs, threshold, max_per_class)` returning indices and labels, class-balanced and deterministic on ties |
| p10 | B | constrained-coding | core | 50 | cpu | implement `forward_field(source_xy, strength, sensors_xy)` and `tikhonov_solve(A, y, lam)` using `torch.linalg.solve` |
| p11 | B | constrained-coding | core | 50 | cpu | implement `mixture_function(x, weights, centers, widths)` and `canonicalize(params)` (sort by center) |
| p12 | B | constrained-coding | advanced | 50 | cpu | implement `run_ablation(configs, train_fn, seeds)` returning a per-config mean ± sample-std table under a fixed step budget |
| p13 | B | proof | core | 45 | cpu | derive the Tikhonov minimizer `(AᵀA + λI)⁻¹Aᵀy` and prove it is unique for `λ > 0` |
| p14 | B | proof | core | 45 | cpu | prove that permuting mixture components leaves the function unchanged, and that sorting by strictly distinct centers gives a unique canonical parameter vector |
| p15 | B | proof | core | 45 | cpu | prove `Var(mean) = σ²/n` for iid runs, and show that a paired difference has lower variance when the runs are positively correlated |
| p16 | C | integrative | core | 65 | L4 | train a small CNN with the p06/p07 helpers: autocast, checkpoint at step k, resume, and certify the loss decrease and resume equality on CPU; accelerator extension for L4 |
| p17 | C | integrative | advanced | 65 | L4 | semi-supervised shape classification on 8×8 synthetic images with 10% labels: certify that self-training beats the labelled-only baseline on the held-out test set, with validation from labelled data only |
| p18 | C | integrative | advanced | 65 | cpu | cluster-then-label with `k-means` on frozen features versus threshold pseudo-labels; certify both against the baseline and report which wins |
| p19 | C | integrative | advanced | 65 | L4 | learned inversion: train an MLP on simulated sensor→source pairs; certify held-out source error below the Tikhonov-linearized baseline and a physics residual below a stated bound |
| p20 | C | integrative | advanced | 65 | L4 | train a regressor from sampled function values to canonical mixture parameters; certify held-out permutation-invariant error below the least-squares baseline's |
| p21 | C | integrative | core | 65 | cpu | produce an evaluation report for two model families: bootstrap CIs, a paired comparison across shared seeds, an ablation table, and robustness to an input-noise shift |
| p22 | C | integrative | core | 65 | cpu | run a budgeted experiment campaign (hypothesis → configs → results → decision) within a fixed total step budget and log it |
| p23 | C | scenario | core | 55 | cpu | plan a Colab L4 session for a stated task: memory and time budget, OOM triage order, checkpoint cadence, restart procedure, submission checklist |
| p24 | C | scenario | core | 55 | cpu | choose the next experiments under a time limit while avoiding hidden-test overfitting |
| p25 | C | scenario | core | 55 | cpu | diagnose when pseudo-labeling hurts (confirmation bias, imbalance) from a literal training trace, and choose a remedy |
| p26 | C | challenge | advanced | 55 | cpu | open-ended inverse-problem mini-competition: build any valid approach within the budget, beat a stated baseline score on the held-out set, and write the approach/alternatives/evaluation section |
| p27 | C | challenge | advanced | 55 | cpu | open-ended mixture-parameter mini-competition with the same deliverables |
| p28 | C | challenge | advanced | 55 | cpu | audit a results report for test-set reuse, seed cherry-picking, an invalid CI, and leakage; write the corrected report |

The ledger has 28 practices: 5 MC, 7 constrained coding, 3 proof, 7 integrative, 3 scenario, and 3 challenge (1,370 practice minutes).
The difficulty spread is 4 intro / 16 core / 8 advanced.
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
| `open-ended-model-evaluation` | model-training, competition-workflow | p21; p28 |
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

- [ ] Write failing tests for `optional-colab-l4` in a copied Book 2 fixture. The policy is accepted only when:
  - the practice has a local solution path (the CPU correctness path);
  - the statement contains an `Accelerator extension` heading.
  The tests also show that `gpu-required` is still rejected (unsupported here), that unknown policies are rejected, and that `cpu` behavior is unchanged byte for byte on the shipped Book 2.
- [ ] Implement the minimal `_check_compute` change.
- [ ] Write failing tests for the existing B2-024 `planned_units` row:
  - the exact prerequisite sequence;
  - the six `provisional_concepts`;
  - the double-length standard (6 sessions, 28 practices);
  - the six rows staying `missing`.
  Also prove, in a copied fixture, the seven-week ledger after B2-023 (`after_book_week: 37`, 10,270 scheduled minutes) and that duplicate, misordered, missing-session, minute-mismatched, or before-week-31 allocations are rejected.
- [ ] Update only the existing planned row and regenerate the roadmap and audit. Run `PATH=/home/chris/.local/bin:$PATH uv run pytest -q tests/test_compute_policy.py tests/test_book2_schedule.py tests/test_b2_024_plan.py` and commit.

### Task 2 — Author lessons, statements, and generators

- [ ] Dispatch authoring to an Opus subagent per `AGENTS.md ## Agent dispatch`. It writes, in a temporary directory outside `book2/units/`:
  - the bridge, overview, six lessons, and review;
  - the 28 statements;
  - `scripts/generate_capstone_data.py` with `data/capstone_data.py`.
- [ ] The generator produces four seeded datasets:
  - 8×8 synthetic shape images (3 classes) with a 10% labelled split, an unlabelled pool, and a held-out test set;
  - inverse-problem pairs (2-D source position and strength → noisy field magnitudes at fixed sensors), split into train and held-out;
  - mixture-function samples (2–3 Gaussian bumps, canonical parameters), split into train and held-out;
  - two literal results tables for p24/p28.
  It exposes immutable split ID tuples and a canonical per-row SHA-256 map, has a `--check` mode, and never stores trained weights or metrics.
- [ ] Training statements (p16–p22, p26, p27) require `train_rows()` / `heldout_rows()` from the generator splits. Clean rows pass unchanged through the model's first `forward` call (or `forward_field` for simulation), so leakage checks can hash them.
- [ ] Every `optional-colab-l4` statement carries an `Accelerator extension` section with the larger L4 configuration.
- [ ] CPU budget for each training solution: fewer than 2,000 examples, at most 2,000 full-batch or mini-batch steps, and well under 20 s on CPU. Each statement pins its exact sizes.
- [ ] The open-ended challenges (p26, p27) fix a held-out set, a score function, a stated baseline score, a step budget, and a required writeup (approach, alternatives considered, evaluation). Any approach that beats the baseline within budget is correct. The solution gives one reference approach plus the writeup.
- [ ] Bundle allowlist checks (as in Plans 027/028), then a SHA-256 manifest outside the bundle.

### Task 3 — Blind-author solutions, publish, and execute

- [ ] Dispatch a separate fresh Opus subagent for solutions with only the hash-verified bundle. One solution per statement, no stored outputs, final `### Answer check`, `SEED=20261022`. Statement ambiguities found are fixed in the statements and listed in the report.
- [ ] Publish atomically, mirroring Plans 027 and 028:
  - the `capstone` concept cluster in the syllabus, plus the live unit entry;
  - clear `provisional_concepts`;
  - the unit tree with its manifest; each practice row declares `compute.policy` as in the ledger, with `compute.seed: 20261022`;
  - the schedule, coverage promotion per the table, and the imports allowlist;
  - the double-length roster;
  - the path inventory and its guard SHA;
  - the 20-second solution-timeout glob;
  - regenerated artifacts.
- [ ] Execute every solution without `--inplace` and record elapsed times (<20 s each). Commit `tests/test_b2_024_statements.py`, covering hygiene, the ledger, coverage, generator `--check`, headers, an `Accelerator extension` heading in every L4 statement, and the exact file inventory.

### Task 4 — Answer-check integrity (lightweight)

- [ ] Write `tests/test_capstone_checks.py`. For every listed function, the untouched solution passes and the named wrong variant fails:
  - `move_batch`: the model moved but the batch left behind;
  - `load_checkpoint`: RNG state not restored;
  - `bootstrap_ci`: resampling predictions without the matching labels;
  - `select_pseudo_labels`: `>` versus `>=` at the threshold, or the per-class cap ignored;
  - `tikhonov_solve`: `+λ` dropped;
  - `canonicalize`: sorting by weight instead of center;
  - `run_ablation`: population std instead of sample std.
  In addition, every training practice (p16–p22, p26, p27) gets a no-op optimizer-step mutant and a held-out-row mutant, detected at the clean-row seam and armed only during the training call.
- [ ] This is a correctness check only; anti-cheat is out of scope. Wire the suite into `scripts/ci-local.sh` step 7 and commit.

### Task 5 — Verification, content gate, report, merge

- [ ] Verification phase:
  - the focused suites and the generator `--check`;
  - the per-book checks (prereq, coverage, scope, schedule, tolerance, hygiene, layer-boundary);
  - the `--all` aggregate checks;
  - the audit and roadmap `--check`;
  - `git diff --check`.
- [ ] `scripts/ci-local.sh` ALL GREEN.
- [ ] 3-way blind content gate:
  - Sol solves p01, p10, p13, p19 and p26.
  - Fable solves p04, p08, p14, p17 and p27.
  - Self solves p07, p11, p15, p20 and p23, and also reviews the ledger, coverage, accessibility, and provenance (originality against the reference analysis).
  Resolve every `[OPEN]` finding and re-review after material changes.
- [ ] Write the verdicts and the post-execution report, and add Plan 029 to `TODO.md`.
- [ ] Rerun CI on the clean tip, push, open the PR, run `pre-merge-guard --pr`, squash-merge without deleting local history refs, and verify `main` equals `origin/main`.

## Out of scope

- The Round 2 assessment (Plan 024, reserved by Plan 019).
- The `gpu-required` policy and any task that cannot run on CPU.
- Executed pretrained-weight downloads or model hubs (the real-pipeline guide stays markdown-only).
- Past-paper text or close paraphrase.
- Changes to Book 1 or to the B2-019–B2-023 units.

## Plan Review

Pending.

## Content Review

Pending.

## Post-execution report

Pending.
