# Plan 009 — Teaching Units Tranche 5: C7 + C8 (CNNs/transfer + embeddings)

> **For agentic workers:** the proven 006/007/008 cycle verbatim (per-task commits; Fable
> drafts lessons + statements, outlines to `reference/outlines-009/<unit>.md` (gitignored);
> gpt-5.6-sol blind-solves per unit; reconciliation before the gate; amended statements →
> blind re-solve; proofs carry numeric anchors + claim-by-claim rubric; ban-register
> contract = core set as minimum + workaround-closers; lesson narration MUST match printed
> output — plan-008's gate caught even a FIX introducing a narration mismatch).

**Goal:** Ship `C7-cnn-transfer` and `C8-embeddings` at the v2 bar (12/16 units).

## Deps (Task 0)

`torchvision` from the SAME explicit pytorch CPU index (add `torchvision = { index = "pytorch" }`
to `[tool.uv.sources]`, then `uv add torchvision` — the 008 pattern; NEVER a bare index add,
the pytorch index shadows PyPI numpy). `gensim` from PyPI (`uv add gensim`).
Verify both import; pin versions in the post-exec report **including the resolved
torch↔torchvision pair (uv add must not bump torch; gensim needs ≥4.3.3 for numpy 2.x —
record both).**

> **Executed (Task 0):** torch **2.13.0+cpu** (unchanged) · torchvision **0.28.0+cpu**
> (resolved from the pinned explicit pytorch index) · gensim **4.4.0** (≥4.3.3 ✓).
> Caches warmed at reference/cache/: resnet50 IMAGENET1K_V1 (total params 25,557,032 —
> matches the canonical figure) and glove-wiki-gigaword-100 (400k vocab × 100 dim).
> Both covered by the `reference/*` gitignore; tree clean.
**Download/cache pin:** pretrained weights and corpora are fetched at first execution and
cached under `reference/cache/` (gitignored). **Path resolution pin (gate finding — notebooks
execute with cwd = the notebook's own directory, so a relative cache path would scatter caches
into unit dirs and re-download per notebook): every loading notebook's header cell runs, BEFORE
the torch/gensim import, exactly:**

**The recipe is SPLIT BY LIBRARY (gate finding: a combined recipe would put the string
TORCH_HOME into C8 notebooks and trip C8's own torch-free sweep). C7 loading notebooks run:**

```python
import os, pathlib
_root = next(p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]
             if (p / "pyproject.toml").exists())
os.environ["TORCH_HOME"] = str(_root / "reference" / "cache" / "torch")
```

**C8 loading notebooks run the same `_root` lines followed ONLY by:**

```python
os.environ["GENSIM_DATA_DIR"] = str(_root / "reference" / "cache" / "gensim")
``` First ci run downloads (~100MB resnet50 +
~130MB glove-wiki-gigaword-100); later runs are warm. **This warm-cache claim is a
LOCAL-ci property — this repo's gate is scripts/ci-local.sh on the developer machine and no
remote runner exists; if remote CI is ever added, it must define its own cache persistence
(gate finding).** Determinism pin: resnet50 loads
`weights=ResNet50_Weights.IMAGENET1K_V1` EXPLICITLY (never `pretrained=True` — deprecated and
ambiguous) **and is put in `model.eval()` immediately after loading, in every notebook that
runs a forward pass** (self-review amendment: train-mode BatchNorm uses batch statistics —
nondeterministic across batch composition AND it mutates running buffers; eval() is the
single switch that makes forward passes reproducible). **All forward passes additionally run
under `torch.inference_mode()` (gate finding: fresh-head parameters default to
requires_grad=True, so without it autograd graphs silently build even in a no-training
course — and it's the honest engineering register).** GloVe artifact `glove-wiki-gigaword-100`
is a fixed file — asserts on its vectors are deterministic — **but gensim returns float32:
C8 casts to float64 at the load boundary (`np.asarray(vecs, dtype=np.float64)`) once, in the
same cell as the load, so all downstream arithmetic sits in the course's float64 register
(self-review amendment)**.

## Units

**C7-cnn-transfer** (prereqs [C6-pytorch]; teaches: convolution, feature-maps, receptive-field,
feature-hierarchy, resnet-architecture, bottleneck-blocks, model-truncation, layer-freezing,
transfer-learning)
- Sessions: `01-convolution-and-feature-maps` (convolution as a sliding local weighted sum —
  1-D by hand first, then 2-D, NumPy component form before `nn.Conv2d`; kernels as edge/texture
  detectors on a tiny synthetic image; feature maps as stacked channel outputs; receptive field
  growth by composition — computed by hand for 2-3 stacked convs; feature-hierarchy
  (edges → textures → parts → semantics) taught with SYNTHETIC activation statistics
  (e.g. spatial frequency/sparsity of seeded maps), NOT a reproduction of the exam's
  image-matching figure — the reasoning register (early = local/high-frequency, late =
  semantic/blobby) is the teachable), `02-resnet-reading` (resnet50 loaded once (cache pin);
  architecture reading via `named_children` — stem, layer1..4, avgpool, fc; stage output
  shapes for (B, 3, 224, 224) traced and VERIFIED in code; bottleneck block anatomy —
  1×1 reduce / 3×3 / 1×1 expand + skip; conv parameter arithmetic out·in·k·k (+ BN params
  stated as a counted-but-not-derived fact); count-without-numel register on real blocks,
  numel as the check), `03-truncation-and-transfer` (truncation via `nn.Sequential(*children)`
  slices; freezing at scale — `requires_grad=False` loops, count frozen vs trainable;
  transfer-learning as frozen-backbone + fresh head; CONSTRUCTION ONLY — the scope-note
  device extends: "training the head needs the machinery beyond this course; the exam grades
  the construction"; worked generic build with a FRESH cut point and class count (never the
  exam's layer3[4]/5-class combo)).
- **22 problems** (the v2 range is 16-24; a 9-concept unit earns the top half — self-review
  amendment). Torch + torchvision allowed; autograd/training BANNED (construction-only, incl.
  transfer heads — asserts inspect shapes/requires_grad/param counts, never fitted values).
  NOTE: 9 concepts × 3 = 27 instances vs 22 problems ⇒ **5 dual-tags ARITHMETICALLY REQUIRED** —
  flag every one in the manifest for gate judgment (008 policy); floors total 18, the 4 extra
  slots go to drills/constrained-coding at intro/core.
- Ban registers: counting problems ban `numel` (+ `sum(p.numel())` idiom, `torchsummary`,
  `state_dict` size reads) where the point is hand arithmetic; shape problems ban running the
  model where the point is tracing (verification cell separate); per-problem closers as needed.
- Determinism: all fixed-weight asserts against IMAGENET1K_V1 literals; seeded synthetic images.

**C8-embeddings** (prereqs [F2-vectors, F3-matrices, F1-scientific-python]; teaches: tokenization,
word-embeddings, embedding-matrices, similarity-matrices, nearest-neighbor-search, gensim-usage)
- NO TORCH anywhere — this unit's chain is NumPy + gensim (prereqs are foundation-track only;
  torch vocabulary stays out, same rule as C5's).
- Sessions: `01-tokens-and-embeddings` (tokenization via `gensim.utils.simple_preprocess` —
  lowercase/strip register; vocabulary filtering; the set/list dedup semantics device (order
  loss + count drop — the exam's P5-1/2 register taught generically on FRESH text); embeddings
  as learned dense vectors — "similar use → nearby vectors" stated-fact route; gensim
  KeyedVectors: load (cache pin), membership, lookup, dimensionality), `02-matrices-and-similarity`
  (stacking token vectors into an (N, 100) matrix; row-normalization WITHOUT np.linalg/loops —
  broadcasting + np.sqrt((V*V).sum(axis=1, keepdims=True)), the exam's P5-4 register; cosine
  similarity from unit rows; the similarity matrix S = W Wᵀ as a Gram matrix (F3's matrix-product
  meaning revisited); symmetry + unit diagonal verified), `03-neighbors-and-retrieval`
  (nearest-neighbor search over similarity rows — argsort descending, self-exclusion, top-k;
  **`np.argsort` is UNTAUGHT in C8's prereq chain — C8-03 teaches it inline (one gloss + one
  checkpoint exercise), and `keepdims` gets a one-line gloss at first use in C8-02 (gate
  finding, the 008 np.roll precedent);**
  manual result cross-checked against `most_similar` (gensim-usage depth); similarity pitfalls
  (frequency/hubness noted as a stated fact); a small retrieval mini-pipeline: query → tokenize →
  filter → embed → rank on FRESH seeded text).
- 20 problems, 6 concepts × 3 = 18 ⇒ 0-2 dual-tags (flag any used).
- Ban register: normalization/similarity problems ban `np.linalg`, loops (exam register),
  plus closers (`np.einsum`, `np.tensordot`, `sklearn.*`, `scipy.*`, `most_similar` where the
  point is manual construction); gensim-usage problems conversely REQUIRE the gensim API.
- Determinism: GloVe vectors fixed; all anchors computed from the pinned artifact; fresh texts
  are seeded string constants in the notebooks (committed, no runtime text downloads).

**Cross-unit pin (C8 → C9 forward compatibility):** the embedding matrix convention is ROWS =
tokens (shape (N, d)), unit-normalized stack named `W`, similarity `S = W @ W.T` — C9's SVD
unit will consume exactly this shape/naming; state it in C8-02 prose once.

**Orchestrator corpus duty:** at reconciliation, structurally compare — with explicit targets —
C7-01's hierarchy/ordering content vs p06 (no image-matching isomorph; different modality),
C7-02/03's counting/truncation/transfer problems vs p08-1..4 (fresh cut points, class counts,
block choices; no isomorph-with-renamed-numbers of the layer3[2] bottleneck count or the
layer3[4]/5-class build), and C8's full arc vs p05-1..7 (fresh texts, fresh query words, dedup
device on different content; generic-skill overlap fine). Verdict recorded in this plan.

> **CORPUS VERDICT (orchestrator, 2026-08-05): PASS — no isomorphs.**
> - C7-01 vs p06: hierarchy taught via synthetic activation statistics (act-frac/roughness on
>   seeded maps) — no image, no figure-matching; the reasoning register is the shared skill.
> - C7 p14 vs p08-3: general formula proof P(m) = 17m² + 12m (BN INCLUDED as stated fact, plus
>   a plain-alternative comparison part) vs the exam's conv-only numeric count of layer3[2];
>   anchors on layer1/layer2/layer4 blocks — never layer3. Different deliverable, scope, blocks.
> - C7 p11 vs p08-4: cut at the first six children (through layer2), 9 classes, hand-count
>   part + named-attribute contract (fresh name Transfer9) vs the exam's layer3[4]/5-class
>   build. Different cut, count, and structure. p08 vs p08-2: inspection-only 6-deliverable
>   architecture read with forward passes BANNED vs a single shape question.
> - C8 p06 vs p05-1/2: the dedup device INVERTED — sets are banned and first-occurrence order
>   must be preserved (dict.fromkeys idiom) on fresh text; teaches the exam's trap by
>   prohibition rather than reproduction. p08 vs p05-4: deliverables are row statistics +
>   centroid-of-unit-rows (register overlap only). p10 vs p05-6/7: computes S then mines
>   extremes via masked argmax/divmod — beyond the exam's express-and-compute ask; fresh words
>   throughout (drafter also scrubbed a torch-substring hazard word from candidates).

Shared: A/B/C sets; v2 floors (≥4 MC w/ ≥1 numeric normal-form — bottleneck/param-count and
similarity-range normal-forms fit; ≥6 constrained coding with exact contracts + ban clauses;
≥2 proof (C7: receptive-field growth formula + bottleneck parameter formula; C8: S = W Wᵀ
entry-wise derivation + cosine range/Cauchy-Schwarz via unit vectors); ≥2 integrative;
≥2 scenario; ≥2 challenge); every concept ≥3; ≈30/45/25; ≥2 checkpoints/section;
pitfalls/exam-connections/going-deeper unit-wide (C7 → C10 by id; C8 → C9-dimensionality-reduction
by id). SEED = 20260804 (+ torch.manual_seed in C7). C7 solution headers
torch.set_default_dtype(torch.float64) EXCEPT cells touching pretrained resnet50 (float32
weights are the artifact — compare with explicit atol=1e-6/rtol=1e-5, cast explicitly;
state this exception in the C7 drafter prompt verbatim). **Input-side pin (gate finding):
tensors fed to resnet50 are cast `.to(torch.float32)` AT THE MODEL BOUNDARY — under the
course's float64 default a float64 input to float32 weights errors or promotes; every
resnet-derived anchor is recorded from that exact float32 pipeline (never a promoted one),
and the atol=1e-6/rtol=1e-5 pair is verified EMPIRICALLY on first execution (float32 carries
~7 significant digits and resnet activations are O(10)) — widen per-problem with a comment
if a specific anchor needs it.**

## Tasks

0. Deps (torchvision via pinned index + gensim; cache-dir pattern verified; resnet50 +
   GloVe downloaded once locally to warm the cache), commit.
1. Manifests ×2 (prereq PASS + coverage RED; C7's **5** dual-tags flagged — matching the
   22-problem arithmetic above), commit.
2-3. Fable drafters ×2 (parallel): lessons + statements + review + outlines.
4. sol blind solvers ×2 (parallel, per-unit scope; warm caches locally — solvers may hit
   sandbox network denial: fall back to writing solutions against the pinned artifact
   literals and the orchestrator re-executes locally with warm cache).
5. Reconciliation (+ re-solve rule) + corpus duty.
6. Verification phase (NAMED): five checks PASS, ci-local ALL GREEN (background; NOTE:
   first-run downloads make this longer), assert scan **(explicitly verifying every
   resnet-touching cell carries the float32 boundary cast + stated atol/rtol — the
   exception must live in cells, not prose; gate finding)**, accessibility sweep (C7 torch-legal,
   C8 torch-free; gensim vocabulary C8-only), estimated_minutes.
7. Ship: content gate (self + codex 5.6-terra + opus + glm; blind-solve ≥3/unit incl ≥1 proof;
   execute-lessons duty; **network-denied reviewer sandboxes get the 008 device pre-named:
   orchestrator stages executed notebooks in a local-only `.gate9-executed/` dir**), post-exec report, TODO tick, PR, guard, squash-merge.

**RECONCILIATION (2026-08-05): 42/42 AGREE.** C7 blind solver matches the outline on all 22
(MC B/C/B/D/A; anchors incl. RF chain 11/35, freeze splits 14,999,569/8,543,296, block counts
280,064/4,462,592/6,039,552, resnet total 25,557,032). C8 matches on all 20 (MC B/C/B/D;
GloVe anchors to 8dp — p11 0.0709294514, p13 gap 1.07e-8, p18 lantern rank 18,755). Cumulative
project record 221/221. Three solver-flagged ambiguities resolved as ANSWER-PRESERVING
statement amendments codifying the solver's own stated interpretations (no re-solve triggered;
content gate judges): C7 p13 now STATES the standing assumption J≤r its proof needs (solver
identified and proved under exactly it); C8 p14 group label "strings"→"concert hall" (flute);
C8 p18(c) rephrased to the pool-vs-displayed-top-5 form. All 42 solutions re-executed locally
(sweep below).

## Out of scope

010 (F6+C9+C10), 011 mock test, 012 course map. Training/fine-tuning of any kind (construction
of transfer heads only). Image datasets/augmentation (C7 uses synthetic tensors + the pretrained
weights themselves; no HuggingFace pulls). SVD/low-rank (C9's — C8 stops at the Gram matrix).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS (amendments applied pre-gate)
1. `[FIXED-pre-gate]` C7 raised 20 → 22 problems: 7 dual-tags at 20 was the heaviest load yet;
   22 (inside the 16-24 band) brings it to 5 and funds 4 extra intro/core slots for a
   9-concept unit.
2. `[FIXED-pre-gate]` model.eval() determinism pin added — train-mode BatchNorm both consumes
   batch statistics and mutates running buffers; without the pin, forward-pass asserts are
   batch-composition-dependent.
3. `[FIXED-pre-gate]` GloVe float32 → float64 boundary-cast pin added for C8 (gensim artifacts
   are float32; the course asserts live in float64).
4. `[NOTED]` First-ci-run download cost (~230MB) accepted and documented; cache under
   gitignored reference/cache/ keeps subsequent runs warm and keeps artifacts out of the
   public repo.

### Review 2 — [fable] Independent Fable 5 (2026-08-04): APPROVE WITH NITS → all resolved
Its MAJOR (model.eval()) and NIT-4 (22 problems) raced the self-review commit — both already
in. New fixes from its round: torch.inference_mode() around all forwards (silent-graph point);
absolute repo-root cache-path recipe (relative TORCH_HOME would scatter caches per-notebook —
real bug); np.argsort taught inline in C8-03 + keepdims gloss in C8-02; .gate9-executed/
staging pre-named for network-denied gate reviewers.

### Review 3 — [glm] GLM 5.2 (2026-08-04): APPROVE WITH NITS → all resolved
Input-side float32 boundary-cast pin added (float64 default × float32 pretrained weights);
empirical tolerance verification mandated; Task 6 assert scan now names the exception cells;
Task 0 records the resolved torch↔torchvision pair + gensim ≥4.3.3.

**GATE RESULT: PASS — 4/4** (claude-self AWN pre-empted; fable AWN→resolved; glm AWN→resolved;
codex REJECT→REJECT→APPROVE clean across three rounds — final round caught the cross-constraint
recipe collision). Implementation may begin.

### Review 4b — [codex] GPT-5.6-sol re-verdict (2026-08-04): REJECT → fixed
Caught a cross-constraint collision introduced by the fable-round recipe: the combined
TORCH_HOME+GENSIM header would put torch strings into C8 notebooks, tripping C8's torch-free
sweep. Recipe split by library (C7: TORCH_HOME only; C8: GENSIM_DATA_DIR only). Second
re-verdict requested.

### Review 4 — [codex] GPT-5.6-sol (2026-08-04): REJECT → fixed
MAJOR: Task 1 still said 7 dual-tags after the 22-problem amendment (racing commit) —
corrected to 5, matching the arithmetic. MINOR: warm-cache claim qualified as a local-ci
property (no remote runner exists; the gate is ci-local.sh). Re-verdict requested.

## Content Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-05)

- **Verdict**: Approved
- Duties: all 6 lessons + 2 reviews executed clean (8/8, staged to .gate9-executed/);
  narration-vs-output verified — every narrated count in the flagged lessons appears in
  printed output (L03's 23,534,669 / 25,331,688 / 8,543,296 chain checked verbatim; two
  initially-missing anchors were practice values, not lesson claims). Independent recomputes:
  C7 p14 (17m² + 12m; m=512 → 4,462,592), p13 (stem chain 7 → 11), p04 (9/17 → 26);
  C8 p11 (Gram entrywise), p12 (Cauchy–Schwarz both bounds), p04 (24/25 → 49) — all agree
  with shipped solutions. Verification phase: five checks PASS, torch-sweep of C8 CLEAN,
  gensim-vocabulary sweep CLEAN, 42/42 asserts, float32-register presence confirmed in all
  10 weights-loading C7 solutions.

### Review 3 — [opus] Independent Opus (2026-08-05)

- **Verdict**: Changes requested → **Approved** (re-verdict 1 verified all 13 fixes but caught
  the closer-insertion corrupting p15/p16/p19 ban sentences + 2 residual rtol nits — fixed at
  `36a9b78`; final re-verdict: Approved, diff exactly the 5 intended files)
- Duties: 10/10 notebooks + 42/42 solutions executed in its own runs; ~30 narration claims
  verified; 12/12 blind-solves agree (4 proofs); p13 amendment judged SOUND (J≤r verified
  against the actual resnet chain).
1. `[FIXED]` [opus] Must Fix: C8 p14's starter code comment still read "theme 0: strings"
   beside the amended prose. → "concert hall".
2. `[FIXED]` [opus] Must Fix: C7 p18's rough spec read as dividing by 2×MAD; the reference
   computes (dx+dy)/(2·scale) where /2 averages the axes. → Statement now states the
   average-of-two-axes form with the formula inline; solution prose aligned; both re-executed.
3. `[FIXED]` [opus] Should Fix: C8 asserts left numpy's DEFAULT rtol=1e-5 in force — the
   float64 contract wasn't enforced (float32 bypass demonstrated on p05). → rtol=0 added to
   every atol-stated isclose/allclose in 13 C8 solutions (all still PASS — anchors were
   genuinely tight); the rtol-default hazard now TAUGHT in C8-02 Pitfall 4 and both review
   habit lines.
4. `[FIXED]` [opus] Should Fix: p18(c) amendment had over-corrected into giving the answer
   away. → Reworded to ask via the displayed-vs-searched distinction without the conclusion.
5. `[FIXED]` [opus] Should Fix: C8 p04 solution rationales vacuous. → Each trap traced
   (A parallel-decode 1/1, B raw-dot 24/1, C dropped cross term 12/25, E off-by-two slip).
6-13. `[FIXED]` [opus] Nits: p13 "probe you write below"; overview says span+telescoping;
   p19 literal-arithmetic wording reconciled + p15/p16/p19 echo nelement/np.prod closers;
   p10 divmod glossed; C7/C8 p03 distractors padded (length tell); C7 review's unused
   torch imports → markdown reminder; C8 manifest drops matrices-as-linear-maps.
   `[NOTED]` difficulty mix 27/50/23 within tolerance.

### Review 2 — [codex] GPT-5.6-terra (2026-08-05)

- **Verdict**: Changes requested → **Approved** (re-verdict: p13 fix verified, no remaining findings)
- Blind-solve: 6/6 agree (C7 p04/p13/p14, C8 p04/p11/p12). All other gate checks reported
  clean (manifests, torch-free C8, bans, float32 convention, construction-only, staged
  narration audit).
1. `[FIXED]` [codex] Must Fix: p13's solution still said the prompt omits the no-gap
   assumption — stale after the reconciliation amendment put the standing assumption INTO
   the statement. → Solution paragraph rewritten to invoke the statement's assumption
   (commit 8ad9b27); re-executed PASS.
