# Plan 008 — Teaching Units Tranche 4: C5 + C6 (neural networks + PyTorch)

> **For agentic workers:** the proven 006/007 cycle verbatim (per-task commits; Fable
> drafts lessons + statements, outlines to `reference/outlines-008/<unit>.md` (gitignored);
> gpt-5.6-sol blind-solves per unit; reconciliation before the gate; amended statements →
> blind re-solve; proofs carry numeric anchors + claim-by-claim rubric; ban-register
> contract = core set as minimum + workaround-closers; lesson narration MUST match printed
> output — three prior gate catches).

**Goal:** Ship `C5-neural-networks` and `C6-pytorch` at the v2 bar.

## Deps (Task 0)

`uv add torch --index https://download.pytorch.org/whl/cpu` (CPU wheel — no GPU assumptions; C6 teaches torch). If the index flag fails under uv, use the `tool.uv.sources`/`extra-index-url` route and record which. Verify `python -c "import torch"` and pin the version in the post-exec report.

## Units

**C5-neural-networks** (prereqs [C3-gradient-descent, F5-probability]; teaches: perceptron, activation-functions, threshold-activation, relu-activation, mlp-architecture, decision-boundaries-geometric, weight-init-variance)
- Sessions: `01-perceptrons-and-activations` (the perceptron as weighted-sum-then-threshold; threshold/step, tanh recap by reference to F4, ReLU; why nonlinearity matters — a stack of linear maps is linear, worked), `02-mlps-and-geometry` (MLP as function composition; hidden units as half-plane detectors; hand-built decision regions from intersections — the exam's triangle-membership pattern taught GENERICALLY with fresh regions (polygon-membership by half-plane AND-ing); forward pass by hand + NumPy), `03-initialization-and-variance` (the F5 weighted-sum variance identity applied to layer pre-activations; the 1/√C scaling derivation — the exam's init pattern, taught from the F5 stated-fact route; seeded simulation verification).
- 18–20 problems, NumPy-only (torch is C6's): forward passes, region design, variance derivations + simulations. NO torch, NO training of MLPs (descent on MLPs is beyond scope — C3 trained linear models only; C5 practice designs weights BY HAND per the exam's inference-only pattern).
- Accessibility: owns perceptron/activation/MLP vocabulary; may use C3's descent + F5's variance freely.

**C6-pytorch** (prereqs [C5-neural-networks]; teaches: python-inheritance, torch-tensors, nn-module, custom-layers, manual-weights, requires-grad, parameter-counting)
- Sessions: `01-tensors-and-inheritance` (torch tensors mirroring F1 NumPy — bridge table; python-inheritance + super() taught explicitly (the syllabus id lives HERE); shapes/dtypes/devices-lite (CPU only)), `02-nn-module-and-custom-layers` (nn.Module subclassing; forward(); building the C5 threshold + linear layers as custom modules — the exam's My_Threshold/My_Linear pattern taught generically with fresh module specs; composing an inference-only MLP with MANUAL weights; requires_grad=False discipline), `03-parameter-counting-and-inspection` (parameters(); counting by hand vs numel; the exam's count-without-numel reasoning register; state_dict inspection; worked normal-form MC on parameter counts).
- 18–20 problems. Torch allowed (that's the point); autograd/training BANNED (inference-only, matching the exam's pattern and C5's scope; optimizer/backward vocabulary forbidden — C-track ends at inference engineering; note in Exam Connections that the real paper's torch problems are inference-only too, paraphrase).
- Conventions: SEED for torch = `torch.manual_seed(20260804)` alongside the NumPy seed where both used.

**C5/C6 shared module-spec pin (both drafter prompts verbatim, the 007-notation-pin lesson):** the hand-built layers are `step_layer(x, W, b)` (NumPy, C5) ↦ `MyThreshold(nn.Module)` / `MyLinear(nn.Module)` (C6) with EXACT semantics: MyLinear stores `weight` (out×in) and `bias` (out,), forward = `x @ weight.T + bias`; MyThreshold forward = `(x >= 0).to(x.dtype)`; C6's lesson builds THESE from C5's NumPy versions by name. Fresh module names (My-prefix but NOT the real paper's exact identifiers where they differ — check the corpus at reconciliation).

**Orchestrator corpus duty (carried from F3/007 precedent):** at reconciliation, structurally compare C5's region-design problems and C6's custom-module/count problems against the local index's P7/P8 sub-parts — generic-skill overlap fine; no isomorph-with-renamed-numbers. Verdict recorded in this plan.

**Float32 note (both prompts):** torch defaults to float32 — assert tolerances in C6 solutions use 1e-5-scale (not 1e-9); cross NumPy/torch comparisons cast explicitly.

Shared: A/B/C sets; v2 floors (≥4 MC w/ ≥1 numeric normal-form — parameter-count normal-forms fit naturally; ≥6 constrained coding with exact contracts + ban clauses (e.g. "no numel" mirrors the exam); ≥2 proof (C5: linear-stack-is-linear; variance derivation; C6: parameter-count formula derivations); ≥2 integrative; ≥2 scenario; ≥2 challenge); every concept ≥3; ≈30/45/25; ≥2 checkpoints/section; pitfalls/exam-connections/going-deeper unit-wide (C5 → C6/C7 by id; C6 → C7-cnn-transfer by id).

## Tasks

0. Deps (torch CPU), commit. 1. Manifests ×2 (prereq PASS + coverage RED), commit.
2-3. Fable drafters ×2 (parallel): lessons + statements + review + outlines.
4. sol blind solvers ×2 (parallel, per-unit scope; torch available locally for C6 verification — sandbox fallback to sequential execution acceptable, orchestrator re-executes locally).
5. Reconciliation (+ re-solve rule).
6. Verification phase (NAMED): five checks PASS, ci-local ALL GREEN (NOTE: run with extended timeout — suite now >10 min), assert scan, accessibility sweep (C5/C6 allowlists; "neural" legal in C5+, torch vocabulary C6-only), estimated_minutes.
7. Ship: content gate (self + codex 5.6-terra + opus + glm; blind-solve ≥3/unit incl ≥1 proof; execute-lessons duty), post-exec report, TODO tick, PR, guard, squash-merge.

## Out of scope

009 (C7+C8, torchvision/gensim), 010 (F6+C9+C10), 011 mock test, 012 course map. Training/autograd (never taught in this curriculum — the exam is inference-only for torch).

## Plan Review

### Review 1 — [claude-self] Claude Fable 5, inline (2026-08-04)

- **Verdict**: APPROVE WITH NITS
1. `[FIXED-pre-gate]` Added the C5/C6 module-spec pin (the 007 notation-pin lesson
   applied to concurrent drafting), the orchestrator corpus structural-comparison duty
   (F3 precedent), and the float32 tolerance note.
2. `[NOTED]` Inference-only scope is the deliberate design: the syllabus never teaches
   MLP training, C3's descent covers linear models only, and the real exam's torch
   problems are inference-only — C5 needs an explicit scope-note device in its lesson
   ("why we design weights by hand here"), flagged for the drafter prompt.
3. `[NOTED]` torch CPU via uv index — fallback route named in Task 0.

## Content Review

(Pre-PR gate findings land here.)
