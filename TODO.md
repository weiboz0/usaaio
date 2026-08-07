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
- [x] 010 — units tranche 6: F6+C9+C10 (merged — original 16-unit shipped sequence complete)
- [x] 011 — first full mock test r1-001 through the pipeline (merged — owns answer-key reproduction + PDF build)
- [x] 012 — course-structure doc (merged — original shipped schedule documented)
- [x] 013 — audit remediation (merged)
- [x] 014 — enrichment tranche (merged — retag pass, 2 error clinics, F6-p25 synthesis problem, targeted items)
- [x] 015 — layered official-topic audit and R1/R2 roadmap (one curriculum graph, two exit gates)
- [x] 016 — R1 foundation, workflow, and mathematical completion (delivery branch ready)
- [ ] 017 — R1 neural-training completion (active)
- [ ] 018 — R1 classical-model breadth (follows Plan 017)

## Deferred, with a named owner plan still to be written

- [ ] **Execute the remaining Plan 015 content tranches.** The canonical owner/order now lives in
      `curriculum/coverage-map.yaml` and `docs/curriculum-roadmap.md`: R1 neural training,
      R1 classical breadth, R2 transformers/NLP, R2 vision/generative,
      then the R2 GPU capstone. Softmax/cross-entropy are owned by
      `P015-R1-NEURAL-TRAINING`; future work must update the shipped syllabus and roadmap
      atomically rather than maintaining a second gap list here.
- [x] **Unit capacity: C7 and C5.** Plan 017 resolves the decision substantively: C7 gains a
      fourth 90-minute lesson session and remains at 27 practices, satisfying both double-length
      bands. C5 remains a compliant standard-length unit with 22 practices because neural-network
      training moves to C11. `docs/unit-standards.md` preserves the Plan 014 rejection history and
      records why this implemented capacity increase differs from the rejected label-only change.
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
- [ ] **Lint `scripts/` in ci-local.** Step 1 runs `ruff check tools/ tests/` only, so
      `scripts/verify-register.py` — which the gate leaned on heavily and which was edited in
      four rounds — is unlinted. Plan 014 found and fixed a SIM102 there by running ruff wider
      by hand; nothing in CI would have caught it.
- [ ] r1-002 / r1-003 via the blueprint's arc rotation (indices 1 and 2).
