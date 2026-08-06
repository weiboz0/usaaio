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
- [ ] **Unit capacity: C7 and C5.** C7 ships 27 problems against the 16–24 band as a recorded
      exception (`docs/unit-standards.md`), and C5 carries the same unresolved question. Plan
      014's gate rejected widening the band and required the capacity question be asked
      directly: split the unit, rehome concepts (`feature-hierarchy`, `receptive-field`,
      `tensor-shape-tracing` are the C7 candidates), or trim.
- [ ] **Real tag-honesty enforcement.** `prereq-check`'s `concepts_used` leg is manifest
      consistency only, so it cannot see a decorative tag. Plan 014's gate found 7 decorative
      tags by hand that the check passed. Needs per-problem evidence for each foreign tag.
- [ ] **Ordered prerequisite closure for unit practice.** Closure currently admits any concept
      the unit teaches anywhere, so a concept taught in a later session can satisfy an earlier
      problem. `docs/course-structure.md` §7 claims session-granular integrity that the checker
      does not yet enforce.
- [ ] r1-002 / r1-003 via the blueprint's arc rotation (indices 1 and 2).
