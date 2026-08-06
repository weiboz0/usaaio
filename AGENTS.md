# Project Instructions

USAAIO Prep. Mock tests and self-contained teaching materials for the USA AI Olympiad
(Round 1 first), for the author's own student(s).
Content-as-code: notebooks are the source of truth, PDFs are built artifacts,
and correctness is enforced by executable verification.
Full design: `docs/designs/000-project-design.md`.

It adopts the PowerMarket development workflow (plan-driven lifecycle, multi-model review
gates, autopilot through merge) tailored for content development.

## CRITICAL RULES (never skip)

- **Autopilot is the DEFAULT operating mode.** For design, plans, and fixes, run the full
  lifecycle autonomously through merge — design → 4-way plan-review gate → phase-by-phase
  implementation → verification (`scripts/ci-local.sh`) → 4-way content-review gate →
  post-execution report → PR → `scripts/pre-merge-guard.sh --pr` → squash-merge — without
  per-step approval. **Pause only for:**
  - **Genuine judgment forks** (scope / curriculum-direction / trust decisions) via `AskUserQuestion`.
  - **Hard safeguards** (always stop): committing secrets (`.gh-token`, `.env*`, `*token*`,
    `*secret*`, `*credential*`); committing raw past-test papers, verbatim past-problem text,
    or student data (**the repo is PUBLIC**); `git push --force`/`reset --hard` on shared
    history; a direct commit to `main`; edits to this file / `docs/development-workflow.md` /
    `docs/content-review-gate.md` / `docs/architecture/decisions.md` (governance —
    human-reviewed, except when the user explicitly asks); plan-scope expansion beyond the
    plan file's phases; unresolved `[OPEN]` blockers at the gate round-cap; a failing
    `pre-merge-guard --pr` / `ci-local.sh`.
  - The user can redirect at any time. Gates are conducted by autopilot, never skipped by it.
- **Branch BEFORE drafting a plan.** `git checkout -b feature/plan-NNN-description` first;
  the plan file and all review verdicts live on that branch. Never commit directly to `main`.
- **Run the 4-way plan-review gate before any implementation** (see `## Plan-review gate`).
- **Run the 4-way content-review gate before opening a PR** (see `docs/content-review-gate.md`).
- **Self-containedness is law.** The student baseline is Calculus AB + basic Python.
  Nothing may be used before it is taught (prereq closure), nothing taught without practice
  (coverage), nothing tested that was not taught. These are CI checks once plan 004 lands;
  until then reviewers enforce them manually.
- **Always run `scripts/ci-local.sh` before merge — local is the gate.**
- **Always write a post-execution report** in the plan file before shipping.

## Project Structure

See `docs/designs/000-project-design.md §1` for the full tree. Top level:
`units/` (teaching, one dir per syllabus unit), `mocktests/` (blueprint + one dir per test),
`reference/` (past-test corpus — raw papers GITIGNORED, only derived analysis committed),
`tools/` (Python verification package), `scripts/` (ci-local, pre-merge-guard),
`docs/` (lifecycle), `syllabus.md` (topic taxonomy + Calc AB baseline allowlist, from plan 003).

## Content Conventions

- Notebooks: student-facing problem notebooks contain NO solutions and no executed outputs;
  solutions live in separate notebooks that run top-to-bottom clean with fixed seeds.
- Every unit and mock test carries a `manifest.yaml`
  (concept tags, prerequisites, provenance, points, blueprint version + generation parameters).
- Datasets are produced by seeded generation scripts, never opaque blobs.
- Provenance: original problems by default; adaptations carry `adapted-from: <reference id>`.
- Docs use semantic line breaks (one sentence per line).

## Verification (the "test suite")

`scripts/ci-local.sh` is authoritative (design §3): solution-notebook execution,
student-notebook hygiene, manifest validation, blueprint conformance, overlap scan,
prereq closure, practice coverage, PDF build, lint.
Checks whose tools don't exist yet print `SKIP (plan NNN)` — a skip is only acceptable
while the named plan is unshipped.

## Git

- Origin is `git@github-weiboz0:weiboz0/usaaio.git` (SSH alias `github-weiboz0` →
  `~/.ssh/id_ed25519_weiboz0`). Do NOT switch to HTTPS or plain `github.com` SSH —
  this machine's default credentials map to a different account.
- Every `gh` command needs `GH_TOKEN=$(cat .gh-token)` (file is gitignored).
- Git identity: Weibo Zhou <weibo.zhou6fe@gmail.com>.
- Never commit directly to `main`; feature branch + PR via `gh pr create`.
- Before any merge: `bash scripts/pre-merge-guard.sh --pr` — catches plan-number and
  unit/mocktest-ID collisions from parallel sessions (`--pr` adds the origin/main union;
  the script takes no PR number).
- Commit messages: what changed and why. Batch related small fixes into one logical commit.

## Plan-review gate (mandatory — 4-way)

| # | Reviewer | Dispatch | Model |
|---|----------|----------|-------|
| 1 | Self-review | active session inline; record in `## Plan Review` | active session model |
| 2 | Sol reviewer | fresh read-only subagent (request `--model gpt-5.6-sol`) | GPT-5.6-sol |
| 3 | Terra reviewer | separate fresh read-only subagent (request `--model gpt-5.6-terra`) | GPT-5.6-terra |
| 4 | GLM | `opencode:opencode-review` subagent, read-only | opencode-go/glm-5.2 |

Dispatch 2–4 in parallel with the inline self-review (one message).
Consensus is full blocking: all four APPROVE / APPROVE WITH NITS, no open blockers.
Verdicts recorded in the plan file's `## Plan Review`, tagged `[self]` / `[sol]` /
`[terra]` / `[glm]`.
Reviewers MUST REJECT a plan shipping units/mock tests without a named verification phase
(design §2 "verification phase" rule; docs-only and tooling-only plans state the exemption
in `## Out of scope`).

## Content-review gate (mandatory — 4-way, pre-PR)

Same roster: active-session self-review, GPT-5.6-sol, GPT-5.6-terra, and GLM-5.2.
Duties and format: `docs/content-review-gate.md`.
Findings tagged `[self]` / `[sol]` / `[terra]` / `[glm]` with
`[OPEN]` / `[FIXED]` / `[WONTFIX]` in the plan file's `## Content Review`;
all `[OPEN]` resolve before merge.

## Agent dispatch

| Work | Dispatch |
|------|----------|
| Planning, review orchestration, test assembly | Active Codex session inline |
| Lesson content + problem/mock-question STATEMENTS | `codex:codex-rescue` (GPT-5.6-sol) — user directive 2026-08-06 |
| ANY job previously routed to Fable 5 (drafting, independent review, audits) | `codex:codex-rescue` (GPT-5.6-sol) — TEMPORARY, expires 2026-08-09 16:00 |
| SOLUTIONS to practice + mock questions | `codex:codex-rescue` (GPT-5.6-sol) — SEPARATE fresh session, never reads statements' outlines; blind-solve independence is now session-level (same model family), cross-model verification lives in the gates |
| Blind independent solving (content gate) | Gate roster (all four reviewers solve blind) |
| Tooling code (`tools/`, `scripts/`) | `codex:codex-rescue` (GPT-5.6-sol) |
| Trivially-scoped edits | Inline |

## Errata

Post-merge content bugs (wrong answer key, broken problem): 2-way diagnosis
(Claude inline + Codex on GPT-5.6-sol — audits use sol, read-only) → fix plan → gates → merge, plus an `ERRATA.md`
entry in the affected mock test's directory. Typos skip diagnosis.

## Session Handoff

- Commit before ending a session (`WIP:` prefix fine); uncommitted work is invisible.
- Check `git status` at session start; ask before discarding leftovers.
- Verify prior work via plan files' post-execution reports + `git log`, not summaries.
