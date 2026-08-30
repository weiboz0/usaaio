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

Its prerequisite-unit list is exactly `[book1:F1-scientific-python, book1:F3-matrices, book1:C6-pytorch, book1:C7-cnn-transfer, book1:C11-neural-training, B2-019-attention-transformers]`.
Its manifest `concepts_used` and `concept_prerequisites` are exactly the concepts actually consumed by the teaching surface: B2-019's `attention-mask`, `causal-self-attention`, `sinusoidal-positional-encoding`, and `transformer-block`; plus Book 1's `book1:random-seeding`, `book1:matrix-multiplication`, `book1:torch-tensors`, `book1:nn-module`, `book1:requires-grad`, `book1:tensor-shape-tracing`, `book1:softmax`, `book1:cross-entropy-loss`, `book1:torch-optimizers`, and `book1:autograd-training`.
The five direct qualified Book 1 units are required because the current checker does not propagate qualified imports through an unqualified same-book prerequisite; they put every declared Book 1 concept in the checked closure rather than relying on an implicit transitive permission.
The bridge may link `book1:C8-embeddings` for remediation, but must never relabel the Book 1 evidence-import concepts as B2-020-owned or add them to the manifest closure.
`book1:C8-embeddings` is deliberately absent from the prerequisite-unit list: B2-020 consumes no C8-owned concept, and the bridge's remediation link is reachable transitively through B2-019, which does declare C8. The list names only units supplying a concept in the checked closure.

The unit depends on `B2-019-attention-transformers`.
It reuses Book 1 C8 only as a qualified remediation reference for token-to-index and fixed-vector vocabulary, and it reuses B2-019 for the Transformer block and causal mask.
It must not re-teach tokenization, GloVe loading, or fixed-vector similarity.
All corpora, labels, vocabulary maps, seeds, expected probes, and checkpoints are small, explicit, synthetic, CPU-only, and committed as source-generation code or literal notebook data.
No internet model hub, external dataset, opaque checkpoint, tokenizer library, or hidden pretrained parameter is in scope.
Every CPU training task uses vocabulary size at most 12, sequence length at most 8, one Transformer block with embedding/attention width at most 8 (the feed-forward inner width is separately pinned at 16), at most two heads, and at most 80 fixed optimization epochs; a fresh solution notebook must finish within 20 seconds.
CI enforces a plain per-notebook 20-second wall-clock timeout on fresh solution execution; the Task-5 integrity tests re-execute variant-substituted copies of the five concept-critical solutions and allow up to 120 seconds each. No execution harness, mutation client, or injected-deadline machinery is required.

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
| 2 | `02-causal-transformer-language-model.ipynb` | token inputs plus B2-019's sinusoidal positional table, causal attention reuse from B2-019, shift-right labels, logits and token loss shapes, and tiny causal LM training |
| 3 | `03-pretraining-objectives.ipynb` | causal next-token versus masked-token objectives, corruption/masking protocol, leakage counterexamples, objective selection, reproducible pretraining traces, and the pretraining stack's two architecture deltas from B2-019's block — learned positional embeddings (replacing B2-019's sinusoidal table) and a GELU feed-forward activation — plus the optimizer AdamW introduced as Adam with decoupled weight decay (zeroed to `0` here, so numerically Adam) before p19 pins it |
| 4 | `04-fine-tune-a-language-transformer.ipynb` | attach a task head, checkpoint/state boundary, frozen versus trainable parameters, supervised classification fine-tuning, and held-out evaluation |
| 5 | `05-language-task-design-and-audit.ipynb` | classify, tag, generate, and retrieve task framing; architecture/loss/metric choice; data-split and leakage audit; complete end-to-end application trace |

Each session contains 6–10 substantive sections, at least two checkpoints per section with collected answers, a common-pitfalls surface, an exam-connections surface, and a forward-only going-deeper surface.
Session 1 contains the first fully worked example (one-hot lookup through context-to-target cross-entropy and one embedding-gradient update), and Session 4 contains the second (one frozen-encoder classification step and the parameter-change audit).
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
| p19 | C | scenario | core | 65 | run seeded causal and masked pretraining objectives, certify each initial/final loss, then select an objective for a stated deployment task |
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
| `causal-language-modeling` | p04, p08, p10, p14, p18, p23 |
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
| 10 | 50 | Session 4 90; p12, p18, p21 | 270 |
| 11 | 51 | Session 5 90; p11, p19, p20, p22, p24 | 380 |
| 12 | 52 | review 60 | 60 |

The Book 2 schedule becomes 12 local weeks, 3,320 total scheduled minutes, and a `final_assessment.after_book_week: 12` future-R2 marker after Book week 12.
The 255/275/420/270/380/60 progression matches B2-019's proven six-week cadence: it front-loads a runnable embedding model, peaks during objective/derivation work, and reserves the final week for retrieval practice and review.

### Required coverage evidence

| Knowledge point | Modalities | Direct practice evidence |
|---|---|---|
| `nlp-word-embeddings` | theory, implementation, model-training | p01, p02, p03, p06, p07, p13, p17 |
| `nlp-transformers` | theory, implementation, model-training | p04, p08, p09, p10, p14, p18, p23 |
| `nlp-pretraining` | theory, implementation, model-training | p05, p11, p15, p16, p19, p24 |
| `nlp-fine-tuning` | theory, implementation, model-training | p12, p20, p21, p24 |
| `transformer-nlp-applications` | theory, implementation, model-training | p09, p18, p20, p22, p23 |

Each row receives a primary lesson anchor and at least one primary practice for every listed modality.
The coverage map promotes exactly these five rows to covered and leaves B2-021 through B2-024 targets untouched.

## Schedule and checker contract

Plan 019 deliberately hard-coded its first live unit in `tools/checks/schedule.py`.
Before B2-020 is live, replace that bootstrap contract with a data-driven Book 2 ledger:

- enumerate every `units/*` entry under the selected Book 2 root and reject any symlinked unit directory or manifest before ledger discovery; every regular unit directory must contain exactly one regular, contained `manifest.yaml`, and a missing, extra, or nonregular manifest is a hard error rather than an invisible directory; any non-directory entry directly under `units/` is likewise a hard error;
- require each remaining regular manifest to declare the one Book 2 bridge diagnostic required by Design 019, all declared lesson sessions, every practice ID exactly once, and exactly one review allocation;
- reconcile allocated minutes and `after_session` against each manifest rather than module-level B2-019 constants;
- require every live manifest path to pass `tools.books.resolve_contained_path()` realpath containment, then be regular and present;
- derive Book 2 total weeks/minutes, `covered_problem_ids`, course-structure wording, and audit counts from the ledger;
- retain Plan 019's accepted six-week/1,660-minute ledger unchanged and prove that B2-020 adds its separate six-week/1,660-minute ledger without reordering or weakening it; every B2-020 allocation (bridge, lesson, practice, review, or final marker) begins strictly after B2-019's final-review allocation.

Tests must first demonstrate rejection of a second manifest by the legacy singleton validator, then demonstrate the generic validator accepting both valid unit ledgers and rejecting: a duplicate problem across units, a missing B2-020 lesson allocation, a mismatched practice minute, an after-session violation, an escaped/symlinked path, a stale total, an attempt to mutate B2-019's pre-existing ledger, and a B2-020 bridge/session allocation before B2-019's final review has completed.

## Answer-check integrity (non-vacuous checks)

The books teach; they do not police whether the person running a notebook is honest, and no
solution requires a sandbox to author or verify.
The one integrity property that IS the material's concern is that a solution's `### Answer
check` must have teeth — it must reject a plausible *honest* mistake rather than pass regardless
of what is written.

For the five concept-critical practices, a focused test (`tests/test_language_transformer_checks.py`)
confirms the untouched solution's Answer check PASSES and that a single named wrong-answer
variant FAILS it. The variant substitutes the body of one pinned, named function in a working
copy of the solution and re-executes; there are no markers, AST binding, isolation, or
process-group apparatus, and student statements carry no solution-marker contract.

| Practice | Pinned function | Wrong-answer variant the check must reject |
|---|---|---|
| p07 | `update_embedding_table` | returns the table unchanged (no gradient step) |
| p18 | `shift_targets` | returns unshifted targets (`(tokens[:-1], tokens[:-1])`) |
| p11 | `apply_mlm_mask` | leaves the true token visible (no masking) |
| p21 | `configure_frozen_stage_optimizer` | optimizes encoder + classifier during the frozen stage |
| p24 | `evaluation_indices` | includes a training row in the evaluation split (leakage) |

## Implementation tasks

### Task 1 — Make the Book 2 schedule multi-unit before adding content

**Files:**

- Modify: `tools/checks/schedule.py`
- Modify: `tools/render_course_structure.py`
- Modify: `tests/test_book2_schedule.py`

- [ ] Write focused failing tests for the two-live-manifest ledger and all named negative mutations above, including a regular B2 unit directory without `manifest.yaml`, extra/nonregular manifests, and early B2-020 practice/review allocations as well as early bridge/lesson allocations.
- [ ] Replace only the B2-019 singleton assumptions with the generic per-manifest ledger contract; do not change Book 1 scheduling semantics or allow unregistered units.
- [ ] Replace the Book 2 renderer's hard-coded local/display week range, six-number cadence prose, and Week-6 final-assessment marker with values derived from the validated ledger: first/last local and global weeks, rendered weekly totals, and the final ledger week.
  Add a copied two-manifest regression test proving the generated Book 2 schedule describes weeks 1–12 / 41–52, both six-week cadence sequences, and the final assessment after Week 12 while preserving the one-unit B2-019 output semantics.
- [ ] Test that a unit-directory symlink and a manifest symlink are each hard failures, rather than silently disappearing from the live ledger, and that traversal is rejected through `resolve_contained_path()` realpath resolution.
- [ ] Preserve the live B2-019 schedule byte-level allocation semantics and the live six-week/1,660-minute ledger.
  Do not append B2-020 to the live schedule until Task 3 creates its manifest and every declared statement-side path.
  Use copied two-manifest fixtures to prove the generic validator before any second live manifest exists.
- [ ] Run `PATH=/home/chris/.local/bin:$PATH uv run pytest -q tests/test_book2_schedule.py`.
- [ ] Commit: `test: generalize Book 2 schedule ledger`.

### Task 2 — Add B2-020 ownership, closure, and generated evidence contracts

**Files:**

- Modify: `book2/syllabus.md`
- Modify: `docs/unit-standards.md`
- Modify: `tools/model.py`
- Modify: `tools/audit_curriculum.py`
- Modify: `scripts/ci-local.sh`
- Create: `scripts/verify-historical-deferred-policy.sh`
- Modify: `tools/checks/scope.py`
- Modify: `book2/curriculum/coverage-map.yaml` (Task-2 erratum: checkbox 4's partial `nlp-word-embeddings` destination/disposition transfer lives here — PARTIAL only, `coverage` stays `partial`; the `covered` promotion is Task 3)
- Modify: `tests/test_model.py` (Task-2 erratum: checkbox 6's B2-020-only deferred-policy parser change supersedes this file's generic-deferred-policy assertions)
- Modify (Task-2 erratum): `tests/test_attention_mutations.py`, `tests/test_audit_curriculum.py`, `tests/test_book2_schedule.py` — registering B2-020's 8 owned concepts mechanically invalidates a Book-2 concept count (11→19), a curriculum digest changed by the partial coverage transfer, and a copied schedule fixture that must satisfy the new shared-parser teaching-order contract. Assertions updated to the new correct values only; no test intent weakened.
- Modify: `tests/test_b2_019_statements.py`
- Modify: `tests/test_integration.py`
- Modify: `tests/test_scope.py`
- Create: `tests/test_b2_020_statements.py`

>  **DESIGN DIRECTIVE (user decision 2026-08-29) — register B2-020 via `planned_units`, not `units:`.**
>  A first Task-2 attempt registered B2-020 as a shipped `units:` entry; that fought the repo's
>  purpose-built `planned_units` / `provisional_concepts` machinery (see `tools/model.py:PlannedUnit`
>  and the extensive `planned_units` handling in `tools/render_curriculum_roadmap.py`) and cascaded
>  stale generated evidence (inventory, roadmap, coverage-audit), each needing a projection
>  workaround. B2-020 is a registered-but-not-yet-shipped unit — exactly what `planned_units` is
>  for. Register it as a `planned_units` entry with its eight concepts as `provisional_concepts`,
>  so the existing machinery keeps the inventory/roadmap/coverage renderers current by design with
>  NO per-renderer projection code. The attempt was reverted to `394addc`; that first attempt's
>  blast radius (the `tests/test_audit_curriculum.py` count 11→19, the `tests/test_attention_mutations.py`
>  digest, and the `tests/test_book2_schedule.py` fixture edits recorded in the Files-list erratum
>  above) was units-approach-specific and does NOT apply to the planned-units design; the real
>  Files list will be whatever the planned-units registration actually touches. The
>  deferred-solution-policy parser, the `scope-check` transfer, and `verify-historical-deferred-policy.sh`
>  remain required either way.

- [ ] Add the `language-transformers` cluster, the eight owned concepts, and B2-020's exact unit/prerequisite/concept-prerequisite contract to Book 2's canonical syllabus.
- [ ] Pin the five direct qualified Book 1 prerequisite units listed above and add a focused prereq-check fixture proving each of the ten declared Book 1 concepts is admitted only through those explicit units.
- [ ] Make B2-020 double-length in both syllabus and manifest contract and extend the standards roster to the exact text `F5, F6, C7, C11, C12, B2-019, and B2-020`, without altering the recorded C7 non-conformance history.
  Update the three existing pinned roster assertions in `tests/test_b2_019_statements.py` and `tests/test_integration.py` rather than leaving them to fail, and add a regression assertion that both B2 unit IDs occur in the roster.
- [ ] Confirm `mc-normal-form` remains the existing standards-defined MC subtype; no new checker type is introduced.
- [ ] Register the ownership and prerequisite contract only; leave each B2-020 coverage row missing/partial until Task 3 has created the referenced statement paths and manifest.
  In that partial registration, transfer `nlp-word-embeddings` from `destination: book1:C8-embeddings` / `disposition: extend-existing-unit` to `destination: B2-020-language-transformers` / `disposition: new-unit`, retain only its declared Book 1 inputs as qualified prerequisites, and reserve the already-declared B2-owned `learned-token-embedding` concept for its future evidence claim.
- [ ] Replace the legacy `scope-check` special case for `nlp-word-embeddings` in `tools/checks/scope.py` with its B2-020 ownership contract: destination `B2-020-language-transformers`, disposition `new-unit`, and coverage limited to the lifecycle states `partial` (Task 2) or `covered` (Task 3).
  Add `tests/test_scope.py` fixtures that accept each named lifecycle state and reject the former Book 1 C8 destination/`extend-existing-unit` state after this plan.
- [ ] Extend the shared manifest parser in `tools/model.py` with the narrow lifecycle policy: a deferred solution policy is valid only for `B2-020-language-transformers` with `plan: plan-020`, `expires: 2026-09-30`, and **no** declared solution file present; all other deferred manifests, an altered plan/expiry, or even one present B2-020 solution under a deferred policy are hard parse errors.
  The historical-policy machinery lands in this task alongside that parser change, not later: the typed `load_unit_manifests(root, *, as_of_date: date | None = None)` parameter, the `scripts/ci-local.sh` rejection of `USAAIO_HISTORICAL_VERIFY`/`USAAIO_AS_OF_DATE`, and `scripts/verify-historical-deferred-policy.sh` are all Task 2 deliverables, and the contract governing their semantics is stated under Task 3 for readability only.
  Update `tools/audit_curriculum.py` to invoke `load_unit_manifests()` before its raw-YAML notebook inventory so it cannot independently accept a deferred policy that the shared parser rejects.
  This common parser rule is then the enforcement used by inventory, coverage, and layer-boundary consumers; test each consumer observes the same rejection through a copied registered Book 2 fixture.
  Modify `scripts/ci-local.sh` and create `scripts/verify-historical-deferred-policy.sh` in this task under the explicit historical-policy contract below, with tests in this task; do not defer their behavior to Task 3.
- [ ] Add a focused fixture demonstrating only the named planned `B2-020-language-transformers` syllabus unit (not arbitrary manifest-less units) is checker-valid until Task 3 atomically publishes its manifest and coverage evidence.
- [ ] Do not render inventory, Book 2 course structure, or aggregate evidence in this task; Task 3 owns their first valid regeneration.
>  **TASK 2 AS IMPLEMENTED (planned-units, 2026-08-29).** Per the design directive above, B2-020
>  was registered through the existing `planned_units` machinery in
>  `book2/curriculum/coverage-map.yaml` (it already had a planned-unit row): its eight owned
>  concepts became that row's `provisional_concepts`, and the `nlp-word-embeddings` knowledge
>  point was transferred to `destination: B2-020-language-transformers` / `disposition: new-unit`
>  (coverage stays `partial`). The legacy `nlp-word-embeddings` scope special case in
>  `tools/checks/scope.py` was inverted to that contract, `docs/curriculum-roadmap.md` and
>  `docs/audits/015-coverage-audit.md` were regenerated (the roadmap is where planned ownership is
>  recorded — 3 lines), and four downstream tests were updated (fixture destination, one
>  assertion, one inverted mutation, one re-baselined guard digest). NO syllabus change, NO parser
>  change, NO projection code, NO staleness — the existing machinery keeps every renderer current
>  by construction. Full suite 1117 passed; B2-019 byte-unchanged; no B2-020 content created.
>  **Deferred to Task 3 (when B2-020 ships its manifest):** adding B2-020's unit/concepts to the
>  canonical `syllabus.md`, the double-length standards roster entry, the deferred-solution-policy
>  parser + historical machinery, and the live schedule-ledger entry — all of which are
>  shipped-unit concerns, not planned-registration concerns.

- [ ] Commit: `docs: register language Transformer coverage`.

### Task 3 — Author the statement-side teaching corpus

**Files:**

- Create: `book2/units/B2-020-language-transformers/manifest.yaml`
- Create: `book2/units/B2-020-language-transformers/lesson.ipynb`
- Create: `book2/units/B2-020-language-transformers/review.ipynb`
- Create: `book2/units/B2-020-language-transformers/lessons/00-book1-bridge.ipynb` through `lessons/05-language-task-design-and-audit.ipynb`
- Create: `book2/units/B2-020-language-transformers/practice/p01.ipynb` through `p24.ipynb`
- Create: `book2/units/B2-020-language-transformers/scripts/generate_language_data.py`
- Create: `book2/units/B2-020-language-transformers/data/tiny_encoder_checkpoint.py` (generated, tracked source)
- Create: `book2/units/B2-020-language-transformers/data/language_fixture.py` (literal student-facing synthetic data)
- Create: `book2/units/B2-020-language-transformers/data/tiny_encoder_state.py` (student-facing trained state only)
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
  Because this is statement-only publication, set the B2-020 manifest's policy exactly to `{status: deferred, plan: plan-020, expires: 2026-09-30}`; the shared parser must compare that date to the current UTC date and hard-fail only when `as_of_date > expires` (the expiry date itself remains valid), so this intentionally temporary intermediate commit is not green after the deadline.
  Its focused tests must freeze the clock on each side of the expiry and prove inventory/coverage/layer-boundary accept only the unexpired named temporary debt and surface its expiry rather than treating absent solutions as valid generally.
  Extend `load_unit_manifests(root, *, as_of_date: date | None = None)` with a typed, non-environment date parameter; omitted by every normal consumer, it uses current UTC, while `scripts/ci-local.sh` must reject `USAAIO_HISTORICAL_VERIFY` and `USAAIO_AS_OF_DATE` if present before any check runs.
  The only historical path is the new explicit `scripts/verify-historical-deferred-policy.sh <archived-commit> <ISO-date>` command, which extracts that commit to a temporary archive and calls a dedicated Python entry point that passes the validated ISO date through this `as_of_date` parameter.
  The parser never reads expiry dates from environment variables.
  Test archived verification succeeds only with its explicit parameter; direct parser/check invocations cannot override expiry through environment variables; and normal CI fails before any check when either variable is set.
  If work has not reached the required-policy transition by that date, a separately reviewed follow-up plan must explicitly amend the expiry before any continuation; it is never silently extended.
- [ ] Have `scripts/generate_language_data.py` run the Session-3 seeded causal/MLM pretraining contract from fixed seed `20260812`, certify literal initial and final losses, and render the trained state into tracked, human-readable `data/tiny_encoder_checkpoint.py` with vocabulary, split IDs, trained encoder weights, objective/loss trace, and semantic hash.
  The single trained state uses this exact protocol: initialize a one-block, pre-norm causal/MLM Transformer encoder (vocabulary 12, sequence length 8, width 8, two attention heads, feed-forward width 16) plus one vocab-logit head shared across both pretraining phases (not weight-tied to the embedding table) from seed `20260812`; train first on the literal causal batches for 40 full-batch AdamW updates (`lr=0.03`, `weight_decay=0`), then on the literal MLM batches for 40 full-batch AdamW updates with the same optimizer state continued across the phase boundary.
  Architecture semantics are learned positional embeddings for positions 0–7, scaled dot-product attention with causal lower-triangular mask during the causal phase and bidirectional attention with only padding masked during MLM, LayerNorm `eps=1e-5`, GELU feed-forward activation, and dropout `0.0` everywhere.
  AdamW is exactly `betas=(0.9, 0.999)`, `eps=1e-8`, `amsgrad=False`, `foreach=False`, `fused=False`, and one instance created before causal update 1 whose state object/step counters continue through MLM update 40.
  Within each update, consume the fixture rows in their stored ascending order, compute mean token cross-entropy over the explicitly non-padding/non-ignored positions, call `zero_grad(set_to_none=True)`, `backward()`, then `step()`; no shuffle, dropout, gradient clipping, scheduler, accumulation, or implicit batch order is permitted.
  A focused generator protocol test uses instrumented model/mask and optimizer wrappers to prove the causal mask for exactly 40 ordered updates, then bidirectional MLM mask for exactly 40, one optimizer instance with phase-boundary state continuity, and a complete 80-entry phase-tagged loss trace emitted from those exact updates.
  The generated checkpoint's causal and MLM trace/loss/probe entries are evaluated from this one final sequential state against the exact fixture held-out IDs.
  Pin the authoring envelope to the lockfile-resolved CPU torch build, deterministic algorithms, single intra/inter-op thread, and every Python/NumPy/Torch seed; do not assert a Linux-only `+cpu` local-version tag.
  Define the versioned semantic hash as SHA-256 over canonical JSON containing vocabulary/splits/architecture/objective plus every committed trained parameter rounded to six decimal places in sorted name/index order; it intentionally excludes raw float bytes.
  Standard CI verifies the committed checkpoint's self-consistent canonical JSON/hash and trained functional contract (both losses improve and fixed held-out probes beat the literal initial-state baseline by named margins), but does **not** regenerate-and-hash-compare 80-epoch weights across CPU architectures.
  The author/CI-only `tiny_encoder_checkpoint.py` must export schema version `1`, `TOKEN_TO_ID`, `TRAIN_SPLIT_IDS`, exact `CAUSAL_HELDOUT_IDS` and `MLM_HELDOUT_IDS`, `INITIAL_LOSSES`, `FINAL_LOSSES`, `PROBE_EXPECTED_TOP1_IDS`, and the measured `MIN_ABSOLUTE_LOSS_IMPROVEMENTS`.
  After the first deterministic Task-3 generator run, record those literal measured loss/probe values and margins with at least 2× observed numerical headroom, then freeze them in the tracked module and its test; no guessed pre-authoring threshold is accepted.
  Its test reconstructs the literal initialized width-8 architecture from seed `20260812`, validates every checkpoint parameter name/shape/dtype (`float32`) against that architecture, recomputes losses within the frozen tolerances, requires each final loss to beat the corresponding initial loss by its frozen minimum absolute improvement, and requires each named probe's top-1 ID to match the pinned expected ID.
  Both modules export the same `ENCODER_STATE_HASH`: SHA-256 of canonical JSON `{schema_version: 1, architecture: <ordered architecture fields>, tensors: [[name, shape, dtype, six-decimal flattened values], ...]}` for the encoder projection only, ordered lexically by tensor name.
  The generated student-facing `tiny_encoder_state.py` contains only architecture/state tensors and `ENCODER_STATE_HASH`—never losses, probes, targets, or training trace—and is the sole state source p20/p21 may load.
  CI verifies that this state module's architecture/tensor names, shapes, dtypes, canonical tensor JSON, and `ENCODER_STATE_HASH` are exactly the encoder projection of `tiny_encoder_checkpoint.py`'s verified trained checkpoint; a random self-hashed state or any tensor mismatch is rejected.
  These fixed data IDs, measured margins, API fields, and canonical JSON schema/version are mandatory, so a self-hashed random or arbitrary parameter set cannot pass merely by changing its own metadata.
  A separate explicit local `--refresh-checkpoint` generator command is the record-once maintenance path; it reports canonical deltas and requires an intentional committed source update when a supported toolchain changes.
  `data/language_fixture.py` contains only the fixed literal vocabulary, token-ID sequences, masks, splits, and labels needed by students, never author training code, answers, loss targets, or generated weights.
  The generator alone creates `tiny_encoder_checkpoint.py` and `tiny_encoder_state.py`.
  The p19 student statement teaches and pins the full pretraining protocol as learner-visible content: the 40-update causal phase, then the 40-update MLM phase, the architecture, masks, AdamW config, and update order.
  p19 exposes `run_pretraining_protocol(fixture) -> (encoder, head, phase_trace)` and independently runs that protocol from the literal fixture; `phase_trace` has 80 ordered records with `phase`, `update_index`, `mask_mode`, `optimizer_step` (read from the single optimizer's own state), and `loss`.
  Its `### Answer check` is FUNCTIONAL: each phase's loss improves from that phase's initial loss, the final held-out objective losses and probes beat the seeded-initial baseline by the frozen margins, and the trace has the correct phase structure, update counts, and a single optimizer whose `optimizer_step` runs continuously 1..80 across the phase boundary (so a phase-2 optimizer reset is caught).
  A light answer-check-integrity test (implemented in Task 5 alongside the five function-substitution tests; stated here as contract-for-readability) confirms the honest solution's Answer check passes and that named conceptual mistakes fail it — skip-MLM, reset-optimizer between phases (caught by the `optimizer_step` continuity assertion), and causal-mask-during-MLM. p19 trains from the fixture and does not load the generated checkpoint or state artifact.
  There is no sandbox, no per-step optimizer-transition instrumentation, and no injection-mutant contract: the check verifies that the training worked, not that the runtime was un-tampered.
  p20/p21 load `tiny_encoder_state.py` as their sole pre-fine-tuning encoder state and confirm `ENCODER_STATE_HASH` matches; a no-load/random-encoder variant fails the Answer check.
- [ ] Exercise all eight owned concepts with at least three direct practices and ensure no problem tags a concept outside the unit/prerequisite closure.
- [ ] Pin the function names for the five concept-critical practices (see `## Answer-check integrity`) so the integrity test can substitute a wrong-answer variant; student statements carry no solution-marker apparatus.
- [ ] In the same commit that creates the manifest, append the exact B2-020 weeks 7–12/global weeks 47–52 ledger above and its post-week-12 final-assessment marker.
  Then promote exactly the five named coverage rows with literal lesson anchors and evidence IDs, and regenerate/check the inventory, Book 2 course structure, roadmap, and audit from the now-valid paths.
  For `nlp-word-embeddings`, replace the inherited C8 anchors, Book 1 practice/assessment evidence, and Book 1 `shipped_concepts` with B2-020 Session 1–3 anchors, the named B2 practices in the ledger, and `shipped_concepts: [learned-token-embedding]`; set `coverage: covered`, `deficits.modalities_missing: []`, and retain `destination: B2-020-language-transformers`.
  The statement test must assert this exact destination/disposition/covered-state transformation and reject any remaining `book1:C8-embeddings` evidence in the B2-020 claim, so the layer-boundary claim cannot be satisfied by Book 1 evidence.
- [ ] Test hygiene, lesson order, manifest paths, source isolation, CPU label, imported-concept boundary, time arithmetic, and coverage tags without executing student notebooks.
- [ ] Commit: `feat: teach language Transformer statements`.

### Task 4 — Blind-author and execute solutions

**Files:**

- Create: `book2/units/B2-020-language-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`
- Modify: `book2/units/B2-020-language-transformers/manifest.yaml`
- Modify: `scripts/ci-local.sh`
- Test: `tests/test_b2_020_statements.py`

- [ ] Author the 24 solutions in a fresh GPT-5.6-sol session that works from the published Task-3 statements and was NOT given the statement-authoring session's outlines. This is blind-solve as a plain workflow step — a separate session for independence — with no sandbox, filesystem isolation, read-access audit, input/output digest, or handoff-script apparatus.
- [ ] Each solution preserves the learner-visible header, uses the seeded literal data, states every answer, and ends with a non-vacuous `### Answer check` — exact numeric/shape/training assertions that reject a plausible wrong answer (see `## Answer-check integrity`).
- [ ] After all 24 solutions exist, atomically flip the manifest `solution_policy` from `deferred` to `required`; test that every declared solution path exists and that a retained deferred policy or a missing solution fails inventory, coverage, and layer-boundary checks.
- [ ] Execute p01–p24 in numeric order on fresh kernels through the Book 2 notebook-execution step of `scripts/ci-local.sh`, each under a per-notebook 20-second wall-clock timeout. Record the measured timings in the post-execution report.
- [ ] Prove the answer register, student hygiene, required-solution policy, and execution all pass.
- [ ] Commit: `feat: add independently solved language practices`.

### Task 5 — Lock the answer-check integrity tests

**Files:**

- Create: `tests/test_language_transformer_checks.py`
- Modify: `scripts/ci-local.sh`

- [ ] Implement the five answer-check-integrity tests from `## Answer-check integrity`: for each concept-critical practice, confirm the untouched solution's `### Answer check` passes, and that substituting the named function's wrong-answer variant in a working copy of the solution makes the Answer check fail.
- [ ] Add, in the same file, the p19 protocol-variant integrity tests (skip-MLM, reset-optimizer, causal-mask-during-MLM) and the p20/p21 no-load/random-encoder variant test; these are protocol/loader variants rather than single-function substitutions.
- [ ] Wire `tests/test_language_transformer_checks.py` into the Book 2 portion of local CI.
- [ ] Prove every wrong-answer variant is rejected, the untouched corpus passes, and the tests need no sandbox or external isolation.
- [ ] Commit: `test: lock language Transformer answer-check integrity`.

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
- [ ] Note in the post-execution report that the 24 solutions were authored in a separate blind session (independence as a plain workflow step); no byte-hash provenance apparatus is required.
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

### Review 2 — sol (2026-08-12)

- **Verdict**: REJECT.
- `[sol][FIXED]` the checker does not propagate Book 1 qualified imports through unqualified B2-019.
  B2-020 now directly names `book1:F1-scientific-python`, `book1:F3-matrices`, `book1:C6-pytorch`, and `book1:C11-neural-training`, with a focused closure fixture required before content ships.
- `[sol][FIXED]` p24 targeted its oracle rather than a solution behavior.
  It now mutates the evaluation-index construction and requires a distinct end-of-notebook split-disjointness oracle.

### Review 2 — fable (2026-08-12)

- **Verdict**: REJECT.
- `[fable][FIXED]` p20/p21 now use a named, tracked, human-readable tiny encoder checkpoint rendered from a fixed seed and semantic-hash checked; no opaque weight file is allowed.
- `[fable][FIXED]` Book 2 unit and manifest symlinks are explicit hard failures, not silently omitted discovery entries.
- `[fable][FIXED]` p12 now follows Session 4 in week 10, while p11 moves to week 11 without changing any minute total.
- `[fable][FIXED]` Task 4 requires a fresh kernel per solution notebook.

### Review 2 — glm (2026-08-12)

- **Verdict**: REJECT.
- `[glm][FIXED]` p10 was orphaned from both the owned-concept and knowledge-point evidence maps.
  It is now direct causal-language-modeling and NLP-Transformer implementation evidence.
- `[glm][FIXED]` the mutation contract now binds a unique declared source marker and a distinct named AST-wrapped oracle, and accepts only the matching first failure.
- `[glm][FIXED]` B2-019 sinusoidal position reuse, direct Book 1 closure, bridge-policy authority, realpath containment, existing `mc-normal-form` status, training budgets, and the two located worked examples are explicit.

The next review round evaluates this consolidated amendment and is the first round eligible for four-way consensus.

### Review 3 — sol (2026-08-12)

- **Verdict**: REJECT.
- `[sol][FIXED]` `book1:tensor-shape-tracing` is owned by C7 rather than the four initially listed direct imports.
  The exact prerequisite list now includes `book1:C7-cnn-transfer`; an executable closure fixture covers all ten Book 1 concepts.
- `[sol][FIXED]` the former checkpoint contract could serialize initial random weights and still call downstream work fine-tuning.
  Review 3 required Session 3/p19 to execute and certify pretraining rather than replay a checkpoint; the final Task-3 contract keeps that independent p19 trace while the generator, not p19, emits the separate trained-state artifact consumed by p20/p21.
- `[sol][FIXED]` CPU runtime limits and B2-019 completion-before-B2-020 start now have named timeout/completion tests.

### Review 3 — fable (2026-08-12)

- **Verdict**: REJECT.
- `[fable][FIXED]` mutation hooks are now student-facing semantic interface spans, not literal solution source lines, preserving blind solution independence while keeping fail-closed target identity.
- `[fable][FIXED]` a mutation is accepted when its distinct named oracle fails; earlier unrelated failures are recorded but never substituted for that oracle.
- `[fable][FIXED]` the intermediate syllabus-only B2-020 state, final-assessment position, theory-bearing p19 pretraining execution, and fresh-review state are now explicit.

### Review 3 — glm (2026-08-12)

- **Verdict**: REJECT.
- `[glm][FIXED]` verified the prior p10-orphan and oracle-binding findings; the final amendment retains their direct evidence and AST-bound named-oracle contracts.

### Review 4 — self (2026-08-12)

- **Verdict**: APPROVE.
- Recomputed all practice type/difficulty/minute ledgers and every session-order dependency.
  The explicit five-unit Book 1 closure now contains all ten qualified concepts, p19 is an executable model-training surface, B2-020 cannot schedule before B2-019 completion, and all five mutations bind behavior through student-facing semantic hooks to a separate named oracle.
- This supersedes Review 1 self-review; no self-review `[OPEN]` item remains.

### Review 4 — glm (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- `[glm][FIXED]` verified both prior findings genuinely closed: p10 is present in the owned-concept map, coverage map, and week-9 schedule; each of the five mutations binds a unique marker hook to a distinct named oracle with no ambiguous bindings.
- Recomputed every ledger independently: practice minutes 100 + 530 + 490 = 1,120; weekly 255/275/420/270/380/60 = 1,660; bridge 30 + 5x90 + 1,120 + 60 = 1,660 = 27.67 h inside the 26-32 h band; type and difficulty mixes match; all 24 practices scheduled exactly once and at or after their teaching session; all ten Book 1 concepts map to the five pinned units.
- `[glm][FIXED]` NIT the width cap could be read to include the feed-forward inner width; now stated as embedding/attention width with the feed-forward width called out separately.
- `[glm][FIXED]` NIT the `2026-08-31` deferred-policy expiry left three days of runway with implementation unstarted; amended below.

### Review 4 — fable (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- `[fable][FIXED]` verified all three prior findings closed by construction, including testing span ambiguity (two implementers converge because every mutant body is a `return`), hook-bypass drift (fail-closed), and the wrong-exception path through the named oracle (fails closed).
- Independently reconfirmed the arithmetic, the registry facts against every `book1/units/*/manifest.yaml`, and the four checker claims the plan relies on; found no unsatisfiable requirement pair across five constructed conflict candidates.
- `[fable][FIXED]` **MAJOR** the `2026-08-31` expiry literal is double-pinned and stale; the fail-closed mechanism is right and only the constant is wrong. Amended to `2026-09-30` at both pinned sites.
- `[fable][FIXED]` **MINOR** Session 3's required teaching surface omitted the pretraining stack's two architecture deltas — learned positional embeddings (against Session 2's sinusoidal reuse) and GELU — neither of which appears anywhere in either book, so p19 would have pinned untaught content. Both are now required teaching surface.
- `[fable][FIXED]` **MINOR** the historical-policy contract was mandated in Task 2 but written under Task 3; Task 2 now names the deliverables explicitly.
- `[fable][FIXED]` NITs: vestigial "source-match" phrasing reworded to the governing marker/AST contract; C8's deliberate absence from the prerequisite-unit list now recorded with its reason.
- `[fable][WONTFIX]` NIT relocating the `encoder.zero_grad(set_to_none=True)` requirement out of the `frozen-stage` hook row: it is p21 statement-protocol text, harmless to mutation semantics, and moving it risks detaching it from the protocol it constrains.

### Review 4 — sol (2026-08-28)

- **Verdict**: REJECT.
- `[sol][FIXED]` **BLOCKER** p19's training was never bound to the state it returns. Instrumenting the trace proves updates occurred, not that they occurred to the returned objects, so a `train-A-return-fresh-B` notebook could train one model for all 80 valid updates, return a fresh model, recompute its held-out values, and pass. The contract now requires optimizer-parameter identity with the returned `encoder`/`head`, before/after snapshots of those same objects, and held-out losses beating an independently reconstructed seeded-initial baseline by frozen margins, with the near-miss pinned as a required failing mutant.
- `[sol][FIXED]` **BLOCKER** p19's isolation was porous: a literal-name scan plus temporary-copy execution does not stop a synthesized absolute path, glob, or `importlib` load from the still-readable original repository. Execution now runs under an enforced read allowlist or a validated read-access log, with all three bypass mutants required to fail.
- `[sol][FIXED]` **MAJOR** the blind-solve digests proved what was copied and returned, never what the session read. The solve now runs with the handoff directory as its enforced readable root or emits a validated read-access log, the statement-side scan symmetrically rejects solution paths and author-only artifacts, and a semantic statement change after the Task-3 cut invalidates the affected blind output outright rather than being reported as a `post-blind amendment`.
- `[sol]` confirmed as already closed: the C7 prerequisite fix, the p20/p21 checkpoint contract's rejection of an initial random state, the five mutation oracles, the fail-closed schedule and policy transition, and Task 6 as a real named verification phase. It also judged the scope coherent as one vertical unit plus enabling infrastructure rather than three plans.

### Round 4 outcome and amendment

Round 4 is `[self]` APPROVE, `[glm]` APPROVE WITH NITS, `[fable]` APPROVE WITH NITS, `[sol]` REJECT — no consensus.
Every finding above is amended in this revision, including the two `[sol]` blockers, which are the substantive ones: both were cases of a contract that looked rigorous while remaining circumventable, the failure class this project's gates have caught repeatedly.
The deferred-policy expiry moves from `2026-08-31` to `2026-09-30`. Two independent reviewers raised it, `[fable]` at MAJOR with the fix prescribed as design-neutral and required before implementation. It is amended here rather than through a separate follow-up plan because no deferred policy is live yet: the plan has not begun implementation, so this is plan-gate iteration, not the silent extension of a running policy that the plan itself forbids.

### Review 5 — glm (2026-08-28)

- **Verdict**: APPROVE.
- Re-derived every ledger independently again (1,120 practice minutes; weekly 255/275/420/270/380/60 = 1,660; 27.67 h in band; all 24 practices scheduled exactly once at or after their teaching session; type/difficulty mixes unchanged).
- Confirmed both prior NITs closed (embedding/attention width wording; `2026-09-30` at both pinned sites), the Session-3 addition within budget and non-duplicative, and no new internal contradiction from the round-5 amendment. Residual NITs are review-history `2026-08-31` mentions (correct immutable text) and one wording preference — no blockers.

### Review 5 — fable (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- Verified all four Round-4 `[fable]` findings closed against the repo, not the plan's assertions.
- Independently judged the `[sol]` returned-state-identity and read-isolation contracts **implementable and not over-constrained**: an honest in-place-training notebook passes every layer while each named mutant fails a distinct layer, and the read-isolation mechanisms reduce all three bypass mutants to observable open/import events.
- `[fable][FIXED]` **MINOR** swept the full pinned protocol constant-by-constant and found one more pinned-but-untaught item of the same class as the Round-4 GELU finding: `AdamW` appears nowhere in either book (Book 1 teaches `Adam`/`SGD`). Mitigated because at the pinned `weight_decay=0` AdamW is numerically Adam, but recorded by fable's own standard. Session 3's teaching surface now introduces AdamW as Adam with decoupled weight decay (zeroed here) before p19 pins it.

### Review 5 — sol (2026-08-28)

- **Verdict**: REJECT.
- `[sol][FIXED]` **BLOCKER** the Review-4 returned-state fix was still evadable by `train-A-copy-into-B`: build the optimizer over the returned model B's exact parameters, then copy a hidden model A's trained tensors into B before a final no-gradient step — B changes, beats the baseline, passes every probe, though every forward and gradient came from A. The contract now requires an exact parameter-object multiset match and instruments every one of the 80 updates to bind its loss to a forward of the returned model, its gradients to those parameters, and its step to that gradient; any returned-parameter change outside an instrumented cycle is a hard failure. `train-A-return-fresh-B`, `train-A-copy-into-B`, and `loss-on-A/optimizer-on-B` are all required failing mutants.
- `[sol][FIXED]` **BLOCKER** the read-isolation fallback (a self-reported access log) was not trusted evidence — notebook code can read via `os.open`/`pathlib`/`ctypes`/`mmap`/a child process and emit a clean log. Both p19 execution and the blind solve now require a mechanism EXTERNAL to the process (filesystem sandbox / mount namespace with the original repo absent, or an out-of-process access audit over all descendants), with an explicit judgment-fork stop if that facility is unavailable rather than a fallback to a self-reported log. Bypass mutants now include `os.open`/`pathlib` and a child process.
- `[sol][FIXED]` **BLOCKER** the Review-4 blind-read wording said a session reading "either checkpoint" must be rejected, which literally rejected `tiny_encoder_state.py` — a REQUIRED allowed read for p20/p21. Forbidden reads are now enumerated by exact path (generator, `tiny_encoder_checkpoint.py`, plan file, every non-allowlisted file), with `tiny_encoder_state.py` explicitly permitted.
- `[sol][FIXED]` **MAJOR** the semantic-vs-non-semantic statement-change distinction was human-classified. It is now mechanical: every markdown/code cell source is semantic by default, the check canonicalizes each statement notebook to its ordered cell sources and requires a byte-identical digest to the Task-3 input, and a `post-blind amendment` is admissible only for changes confined to an enumerated set of notebook-JSON metadata paths that leave every cell-source digest unchanged.

### Review 5 — self (2026-08-28)

- **Verdict**: APPROVE.
- Applied the round-5 amendments and re-read every amended sentence; the four `[sol]` fixes and the `[fable]` AdamW fix are recorded in the contract text, and the ledgers are unchanged.

### Round 5 outcome and amendment

Round 5 is `[self]` APPROVE, `[glm]` APPROVE, `[fable]` APPROVE WITH NITS, `[sol]` REJECT — no consensus.
All four `[sol]` findings were defects in the Review-4 amendment itself — three anti-cheat contracts that read as rigorous while remaining circumventable, plus one self-contradiction ("either checkpoint" rejecting a required read). This round adopts `[sol]`'s own prescribed fixes verbatim rather than a weaker paraphrase, which is what let the Review-4 versions be punctured: the read-isolation escape hatch is removed outright and its unavailability made an explicit stop, and the semantic-change test is made mechanical rather than reported. Fable's `AdamW` finding is fixed in the same pass.

### Review 6 — glm (2026-08-28)

- **Verdict**: APPROVE.
- Re-derived every ledger independently and confirmed via `git diff bf8cd22` that the round-6 amendment changed no ledger row; the two isolation contexts (p19 loads neither artifact; the blind solve permits `tiny_encoder_state.py`) are correctly separate; no earlier round's recorded verdict was altered.
- NITs: the Session-3 row's "two deltas" phrase listing three items, and a Review-5 self-verdict recorded only in the outcome paragraph. Both fixed below.

### Review 6 — fable (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- Confirmed the AdamW MINOR closed and did an EXHAUSTIVE constant-by-constant sweep of the entire Task-3 protocol against the shipped corpus, declaring the pinned-but-untaught thread definitively closed — no third item. Verified `bwrap`/`unshare` are installed on this host, so the read-isolation external-mechanism requirement is realistic rather than a guaranteed block.
- Independently judged the `[sol]` returned-state contract satisfiable by an honest in-place-training notebook (init precedes the pre-first-update snapshot; `zero_grad(set_to_none=True)` touches `.grad` not `.data`; all `.data` mutation is inside `step()`).
- `[fable][FIXED]` NIT the "two deltas" wording (same as glm); NIT the shared vocab-logit head could be misread as weight-tied to the embedding table, colliding with the exact-parameter-multiset assertion — now stated "not weight-tied to the embedding table" as a distinct parameter; NIT smoke-test the isolation facility at the START of the blind-solve task — added.

### Review 6 — sol (2026-08-28)

- **Verdict**: REJECT.
- `[sol][FIXED]` **BLOCKER** the round-5 returned-state fix still permitted an IN-cycle injection: copy model A's trained tensors into the returned model B during B's `forward`, so loss/gradients/step are all genuinely on B yet the values are A's, injected inside a cycle the round-5 rule only guarded from the outside. Because a correct final value is indistinguishable from a trained one, no result-level check can separate them; the fix pins the PROCESS instead — parameters held tensor-identical through forward/backward, and each of the 80 post-step optimizer states (parameters AND the AdamW moment buffers) required to equal an independently recomputed AdamW transition of the captured pre-step state under the observed gradient. `copy-into-B-during-forward` joins the required failing mutants. The moment-buffer inclusion pre-empts the obvious pivot of injecting into `exp_avg` rather than the parameters.
- `[sol]` confirmed the other three Review-5 fixes fully closed: read isolation (no residual self-log fallback; judgment-fork stop stated for both p19 and the blind solve), the enumerated forbidden-path fix (no remaining clause forbids `tiny_encoder_state.py`), and the mechanical semantic-change digest (a changed cell source cannot be relabeled as metadata). No new contradiction with earlier-accepted contracts.

### Review 6 — self (2026-08-28)

- **Verdict**: APPROVE.
- Applied the round-6 amendment (per-step transition fix + fable AdamW fix) and re-read every amended sentence; ledgers unchanged.

### Round 6 outcome and amendment

Round 6 is `[self]` APPROVE, `[glm]` APPROVE, `[fable]` APPROVE WITH NITS, `[sol]` REJECT — no consensus.
The single `[sol]` blocker is one more level of the returned-state injection: rounds 4-6 walked it from "prove B changed and is good" to "prove B changed by training" to "prove every step is the optimizer's exact function of the gradient." This round's fix pins the full per-step optimizer transition (parameters and moment buffers), which is the terminal form: because injecting a correct value is result-indistinguishable from training it, only verifying the closed-form process at every step separates the two, and a notebook that passes every step's recomputation has necessarily run the protocol. `[fable]` closed the pinned-constant thread exhaustively and both `[sol]` and `[fable]` judge the accumulated contract satisfiable by an honest notebook, so the remaining question for round 7 is solely whether this per-step transition check has any residual gap.

### Review 7 — glm (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- Confirmed both Review-6 NITs closed and re-derived every ledger; `git diff` showed the round-7 amendment changed no ledger row. NITs: an "above" that should read "below", and a missing `### Review 6 — self` subsection.

### Review 7 — fable (2026-08-28)

- **Verdict**: APPROVE.
- Empirically ran the honest per-step contract on the locked torch and confirmed bitwise-exact AdamW transitions at all 80 steps (satisfiable, not over-constrained), and found no residual gap in the then-current contract.

### Review 7 — sol (2026-08-28)

- **Verdict**: REJECT.
- **BLOCKER** gradient substitution: the per-step transition check trusted the *observed* gradient came from the pinned loss; a `.grad` hook forges it while parameters stay tensor-identical through forward/backward. Prescribed fix: independently recompute each step's gradient of the pinned loss and require equality.

### Review 7 — self (2026-08-28)

- **Verdict**: APPROVE.
- Applied the round-7 amendment (per-step transition covering the moment buffers; the three round-6 NITs) and verified the amended paragraphs read coherently.

### Scope change — user directive (2026-08-28): anti-cheat is out of scope

The user directed that anti-cheat is not the books' responsibility — "focus on the material
instead of the execution of teaching" — and that no solution may require a sandbox, keeping
blind-solve as a plain workflow step. This **supersedes the entire p19 anti-injection line**
(`[sol]` Reviews 4-7: returned-state identity, per-step optimizer transition, gradient
provenance) and the read-isolation / blind-solve sandboxing line, and moots the `[glm]`/`[fable]`
NITs attached to that removed machinery.

What was removed: the p19 returned-state identity contract and injection mutants; the p19 and
blind-solve external-isolation/sandbox/read-audit machinery; the marker/AST mutation-oracle
runner and its `MUTATION_TARGET`/`EXPECTED_CHECK` statement markers; the byte-hash
blind-provenance/semantic-digest apparatus; and the process-group timeout harness.
What was kept: all teaching content and ledgers unchanged; the self-containedness teaching
additions (GELU, AdamW, learned positional embeddings in Session 3); p19 as a functional
training surface (loss improves, correct shapes/probes); non-vacuous answer-checks recast as
five lightweight "answer-check integrity" tests that reject a named honest wrong answer keyed on
pinned function names; the generator's reproducible trained-state artifact under CI; and
blind-solve as a plain separate-session step. A plain 20-second per-notebook CI timeout replaces
the harness.

The rewrite touched no ledger row (verified). This is a materially simpler plan state and starts
a fresh review round.

### Review 8 — glm (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- Verified via `git diff` that the strip touched no ledger/schedule/concept row; the five pinned functions are consistent across Tasks 3/4/5; round history intact. NITs: the stale lines 34-35, and p19's light test wording. Both fixed below.

### Review 8 — fable (2026-08-28)

- **Verdict**: APPROVE WITH NITS.
- Confirmed self-containedness survived (GELU/AdamW/learned-positional still taught Session 3 before p19), the generator artifact chain is coherent without p19 self-certification, and Task 6 is a real verification phase; re-derived every ledger.
- `[fable][FIXED]` **MAJOR** the strip dropped `optimizer_step` from p19's `phase_trace`, which made the required-failing `reset-optimizer` honest mistake undetectable by the functional check (a fresh phase-2 Adam still improves loss within margin). Restored `optimizer_step` and the 1..80 cross-phase continuity assertion — teaching-adjacent, design-neutral. Plus the stale-lines and Task-5 assignment MINORs.

### Review 8 — sol (2026-08-28)

- **Verdict**: REJECT.
- Stated plainly that "the simplified content design is sound"; confirmed self-containedness, the five wrong-answer variants, the generator artifact chain, and Task 6. Raised no gameability finding (out of scope).
- `[sol][FIXED]` **MAJOR** the removed timeout/mutation machinery remained globally required at lines 34-35 (a 120s mutated-notebook path, a Task 3/4 "execution harness", a Task 5 "mutation client", injected-deadline regression tests) — an implementer following the global scope would resurrect deleted machinery. Reworded to the plain 20s per-notebook CI timeout (with a 120s bound only for Task 5's variant re-executions).

### Round 8 outcome and amendment

Round 8 is `[self]` APPROVE, `[glm]` APPROVE WITH NITS, `[fable]` APPROVE WITH NITS, `[sol]` REJECT — no consensus, but the character of the round confirms the strip worked: `[sol]`'s reject is janitorial (a stale requirement I forgot to clean up), not another injection evasion, and it explicitly calls the content design sound. `[fable]`'s MAJOR is a real content defect the strip introduced — dropping `optimizer_step` broke a legitimate honest-mistake check — now fixed by restoring the field. All round-8 findings are content/coherence; none reopens anti-cheat.

### Review 9 — glm (2026-08-28)

- **Verdict**: APPROVE.
- Verified via `git diff` that the round-8 fixes landed and touched no ledger row; every remaining harness/sandbox mention in the body is a disclaimer, not a requirement; round history intact.

### Review 9 — fable (2026-08-28)

- **Verdict**: APPROVE.
- Confirmed the `optimizer_step` restoration detects a reset optimizer (honest fresh optimizer records 1..40 twice and fails continuity; a continued one records 41..80 and passes) and is teaching-coherent; re-derived every ledger and re-verified self-containedness against the shipped corpus.

### Review 9 — sol (2026-08-28)

- **Verdict**: REJECT.
- Confirmed lines 34-35, the `optimizer_step` contract, and Task 6.
- `[sol][FIXED]` **MAJOR** phase-ordering defect introduced by the round-8 timeout reword: a Task-3 checkbox required executing B2-020 solution notebooks, but Task 3 publishes statements with solutions deferred — solutions are not created until Task 4, which already owns their CI execution. The Task-3 checkbox is deleted; Task 4 retains the complete requirement.

### Round 9 outcome and amendment

Round 9 is `[self]` APPROVE, `[glm]` APPROVE, `[fable]` APPROVE, `[sol]` REJECT — one finding, a
self-inflicted phase-ordering slip from the round-8 timeout reword (an execute-solutions checkbox
placed in the statement-authoring task). Fixed by deletion; Task 4 already owns solution
execution. Three of four approve with the fourth's sole finding a one-line coherence fix.

### Review 10 — self / glm / fable / sol (2026-08-29)

- **`[self]`**: APPROVE — deleted the misplaced Task-3 checkbox; ran a full phase-ordering self-review (no task depends on a later task's artifact; every referenced file is created by an earlier task).
- **`[glm]`**: APPROVE — diff is only the deletion plus round-9 records; ledgers recompute; prior verdicts unaltered.
- **`[fable]`**: APPROVE, no findings — "the plan is implementable end-to-end as written"; deletion left no orphan (Task 4 solely owns solution execution), self-containedness and the `optimizer_step` contract intact, phase ordering sound end-to-end.
- **`[sol]`**: APPROVE — "no content findings remain"; all six tasks correctly ordered, no normative dangling reference to removed machinery.

## PLAN GATE CLOSED — 4-way consensus (Review 10, 2026-08-29)

All four reviewers APPROVE with no open blockers. The gate ran ten rounds. Rounds 4-7 were a
genuine design problem — an anti-cheat arms race the plan had pulled p19 into (each round `[sol]`
found a sharper injection evasion of the prior round's fix). The user directed on 2026-08-28 that
anti-cheat is out of scope and no solution may require a sandbox; the resulting strip (Review 8
onward) reduced the plan to its material core, and the gate converged: Review 8 caught one real
content defect the strip introduced (a dropped `optimizer_step` field), Reviews 9-10 closed a
single misplaced checkbox. What ships is a materially simpler, self-contained, correctly phased
plan. Implementation may proceed.

## Content Review

Pending implementation and four-way blind review.

## Post-execution report

Pending implementation, verification, review, PR guard, and squash merge.
