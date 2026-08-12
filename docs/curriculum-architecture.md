# Curriculum Architecture

USAAIO uses **two separately complete book roots linked by qualified imports**.
The split follows the student's two-stage progression without copying shared prerequisites.

```text
books.yaml
├── book1/  complete Round 1 course → r1-* assessments
└── book2/  complete Round 2 course → r2-* assessments
      └── qualified prerequisite and evidence imports from book1/
```

Book 1 keeps probability, linear algebra, calculus, scientific Python, model evaluation,
and PyTorch fundamentals authoritative in one place.
Book 2 declares Book 1 as a prerequisite book, consumes only its persisted import allowlists,
and adds attention, transformers, advanced vision, generative modeling, and open-ended GPU work.
It does not create a second version of the same prerequisites.
Layer labels describe reuse and exit scope, not a promise that every shared node is taught
before every Round 1 core node; each book's explicit dependency DAG determines teaching order.
An official Round 2 target may already be covered by qualified Book 1 evidence, as with C8
tokenization and word embeddings, without transferring its concept ownership to Book 2.
Exit membership always comes from official `required_for`, not from calendar position.

## Contracts and exits

`books.yaml` is the registry contract.
Within each registered root, `syllabus.md` is the shipped-content contract and
`curriculum/coverage-map.yaml` is the planning contract.
Book-local checks never scan a sibling root.
Book 2 resolves Book 1 units, concepts, and evidence only through its exact qualified
`imports` and `evidence_imports` syllabus blocks.
`docs/curriculum-roadmap.md` and the coverage audit are shared generated views over the
registered books; they are never a third source of truth.

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
  the owning book's `curriculum/official-topics.yaml`: repeated R1 integration or an integral role in the indexed
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
