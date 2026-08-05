# Plan 014 — Enrichment Tranche (synthesis set, clinics, softmax, callbacks)

**Goal:** Ship the audit's additive findings — the cross-unit synthesis problem set (both
audit models' #1 enrichment), two error clinics, the softmax/cross-entropy teaching gap, the
bias–variance callback the syllabus promised, and two targeted items.

> Cycle pins carried from 013: sol drafts statements/sections, SEPARATE sol sessions
> blind-solve; reconciliation; **no regex prose edits — read every sentence after mechanical
> changes** (013's gate caught duplicated clauses + a dangling imperative from exactly this);
> **self-reported audits are vacuous — graded checks must derive from the real artifact**
> (013's C4-p22 lesson); tolerance contracts explicit (the guard enforces repo-wide);
> per-scope opencode gate dispatch. **Model note: all Fable slots delegate to gpt-5.6-sol
> until 2026-08-09 16:00 (user directive) — the plan-gate independent slot runs as a second,
> independent sol session.**

## Task 1 — The synthesis set (the largest item; both auditors' #1)

New top-level `synthesis/` unit-like directory (NOT a syllabus unit — no new concepts):
`synthesis/manifest.yaml` + `synthesis/problems/sNN.ipynb` + `sNN_solution.ipynb`.
**Six graded multi-unit arcs**, each tagging concepts from ≥2 units (the corpus currently has
0 of 319 cross-unit tagged problems):
- s01 F2+F3+F6: Gram matrix → spectrum → low-rank (fresh data, no C9 overlap).
- s02 F4+C2+C3: gradient → MSE surface → descent step-size regime.
- s03 F5+C5: variance-of-sums → init rule → measured explosion/vanishing.
- s04 C8+F6+C9: embeddings → SVD → neighbour damage under compression.
- s05 C1+C4+C10: imbalance → pipeline → contract → writeup (mini-arc, not a full comp).
- s06 C6+C7: module construction → truncation → parameter audit.
**Tooling (sol):** extend `tools/model.py` + prereq/coverage checks to recognise the
synthesis directory (its problems must satisfy prereq closure against the FULL taught set and
must NOT count toward any unit's ≥3 coverage — synthesis is additive, never a substitute).
`docs/unit-standards.md` gains a short "Synthesis set" section defining the contract.

## Task 2 — Error clinics (2 problems + 1 section)

- C3 (or C5) "broken descent" clinic: 5 short transcripts, one planted bug each (η too large;
  sum-vs-mean loss mismatch; gradient sign flip; un-zeroed accumulator; wrong-axis broadcast).
  Student diagnoses from the loss trace BEFORE touching code — precommit-gated verification
  cell per 013's C7-p24 precedent.
- C7 BN/eval/requires_grad three-way clinic: toggle each independently on a small
  BatchNorm trunk; which changes gradients, outputs, running buffers?

## Task 3 — softmax + cross-entropy (the top future-proofing gap)

New syllabus ids `softmax` + `cross-entropy-loss` → C5 (prereqs in-chain:
exponentials-and-logs baseline, mlp-architecture, expectation). New C5 lesson section
(logits → probabilities; the shift-invariance trick; CE as −log p_correct; why MSE is the
wrong classification loss) + 3 problems each (MC normal-form; constrained coding; one proof
of shift-invariance or the CE-gradient identity). NOTE: teaching CE does NOT introduce
training — it stays inference/analysis register per the curriculum's standing scope.

## Task 4 — Promised callbacks + targeted items

- Bias–variance callback (C9 or C5 section): revisit C1's rigid/flexible spectrum with the
  now-precise variance vocabulary + 1 problem tying evr/capacity to the train–test gap.
- F5: covariance-converse trap problem (X symmetric, Y = X²: zero covariance, dependent).
- C1: underfitting-side scenario (both scores poor and close → recommend more flexibility).

## Task 5 — Statements/solutions cycle

sol drafters (sections + statements + outlines to gitignored reference/outlines-014/);
SEPARATE sol sessions blind-solve; reconciliation; amended-statement → re-solve;
corpus duty: synthesis arcs vs the exam's integrative arc AND vs r1-001's P5 (our own mock)
— the synthesis set must not duplicate either.

## Task 6 — Verification (NAMED)

All checks incl. tolerance-check + the extended coverage/prereq (synthesis-aware) PASS;
verify-register.py passes with the new problems; ci-local ALL GREEN; every new notebook
executed; synthesis manifest validates.

## Task 7 — Ship

4-way content gate (self + codex terra + opus + glm ×2 by scope: synthesis / rest);
blind-solve ≥3 synthesis arcs per reviewer; post-exec report, TODO, PR, guard, squash-merge.

## Plan Review

### Review 1 — [claude-self] inline (2026-08-05, Opus session model)

- **Verdict**: APPROVE WITH NITS (pre-emptions applied below)
1. `[FIXED-pre-gate]` Synthesis-set counting rule made explicit in Task 1: synthesis problems
   satisfy prereq closure against the full taught set but are EXCLUDED from every unit's ≥3
   coverage tally — otherwise they could silently substitute for unit practice, which the
   013 rule exists to prevent.
2. `[FIXED-pre-gate]` Task 3 scope guard stated: teaching cross-entropy does NOT introduce
   training; problems stay in the inference/analysis register (evaluate a loss, prove
   shift-invariance) with no optimizer or backward call.
3. `[NOTED]` Model-delegation context: all Fable slots run as gpt-5.6-sol until
   2026-08-09 16:00; gate slot 3 is a second, independent sol session prompted not to
   assume slot 2's findings.

## Inherited item (from 013's gate, recorded)

**ci lesson-execution scope.** ci step 3 executes only `*_solution`/`solutions/*`, so lesson
and review notebooks — which now carry enforced tolerance contracts and whose narration must
match printed output — are never executed by ci. Plan 013 deferred this deliberately rather
than expand its own tail. **Task 0 of THIS plan decides it:** either widen step 3 to execute
lessons/reviews (accepting the runtime cost, with the warm caches already in place), or add a
narrower `lesson-execution` step behind a documented rationale. Whichever is chosen must be
recorded here with its measured runtime delta.

## Out of scope

r1-002/r1-003 generation. Training loops/optimizers (watch-list). k-means, big-O, the
R2-evidence family (attention/KL/Bayes/mixtures) — documented watch-list, revisit on evidence.
