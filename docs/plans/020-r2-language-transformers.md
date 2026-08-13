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

The unit depends on `B2-019-attention-transformers`.
It reuses Book 1 C8 only as a qualified remediation reference for token-to-index and fixed-vector vocabulary, and it reuses B2-019 for the Transformer block and causal mask.
It must not re-teach tokenization, GloVe loading, or fixed-vector similarity.
All corpora, labels, vocabulary maps, seeds, expected probes, and checkpoints are small, explicit, synthetic, CPU-only, and committed as source-generation code or literal notebook data.
No internet model hub, external dataset, opaque checkpoint, tokenizer library, or hidden pretrained parameter is in scope.
Every CPU training task uses vocabulary size at most 12, sequence length at most 8, one Transformer block with model width at most 8, at most two heads, and at most 80 fixed optimization epochs; a fresh solution notebook must finish within 20 seconds and a mutated notebook within 120 seconds.
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
| 3 | `03-pretraining-objectives.ipynb` | causal next-token versus masked-token objectives, corruption/masking protocol, leakage counterexamples, objective selection, and reproducible pretraining traces |
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

Create `tools/verify_language_transformer_mutations.py` and `tests/test_language_transformer_mutations.py` using the same fail-closed source-match and wrapped-real-answer-check pattern as Plan 019.
The untouched corpus must pass all five mutations; each altered solution must fail its named answer assertion:

1. `practice/p07_solution.ipynb` — mutate the explicitly marked context-to-target update hook so its table is not updated;
2. `practice/p18_solution.ipynb` — mutate the explicitly marked target-shift hook so it supplies unshifted input tokens;
3. `practice/p11_solution.ipynb` — mutate the explicitly marked masking hook so it leaves the original true token visible;
4. `practice/p21_solution.ipynb` — mutate the explicitly marked frozen-stage parameter-policy hook so the encoder updates during the frozen stage;
5. `practice/p24_solution.ipynb` — mutate the explicitly marked evaluation-index hook so it includes one named training row; a separate end-of-notebook disjointness assertion must detect that leaked split.

Each mutation-relevant student statement declares the semantic hook's required function name, input/output contract, and the non-solution marker contract below: `# MUTATION_TARGET:<id>:BEGIN`/`END` at the hook body and exactly one top-level `# EXPECTED_CHECK:<id>` immediately preceding the mutation-specific `assert` in the solution's final Answer check.
It instructs the solver to provide that assertion without supplying a target numeric answer, solution approach, or test expression.
It also prohibits any assertion before the final Answer check from checking that mutation hook's behavioral outcome; ordinary shape/type/input checks remain allowed.
The blind solver may use any equivalent implementation within that hook; it does not need to reproduce a literal source line or algorithmic outline.
Each required hook is delimited exactly by `# MUTATION_TARGET:<id>:BEGIN` and `# MUTATION_TARGET:<id>:END`, each at the same indentation within the named function body; zero, multiple, reversed, nested, or cross-function markers are hard failures.
The runner uses the delimiters plus the function AST range, applies the following fixed body replacement rather than matching a prescribed solution line, and uses AST to bind one named top-level expected assertion:

| ID | Required hook signature | Mutant body outcome |
|---|---|---|
| `embedding-update` | `update_embedding_table(table, contexts, targets, learning_rate) -> table` | return an unchanged copy of `table` |
| `target-shift` | `shift_targets(tokens) -> (inputs, targets)` | return `(tokens[:-1], tokens[:-1])` |
| `mlm-mask` | `apply_mlm_mask(tokens, mask_index, mask_token) -> masked_tokens` | return an unchanged copy of `tokens` |
| `frozen-stage` | `configure_frozen_stage_optimizer(encoder, classifier, learning_rate) -> optimizer` | return a `torch.optim.SGD` optimizer over `list(encoder.parameters()) + list(classifier.parameters())` at `learning_rate` rather than the required classifier-only parameter set |
| `evaluation-indices` | `evaluation_indices(train_indices, test_indices, leaked_train_index) -> list[int]` | return `list(test_indices) + [leaked_train_index]` rather than the required test-only list |

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
- [ ] Extend the shared manifest parser in `tools/model.py` with the narrow lifecycle policy: a deferred solution policy is valid only for `B2-020-language-transformers` with `plan: plan-020`, `expires: 2026-08-31`, and **no** declared solution file present; all other deferred manifests, an altered plan/expiry, or even one present B2-020 solution under a deferred policy are hard parse errors.
  Update `tools/audit_curriculum.py` to invoke `load_unit_manifests()` before its raw-YAML notebook inventory so it cannot independently accept a deferred policy that the shared parser rejects.
  This common parser rule is then the enforcement used by inventory, coverage, and layer-boundary consumers; test each consumer observes the same rejection through a copied registered Book 2 fixture.
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
  Because this is statement-only publication, set the B2-020 manifest's policy exactly to `{status: deferred, plan: plan-020, expires: 2026-08-31}`; the shared parser must compare that date to the current UTC date and hard-fail once expired, so this intentionally temporary intermediate commit is not green after the deadline.
  Its focused tests must freeze the clock on each side of the expiry and prove inventory/coverage/layer-boundary accept only the unexpired named temporary debt and surface its expiry rather than treating absent solutions as valid generally.
  Extend `load_unit_manifests(root, *, as_of_date: date | None = None)` with a typed, non-environment date parameter; omitted by every normal consumer, it uses current UTC, while `scripts/ci-local.sh` must reject `USAAIO_HISTORICAL_VERIFY` and `USAAIO_AS_OF_DATE` if present before any check runs.
  The only historical path is the new explicit `scripts/verify-historical-deferred-policy.sh <archived-commit> <ISO-date>` command, which extracts that commit to a temporary archive and calls a dedicated Python entry point that passes the validated ISO date through this `as_of_date` parameter.
  The parser never reads expiry dates from environment variables.
  Test archived verification succeeds only with its explicit parameter; direct parser/check invocations cannot override expiry through environment variables; and normal CI fails before any check when either variable is set.
  If work has not reached the required-policy transition by that date, a separately reviewed follow-up plan must explicitly amend the expiry before any continuation; it is never silently extended.
- [ ] Have `scripts/generate_language_data.py` run the Session-3 seeded causal/MLM pretraining contract from fixed seed `20260812`, certify literal initial and final losses, and render the trained state into tracked, human-readable `data/tiny_encoder_checkpoint.py` with vocabulary, split IDs, trained encoder weights, objective/loss trace, and semantic hash.
  Pin the authoring envelope to the lockfile-resolved CPU torch build, deterministic algorithms, single intra/inter-op thread, and every Python/NumPy/Torch seed; do not assert a Linux-only `+cpu` local-version tag.
  Define the versioned semantic hash as SHA-256 over canonical JSON containing vocabulary/splits/architecture/objective plus every committed trained parameter rounded to six decimal places in sorted name/index order; it intentionally excludes raw float bytes.
  Standard CI verifies the committed checkpoint's self-consistent canonical JSON/hash and trained functional contract (both losses improve and fixed held-out probes beat the literal initial-state baseline by named margins), but does **not** regenerate-and-hash-compare 80-epoch weights across CPU architectures.
  The author/CI-only `tiny_encoder_checkpoint.py` must export schema version `1`, `TOKEN_TO_ID`, `TRAIN_SPLIT_IDS`, exact `CAUSAL_HELDOUT_IDS` and `MLM_HELDOUT_IDS`, `INITIAL_LOSSES`, `FINAL_LOSSES`, `PROBE_EXPECTED_TOP1_IDS`, and the measured `MIN_ABSOLUTE_LOSS_IMPROVEMENTS`.
  After the first deterministic Task-3 generator run, record those literal measured loss/probe values and margins with at least 2× observed numerical headroom, then freeze them in the tracked module and its test; no guessed pre-authoring threshold is accepted.
  Its test reconstructs the literal initialized width-8 architecture from seed `20260812`, validates every checkpoint parameter name/shape/dtype (`float32`) against that architecture, recomputes losses within the frozen tolerances, requires each final loss to beat the corresponding initial loss by its frozen minimum absolute improvement, and requires each named probe's top-1 ID to match the pinned expected ID.
  The generated student-facing `tiny_encoder_state.py` contains only architecture/state tensors and state hash—never losses, probes, targets, or training trace—and is the sole state source p20/p21 may load.
  These fixed data IDs, measured margins, API fields, and canonical JSON schema/version are mandatory, so a self-hashed random or arbitrary parameter set cannot pass merely by changing its own metadata.
  A separate explicit local `--refresh-checkpoint` generator command is the record-once maintenance path; it reports canonical deltas and requires an intentional committed source update when a supported toolchain changes.
  `data/language_fixture.py` contains only the fixed literal vocabulary, token-ID sequences, masks, splits, and labels needed by students, never author training code, answers, loss targets, or generated weights.
  The generator alone creates `tiny_encoder_checkpoint.py` and `tiny_encoder_state.py`.
  p19 independently reruns both specified bounded seeded causal and MLM 80-epoch training traces from the literal fixture, asserts each trace improves from its own initial loss, and recomputes its own held-out probes; it does not load either checkpoint/state artifact or copy their constants.
  p20/p21 may load only `tiny_encoder_state.py` as the committed trained source state.
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

- [ ] Implement and run `scripts/prepare_b2_020_blind_solve_input.py` to build an auditable, **procedurally isolated** blind-solve handoff at the committed Task-3 revision: create a temporary directory from `git archive <task3-commit>` containing **only** the 24 student practice notebooks, unit `lesson.ipynb`/`review.ipynb`, `lessons/`, `manifest.yaml`, `data/language_fixture.py`, and `data/tiny_encoder_state.py`.
  The author-only `scripts/generate_language_data.py` is explicitly excluded because it contains the authoring training design.
  Emit a sorted allowlist with SHA-256 for each input and the exact source commit; verify the directory contains no plan, author notes, solution notebook, or unrelated repository file.
  Dispatch a separate fresh GPT-5.6-sol solution session in that directory with only this allowlist, never the author outline, statement-session context, solution notebooks, or a solution design.
  Its sole allowed outputs are exactly `out/practice/p01_solution.ipynb` through `p24_solution.ipynb` and `out/BLIND_OUTPUTS.sha256`; the output manifest lists those 24 relative paths in lexical order with SHA-256, and no other output file is accepted.
  Implement and run `scripts/import_b2_020_blind_solve_output.py` to reject a missing, extra, renamed, or digest-mismatched output, copy only those 24 files to the corresponding branch `practice/pNN_solution.ipynb` paths, and rehash the destination byte-for-byte against `BLIND_OUTPUTS.sha256` before Task 4 tests or mutation work.
  Task 5 may not edit an imported solution notebook. A pre-oracle mutation failure is a hard handoff failure: regenerate the full blind output through a fresh isolated solve and verified import, rather than silently repairing the branch copy.
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

Pending fresh independent Review 4 verdicts: `[sol]`, `[glm]`, and `[fable]`.

## Content Review

Pending implementation and four-way blind review.

## Post-execution report

Pending implementation, verification, review, PR guard, and squash merge.
