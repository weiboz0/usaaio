# Mock-Test Generation Pipeline

STUB — this document is completed by plan 003 (syllabus + blueprint).
Until then, the authoritative outline is design 000 §2b:

1. **Blueprint** — `mocktests/blueprint.yaml`, derived from `reference/analysis.md`; versioned.
2. **Instantiate** — `tools new-mocktest r1-NNN` scaffolds the directory + per-slot problem specs.
3. **Draft** — problems/solutions per spec (subagent-dispatched); datasets from seeded scripts.
4. **Verify** — `scripts/ci-local.sh` (design §3 checks).
5. **Gate** — the 4-way content-review gate, including the fidelity review.

Every manifest records blueprint version + generation parameters, so generation is repeatable.
