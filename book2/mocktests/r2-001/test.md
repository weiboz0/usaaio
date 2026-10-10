---
test: r2-001
round: 2
days: 2
day_duration_minutes: 240
total_points: 300
instructions:
  - The test has two days of 240 minutes each; work only on that day's problems during each day.
  - Answer every part; follow each part's reasoning, coding, normal-form, identifier, and API requirements exactly.
  - Unless a part states otherwise, give exact values rather than decimal approximations.
  - Use only Python's standard library, NumPy, and PyTorch on a CPU, and only the data shipped in data/; no web, downloads, external data, or pretrained weights.
  - Open-ended problems call final_test_score exactly once and respect their step budget and time limit.
points_by_section:
  d1-arc: 90
  d1-open: 70
  d2-arc: 50
  d2-open: 90
time_budget:
  1:
    d1-arc: 120
    d1-open: 120
  2:
    d2-arc: 80
    d2-open: 160
---

# USAAIO Mock Test r2-001 — Round 2

**Two days · 240 minutes per day · Total: 300 points · Five problems · 25 graded parts**

## Instructions

1. The test runs over two days of 240 minutes each.
   Day 1 is Problems 1 and 2; Day 2 is Problems 3, 4, and 5.
   Work only on the current day's problems.
2. Answer every part.
   Follow each part's reasoning (*Reasoning is required* / *not required*), coding (*Coding is allowed* / *not allowed*), normal-form, exact-identifier, and API requirements.
   A part that uses a banned API scores zero.
3. Unless a part states otherwise, give exact values rather than decimal approximations.
   Multiple-choice parts have five options, exactly one correct.
4. Tools: Python's standard library, NumPy, and PyTorch, on a CPU.
   Use only the data in `data/`, loaded by the code cells provided; no web access, downloads, external datasets, model hubs, or pretrained weights.
   Seeds are fixed (`SEED = 20261101`); keep every seeding line the statements give.
5. Every formula you need is defined in the statements.
   Problems 1 and 3 each begin with a shared setup that all their parts use; later parts use earlier results, so work the parts in order.
6. Problems 2, 4, and 5 are open-ended.
   Each reads its data only through `data/r2_001_data.py`, keeps training, validation, and locked-test rows in their stated roles, wraps every optimizer in the problem's `StepBudget`, and calls `final_test_score` exactly once.
   Each is graded 60% on the test score (tiers relative to the printed baseline score B and reference score R) and 40% on a four-part writeup.
   Each also has an optional `Accelerator extension` for a Colab L4 GPU; it is never graded.
7. Submit the notebooks so that each runs top to bottom in a fresh kernel without errors.

## Day 1 (240 minutes)

| Problem | Section | Parts | Points | Suggested time | Where |
|---|---|---:|---:|---:|---|
| 1. A tiny causal language model, end to end | d1-arc (scaffolded arc) | 14 | 90 | 120 min | `theory/p01.md` (Parts 1.1–1.10, 1.14) and `problems/p01.ipynb` (Parts 1.11–1.13) |
| 2. Two-source heat localization | d1-open (open-ended) | 1 | 70 | 120 min | `problems/p02.ipynb` |

## Day 2 (240 minutes)

| Problem | Section | Parts | Points | Suggested time | Where |
|---|---|---:|---:|---:|---|
| 3. A β-weighted variational autoencoder | d2-arc (scaffolded arc) | 8 | 50 | 80 min | `theory/p03.md` (Parts 3.1–3.4) and `problems/p03.ipynb` (Parts 3.5–3.8) |
| 4. Texture patches with five percent of the labels | d2-open (open-ended) | 1 | 40 | 70 min | `problems/p04.ipynb` |
| 5. Reading two Lorentzian peaks | d2-open (open-ended) | 1 | 50 | 90 min | `problems/p05.ipynb` |

## Points by section

| Section | Day | Kind | Problems | Points |
|---|---:|---|---|---:|
| d1-arc | 1 | scaffolded arc | 1 | 90 |
| d1-open | 1 | open-ended | 2 | 70 |
| d2-arc | 2 | scaffolded arc | 3 | 50 |
| d2-open | 2 | open-ended | 4, 5 | 90 |
| **Total** | | | | **300** |

Open-ended work carries 160 of the 300 points.
