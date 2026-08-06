# USAAIO Shipped Curriculum Syllabus

This is the currently shipped, R1-first curriculum for a high schooler whose background is
exactly **Calculus AB + basic Python**. Every concept declared in the contract below is taught
before use (enforced by `prereq-check`). The contract is not a claim that every topic in the
official Round 1 or Round 2 syllabus has shipped; audited gaps and their destinations live in
`curriculum/coverage-map.yaml` and `docs/curriculum-roadmap.md`.

**Machine-readable contract:** the YAML block immediately after the
syllabus-canonical sentinel comment below is the canonical syllabus.
Tooling parses exactly that fence; any other YAML fence in this repo is illustrative.
Narrative text refers to concepts by their vocabulary `id` so prose and YAML cannot drift.

Grounding: shipped unit scope began from the indexed 2026 Round 1 paper. The current official
and observed-source boundary is frozen in `curriculum/sources.yaml` and
`curriculum/official-topics.yaml`; the coverage map reconciles those sources with this shipped
contract.

<!-- syllabus-canonical -->
```yaml
syllabus_version: 1
baseline:   # Calc AB + basic Python allowlist — usable WITHOUT being taught
  math: [algebra, functions-and-graphs, trigonometry-basics, limits, derivatives-1d,
         chain-rule-1d, integrals-1d, exponentials-and-logs]
  python: [variables-and-types, lists-dicts-sets, control-flow, functions,
           classes-basics, file-io-basics]
clusters: [python-scientific, linear-algebra, calculus-multivar, probability-statistics,
           ml-concepts, pytorch, cnn-vision, nlp-embeddings, applied-ml, competition-craft,
           numpy]   # numpy is a distribution-level bucket: python-scientific concepts fold
                    # into it for blueprint topic accounting (blueprint cluster_fold)
concepts:
  # --- F1 ---
  - {id: numpy-arrays,              cluster: python-scientific}
  - {id: array-indexing-slicing,    cluster: python-scientific}
  - {id: broadcasting,              cluster: python-scientific}
  - {id: vectorization,             cluster: python-scientific}
  - {id: elementwise-ops,           cluster: python-scientific}
  - {id: aggregation-axis,          cluster: python-scientific}
  - {id: random-seeding,            cluster: python-scientific}
  - {id: matplotlib-basics,         cluster: python-scientific}
  # --- F2 ---
  - {id: vectors-and-norms,         cluster: linear-algebra}
  - {id: distance-metrics,          cluster: linear-algebra}
  - {id: dot-product,               cluster: linear-algebra}
  - {id: cosine-similarity,         cluster: linear-algebra}
  - {id: projection,                cluster: linear-algebra}
  - {id: residuals,                 cluster: linear-algebra}
  - {id: unit-vectors,              cluster: linear-algebra}
  - {id: orthogonality-orthonormality, cluster: linear-algebra}
  # --- F3 ---
  - {id: matrices-as-linear-maps,   cluster: linear-algebra}
  - {id: matrix-multiplication,     cluster: linear-algebra}
  - {id: rank,                      cluster: linear-algebra}
  - {id: invertibility-via-rank,    cluster: linear-algebra}
  - {id: outer-products,            cluster: linear-algebra}
  - {id: matrix-from-action,       cluster: linear-algebra}
  - {id: gram-matrices,             cluster: linear-algebra}
  - {id: linear-independence-span,  cluster: linear-algebra}
  # --- F4 ---
  - {id: partial-derivatives,       cluster: calculus-multivar}
  - {id: gradient,                  cluster: calculus-multivar}
  - {id: multivar-chain-rule,       cluster: calculus-multivar}
  - {id: sum-of-squares-gradients,  cluster: calculus-multivar}
  - {id: tanh-derivative,           cluster: calculus-multivar}
  # --- F5 ---
  - {id: random-variables,          cluster: probability-statistics}
  - {id: expectation,               cluster: probability-statistics}
  - {id: variance,                  cluster: probability-statistics}
  - {id: independence,              cluster: probability-statistics}
  - {id: variance-of-sums,          cluster: probability-statistics}
  - {id: gaussian-distribution,     cluster: probability-statistics}
  - {id: sampling-simulation,       cluster: probability-statistics}
  - {id: covariance,                cluster: probability-statistics}
  # --- F6 ---
  - {id: eigenvalues-eigenvectors,  cluster: linear-algebra}
  - {id: spectral-decomposition,    cluster: linear-algebra}
  - {id: svd,                       cluster: linear-algebra}
  - {id: singular-values,           cluster: linear-algebra}
  - {id: low-rank-approximation,    cluster: linear-algebra}
  - {id: frobenius-norm,            cluster: linear-algebra}
  # --- C1 ---
  - {id: supervised-vs-unsupervised, cluster: ml-concepts}
  - {id: clustering-concept,        cluster: ml-concepts}
  - {id: train-test-split,          cluster: ml-concepts}
  - {id: overfitting,               cluster: ml-concepts}
  - {id: bias-variance-intuition,   cluster: ml-concepts}
  - {id: accuracy-precision-recall, cluster: ml-concepts}
  - {id: f1-score,                  cluster: ml-concepts}
  - {id: f1-macro,                  cluster: ml-concepts}
  - {id: class-imbalance,           cluster: ml-concepts}
  # --- C2 ---
  - {id: linear-regression,         cluster: ml-concepts}
  - {id: mse-loss,                  cluster: ml-concepts}
  - {id: l1-regularization,         cluster: ml-concepts}
  - {id: l2-regularization,         cluster: ml-concepts}
  - {id: sparsity,                  cluster: ml-concepts}
  # --- C3 ---
  - {id: loss-surfaces,             cluster: ml-concepts}
  - {id: gradient-descent,          cluster: ml-concepts}
  - {id: learning-rate,             cluster: ml-concepts}
  - {id: stochastic-gd,             cluster: ml-concepts}
  # --- C4 ---
  - {id: knn,                       cluster: applied-ml}
  - {id: feature-scaling,           cluster: applied-ml}
  - {id: pandas-basics,             cluster: applied-ml}
  - {id: csv-data-loading,          cluster: applied-ml}
  - {id: sklearn-pipelines,         cluster: applied-ml}
  - {id: cross-validation,          cluster: applied-ml}
  - {id: tabular-feature-engineering, cluster: applied-ml}
  # --- C5 ---
  - {id: perceptron,                cluster: pytorch}
  - {id: activation-functions,      cluster: pytorch}
  - {id: threshold-activation,      cluster: pytorch}
  - {id: mlp-architecture,          cluster: pytorch}
  - {id: relu-activation,           cluster: pytorch}
  - {id: decision-boundaries-geometric, cluster: pytorch}
  - {id: weight-init-variance,      cluster: probability-statistics}
  # --- C6 ---
  - {id: python-inheritance,        cluster: python-scientific}
  - {id: torch-tensors,             cluster: pytorch}
  - {id: nn-module,                 cluster: pytorch}
  - {id: custom-layers,             cluster: pytorch}
  - {id: manual-weights,            cluster: pytorch}
  - {id: requires-grad,             cluster: pytorch}
  - {id: parameter-counting,        cluster: pytorch}
  # --- C7 ---
  - {id: convolution,               cluster: cnn-vision}
  - {id: feature-maps,              cluster: cnn-vision}
  - {id: receptive-field,           cluster: cnn-vision}
  - {id: feature-hierarchy,         cluster: cnn-vision}
  - {id: resnet-architecture,       cluster: cnn-vision}
  - {id: bottleneck-blocks,         cluster: cnn-vision}
  - {id: model-truncation,          cluster: cnn-vision}
  - {id: layer-freezing,            cluster: cnn-vision}
  - {id: transfer-learning,         cluster: cnn-vision}
  - {id: tensor-shape-tracing,      cluster: cnn-vision}
  # --- C8 ---
  - {id: tokenization,              cluster: nlp-embeddings}
  - {id: word-embeddings,           cluster: nlp-embeddings}
  - {id: embedding-matrices,        cluster: nlp-embeddings}
  - {id: similarity-matrices,       cluster: nlp-embeddings}
  - {id: nearest-neighbor-search,   cluster: nlp-embeddings}
  - {id: gensim-usage,              cluster: nlp-embeddings}
  # --- C9 ---
  - {id: pca,                       cluster: ml-concepts}
  - {id: truncated-svd-practice,    cluster: linear-algebra}
  - {id: umap-concept,              cluster: ml-concepts}
  - {id: local-vs-global-structure, cluster: ml-concepts}
  # --- C10 ---
  - {id: normal-form-answers,       cluster: competition-craft}
  - {id: api-constraint-compliance, cluster: competition-craft}
  - {id: notebook-discipline,       cluster: competition-craft}
  - {id: hidden-test-protocol,      cluster: competition-craft}
  - {id: prediction-function-contract, cluster: competition-craft}
  - {id: metric-driven-iteration,   cluster: competition-craft}
  - {id: writeup-quality,           cluster: competition-craft}
units:
  - id: F1-scientific-python
    track: foundation
    title: Scientific Python and NumPy
    prereqs: []
    teaches: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization,
              elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
  - id: F2-vectors
    track: foundation
    title: Vectors, Norms, and Projections
    prereqs: [F1-scientific-python]
    teaches: [vectors-and-norms, distance-metrics, dot-product, cosine-similarity,
              projection, residuals, unit-vectors, orthogonality-orthonormality]
  - id: F3-matrices
    track: foundation
    title: Matrices as Linear Maps
    prereqs: [F2-vectors]
    teaches: [matrices-as-linear-maps, matrix-multiplication, rank, invertibility-via-rank,
              outer-products, matrix-from-action, gram-matrices, linear-independence-span]
  - id: F4-multivar-calculus
    track: foundation
    title: Gradients from Calculus AB
    prereqs: [F2-vectors]
    teaches: [partial-derivatives, gradient, multivar-chain-rule, sum-of-squares-gradients,
              tanh-derivative]
  - id: F5-probability
    track: foundation
    title: Probability and Statistics Essentials
    prereqs: [F1-scientific-python]
    teaches: [random-variables, expectation, variance, independence, variance-of-sums,
              gaussian-distribution, sampling-simulation, covariance]
  - id: F6-svd-spectral
    track: foundation
    title: Eigenvalues, SVD, and Low-Rank Structure
    length: double   # heaviest LESSON load in the roster (425 min); splits into two sittings
    prereqs: [F3-matrices]
    teaches: [eigenvalues-eigenvectors, spectral-decomposition, svd, singular-values,
              low-rank-approximation, frobenius-norm]
  - id: C1-ml-fundamentals
    track: core
    title: Machine Learning Fundamentals
    prereqs: [F1-scientific-python]
    teaches: [supervised-vs-unsupervised, clustering-concept, train-test-split, overfitting,
              bias-variance-intuition, accuracy-precision-recall, f1-score, f1-macro,
              class-imbalance]
  - id: C2-linear-models
    track: core
    title: Linear Models and Regularization
    prereqs: [F3-matrices, F4-multivar-calculus, C1-ml-fundamentals]
    teaches: [linear-regression, mse-loss, l1-regularization, l2-regularization, sparsity]
  - id: C3-gradient-descent
    track: core
    title: Optimization by Gradient Descent
    prereqs: [F4-multivar-calculus, C2-linear-models]
    teaches: [loss-surfaces, gradient-descent, learning-rate, stochastic-gd]
  - id: C4-classical-ml-practice
    track: core
    title: Classical ML Practice with sklearn and pandas
    prereqs: [C1-ml-fundamentals, F1-scientific-python, F2-vectors, F5-probability]
    teaches: [knn, feature-scaling, pandas-basics, csv-data-loading, sklearn-pipelines,
              cross-validation, tabular-feature-engineering]
  - id: C5-neural-networks
    track: core
    title: Neural Networks from First Principles
    prereqs: [C3-gradient-descent, F5-probability]
    teaches: [perceptron, activation-functions, threshold-activation, relu-activation,
              mlp-architecture, decision-boundaries-geometric, weight-init-variance]
  - id: C6-pytorch
    track: core
    title: PyTorch Engineering
    prereqs: [C5-neural-networks]
    teaches: [python-inheritance, torch-tensors, nn-module, custom-layers, manual-weights,
              requires-grad, parameter-counting]
  - id: C7-cnn-transfer
    track: core
    title: CNNs, ResNet, and Transfer Learning
    prereqs: [C6-pytorch]
    teaches: [convolution, feature-maps, receptive-field, feature-hierarchy,
              resnet-architecture, bottleneck-blocks, model-truncation, layer-freezing,
              transfer-learning, tensor-shape-tracing]
  - id: C8-embeddings
    track: core
    title: Word Embeddings and Similarity
    prereqs: [F2-vectors, F3-matrices, F1-scientific-python]
    teaches: [tokenization, word-embeddings, embedding-matrices, similarity-matrices,
              nearest-neighbor-search, gensim-usage]
  - id: C9-dimensionality-reduction
    track: core
    title: Dimensionality Reduction
    prereqs: [F6-svd-spectral, C8-embeddings, F5-probability, C1-ml-fundamentals]
    teaches: [pca, truncated-svd-practice, umap-concept, local-vs-global-structure]
  - id: C10-competition-craft
    track: core
    title: Competition and Notebook Craft
    prereqs: [C4-classical-ml-practice]
    teaches: [notebook-discipline, hidden-test-protocol, prediction-function-contract,
              metric-driven-iteration, writeup-quality, normal-form-answers,
              api-constraint-compliance]
```

## Foundation track — rationale

`F1-scientific-python` opens the curriculum:
every later unit's practice is notebook-based, and the exam bans loops in favor of
`broadcasting`/`vectorization` (analysis: NumPy tasks with explicit API bans).
`F2-vectors` and `F3-matrices` build the linear-algebra spine —
`projection`, `residuals`, `matrix-from-action`, `outer-products`, and `gram-matrices`
appeared directly as exam sub-parts.
`F4-multivar-calculus` extends Calc AB to `gradient` and `multivar-chain-rule`,
stated component-wise (`sum-of-squares-gradients`) so no matrix calculus is needed;
`tanh-derivative` is the exam's canonical 1-D exercise.
`F5-probability` exists chiefly for `variance-of-sums` — the exam's
weight-initialization derivation — and `sampling-simulation` for dataset generation.
`F6-svd-spectral` is the flagged double-length capstone:
`svd`, `spectral-decomposition`, and `low-rank-approximation` anchored the heaviest
sub-parts of the 2026 integrative arc.

## Core track — rationale

`C1-ml-fundamentals` covers the opening concept block
(`supervised-vs-unsupervised` through `class-imbalance`);
`bias-variance-intuition` is deliberately intuitive; its statistical vocabulary
(`variance`, `expectation`) firms up in F5 and is exercised in C5's
`weight-init-variance` derivation.
`C2-linear-models` currently teaches the gradient view. The official closed-form OLS target —
normal equations, rank/identifiability conditions, and pseudoinverse behavior — is therefore
recorded as partial and assigned back to C2 in the roadmap rather than treated as unnecessary.
Fitting itself is deferred to `C3-gradient-descent`; C2 practice evaluates and
differentiates `mse-loss` for given parameters and reasons about `sparsity` —
so every C2 concept has practice without a training loop.
`C4-classical-ml-practice` teaches the `knn` + `pandas-basics` + `sklearn-pipelines`
craft that the 50-point applied problem demands;
`C10-competition-craft` turns that into exam technique
(`prediction-function-contract`, `hidden-test-protocol`).
`C5-neural-networks` → `C6-pytorch` → `C7-cnn-transfer` is the engineering ladder from
`perceptron` to `resnet-architecture` surgery.
`C8-embeddings` + `C9-dimensionality-reduction` cover the integrative-arc territory
(`similarity-matrices`, `truncated-svd-practice`).

## Suggested order (one feasible topological sort)

F1 → F2 → C1 → F4 → F3 → F5 → C4 → C2 → C3 → C5 → C6 → C7 → C8 → F6 → C9 → C10

Foundation units interleave with core units so the student reaches applied work
(C4) early — F5 precedes C4 because `feature-scaling` standardization needs `variance`;
F6 is deferred until C8 motivates it (the similarity matrix begs for SVD).

This order is the shipped path. The full architecture reuses it as shared foundation and
Round 1 core, then attaches Round 2 extensions without duplicating probability, linear
algebra, PyTorch, or other prerequisites; see `docs/curriculum-architecture.md`.
