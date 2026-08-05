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
**Six graded multi-unit arcs**, each tagging concepts from ≥2 units (no UNIT PRACTICE problem is cross-unit tagged — 0 of
337; note mock test r1-001 does carry 19 multi-unit problems, so the gap is specifically in
the practice corpus, not the assessment corpus):
- s01 F2+F3+F6: Gram matrix → spectrum → low-rank (fresh data, no C9 overlap).
- s02 F4+C2+C3: gradient → MSE surface → descent step-size regime.
- s03 F5+C5: variance-of-sums → init rule → measured explosion/vanishing.
- s04 C8+F6+C9: embeddings → SVD → neighbour damage under compression.
- s05 C1+C4+C10: imbalance → pipeline → contract → writeup (mini-arc, not a full comp).
- s06 C6+C7: module construction → truncation → parameter audit.
**Tooling (sol) — EVERY consumer must recognise `synthesis/`, or ci is vacuously green for
the whole set (gate MAJOR; the 013 anti-vacuity lesson):**
1. `tools/model.py`: load `synthesis/manifest.yaml` alongside unit manifests.
2. `prereq-check`: synthesis problems satisfy closure against the FULL taught set.
3. `coverage-check`: synthesis problems are EXCLUDED from every unit's ≥3 tally (additive,
   never a substitute).
4. `scripts/ci-local.sh` step 3: the execution `find` and the answer-check assert glob must
   include `synthesis/problems/*_solution.ipynb`.
5. `hygiene-check`: `_student_notebooks` must include `synthesis/problems/sNN.ipynb`
   (no outputs, no solutions).
6. `overlap-scan`: its `units/*/practice/*.ipynb` glob must also cover synthesis statements
   (they are the likeliest place to duplicate existing material).
7. `scripts/verify-register.py`: currently walks `units/*/manifest.yaml` only — extend to the
   synthesis manifest so headers/flags/ban-pricing are enforced there too.
8. `tolerance-check` already covers it only if synthesis sits under `units/`/`mocktests/` —
   it does NOT, so its tree list gains `synthesis/**` (the 013 full-tree scan is per-tree).
**Acceptance:** each of the 8 is demonstrated by a deliberately-broken fixture (a synthesis
notebook that violates the check) proving the check FAILS — no consumer is accepted on the
strength of a green run alone.
`docs/unit-standards.md` gains a short "Synthesis set" section defining the contract, AND its
stale "coverage-check enforces ≥1" line is corrected to ≥3 (plan 013 made it machine-enforced).

## Task 2 — Error clinics (2 problems + 1 section)

- C3 (or C5) "broken descent" clinic: 5 short transcripts, one planted bug each (η too large;
  sum-vs-mean loss mismatch; gradient sign flip; un-zeroed accumulator; wrong-axis broadcast).
  Student diagnoses from the loss trace BEFORE touching code — precommit-gated verification
  cell per 013's C7-p24 precedent.
- C7 BN/eval/requires_grad three-way clinic: toggle each independently on a small
  BatchNorm trunk; which changes gradients, outputs, running buffers?
  **This clinic owns the plan's "1 section" (gate finding): BatchNorm train/eval semantics
  and running buffers are NOT taught ids today — C7's lesson 02 gains a short subsection
  teaching them before the clinic assesses them, and the clinic's problems tag only taught
  ids (`layer-freezing`, `requires-grad`, `resnet-architecture`), with the BN behaviour
  taught-and-assessed as part of that register rather than as a new concept id.**

## Task 3 — softmax + cross-entropy (the top future-proofing gap)

New syllabus ids `softmax` + `cross-entropy-loss` → C5 (prereqs in-chain:
exponentials-and-logs baseline, mlp-architecture, expectation). **Clusters (gate finding):
both `ml-concepts` — they are model-semantics vocabulary, not framework work; neither folds,
so blueprint topic accounting is unaffected.** New C5 lesson section
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

### Review 2 — [glm] GLM 5.2 (2026-08-05): REJECT → all resolved
MAJOR (synthesis CI-invisibility — ci's find, assert glob, hygiene, overlap all exclude the
new tree, making Task 6 vacuously green): Task 1 now enumerates ALL EIGHT consumers plus a
broken-fixture acceptance test per consumer, so no check is accepted on a green run alone.
MINORs: verify-register extension folded into that list; the C7 clinic now owns a BN-teaching
subsection and tags only taught ids; Task 0 gains a timing methodology and a wire-it-in
requirement. NITs: unit-standards' stale ≥1 line corrected alongside; the cross-unit claim
scoped to practice problems (r1-001 has 19 multi-unit items); softmax/CE clustered
`ml-concepts`.

## Inherited item (from 013's gate, recorded)

**ci lesson-execution scope.** ci step 3 executes only `*_solution`/`solutions/*`, so lesson
and review notebooks — which now carry enforced tolerance contracts and whose narration must
match printed output — are never executed by ci. Plan 013 deferred this deliberately rather
than expand its own tail. **Task 0 of THIS plan decides it:** either widen step 3 to execute
lessons/reviews (accepting the runtime cost, with the warm caches already in place), or add a
narrower `lesson-execution` step behind a documented rationale. Whichever is chosen must be
recorded here with its measured runtime delta, **measured as: three consecutive
`scripts/ci-local.sh` runs on warm caches before and after, reporting the median wall-clock
delta; and the chosen step must be WIRED INTO ci-local.sh (not merely recorded), with the
exit-3-tolerant pattern (gate finding).**

## Out of scope

r1-002/r1-003 generation. Training loops/optimizers (watch-list). k-means, big-O, the
R2-evidence family (attention/KL/Bayes/mixtures) — documented watch-list, revisit on evidence.
