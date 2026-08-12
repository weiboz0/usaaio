# Book 1 Syllabus

Complete Round 1 curriculum. The assumed baseline is Calculus AB and basic Python.

<!-- syllabus-canonical -->
```yaml
syllabus_version: 1
baseline:
  math:
  - algebra
  - functions-and-graphs
  - trigonometry-basics
  - limits
  - derivatives-1d
  - chain-rule-1d
  - integrals-1d
  - exponentials-and-logs
  python:
  - variables-and-types
  - lists-dicts-sets
  - control-flow
  - functions
  - classes-basics
  - file-io-basics
clusters:
- python-scientific
- linear-algebra
- calculus-multivar
- probability-statistics
- ml-concepts
- pytorch
- cnn-vision
- nlp-embeddings
- applied-ml
- competition-craft
- numpy
concepts:
- id: numpy-arrays
  cluster: python-scientific
- id: array-indexing-slicing
  cluster: python-scientific
- id: broadcasting
  cluster: python-scientific
- id: vectorization
  cluster: python-scientific
- id: elementwise-ops
  cluster: python-scientific
- id: aggregation-axis
  cluster: python-scientific
- id: random-seeding
  cluster: python-scientific
- id: matplotlib-basics
  cluster: python-scientific
- id: seaborn-programming
  cluster: python-scientific
- id: vectors-and-norms
  cluster: linear-algebra
- id: distance-metrics
  cluster: linear-algebra
- id: dot-product
  cluster: linear-algebra
- id: cosine-similarity
  cluster: linear-algebra
- id: projection
  cluster: linear-algebra
- id: residuals
  cluster: linear-algebra
- id: unit-vectors
  cluster: linear-algebra
- id: orthogonality-orthonormality
  cluster: linear-algebra
- id: matrices-as-linear-maps
  cluster: linear-algebra
- id: matrix-multiplication
  cluster: linear-algebra
- id: rank
  cluster: linear-algebra
- id: invertibility-via-rank
  cluster: linear-algebra
- id: outer-products
  cluster: linear-algebra
- id: matrix-from-action
  cluster: linear-algebra
- id: gram-matrices
  cluster: linear-algebra
- id: linear-independence-span
  cluster: linear-algebra
- id: partial-derivatives
  cluster: calculus-multivar
- id: gradient
  cluster: calculus-multivar
- id: multivar-chain-rule
  cluster: calculus-multivar
- id: sum-of-squares-gradients
  cluster: calculus-multivar
- id: tanh-derivative
  cluster: calculus-multivar
- id: random-variables
  cluster: probability-statistics
- id: expectation
  cluster: probability-statistics
- id: variance
  cluster: probability-statistics
- id: independence
  cluster: probability-statistics
- id: variance-of-sums
  cluster: probability-statistics
- id: gaussian-distribution
  cluster: probability-statistics
- id: sampling-simulation
  cluster: probability-statistics
- id: covariance
  cluster: probability-statistics
- id: conditional-probability
  cluster: probability-statistics
- id: bayes-rule
  cluster: probability-statistics
- id: hoeffding-inequality
  cluster: probability-statistics
- id: eigenvalues-eigenvectors
  cluster: linear-algebra
- id: spectral-decomposition
  cluster: linear-algebra
- id: svd
  cluster: linear-algebra
- id: singular-values
  cluster: linear-algebra
- id: low-rank-approximation
  cluster: linear-algebra
- id: frobenius-norm
  cluster: linear-algebra
- id: positive-semidefinite-matrices
  cluster: linear-algebra
- id: kernel-validity
  cluster: linear-algebra
- id: convex-sets
  cluster: linear-algebra
- id: convex-functions
  cluster: calculus-multivar
- id: first-order-optimality
  cluster: calculus-multivar
- id: lagrangians
  cluster: calculus-multivar
- id: optimization-duality
  cluster: calculus-multivar
- id: supervised-vs-unsupervised
  cluster: ml-concepts
- id: clustering-concept
  cluster: ml-concepts
- id: train-test-split
  cluster: ml-concepts
- id: overfitting
  cluster: ml-concepts
- id: bias-variance-intuition
  cluster: ml-concepts
- id: accuracy-precision-recall
  cluster: ml-concepts
- id: f1-score
  cluster: ml-concepts
- id: f1-macro
  cluster: ml-concepts
- id: class-imbalance
  cluster: ml-concepts
- id: linear-regression
  cluster: ml-concepts
- id: mse-loss
  cluster: ml-concepts
- id: l1-regularization
  cluster: ml-concepts
- id: l2-regularization
  cluster: ml-concepts
- id: sparsity
  cluster: ml-concepts
- id: linear-regression-estimator-derivation
  cluster: ml-concepts
- id: ols-rank-identifiability-and-pseudoinverse
  cluster: ml-concepts
- id: loss-surfaces
  cluster: ml-concepts
- id: gradient-descent
  cluster: ml-concepts
- id: learning-rate
  cluster: ml-concepts
- id: stochastic-gd
  cluster: ml-concepts
- id: knn
  cluster: applied-ml
- id: feature-scaling
  cluster: applied-ml
- id: pandas-basics
  cluster: applied-ml
- id: csv-data-loading
  cluster: applied-ml
- id: sklearn-pipelines
  cluster: applied-ml
- id: cross-validation
  cluster: applied-ml
- id: tabular-feature-engineering
  cluster: applied-ml
- id: perceptron
  cluster: pytorch
- id: activation-functions
  cluster: pytorch
- id: threshold-activation
  cluster: pytorch
- id: mlp-architecture
  cluster: pytorch
- id: relu-activation
  cluster: pytorch
- id: decision-boundaries-geometric
  cluster: pytorch
- id: weight-init-variance
  cluster: probability-statistics
- id: python-inheritance
  cluster: python-scientific
- id: torch-tensors
  cluster: pytorch
- id: nn-module
  cluster: pytorch
- id: custom-layers
  cluster: pytorch
- id: manual-weights
  cluster: pytorch
- id: requires-grad
  cluster: pytorch
- id: parameter-counting
  cluster: pytorch
- id: softmax
  cluster: pytorch
- id: cross-entropy-loss
  cluster: pytorch
- id: manual-backpropagation
  cluster: pytorch
- id: autograd-training
  cluster: pytorch
- id: torch-optimizers
  cluster: pytorch
- id: trained-mlp
  cluster: pytorch
- id: batch-normalization
  cluster: pytorch
- id: dropout
  cluster: pytorch
- id: convolution
  cluster: cnn-vision
- id: feature-maps
  cluster: cnn-vision
- id: receptive-field
  cluster: cnn-vision
- id: feature-hierarchy
  cluster: cnn-vision
- id: resnet-architecture
  cluster: cnn-vision
- id: bottleneck-blocks
  cluster: cnn-vision
- id: model-truncation
  cluster: cnn-vision
- id: layer-freezing
  cluster: cnn-vision
- id: transfer-learning
  cluster: cnn-vision
- id: tensor-shape-tracing
  cluster: cnn-vision
- id: cnn-training
  cluster: cnn-vision
- id: tokenization
  cluster: nlp-embeddings
- id: word-embeddings
  cluster: nlp-embeddings
- id: embedding-matrices
  cluster: nlp-embeddings
- id: similarity-matrices
  cluster: nlp-embeddings
- id: nearest-neighbor-search
  cluster: nlp-embeddings
- id: gensim-usage
  cluster: nlp-embeddings
- id: pca
  cluster: ml-concepts
- id: truncated-svd-practice
  cluster: linear-algebra
- id: umap-concept
  cluster: ml-concepts
- id: local-vs-global-structure
  cluster: ml-concepts
- id: pca-centered-covariance-eigenproblem-derivation
  cluster: ml-concepts
- id: numpy-pca-class-from-scratch
  cluster: ml-concepts
- id: pca-black-box-insufficiency
  cluster: ml-concepts
- id: normal-form-answers
  cluster: competition-craft
- id: api-constraint-compliance
  cluster: competition-craft
- id: notebook-discipline
  cluster: competition-craft
- id: hidden-test-protocol
  cluster: competition-craft
- id: prediction-function-contract
  cluster: competition-craft
- id: metric-driven-iteration
  cluster: competition-craft
- id: writeup-quality
  cluster: competition-craft
- id: colab-markdown-solution-authoring
  cluster: competition-craft
- id: markdown-code-snippets
  cluster: competition-craft
- id: markdown-math-formulae
  cluster: competition-craft
- id: colab-coding-submission
  cluster: competition-craft
- id: cpu-and-gpu-round-boundary
  cluster: competition-craft
- id: logistic-regression
  cluster: ml-concepts
- id: svm
  cluster: ml-concepts
- id: margin-and-hinge-loss
  cluster: ml-concepts
- id: decision-trees
  cluster: ml-concepts
- id: tree-split-criteria
  cluster: ml-concepts
- id: ensemble-learning
  cluster: ml-concepts
- id: bagging-and-boosting
  cluster: ml-concepts
- id: k-means
  cluster: ml-concepts
- id: lloyd-algorithm
  cluster: ml-concepts
- id: classical-model-comparison
  cluster: ml-concepts
units:
- id: F1-scientific-python
  track: foundation
  title: Scientific Python and NumPy
  prereqs: []
  teaches:
  - numpy-arrays
  - array-indexing-slicing
  - broadcasting
  - vectorization
  - elementwise-ops
  - aggregation-axis
  - random-seeding
  - matplotlib-basics
  - seaborn-programming
- id: F2-vectors
  track: foundation
  title: Vectors, Norms, and Projections
  prereqs:
  - F1-scientific-python
  teaches:
  - vectors-and-norms
  - distance-metrics
  - dot-product
  - cosine-similarity
  - projection
  - residuals
  - unit-vectors
  - orthogonality-orthonormality
- id: F3-matrices
  track: foundation
  title: Matrices as Linear Maps
  prereqs:
  - F2-vectors
  teaches:
  - matrices-as-linear-maps
  - matrix-multiplication
  - rank
  - invertibility-via-rank
  - outer-products
  - matrix-from-action
  - gram-matrices
  - linear-independence-span
- id: F4-multivar-calculus
  track: foundation
  title: Gradients from Calculus AB
  prereqs:
  - F2-vectors
  teaches:
  - partial-derivatives
  - gradient
  - multivar-chain-rule
  - sum-of-squares-gradients
  - tanh-derivative
- id: F5-probability
  track: foundation
  title: Probability and Statistics Essentials
  length: double
  prereqs:
  - F1-scientific-python
  teaches:
  - random-variables
  - expectation
  - variance
  - independence
  - variance-of-sums
  - gaussian-distribution
  - sampling-simulation
  - covariance
  - conditional-probability
  - bayes-rule
  - hoeffding-inequality
- id: F6-svd-spectral
  track: foundation
  title: Eigenvalues, SVD, and Low-Rank Structure
  length: double
  prereqs:
  - F3-matrices
  teaches:
  - eigenvalues-eigenvectors
  - spectral-decomposition
  - svd
  - singular-values
  - low-rank-approximation
  - frobenius-norm
- id: F7-kernels-convex-optimization
  track: foundation
  title: Kernel Validity and Convex Optimization
  prereqs:
  - F3-matrices
  - F4-multivar-calculus
  - F6-svd-spectral
  - C3-gradient-descent
  teaches:
  - positive-semidefinite-matrices
  - kernel-validity
  - convex-sets
  - convex-functions
  - first-order-optimality
  - lagrangians
  - optimization-duality
- id: C1-ml-fundamentals
  track: core
  title: Machine Learning Fundamentals
  prereqs:
  - F1-scientific-python
  teaches:
  - supervised-vs-unsupervised
  - clustering-concept
  - train-test-split
  - overfitting
  - bias-variance-intuition
  - accuracy-precision-recall
  - f1-score
  - f1-macro
  - class-imbalance
- id: C2-linear-models
  track: core
  title: Linear Models and Regularization
  prereqs:
  - F3-matrices
  - F4-multivar-calculus
  - C1-ml-fundamentals
  teaches:
  - linear-regression
  - mse-loss
  - l1-regularization
  - l2-regularization
  - sparsity
  - linear-regression-estimator-derivation
  - ols-rank-identifiability-and-pseudoinverse
- id: C3-gradient-descent
  track: core
  title: Optimization by Gradient Descent
  prereqs:
  - F4-multivar-calculus
  - C2-linear-models
  teaches:
  - loss-surfaces
  - gradient-descent
  - learning-rate
  - stochastic-gd
- id: C4-classical-ml-practice
  track: core
  title: Classical ML Practice with sklearn and pandas
  prereqs:
  - C1-ml-fundamentals
  - F1-scientific-python
  - F2-vectors
  - F5-probability
  teaches:
  - knn
  - feature-scaling
  - pandas-basics
  - csv-data-loading
  - sklearn-pipelines
  - cross-validation
  - tabular-feature-engineering
- id: C5-neural-networks
  track: core
  title: Neural Networks from First Principles
  prereqs:
  - C3-gradient-descent
  - F5-probability
  teaches:
  - perceptron
  - activation-functions
  - threshold-activation
  - relu-activation
  - mlp-architecture
  - decision-boundaries-geometric
  - weight-init-variance
- id: C6-pytorch
  track: core
  title: PyTorch Engineering
  prereqs:
  - C5-neural-networks
  teaches:
  - python-inheritance
  - torch-tensors
  - nn-module
  - custom-layers
  - manual-weights
  - requires-grad
  - parameter-counting
- id: C11-neural-training
  track: core
  title: Neural Network Training from Scratch to PyTorch
  length: double
  prereqs:
  - F4-multivar-calculus
  - C3-gradient-descent
  - C5-neural-networks
  - C6-pytorch
  teaches:
  - softmax
  - cross-entropy-loss
  - manual-backpropagation
  - autograd-training
  - torch-optimizers
  - trained-mlp
  - batch-normalization
  - dropout
- id: C7-cnn-transfer
  track: core
  title: CNNs, ResNet, and Transfer Learning
  length: double
  prereqs:
  - C6-pytorch
  - C11-neural-training
  teaches:
  - convolution
  - feature-maps
  - receptive-field
  - feature-hierarchy
  - resnet-architecture
  - bottleneck-blocks
  - model-truncation
  - layer-freezing
  - transfer-learning
  - tensor-shape-tracing
  - cnn-training
- id: C8-embeddings
  track: core
  title: Word Embeddings and Similarity
  prereqs:
  - F2-vectors
  - F3-matrices
  - F1-scientific-python
  teaches:
  - tokenization
  - word-embeddings
  - embedding-matrices
  - similarity-matrices
  - nearest-neighbor-search
  - gensim-usage
- id: C9-dimensionality-reduction
  track: core
  title: Dimensionality Reduction
  prereqs:
  - F6-svd-spectral
  - C8-embeddings
  - F5-probability
  - C1-ml-fundamentals
  teaches:
  - pca
  - truncated-svd-practice
  - umap-concept
  - local-vs-global-structure
  - pca-centered-covariance-eigenproblem-derivation
  - numpy-pca-class-from-scratch
  - pca-black-box-insufficiency
- id: C10-competition-craft
  track: core
  title: Competition and Notebook Craft
  prereqs:
  - C4-classical-ml-practice
  teaches:
  - notebook-discipline
  - hidden-test-protocol
  - prediction-function-contract
  - metric-driven-iteration
  - writeup-quality
  - normal-form-answers
  - api-constraint-compliance
  - colab-markdown-solution-authoring
  - markdown-code-snippets
  - markdown-math-formulae
  - colab-coding-submission
  - cpu-and-gpu-round-boundary
- id: C12-classical-models
  track: core
  title: Classical Supervised and Unsupervised Models
  length: double
  prereqs:
  - C1-ml-fundamentals
  - C2-linear-models
  - C3-gradient-descent
  - C4-classical-ml-practice
  - F7-kernels-convex-optimization
  teaches:
  - logistic-regression
  - svm
  - margin-and-hinge-loss
  - decision-trees
  - tree-split-criteria
  - ensemble-learning
  - bagging-and-boosting
  - k-means
  - lloyd-algorithm
  - classical-model-comparison
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
`F5-probability` is a double-length unit: it connects `variance-of-sums` and
`sampling-simulation` to `conditional-probability`, `bayes-rule`, and
`hoeffding-inequality`.
`F6-svd-spectral` is also a double-length unit:
`svd`, `spectral-decomposition`, and `low-rank-approximation` anchored the heaviest
sub-parts of the 2026 integrative arc.
`F7-kernels-convex-optimization` completes the shared mathematical foundation by turning
PSD structure into `kernel-validity` proofs and extending gradient intuition to
`convex-functions`, `lagrangians`, and `optimization-duality`.

## Core track — rationale

`C1-ml-fundamentals` covers the opening concept block
(`supervised-vs-unsupervised` through `class-imbalance`);
`bias-variance-intuition` is deliberately intuitive; its statistical vocabulary
(`variance`, `expectation`) firms up in F5 and is exercised in C5's
`weight-init-variance` derivation.
`C2-linear-models` session 02 ships closed-form unregularized OLS fitting and the
`linear-regression-estimator-derivation`, including rank, identifiability, and
pseudoinverse behavior.
Only iterative gradient-based fitting remains deferred to `C3-gradient-descent`.
`C4-classical-ml-practice` teaches the `knn` + `pandas-basics` + `sklearn-pipelines`
craft that the 50-point applied problem demands;
`C10-competition-craft` turns that into exam technique
(`prediction-function-contract`, `hidden-test-protocol`).
`C5-neural-networks` → `C6-pytorch` → `C11-neural-training` → `C7-cnn-transfer` is the
engineering ladder from `perceptron`, through explicit and autograd-based training, to
`resnet-architecture` surgery.
`C11-neural-training` is double-length because five sessions connect manual gradients,
NumPy training, PyTorch autograd and optimizers, BatchNorm, and dropout to 24 practices.
`C7-cnn-transfer` is also double-length: its fourth session and 27-practice register make
`cnn-training` a substantive bridge from trained MLPs to convolutional transfer learning.
`C8-embeddings` + `C9-dimensionality-reduction` cover the integrative-arc territory
(`similarity-matrices`, `truncated-svd-practice`).
`C12-classical-models` is double-length because six sessions connect logistic classification,
linear and kernel margins, trees, ensembles, clustering, and explicit model comparison to 30
ordered practices.

## Suggested order (one feasible topological sort)

F1 → F2 → C1 → F4 → F3 → F5 → C4 → C2 → C3 → C5 → C6 → C11 → C7 → C8 → F6 → F7 → C9 → C10 → C12

Foundation units interleave with core units so the student reaches applied work
(C4) early — F5 precedes C4 because `feature-scaling` standardization needs `variance`;
F6 is deferred until C8 motivates it (the similarity matrix begs for SVD); F7 follows all
four of its declared prerequisites before C9, C10, and the final classical-model unit.

This order is the shipped Book 1 path.
Book 2 imports its prerequisites through `books.yaml` without duplicating Book 1 content;
see `docs/curriculum-architecture.md`.
