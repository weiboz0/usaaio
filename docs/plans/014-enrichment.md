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

## Task 0b — Retagging audit FIRST (gate finding: the cheap option is unverified)

Before any synthesis file is written, audit whether existing practice problems can be
HONESTLY retagged cross-unit: for each of the 337 problems, does it substantively exercise a
concept owned by another unit (not merely use it as scaffolding)? Record the count and the
qualifying list. **Decision rule:** every arc the retagging audit can cover honestly is
covered that way (cheaper, no new tree); the synthesis set is built ONLY for arcs retagging
cannot express — a graded problem whose parts consume results across units in one narrative.
If the audit finds ≥4 arcs coverable by retagging, this plan drops to a retagging pass plus
the residual arcs, and Task 1's tooling shrinks accordingly. Record the verdict here.

> **PRELIMINARY EVIDENCE (orchestrator, read-only, 2026-08-05 — pre-gate scan):** a textual
> scan for foreign-concept surface forms across all 337 unit practice problems finds **116
> with a foreign-concept signal**. Strongest unit→foreign-owner directions:
> C3←F4 (18), C10←C1 (17), C9←F1 (12), F3←F1 (12), C10←F4 (9), C9←F6 (8), C4←C1 (7),
> C9←F5 (7). **Three of these directions map onto proposed arcs** (F4+C2+C3 gradient chain;
> C8+F6+C9 compression; C1+C4+C10 applied arc), so the cheap option looks materially viable
> for part of the set. **Caveat, and why this is evidence not a verdict:** a textual signal
> is an UPPER BOUND — mentioning "variance" (e.g. C1-p03) is usually scaffolding, not
> substantive exercise of F5's concept, which is the bar this plan sets. Task 0b's real work
> is the per-candidate semantic judgment; this scan only proves the audit is worth running
> and gives it a starting list.

## Task 1 — The synthesis set (only for what Task 0b leaves uncovered)

New top-level `synthesis/` directory (NOT a syllabus unit — no new concepts):
`synthesis/manifest.yaml` + `synthesis/problems/sNN.ipynb` + `sNN_solution.ipynb`.
**Manifest contract (gate finding — previously undefined):** the file declares
`set: synthesis`, and each entry carries `id` (sNN), `concepts` (≥2 concepts whose OWNING
UNITS differ — validated, not merely documented), `units` (the owning units, ≥2), `type`,
`difficulty`, `path`, `solution_path`. `tools/model.py` gains a `load_synthesis()` returning
the same problem shape as units; `prereq-check` validates closure against the FULL taught set
(not a single unit's chain) and REJECTS an entry whose concepts all share one owning unit.
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
strength of a green run alone. **Plus one NEGATIVE test (gate finding): a unit concept with
only 2 unit-practice problems plus 1 synthesis problem must still FAIL coverage-check —
synthesis can never rescue a unit's ≥3.**
`docs/unit-standards.md` gains a short "Synthesis set" section defining the contract, AND its
stale "coverage-check enforces ≥1" line is corrected to ≥3 (plan 013 made it machine-enforced).

## Task 2 — Error clinics (2 problems + 1 section) — PLACEMENTS PINNED (gate finding:
"C3 (or C5)" / "C9 or C5" left curriculum placement to drafters)

- **C3** "broken descent" clinic (C3 owns descent; 1 problem, type `scenario`, difficulty
  `advanced`): 5 short transcripts, one planted bug each (η too large;
  sum-vs-mean loss mismatch; gradient sign flip; un-zeroed accumulator; wrong-axis broadcast).
  Student diagnoses from the loss trace BEFORE touching code.
  **Verifier contract — all FOUR properties of the C7-p24 precedent are REQUIRED (gate
  finding: citing the precedent is not pinning it): (1) committed-answer schema — the
  student's diagnosis variables are named and typed in the statement; (2) completeness check
  — the verifier raises if any answer is uncommitted AND if the committed collection's length
  differs from the expected count (013's `zip()` truncation hole); (3) artifact-derived
  grading — the verdict is computed from the actual transcripts/run, never from a
  student-assigned value (013's C4-p22 vacuity lesson); (4) non-disclosure — the verifier
  reports agreement only, never the expected values.**
- C7 BN/eval/requires_grad three-way clinic: toggle each independently on a small
  BatchNorm trunk; which changes gradients, outputs, running buffers?
  **This clinic owns the plan's "1 section" (gate finding): BatchNorm train/eval semantics
  and running buffers are NOT taught ids today — C7's lesson 02 gains a short subsection
  teaching them before the clinic assesses them, and the clinic's problems tag only taught
  ids (`layer-freezing`, `requires-grad`, `resnet-architecture`), with the BN behaviour
  taught-and-assessed as part of that register rather than as a new concept id.**

## Task 3 — softmax + cross-entropy: DEFERRED to plan 015 (gate finding)

**Recorded decision.** C5 currently holds 22 problems; unit-standards' band is 16-24, so the
6 planned problems (3 per new id) would put C5 at 28 — and both codex reviewers independently
flagged the sizing. Softmax/cross-entropy is a FUTURE-RISK item (no current exam sub-part
tests it), not a coverage gap, so it does not justify either breaking the band or a rushed
unit-capacity decision inside an already-large plan. **Plan 015 owns it** and must resolve
placement explicitly (which unit gains capacity, or whether the band flexes with a recorded
unit-standards amendment). Two corrections carried forward for that plan: the section must sit
AFTER `mlp-architecture` within C5's lesson order (it is taught inside C5, not a unit prereq,
and unit-level tooling cannot catch intra-unit ordering); and the scope claim must be stated
accurately (gate finding — my first correction was still wrong): C3 DOES implement and run
training loops — hand-written gradient-descent updates for LINEAR models, named as such in
lesson 02. The real boundary is narrower and framework-shaped: **no unit performs AUTOGRAD-BASED
TRAINING — there is no `.backward()` and no `torch.optim` anywhere in `units/` (grep-verified
at gate time). C5-C7 are construction/inference-only. Note the precise line (gate finding,
third correction of this sentence): C6/C7 DO teach autograd *machinery* — `requires_grad`
flags and `torch.inference_mode()` — as inference discipline; what no unit does is call
backward or drive an optimizer.** Cross-entropy may
therefore be taught, evaluated, and differentiated ON PAPER, and may even be minimised by a
hand-written descent loop in C3's register if plan 015 wants it — but it must not introduce
autograd or an optimizer object. The optional CE-gradient proof
additionally depends on F4's partial-derivatives/multivariable-chain-rule (in C5's transitive
chain — state it).

<!-- superseded spec retained for plan 015's drafter -->

New syllabus ids `softmax` + `cross-entropy-loss` → C5 (prereqs in-chain:
exponentials-and-logs baseline, mlp-architecture, expectation). **Clusters (gate finding):
both `ml-concepts` — they are model-semantics vocabulary, not framework work; neither folds,
so blueprint topic accounting is unaffected.** New C5 lesson section
(logits → probabilities; the shift-invariance trick; CE as −log p_correct; why MSE is the
wrong classification loss) + 3 problems each (MC normal-form; constrained coding; one proof
of shift-invariance or the CE-gradient identity). NOTE: teaching CE does NOT introduce
training — it stays inference/analysis register per the curriculum's standing scope.

## Task 4 — Promised callbacks + targeted items

- **C9** bias–variance callback (C9 owns evr/capacity; 1 lesson subsection + 1 problem, type
  `scenario`, difficulty `core`) revisiting C1's rigid/flexible spectrum with the now-precise
  variance vocabulary and tying evr/capacity to the train–test gap.
- F5: covariance-converse trap problem. **CORRECTED SPEC (gate BLOCKER — the original
  "X symmetric, Y = X²" is FALSE in general: for Rademacher X = ±1, X² ≡ 1 is constant and
  therefore INDEPENDENT of X, verified numerically at gate time). Pin a NONDEGENERATE
  symmetric distribution whose |X| varies — e.g. X uniform on {−2, −1, 1, 2} — so that
  Cov(X, X²) = E[X³] = 0 by symmetry while X² is a non-constant function of X, hence
  dependent. The statement must make the varying-magnitude requirement explicit, and the
  solution must show the degenerate case as the instructive near-miss.**
- **C1**: underfitting-side scenario (1 problem, type `scenario`, difficulty `core`): both
  scores poor and close → recommend more flexibility, distinguished from overfitting.

## Task 5 — Statements/solutions cycle

sol drafters (sections + statements + outlines to gitignored reference/outlines-014/);
SEPARATE sol sessions blind-solve; reconciliation; amended-statement → re-solve;
corpus duty (gate finding — make it enforced, not aspirational): overlap-scan covers
synthesis statements per Task 1's consumer #6, AND the orchestrator records an explicit
structural comparison of every arc against (i) the exam's integrative arc and (ii) r1-001's
P5 chain — our own mock — with a per-arc recorded verdict in this plan. An arc that would
duplicate either is redesigned before drafting, not after.

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

### Review 2 — [glm] GLM 5.2 (2026-08-05): REJECT → **APPROVE** (re-verdict: all seven
verified with line references; nothing remaining)
MAJOR (synthesis CI-invisibility — ci's find, assert glob, hygiene, overlap all exclude the
new tree, making Task 6 vacuously green): Task 1 now enumerates ALL EIGHT consumers plus a
broken-fixture acceptance test per consumer, so no check is accepted on a green run alone.
MINORs: verify-register extension folded into that list; the C7 clinic now owns a BN-teaching
subsection and tags only taught ids; Task 0 gains a timing methodology and a wire-it-in
requirement. NITs: unit-standards' stale ≥1 line corrected alongside; the cross-unit claim
scoped to practice problems (r1-001 has 19 multi-unit items); softmax/CE clustered
`ml-concepts`.

### Review 3 — [codex] GPT-5.6-sol, slot 2 (2026-08-05): REJECT → all resolved
Its BLOCKER-1 (synthesis invisibility) raced the glm round's 8-consumer fix. NEW and applied:
the retagging-first audit (Task 0b — the cheaper option was untested); the clinic verifier's
four REQUIRED properties spelled out rather than cited; softmax placement/scope corrections
(carried into the deferral); every "A or B" placement pinned. **BLOCKER-6 was a real
mathematical error in this plan** — "X symmetric ⇒ X, X² dependent" is false for Rademacher X
(X² constant ⇒ independent), verified numerically at gate time; the spec now pins a
nondegenerate symmetric distribution and makes the degenerate case the instructive near-miss.

**Slot-2 re-verdict round 2:** its remaining finding was that my own scope correction was
STILL factually wrong — C3 implements and runs a training loop (verified: lesson 02's
hand-written descent updates). Re-corrected to the accurate, narrower boundary: no unit
trains a NEURAL NETWORK; `grep` confirms zero `.backward()` / `torch.optim` in `units/`.

### Review 4 — [codex] GPT-5.6-sol, slot 3 — independent session (2026-08-05): REJECT → all resolved
Its blocker raced the same fix but added the negative test (synthesis must never rescue a
unit's ≥3) — applied. NEW and applied: the synthesis manifest contract (schema, loader,
cross-unit-tag VALIDATION, full-taught-set closure); the overlap duty made enforced rather
than aspirational, incl. a per-arc recorded verdict against r1-001's P5; Task 0's acceptance
criteria beyond runtime; **the C5 capacity overflow (22 + 6 = 28 > band 24), which drove the
Task 3 deferral**; the CE-gradient proof's F4 dependency.

**GATE RESULT: PASS — 4/4** (claude-self AWN pre-empted; glm REJECT→APPROVE; both codex
slots REJECT→resolved, consolidated re-verdict APPROVE WITH NITS — its final nit, that
"no autograd anywhere" was overbroad given C6/C7 teach `requires_grad`/`inference_mode`,
is fixed above). Implementation may begin.

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
exit-3-tolerant pattern. **ACCEPTANCE beyond runtime (gate finding — measurement is not a
criterion): the chosen step MUST execute every lesson and review notebook that carries an
enforced tolerance contract or executable narration (scope stated explicitly, not sampled);
warm caches are assumed and stated; the step FAILS ci on any execution error; and if the
median delta exceeds +12 minutes the narrower option is taken WITH the same coverage
guarantee (parallelism or reuse), never by dropping notebooks from scope.**

## Out of scope

r1-002/r1-003 generation. Training loops/optimizers (watch-list). k-means, big-O, the
R2-evidence family (attention/KL/Bayes/mixtures) — documented watch-list, revisit on evidence.
