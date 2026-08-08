# Curriculum Architecture

USAAIO should use **one layered curriculum graph with two exit gates**, not separate Round 1
and Round 2 copies of the teaching materials.

```text
shared/reusable nodes --+
                        +-> dependency-closed Round 1 core -> R1 exit assessment
                        |                                  |
                        +----------------------------------+-> Round 2 extension
                                                              -> R2 capstone / GPU practice
```

The shared graph keeps probability, linear algebra, calculus, scientific Python, model
evaluation, and PyTorch fundamentals authoritative in one place. Round 2 units consume those
nodes and add attention, transformers, advanced vision, generative modeling, and open-ended
GPU work. They do not create a second version of the same prerequisites.
Layer labels describe reuse and exit scope, not a promise that every shared node is taught
before every Round 1 core node; the explicit dependency DAG determines teaching order. A
Round-2-extension topic may already be shipped early in the current course, as with C8
tokenization and word embeddings. Exit membership always comes from official `required_for`,
not from the unit's calendar position.

## Contracts and exits

`syllabus.md` is the shipped-content contract: its concepts and units exist now and must obey
prerequisite and practice gates. `curriculum/coverage-map.yaml` is the planning contract: it
records every official or observed atomic target as covered, partial, or missing and assigns
each gap exactly one destination. `docs/curriculum-roadmap.md` and the coverage audit are
generated views of that map, except for the four plainly labelled renderer-owned editorial
hour estimates whose schema promotion remains future work.

The Round 1 exit includes every target officially required for Round 1, whether it belongs to
shared foundation or Round 1 core. Passing a single indexed paper is not the definition of
that exit. The Round 2 exit includes the Round 1 foundation plus the official Round 2-only
targets and GPU execution policy, then the observed integration capabilities.

## Systematic topic decisions

- Gaussian probability is already taught and practised. Bayes' rule and Hoeffding's inequality
  are official gaps; conditional probability is their necessary prerequisite bridge. Gaussian
  proximity covers none of them. Student's t distribution and t-tests are coherent optional
  enrichment, but neither the official sources nor current consumers make them required.
- Linear regression is taught through MSE and gradient descent. The officially required
  closed-form estimator derivation is missing; rank/identifiability and pseudoinverse behavior
  are separate closure bridges assigned to the existing linear-model unit.
- SVD-based PCA is taught. The centered-covariance eigenproblem derivation and a reusable NumPy
  PCA class remain partial targets assigned to the dimensionality-reduction unit.
- Manual neural forward propagation is already covered. Official backpropagation/from-scratch
  training plus softmax/cross-entropy objective bridges, autograd/optimizers, BatchNorm
  completion, and dropout form the dependency-ordered neural-training tranche.
- The transformer architecture target includes LayerNorm, residual connections, and the
  position-wise feed-forward block; BatchNorm is not treated as a transformer prerequisite.
- The observed Round 2 capstone layer includes semi-supervised/pseudo-label learning alongside
  inverse problems and mixture-parameter regression, because the indexed paper assesses each
  as an integrative capability.
- Past-paper-only targets promoted to required status carry an explicit acceptance marker in
  `curriculum/official-topics.yaml`: repeated R1 integration or an integral role in the indexed
  R2 attention arc. Single-paper integration families remain labelled as bridges.
- Importance sampling is not an official or observed requirement and has no current consumer.
  It remains optional until a probabilistic-modeling unit needs proposal distributions and
  weighted estimators.

## Capacity and promotion rule

The validated 40-week schedule has no silent extension capacity: its only 240-minute difference
between manifested and scheduled totals is the final mock plus debrief, not slack.
The margin below 500 minutes in an individual week is recovery buffer, not unallocated
curriculum capacity.
A Round 1 addition must explicitly replace scheduled work or extend the calendar. A planned topic becomes
shipped only when its concept enters the syllabus, its lesson and required modalities ship,
and at least three honest unit practices exercise it; the coverage map and shipped contract
must change atomically.
