# Plan 012 — Course Structure Document

**Goal:** Ship `docs/course-structure.md` — the pacing map that turns the 16 units + mock
test into a formal two-semester training course, closing the roadmap.

## Inputs (all committed, authoritative)

Manifests' `estimated_minutes` (totals: lessons 3,900 + practice 7,160 + reviews 640 =
11,700 min = 195 h), the syllabus DAG, and mocktests/r1-001.

## The document (single deliverable)

`docs/course-structure.md`, semantic line breaks, containing:

1. **Course model:** two 13-week semesters with PER-SEMESTER weekly loads (gate fix —
   a flat 7.5 h/wk leaves S1 overflowing): S1 = 101.1 h → 7.8 h/wk; S2 = 93.9 h content +
   3-h mock + 1-h debrief = 97.9 h → 7.5 h/wk. Course-wide derived split ≈2.5 h in-class +
   ≈5 h independent (lesson 65 h / practice+review 130 h). All figures computed from
   manifests, none assumed.
2. **Semester split (DAG-respecting, hour-balanced):**
   - Semester 1 (≈101 h): F1 → F2 → {F4, F3} → F5 → C1 → C2 → C3 → C4. Foundations plus
     the classical-ML core; ends with C4's sklearn practice as the semester capstone.
   - Semester 2 (93.9 h content, 97.9 h total with the mock + debrief): C5 → C6 → C7 ∥ C8 →
     F6 → C9 → C10 → r1-001 as the final-week
     mock exam (3 h) + debrief. F6 placed mid-semester-2 directly before C9 (its consumer),
     its five 85-min sessions spread across three teaching weeks (2+2+1, sharing the first — the
     double-unit weight; each sitting stays inside the 60-90-min session rule).
3. **Week-by-week table:** one row per week — units/sessions covered, in-class vs
   independent minutes (from lesson_sessions / practice / review), the unit-review
   checkpoints as week-end gates (F1 has no review artifact — its gate is the F2-opening
   recap, noted in the table), and the mock-exam week. Pacing: the per-semester loads above already
   include the mock + debrief in S2's final week — the table's rows sum exactly to
   101.1 h and 97.9 h.
4. **Milestones & assessment:** unit reviews as formative checks; r1-001 as the summative
   mock (blueprint-scored, 300 pts); a slot marked for r1-002 as an optional
   semester-1-end or pre-exam second mock (generated on demand via the pipeline).
5. **Provenance note:** all numbers derive from unit manifests; the regeneration one-liner
   included in a comment for maintainers — it MUST sum `lesson_sessions` (C1's manifest
   has no `lesson:` scalar; summing `lesson:` undercounts by 240 — gate catch).
6. **Assessment & grading guidance (gate addition):** suggested weights (unit-review
   checkpoints formative/ungraded; the mock summative at blueprint scoring, 300 pts; a
   pass bar suggestion referencing the difficulty bands) and calendar-buffer guidance
   (S1 runs at 7.8 h/wk with no slack — the stated recovery mechanism is trimming
   C-set/challenge practice problems first, never lessons or reviews; optional r1-002
   DISPLACES a review week rather than adding hours).
7. **Prereq-integrity statement:** the week order is a topological order of the syllabus
   DAG (each unit scheduled after all its prereqs; verified in-document by listing each
   unit's prereqs beside its week).

## Tasks

1. Draft `docs/course-structure.md` per the section list above (sol drafts per the current
   dispatch; orchestrator verifies every number against the manifests before the gate).
2. Content gate (4-way; reviewers verify: arithmetic vs manifests, DAG order, hour
   balance, semantic line breaks, no invented facts).
3. Ship: post-exec report, TODO tick, PR, guard, squash-merge.

## Out of scope

Generating r1-002/r1-003 (on-demand later). Any tooling. Any unit/manifest edits.
**Verification-phase exemption (docs-only plan):** no new executable content; ci-local
runs unchanged as the merge gate; correctness is enforced by the gate's
arithmetic-verification duty (design §2 exemption stated).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-07)

- **Verdict**: APPROVE
- Arithmetic verified by direct manifest computation: totals 3,900/7,160/640 = 11,700 min;
  Semester 1 (F1,F2,F4,F3,F5,C1,C2,C3,C4) = 6,065 min = 101.1 h; Semester 2 = 5,635 min =
  93.9 h + the 3-h mock; 26 × 7.5 = 195. DAG: the stated order verified topological (C8's
  foundation-only prereqs make the C7 ∥ C8 parallelism legal; C9's four prereqs all
  precede it; C4's all in semester 1).

### Review 3 — [codex] GPT-5.6-terra (2026-08-07)

- **Verdict**: Changes requested → response below, re-verdict pending
1. `[WONTFIX-with-reasoning + FIXED-clarification]` [codex] Strict week-granular prereq
   ordering FAIL on the five shared weeks: the plan pinned SESSION-granular topological
   integrity, and every shared week's "then" notation is strict in-week sequence (a unit's
   first session always follows its prerequisites' final sessions). Week-granular
   strictness would force five half-empty transition weeks for no pedagogical gain.
   FIXED-clarification: §7 now states the granularity rule explicitly so the reading
   cannot recur. All its other duties PASS (arithmetic exact, one-liner reproduced,
   sections complete, style clean).

### Review 2 — [glm] GLM 5.2 (2026-08-07): APPROVE WITH NITS → all resolved
All arithmetic and topology verified exact. Nits fixed in the plan: the weekly split is now
the DERIVED 2.5/5 (not the assumed 3/4.5 — lesson 65 h and practice+review 130 h divide 26
exactly); the mock+debrief absorption into S2's 4-h slack pinned for the week table; F6's
"two sittings" made concrete (sessions 3+2 across two weeks).

### Review 4 — [codex] GPT-5.6-sol (2026-08-07): APPROVE WITH NITS → resolved
Full arithmetic/topology/model verification concurs (199/26 = 7.65 overall; 7.78/7.53
per-semester correctly rounded). Nits: residual "≈94 h" phrasing fixed to the content/total
form; grading-weights + calendar-buffer guidance added as document section 6 (trim C-set
practice first; r1-002 displaces, never adds).

**GATE RESULT: PASS — 4/4** (self APPROVE; glm/fable/codex all APPROVE WITH NITS, all
resolved). Drafting may begin.

### Review 3 — [fable] Independent Fable 5 (2026-08-07): APPROVE WITH NITS → all resolved
Arithmetic + DAG independently verified. Major 4 (F6 sittings) raced the glm fix and is now
further tightened (2+2+1 sessions, 60-90-min rule respected). Major 5 (zero slack — S1
overflows a flat 7.5): fixed with honest PER-SEMESTER loads (7.8/7.5 incl. mock+debrief).
Minors: regeneration snippet pinned to lesson_sessions (C1 trap); F1's missing review gate
handled in the table spec.

## Content Review

### Review 3 — [codex] GPT-5.6-terra (2026-08-07)

- **Verdict**: Changes requested → response below, re-verdict pending
1. `[WONTFIX-with-reasoning + FIXED-clarification]` [codex] Strict week-granular prereq
   ordering FAIL on the five shared weeks: the plan pinned SESSION-granular topological
   integrity, and every shared week's "then" notation is strict in-week sequence (a unit's
   first session always follows its prerequisites' final sessions). Week-granular
   strictness would force five half-empty transition weeks for no pedagogical gain.
   FIXED-clarification: §7 now states the granularity rule explicitly so the reading
   cannot recur. All its other duties PASS (arithmetic exact, one-liner reproduced,
   sections complete, style clean).

### Review 2 — [glm] GLM 5.2 (2026-08-07)

- **Verdict**: Approved (full arithmetic re-derivation exact; spot units exact; topology
  sound; all devices present).
1. `[FIXED]` [glm] N: the PLAN's "two-and-a-half teaching weeks" phrasing (the doc already
  said three) → aligned to "three teaching weeks (2+2+1, sharing the first)".

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-07)

- **Verdict**: Approved
- Table column sums verified programmatically (26 rows: S1 1,970+4,095 = 6,065; S2
  2,170+3,705 = 5,875 — both exact). Per-unit practice allocations hand-verified for all
  16 units against manifests (two initial flags were my parser's regex artifacts — C4's
  "capstone-practice" phrasing and prereq-list mis-attribution — both totals correct:
  460 and 420). All pinned devices present (per-semester loads, F6 2+2+1, F1 recap gate,
  r1-002 displacement, C-set-first buffer, prereqs beside weeks, lesson_sessions
  regeneration one-liner printing 3900/7160/640).
