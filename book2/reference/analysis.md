# Reference Corpus Analysis

Original derived analysis of the public USA-NA-AIO past tests.
No verbatim problem text appears in this file (public-repo policy, `decisions.md §2`);
everything below is paraphrased or structural observation.
Raw papers and the per-problem `index.yaml` files live only on machines that ran
`bash scripts/fetch-reference.sh --book book2` plus the indexing step (they are gitignored).

## Sources

| Test | Source | Fetched | Local path | Indexed |
|------|--------|---------|-----------|---------|
| r2-2026 day 1 | same | 2026-08-03 | `book2/reference/r2-2026/day1.pdf` (15 pp) | yes (light) |
| r2-2026 day 2 | same | 2026-08-03 | `book2/reference/r2-2026/day2.pdf` (14 pp) | yes (light) |
| r2-2026 rationale | same | 2026-08-03 | `book2/reference/r2-2026/rationale.pdf` (6 pp) | mined for design intent |
| r2-2025 | forum.beaver-edge.ai | not fetched | — | no |

## Round 2 shape and topics

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
These findings define Book 2's advanced curriculum surface and mock-test structure.
The rationale document also supplies a model for Book 2 mock-test design-intent records.

## Round 2 shape notes

Structure only; no 2026 topic, task, or wording is carried into the blueprint.
`book2/mocktests/blueprint.yaml` encodes these observations.

- **Days and totals.** Two in-person days; 300 printed points; 5 problems; 26 gradable sub-parts.
  No duration is printed, so the blueprint's 240 minutes per day is an external assumption.
- **Day pattern.** Each day opens with one long scaffolded arc (non-open-ended) and then gives open-ended model-building work.
- **Section anchors.** Day 1: a 90-point arc plus one 70-point open-ended task.
  Day 2: a 50-point arc plus two open-ended tasks of 40 and 50 points.
- **Open-ended share.** 160/300 (0.53); the blueprint band is 0.45–0.60.
- **Arc texture.** Arcs are long chains of short sub-parts in which later parts consume earlier results; the day-1 arc has roughly 14 sub-parts and the day-2 arc roughly 9.
  Round 2 arcs typically introduce one fresh mechanism inside the arc; mock tests after r2-001 should lean that way.
- **Open-ended texture.** Each open-ended task names a metric, supplies data and a baseline, and is graded on a held-out score plus a written account.
- **Sample size.** n = 1 fully indexed paper; every range is provisional.
