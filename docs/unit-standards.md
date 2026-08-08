# Unit Standards (v2 — semester-grade)

The bar every teaching unit must meet
(user directives, 2026-08-04 ×2: materials constitute a FORMAL MULTI-SEMESTER TRAINING
COURSE; depth, coverage, and variety must reach that level — not tutoring notes).
Applies to plan 005's units retroactively and every later **shipped teaching unit**, whether
the unit belongs to shared foundation, Round 1 core, Round 2 extension, or optional enrichment.
A roadmap row or provisional unit does not satisfy this standard: it becomes coverage only
when the lesson, review, manifest, and honest practice set ship together.
Verification: coverage/hygiene/prereq checks enforce the mechanical parts;
the content gate's reviewers enforce the qualitative parts against this document.

## Lessons are session-structured

- Each unit's lesson splits into **2–4 class-session notebooks** in `lessons/`
  (`lessons/01-<slug>.ipynb`, …), each sized to one course session (60–90 min:
  ~6–10 sections with worked examples and checkpoints).
  A root `lesson.ipynb` remains as the unit overview/index (goals, session map,
  prerequisites recap, how-to-study guidance).
- Double-length units (F5, F6, C7, C11, C12) use 4–6 sessions.
- `estimated_minutes` in the manifest lists per-session lesson minutes plus practice.

## Practice sets

- **Count:** 16–24 problems per unit (double-length units: 24–30), organized as
  **problem sets** mirroring homework cadence:
  - Set A — fundamentals (drills per concept, intro/core),
  - Set B — exam register (constrained coding, normal-form MC, reasoning-required),
  - Set C — integration + challenge (multi-part arcs, scenarios, advanced tier).
  File layout stays flat in `practice/` (pNN + pNN_solution); the manifest orders
  problems and a `set:` tag (A/B/C) records the grouping.
- **Type mix** (each unit includes at least): 4 exam-style MC (exactly five options A–E;
  ≥1 numeric normal-form with gcd/sign constraints), 6 constrained coding tasks (exact
  function/identifier contracts, shape contracts, API bans with the zero-points register),
  2 proof/derivation ("Reasoning is required"), 2 integrative multi-part (parts consume
  earlier results), 2 scenario analyses, 2 challenge problems (advanced, within closure).
- **Difficulty spread:** roughly 30% intro / 45% core / 25% advanced, tagged per problem
  in the manifest (`difficulty:` informational field).
- Every taught concept exercised by **≥3 problems** — `coverage-check` enforces this
  MACHINE-SIDE since plan 013 (it previously enforced only ≥1 and left the rest to reviewers).
  The same floor applies in every curriculum layer. Round 2 GPU depth does not waive the
  practice contract; any future exception requires an explicit standards change and gate.

### Recorded non-conformance

**At the Plan 014 gate, `C7-cnn-transfer` shipped 27 problems against a 24 ceiling.
It was over the band, and that was recorded here rather than legalized.**
C7 was not double-length: it ran three lesson sessions where the rule above required 4–6.
At that gate, its 10 taught concepts and 672 practice minutes were both corpus maxima, which
explained the overflow without excusing it.
The required resolution was a unit *capacity* decision — split C7, rehome concepts such as
`feature-hierarchy`, `receptive-field`, or `tensor-shape-tracing`, or trim — and it was deferred
to a dedicated plan; see `TODO.md`.
`C5-neural-networks` carried the same open question.

This entry exists because plan 014 tried twice to make the overflow legal and its content gate
rejected both attempts.

The first proposed a ceiling scaling at +2 problems per taught concept beyond 7, on the argument
that the ≥3 rule forces a 10-concept unit past 24 problems.
It does not.
Measured on C7 as shipped: 27 problems, 65 tag instances, of which **33 are C7's own concepts**
(1.22 per problem; the other 32 are foreign tags that earn no coverage credit).
Seven of its ten concepts sit at exactly 3, and 8 of its 27 problems tag no floor-critical
concept at all.
Those eight are each *individually* droppable but not *jointly* so — removing all eight would
take `tensor-shape-tracing` to 0, `convolution` to 1 and `layer-freezing` to 2.
The largest subset that can go while every concept stays at ≥3 is **three** (for example
C7-p01, C7-p10 and C7-p23), and that lands C7 at exactly 24.
So a trim to the band exists without touching coverage, and the coverage rule was never the
binding constraint — which is the whole basis on which the amendment was rejected.

The second attempt marked C7 `length: double`, which a reviewer rejected as an unenforced label
that contradicts the session rule above — C7 runs three sessions where double-length means 4–6,
so the flag would have meant one thing on F6 and another on C7 with nothing recording the
difference.
The generalizable lesson, and the reason this is written down: **when a unit overflows a
standard, record the non-conformance and fix the unit — do not reshape the standard, and do not
reach for an existing exemption the unit does not actually qualify for.**
A standard that moves to accommodate its own artifacts has stopped being one.

**Plan 017 resolution.**
The capacity issue is now resolved by changing the unit rather than relabeling the old artifact.
C7 now has a substantive fourth 90-minute lesson session and keeps 27 practices, so it satisfies
both double-length bands.
Its final 1,280 minutes exceed the pre-Plan-017 corpus maximum of 1,120 minutes.
Its lesson load of 345 minutes over four sessions is lighter than F5's 415/5, F6's 425/5, and
C11's 450/5; F7 shows why four sessions alone are not sufficient, because its 20 practices remain
inside the standard-length band.
C5 remains a compliant standard-length unit with 22 practices because neural-network training
moved to C11 instead of being crowded into C5.
The current double-length roster is therefore F5, F6, C7, C11, and C12.
Across the shipped roster, C10 has the concept maximum at 12 taught concepts, while C12 has the
practice-time maximum at 1,410 minutes.

## Per-unit review material

- `review.ipynb` at the unit root: concept summary table, formula/idiom sheet,
  a 10–15-item self-quiz spanning every taught concept (answers in a collapsed
  section at the end — lesson-style, not hygiene-scoped), and pointers to which
  practice problems to redo for each weak spot.

## Lessons

Beyond the motivation → definition → worked example → checkpoint cycle:

- **≥2 fully worked exam-style examples** in the lesson body, solved step by step in the
  blueprint's register (identifiers, constraints, reasoning-required flags).
- **Common pitfalls** section — the errors a newcomer actually makes (shape bugs,
  off-by-one axes, metric confusions…), each with a broken example and the fix.
  *(Distribution rule, decided at plan-005 gate: Pitfalls / Exam Connections / Going
  Deeper may be distributed across a unit's session notebooks wherever they fit best —
  the requirement is satisfied UNIT-WIDE, each section appearing at least once per
  unit; sessions need not each carry all three.)*
- **Exam connections** section — how this unit's concepts appear in the real Round 1
  (paraphrase level, no verbatim past-test text; cite reference/analysis.md cluster).
- **Going deeper** section — optional enrichment pointing FORWARD along the syllabus DAG
  (named unit ids), never assuming untaught material in the main text.
- **Checkpoints:** ≥2 exercises per section; all answers collected at lesson end.
- Length signal: a unit lesson should stand alone as the student's complete text for its
  concepts — if a competent tutor would need to supplement it, it is too thin.

## Manifests

- `estimated_minutes` reflects the enriched scope (lesson + full practice set).
- Practice entries carry `difficulty:` tags; integrative problems may use part-suffixed
  ids (`F2-p08a`) with one manifest entry per gradable part or one entry for the whole
  problem — choose per gradability.
