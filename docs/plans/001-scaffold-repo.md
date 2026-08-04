# Plan 001 — Scaffold Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the usaaio repository skeleton — process docs, CLAUDE.md, Python tooling package, and the two guard scripts — so every later plan runs inside the adopted PowerMarket-style lifecycle.

**Architecture:** Content-as-code monorepo per `docs/designs/000-project-design.md`. This plan ships no teaching content and no real verification tools; it ships the process (docs + CLAUDE.md), a uv-managed Python package with a CLI stub that later plans fill in, and the CI/guard scripts that make the lifecycle enforceable from day one.

**Tech Stack:** Python 3.12 + uv + hatchling; pytest; ruff; bash for scripts. Heavy deps (torch, sklearn, Quarto) are deliberately NOT added here — they arrive with the plans that need them (003–006).

## Global Constraints

- Baseline audience assumption everywhere: high schooler with Calculus AB + basic Python (design §2a).
- Repo is PUBLIC: never commit raw past-test papers, verbatim past-problem text, student data, or `.gh-token` (design "Git" requirement).
- Doc numbering: 3-digit prefixes in `docs/{proposals,designs,plans,reviews}/`; plans start at 001.
- Markdown in docs: semantic line breaks (one sentence per line; break long sentences at clause boundaries).
- Git identity: Weibo Zhou <weibo.zhou6fe@gmail.com> (already in local config). Origin is `git@github-weiboz0:weiboz0/usaaio.git`; `gh` commands need `GH_TOKEN=$(cat .gh-token)`.
- Everything lands on branch `feature/plan-001-scaffold-repo`; merge via PR after the content/code-review gate.

---

### Task 1: Docs lifecycle skeleton + docs/README.md

**Files:**
- Create: `docs/README.md`
- Create: `docs/proposals/.gitkeep`, `docs/reviews/.gitkeep`

**Interfaces:**
- Produces: the four numbered lifecycle folders (`proposals/`, `designs/`, `plans/`, `reviews/`) and the taxonomy doc every later plan references.

- [ ] **Step 1: Create folders**

```bash
mkdir -p docs/proposals docs/reviews
touch docs/proposals/.gitkeep docs/reviews/.gitkeep
```

- [ ] **Step 2: Write `docs/README.md`**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add docs/README.md docs/proposals/.gitkeep docs/reviews/.gitkeep
git commit -m "docs: add lifecycle folder skeleton and taxonomy"
```

---

### Task 2: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Interfaces:**
- Produces: the project's operating rules; every future session reads this first. Later docs (Tasks 3–4) are referenced by path from here and must exist by end of plan.

- [ ] **Step 1: Write `CLAUDE.md`**

```markdown
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
| 1 | Claude self-review | inline; record in `## Plan Review` | claude-fable-5 (fallback opus) |
| 2 | Codex | `codex:codex-rescue` subagent | Codex GPT-5.5 |
| 3 | Independent Fable | `Agent` general-purpose, `model: fable`, fresh context, read-only | claude-fable-5 (fallback opus) |
| 4 | GLM | `opencode:opencode-review` subagent, read-only | opencode-go/glm-5.2 |

Dispatch 2–4 in parallel with the inline self-review (one message).
Consensus is full blocking: all four APPROVE / APPROVE WITH NITS, no open blockers.
Verdicts recorded in the plan file's `## Plan Review`, tagged `[claude-self]` / `[codex]` / `[fable]` / `[glm]`.
Reviewers MUST REJECT a plan shipping units/mock tests without a named verification phase
(design §2 "verification phase" rule; docs-only and tooling-only plans state the exemption
in `## Out of scope`).

## Content-review gate (mandatory — 4-way, pre-PR)

Same roster shape (Claude self on Opus, Codex, independent Opus `Agent`, GLM).
Duties and format: `docs/content-review-gate.md`.
Findings tagged `[claude-self]` / `[codex]` / `[opus]` / `[glm]` with
`[OPEN]` / `[FIXED]` / `[WONTFIX]` in the plan file's `## Content Review`;
all `[OPEN]` resolve before merge.

## Agent dispatch

| Work | Dispatch |
|------|----------|
| Planning, review orchestration, test assembly | Orchestrator Claude inline |
| Problem / lesson drafting | `general-purpose` subagents (parallel per unit/problem) |
| Blind independent solving (content gate) | Gate roster (Codex + GLM solve blind) |
| Tooling code (`tools/`, `scripts/`) | `codex:codex-rescue` |
| Trivially-scoped edits | Inline |

## Errata

Post-merge content bugs (wrong answer key, broken problem): 2-way diagnosis
(Claude inline + Codex, read-only) → fix plan → gates → merge, plus an `ERRATA.md`
entry in the affected mock test's directory. Typos skip diagnosis.

## Session Handoff

- Commit before ending a session (`WIP:` prefix fine); uncommitted work is invisible.
- Check `git status` at session start; ask before discarding leftovers.
- Verify prior work via plan files' post-execution reports + `git log`, not summaries.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md — tailored PowerMarket process for content development"
```

---

### Task 3: development-workflow.md

**Files:**
- Create: `docs/development-workflow.md`

**Interfaces:**
- Consumes: gate rosters defined in `CLAUDE.md` (Task 2).
- Produces: the Steps 1–6 reference every plan follows.

- [ ] **Step 1: Write `docs/development-workflow.md`**

```markdown
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
4. Self-review, then run the 4-way plan-review gate (`CLAUDE.md ## Plan-review gate`).
   A passing gate IS approval to implement.
5. Save as `docs/plans/NNN-name.md` (next free number) and commit before any implementation.

## Step 3 — Build

Per phase: implement (dispatch per `CLAUDE.md ## Agent dispatch`) → verify → self-review
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
```

- [ ] **Step 2: Commit**

```bash
git add docs/development-workflow.md
git commit -m "docs: add development workflow (Steps 1-6, content-tailored)"
```

---

### Task 4: content-review-gate.md + mocktest-generation.md stub + decisions.md + TODO.md

**Files:**
- Create: `docs/content-review-gate.md`
- Create: `docs/mocktest-generation.md`
- Create: `docs/architecture/decisions.md`
- Create: `TODO.md`

**Interfaces:**
- Consumes: design §2 gate duties; milestone list from design.
- Produces: gate spec referenced by CLAUDE.md; decision log seeded with the decisions already made in design 000.

- [ ] **Step 1: Write `docs/content-review-gate.md`**

```markdown
# Content-Review Gate

The pre-PR quality gate for teaching content and mock tests
(the tailored equivalent of a code-review gate). 4-way, full-blocking consensus.

## Roster

| # | Reviewer | Dispatch | Model |
|---|----------|----------|-------|
| 1 | Claude self | inline | claude-opus (or session model) |
| 2 | Codex | `codex:codex-rescue` subagent | Codex GPT-5.5 |
| 3 | Independent Opus | `Agent` general-purpose, `model: opus`, fresh context, read-only | claude-opus |
| 4 | GLM | `opencode:opencode-review` subagent, read-only | opencode-go/glm-5.2 |

Dispatch 2–4 in parallel with the inline self-review.
Tooling code changes (`tools/`, `scripts/`) in the same plan get conventional code review
by the same roster in the same round.

## Reviewer duties (content)

1. **Solve blind first.** Attempt each problem from the student-facing materials alone,
   BEFORE reading the solution or answer key. Report your answer, then compare.
2. **Correctness.** Verify the answer key and rubric against your independent solution.
3. **Clarity.** Flag ambiguous wording, underspecified inputs, unstated assumptions.
4. **Difficulty + timing.** Judge against real Round 1 level and the stated time budget.
5. **Rubric fairness.** Points match difficulty; partial credit is well-defined.
6. **Provenance.** `adapted-from` tags present where content resembles a known past problem;
   note any resemblance the tags miss.
7. **Fidelity.** For mock tests: style, wording register, and problem shape match the
   reference corpus; record a per-section fidelity verdict.
8. **Accessibility.** For units: read as the target student
   (Calculus AB + basic Python + declared prerequisites only);
   flag any silently-assumed concept.

## Format

Findings append to the plan file's `## Content Review`, one review round per reviewer pass:

    ### Review N — <reviewer> (YYYY-MM-DD)
    - **Verdict**: Approved / Approved with suggestions / Changes requested
    1. `[OPEN]` Finding with file/section reference. Priority: Must Fix / Should Fix / Nice to Have.

Authors respond inline with `→ Response:` and retag `[FIXED]` / `[WONTFIX]` (with reason).
Source tags: `[claude-self]` / `[codex]` / `[opus]` / `[glm]`.

## Acceptance

All four reviewers APPROVE (or approve-with-nits) and every `[OPEN]` item is resolved.
One REJECT blocks. Iterate fix → re-review to consensus.
```

- [ ] **Step 2: Write `docs/mocktest-generation.md`** (stub — completed by plan 003)

```markdown
# Mock-Test Generation Pipeline

STUB — this document is completed by plan 003 (syllabus + blueprint).
Until then, the authoritative outline is design 000 §2b:

1. **Blueprint** — `mocktests/blueprint.yaml`, derived from `reference/analysis.md`; versioned.
2. **Instantiate** — `tools new-mocktest r1-NNN` scaffolds the directory + per-slot problem specs.
3. **Draft** — problems/solutions per spec (subagent-dispatched); datasets from seeded scripts.
4. **Verify** — `scripts/ci-local.sh` (design §3 checks).
5. **Gate** — the 4-way content-review gate, including the fidelity review.

Every manifest records blueprint version + generation parameters, so generation is repeatable.
```

- [ ] **Step 3: Write `docs/architecture/decisions.md`** seeded with decisions already made:

```markdown
# Architecture Decisions

Single source of truth for cross-cutting rules. Update when a plan introduces a new decision.

## §0 — Self-containedness (design 000 §2a)

Baseline: Calculus AB + basic Python. Concept vocabulary lives in `syllabus.md` (plan 003).
Prereq closure, practice coverage, and tested-only-if-taught are merge blockers
(manual review until plan 004 ships the tools).

## §1 — Toolchain

Python 3.12, uv-managed, hatchling build. Notebooks executed via nbclient with fixed seeds.
PDF rendering: Quarto (added in plan 006 when the first test is assembled).
Lint: ruff. Tests: pytest.

## §2 — Public-repo content policy

The repo is public. Never commit: raw past-test papers, verbatim past-problem text,
student data, tokens/secrets. `reference/` raw material is gitignored;
only original derived analysis is committed.

## §3 — Manifests

Every unit and mock test carries `manifest.yaml` — the machine-readable contract that CI
validates. Schema is owned by `tools/` (plan 004); design 000 §1 lists the required fields.
```

- [ ] **Step 4: Write `TODO.md`**

```markdown
# TODO

- [x] 000 — project design (docs/designs/000-project-design.md)
- [ ] 001 — scaffold repo (this plan)
- [ ] 002 — reference corpus: ingest past tests (local-only), per-problem index, analysis.md
- [ ] 003 — syllabus + blueprint + mocktest-generation.md; Calc AB baseline allowlist
- [ ] 004 — verification tooling: blueprint-check, overlap-scan, prereq-check, coverage-check, hygiene-check, new-mocktest
- [ ] 005 — first teaching unit (foundation track)
- [ ] 006 — first full mock test r1-001 through the pipeline
```

- [ ] **Step 5: Commit**

```bash
git add docs/content-review-gate.md docs/mocktest-generation.md docs/architecture/decisions.md TODO.md
git commit -m "docs: add content-review gate, generation-pipeline stub, decisions log, TODO"
```

---

### Task 5: Python package skeleton (pyproject + tools/ + test)

**Files:**
- Create: `pyproject.toml`
- Create: `tools/__init__.py`
- Create: `tools/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `tools.cli:main` console script `usaaio-tools` with subcommand framework;
  plan 004 adds real subcommands (`blueprint-check`, `overlap-scan`, `prereq-check`,
  `coverage-check`, `hygiene-check`, `new-mocktest`) into `SUBCOMMANDS`.
  `tools.__version__` string.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "usaaio-tools"
version = "0.1.0"
description = "Verification and build tooling for USAAIO mock tests and teaching materials"
requires-python = ">=3.12"
dependencies = []
# pyyaml arrives with plan 004 (manifest parsing) — no unused deps at scaffold time.

[project.scripts]
usaaio-tools = "tools.cli:main"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.6",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tools"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write the failing test** `tests/test_cli.py`

```python
import subprocess
import sys

import tools
from tools.cli import SUBCOMMANDS


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "tools.cli", *args],
        capture_output=True,
        text=True,
    )


def test_version_flag():
    proc = run_cli("--version")
    assert proc.returncode == 0
    assert tools.__version__ in proc.stdout


def test_help_lists_planned_subcommands():
    proc = run_cli("--help")
    assert proc.returncode == 0
    for name in SUBCOMMANDS:
        assert name in proc.stdout


def test_unimplemented_subcommand_exits_2():
    proc = run_cli("blueprint-check")
    assert proc.returncode == 2
    assert "plan 004" in proc.stderr
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — either a build/sync error (hatchling cannot package the not-yet-created
`tools/` directory) or, if the env resolves, ModuleNotFoundError / ImportError.
Both count as the red step; proceed.

- [ ] **Step 4: Implement** `tools/__init__.py`:

```python
__version__ = "0.1.0"
```

`tools/cli.py`:

```python
"""usaaio-tools CLI.

Subcommand framework only; real implementations land with plan 004.
"""

import argparse
import sys

import tools

# name -> (help text, plan that implements it)
SUBCOMMANDS = {
    "blueprint-check": ("verify a mock test against mocktests/blueprint.yaml", "plan 004"),
    "overlap-scan": ("flag problems too similar to the reference corpus", "plan 004"),
    "prereq-check": ("verify the unit DAG and concept closure", "plan 004"),
    "coverage-check": ("verify every taught concept has a practice problem", "plan 004"),
    "hygiene-check": ("verify student notebooks contain no solutions or outputs", "plan 004"),
    "new-mocktest": ("scaffold a mock test from the blueprint", "plan 004"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="usaaio-tools")
    parser.add_argument("--version", action="version", version=f"usaaio-tools {tools.__version__}")
    sub = parser.add_subparsers(dest="command")
    for name, (help_text, _) in SUBCOMMANDS.items():
        sub.add_parser(name, help=help_text)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    plan = SUBCOMMANDS[args.command][1]
    print(f"usaaio-tools {args.command}: not implemented yet ({plan})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Sync env and run tests to verify they pass**

Run: `uv sync && uv run pytest tests/test_cli.py -v`
Expected: 3 passed

- [ ] **Step 6: Lint**

Run: `uv run ruff check tools/ tests/`
Expected: clean (fix anything it flags)

- [ ] **Step 7: Commit** (include `uv.lock`)

```bash
git add pyproject.toml uv.lock tools/ tests/
git commit -m "feat: uv-managed tools package with CLI subcommand framework"
```

---

### Task 6: Guard scripts (pre-merge-guard.sh + ci-local.sh)

**Files:**
- Create: `scripts/pre-merge-guard.sh`
- Create: `scripts/ci-local.sh`

**Interfaces:**
- Consumes: `uv run pytest` / `uv run ruff` from Task 5.
- Produces: `bash scripts/ci-local.sh` (exit 0 = mergeable) and
  `bash scripts/pre-merge-guard.sh [--pr]` (exit 0 = no collisions).
  Later plans extend `ci-local.sh` by replacing `skip` lines with real commands.

- [ ] **Step 1: Write `scripts/pre-merge-guard.sh`**

```bash
#!/usr/bin/env bash
# Guards against artifacts that collide when parallel sessions merge:
# duplicate 3-digit doc numbers and duplicate unit/mocktest IDs.
# --pr: also check against origin/main (the simulated post-merge union).
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
fail=0

collect() {  # collect <git-ref-or-WORKTREE> <glob-dir>
  local ref="$1" dir="$2"
  if [[ "$ref" == "WORKTREE" ]]; then
    [[ -d "$dir" ]] && find "$dir" -maxdepth 1 -mindepth 1 -printf '%f\n' || true
  else
    git ls-tree --name-only "$ref" "$dir/" 2>/dev/null | xargs -rn1 basename || true
  fi
}

check_dupes() {  # check_dupes <label> <newline-separated names> <prefix-regex>
  local label="$1" names="$2" regex="$3"
  local dupes
  # `|| true`: grep exits 1 on no match, which pipefail would otherwise turn fatal
  dupes=$(printf '%s\n' "$names" | grep -oE "$regex" | sort | uniq -d || true)
  if [[ -n "$dupes" ]]; then
    echo "FAIL: duplicate ${label} number(s): $(echo "$dupes" | tr '\n' ' ')"
    fail=1
  fi
}

refs=(WORKTREE)
if [[ "$MODE" == "--pr"* ]]; then
  if git fetch -q origin main 2>/dev/null; then
    refs+=(origin/main)
  else
    echo "note: origin/main not reachable — checking worktree only"
  fi
fi

for dir in docs/proposals docs/designs docs/plans docs/reviews; do
  names=""
  for ref in "${refs[@]}"; do names+="$(collect "$ref" "$dir")"$'\n'; done
  check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^[0-9]{3}'
done

for dir in units mocktests; do
  names=""
  for ref in "${refs[@]}"; do names+="$(collect "$ref" "$dir")"$'\n'; done
  # unit dirs: NN-name; mocktest dirs: r1-NNN
  check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^(r[0-9]-)?[0-9]+'
done

if git grep -nE '^(<{7}|={7}|>{7})( |$)' -- ':!scripts/pre-merge-guard.sh' >/dev/null 2>&1; then
  echo "FAIL: conflict markers found:"
  git grep -nE '^(<{7}|={7}|>{7})( |$)' -- ':!scripts/pre-merge-guard.sh' | head || true
  fail=1
fi

if [[ $fail -eq 0 ]]; then echo "pre-merge-guard: OK"; fi
exit $fail
```

Note on the dedupe logic: names are unioned across refs with `sort -u` first
(the same file on both branch and main is not a collision),
then duplicate NUMBER prefixes across DIFFERENT names are flagged.
The regex captures only the numeric prefix, so `003-syllabus.md` on main and
`003-blueprint.md` on the branch collide; `docs/plans/001-scaffold-repo.md` present
in both refs does not.

- [ ] **Step 2: Write `scripts/ci-local.sh`**

```bash
#!/usr/bin/env bash
# The authoritative local gate (design 000 §3). Must be green before any merge.
# Checks whose tools are not yet shipped print "SKIP (plan NNN)" — acceptable only
# while that plan is unshipped.
set -euo pipefail
cd "$(dirname "$0")/.."

step() { echo; echo "=== $1 ==="; }

step "1/6 lint (ruff)"
uv run ruff check tools/ tests/

step "2/6 unit tests (pytest)"
uv run pytest -q

step "3/6 solution-notebook execution"
notebooks=$(find units mocktests -path '*/solutions/*.ipynb' -o -path '*/practice/*.ipynb' 2>/dev/null || true)
if [[ -z "$notebooks" ]]; then
  echo "no notebooks yet — nothing to execute"
else
  while IFS= read -r nb; do
    echo "executing: $nb"
    uv run jupyter execute "$nb"
  done <<< "$notebooks"
fi

step "4/6 manifest + content checks"
echo "SKIP manifest validation      (plan 004)"
echo "SKIP blueprint-check          (plan 004)"
echo "SKIP overlap-scan             (plan 004)"
echo "SKIP prereq-check             (plan 004)"
echo "SKIP coverage-check           (plan 004)"
echo "SKIP hygiene-check            (plan 004)"

step "5/6 PDF build (quarto)"
echo "SKIP (plan 006)"

step "6/6 pre-merge-guard"
bash scripts/pre-merge-guard.sh

echo
echo "ci-local: ALL GREEN"
```

- [ ] **Step 3: Make executable and run both**

Run: `chmod +x scripts/*.sh && bash scripts/ci-local.sh`
Expected: exits 0, "ci-local: ALL GREEN", steps 4–5 all SKIP, guard OK.
(Step 3 executes no notebooks yet; `jupyter execute` dependency is NOT added until a plan
ships notebooks — the empty-find branch keeps this green.)

- [ ] **Step 4: Negative test of the guard** (throwaway, not committed)

Assert the MESSAGE, not just the exit code — a crash also exits non-zero and must not
count as a pass:

```bash
touch docs/plans/001-fake-collision.md
out=$(bash scripts/pre-merge-guard.sh 2>&1 || true)
rm docs/plans/001-fake-collision.md
echo "$out" | grep -q 'duplicate docs/plans' \
  && echo "guard correctly detected the collision" \
  || { echo "BUG: guard did not report the collision. Output was:"; echo "$out"; false; }
```

Expected: "guard correctly detected the collision".

- [ ] **Step 5: Commit**

```bash
git add scripts/pre-merge-guard.sh scripts/ci-local.sh
git commit -m "feat: ci-local + pre-merge-guard scripts"
```

---

### Task 7: Reference-dir gitignore + final verification + ship

**Files:**
- Modify: `.gitignore`
- Create: `reference/.gitkeep`
- Modify: `docs/plans/001-scaffold-repo.md` (post-execution report)
- Modify: `TODO.md` (mark 001 done)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Gitignore the reference corpus raw material** (public-repo policy, decisions §2)

Create the directory and append to the existing `.gitignore`
(it already exists with `.gh-token` + `build/` entries from the design commits):

```bash
mkdir -p reference && touch reference/.gitkeep
```

```
# Public repo: raw past-test papers stay local-only (copyright).
# Only reference/analysis.md and other original derived work are committed.
reference/*
!reference/.gitkeep
!reference/analysis.md
```

Then verify all ignore rules actually hold — one path at a time
(`git check-ignore` with multiple paths exits 0 if ANY is ignored, so a joint call
would pass with missing rules):

```bash
for p in .gh-token build/x reference/some-paper.pdf; do
  git check-ignore -q "$p" || echo "BUG: $p is not ignored"
done
git check-ignore -q reference/.gitkeep && echo "BUG: .gitkeep must be committed" || true
echo "ignore checks done"
```

Expected: only "ignore checks done", no BUG lines.

- [ ] **Step 2: Full verification**

Run: `bash scripts/ci-local.sh`
Expected: ALL GREEN.
Precondition check for the ship step: `git ls-remote -q origin >/dev/null && echo "origin OK"`
(the GitHub repo weiboz0/usaaio was already created in the design session; this just confirms it).

- [ ] **Step 3: Content-review gate**

Run the 4-way gate per `docs/content-review-gate.md`
(this plan is docs+tooling, so duties reduce to conventional doc/code review).
Record findings in this plan's `## Content Review`; resolve all `[OPEN]`.

- [ ] **Step 4: Post-execution report + TODO, commit**

Write `## Post-execution report` in this plan file (deviations, limitations, follow-ups);
tick 001 in `TODO.md`.

```bash
git add docs/plans/001-scaffold-repo.md TODO.md .gitignore reference/.gitkeep
git commit -m "docs: plan 001 post-execution report"
```

- [ ] **Step 5: PR + guard + merge**

```bash
git push -u origin feature/plan-001-scaffold-repo
GH_TOKEN=$(cat .gh-token) gh pr create --title "Plan 001: scaffold repo" \
  --body "$(cat <<'EOF'
Scaffolds the repo per docs/designs/000-project-design.md milestone 001:
CLAUDE.md, lifecycle docs, uv tools package, ci-local + pre-merge-guard.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
bash scripts/pre-merge-guard.sh --pr
GH_TOKEN=$(cat .gh-token) gh pr merge --squash --delete-branch
```

---

## Out of scope

- No teaching content, no mock tests, no syllabus (plans 002–006).
- No real verification subcommands (plan 004) — CLI stubs exit 2.
- No Quarto/PDF toolchain (plan 006), no torch/sklearn/jupyter deps until a plan needs them.
- **Verification-phase exemption:** this is a docs+tooling plan; it ships no units or mock
  tests, so the design-§2 named verification phase does not apply. Tooling here is covered
  by pytest + the scripted self-checks in Tasks 5–6.

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-03)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` Task 5 Step 3 predicted ImportError, but with `packages = ["tools"]` in
   pyproject and no `tools/` dir yet, `uv run` fails at build/sync time.
   → Response: expected-output text corrected to accept either failure mode.
2. `[NIT]` `ci-local.sh` step 3 relies on `jupyter execute` which is not a declared
   dependency; acceptable because the empty-find branch keeps it unreachable until a plan
   ships notebooks, and that plan must add the dependency. Called out in Task 6 Step 3.
3. Checked: pre-merge-guard dedupe unions names across refs with `sort -u` before
   prefix-dupe detection (same file on both refs is not a collision); conflict-marker
   regex does not self-trigger on the plan file or the script's own source; pytest tests
   match the CLI implementation (argparse `--version` exit 0, subcommand exit 2 with
   "plan 004" on stderr).

Spec-coverage check: every milestone-001 deliverable maps to a task
(docs skeleton T1, CLAUDE.md T2, workflow T3, gate/stub/decisions/TODO T4,
pyproject+tools T5, scripts T6, public-repo gitignore + ship T7).
Verification-phase exemption for a docs+tooling plan is legitimate per design §2
and stated in `## Out of scope`.

### Review 2 — [codex] Codex GPT-5.5 via codex-rescue (2026-08-03)

- **Verdict**: REJECT (round 1) → fixes applied, re-review requested

1. `[FIXED]` BLOCKER: `check_dupes` grep exits 1 on no match; under `set -euo pipefail`
   the guard aborts on any dir without numbered names (e.g. `.gitkeep`-only).
   → Response: `|| true` added inside the command substitution.
2. `[FIXED]` `--pr <number>` documented but the script ignores the argument.
   → Response: docs (CLAUDE.md, workflow, ship steps) now uniformly use plain `--pr`.
3. `[FIXED]` `reference/` dir never created despite gitignore rules for it.
   → Response: Task 7 Step 1 now creates `reference/.gitkeep` with a `!` negation.
4. `[NOTED]` Verification-phase exemption confirmed legitimate.

### Review 3 — [fable] Independent Fable 5, fresh context (2026-08-03)

- **Verdict**: REJECT (round 1) → fixes applied, re-review requested

1. `[FIXED]` Same grep/pipefail BLOCKER as [codex] #1, plus the observation that the
   negative test would "pass" on the crash rather than the detection.
   → Response: `|| true` fix; negative test now asserts the "duplicate docs/plans"
   message, not just the exit code.
2. `[FIXED]` Content-gate roster (Opus) contradicted design §2 "same 4-way roster".
   → Response: design clarified to the PowerMarket convention — Fable slots for
   plan review, Opus slots for content review; CLAUDE.md/gate doc already match.
3. `[FIXED]` Student-notebook hygiene check (design §3.2) had no SKIP line, no
   subcommand, and no owning milestone.
   → Response: `hygiene-check` added to SUBCOMMANDS, ci-local SKIP list,
   TODO 004, and design milestone 004.
4. `[FIXED]` Milestone says "GitHub repo" but no task creates the remote.
   → Response: remote was created in the design session (repo exists, public);
   Task 7 Step 2 now has an explicit `git ls-remote` precondition check.
5. `[FIXED]` `.gitignore`/`.gh-token` entries assumed, not verified.
   → Response: Task 7 Step 1 now runs `git check-ignore` assertions for
   `.gh-token`, `build/`, and `reference/` rules.
6. `[FIXED]` `--pr <number>` doc/interface mismatch — same as [codex] #2.
7. `[WONTFIX]` Conflict-marker regex could false-positive on a 7-`=` setext H1
   underline. → Response: project docs use ATX headings and semantic line breaks;
   a false positive would be visible and trivially resolved, while loosening the
   regex risks missing real `=======` conflict separators.

### Review 4 — [glm] GLM 5.2 via opencode-review (2026-08-03)

- **Verdict**: APPROVE WITH NITS

1. `[FIXED]` Content-gate roster divergence from design — same as [fable] #2
   (resolved by clarifying the design, the direction GLM listed as acceptable).
2. `[FIXED]` `--pr` fetch hard-fails when origin/main is absent.
   → Response: fetch wrapped with a graceful "worktree only" fallback.
3. `[FIXED]` `--pr <number>` doc mismatch — same as [codex] #2.
4. `[FIXED]` Unused `pyyaml` runtime dep. → Response: removed; plan 004 adds it.
5. `[FIXED]` `| head` SIGPIPE brittleness under pipefail in the conflict-marker
   diagnostic. → Response: `|| true` appended.
6. `[WONTFIX]` Seed `units/`/`mocktests/` with `.gitkeep`. → Response: the guard and
   ci-local handle their absence; the dirs appear with the plans that fill them (YAGNI).
7. `[WONTFIX]` docs/README lifecycle line compresses the gate order. → Response: the
   line already names `ci-local.sh` at its verification position; CLAUDE.md is the
   authoritative ordering.

### Round 2 — re-review of commit 49a22ba

- **[fable] VERDICT: APPROVE WITH NITS.** Confirmed all seven round-1 findings genuinely
  fixed. Remaining: multi-path `git check-ignore` passes if ANY path is ignored
  (`[FIXED]` — per-path loop); Task 5 Interfaces list missing `hygiene-check`
  (`[FIXED]`); negative-test failure branch exits 0 (`[FIXED]` — `false` appended).
- **[codex] VERDICT: APPROVE WITH NITS.** Confirmed all three round-1 items fixed.
  Same three nits as [fable], all `[FIXED]` as above.

**GATE RESULT: PASS — 4/4 APPROVE WITH NITS**
([claude-self], [codex], [fable], [glm]); no open blockers. Per CLAUDE-md-to-be and the
adopted workflow, a passing gate authorizes implementation.

## Content Review

(Pre-PR gate findings land here.)
