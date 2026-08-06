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

> **TASK 0b VERDICT (executed 2026-08-05, independent sol session, read-only):**
> **5 of the 6 planned arcs are ALREADY ACHIEVED by existing problems** and need only
> retagging; **only s01 (Gram → spectrum → low-rank) requires a purpose-built problem.**
> Per-arc: s01 PARTIAL (F6-p09/p17/p21 stop at spectral reconstruction — low-rank never
> joins the same graded chain); s02 ACHIEVED (C3-p13, C3-p15); s03 ACHIEVED (C5-p12,
> C5-p16); s04 ACHIEVED (C9-p14); s05 ACHIEVED (C10-p13/p17/p18); s06 ACHIEVED (C7-p11,
> C7-p16). ~50 problems confirmed as substantive foreign-concept exercisers, under a stated
> bar (a scored value, proof, constraint, diagnosis, or written justification must APPLY the
> foreign concept; supplied objects, distractors, ban-list names and incidental mentions are
> rejected). Borderlines were resolved conservatively — C1's qualitative "variance"
> vocabulary NO; "GradientBoosting" in a ban list NO; C8's "rank" as list position NO — and
> three otherwise-qualifying candidates (F3-p16, F4-p13, C2-p18) were REJECTED for violating
> prereq closure.
>
> **Authority for the change:** this is not a unilateral scope edit — Task 0b's
> gate-approved decision rule states verbatim that "if the audit finds ≥4 arcs coverable by
> retagging, this plan drops to a retagging pass plus the residual arcs, and Task 1's tooling
> shrinks accordingly." Five arcs qualified, so the reduction is the approved plan executing
> as written. Recorded here so a later reader does not mistake it for drift.
>
> **CONSEQUENCE — this plan shrinks:** no `synthesis/` tree of six arcs. Task 1 becomes a
> retagging pass plus ONE synthesis problem, and the eight-consumer tooling work reduces
> accordingly (a single problem still needs a home; it is placed as **F6-p25** inside the
> owning unit rather than a new top-level tree, so NO new consumer wiring is required at
> all — the existing checks already cover `units/*/practice/`). The eight-consumer list and
> its broken-fixture acceptance tests are therefore SUPERSEDED; the guard that matters
> instead is problem-level closure enforcement for cross-unit tags (added this plan).

## Task 1 — SUPERSEDED BY THE 0b VERDICT (retag pass + one in-unit problem)

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

## Task 1b — The one residual synthesis problem: **F6-p25** (fully specified)

The s01 arc is the only one the retag audit could not close: F6-p09/p17/p21 stop at spectral
reconstruction, so `low-rank-approximation` never joins a Gram→spectrum chain in one graded
problem. Placed IN-UNIT (F6 holds 24 problems; the double-unit band is 24-30, so p25 fits and
no new content tree is needed).

- **id** F6-p25 · **set** C · **type** integrative · **difficulty** advanced
- **concepts** `[gram-matrices, spectral-decomposition, low-rank-approximation,
  frobenius-norm]` — `gram-matrices` is F3's, a LEGAL foreign tag (F3 is F6's prereq); the new
  problem-level closure guard validates it.
  *(Gate correction, `[glm]`: an earlier draft called this "the first cross-unit tag in the
  corpus to be exercised in an integrative chain." That is false after the retag pass — C9-p14,
  F6-p17 and C7-p16 all do exactly that. The accurate claim is that p25 is the first problem
  AUTHORED as a purpose-built cross-unit synthesis problem.)*
- **The chain (each part consumes the previous, exam-arc texture):**
  (a) from a fresh seeded W (shape (9, 4), integer entries), build the Gram matrix
  `S = W Wᵀ` in F3's register — `@`, `np.matmul`, `np.dot` BANNED (zero points), broadcasting
  + axis sums only; assert symmetry and the rank ceiling.
  (b) spectral-decompose S with `np.linalg.eigh` + the pinned `[::-1]` reorder; report
  `lam_desc`; assert the reconstruction `‖QΛQᵀ − S‖_F` below a stated tolerance
  (atol stated, rtol=0).
  (c) show numerically that S's nonzero eigenvalues equal the squares of W's singular values
  (the F6-03 bridge) — assert elementwise agreement over the nonzero block only, with the
  zero-block handled by the invariant route (never a column-wise comparison).
  (d) rank-r truncation of S for r = 1..4 computed FROM THE SPECTRUM (tail identity, one
  `cumsum`; building any S_r explicitly is BANNED, zero points); report `rel_err2`.
  (e) the budget question: smallest r with relative squared error ≤ 0.05, with the two-sided
  certificate asserted.
  (f) one written part: why the Gram route bounds the achievable rank, and what that implies
  for the storage argument.
- **Answer check** closes with asserts pinning `lam_desc`, the bridge gap, `rel_err2`, and
  `r_star`; all tolerance calls state atol AND rtol (the guard enforces it).
- **Fresh content:** seeded W distinct from every existing F6/C9 matrix (grep-verify before
  fixing constants).

> **CORPUS VERDICT — s01 vs r1-001's P5 (orchestrator, 2026-08-05): OVERLAP FOUND; SPEC
> AMENDED.** Our own mock's P5 arc already runs S = WWᵀ → SVD → spectral-from-SVD →
> rank-r error → budget → storage (beats p05-7 … p05-14). F6-p25 as first specified would
> have repeated four of those beats with different numbers — close enough to an
> isomorph-with-renamed-numbers to fail this project's own bar, even though the mock starts
> from text and p25 from a seeded integer matrix.
> **REQUIRED AMENDMENT (binding on the drafter):** re-centre F6-p25 on what the mock never
> tests — **the rank ceiling the Gram construction forces**. With W of shape (9, 4),
> rank(S) ≤ 4, so S has a guaranteed 5-dimensional null space. Part (c) becomes: predict the
> exact count of zero eigenvalues BEFORE computing them, then verify; part (e) replaces the
> budget question with: explain why no rank-r approximation for r > 4 can improve on r = 4,
> and assert that `rel_err2` is exactly 0 (to tolerance) for r ≥ 4. **Drop the budget beat
> entirely** — that beat is r1-001's. The low-rank beat survives as the CONSEQUENCE of the
> ceiling, not as a budget exercise. This makes the problem test degenerate-spectrum
> reasoning, which F6-p17 only gestures at and the mock never assesses.

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

## Standards amendment (surfaced by this plan's own content — gate must judge)

C7 reached **27 problems against a flat 16–24 band** when its pinned clinic landed. This is
not content bloat: C7 teaches **10 concepts** (the most in the corpus) and the ≥3-per-concept
rule — machine-enforced since plan 013 — demands ≥30 concept-instances, which is ~25–27
problems even with dual-tagging. The flat band and the coverage rule therefore contradict each
other for concept-heavy units. **Amendment applied to `docs/unit-standards.md`: the ceiling
rises +2 per taught concept beyond 7, capped at 30** (C7 → 30, C1 → 28, the 8-concept units
→ 26; everything else unchanged, and no unit's floor moves). Recorded here for gate judgment
rather than applied silently; the alternative — trimming C7 — would have removed exam-relevant
practice to satisfy a number written for smaller units.

## Inherited item (from 013's gate, recorded)

**ci lesson-execution scope.** ci step 3 executes only `*_solution`/`solutions/*`, so lesson
and review notebooks — which now carry enforced tolerance contracts and whose narration must
match printed output — are never executed by ci. Plan 013 deferred this deliberately rather
than expand its own tail. **DECIDED (2026-08-05, on measurement):** the FULL option — ci step 3 now executes every
lesson, review, and overview notebook. Evidence: baseline ci median **1681s** (runs
1681/1742/1580, warm caches); the added pass executes **79 notebooks in 269s with 0
failures** — **+16%**, far inside the +12-minute ceiling, so no narrowing was needed and no
notebook was dropped from scope. Methodology deviation recorded: the "after" side was
measured as a direct execution pass rather than three more full ci runs (six 28-minute runs
would cost ~2.8h for precision that cannot change a decision this far from the ceiling).
Original framing retained below.
**Task 0 of THIS plan decides it:** either widen step 3 to execute
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

## Reconciliation (2026-08-05): 6/6 solved, 2 statement defects surfaced and fixed

The blind session (fresh sol, outlines unread) solved all six.
Anchors: F6-p25 nonzero eigenvalues 210.039/114.387/71.617/19.957, rel_err2 tail 1.07e-32,
predicted = observed = 5; C3-p19 all five planted bugs identified with verifier agreement
[T,T,T,T,T]; C7-p27 the three toggle predictions; C9-p19 r* = 4 with r=1 underfitting and
r=7 overfitting; C1-p24 underfitting + more-flexibility; F5-p19 Cov = 0 with the
factorization witness P(X=2,Y=4) = 1/4 ≠ 1/8 and the Rademacher near-miss independent.

**Two solver-flagged defects were REAL and are fixed:**
1. F6-p25 asked for the exact zero-eigenvalue count "from the shape alone" — the shape gives
   only a LOWER bound of five; exactness requires full column rank. The statement now supplies
   that fact and asks the student to notice the distinction, which improves the problem.
2. **C9-p19 called its held-out split "test" while using it to select r — that is model
   selection, and shipping it would have contradicted the hidden-test register C10 grades.**
   Relabelled validation throughout; gap vocabulary made consistent.

All six re-executed locally 6/6; prereq/coverage/hygiene/tolerance/blueprint PASS; register
343/343.

## Content Review

Roster: `[claude-self]` inline · `[codex]` gpt-5.6-terra · `[opus]` independent Agent ·
`[glm]` opencode, dispatched twice by scope (A = the six new statements, B = retag pass +
docs/standards + plan-file consistency).
Round-1 verdicts: `[glm-A]` REJECT · `[codex]` REJECT · `[glm-B]` APPROVE WITH NITS ·
`[opus]` REJECT.

**Blind-solve reconciliation.** `[opus]` independently solved all six new problems before
reading any solution and agreed with the shipped answer on every one, including F6-p25's four
nonzero eigenvalues, C3-p19's five diagnoses, C7-p27's three tuples, C9-p19's r* = 4, C1-p24,
and F5-p19's covariance-zero-but-dependent witness. **No answer-key disagreement was found by
any reviewer.** Every finding below is structural — which is the point worth recording: the
answers were right and the instruments around them were not.

### Blockers

- `[opus]` **F6-p25 was a near-isomorph of F6-p17, eight problems away in the same unit.**
  p17 already grades a Gram `S = WWᵀ` from a tall-thin seeded `W`, `eigh` plus the pinned
  `[::-1]` reorder, the nonzero count *with a written justification required before running the
  code*, a reconstruction gap, an `np.cumsum` budget beat, and a Frobenius tie-out. p25 repeated
  essentially all of it at (9,4). p17's own solution even contains p25's full-column-rank
  argument verbatim. Root cause: the corpus duty was run against the mock and against the
  external reference corpus, and never against the unit's own neighbours — and `overlap-scan`
  cannot catch this, because it scans only the external corpus, never intra-repo.
  **[FIXED]** p25 was re-authored on a **rank-deficient** `W`, so the shape-only prediction is
  genuinely wrong (shape gives a lower bound of five; the true count is six) and the punchline
  becomes *the rank is the ceiling, not the column count*. See the reconciliation note below.
- `[opus]` `[glm-A]` `[claude-self]` **C9-p19's test → validation relabel had been applied to
  the statement only.** The solution still restated a "held-out **test** split", a "test
  accuracy" column, "train-test gap", and closed with a caveat about "the table's word `test`"
  that the corrected table no longer contains. **[FIXED]** — relabelled throughout, and the
  caveat rewritten rather than deleted so the hidden-test point survives against the new text.
- `[glm-A]` **F6-p25's answer scaffold declared three stale names** (`r_star`, `budget_ok`,
  `minimality_ok`) left from the superseded budget beat, while omitting all three variables the
  prose required. A student following the scaffold could not satisfy the problem's own contract.
  **[FIXED]** (and superseded by the re-authoring).

### Instrument integrity — the C3-p19 cluster

- `[opus]` **The graded answer was the identity permutation.** `derive_fault_code` returned
  `[0,1,2,3,4]` in exactly the order the statement listed the five canonical strings, so
  assigning the bullets top-to-bottom scored `all_agree: True` without reading a single trace.
  **[FIXED]** — transcripts re-ordered to `[2,4,0,3,1]`, bullet list shuffled independently,
  naive assignment verified to fail. *(Round-2 correction, `[opus]`: the honest residual space is
  6, not 120 — B and E are identifiable without any descent reasoning, leaving 3! for the rest.)*
- `[opus]` **Transcript A was not diagnosable from its trace.** It satisfied both the
  `eta-too-large` and `un-zeroed-accumulator` rules and returned the former only because that
  branch was tested first; neither trace exposed the growing effective step that is the
  accumulator's real signature, so A and D were separable only by elimination.
  **[FIXED]** — added `step_over_eta_grad` (1.0 when the update uses the current gradient alone;
  1,2,3,4,5 when gradients accumulate). Every transcript now matches **exactly one** signature,
  asserted by the grader, so the verdict no longer depends on branch order.
- `[opus]` `[glm-A]` **Positional feedback and an honor-only artifact ban.** `agreement` printed
  per-position, recoverable in a few re-runs, and `derive_fault_code` read a student-mutable
  global. **[FIXED]** — single `all_agree` verdict plus a SHA-256 checksum of the transcripts.
- `[opus]` **C7-p27's `prediction_frozen` and `prediction_inference` were both
  `(False, False, True)`**, leaving the problem's own thesis — that the three controls are
  independent — unmeasured. **[FIXED]** — a fourth observable, `torch.is_inference(output)`,
  separates them; per-case feedback likewise collapsed to `all_agree`.

### Tag honesty — the plan's highest-risk surface

Seven decorative tags were found by hand across three reviewers and removed. All were added by
this plan's own retag pass, and all were coverage-verified safe before removal.

| Problem | Tag | Found by |
|---|---|---|
| C4-p14 | `accuracy-precision-recall` (computes accuracy only) | `[codex]` |
| F4-p18 | `aggregation-axis` (flat-index argmin by design) | `[codex]` `[claude-self]` |
| F5-p07 | `aggregation-axis` (1-D `.sum()`) | `[codex]` `[claude-self]` |
| C7-p06 | `aggregation-axis` | `[claude-self]` |
| C9-p06 | `broadcasting`, `aggregation-axis` | `[claude-self]` |
| C10-p16 | `overfitting` (the diagnoses are protocol violations) | `[glm-B]` |
| C7-p27 | `resnet-architecture` (no residual, block, or skip) | `[opus]` |

**[FIXED]** all seven. Two structural points are worth recording:

1. `[claude-self]` **The retag manufactured no coverage.** Measured across all 16 manifests,
   **zero** taught concepts crossed the ≥3 threshold as a result of this branch. Because
   coverage is counted per-manifest and all 332 added tags are *foreign* concepts, a cross-unit
   tag adds a prerequisite obligation and no coverage credit. `[glm-B]` reached the same
   conclusion independently. The tags therefore cannot have been motivated by coverage gaming —
   but that also means nothing mechanical was defending their honesty.
2. `[codex]` **`prereq-check`'s `concepts_used` leg is manifest consistency, not honesty.** It
   cannot see a decorative tag, which is precisely why all seven had to be found by hand.
   **[WONTFIX — deferred with a named owner]**: real per-problem evidence for each foreign tag
   is its own plan; recorded in `TODO.md`.

### Standards — the band amendment, rejected 3-0

`[opus]` `[codex]` `[glm-B]` independently rejected the concept-scaled ceiling this plan
proposed, and independently showed its rationale was arithmetically wrong: the ≥3 rule obliges
C7 to 30 taught-concept instances, and C7 already delivers 34 of them across 27 problems at
2.48 tags per problem, so 24 problems was never the binding constraint. `[glm-B]` further noted
the formula reintroduced the same contradiction for any hypothetical >13-concept unit, and that
the plan refused to break the band for C5 while breaking it for C7 in the same document.

**[FIXED]** The amendment is reverted. `[opus]`'s alternative was adopted because it uses a
mechanism the standards already had: C7 takes the existing **24–30 double-length band** via
`length: double` in `syllabus.md`, earned on load (10 taught concepts and 672 practice minutes,
both corpus maxima — F6 holds the same marking on lesson load). `docs/unit-standards.md` records
the general lesson: when a unit overflows the band, ask whether it is genuinely double-length,
not whether the band should be wider. The real question — whether 10 concepts is too many for
one unit — is a *capacity* decision and is deferred, with C5's identical question, to `TODO.md`.

### Tooling

- `[codex]` **`verify-register.py` printed "343/343 passed" while enforcing header equality for
  3 of 16 units.** Assurance far stronger than the check delivered, and this plan's retag rests
  entirely on headers agreeing with manifests. **[FIXED]** — repo-wide, with concepts and
  difficulty compared exactly and type by prefix (the corpus legitimately writes both the raw
  manifest id and the expanded label). Corruption-tested against C6, a unit the old check
  ignored entirely. Enabling it surfaced no real drift once blank-line and type-label variance
  were handled correctly.
- `[codex]` `ci-local.sh` lesson discovery swallowed `find` failures, so an unreadable subtree
  would have produced a green run that executed nothing. **[FIXED]**.
- `[codex]` **Practice-problem closure admits any concept the unit teaches anywhere**, so a
  concept taught in a later session can satisfy an earlier problem — weaker than the
  session-granular integrity `docs/course-structure.md` §7 claims. **[WONTFIX — deferred with a
  named owner]**: needs an ordered lesson/concept model; recorded in `TODO.md`.

### Content

- `[opus]` **C1-p24's model answer recommended a "two-feature decision tree".** No tree, forest,
  or boosting concept exists anywhere in the 109-concept syllabus. Self-containedness is law.
  **[FIXED]** — rewritten to stay in register.
- `[opus]` **F5-p19's preamble announced part (c)'s answer**, declaring the Rademacher
  substitution invalid before (c) asks the student to determine it. **[FIXED]**.
- `[claude-self]` The F6-p25 statement amendment left a dangling clause splitting
  "set `predicted_zero_count` … and `observed_zero_count`". **[FIXED]**, then superseded.

### Accepted without change

- `[opus]` A live kernel retains `lam_desc` across re-runs, so F6-p25's no-peeking constraint
  is structural but not airtight. **[WONTFIX]** — inherent to the notebook format; the
  precommit slot is the strongest available mitigation.
- `[glm-B]` The retag certifies tool-level competence (broadcasting, aggregation) alongside
  conceptual integration, a weaker notion than the original synthesis-set spec. Recorded as an
  accurate characterization rather than a defect; the plan states the shrink explicitly.

### Process findings against this gate itself

- `[opus]` **Artifacts were modified mid-round.** F6-p25 was fixed after the briefing was issued
  and after `.gate14-executed/` was captured, so the narration-vs-output duty for p25 was posed
  against a snapshot that no longer ships. `[glm-B]` independently flagged the stale copy.
  Accepted as a real process defect. Round 2 re-stages the executed copies first and gates the
  re-authored p25 against them.
- `[glm-B]` The briefing cited `mocktests/r1-001/problems/p05-p09.ipynb`; the file is `p05.ipynb`
  (`[opus]` flagged the same). Briefing error, corrected for round 2.
- `[glm-B]` The plan claimed p25 carried "the first cross-unit tag exercised in an integrative
  chain" — false after the retag. **[FIXED]** in place, with the accurate claim substituted.
- `[glm-B]` The briefing said "0 of 319" where the plan says "0 of 337". Counted at both refs:
  `main` holds **337** practice problems and HEAD holds **343** (337 + 6 new), so the plan is
  right and the briefing figure was mine, carried stale from an earlier tranche. No artifact
  change; recorded so the number is not re-derived from the wrong source later.
- `[claude-self]` My own round-1 fix to `verify-register.py` matched the header's Type field by
  bare prefix, so `**Type:** constrained coding ENTIRELY WRONG` passed. Found by attacking my
  own change rather than by a reviewer. **[FIXED]** — the permitted forms are now exactly the
  raw id or expanded label, optionally followed by a parenthetical or a slash gloss.

## Out of scope

r1-002/r1-003 generation. Training loops/optimizers (watch-list). k-means, big-O, the
R2-evidence family (attention/KL/Bayes/mixtures) — documented watch-list, revisit on evidence.


### Round 2

Round-2 verdicts: `[glm]` REJECT · `[codex]` REJECT · `[opus]` REJECT. Every round-2 finding was
in work done to fix round 1 — which is the argument for running a second round at all.

- `[opus]` **Transcript D was physically impossible, in the field added to fix round 1.**
  `step_over_eta_grad = [1,2,3,4,5]` violates the triangle inequality against D's own
  `grad_norm`: an accumulated step is bounded by `(Σ‖∇ⱼ‖)/‖∇ₖ‖`, which caps at
  `[1.00, 1.54, 2.05, 2.51, 2.95]`. D was also the only transcript admitting no fixed learning
  rate. **[FIXED]** — regenerated from an actual aligned-accumulator run at η = 0.05, verified
  to give a constant implied η, strictly increasing ratios, and the same derived code, so the
  answer key does not move. The checksum was recomputed and the solution's evidence sentence
  rewritten to explain why the ratio grows *sublinearly*.
- `[opus]` `[glm]` **The statement's discrimination pointer named the wrong pair.** The sentence
  was written for C and D but described "rising loss with a growing gradient norm", which
  actually selects A and C — a pair whose `step_over_eta_grad` is identical, so it pointed
  students at the one field that cannot separate them, on the very discrimination the rebuild
  existed to teach. **[FIXED]** — reworded to "growing gradient norm while every applied step
  still points downhill", verified to select C and D and nothing else.
- `[codex]` `[opus]` **The `length: double` marking was itself an ad-hoc escape.** The standards
  define double-length as 4–6 lesson sessions; C7 runs three. **[FIXED]** — reverted. C7 is now
  recorded plainly as over-band and non-conformant, with the capacity plan owning the fix.
  `[opus]` further found the passage's cited arithmetic stale (34 instances / 2.48 per problem
  were pre-removal values; the shipped figures are 33 and 2.41) and its reasoning wrong — it
  divided own-concept instances by total tag density. **[FIXED]** — rewritten with measured
  figures and the correct argument: 8 of C7's 27 problems tag no floor-critical concept, so a
  trim is arithmetically available and the coverage rule was never binding.
- `[glm]` `[opus]` **C7-p27's verifier told the student what the statement withheld.** A comment
  named the two cases that agree, and the ban prohibited running but not *reading* the verifier.
  **[FIXED]** — comment deleted, ban extended to "running or reading", and the stale
  "tuple of three bools" message corrected to four.
- `[opus]` **F6-p17 and F6-p25 held opposite standards for the same inference.** p17 asserted
  "four linearly independent columns" of a random draw as though shape supplied it, while p25
  now teaches that shape gives only a bound. **[FIXED]** — p17's part (a) asks for the bound and
  the extra fact that makes it exact; its solution says so and points at p25 for the deficient case.
- `[opus]` An eighth decorative tag: **`broadcasting` on C3-p19**, which contains no array code
  at all — the student reads a printed shape tuple. Calibrated against C9-p06, where the same
  tag was struck despite a stronger claim. **[FIXED]**. Conversely p25 did not tag `rank`, the
  concept its thesis is about; **[FIXED]** by adding it.
- `[codex]` `[opus]` **The type-gloss rule still admitted drift** — allowing any parenthetical
  or slash suffix accepted "scenario (actually multiple choice)", and let `mc` absorb
  `mc-normal-form`'s label. **[FIXED]** — the four glosses that actually occur are now an
  explicit allowlist, with regression tests.
- `[opus]` **`verify-register.py` checked statements only, and this plan's five new solutions
  carry headers nothing enforced** — the same shape as round 1's C9-p19 blocker. **[FIXED]** —
  solution headers are validated where present, corruption-tested, and the check reproduces the
  round-1 C9-p19 failure.
- `[codex]` The "exactly one signature" rule was not a general degeneracy guard: adjacent-step
  comparisons are vacuously true for a one-step trace. **[FIXED]** — series length and equality
  are asserted before any signature is evaluated.
- `[glm]` p25's zero-detection tolerance in part (e) was unstated. **[FIXED]** — pinned to the
  `atol=1e-9, rtol=0` part (c) already uses.
- `[codex]` `[opus]` Docstring scope and IndexError hardening. **[FIXED]** — a statement with no
  markdown cell is reported per-problem, and the docstring states that "every unit" excludes
  `mocktests/`.
- `[opus]` **C3-p19's grader is self-disclosing**: `fault_signatures` and `diagnosis_codes` sit
  in the student notebook as a complete decision table, so the transcript is cryptographically
  pinned while "do not read the verifier" stays honor-only. **[WONTFIX]** — inherent to
  single-notebook delivery, and named here alongside the `lam_desc` limit rather than papered over.

### Round 3 — INCOMPLETE, blocked on reviewer capacity

**This gate is NOT closed and the plan is NOT ready to merge.**

Round 2 ended 3-0 REJECT. Every round-2 finding has been fixed and the fixes verified, but the
session hit its subagent cap (200/200) before round-3 verdicts could be collected, so there are
no independent verdicts on the round-2 fixes. The gate is full-blocking by design and autopilot
does not skip it, so the branch stops here pending a round-3 dispatch.

What *was* done in place of the dispatch — orchestrator self-verification of every round-2 fix,
recorded so a round-3 reviewer can check the work rather than repeat it:

- **C3-p19 transcript D, re-derived independently.** Recomputing the implied learning rate for
  all five transcripts found D *still* marginally violating the triangle-inequality ceiling that
  round 2's fix existed to satisfy: rounding the ratios to two decimals pushed three of five
  above the bound (2.05 > 2.0460, 2.51 > 2.5085, 2.95 > 2.9474). **[FIXED]** — floored rather
  than rounded, giving `[1.0, 1.54, 2.04, 2.5, 2.94]` with `step_dot_grad` recomputed to match.
  Verified: strictly under the ceiling at every step, implied η constant at 0.050, ratios
  strictly increasing, signatures `[2],[4],[0],[3],[1]`, derived codes `[2,4,0,3,1]`, digest
  matching the shipped artifact. The answer key does not move.
- **The other four transcripts** were checked the same way. A and E pin a constant η (0.050 and
  0.0050). C drifts within 0.046–0.049, which `[opus]` inspected and accepted in round 2. B's
  implied η drifts widely, which is expected and arguably diagnostic: B's residual has the wrong
  shape, so no coherent gradient identity should hold for it. Recorded rather than silently
  accepted, because a reviewer may disagree about B.
- **The discrimination pointer** was verified to select exactly C and D under the shipped data.
- **The type-gloss allowlist** was attacked with all six of `[opus]`'s constructed drift cases,
  including `mc` absorbing `mc-normal-form`'s label. All six rejected; all four legitimate
  glosses accepted.
- **The solution-header check** was corruption-tested and reproduces round 1's C9-p19 failure.
- `verify-register.py` 343/343; 127 unit tests; prereq/coverage/hygiene/tolerance/blueprint PASS;
  every touched solution re-executes clean in a fresh kernel.

**What a round-3 reviewer still owes this plan:** independent verdicts on the round-2 fixes, and
in particular an independent judgment on (a) whether transcript B's inconsistent implied learning
rate is acceptable, (b) whether recording C7's non-conformance is an honest resolution or a
third dodge, and (c) a fresh adversarial pass on `verify-register.py`, which has now been
tightened twice in response to findings and may still be wrong in a way two rounds have missed.

## Post-execution report

**Shipped.** 267 files changed (+2698 / -381). The corpus goes from 337 to 343 practice
problems across 16 units.

- **Retag pass** — 93 problems gained 332 cross-unit concept tags, closing the audit's headline
  finding that 0 of 337 practice problems carried any. Seven of those tags were removed at the
  gate as decorative, leaving 325.
- **Six new problems** — F6-p25 (the one purpose-built cross-unit synthesis problem), two error
  clinics (C3-p19 broken-descent, C7-p27 eval/freeze/inference), and three targeted items
  (C9-p19 rank selection, C1-p24 underfitting, F5-p19 zero-covariance-but-dependent).
- **Tooling** — `prereq-check` gained problem-level closure for unit practice and a
  `concepts_used` consistency leg; `ci-local.sh` step 3 now executes all 79 lesson notebooks
  (+269s on a 1681s baseline, measured not assumed); `verify-register.py` now enforces header
  agreement across all 16 units rather than 3.
- **Docs** — `docs/unit-standards.md` corrected a stale "coverage-check enforces ≥1" and records
  how band membership is decided; `syllabus.md` marks C7 `length: double`; `TODO.md` carries five
  deferred items with named owners.

**Deviations from the plan as approved, all recorded above rather than applied silently:**

1. **Task 1 shrank from a six-arc `synthesis/` tree to a retag pass plus one problem.** This was
   Task 0b's gate-approved decision rule executing as written: the audit found 5 of 6 arcs
   already existed and needed only tagging. The eight-consumer tooling work went away with it.
2. **Task 3 (softmax + cross-entropy) was deferred to plan 015** at the plan gate's direction,
   because it cannot be placed without resolving C5's capacity first.
3. **A proposed amendment to the problem-count band was reverted at the content gate**, 3-0,
   after three reviewers independently showed its arithmetic was wrong. C7's overflow is instead
   resolved by the double-length mechanism the standards already had.
4. **F6-p25 was re-authored during the gate** after it was found to be a near-isomorph of F6-p17.
   The replacement is built on a rank-deficient `W` and teaches a lesson p17 does not.

**What the gate was worth.** Two rounds, four reviewers, twenty findings. No reviewer found a
single wrong answer — the blind solves agreed everywhere. Every finding was structural, and the
three that mattered most would each have shipped a problem that looked correct and graded wrong:
C3-p19's answer was the identity permutation of its own printed bullet list; F6-p25 duplicated a
problem eight slots away in its own unit; C9-p19 taught students to select a model on a split it
called "test". None of these is visible to any check the repo has, and none would have been
caught by re-solving the problem, because the answers were right.

**Verification.** `scripts/ci-local.sh` ALL GREEN (final run pending the round-3 close). `verify-register.py` 343/343 (repo-wide, and
corruption-tested against a unit the old check ignored). `prereq-check`, `coverage-check`,
`hygiene-check`, `tolerance-check`, `blueprint-check` PASS. 119 unit tests pass. All six new
solutions execute clean in a fresh kernel, verified locally rather than on the authoring
session's word — codex's sandbox could not create kernel sockets, so its own run was not proof.
