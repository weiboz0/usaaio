# Design 019 — Round 2 as Book 2

## Status

Proposed architecture for the Round 2 extension.
This design changes neither the shipped Round 1 curriculum nor the current 40-week Round 1 schedule.

## Goal

Organize every required or bridge Round 2 knowledge point as a separate Book 2 program.
Book 2 reuses Book 1 as a prerequisite graph, closes the 30 currently missing or partial Round 2 targets, and makes the Round 1 / Round 2 boundary visible to students and enforceable in content-as-code tooling.

## Decisions

- Book 1 remains the current Round 1 core course, with its existing 40-week schedule, units, mock tests, and CPU-only competition boundary.
- Book 2 is a separately scheduled Round 2 extension, not a replacement or rewrite of Book 1.
- Both books remain in one repository and use one concept DAG, manifest format, verification suite, and provenance policy.
- A Book 2 unit may use a Book 1 concept as a prerequisite but does not duplicate or re-own it.
- The Book 2 schedule begins after Book 1 Week 40 and is independently rendered, validated, and navigated.
- GPU work is permitted only when a Book 2 unit declares it.
- Student's t-test and importance sampling remain optional enrichment and are not Book 2 atomic targets.

## Program shape

Book 2 is six dependency-ordered delivery plans with a combined estimate of 142–182 hours.

| Delivery plan | Book 2 unit | Hours | Required/bridge targets closed |
|---|---|---:|---|
| 019 | Attention and Transformer Mechanics | 22–28 | attention-mechanism-foundations, self-attention, multi-head-attention, positional-encoding, attention-complexity-analysis, attention-from-scratch, transformer-architecture-foundations |
| 020 | Language Transformers | 26–32 | nlp-word-embeddings model-training completion, nlp-transformers, nlp-pretraining, nlp-fine-tuning, transformer-nlp-applications |
| 021 | Cross-modal Transformers and Advanced Vision | 22–28 | vision-transformers, graph-neural-network-transformer-applications, object-detection, unet |
| 022 | Probabilistic Latent Models | 22–28 | multivariate-gaussian, gaussian-reparameterization, kl-divergence, autoencoder, variational-autoencoder |
| 023 | Generative Models and Diffusion | 20–26 | generative-adversarial-network, denoising-diffusion-probabilistic-models, stable-diffusion |
| 024 | GPU Scientific-ML Capstone | 30–40 | gpu-colab-l4-workflow, semi-supervised-pseudo-labeling, scientific-ml-inverse-problems, mixture-parameter-regression, open-ended-experiment-design, open-ended-model-evaluation |

## Dependency graph

```text
Book 1: C6 PyTorch, C7 CNN, C8 embeddings, C11 neural training
  └─ B2-019 Attention and Transformer Mechanics
       └─ B2-020 Language Transformers
            └─ B2-021 Cross-modal Transformers and Advanced Vision

Book 1 probability, linear algebra, calculus, C7 CNN, C11 neural training
  └─ B2-022 Probabilistic Latent Models
       └─ B2-023 Generative Models and Diffusion

B2-020 + B2-021 + B2-023 + Book 1 competition craft
  └─ B2-024 GPU Scientific-ML Capstone
```

The C8 word-embedding training deficit is completed by a scoped Book 2 bridge lab.
The lab extends C8's existing conceptual owner rather than relabelling embedding use as a newly taught Book 2 topic.

## Learner-facing boundary

The generated course landing page presents two paths:

```text
Book 1 — Round 1 Core Course
  Foundations and core units through Week 40

Book 2 — Round 2 Extension Program
  Attention and Transformers
  Language Transformers
  Cross-modal Vision
  Probabilistic and Generative Models
  GPU Scientific-ML Capstone
```

Every Book 2 overview, lesson, practice, solution, and PDF carries a visible `Round 2 extension` label, its prerequisite units, and its compute policy.
An R2 unit begins with a short `Book 1 bridge` diagnostic that links to prerequisite material rather than reteaching it.

## Data model

All new unit manifests require the following additive fields:

```yaml
book: 2
layer: round-2-extension
track: extension
round: 2
prereq_units: [C6-pytorch, C7-cnn-transfer, C8-embeddings, C11-neural-training]
concepts_taught: [attention-mechanism-foundations, self-attention]
concepts_used: [softmax, matrix-multiplication, pytorch-autograd-and-optimizer-training]
compute_policy:
  baseline: cpu
  accelerator: optional-colab-l4
```

`concepts_taught` is the ownership boundary.
`concepts_used` lists only already-covered prerequisite concepts.
The coverage map remains the canonical source of each knowledge point's layer and coverage state.
Manifest metadata is cross-checked against that map rather than trusted independently.

## Assessment and compute boundary

Book 1 mocks may assess only shared-foundation or `round-1-core` concepts and retain the existing CPU-only policy.
Book 2 assessments use a distinct R2 mock/practical namespace and may assess Round 1 prerequisites only as supporting steps.
Their primary scored objective must be a Book 2 concept.

Each Book 2 computational task declares one of:

- `cpu`: executes locally with seeded small data;
- `optional-colab-l4`: has a local correctness path and an accelerated extension;
- `gpu-required`: specifies a Colab L4 resource budget, device placement, memory budget, seed, restart procedure, and CPU smoke-test surrogate.

No required lesson depends on opaque pretrained-weight downloads.
Stable Diffusion is taught through auditable components and a small seeded latent-diffusion exercise; large external models are optional demonstrations only.

## Verification contract

The implementation adds a layer-boundary check and extends existing prerequisite, coverage, schedule, hygiene, PDF, and overlap checks.

The layer-boundary check must reject:

1. a Book 1 manifest or Book 1 mock that teaches or primarily assesses a Round 2-owned concept;
2. a Book 2 manifest whose taught concept is not `round-2-extension` in the coverage map;
3. a Book 2 prerequisite that is neither already covered nor delivered earlier in the Book 2 DAG;
4. a Book 2 schedule allocation at or before Book 1 Week 40;
5. GPU-required work in Book 1 or an R2 GPU task without a declared CPU smoke-test surrogate;
6. a bridge diagnostic that claims a reused Book 1 concept as new Book 2 coverage.

Permanent answer-affecting mutation suites accompany each delivery plan.
Examples include incorrect attention scaling or mask axis, faulty multi-head concatenation, broken reparameterization or KL calculation, reversed GAN update ownership, incorrect diffusion target/schedule, and invalid device placement or experiment-lineage records.

## Delivery and stop points

Each numbered plan is independently planned, reviewed, implemented, verified, and merged before its successor begins.
No Book 2 unit starts until the layer-boundary data model and its checker are delivered with Plan 019.
Round 1 remains frozen apart from narrowly scoped shared-tooling changes that are required to enforce the two-book boundary.

## Out of scope

- Rewriting, moving, or relabelling existing Book 1 teaching material.
- Promoting optional Student's t-test or importance sampling to required content.
- Unbounded research projects, uncontrolled external datasets, raw contest content, student data, or committed opaque model weights.
