# Design 017 — Round 1 Neural Training Completion

## Objective

Close every acknowledged Round 1 neural-training gap from Plan 015 as one prerequisite-closed
system rather than scattering isolated APIs across C5, C6, and C7.
Students must be able to derive and implement stable multiclass loss, propagate gradients by
hand, train a fully connected network from scratch, reproduce the same loop with PyTorch
autograd and optimizers, reason about BatchNorm and dropout, and then train a small CNN.

The tranche is complete only when all ten neural knowledge points are checker-derived
`covered`, C7's recorded capacity non-conformance is honestly resolved, the course schedule
contains the new time before the Round 1 mock, and every changed statement/solution pair passes
the repository's execution and review gates.

## Considered approaches

### Continue appending to C5 and C6

C5 already owns network structure and forward propagation, while C6 owns tensors and module
construction.
Appending loss, backpropagation, full training loops, normalization, and regularization to those
units would blur the boundary between inference and learning and push their three-session shapes
beyond what their existing practice sets support.
It would also leave C7's model-training gap and recorded capacity decision unresolved.
This approach is rejected.

### Add only a new neural-training unit

A dedicated unit gives the loss-to-training arc a coherent owner and preserves C5/C6.
By itself, however, it would stop at fully connected networks while the audit explicitly records
C7 CNN model training as a remaining Round 1 gap.
C7 would also remain a 27-problem, three-session non-conformance.
This approach is incomplete and is rejected.

### Add C11 and complete C7's training surface

This is the selected design.
`C11-neural-training` is a double-length unit placed after C6 and before C7.
It owns the eight provisional concepts from Plan 015 and supplies the missing model-training
evidence for the existing PyTorch-programming knowledge point.
C7 then adds a fourth session plus four substantive training expansions and owns one new
`cnn-training` concept.
That added session makes C7 genuinely double-length under the existing 4–6-session and
24–30-practice contract; the design does not weaken or reinterpret the standard.

## Curriculum placement

### C11 neural losses, gradients, and training

Create `C11-neural-training` in the Round 1 core track with prerequisites
`F4-multivar-calculus`, `C3-gradient-descent`, `C5-neural-networks`, and `C6-pytorch`.
The explicit prerequisites mirror the audited owner boundary even where the graph is transitively
redundant, making the intended mathematical and engineering inputs visible locally.

C11 owns exactly these eight concepts:

- `softmax`;
- `cross-entropy-loss`;
- `manual-backpropagation`;
- `autograd-training`;
- `torch-optimizers`;
- `trained-mlp`;
- `batch-normalization`;
- `dropout`.

The unit has five 90-minute sessions:

1. stable softmax, shift invariance, log-sum-exp reasoning, categorical cross-entropy,
   negative log likelihood, the softmax Jacobian, and the fused gradient `p - y`;
2. computational graphs, local derivatives, gradient accumulation, tensor shapes, and a complete
   two-layer MLP backward pass by hand;
3. a deterministic NumPy network with forward cache, backward pass, mini-batches, parameter
   updates, loss tracking, and from-scratch training certification;
4. the PyTorch lifecycle `zero_grad` → forward → loss → `backward` → `step`, optimizer state,
   `train`/`eval`, `no_grad`, reproducibility, and evaluation;
5. BatchNorm's batch/running statistics and affine parameters, a derived backward formula,
   inverted-dropout expectation preservation, mode behavior, and controlled training ablations.

Examples use small seeded synthetic arrays only.
There are no downloads, network calls, GPU requirements, or hidden local datasets.
Numerical checks compare invariants, losses, gradients, and parameter movement under explicit
`atol`/`rtol`; they do not require fragile exact trained weights.

### C7 CNN training completion

Change C7's prerequisites to `[C6-pytorch, C11-neural-training]`.
The explicit C6 edge is transitively redundant but follows the same local-visibility principle as
C11's prerequisite list and keeps the engineering handoff readable at the unit and schedule row.
Add `cnn-training` to C7's owned concepts and add a 90-minute fourth session that transfers the
C11 loop to a tiny convolutional classifier and then to selective fine-tuning.
The session covers optimizer parameter selection, frozen-parameter invariants, train/eval mode,
BatchNorm buffers, dropout, loss-curve interpretation, and evaluation without gradients.

Expand C7-p10, C7-p24, C7-p26, and C7-p27 into 75-minute training capstones while preserving a
separately scored version of each existing learning objective:

- C7-p10 freezes the intended stages, performs a real optimizer update, and certifies that only
  eligible parameters move;
- C7-p24 preserves the hand-derived shape trace, constructs the traced tiny CNN, and trains it on
  a seeded synthetic batch;
- C7-p26 preserves the general convolution-shape helper, uses its trace to construct a valid
  stack, and certifies a real update;
- C7-p27 preserves the independence of mode, trainability, and graph recording, then audits
  BatchNorm/dropout and frozen-parameter behavior across actual training/evaluation steps.

All four grade `cnn-training` substantively, leaving one problem of margin over the coverage
floor.
They may tag C11 concepts only where those concepts change a scored deliverable.

## Knowledge-point closure

Every coverage-map row retains exactly one `destination` even when evidence spans prerequisite
units.
Existing `shipped_concepts` remain and the additions below make every new anchor resolve to a
concept taught by that anchor's unit.

| Knowledge point | Single destination | Evidence units | `shipped_concepts` additions | New evidence |
|---|---|---|---|---|
| softmax | C11 | C11 | softmax | theory, derivation, implementation |
| cross-entropy-loss | C11 | C11 | cross-entropy-loss | theory, derivation, implementation |
| backpropagation-by-hand | C11 | C11 | manual-backpropagation | theory, derivation, implementation |
| pytorch-autograd-and-optimizer-training | C11 | C6, C11 | autograd-training, torch-optimizers | implementation, model training |
| multilayer-perceptron-model | C11 | C5, C11 | trained-mlp | model training |
| fully-connected-network-from-scratch | C11 | C5, C11 | manual-backpropagation, trained-mlp | model training |
| batch-normalization | C11 | C7, C11 | batch-normalization | derivation, implementation, model training |
| dropout | C11 | C11 | dropout | theory, implementation, model training |
| pytorch-deep-learning-programming | C6 | C6, C11 | autograd-training, torch-optimizers | model training |
| convolutional-neural-network-basics | C7 | C7 | cnn-training | model training |

The first eight rows replace `P015-R1-NEURAL-TRAINING` with shipped evidence.
The last two rows are the coherently adjacent existing-unit gaps explicitly named by the Plan 015
queue and are included so the unit sequence is a complete Round 1 training system.
No Round 2 attention, transformer, advanced-vision, or GPU-capstone topic is promoted early.

## Practice and timing contract

C11 is double-length with exactly 24 practices and five lesson sessions.
The practice set contains four five-option MC problems, six constrained-coding tasks, three
proof/derivations, three integrative problems, four scenarios, and four challenges.
Each of the eight taught concepts appears in at least three distinct graded statements and paths.

C11 manifests 450 lesson minutes, 1,040 practice minutes, and 60 review minutes, for 1,550
minutes total.
C7 changes from 255/672/45 to 345/875/60 lesson/practice/review minutes, a 308-minute increase.
Its four sessions and 27 practices satisfy the existing double-length contract.
Plan 017 therefore adds exactly 1,858 manifested minutes = 30.97 hours.

This is deliberately calibrated against the current corpus rather than treating `length: double`
as an unlimited exemption.
The largest current units are 1,120 minutes and the largest current practice budget is 730;
C11's 1,550/1,040 is larger because it owns eight concepts and two end-to-end training systems,
but it is no longer the draft's 1,900/1,390 outlier.
Its 24 problems average 43.3 minutes, with a 75-minute maximum; the longer problems integrate
derivation, implementation, and training rather than stretching a single drill.
Splitting C11 would duplicate the forward/backward/training loop across two unit reviews and make
BatchNorm/dropout depend on a second artificial boundary, so one calibrated double-length unit is
preferred.

The corpus moves from 17 to 18 units, 130 to 139 concepts, 383 to 407 unit practices, 57 to 63
lesson sessions, 91 to 99 lesson/review/overview notebooks, and 857 to 913 unit notebooks.
Manifested time moves from 14,767 to 16,625 minutes and scheduled time from 15,007 to 16,865
minutes, including the unchanged 180-minute mock and 60-minute debrief.

The 35-week schedule keeps Semester 1 unchanged at 16 weeks / 7,915 minutes.
Semester 2 grows to 19 weeks / 8,950 minutes, inserts C11 after C6 and before C7, and keeps
`r1-001` plus its debrief at the final gate.
`curriculum/course-schedule.yaml` becomes the machine-readable schedule source.
A schedule checker reconciles every allocated session, practice minute, review minute, mock, and
debrief against the manifests and prerequisite graph and rejects a weekly total outside 450–500
minutes.
A renderer owns only sentinel-delimited numeric baseline, semester arithmetic, weekly table,
captured-total, and first-instruction/topological-order regions in `docs/course-structure.md`.
The optional-mock policy, grading guidance, and explanatory prerequisite prose outside those
markers remain human-authored and byte-preserved.

## Evidence and roadmap transition

The canonical coverage map remains the single source of audit truth.
For each of the ten rows, Plan 017 must record exact lesson anchors, at least three honest practice
references where a new taught concept is involved, disposition `keep`, empty deficits, and the
shipped destination.
`P015-R1-NEURAL-TRAINING` is removed from `planned_units` only after all eight owned targets are
checker-derived covered.
The C7 and C6 existing-unit estimates disappear only after their respective missing modalities
are present.

The Round 1 acknowledged gap count falls from 15 to 5.
The remaining rows are exactly logistic regression, SVM, decision trees, ensembles, and k-means,
all owned by Plan 018.
The Round 2 planned units that previously named `P015-R1-NEURAL-TRAINING` as a prerequisite are
retargeted to shipped `C11-neural-training` in the same atomic map change, so the roadmap graph has
no dangling planned-unit edge.

The permanent `C11` id sorts after `C10` lexically although the pedagogical schedule places it
between C6 and C7.
All schedule, prerequisite, audit, and roadmap consumers use explicit ids/edges rather than
filesystem order; the id preserves the next available core-unit number without renaming shipped
C5–C10 directories.

## Source and authorship boundary

All 24 new C11 statements and four expanded C7 statements are original.
They may use the committed derived reference analysis for register guidance but may not read or
copy raw past papers, verbatim past-problem text, student data, secrets, or ignored local
artifacts.
Statement and solution authors run in separate fresh sessions.
The blind solution author sees the final student statements but not statement-author outlines or
draft answers.

Student notebooks contain no solutions or stored outputs.
Solutions use fixed seed `20260804` where randomness is present, declare explicit tolerances,
execute top to bottom, and end with `### Answer check`.

## Verification design

Fail-first tests pin the baseline/delta counts, exact unit shapes, target transition, prerequisite
order, minutes, and remaining five-gap boundary before content exists.
The implementation then has to satisfy the real manifest, prerequisite, coverage, scope,
inventory, audit, roadmap, and course-schedule consumers; no self-reported completion flag is
accepted.

The named verification phase executes every changed solution and teaching notebook in fresh
Jupyter kernels, runs focused negative and integration tests, regenerates curriculum evidence,
and finishes with the full `scripts/ci-local.sh` gate.
A permanent training-mutation runner copies the real changed solution notebooks, applies an
exactly-once registered corruption for optimizer ordering, missing parameter updates, frozen
parameter leakage, late prediction commitment, and mode/buffer misuse, and requires each mutant
to fail its real final answer check.
The runner fails closed if a mutation target matches zero or multiple source locations or if a
mutant unexpectedly executes successfully.
The four content reviewers blind-solve all 28 changed/new statements before reading solutions.

## Out of scope

- Logistic regression, SVM, trees, ensembles, and k-means remain Plan 018.
- Attention, transformers, NLP training, CNN architectures beyond the existing C7 surface,
  object detection, generative models, and GPU workflows remain Round 2.
- The plan does not add a second mock test or rewrite `r1-001`.
- The plan does not legalize a unit overflow by changing the shared standard.
- Student's t-test and importance sampling remain explicitly optional, non-required candidates.
