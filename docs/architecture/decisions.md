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
