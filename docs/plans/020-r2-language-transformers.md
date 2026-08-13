# Plan 020 — Round 2 Language Transformers

## Goal

Ship `book2/units/B2-020-language-transformers` as the second independently complete Book 2 unit.
It closes the remaining model-training gap for word embeddings and the four missing Round 2 language rows: NLP Transformers, pretraining, fine-tuning, and Transformer NLP applications.
It also replaces the temporary single-unit Book 2 schedule contract with a manifest-driven multi-unit contract before a second live unit is added.

## Branch and baseline

- Branch: `feature/plan-020-language-transformers`.
- Base: `ab795cd`, the squash merge of Plan 019 / PR #22.
- Content baseline: Book 1 has 19 units and Book 2 has one live double-length unit, B2-019, with 11 Book 2-owned concepts, 24 practices, six local weeks, and 1,660 scheduled minutes.
- Verification environment: prepend `/home/chris/.local/bin` to `PATH` for `uv`.
  The private `book1/reference/r1-2026/` corpus is mounted locally and remains ignored; no raw reference, student data, cache, or credential is ever staged.

## Scope and curricular boundary

B2-020 is a 26–32-hour, double-length Round 2 extension unit.
It has a 30-minute bridge diagnostic, five 90-minute lessons, 24 practices totaling 1,120 minutes, and a 60-minute review: 1,660 minutes / 27.67 hours of scheduled study time.
It occupies Book 2 local weeks 7–12 and global weeks 47–52.

Its prerequisite-unit list is exactly `[B2-019-attention-transformers]`.
Its manifest `concepts_used` and `concept_prerequisites` are exactly the concepts actually consumed by the teaching surface: B2-019's `attention-mask`, `causal-self-attention`, `sinusoidal-positional-encoding`, and `transformer-block`; plus Book 1's `book1:random-seeding`, `book1:matrix-multiplication`, `book1:torch-tensors`, `book1:nn-module`, `book1:requires-grad`, `book1:tensor-shape-tracing`, `book1:softmax`, `book1:cross-entropy-loss`, `book1:torch-optimizers`, and `book1:autograd-training`.
Those qualified Book 1 concepts are already authorized by B2-019's transitive prerequisite closure; B2-020 records the exact used subset rather than treating that closure as an implicit permission.
The bridge may link `book1:C8-embeddings` for remediation, but must never relabel the Book 1 evidence-import concepts as B2-020-owned or add them to the manifest closure.

The unit depends on `B2-019-attention-transformers`.
It reuses Book 1 C8 only as a qualified remediation reference for token-to-index and fixed-vector vocabulary, and it reuses B2-019 for the Transformer block and causal mask.
It must not re-teach tokenization, GloVe loading, or fixed-vector similarity.
All corpora, labels, vocabulary maps, seeds, expected probes, and checkpoints are small, explicit, synthetic, CPU-only, and committed as source-generation code or literal notebook data.
No internet model hub, external dataset, opaque checkpoint, tokenizer library, or hidden pretrained parameter is in scope.

### Owned concepts

B2-020 owns exactly these eight Book 2 concepts, all introduced once in the stated session and practiced directly at least three times:

1. `embedding-model-training` — Session 1.
2. `learned-token-embedding` — Session 1.
3. `language-transformer` — Session 2.
4. `causal-language-modeling` — Session 2.
5. `masked-language-modeling` — Session 3.
6. `nlp-pretraining-objectives` — Session 3.
7. `nlp-fine-tuning-protocol` — Session 4.
8. `transformer-nlp-task-design` — Session 5.

The embedding bridge trains a token-embedding matrix from scratch by multiplying explicit one-hot rows by a trainable table and optimizing a context-to-target softmax objective.
It therefore supplies the missing `model-training` evidence for `nlp-word-embeddings` without claiming ownership of Book 1's `word-embeddings` or `embedding-matrices` concepts.

### Five-session teaching spine

| Session | File | Required teaching surface |
|---:|---|---|
| 1 | `01-train-token-embeddings.ipynb` | one-hot lookup, embedding table shapes, context-to-target objective, cross-entropy gradient flow, seeded embedding training, and fixed versus learned-vector boundary |
| 2 | `02-causal-transformer-language-model.ipynb` | token/position inputs, causal attention reuse from B2-019, shift-right labels, logits and token loss shapes, and tiny causal LM training |
| 3 | `03-pretraining-objectives.ipynb` | causal next-token versus masked-token objectives, corruption/masking protocol, leakage counterexamples, objective selection, and reproducible pretraining traces |
| 4 | `04-fine-tune-a-language-transformer.ipynb` | attach a task head, checkpoint/state boundary, frozen versus trainable parameters, supervised classification fine-tuning, and held-out evaluation |
| 5 | `05-language-task-design-and-audit.ipynb` | classify, tag, generate, and retrieve task framing; architecture/loss/metric choice; data-split and leakage audit; complete end-to-end application trace |

Each session contains 6–10 substantive sections, at least two checkpoints per section with collected answers, two worked examples across the unit, a common-pitfalls surface, an exam-connections surface, and a forward-only going-deeper surface.
Every overview, bridge, lesson, review, practice, and solution visibly states `Round 2 extension`, `compute.policy: cpu`, and the qualified remediation links that it actually uses.

### Exact practice ledger

All student notebooks are unexecuted and contain no solution text.
Coding and training statements pin identifiers, shapes, dtypes, seeds, allowed and banned APIs, probes, `atol`, and `rtol`.
Every independently authored solution ends with `### Answer check` and executable assertions that reject a named plausible mutant.

| ID | Set | Type | Difficulty | Minutes | Primary scored contract |
|---|---|---|---|---:|---|
| p01 | A | mc | intro | 20 | distinguish fixed embeddings from a table trained by a predictive loss |
| p02 | A | mc-normal-form | intro | 20 | one-hot lookup, context logit, and normalized target probability |
| p03 | A | mc | core | 20 | predict which embedding rows receive gradient under a pinned context objective |
| p04 | A | mc | intro | 20 | choose a causal-label shift and reject target-token leakage |
| p05 | A | mc | core | 20 | choose causal or masked pretraining for a stated language task |
| p06 | B | constrained-coding | intro | 50 | one-hot matrix embedding lookup with exact shape and row probes |
| p07 | B | constrained-coding | core | 50 | train a seeded context-to-target embedding table and certify loss/row movement |
| p08 | B | constrained-coding | core | 50 | build causal-LM inputs, targets, and logits with exact sequence axes |
| p09 | B | constrained-coding | advanced | 50 | integrate a B2-019 causal Transformer block into a tiny language model |
| p10 | B | constrained-coding | core | 50 | mean token cross-entropy with explicit padding/loss mask contract |
| p11 | B | constrained-coding | intro | 50 | construct a masked-token corruption objective without observing the original token |
| p12 | B | constrained-coding | intro | 50 | attach a sequence-classification head and audit frozen/trainable parameters |
| p13 | B | proof | core | 45 | derive why only selected one-hot embedding rows receive direct lookup gradient |
| p14 | B | proof | core | 45 | prove a causal-logit at position i cannot depend on a future token under the mask contract |
| p15 | B | proof | core | 45 | derive token-level negative log likelihood as a maximum-likelihood objective |
| p16 | B | proof | core | 45 | show the true token leaks when it remains visible in a masked-token input |
| p17 | C | integrative | advanced | 65 | train and audit the seeded embedding bridge, including loss and nearest-neighbor change certificates |
| p18 | C | integrative | advanced | 65 | train a tiny causal Transformer LM and validate shifted predictions and held-out loss |
| p19 | C | scenario | core | 65 | compare causal and masked pretraining traces and select an objective for a stated deployment task |
| p20 | C | integrative | advanced | 65 | fine-tune the committed tiny encoder/checkpoint on a synthetic intent-classification task |
| p21 | C | integrative | core | 65 | run a freeze-then-unfreeze protocol and certify which parameter groups changed |
| p22 | C | scenario | intro | 55 | select a Transformer NLP task formulation, head, loss, and evaluation metric |
| p23 | C | challenge | advanced | 55 | reconstruct a language-model forward/loss shape trace and repair an off-by-one target error |
| p24 | C | challenge | advanced | 55 | identify and repair pretraining/fine-tuning leakage or frozen-head failure from a concrete training log |

The ledger is exactly 7 intro, 11 core, and 6 advanced practices; 5 MC (where `mc-normal-form` is a scored MC subtype), 7 constrained coding, 4 proof, 4 integrative, 2 scenario, and 2 challenge practices.
Set A is p01–p05, Set B is p06–p16, and Set C is p17–p24.

### Owned-concept practice map

| Owned concept | Direct practices |
|---|---|
| `embedding-model-training` | p01, p07, p13, p17 |
| `learned-token-embedding` | p02, p03, p06, p17 |
| `language-transformer` | p04, p08, p09, p18, p23 |
| `causal-language-modeling` | p04, p08, p14, p18, p23 |
| `masked-language-modeling` | p05, p11, p16, p19 |
| `nlp-pretraining-objectives` | p05, p15, p16, p19, p24 |
| `nlp-fine-tuning-protocol` | p12, p20, p21, p24 |
| `transformer-nlp-task-design` | p19, p20, p22, p24 |

### Exact six-week schedule ledger

| Book week | Global week | Allocation | Minutes |
|---:|---:|---|---:|
| 7 | 47 | bridge 30; Session 1 90; p01, p02, p06, p13 | 255 |
| 8 | 48 | Session 2 90; p03, p04, p07, p08, p14 | 275 |
| 9 | 49 | Session 3 90; p05, p09, p10, p15, p16, p17, p23 | 420 |
| 10 | 50 | Session 4 90; p11, p18, p21 | 270 |
| 11 | 51 | Session 5 90; p12, p19, p20, p22, p24 | 380 |
| 12 | 52 | review 60; future R2 final-assessment marker | 60 |

The Book 2 schedule becomes 12 local weeks, 3,320 total scheduled minutes, and a final-assessment marker after Book week 12.
The 255/275/420/270/380/60 progression matches B2-019's proven six-week cadence: it front-loads a runnable embedding model, peaks during objective/derivation work, and reserves the final week for retrieval practice and review.

### Required coverage evidence

| Knowledge point | Modalities | Direct practice evidence |
|---|---|---|
| `nlp-word-embeddings` | theory, implementation, model-training | p01, p02, p03, p06, p07, p13, p17 |
| `nlp-transformers` | theory, implementation, model-training | p04, p08, p09, p14, p18, p23 |
| `nlp-pretraining` | theory, implementation, model-training | p05, p11, p15, p16, p19, p24 |
| `nlp-fine-tuning` | theory, implementation, model-training | p12, p20, p21, p24 |
| `transformer-nlp-applications` | theory, implementation, model-training | p09, p18, p20, p22, p23 |

Each row receives a primary lesson anchor and at least one primary practice for every listed modality.
The coverage map promotes exactly these five rows to covered and leaves B2-021 through B2-024 targets untouched.

## Schedule and checker contract

Plan 019 deliberately hard-coded its first live unit in `tools/checks/schedule.py`.
Before B2-020 is live, replace that bootstrap contract with a data-driven Book 2 ledger:

- discover every non-symlinked `units/*/manifest.yaml` under the selected Book 2 root;
- require its manifest `unit` to have exactly one bridge, all declared lesson sessions, every practice ID exactly once, and exactly one review allocation;
- reconcile allocated minutes and `after_session` against each manifest rather than module-level B2-019 constants;
- require every live manifest path to be contained, regular, and present;
- derive Book 2 total weeks/minutes, `covered_problem_ids`, course-structure wording, and audit counts from the ledger;
- retain Plan 019's accepted six-week/1,660-minute ledger unchanged and prove that B2-020 adds its separate six-week/1,660-minute ledger without reordering or weakening it.

Tests must first demonstrate rejection of a second manifest by the legacy singleton validator, then demonstrate the generic validator accepting both valid unit ledgers and rejecting: a duplicate problem across units, a missing B2-020 lesson allocation, a mismatched practice minute, an after-session violation, an escaped/symlinked path, a stale total, and an attempt to mutate B2-019's pre-existing ledger.

## Permanent answer-affecting mutations

Create `tools/verify_language_transformer_mutations.py` and `tests/test_language_transformer_mutations.py` using the same fail-closed source-match and wrapped-real-answer-check pattern as Plan 019.
The untouched corpus must pass all five mutations; each altered solution must fail its named answer assertion:

1. `practice/p07_solution.ipynb` — replace the exact context-to-target optimizer-update statement with a no-update table;
2. `practice/p18_solution.ipynb` — replace the exact shifted-target assignment (`targets = token_ids[:, 1:]`) with the unshifted input tokens;
3. `practice/p11_solution.ipynb` — replace the exact masked-position assignment with the original true token;
4. `practice/p21_solution.ipynb` — replace the exact frozen-stage encoder parameter policy so it updates during the declared frozen stage;
5. `practice/p24_solution.ipynb` — replace the exact held-out membership assertion so a training row is evaluated as held out.

The mutation runner must reject zero/multiple source matches, an expected-check marker outside one top-level assertion, a mutant that executes without failure, and a failure in the wrong check.

## Implementation tasks

### Task 1 — Make the Book 2 schedule multi-unit before adding content

**Files:**

- Modify: `tools/checks/schedule.py`
- Modify: `tests/test_book2_schedule.py`

- [ ] Write focused failing tests for the two-live-manifest ledger and all named negative mutations above.
- [ ] Replace only the B2-019 singleton assumptions with the generic per-manifest ledger contract; do not change Book 1 scheduling semantics or allow unregistered units.
- [ ] Preserve the live B2-019 schedule byte-level allocation semantics and the live six-week/1,660-minute ledger.
  Do not append B2-020 to the live schedule until Task 3 creates its manifest and every declared statement-side path.
  Use copied two-manifest fixtures to prove the generic validator before any second live manifest exists.
- [ ] Run `PATH=/home/chris/.local/bin:$PATH uv run pytest -q tests/test_book2_schedule.py`.
- [ ] Commit: `test: generalize Book 2 schedule ledger`.

### Task 2 — Add B2-020 ownership, closure, and generated evidence contracts

**Files:**

- Modify: `book2/syllabus.md`
- Modify: `docs/unit-standards.md`
- Test: new assertions in `tests/test_b2_020_statements.py`

- [ ] Add the `language-transformers` cluster, the eight owned concepts, and B2-020's exact unit/prerequisite/concept-prerequisite contract to Book 2's canonical syllabus.
- [ ] Make B2-020 double-length in both syllabus and manifest contract and extend the standards roster without altering the recorded C7 non-conformance history.
- [ ] Register the ownership and prerequisite contract only; leave each B2-020 coverage row missing/partial until Task 3 has created the referenced statement paths and manifest.
- [ ] Do not render inventory, Book 2 course structure, or aggregate evidence in this task; Task 3 owns their first valid regeneration.
- [ ] Commit: `docs: register language Transformer coverage`.

### Task 3 — Author the statement-side teaching corpus

**Files:**

- Create: `book2/units/B2-020-language-transformers/manifest.yaml`
- Create: `book2/units/B2-020-language-transformers/lesson.ipynb`
- Create: `book2/units/B2-020-language-transformers/review.ipynb`
- Create: `book2/units/B2-020-language-transformers/lessons/00-book1-bridge.ipynb` through `lessons/05-language-task-design-and-audit.ipynb`
- Create: `book2/units/B2-020-language-transformers/practice/p01.ipynb` through `p24.ipynb`
- Create: `book2/units/B2-020-language-transformers/scripts/generate_language_data.py`
- Modify: `book2/curriculum/course-schedule.yaml`
- Modify: `book2/curriculum/coverage-map.yaml`
- Modify: `book2/curriculum/material-inventory.yaml` (generated)
- Modify: `book2/docs/course-structure.md` (generated)
- Modify: `docs/curriculum-roadmap.md` and `docs/audits/015-coverage-audit.md` (generated)
- Test: `tests/test_b2_020_statements.py`

- [ ] Dispatch a fresh GPT-5.6-sol statement-authoring session with the approved Plan 020 scope, but no solution outlines.
- [ ] Require a bridge diagnostic that distinguishes imported fixed-vector/token-index remediation from B2-019's attention/causal-mask prerequisite and supplies qualified remediation links.
- [ ] Create the overview, five lessons, review, generator, and all 24 final student statements to the ledger; no solutions, executed outputs, external corpus, hidden state, or pretrained checkpoint may enter a student notebook.
- [ ] Pin `compute.policy: cpu`, fixed seed `20260812`, every session/practice minute, all source/solution paths, exact prerequisite lists, and concept tags.
- [ ] Exercise all eight owned concepts with at least three direct practices and ensure no problem tags a concept outside the unit/prerequisite closure.
- [ ] In the same commit that creates the manifest, append the exact B2-020 weeks 7–12/global weeks 47–52 ledger above and its post-week-12 final-assessment marker.
  Then promote exactly the five named coverage rows with literal lesson anchors and evidence IDs, and regenerate/check the inventory, Book 2 course structure, roadmap, and audit from the now-valid paths.
- [ ] Test hygiene, lesson order, manifest paths, source isolation, CPU label, imported-concept boundary, time arithmetic, and coverage tags without executing student notebooks.
- [ ] Commit: `feat: teach language Transformer statements`.

### Task 4 — Blind-author and execute solutions

**Files:**

- Create: `book2/units/B2-020-language-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`

- [ ] Dispatch a separate fresh GPT-5.6-sol solution session with only committed student statements and the manifest, never the author outline or statement session context.
- [ ] Require each solution to preserve the learner-visible header, use the seeded literal data, state every answer, and end with a non-vacuous `### Answer check` plus exact numeric/shape/training assertions.
- [ ] Execute p01–p24 in numeric order on a fresh kernel and prove the answer register, source isolation, student hygiene, and required-solution policy pass.
- [ ] Commit: `feat: add independently solved language practices`.

### Task 5 — Lock coverage and language-model failure modes

**Files:**

- Create: `tools/verify_language_transformer_mutations.py`
- Create: `tests/test_language_transformer_mutations.py`
- Modify: `scripts/ci-local.sh`
- Modify: `tests/test_b2_020_statements.py`

- [ ] Implement the five named answer-affecting mutations and the fail-closed runner contract.
- [ ] Wire the new mutation runner into the Book 2 portion of local CI after the existing attention runner.
- [ ] Prove every exact source/cell mutation fails its intended answer check, the untouched corpus passes, and generic runner fault modes fail closed.
- [ ] Commit: `test: lock language Transformer evidence`.

### Task 6 — Verification, content gate, report, and merge

**Files:**

- Modify: `docs/plans/020-r2-language-transformers.md`

- [ ] Run all relevant focused tests, execute every B2-020 solution and lesson fresh, regenerate/check all Book 2 and aggregate evidence, and run the full local gate:

```bash
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/ci-local.sh
PATH=/home/chris/.local/bin:$PATH UV_CACHE_DIR=/tmp/uvcache bash scripts/pre-merge-guard.sh --pr
```

- [ ] Run the post-cutoff four-way content gate: active-session self-review, fresh GPT-5.6-sol, GLM 5.2, and fresh Fable 5. Each reviewer blind-solves student notebooks before reading solutions.
- [ ] Resolve every `[OPEN]` item, rerun affected verification, append the exact evidence and reviewer verdicts below, and commit the post-execution report.
- [ ] Push the feature branch, open a PR with the configured SSH origin and `.gh-token`, rerun `scripts/pre-merge-guard.sh --pr`, then squash-merge from outside this worktree.

## Out of scope

- B2-021 through B2-024 content and their coverage rows.
- A public model hub, large corpus, GPU requirement, raw past-paper content, external tokenizer, or pretrained download.
- Any modification to Book 1's shipped C8 lesson, ownership, or its existing fixed-vector evidence.
- A Round 2 mock test; the scheduled final assessment remains a future marker until its dedicated plan.

## Plan Review

### Review 1 — self (2026-08-12)

- **Verdict**: APPROVE.
- The unit closes exactly the five B2-020 rows, including the previously partial
  word-embedding row's missing model-training modality, without taking ownership of Book 1
  tokenization or fixed-vector concepts.
- The 24-problem ledger satisfies the double-length count, type, difficulty, per-concept
  practice, and 1,120-minute contracts; its 450 lesson + 1,120 practice + 60 review + 30
  bridge arithmetic is exactly 1,660 minutes across weeks 7–12.
- The plan names a prerequisite-closed eight-concept ownership surface, direct evidence for
  every required modality, five answer-affecting mutants, an implementation sequence that
  repairs the singleton schedule contract before adding the second manifest, and a full
  verification/content-gate phase.
- No `[OPEN]` blocker remains from self-review.

Pending independent reviews: `[sol]`, `[glm]`, and `[fable]`.

### Review 1 — sol (2026-08-12)

- **Verdict**: REJECT.
- `[sol][FIXED]` p21 was allocated after Session 3 despite practicing the Session 4 fine-tuning protocol.
  The ledger now swaps p17 and p21, preserving every weekly total while placing p21 after Session 4.
- `[sol][FIXED]` the difficulty/type totals were inconsistent with the ledger and had only one scenario.
  p11 is intro, p15 is core, p19 is scenario, and the checked summary is now 7/11/6 and 5/7/4/4/2/2.
- `[sol][FIXED]` B2-020 had omitted qualified Book 1 prerequisites it directly consumes.
  The plan now pins the exact imported concept subset through B2-019's transitive closure.
- `[sol][FIXED]` two mutation entries named alternative targets.
  The mutation contract now gives each of five mutations one notebook and one source statement.

### Review 1 — fable (2026-08-12)

- **Verdict**: REJECT.
- `[fable][FIXED]` confirmed the same ledger arithmetic and p21 teaching-order defects as Sol.
- `[fable][FIXED]` Task 1 would have made a live B2-020 schedule before its manifest existed.
  It now validates only copied two-manifest fixtures; Task 3 atomically creates the live manifest, paths, schedule ledger, coverage evidence, and generated artifacts.
- `[fable][FIXED]` the per-owned-concept three-practice claim was not auditable.
  The owned-concept practice map now names every qualifying practice.
- `[fable][FIXED]` Task 2's generated-artifact file list contradicted its own path-existence guard.
  Regeneration now occurs only in Task 3 after statement paths exist.
- `[fable][FIXED]` the plan now specifies that `mc-normal-form` rolls up as the fifth MC and removes the ambiguous "repeated" schedule wording.

The first GLM runtime completed but its ephemeral output was unavailable after the wrapper session closed.
The amended commit starts a fresh independent GLM review rather than treating that inaccessible result as a verdict.

## Content Review

Pending implementation and four-way blind review.

## Post-execution report

Pending implementation, verification, review, PR guard, and squash merge.
