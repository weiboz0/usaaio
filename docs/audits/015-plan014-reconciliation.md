# Plan 014 reconciliation for Plan 015

## Resolution

Plan 014 is **merged**.
Its squash commit is `b486d72` (`plan 014: enrichment tranche — cross-unit retag,
error clinics, synthesis problem (#14)`), and `git merge-base --is-ancestor b486d72
HEAD` succeeds on the rebased Plan 015 branch.
Commit `5d197e5` is the follow-up documentation commit that ticks Plan 014 in
`TODO.md` and records the squash commit and PR number.

## Recomputed shipped baseline

These figures were recomputed from the canonical YAML in `syllabus.md`, every
`units/*/manifest.yaml`, and `mocktests/r1-001/manifest.yaml` after the merge.
They are not copied from Plan 014's prose.

| Measure | Shipped count |
|---|---:|
| Canonical concepts | 109 |
| Unit manifests | 16 |
| Unit practices | 343 |
| Lesson sessions | 47 |
| Unit lesson-overview, lesson-session, and review notebooks | 79 |
| Lesson minutes | 3,900 |
| Practice minutes | 7,767 |
| Review minutes | 680 |
| Total manifested minutes | 12,347 |
| Scheduled minutes including the 180-minute mock and 60-minute debrief | 12,587 |

The 79-notebook subtotal is 16 unit `lesson.ipynb` overviews, 47 files under
`units/*/lessons/`, and 16 unit `review.ipynb` files.
The manifested total is `3,900 + 7,767 + 680 = 12,347` minutes.
The scheduled total is `12,347 + 180 + 60 = 12,587` minutes.

## Overlapping-topic dispositions

- Plan 014 shipped no top-level `synthesis/` tree.
  It shipped six new in-unit problems: F6-p25, C3-p19, C7-p27, C9-p19, C1-p24,
  and F5-p19.
  F6-p25 is the one purpose-built cross-unit synthesis problem; the retagged
  existing practices and these six problems are complementary evidence for the
  Plan 015 audit, not automatic coverage findings.
- Plan 014 shipped a BatchNorm subsection in C7's ResNet lesson and the C7-p27
  train/eval/freeze/inference clinic.
  This is partial evidence only: the shipped syllabus has no
  `batch-normalization` concept owner and no three honestly tagged unit
  practices for that concept.
  The later Round 1 neural-training tranche still owns the standalone concept,
  teaching, and practice completion.
- Plan 014 did not ship `softmax` or `cross-entropy-loss`.
  Both remain assigned to the later Round 1 neural-training tranche together
  with manual forward/backward propagation and complete network training.
- Plan 014's historical `future-risk` language does not decide Plan 015 source
  status.
  Bayes' rule, attention, KL divergence, mixture modeling, and related families
  receive their official, bridge, or observed status from the dated sources and
  preliminary decisions in Plan 015.
- Plan prose is not shipped-content evidence.
  Only committed teaching, practice, assessment, manifest, and generated audit
  anchors may support later coverage judgments.
