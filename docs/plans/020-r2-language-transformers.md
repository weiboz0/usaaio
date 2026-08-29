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
Every CPU training task uses vocabulary size at most 12, sequence length at most 8, one Transformer block with embedding/attention width at most 8 (the feed-forward inner width is separately pinned at 16), at most two heads, and at most 80 fixed optimization epochs; a fresh solution notebook must finish within 20 seconds and a mutated notebook within 120 seconds.
The Task 3/4 execution harness must measure a per-notebook 20-second wall-clock timeout and Task 5's mutation client must use 120 seconds, with fast regression tests that inject shorter deadlines while separately pinning the production constants.

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

## Permanent answer-affecting mutations

Create `tools/verify_language_transformer_mutations.py` and `tests/test_language_transformer_mutations.py` using the same fail-closed marker/AST and wrapped-real-answer-check pattern as Plan 019.
The untouched corpus must pass all five mutations; each altered solution must fail its named answer assertion:

1. `practice/p07_solution.ipynb` — mutate the explicitly marked context-to-target update hook so its table is not updated;
2. `practice/p18_solution.ipynb` — mutate the explicitly marked target-shift hook so it supplies unshifted targets;
3. `practice/p11_solution.ipynb` — mutate the explicitly marked masking hook so it leaves the original true token visible;
4. `practice/p21_solution.ipynb` — mutate the explicitly marked frozen-stage parameter-policy hook so the encoder updates during the frozen stage;
5. `practice/p24_solution.ipynb` — mutate the explicitly marked evaluation-index hook so it includes one named training row; the marked `EXPECTED_CHECK:evaluation-indices` assertion inside the final Answer check is the separate end-of-notebook disjointness assertion that must detect that leaked split.

Each mutation-relevant student statement declares the semantic hook's required function name, input/output contract, and the non-solution marker contract below: `# MUTATION_TARGET:<id>:BEGIN`/`END` at the hook body and exactly one top-level `# EXPECTED_CHECK:<id>` immediately preceding the mutation-specific `assert` in the solution's final Answer check.
It instructs the solver to provide that assertion without supplying a target numeric answer, solution approach, or test expression.
It states verbatim that no assertion before the final Answer check may inspect that hook's return value or behavioral outcome; ordinary shape/type/input checks remain allowed.
The blind solver may use any equivalent implementation within that hook; it does not need to reproduce a literal source line or algorithmic outline.
Each required hook is delimited exactly by `# MUTATION_TARGET:<id>:BEGIN` and `# MUTATION_TARGET:<id>:END`, each at the same indentation within the named function body; zero, multiple, reversed, nested, or cross-function markers are hard failures.
The runner uses the delimiters plus the function AST range, applies the following fixed body replacement rather than matching a prescribed solution line, and uses AST to bind one named top-level expected assertion:

| ID | Required hook signature | Mutant body outcome |
|---|---|---|
| `embedding-update` | `update_embedding_table(table: torch.Tensor, contexts: torch.LongTensor shape (N,), targets: torch.LongTensor shape (N,), learning_rate: float) -> torch.Tensor` | return an unchanged clone of `table` |
| `target-shift` | `shift_targets(tokens: list[int]) -> tuple[list[int], list[int]]`, with `tokens` exactly one unbatched sequence of length at least 2 | return `(tokens[:-1], tokens[:-1])` |
| `mlm-mask` | `apply_mlm_mask(tokens: list[int], mask_index: int, mask_token: int) -> list[int]`; fixtures require `tokens[mask_index] != mask_token` | return a list copy of unchanged `tokens` |
| `frozen-stage` | `configure_frozen_stage_optimizer(encoder, classifier, learning_rate) -> optimizer`; the frozen stage is expressed **solely** by a classifier-only optimizer parameter list and must not set any encoder `requires_grad` flag; immediately before the unfreeze optimizer is built, call `encoder.zero_grad(set_to_none=True)` | return a `torch.optim.SGD` optimizer over `list(encoder.parameters()) + list(classifier.parameters())` at `learning_rate` rather than the required classifier-only parameter set |
| `evaluation-indices` | `evaluation_indices(train_indices: list[int], test_indices: list[int], candidate_extra_index: int) -> list[int]` | return `list(test_indices) + [candidate_extra_index]` rather than the required test-only list |

The parser tests every malformed-marker case and every replacement's function/signature mismatch.
It AST-wraps that exact assertion so an `AssertionError` becomes the fixed `PLAN020_EXPECTED_CHECK::<id>` failure token, executes the whole notebook in order with `NotebookClient(allow_errors=True)`, inspects each cell output, and accepts the mutant only if that token arises from the named assertion; an earlier error before the named oracle is a strict runner failure, is recorded, and does not substitute for the named oracle.
It rejects zero/multiple hook spans, a target outside the declared hook, a missing/duplicate/wrong-ID/non-top-level expected-check marker, an expected-check marker outside one assertion, a mutant that executes without the named oracle failing, and a named assertion that still passes.

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
- Modify: `tests/test_b2_019_statements.py`
- Modify: `tests/test_integration.py`
- Modify: `tests/test_scope.py`
- Create: `tests/test_b2_020_statements.py`

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
- Create: `tools/verify_b2_020_solution_timeouts.py`
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
  The single trained state uses this exact protocol: initialize a one-block, pre-norm causal/MLM Transformer encoder (vocabulary 12, sequence length 8, width 8, two attention heads, feed-forward width 16) plus one vocab-logit head shared across both pretraining phases but NOT weight-tied to the embedding table (the head is a distinct parameter, so the exact parameter-object multiset assertion above counts it separately) from seed `20260812`; train first on the literal causal batches for 40 full-batch AdamW updates (`lr=0.03`, `weight_decay=0`), then on the literal MLM batches for 40 full-batch AdamW updates with the same optimizer state continued across the phase boundary.
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
  The p19 student statement itself teaches and pins the complete preceding 40-update causal-then-40-update MLM protocol, including architecture/masks/AdamW/update order; this is necessary learner-visible training content, not an answer outline.
  p19 must expose `run_pretraining_protocol(fixture) -> (encoder, head, phase_trace)`, where `phase_trace` has exactly 80 ordered records with fields `phase`, `update_index`, `mask_mode`, `optimizer_instance_id`, `optimizer_step`, and `loss`.
  p19 independently reruns that exact protocol through this callable from the literal fixture, asserts each phase improves from its own phase-initial loss, and recomputes both final-state held-out objective losses/probes; it does not load either checkpoint/state artifact or copy their constants.
  The statement/import test rejects `p19_solution.ipynb` if source references `tiny_encoder_state`, `tiny_encoder_checkpoint`, or either artifact's import path, and execution runs p19 in a temporary copy containing only its notebook and `data/language_fixture.py` with the state/checkpoint paths absent; a dynamic-import/path-load bypass fixture must fail.
  The isolated p19 test invokes and instruments this callable's structured trace plus patchable optimizer/model constructors to prove its own 40 causal then 40 MLM ordered updates, causal then bidirectional MLM masks, and one optimizer continuous across the boundary; skip-MLM, reset-optimizer, and causal-mask-in-MLM mutants each fail named assertions.
  **Returned-state identity (Review 4 `[sol]` BLOCKER).** Instrumenting the trace proves that updates happened; it does not prove they happened to the objects returned.
  The isolated test must additionally assert that the parameter objects held by the instrumented optimizer are the SAME objects reachable from the returned `encoder`/`head` — identity over `optimizer.param_groups` versus `encoder.parameters()`/`head.parameters()`, not equality of values — and must snapshot those same returned objects immediately before the first update and after the last, requiring their tensors to differ.
  It then independently reconstructs the seeded-initial state and requires each returned held-out objective loss to beat that baseline by a frozen margin, with every probe meeting a pinned oracle, so that "recomputes" is replaced by a functional assertion about the returned model.
  Optimizer-parameter identity alone is still evadable (Review 5 `[sol]`): a notebook can train a hidden model A, build the optimizer over the returned model B's exact parameters, then COPY A's trained tensors into B before a final no-gradient optimizer step — B changes, beats the baseline, and passes every probe although every forward and gradient came from A.
  Restricting foreign writes to OUTSIDE the cycle is still evadable (Review 6 `[sol]`): a notebook can copy a hidden model A's trained tensors into the returned model during its `forward`, so the loss, gradients, and step are all genuinely on the returned parameters yet the values are A's, injected inside the cycle.
  Because injecting a CORRECT final value is indistinguishable from having trained it, no result-level check (baseline margin, probe, or reference-trajectory match) can separate the two; the contract must instead pin the PROCESS by verifying the optimizer's closed-form transition at every step.
  The assertion is therefore: an exact parameter-object MULTISET match (no missing, extra, or duplicated parameter); returned parameters held tensor-identical through each `forward` and `backward` (only `step()` may mutate `.data`, so the gradient is genuinely the return model's gradient on its own current parameters); and, at each of the 80 updates, the post-step optimizer state — every parameter tensor AND the AdamW moment buffers (`exp_avg`, `exp_avg_sq`, `step`) — equal an independently recomputed AdamW transition of the captured pre-step state under the observed gradient.
  Pinning the full per-step transition leaves no injection point: to pass every step's recomputation a notebook must present, at every step, the exact values the real optimizer would produce from the real gradient, which is achievable only by actually running the protocol.
  Four named mutants must each fail a named assertion: `train-A-return-fresh-B` (returns a different object), `train-A-copy-into-B` (foreign values written between or after cycles), `copy-into-B-during-forward` (foreign values written inside a cycle's forward), and `loss-on-A/optimizer-on-B` (loss and optimizer bound to different models).
  **Read isolation for p19 (Review 4 `[sol]` BLOCKER).** A literal-name scan plus temporary-copy execution does not stop a synthesized absolute path, glob, or `importlib` load from the still-readable original repository.
  A self-reported read-access log is not trusted evidence (Review 5 `[sol]`): notebook code can read through `os.open`, `pathlib`, `ctypes`, `mmap`, or a child process and still emit a clean application-level log.
  p19's isolated execution must therefore run under a mechanism EXTERNAL to the notebook process that makes the original repository unreachable — a filesystem sandbox or mount namespace whose root is the temporary copy, or an out-of-process syscall/file-access audit covering the process and all descendants.
  If no such facility is available in the execution environment, that is an explicit judgment-fork stop for the implementer (recorded, surfaced), not a fallback to an in-process log.
  Dedicated bypass mutants reaching the original repository outside the temporary copy — by absolute path, by glob, by `importlib.import_module`, by `os.open`/`pathlib`, and by a child process — must each fail.
  p20/p21 must load `tiny_encoder_state.py` as their sole pre-finetuning encoder state, reconstruct `ENCODER_STATE_HASH` before the first fine-tuning update, and assert equality to the shared `ENCODER_STATE_HASH` verified against `tiny_encoder_checkpoint.py`.
  Their tests replace the loader with a random/fresh or no-load encoder and require the provenance assertion to fail before fine-tuning.
  Tests reject an initial/random-weight checkpoint before fine-tuning through the functional contract as well as hash consistency.
- [ ] Exercise all eight owned concepts with at least three direct practices and ensure no problem tags a concept outside the unit/prerequisite closure.
- [ ] Give each of the five mutation-relevant statements its declared `MUTATION_TARGET` bind point and source-interface identifier without exposing an answer; assert the actual solution later contains exactly that marker and a separately named oracle assertion.
- [ ] In the same commit that creates the manifest, append the exact B2-020 weeks 7–12/global weeks 47–52 ledger above and its post-week-12 final-assessment marker.
  Then promote exactly the five named coverage rows with literal lesson anchors and evidence IDs, and regenerate/check the inventory, Book 2 course structure, roadmap, and audit from the now-valid paths.
  For `nlp-word-embeddings`, replace the inherited C8 anchors, Book 1 practice/assessment evidence, and Book 1 `shipped_concepts` with B2-020 Session 1–3 anchors, the named B2 practices in the ledger, and `shipped_concepts: [learned-token-embedding]`; set `coverage: covered`, `deficits.modalities_missing: []`, and retain `destination: B2-020-language-transformers`.
  The statement test must assert this exact destination/disposition/covered-state transformation and reject any remaining `book1:C8-embeddings` evidence in the B2-020 claim, so the layer-boundary claim cannot be satisfied by Book 1 evidence.
- [ ] Test hygiene, lesson order, manifest paths, source isolation, CPU label, imported-concept boundary, time arithmetic, and coverage tags without executing student notebooks.
- [ ] Implement `tools/verify_b2_020_solution_timeouts.py` as the fresh-kernel execution harness for B2-020: it takes an explicit notebook list, executes only B2-020 solution notebooks through `NotebookClient`, enforces a process-level 20-second wall-clock deadline per notebook in addition to a cell timeout, and emits a failing notebook/elapsed-time diagnostic.
  It uses the same subprocess process-group TERM, KILL-after-grace, wait/reap, and no-surviving-child contract required for Task 5 mutations.
  Expose a test-only injected deadline; test a synthetic sleeping notebook with a 1-second injected deadline without waiting for a production-length sleep, and separately assert the production constant is 20 seconds.
  Do not rely on a Jupyter CLI default timeout.
- [ ] Commit: `feat: teach language Transformer statements`.

### Task 4 — Blind-author and execute solutions

**Files:**

- Create: `book2/units/B2-020-language-transformers/practice/p01_solution.ipynb` through `p24_solution.ipynb`
- Create: `scripts/prepare_b2_020_blind_solve_input.py`
- Create: `scripts/import_b2_020_blind_solve_output.py`
- Modify: `book2/units/B2-020-language-transformers/manifest.yaml`
- Modify: `scripts/ci-local.sh`
- Modify: `tools/model.py`
- Test: `tests/test_b2_020_statements.py`

- [ ] Before building the handoff, smoke-test the chosen external isolation facility (for example `bwrap` or `unshare`, both present on this host) so an unexpected unprivileged-namespace restriction surfaces as the plan's designed judgment-fork stop at the START of this task rather than mid-implementation.
- [ ] Implement and run `scripts/prepare_b2_020_blind_solve_input.py` to build an auditable, **procedurally isolated** blind-solve handoff at the committed Task-3 revision: create a temporary directory from `git archive <task3-commit>` containing **only** the 24 student practice notebooks, unit `lesson.ipynb`/`review.ipynb`, `lessons/`, `manifest.yaml`, `data/language_fixture.py`, and `data/tiny_encoder_state.py`.
  The author-only `scripts/generate_language_data.py` is explicitly excluded because it contains generation/serialization implementation, while the necessary instructional training protocol is already stated in p19 itself.
  Emit a sorted allowlist with SHA-256 for each input and the exact source commit; verify the directory contains no plan, author notes, solution notebook, or unrelated repository file.
  Dispatch a separate fresh GPT-5.6-sol solution session in that directory with only this allowlist, never the author outline, statement-session context, solution notebooks, or a solution design.
  **Read isolation, not just input digests (Review 4 `[sol]` MAJOR).** The allowlist and digests prove what was copied in and what came back; they do not constrain what the session READ.
  A working-directory change cannot constrain a separately dispatched session, and a solver-produced log is not independent evidence (Review 5 `[sol]`).
  The solve must run under the same external isolation the p19 test requires — a sandbox/mount namespace or out-of-process access audit under which the original repository is absent — with the same judgment-fork stop if that facility is unavailable, rather than accepting a self-reported log.
  The forbidden reads are enumerated by exact path, not by the loose word "checkpoint": the author-only `scripts/generate_language_data.py`, `data/tiny_encoder_checkpoint.py`, the plan file, and every non-allowlisted repository file are forbidden, while the allowlisted `data/tiny_encoder_state.py` (which p20/p21 legitimately load) is explicitly permitted.
  The statement-side scan is symmetric: a student notebook referencing a solution notebook name, a solution path, or any author-only artifact is a hard failure.
  Its sole allowed outputs are exactly `out/practice/p01_solution.ipynb` through `p24_solution.ipynb` and `out/BLIND_OUTPUTS.sha256`; the output manifest lists those 24 relative paths in lexical order with SHA-256, and no other output file is accepted.
  Implement and run `scripts/import_b2_020_blind_solve_output.py` to reject a missing, extra, renamed, or digest-mismatched output, and before copying run the read-only mutation-marker/AST structural validator (marker count/order/indentation/function/signature/top-level expected-check plus a best-effort flag for any pre-oracle assertion referencing a hook return/output variable; no mutations or answers) against the isolated outputs.
  Copy only those 24 files to the corresponding branch `practice/pNN_solution.ipynb` paths, and rehash the destination byte-for-byte against `BLIND_OUTPUTS.sha256` before Task 4 tests or mutation work.
  Task 5 may not edit an imported solution notebook. A pre-oracle failure **or named oracle that survives its prescribed mutant** is a hard handoff failure: regenerate the full blind output through a fresh isolated solve and verified import, rather than silently repairing the branch copy.
  Cap this recovery at two fresh blind-output attempts; a second structural, pre-oracle, or oracle-survival failure stops the autopilot at a judgment fork with the exact diagnostic rather than looping.
  Retain the input allowlist, output digest, source commit, and verified destination hashes in the post-execution report, proving the committed solution notebooks are exactly the blind-authored artifacts.
- [ ] Require each solution to preserve the learner-visible header, use the seeded literal data, state every answer, and end with a non-vacuous `### Answer check` plus exact numeric/shape/training assertions.
- [ ] After all 24 solutions exist, atomically replace B2-020's deferred policy with `solution_policy: required`; test that every declared solution path exists and that any retained deferred policy (rejected by the shared manifest parser as soon as one solution exists) or deleted solution fails inventory, coverage, and layer-boundary checks.
- [ ] Execute p01–p24 in numeric order through `tools/verify_b2_020_solution_timeouts.py`, each on its own fresh kernel with a 20-second wall-clock timeout, and invoke that same harness from the Book 2 notebook-execution step of `scripts/ci-local.sh` for the B2-020 solutions rather than the unbounded Jupyter CLI route.
  While the blind solver constructs its complete 24-notebook output set in the isolated directory, run only this explicit-notebook-list harness and no manifest-aware verifier; the branch receives all 24 only through the atomic verified import and required-policy flip.
  Measure each completed solution on the verification host and require the maximum to be at most 10 seconds, documenting those timings in the post-execution report as twofold headroom under the 20-second production limit.
  Prove the answer register, source isolation, student hygiene, required-solution policy, and timeout harness pass.
- [ ] Commit: `feat: add independently solved language practices`.

### Task 5 — Lock coverage and language-model failure modes

**Files:**

- Create: `tools/verify_language_transformer_mutations.py`
- Create: `tests/test_language_transformer_mutations.py`
- Modify: `scripts/ci-local.sh`
- Modify: `tests/test_b2_020_statements.py`

- [ ] Implement the five named answer-affecting mutations and the fail-closed runner contract.
- [ ] Enforce a 120-second mutation-execution timeout and add focused timeout mutants for both the 20-second solution route and the 120-second mutation route.
  Both runners expose test-only injected deadlines so those tests finish in seconds, while separate assertions pin production values to 20 and 120 seconds.
- [ ] The mutation runner launches each mutated-notebook worker in a new subprocess process group, applies the 120-second process-level deadline (not merely a cell timeout), then on expiry sends TERM, escalates to KILL after a short grace period, waits/reaps the worker, and reports its notebook and elapsed time.
  A 1-second injected synthetic-sleeper test must prove timeout, process-group cleanup, and no surviving child; an unmutated run remains required to pass.
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
- [ ] Before the content gate and again immediately before merge, emit a `blind-provenance` report that compares every final statement byte hash to the Task-3 input allowlist and every final solution byte hash to `BLIND_OUTPUTS.sha256`.
  Any difference must name the file, reason, authoring stage, and reviewer confirmation as a `post-blind amendment`; only a zero-difference report may claim the committed solutions are exactly the blind-authored artifacts.
  "Semantic" must be decided mechanically, not by a reported classification (Review 5 `[sol]`): a changed number, negation, identifier, or tolerance could otherwise be labeled formatting and keep a stale solution.
  Every markdown and code cell SOURCE is treated as semantic by default: the check canonicalizes each statement notebook to the ordered concatenation of its cell sources and requires that digest to be byte-identical to the Task-3 blind input, and any difference there invalidates the affected blind output and forces a fresh isolated solve.
  A `post-blind amendment` is admissible ONLY for changes confined to an explicitly enumerated set of notebook-JSON metadata paths (for example `metadata.kernelspec`) that leave every cell source digest unchanged.
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

### Round 6 outcome and amendment

Round 6 is `[self]` APPROVE, `[glm]` APPROVE, `[fable]` APPROVE WITH NITS, `[sol]` REJECT — no consensus.
The single `[sol]` blocker is one more level of the returned-state injection: rounds 4-6 walked it from "prove B changed and is good" to "prove B changed by training" to "prove every step is the optimizer's exact function of the gradient." This round's fix pins the full per-step optimizer transition (parameters and moment buffers), which is the terminal form: because injecting a correct value is result-indistinguishable from training it, only verifying the closed-form process at every step separates the two, and a notebook that passes every step's recomputation has necessarily run the protocol. `[fable]` closed the pinned-constant thread exhaustively and both `[sol]` and `[fable]` judge the accumulated contract satisfiable by an honest notebook, so the remaining question for round 7 is solely whether this per-step transition check has any residual gap.

Pending fresh independent Review 7 verdicts: `[sol]`, `[glm]`, and `[fable]`.

## Content Review

Pending implementation and four-way blind review.

## Post-execution report

Pending implementation, verification, review, PR guard, and squash merge.
