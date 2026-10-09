# Plan 026 — py4kids Review Roster and Deferred-Policy Test Clock

## Goal

Adopt the `../py4kids` model roles for every later review round and dispatch, by user directive on 2026-10-09.
Restore a green unit suite that went red on 2026-10-01 only because two tests read the real clock.

## Trigger and diagnosis

The user directed on 2026-10-09: "use the same model rolls as ../py4kids, and continue with autopilot until completion of the book 2".
`../py4kids` runs a 3-way gate (`[self]` / `[sol]` / `[fable]`): Sol on GPT-6-sol with a GPT-5.6-sol fallback, Fable 5 as a general-purpose subagent, no GLM or DeepSeek.
It dispatches lesson/statement authoring, blind solutions, and tooling to Opus subagents.
The user's explicit request authorizes these governance edits.

Running `uv run pytest -q` on `origin/main` (210bf68) on 2026-10-09 fails two tests:

- `tests/test_b2_019_statements.py::test_named_b2_020_deferred_policy_emits_plan_linked_expiring_debt`
- `tests/test_b2_020_statements.py::test_task4_policy_and_solution_set_fail_closed`

Both write a `deferred` B2-020 `solution_policy` expiring `2026-09-30`.
They then exercise the live-policy path through `check_coverage`, `check_layer_boundary`, and `audit_curriculum.build_inventory`.
Two live-clock reads sit on that path.
`tools.model.load_unit_manifests` is reached without an `as_of_date`, so its policy date is `datetime.now(UTC).date()`.
`tools.checks.schedule._book2_solution_policy` (reached through `build_inventory`) separately requires `expiry_date >= datetime.now(UTC).date()`.
After 2026-09-30 the loader correctly raises `deferred solution_policy expired after 2026-09-30` before the behavior under test is reached.
The production rule is right; the tests are date bombs.
The expired-policy rejection itself remains covered by `tests/test_model.py` (`match="expired after 2026-09-30"`), which passes an explicit date.

## Exact scope

**Modify (governance, user-authorized):**

- `AGENTS.md` — 3-way plan and content gates, py4kids roster table and tags, Opus dispatch for authoring/solutions/tooling, errata diagnosis on GPT-6-sol (fallback GPT-5.6-sol).
- `docs/content-review-gate.md` — same roster, 3-way acceptance, tags `[self]` / `[sol]` / `[fable]`.
- `docs/development-workflow.md` — "4-way" → "3-way" in the two gate references.

**Create:**

- `tests/conftest.py` — a function-scoped `deferred_policy_window` fixture that monkeypatches `datetime` in both `tools.model` and `tools.checks.schedule` so `now()` returns 2026-09-15 12:00 UTC (naive when called without a tz).
- `docs/plans/026-roster-and-policy-clock.md`

**Modify (tests):**

- `tests/test_b2_019_statements.py` and `tests/test_b2_020_statements.py` — mark the two date-dependent tests with `@pytest.mark.usefixtures("deferred_policy_window")`.

**Modify (non-governance docs, from content review):**

- `docs/README.md` and `docs/mocktest-generation.md` — "4-way" → "3-way" gate references.
- `docs/designs/000-project-design.md` — §2 gate roster and dispatch rows point to `AGENTS.md` as authoritative and mark earlier rosters historical.

**Modify at shipping time only:** `TODO.md`.

## Tasks

- [ ] Edit the three governance files to the py4kids roster; no other governance text changes.
- [ ] Add the fixture and markers; production code unchanged.
- [ ] Run `uv run ruff check tools/ tests/` and the full `uv run pytest -q`; both must be green.
- [ ] Run `scripts/ci-local.sh` (verification phase).
- [ ] Run the 3-way content-review gate (as conventional code/doc review of this diff) and record it in `## Content Review`.
- [ ] Record the post-execution report, tick `TODO.md`, push, PR, `pre-merge-guard --pr`, squash-merge.

## Out of scope

Docs-and-tests-only plan: no unit, mock test, or production tool changes, so it is exempt from the named content verification phase (design §2 exemption).
It is not exempt from the pre-PR content-review gate, which reviews this diff as conventional code and doc review.
Rounds already begun (Plans 021 and 022 plan gates) keep their recorded rosters; their content gates start after this merges and use the 3-way roster.
The deferred-policy machinery itself is not retired here.

## Plan Review

Roster: py4kids 3-way (`[self]` / `[sol]` / `[fable]`), the roster this plan adopts.

### Review 1 — self (2026-10-09)
- **Verdict**: Approve with nits.
1. `[FIXED]` Full `pytest -q` at 74b9933 showed 1 failed / 1183 passed; the B2-019 debt test still failed (same root cause as Fable 1).

### Review 1 — Sol, GPT-6-sol (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the out-of-scope section claimed a content-review-gate exemption; design §2 exempts only the verification phase. → Response: exemption narrowed; content-gate task added.
- Governance fidelity, fixture scoping, and retained expiry coverage confirmed.

### Review 1 — Fable (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: `tools/checks/schedule.py:425` reads the clock independently, so `build_inventory` still failed. → Response: the fixture now patches `tools.checks.schedule.datetime` too; diagnosis corrected. Affected files: 209 passed.
2. `[FIXED]` Should Fix: tasks were ticked before the green suite ran. → Response: unticked until verified.
3. `[FIXED]` Nit: naive `now()` stand-in returned an aware datetime. → Response: returns naive for `tz=None`.

### Review 2 — self (2026-10-09)
- **Verdict**: Approve. Affected files 209 passed at 05c9b00; full CI is the plan's own verification task.

### Review 2 — Sol (2026-10-09; requested `gpt-6-sol`, model self-reported "GPT-6-astra")
- **Verdict**: Approve with nits.
1. `[WONTFIX]` Nit: `tests/test_scope.py:377` uses `review_after: 2099-01-01` against the real clock at `tools/checks/scope.py:268`. → Response: not a date bomb before 2099 and outside this plan's two failing tests.

### Review 2 — Fable (2026-10-09)
- **Verdict**: Approve. No new findings; 209 passed on the three affected files.

**Gate result:** 3-way consensus at 05c9b00; implementation authorized.

## Content Review

Roster: 3-way (`[self]` / `[sol]` / `[fable]`), reviewing this diff as code and doc review.

### Review 1 — self (2026-10-09)
- **Verdict**: Approve with suggestions. Unit tests 1184 passed. `ci-local.sh` failed only at the Book 1 C12 p20 solution notebook (pre-existing `main` near-tie bug owned by Plan 022). See the post-execution report for the paired 026+022 CI run.

### Review 1 — Sol (2026-10-09)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: the round-2 plan-gate Sol entry recorded a self-reported "GPT-6-astra" model, so the slot's model was unproven. → Response: Codex's own session rollouts for 2026-10-09 (`~/.codex/sessions/2026/10/09/rollout-*.jsonl`, all four review sessions) record `"model":"gpt-6-sol"`. The model's self-description is not authoritative; the rollout metadata is.
2. `[FIXED]` Must Fix: four-reviewer instructions remained in `docs/designs/000-project-design.md`, `docs/README.md` and `docs/mocktest-generation.md`. → Response: all three now describe the 3-way roster; the design doc defers to `AGENTS.md` as authoritative and labels earlier rosters historical.

### Review 1 — Fable (2026-10-09)
- **Verdict**: Approve with nits.
1. `[FIXED]` Should Fix: `docs/README.md` and `docs/mocktest-generation.md` still said "4-way" (same as Sol 2).
2. `[FIXED]` Nit: `TODO.md` was listed under test modifications. → Response: moved to its own line.
3. `[FIXED]` Nit: the solution-dispatch row should state that authoring-side independence is session-level only. → Response: `AGENTS.md` row updated.

### Review 2 — self (2026-10-09)
- **Verdict**: Approve.

### Review 2 — Sol (2026-10-09; rollout metadata `gpt-6-sol`)
- **Verdict**: Reject.
1. `[FIXED]` Must Fix: `## Exact scope` omitted `docs/designs/000-project-design.md`. → Response: added at 1c8fe7e.

### Review 3 — Sol (2026-10-09; rollout `rollout-2026-10-09T12-36-20-…` records `gpt-6-sol`, although the model self-described as "GPT-6-astra")
- **Verdict**: Approve with nits.
1. `[FIXED]` Nit: this record pre-stated Sol's approval before Sol issued it. → Response: rounds 2 and 3 are now separate entries with Sol's actual verdicts.

### Review 2 — Fable (2026-10-09)
- **Verdict**: Approve with nits.
1. `[WONTFIX]` Nit: Plan 020's task text still names a four-way content gate. → Response: Plan 020 shipped as PR #24; that task line is a historical record, not a pending round.
2. `[FIXED]` Nit: the post-execution report must be filled before the PR. → Response: filled at shipping.

**Gate result:** 3-way consensus (self Approve, Sol Approve with nits in round 3, Fable Approve with nits in round 2) at 1c8fe7e plus this record-only update.

## Post-execution report

Pending.
