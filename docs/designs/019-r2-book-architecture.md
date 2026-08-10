# Design 019 — Round 2 as Book 2

## Status

Approved architecture amended on 2026-08-10 to make Book 1 and Book 2 physically separate, complete book roots.
The amendment supersedes the earlier shared-root `units/`, `curriculum/`, `mocktests/`, `reference/`, and `syllabus.md` layout.

## Goal

Organize Round 1 and Round 2 as two complete books in one repository.
Each book owns its syllabus, curriculum contracts, units, assessments, reference namespace, learner documentation, and build artifacts.
Shared tooling discovers books through one explicit registry and enforces the dependency from Book 2 to Book 1 without creating a second source of truth.

## Decisions

- Book 1 remains the current 40-week Round 1 course and retains its existing unit, concept, problem, and assessment IDs.
- Book 2 is a separately scheduled Round 2 program that closes the 30 currently missing or partial required or bridge targets.
- The migration is an atomic cutover, not a dual-read transition or symlink facade.
- Root-level content paths become forbidden after the cutover.
- `books.yaml` is the only repository-level book registry.
- Each book is independently loadable, verifiable, renderable, and buildable.
- Book 2 may explicitly import Book 1 prerequisites, but it may not duplicate or re-own them.
- Shared `tools/` and `scripts/` operate on an explicit book root or on all registered books.
- GPU work is permitted only in Book 2 when a task declares and satisfies its compute contract.
- Student's t-test and importance sampling remain optional enrichment and are not Book 2 atomic targets.

## Canonical repository layout

```text
usaaio/
├── books.yaml
├── book1/
│   ├── syllabus.md
│   ├── curriculum/
│   │   ├── course-schedule.yaml
│   │   ├── coverage-map.yaml
│   │   ├── material-inventory.yaml
│   │   ├── official-topics.yaml
│   │   └── source-manifest.yaml
│   ├── units/
│   ├── mocktests/
│   │   ├── blueprint.yaml
│   │   └── r1-001/
│   ├── reference/
│   ├── docs/
│   │   └── course-structure.md
│   └── build/
├── book2/
│   ├── syllabus.md
│   ├── curriculum/
│   │   ├── course-schedule.yaml
│   │   ├── coverage-map.yaml
│   │   ├── material-inventory.yaml
│   │   ├── official-topics.yaml
│   │   └── source-manifest.yaml
│   ├── units/
│   ├── mocktests/
│   │   ├── blueprint.yaml
│   │   └── r2-*/
│   ├── reference/
│   ├── docs/
│   │   └── course-structure.md
│   └── build/
├── tools/
├── scripts/
└── docs/
    ├── architecture/
    ├── audits/
    ├── designs/
    ├── plans/
    └── reviews/
```

The shared `docs/` tree contains repository governance and cross-book reports only.
Student-facing course documents belong to the book that produces them.
Generated PDFs and other build products belong under the producing book's `build/` directory.

## Book registry and discovery

`books.yaml` declares every valid book root and its dependency edges.

```yaml
books_version: 1
books:
  - id: book1
    number: 1
    root: book1
    depends_on: []
  - id: book2
    number: 2
    root: book2
    depends_on: [book1]
```

The registry rejects duplicate IDs, duplicate numbers, duplicate or escaping roots, unknown dependencies, dependency cycles, symlinked roots, and undeclared `book*/` directories.
Loaders never discover content by falling back to a root-level legacy path.
Commands accept `--book book1`, `--book book2`, or `--all` when a combined operation is meaningful.

## Atomic Book 1 migration

Plan 019 moves the existing Book 1 source tree with history-preserving Git moves.

- `syllabus.md` moves to `book1/syllabus.md`.
- `curriculum/` moves to `book1/curriculum/`, except cross-book reports that are regenerated under shared `docs/`.
- `units/` moves to `book1/units/`.
- `mocktests/` moves to `book1/mocktests/`.
- Round 1 reference material moves to `book1/reference/`.
- Round 2 reference material moves to `book2/reference/`.
- Book 1 learner documents move to `book1/docs/`.
- Book 1 generated artifacts move to `book1/build/`.

After the cutover, root-level `syllabus.md`, `curriculum/`, `units/`, `mocktests/`, `reference/`, and learner-facing course-structure files are invalid.
The pre-merge guard and CI reject their reintroduction.
There is no compatibility symlink, copy, or dual-write period.

## Book 2 program shape

Book 2 is six dependency-ordered delivery units with a combined estimate of 142–182 hours.

| Delivery plan | Book 2 unit | Hours | Required or bridge targets closed |
|---|---|---:|---|
| 019 | B2-019 Attention and Transformer Mechanics | 22–28 | attention-mechanism-foundations, self-attention, multi-head-attention, positional-encoding, attention-complexity-analysis, attention-from-scratch, transformer-architecture-foundations |
| 020 | B2-020 Language Transformers | 26–32 | nlp-word-embeddings model-training completion, nlp-transformers, nlp-pretraining, nlp-fine-tuning, transformer-nlp-applications |
| 021 | B2-021 Cross-modal Transformers and Advanced Vision | 22–28 | vision-transformers, graph-neural-network-transformer-applications, object-detection, unet |
| 022 | B2-022 Probabilistic Latent Models | 22–28 | multivariate-gaussian, gaussian-reparameterization, kl-divergence, autoencoder, variational-autoencoder |
| 023 | B2-023 Generative Models and Diffusion | 20–26 | generative-adversarial-network, denoising-diffusion-probabilistic-models, stable-diffusion |
| 024 | B2-024 GPU Scientific Modeling Capstone | 30–40 | gpu-colab-l4-workflow, semi-supervised-pseudo-labeling, scientific-ml-inverse-problems, mixture-parameter-regression, open-ended-experiment-design, open-ended-model-evaluation |

The table is a one-to-one closure inventory for all 30 missing or partial `round-2-extension` targets.

## Dependency graph

```text
book1:C6 + book1:C7 + book1:C8 + book1:C11
  └─ book2:B2-019
       └─ book2:B2-020
            └─ book2:B2-021

book1 probability + linear algebra + calculus + C7 + C11
  └─ book2:B2-022

B2-020 + B2-021 + B2-022
  └─ book2:B2-023

B2-020 + B2-021 + B2-022 + B2-023 + book1:C10
  └─ book2:B2-024
```

Cross-book references use qualified identities such as `book1:C6-pytorch` and `book1:softmax` at the registry boundary.
Inside one book, existing local IDs remain unchanged.
The loader resolves a qualified import only through the dependency graph in `books.yaml`.

## Syllabus, ownership, and imports

Each book's `syllabus.md` is authoritative only for concepts and units owned by that book.
Book 1 owns the existing Round 1 concepts and units.
Book 2 owns only new Round 2 concepts and `B2-*` units.

Book 2 declares its Book 1 dependencies explicitly.

```yaml
imports:
  book: book1
  units: [C6-pytorch, C7-cnn-transfer, C8-embeddings, C11-neural-training]
  concepts: [softmax, matrix-multiplication, autograd-training, torch-optimizers]
```

An imported concept may appear in `concepts_used` but never in Book 2 `concepts_taught`.
A Book 2 manifest's `prereq_units` and `concept_prerequisites` must exactly match its declared and transitively valid imports.
The Plan 020 embedding bridge teaches the new Book 2 concept `embedding-model-training` and does not re-own Book 1 tokenization or fixed-vector concepts.

## Book-local schedules and assessment

`book1/curriculum/course-schedule.yaml` remains the canonical 40-week Round 1 schedule.
`book2/curriculum/course-schedule.yaml` uses local `book_week` numbering beginning at 1 and records its display-only `global_week` offset after Book 1.
Neither schedule loader reads manifests from the other book.
Combined navigation may display the global offset, but each book reconciles only its own lessons, practices, reviews, and assessments.

Book 1 assessments remain under `book1/mocktests/r1-*` and use `book1/mocktests/blueprint.yaml`.
Book 2 assessments use `book2/mocktests/r2-*` and `book2/mocktests/blueprint.yaml`.
Answer-key, hygiene, PDF, overlap, and prerequisite checks operate per book before any cross-book report is generated.

## Learner-facing completeness

Each book builds its own landing document and PDF collection.
Book 1 remains usable without Book 2.
Book 2 is a complete Round 2 program but declares Book 1 as a prerequisite book rather than copying Book 1 lessons.
Every Book 2 unit starts with a `Book 1 bridge` diagnostic that links to qualified prerequisite units and identifies remediation paths.
Every Book 2 overview, lesson, practice, solution, and PDF visibly states `Round 2 extension`, its prerequisite imports, and its compute policy.

## Compute contract

Book 1 remains CPU-only.
Every Book 2 computational task declares one of `cpu`, `optional-colab-l4`, or `gpu-required` and a fixed seed.
`cpu` requires a local executable correctness path.
`optional-colab-l4` requires that path plus an accelerator extension.
`gpu-required` additionally requires a Colab L4 resource budget, device contract, restart procedure, and distinct CPU smoke-test surrogate.
No required lesson depends on opaque pretrained-weight downloads.

## Verification contract

CI first validates `books.yaml`, then validates each book independently, then validates cross-book imports and aggregate reports.
The migration and permanent checks reject:

1. any forbidden root-level content path after cutover;
2. any loader or renderer that silently falls back to a legacy root path;
3. any Book 1 output, count, schedule, or answer changed by adding a valid Book 2 fixture;
4. any Book 2 artifact discovered by a Book 1-only command, or the reverse;
5. any unqualified, undeclared, cyclic, later-layer, or ownership-changing cross-book import;
6. any concept or unit owned by more than one book;
7. any Book 1 artifact asserting Round 2 coverage or accelerator work;
8. any Book 2 manifest with invalid ownership, evidence, schedule, assessment, or compute contracts;
9. any undiscovered `r1-*` or `r2-*` assessment artifact inside its registered book;
10. any generated inventory, roadmap, course structure, or PDF written outside its registered book root.

Mutation fixtures copy both minimal book roots and prove that `--book book1`, `--book book2`, and `--all` observe the correct isolation boundary.
Clean-checkout verification proves that Git moves, generated paths, PDF inputs, reference discovery, and CLI defaults work without untracked legacy files.

## Migration sequencing

The architecture amendment invalidates Plan 019's earlier shared-root plan-review verdict and pauses Phase 2 implementation.
Plan 019 is rewritten and receives a new four-way plan-review gate before any migration or schedule work resumes.
The revised plan performs the atomic Book 1 move and book-registry migration before creating Book 2 teaching content.
Every existing producer and consumer is migrated in the same plan, including tools, scripts, tests, generated documents, reference mounts, PDF paths, and pre-merge collision checks.
No later Book 2 delivery plan starts until the two-book cutover and B2-019 are merged.

## Out of scope

- Rewriting or relabelling the pedagogical content inside existing Book 1 notebooks.
- Changing Book 1 unit, concept, practice, or assessment IDs.
- Maintaining compatibility symlinks, duplicate content roots, or permanent legacy-path aliases.
- Promoting optional Student's t-test or importance sampling to required content.
- Unbounded research projects, uncontrolled external datasets, raw contest content, student data, or committed opaque model weights.
