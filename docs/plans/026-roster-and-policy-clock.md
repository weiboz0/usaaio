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
Those callers reach `tools.model.load_unit_manifests` without an `as_of_date`, so the policy date is `datetime.now(UTC).date()`.
After 2026-09-30 the loader correctly raises `deferred solution_policy expired after 2026-09-30` before the behavior under test is reached.
The production rule is right; the tests are date bombs.
The expired-policy rejection itself remains covered by `tests/test_model.py` (`match="expired after 2026-09-30"`), which passes an explicit date.

## Exact scope

**Modify (governance, user-authorized):**

- `AGENTS.md` — 3-way plan and content gates, py4kids roster table and tags, Opus dispatch for authoring/solutions/tooling, errata diagnosis on GPT-6-sol (fallback GPT-5.6-sol).
- `docs/content-review-gate.md` — same roster, 3-way acceptance, tags `[self]` / `[sol]` / `[fable]`.
- `docs/development-workflow.md` — "4-way" → "3-way" in the two gate references.

**Create:**

- `tests/conftest.py` — a `deferred_policy_window` fixture that monkeypatches `tools.model.datetime` so `now()` returns 2026-09-15 12:00 UTC.
- `docs/plans/026-roster-and-policy-clock.md`

**Modify (tests):**

- `tests/test_b2_019_statements.py` and `tests/test_b2_020_statements.py` — mark the two date-dependent tests with `@pytest.mark.usefixtures("deferred_policy_window")`.
- `TODO.md` at shipping time only.

## Tasks

- [x] Edit the three governance files to the py4kids roster; no other governance text changes.
- [x] Add the fixture and markers; production code unchanged.
- [ ] Run `uv run ruff check tools/ tests/` and the full `uv run pytest -q`; both must be green.
- [ ] Run `scripts/ci-local.sh` (verification phase).
- [ ] Record the 3-way review, post-execution report, tick `TODO.md`, push, PR, `pre-merge-guard --pr`, squash-merge.

## Out of scope

Docs-and-tests-only plan: no unit, mock test, or production tool changes, so it is exempt from the content verification phase and content-review gate (design §2 exemption).
Rounds already begun (Plans 021 and 022 plan gates) keep their recorded rosters; their content gates start after this merges and use the 3-way roster.
The deferred-policy machinery itself is not retired here.

## Plan Review

Pending.

## Post-execution report

Pending.
