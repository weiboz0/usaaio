# docs/

Project documentation and the plan-driven execution lifecycle.

## Plan-driven execution docs

Four numbered folders, all 3-digit prefix, monotonically increasing per folder:

- `proposals/NNN-…` — pre-decision ideas worth keeping; iterate over time; may never ship.
- `designs/NNN-…` — approved designs for large or cross-cutting work, referenced by multiple plans.
- `plans/NNN-…` — concrete execution plans: phases, files, verification steps.
  Plan-review and content-review verdicts are EMBEDDED in the plan file.
- `reviews/NNN-…` — standalone review artifacts that outgrow a plan file (rare).

Lifecycle per plan: design (or verbal alignment) → plan file committed on a feature branch →
4-way plan-review gate → phase-by-phase build → verification (`scripts/ci-local.sh`) →
4-way content-review gate → post-execution report → PR → `scripts/pre-merge-guard.sh --pr` → squash-merge.

## Reference docs

- `development-workflow.md` — Steps 1–6 of the lifecycle, tailored for content development.
- `content-review-gate.md` — the 4-way content-review gate (replaces a code-review gate).
- `mocktest-generation.md` — the repeatable mock-test generation pipeline (stub until plan 003).
- `architecture/decisions.md` — single source of truth for cross-cutting decisions.
