# Reference Corpus Analysis

Original derived analysis of the public USA-NA-AIO past tests.
No verbatim problem text appears in this file (public-repo policy, `decisions.md §2`);
everything below is paraphrased or structural observation.
Raw papers and the per-problem `index.yaml` files live only on machines that ran
`bash scripts/fetch-reference.sh` + the indexing step (they are gitignored).

## Sources

| Test | Source | Fetched | Local path | Indexed |
|------|--------|---------|-----------|---------|
| r2-2026 day 1 | same | 2026-08-03 | `reference/r2-2026/day1.pdf` (15 pp) | yes (light) |
| r2-2026 day 2 | same | 2026-08-03 | `reference/r2-2026/day2.pdf` (14 pp) | yes (light) |
| r2-2026 rationale | same | 2026-08-03 | `reference/r2-2026/rationale.pdf` (6 pp) | mined for design intent |
| r2-2025 | forum.beaver-edge.ai | not fetched | — | no |

## Round 2 shape and topics (light index; out of current scope)

**r2-2026:** two in-person days, 300 printed points, 5 problems, 26 gradable sub-parts;
no duration printed in either paper.
Structure: each day pairs one long scaffolded "non-open-ended" arc with open-ended
model-building tasks — day 1: a 90-pt 14-part linear-attention arc + a 70-pt open-ended
inverse-problem (reconstructing a single-source force field given measured field vectors);
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
