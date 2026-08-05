# Plan 012 — Course Structure Document

**Goal:** Ship `docs/course-structure.md` — the pacing map that turns the 16 units + mock
test into a formal two-semester training course, closing the roadmap.

## Inputs (all committed, authoritative)

Manifests' `estimated_minutes` (totals: lessons 3,900 + practice 7,160 + reviews 640 =
11,700 min = 195 h), the syllabus DAG, and mocktests/r1-001.

## The document (single deliverable)

`docs/course-structure.md`, semantic line breaks, containing:

1. **Course model:** weekly budget 7.5 h (3 in-class + ~4.5 independent practice) →
   195 h ≈ 26 teaching weeks ≈ two 13-week semesters. Assumption stated, tunable.
2. **Semester split (DAG-respecting, hour-balanced):**
   - Semester 1 (≈101 h): F1 → F2 → {F4, F3} → F5 → C1 → C2 → C3 → C4. Foundations plus
     the classical-ML core; ends with C4's sklearn practice as the semester capstone.
   - Semester 2 (≈94 h): C5 → C6 → C7 ∥ C8 → F6 → C9 → C10 → r1-001 as the final-week
     mock exam (3 h) + debrief. F6 placed mid-semester-2 directly before C9 (its consumer),
     honoring the double-unit weight with two sittings.
3. **Week-by-week table:** one row per week — units/sessions covered, in-class vs
   independent minutes (from lesson_sessions / practice / review), the unit-review
   checkpoints as week-end gates, and the mock-exam week.
4. **Milestones & assessment:** unit reviews as formative checks; r1-001 as the summative
   mock (blueprint-scored, 300 pts); a slot marked for r1-002 as an optional
   semester-1-end or pre-exam second mock (generated on demand via the pipeline).
5. **Provenance note:** all numbers derive from unit manifests; the regeneration one-liner
   (the yaml-summing snippet) included in a comment for maintainers.
6. **Prereq-integrity statement:** the week order is a topological order of the syllabus
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

(4-way gate verdicts land here.)

## Content Review

(Pre-PR gate findings land here.)
