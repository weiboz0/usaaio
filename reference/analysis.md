# Reference Corpus Analysis

Original derived analysis of the public USA-NA-AIO past tests.
No verbatim problem text appears in this file (public-repo policy, `decisions.md §2`);
everything below is paraphrased or structural observation.
Raw papers and the per-problem `index.yaml` files live only on machines that ran
`bash scripts/fetch-reference.sh` + the indexing step (they are gitignored).

## Sources

| Test | Source | Fetched | Local path | Indexed |
|------|--------|---------|-----------|---------|
| r1-2026 | usaaio.org/past-problems → Google Drive | 2026-08-03 | `reference/r1-2026/paper.pdf` (24 pp) | yes (24 sub-parts) |
| r2-2026 day 1 | same | 2026-08-03 | `reference/r2-2026/day1.pdf` (15 pp) | yes (light) |
| r2-2026 day 2 | same | 2026-08-03 | `reference/r2-2026/day2.pdf` (14 pp) | yes (light) |
| r2-2026 rationale | same | 2026-08-03 | `reference/r2-2026/rationale.pdf` (6 pp) | mined for design intent |
| r1-2025 | forum.beaver-edge.ai (per-part threads) | structure only | — | no |
| r2-2025 | forum.beaver-edge.ai | not fetched | — | no |

**2025 manual-export follow-up:** the 2025 R1 problems exist only as ~35+ individual forum
threads (one per problem part), not as a downloadable paper.
Visible thread titles establish the structure (below) without scraping content.
If plan 003 needs the full 2025 text, export thread-by-thread manually into
`reference/r1-2025/` using the same index schema.

## Round 1 format

**Observed sample: n=1 full paper (2026) + structural metadata for 2025.**
Fields marked (printed) appear in the paper; (external) come from the official site;
(inferred) are judgment.

- **Duration:** 180 minutes (external — official schedule 12–3pm ET; not printed in paper).
- **Total:** 300 points (printed, summed) across **9 problems / 24 gradable sub-parts** (2026).
- **2025 structural contrast:** only 3 problems, but each with many parts
  (≥8, ≥13, 18 visible) — the format varies year to year in problem-count shape while
  keeping the "few long multi-part arcs plus standalone items" texture.
- **Problem sizes (2026):** 50, 15, 10, 20, 90, 10, 30, 25, 50 points.
  One dominant multi-part arc (90 pts, 15 parts) builds a single narrative
  (embeddings → similarity → SVD → low-rank approximation);
  one open-ended applied task (50 pts) is a Kaggle-style notebook submission.
- **Answer forms (2026, by sub-part):** multiple-choice ×9 (all in the first two problems),
  code ×15-ish, short-answer/proof for the rest; roughly half the points are programming.
- **Sub-part granularity:** 5-point atoms dominate (17 of 24 sub-parts are 5 pts);
  larger sub-parts (10–15 pts) mark reasoning-heavy or integrative steps; the notebook task
  is a single 50-pt unit.
- **Scaffolding style:** later parts consume earlier parts' results explicitly
  (a computed unit vector feeds the projection part; an SVD feeds the spectral part;
  a variance derivation feeds a module's initialization).
- **Tooling surface (2026):** NumPy (with deliberate API bans: no `np.linalg`, no `@`/`.T`,
  no loops in specific tasks), PyTorch (`nn.Module` subclassing, pretrained torchvision
  ResNet50), gensim GloVe embeddings, sklearn (restricted to kNN), pandas, matplotlib.
  Starter code is provided verbatim in the paper; public datasets are pulled from an
  official HuggingFace org at runtime.
- **Grading signals (printed):** "Reasoning is required / not required" per part;
  hard zero-point penalties for violating API bans; the notebook task grades
  run-from-start-to-finish, hidden-test performance, and reasoning quality, explicitly
  not code style.

## Topic distribution (r1-2026, by sub-part count / points)

| Topic cluster | Sub-parts | Points |
|---------------|-----------|--------|
| Linear algebra (vectors, projection, rank, outer products, Gram/SVD/spectral, low-rank) | 10 | 70 |
| ML concepts (supervised vs unsupervised, regularization/sparsity, bias-variance, metrics, UMAP) | 5 | 50 |
| NumPy implementation (broadcasting-only gradients, normalization, similarity, argsort, plotting) | 6 | 45 |
| PyTorch engineering (custom modules, manual-weight MLP geometry, ResNet surgery, transfer learning) | 6 | 55 |
| Probability/statistics (variance-preserving init) | 1 | 5 |
| Calculus (tanh derivative) | 1 | 5 |
| CNN representations (feature-map depth ordering) | 1 | 10 |
| NLP/embeddings context (tokenization, cosine similarity semantics) | ~4 | 20 |
| Applied tabular ML (kNN pipeline, f1-macro, notebook craft) | 1 | 50 |

(Sub-parts overlap clusters; counts assign each to its dominant cluster. R2 topics are
tabulated separately below.)

## Difficulty profile (against the Calc AB + basic Python baseline)

- **Directly reachable from the baseline + early foundation units:** the five concept MCQs,
  tanh derivative (single-variable calculus), Python set/list semantics, basic NumPy array
  conversion. Roughly 45–55 of 300 points.
- **Reachable after a linear-algebra foundation unit** (dot products, norms, projection,
  matrix action, rank): Problems 2, 3, and the first half of Problem 5 — about 60 more points.
- **Requires dedicated curriculum beyond current foundation scope:** SVD/spectral
  decomposition/Eckart-Young (P5 back half), variance-propagation initialization (P7.2),
  ResNet internals and parameter arithmetic (P8), CNN feature hierarchy (P6),
  and end-to-end model-selection craft (P9).
  These set the ceiling: the curriculum's advanced tier must teach truncated SVD as
  low-rank approximation, weight-init variance arguments, and torchvision surgery —
  all teachable from the baseline through the DAG, but multi-unit journeys.
- **Difficulty shape:** intro sub-parts cluster at the front of each problem; each arc
  ramps within itself. Nothing requires math beyond what a Calc AB student can be taught
  (no multivariable integrals, no measure theory; matrix calculus appears only as
  first-order gradient identities).

## Style notes (for fidelity review)

- Formal-but-plain register; imperative task statements ("Compute", "Build", "Write code
  to"); explicit meta-instructions per part on whether reasoning is required and whether
  coding is allowed/needed.
- Multiple-choice items use exactly five options A–E, including a recurring
  cannot-be-determined style of distractor.
- Numeric MC answers are made unique-decodable via normal-form constraints
  (gcd conditions, sign conventions) — a distinctive USAAIO pattern.
- Programming tasks name exact function/class identifiers (snake_case functions,
  My_CamelCase modules), fix input/output shapes precisely, and enumerate banned APIs with
  a zero-points penalty clause.
- Starter code blocks are complete and runnable, pulling public assets (GloVe via gensim,
  official HuggingFace datasets).
- Sponsor footer on every page; "Page N of M" footer; problems numbered `Problem N.` with
  `Part N.M.` sub-headers and points in the header line.

## Implications

**For plan 003 (syllabus + blueprint):**
1. Blueprint should parameterize: total points 300, 3h, 8–10 problems, 20–26 gradable
   sub-parts, one long integrative arc (~30% of points), one open-ended notebook task
   (~15–17%), MC concentrated in an opening concept block, ~50% of points on programming.
2. Syllabus foundation track must cover: vectors/norms/projection → matrices/rank/outer
   products → Gram matrices → SVD → low-rank approximation; probability to variance of
   sums; single-variable calculus is assumed but chain-rule fluency must be exercised.
3. Advanced tier units needed: PyTorch nn.Module craft, CNN/ResNet architecture reading,
   transfer learning, embeddings/cosine similarity, kNN + preprocessing pipelines,
   metric selection (f1-macro) and hidden-test discipline.
4. Year-to-year variance (2025's 3-problem shape vs 2026's 9-problem shape) means the
   blueprint should fix the texture (arcs, atoms, notebook task, point budget) rather than
   an exact problem count; keep problem-count a tunable parameter.

**For plan 004 (verification tooling):**
5. `overlap-scan` should extract verbatim text from local PDFs via `pdftotext` at scan
   time (the committed analysis contains none) and compare against the local
   `index.yaml` `text:` fields; it must SKIP LOUDLY when the corpus is absent, naming
   `bash scripts/fetch-reference.sh` as the remedy.
6. `blueprint-check` tolerances should treat sub-part count and point distribution as the
   invariants, not problem count (see implication 4).

## Round 2 shape and topics (light index; out of current scope)

**r2-2026:** two in-person days, 300 printed points, 5 problems, 26 gradable sub-parts;
no duration printed in either paper.
Structure: each day pairs one long scaffolded "non-open-ended" arc with open-ended
model-building tasks — day 1: a 90-pt 14-part linear-attention arc + a 70-pt open-ended
inverse-problem (recovering a central field from vector-field observations);
day 2: a 50-pt 9-part diffusion-models arc + two open-ended tasks
(40-pt image-shape classification, 50-pt mixture-function parameter regression).
Open-ended work carries 160/300 points — a much higher open-ended share than Round 1.
A published rationale document states per-problem design intent (indexed as
`design_intent:` fields).

Topic clusters beyond the Round 1 surface: transformers/attention (incl. linear attention,
positional encoding, kernel feature maps, complexity analysis), diffusion models
(Gaussian reparameterization, KL divergence, induction/limit arguments),
scientific-ML inverse problems, semi-supervised/latent-variable ideas, and
curve-fitting/mixture parameter estimation.
Relevance to this project now: Round 2 marks the difficulty ceiling the strongest units
could point toward, and its rationale doc is a model for our own mock-test
design-intent records; otherwise deferred.
