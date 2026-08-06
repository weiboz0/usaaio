# Development Workflow

Follow this process for every plan. Do NOT skip steps or batch them.
Trivial changes (typos, one-line fixes) use judgment; anything multi-file follows the workflow.

## Step 1 — Design

1. Clarify intent: what does the student gain, what does success look like?
2. Read `docs/architecture/decisions.md`, the design doc, and existing plans.
3. Brainstorm approaches, compare trade-offs, align with the user when the fork is genuine.

Output: verbal alignment, a proposal in `docs/proposals/`, or a design in `docs/designs/`.
Skip when the task is well-defined (e.g. "add unit NN per the syllabus").

## Step 2 — Plan

1. Branch: `git checkout -b feature/plan-NNN-description`.
2. Write the plan: phases, file lists, per-phase verification, acceptance criteria.
3. **Named verification phase is mandatory** for any plan shipping units or mock tests
   (design §2): solutions execute and reproduce the answer key; manifests validate;
   blueprint conformance, overlap scan, prereq closure, practice coverage all pass;
   PDF builds; difficulty/timing budget stated.
   Exempt (docs-only, tooling-only, plan-design plans) must say so in `## Out of scope`.
4. Self-review, then run the 4-way plan-review gate (`AGENTS.md ## Plan-review gate`).
   A passing gate IS approval to implement.
5. Save as `docs/plans/NNN-name.md` (next free number) and commit before any implementation.

## Step 3 — Build

Per phase: implement (dispatch per `AGENTS.md ## Agent dispatch`) → verify → self-review
against the plan and `decisions.md` → update docs → commit.
Independent phases may run in parallel subagents; dependent phases run in order.

## Step 4 — Verify

1. Run `scripts/ci-local.sh` — the full suite, not just changed checks.
2. Confirm the verification phase shipped exactly what its acceptance criteria promised.
3. Check cross-phase consistency (duplicate content, inconsistent terminology, orphan concepts).

## Step 5 — Review

Run the 4-way content-review gate per `docs/content-review-gate.md`.
Findings live in the plan file's `## Content Review`; all `[OPEN]` items resolve before merge.
Evaluate findings rigorously — push back with reasoning rather than agreeing performatively.

## Step 6 — Ship

1. Post-execution report in the plan file (deviations, limitations, follow-ups).
2. Update `decisions.md` and `TODO.md`.
3. Final `scripts/ci-local.sh` run — must be green.
4. Push; `GH_TOKEN=$(cat .gh-token) gh pr create`; `bash scripts/pre-merge-guard.sh --pr`;
   squash-merge.

## Session Handoff

Commit everything before ending (`WIP:` ok); push the branch;
check `git status` on start; trust `git log` + post-execution reports, not summaries.
