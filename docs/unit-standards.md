# Unit Standards

The depth-and-variety bar every teaching unit must meet
(user directive, 2026-08-04; applies to plan 005's units retroactively and all later tranches).
Verification: coverage/hygiene/prereq checks enforce the mechanical parts;
the content gate's reviewers enforce the qualitative parts against this document.

## Practice sets

- **Count:** 10–14 problems per unit (double-length units like F6: 14–18).
- **Mandated type mix** (each unit includes at least):
  - 2 exam-style MC items — exactly five options A–E; numeric MC uses normal-form
    constraints (gcd/sign) where applicable, matching the blueprint style rules.
  - 3 constrained coding tasks — exact function/identifier contracts, shape contracts,
    and API bans with the zero-points clause register (the exam's signature move).
  - 1 by-hand derivation or proof-style problem ("Reasoning is required" register).
  - 1 integrative multi-part problem (a/b/c parts, later parts consume earlier results —
    miniature of the exam's arc texture).
  - 1 scenario/application analysis (interpretation and judgment, not just computation).
  - 1 challenge problem (advanced tier; stretches past the lesson without leaving the
    unit's concept closure).
- **Difficulty spread:** roughly 30% intro / 45% core / 25% advanced, tagged per problem
  in the manifest (`difficulty:` informational field).
- Every taught concept exercised by ≥2 problems where feasible (coverage-check enforces ≥1).

## Lessons

Beyond the motivation → definition → worked example → checkpoint cycle:

- **≥2 fully worked exam-style examples** in the lesson body, solved step by step in the
  blueprint's register (identifiers, constraints, reasoning-required flags).
- **Common pitfalls** section — the errors a newcomer actually makes (shape bugs,
  off-by-one axes, metric confusions…), each with a broken example and the fix.
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
