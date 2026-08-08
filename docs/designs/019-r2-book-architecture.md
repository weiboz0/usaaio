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
- Book 2 has its own `curriculum/book2-schedule.yaml`: its learner-facing `book_week` numbering starts at 1, every row has a `global_week` greater than 40, and it is independently rendered, validated, and navigated.
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

The table is a one-to-one closure inventory: its 30 rows are all and only the currently missing or partial required/bridge `round-2-extension` knowledge points.
`vision-transformers` and `graph-neural-network-transformer-applications` are transformer-family targets even though Plan 021 also delivers the advanced-vision targets `object-detection` and `unet`.

## Dependency graph

```text
Book 1: C6 PyTorch, C7 CNN, C8 embeddings, C11 neural training
  └─ B2-019 Attention and Transformer Mechanics
       └─ B2-020 Language Transformers
            └─ B2-021 Cross-modal Transformers and Advanced Vision

Book 1 probability, linear algebra, calculus, C7 CNN, C11 neural training
  └─ B2-022 Probabilistic Latent Models

B2-020 + B2-021 + B2-022
  └─ B2-023 Generative Models and Diffusion

B2-020 + B2-021 + B2-022 + B2-023 + Book 1 competition craft
  └─ B2-024 GPU Scientific-ML Capstone
```

The Plan 020 embedding bridge does not re-own C8's tokenization or fixed-vector concepts.
It teaches the new Book 2 syllabus concept `embedding-model-training`, and records a controlled bridge completion for the partial `nlp-word-embeddings` knowledge point's missing `model-training` modality.
Thus a Round 2 knowledge-point requirement can reuse Book 1 evidence without falsely making its existing shipped concepts Round 2-owned.

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

## Canonical data model and ownership

`syllabus.md` and `tools.model.Unit` remain the canonical concept-ownership graph; unit manifests must match them rather than establish a parallel graph.
The Plan 019 migration gives every existing Book 1 unit explicit or backward-compatible defaults of `book: 1`, `layer: round-1-core` or `shared-foundation`, and `round: 1`.
Every Book 2 unit must declare the corresponding fields in both the syllabus unit record and its manifest.
Plan 019 also promotes the provisional Book 2 vocabulary to unique syllabus concepts before a manifest can teach it.

An illustrative Book 2 manifest therefore contains only syllabus concept IDs in `concepts_taught` and `concepts_used`:

```yaml
book: 2
layer: round-2-extension
track: extension
round: 2
prereq_units: [C6-pytorch, C7-cnn-transfer, C8-embeddings, C11-neural-training]
concepts_taught: [scaled-dot-product-attention, multi-head-attention]
concepts_used: [softmax, matrix-multiplication, autograd-training, torch-optimizers]
coverage_claims:
  - knowledge_point: attention-mechanism-foundations
    first_session: 1
    modalities: [theory, derivation, implementation]
    evidence_concepts: [scaled-dot-product-attention]
  - knowledge_point: self-attention
    first_session: 2
    modalities: [theory, implementation]
    evidence_concepts: [scaled-dot-product-attention]
```

`concepts_taught` is the concept-ownership boundary.
`concepts_used` lists only already-covered prerequisite concepts.
The canonical syllabus `prereqs` field remains the unit-ID DAG and must exactly equal manifest `prereq_units`.
Plan 019 adds a distinct canonical `concept_prerequisites` field to `Unit` and the syllabus record; it must exactly equal manifest `concepts_used` and is checked against the taught closure of `prereq_units`.
Parser and migration fixtures preserve both fields and reject either a unit-edge or concept-prerequisite mismatch.
The coverage map remains canonical for each knowledge point's requirement layer and coverage state; this is distinct from a syllabus concept's owner.
Each Book 2 `coverage_claims` row references a Round 2 knowledge point, its required modalities, and the newly taught concept evidence that closes it.
The sole exception is a partial target with Book 1 evidence: Plan 020 declares `bridge_completion: {knowledge_point: nlp-word-embeddings, missing_modalities: [model-training], new_concepts: [embedding-model-training]}`.
The checker accepts that form only for a partial Round 2 knowledge point, verifies that the listed modalities are exactly the coverage-map deficit, and credits it only after the new Book 2 concept has executable lesson and practice evidence.
Each Book 2 manifest also declares `bridge_diagnostic: {path: lessons/00-book1-bridge.ipynb, referenced_concepts: [...]}`; its referenced concepts must be a subset of `concepts_used` and disjoint from `concepts_taught`.

Every practice or computational lesson is also a closed task inventory entry, not an inference from unit-level metadata:

```yaml
compute:
  policy: optional-colab-l4  # cpu | optional-colab-l4 | gpu-required
  seed: 20260808
  cpu_smoke_solution: solutions/p03-cpu-smoke.ipynb
  accelerator_extension: practice/p03-colab-l4.ipynb
```

Every Book 2 task entry requires its policy and fixed seed.
`cpu` additionally requires a local executable correctness path, `optional-colab-l4` additionally requires that local path and an accelerator extension, and `gpu-required` additionally requires `resource_budget: {accelerator: colab-l4, runtime_minutes: ..., memory_gib: ...}`, `device_contract`, `restart_procedure`, and a distinct CPU smoke-test surrogate.
Book 1 defaults every task to `cpu` and may not opt into an accelerator.

## Assessment and compute boundary

Book 2 assessments use the `mocktests/r2-*` namespace and a distinct R2 blueprint/PDF route.
Each R2 problem manifest row carries `primary_knowledge_point` and `supporting_concepts`; the primary knowledge point must be Round 2, while supporting concepts may be existing Book 1 prerequisites.
The mock loader, blueprint validator, answer-key checker, PDF builder, hygiene checker, overlap scan, and prerequisite checker discover both `r1-*` and `r2-*` namespaces.
Book 1 problem rows have no Round 2 coverage claim and retain the existing CPU-only policy.

Each Book 2 computational task declares one of:

- `cpu`: fixed seed and a local executable correctness path with small data;
- `optional-colab-l4`: the CPU contract plus an accelerated extension;
- `gpu-required`: fixed seed, Colab L4 resource budget, device placement, memory budget, restart procedure, and CPU smoke-test surrogate.

No required lesson depends on opaque pretrained-weight downloads.
Stable Diffusion is taught through auditable components and a small seeded latent-diffusion exercise; large external models are optional demonstrations only.

## Verification contract

The implementation adds a layer-boundary check and extends existing prerequisite, coverage, schedule, hygiene, PDF, and overlap checks.
It parses `curriculum/book2-schedule.yaml` separately from the frozen Book 1 `curriculum/course-schedule.yaml` and validates `book_week: 1..total_book_weeks`, `global_week: starts_after_global_week + book_week`, Book 2 final-assessment semantics, and a non-mutating Book 1 regression.

The layer-boundary check must reject:

1. a Book 1 unit or mock that asserts a Round 2 `coverage_claim` or uses an R2 primary knowledge point;
2. a Book 2 manifest whose taught concept lacks a Book 2 syllabus owner, whose coverage claim is not a Round 2 map row, or whose required modalities lack declared evidence;
3. a bridge completion that is not a partial Round 2 target, changes existing Book 1 concept ownership, or credits more than its listed missing modalities, or a bridge diagnostic that lacks its declared path/reused-concept contract;
4. a Book 2 prerequisite or plan edge that is neither already covered nor delivered earlier in the full Book 2 DAG, including a `coverage_claim.first_session` that is not strictly after every same-unit knowledge-point dependency;
5. a Book 2 schedule whose local/global numbering, `starts_after_global_week`, or final-assessment semantics are invalid, or any mutation of Book 1's 40-week schedule;
6. an R2 mock without an R2 primary knowledge point, an R1 mock with one, or an undiscovered `r2-*` assessment artifact;
7. accelerator work in Book 1; any R2 task with no compute inventory or seed; a `cpu` task without its local correctness path; an `optional-colab-l4` task without that path or accelerator extension; or a `gpu-required` task without its budget, device/restart contract, or CPU smoke-test surrogate.

Parser and mutation fixtures cover missing/mismatched Book fields, non-syllabus concepts, invalid coverage claims, illegal bridge closure, R1/R2 assessment leakage, malformed Book 2 schedules, missing per-task GPU contracts, and undeclared GPU calls.
Permanent answer-affecting mutation suites accompany each delivery plan.
Examples include incorrect attention scaling or mask axis, faulty multi-head concatenation, broken reparameterization or KL calculation, reversed GAN update ownership, incorrect diffusion target/schedule, and invalid device placement or experiment-lineage records.

## Delivery and stop points

Each numbered plan is independently planned, reviewed, implemented, verified, and merged before any of its DAG successors begins.
Plan 019 delivers the canonical data-model migration, layer-boundary checker, Book 2 schedule/parser/render route, and their negative fixtures before creating its attention lessons and practices.
No later Book 2 unit starts until that Plan 019 foundation is merged.
Round 1 remains frozen apart from narrowly scoped shared-tooling changes that are required to enforce the two-book boundary.

## Out of scope

- Rewriting, moving, or relabelling existing Book 1 teaching material.
- Promoting optional Student's t-test or importance sampling to required content.
- Unbounded research projects, uncontrolled external datasets, raw contest content, student data, or committed opaque model weights.
