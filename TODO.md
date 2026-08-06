# TODO

- [x] 000 — project design (docs/designs/000-project-design.md)
- [x] 001 — scaffold repo (docs/plans/001-scaffold-repo.md)
- [x] 002 — reference corpus (docs/plans/002-reference-corpus.md)
- [x] 003 — syllabus + blueprint (docs/plans/003-syllabus-blueprint.md)
- [x] 004 — verification tooling (docs/plans/004-verification-tooling.md)
- [x] 005 — units tranche 1: F1+F2+C1 (docs/plans/005-foundation-units-1.md)
- [x] 006 — units tranche 2: F4+F3+F5 (docs/plans/006-units-tranche-2.md)
- [x] 007 — units tranche 3: C4+C2+C3 (docs/plans/007-units-tranche-3.md)
- [x] 008 — units tranche 4: C5+C6 (merged)
- [x] 009 — units tranche 5: C7+C8 (merged)
- [x] 010 — units tranche 6: F6+C9+C10 (merged — curriculum complete)
- [x] 011 — first full mock test r1-001 through the pipeline (merged — owns answer-key reproduction + PDF build)
- [x] 012 — course-structure doc (merged — roadmap complete) (units -> semesters/weeks pacing)
- [x] 013 — audit remediation (merged)
- [ ] 014 — enrichment tranche (retag pass, 2 error clinics, F6-p25 synthesis problem, targeted items)

## Deferred, with a named owner plan still to be written

- [ ] softmax + cross-entropy-loss into C5 — deferred from plan 014 Task 3. Must resolve C5's
      capacity explicitly, place the section after `mlp-architecture`, respect the
      no-autograd-training boundary, and note the CE-gradient proof's F4 dependency.
- [ ] **Unit capacity: C7 and C5.** C7 ships 27 problems against the 16–24 band — over it, and
      recorded as non-conformant in `docs/unit-standards.md` rather than excused. C5 carries the
      same unresolved question. Plan 014's gate rejected two attempts to make the overflow legal
      (a concept-scaled ceiling, then a `length: double` marking) and required the capacity
      question be asked directly: split the unit, rehome concepts (`feature-hierarchy`,
      `receptive-field`, `tensor-shape-tracing` are the C7 candidates), or trim. Note 8 of C7's
      27 problems tag no floor-critical concept, so a trim to the band is arithmetically
      available without breaking coverage.
- [ ] **Real tag-honesty enforcement.** `prereq-check`'s `concepts_used` leg is manifest
      consistency only, so it cannot see a decorative tag. Plan 014's gate found 7 decorative
      tags by hand that the check passed. Needs per-problem evidence for each foreign tag.
- [ ] **Ordered prerequisite closure for unit practice.** Closure currently admits any concept
      the unit teaches anywhere, so a concept taught in a later session can satisfy an earlier
      problem. `docs/course-structure.md` §7 claims session-granular integrity that the checker
      does not yet enforce.
- [ ] **Intra-repo overlap detection.** `overlap-scan` compares our problems against the
      external reference corpus only, never against each other. Plan 014's gate caught F6-p25
      shipping as a near-isomorph of F6-p17 — same unit, eight problems apart — by human
      reading alone, after the plan's own corpus duty had checked the mock and the external
      corpus and skipped the unit's own neighbours. A problem-vs-problem pass over
      `units/*/practice/` and `mocktests/` would have caught it mechanically.
- [ ] **Strip stale stored outputs from the 15 solutions that carry them.** 328 of 343 store
      none — that is the convention. The 15 that do (C3-p13 and
      C9-p05..p18) will silently go stale the moment their source is edited, which is exactly how
      plan 014's gate found two of its own solutions printing round-2 values against round-3
      source. Plan 014 cleared the two it touched; the rest are out of its scope.
- [ ] r1-002 / r1-003 via the blueprint's arc rotation (indices 1 and 2).
