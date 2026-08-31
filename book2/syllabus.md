# Book 2 Syllabus

Complete Round 2 extension curriculum. Book 1 is a declared prerequisite dependency; no Book 1 content is duplicated here.

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
- attention-transformers
- language-transformers
imports:
  book: book1
  units:
  - F1-scientific-python
  - F2-vectors
  - F3-matrices
  - F5-probability
  - C6-pytorch
  - C7-cnn-transfer
  - C8-embeddings
  - C11-neural-training
  concepts:
  - numpy-arrays
  - broadcasting
  - vectorization
  - elementwise-ops
  - aggregation-axis
  - random-seeding
  - dot-product
  - matrix-multiplication
  - expectation
  - variance
  - independence
  - variance-of-sums
  - torch-tensors
  - nn-module
  - requires-grad
  - tensor-shape-tracing
  - softmax
  - cross-entropy-loss
  - torch-optimizers
  - autograd-training
evidence_imports:
  book: book1
  concepts:
  - tokenization
  - word-embeddings
  - gensim-usage
  - embedding-matrices
  lesson_paths:
  - units/C8-embeddings/lessons/01-tokens-and-embeddings.ipynb
  practices:
  - C8-p01
  - C8-p02
  - C8-p05
  - C8-p06
  - C8-p12
  - C8-p13
  - C8-p15
  - C8-p17
  assessments:
  - r1-001-p05-1
  - r1-001-p05-2
  - r1-001-p05-3
  - r1-001-p05-4
concepts:
- id: matrix-transpose
  cluster: attention-transformers
- id: query-key-value-attention
  cluster: attention-transformers
- id: scaled-dot-product-attention
  cluster: attention-transformers
- id: attention-mask
  cluster: attention-transformers
- id: causal-self-attention
  cluster: attention-transformers
- id: multi-head-attention
  cluster: attention-transformers
- id: sinusoidal-positional-encoding
  cluster: attention-transformers
- id: attention-complexity
  cluster: attention-transformers
- id: transformer-residual-layernorm
  cluster: attention-transformers
- id: position-wise-feed-forward
  cluster: attention-transformers
- id: transformer-block
  cluster: attention-transformers
- id: embedding-model-training
  cluster: language-transformers
- id: learned-token-embedding
  cluster: language-transformers
- id: language-transformer
  cluster: language-transformers
- id: causal-language-modeling
  cluster: language-transformers
- id: masked-language-modeling
  cluster: language-transformers
- id: nlp-pretraining-objectives
  cluster: language-transformers
- id: nlp-fine-tuning-protocol
  cluster: language-transformers
- id: transformer-nlp-task-design
  cluster: language-transformers
units:
- id: B2-019-attention-transformers
  track: extension
  title: Attention and Transformer Mechanics
  book: 2
  layer: round-2-extension
  round: 2
  prereqs:
  - book1:C6-pytorch
  - book1:C7-cnn-transfer
  - book1:C8-embeddings
  - book1:C11-neural-training
  concept_prerequisites:
  - book1:numpy-arrays
  - book1:broadcasting
  - book1:vectorization
  - book1:elementwise-ops
  - book1:aggregation-axis
  - book1:random-seeding
  - book1:dot-product
  - book1:matrix-multiplication
  - book1:expectation
  - book1:variance
  - book1:independence
  - book1:variance-of-sums
  - book1:torch-tensors
  - book1:nn-module
  - book1:requires-grad
  - book1:tensor-shape-tracing
  - book1:softmax
  - book1:cross-entropy-loss
  - book1:torch-optimizers
  - book1:autograd-training
  teaches:
  - matrix-transpose
  - query-key-value-attention
  - scaled-dot-product-attention
  - attention-mask
  - causal-self-attention
  - multi-head-attention
  - sinusoidal-positional-encoding
  - attention-complexity
  - transformer-residual-layernorm
  - position-wise-feed-forward
  - transformer-block
  length: double
- id: B2-020-language-transformers
  track: extension
  title: Language Transformers
  book: 2
  layer: round-2-extension
  round: 2
  prereqs:
  - book1:F1-scientific-python
  - book1:F3-matrices
  - book1:C6-pytorch
  - book1:C7-cnn-transfer
  - book1:C11-neural-training
  - B2-019-attention-transformers
  concept_prerequisites:
  - attention-mask
  - causal-self-attention
  - sinusoidal-positional-encoding
  - transformer-block
  - book1:random-seeding
  - book1:matrix-multiplication
  - book1:torch-tensors
  - book1:nn-module
  - book1:requires-grad
  - book1:tensor-shape-tracing
  - book1:softmax
  - book1:cross-entropy-loss
  - book1:torch-optimizers
  - book1:autograd-training
  teaches:
  - embedding-model-training
  - learned-token-embedding
  - language-transformer
  - causal-language-modeling
  - masked-language-modeling
  - nlp-pretraining-objectives
  - nlp-fine-tuning-protocol
  - transformer-nlp-task-design
  length: double
```
