# r2-001 — Scoring Rubric (per-part partial credit)

Multiple-choice parts are all or nothing.
Programming parts are graded by re-executing the notebook top to bottom in a fresh kernel (`SEED = 20261101`, CPU); a part that uses a banned API scores 0.
"Tolerance" is an absolute tolerance on the printed answer.

## Problem 1 (Day 1, d1-arc, 90 points)

- **r2-001-p01-1** (5, MC): 5 for **B** ($11/24$, so $35$); 0 otherwise.
- **r2-001-p01-2** (5, short answer): 5 for exactly $73728$ ($2Bn^2d=2\cdot8\cdot144\cdot32$); 0 otherwise.
- **r2-001-p01-3** (5, MC): 5 for **C** ($65$); 0 otherwise.
- **r2-001-p01-4** (10, proof):
  - 3 points: (a) MHA has $4(d^2+d)=4d^2+4d$ parameters, with the argument that the head split is a reshape of the full-width projections (each of $W_Q,W_K,W_V,W_O$ is one $d\times d$ map plus bias regardless of $h$; equivalently $h$ heads of $d\times d_h$ blocks total $h\cdot d\cdot d/h=d^2$), so $h$ cancels.
  - 3 points: (b) $P_{\text{block}}=4d^2+2d\,d_{ff}+9d+d_{ff}$, itemised: two LayerNorms $2\cdot2d$, MHA $4d^2+4d$, feed-forward $d\,d_{ff}+d_{ff}+d_{ff}d+d$.
  - 2 points: (c) $8544$.
  - 2 points: refutation: more heads means narrower heads ($d_h=d/h$), not more or larger matrices; the attention parameter count stays $4d^2+4d$.
- **r2-001-p01-5** (5, short answer): 5 for exactly $18712$ ($768+2\cdot8544+64+792$); 0 otherwise.
- **r2-001-p01-6** (5, MC): 5 for **D** ($a=200$); 0 otherwise.
- **r2-001-p01-7** (10, proof):
  - 4 points: (a) pairs coordinates $2i,2i+1$ and applies $\sin A\sin B+\cos A\cos B=\cos(A-B)$ with $A=p\omega_i$, $B=q\omega_i$, then sums over $i$; states the dependence on $p-q$ only.
  - 3 points: (b) $\lVert\mathrm{PE}[p]\rVert^2=d/2$ (from $\cos0=1$ or $\sin^2+\cos^2=1$) and $\lVert\mathrm{PE}[p]-\mathrm{PE}[q]\rVert^2=d-2\sum_i\cos((p-q)\omega_i)$.
  - 3 points: (c) $\cos 4+\cos(1/25)$ (since $\omega_0=1$, $\omega_1=1/100$, offset $4$), $\approx0.3456$; 2 of the 3 for the closed form with an arithmetic slip in the decimal.
- **r2-001-p01-8** (5, MC): 5 for **A**; 0 otherwise.
- **r2-001-p01-9** (5, MC): 5 for **D** ($24$); 0 otherwise.
- **r2-001-p01-10** (5, short answer): 5 for exactly $2^{7/4}$ (four scored positions, mean cross-entropy $\frac74\ln2$); 0 otherwise.
- **r2-001-p01-11** (5, code):
  - 2 points: `causal_mask` returns `torch.bool` `(n, n)` lower-triangular with the diagonal allowed.
  - 2 points: `masked_softmax` masks with $-\infty$ **before** the softmax over the last axis (post-softmax zeroing earns 0 of these 2), raises `ValueError` on an all-forbidden row.
  - 1 point: required assertions present and passing, including the bit-for-bit forbidden-score check; answer `2.333333` ($7/3$, tolerance `1e-6`).
- **r2-001-p01-12** (10, code):
  - 3 points: four `nn.Linear(32, 32)` projections created in the stated order, no other parameters, `ValueError` on `d_model % n_heads != 0`; `n_params == 4224`.
  - 3 points: correct head split/merge (`view(B, n, h, d_h).transpose(1, 2)` and its inverse), `1/sqrt(d_h)` scaling, Part 1.11 mask before softmax, `o_proj` after the merge.
  - 2 points: future-perturbation certificate: positions 0–6 bit-for-bit unchanged, positions 7–11 changed.
  - 2 points: `probe_value = 0.167092` (tolerance `1e-4`); 0 of these 2 if the probe was built with a different seed or construction order.
- **r2-001-p01-13** (10, code):
  - 2 points: `sinusoidal_table` (sine on even, cosine on odd coordinates, $\omega_i=10000^{-2i/d}$; `pe[0]` checks) and `shift_for_causal_lm`.
  - 3 points: `TinyCausalLM` to specification (stated construction order, pre-norm blocks, `pe` a buffer, final LayerNorm and head); trainable parameter count `18712` equals the Part 1.5 answer.
  - 3 points: training protocol exactly as stated (seed, Adam settings, 150 full-batch updates in the stated order, shifted targets) with `losses[-1] < 0.25 * losses[0]`; validation perplexity before and after, computed under `eval()` and `no_grad()`.
  - 2 points: `val_ppl_after = 1.132` (tolerance `0.03`) with `1.05 < val_ppl_after < 1.20`, position 0 the largest per-position perplexity, and an explanation that position 0 sees only $t_0$ and cannot know the step $k$ (three equally likely next tokens, the rule-aware floor of Part 1.14(a)), while later positions can read the step from two tokens.
    Small platform-dependent variation in the third decimal (for example `1.130` or `1.128` from different CPU kernels or thread counts) is covered by the stated tolerance and earns these points.
  - A value at or below `1.05` (a leak: missing mask or unshifted targets) earns at most 3 of the 10 points.
- **r2-001-p01-14** (5, proof):
  - 1 point: (a) $3^{1/12}$ (mean cross-entropy $\ln3/12$; $\approx1.0959$).
  - 2 points: (b) induction: the embedding plus position at output position $i$ uses only token $i$; LayerNorm, the feed-forward sublayer, residual additions, final LayerNorm, and the head are per-position; masked attention at position $i$ combines only value rows $j\le i$ with weights computed from scores $j\le i$ (forbidden scores are $-\infty$ before the softmax, so they do not enter the normalisation), so if every position $\le i$ of the block input is unchanged, every position $\le i$ of the block output is unchanged.
  - 2 points: (c) any two of: the causal mask omitted (position 0 can attend to input position 1, which is $t_1$, its own target); targets not shifted, `targets = inputs` (position 0's target is $t_0$, which it sees directly); a mask reversed or applied with the wrong orientation so that keys $j>i$ are allowed (position 0 sees $t_1,\dots,t_{11}$).
    One point per correctly explained error; any other error is accepted only if it lets the logits at output position 0 depend on $t_1$ (or a later token) or makes $t_0$ its own target.

## Problem 2 (Day 1, d1-open, 70 points)

- **r2-001-p02** (70, open-ended): see "Open-ended grading" below.
  Metric: mean permutation-invariant source-position error (lower is better).
  **B = 0.04810, R = 0.001541, g = 0.04656.**
  Test-score portion (42 points): **42** if score `<= 0.01318`; **25.2** if `< 0.04810`; **10.5** if `< 0.05974`; **0** otherwise.
  Writeup portion: 28 points (7 per part).

## Problem 3 (Day 2, d2-arc, 50 points)

- **r2-001-p03-1** (5, MC): 5 for **B** ($2-\ln2$); 0 otherwise.
- **r2-001-p03-2** (5, short answer): 5 for exactly $\frac{35}{16}-\frac12\ln2$ (recon mean $9/16$, KL mean $\frac{13}{16}-\frac14\ln2$); 0 otherwise.
  A value of $\frac{9}{8}+\frac{13}{16}-\frac14\ln 2$ (β applied to reconstruction) earns 0.
- **r2-001-p03-3** (10, proof):
  - 2 points: (a) $E[(x-z)^2]=\operatorname{Var}(z)+(E[z]-x)^2=s+(x-\mu)^2$, by expanding $(x-\mu-(z-\mu))^2$ and using $E[z-\mu]=0$.
  - 4 points: (b) $\partial J/\partial\mu=-(x-\mu)+\beta\mu=0\Rightarrow\mu^*=x/(1+\beta)$; $\partial J/\partial s=\tfrac12+\tfrac\beta2(1-1/s)=0\Rightarrow s^*=\beta/(1+\beta)$; global minimality argued (e.g. $J$ separates into a strictly convex quadratic in $\mu$ plus a strictly convex function of $s$ on $s>0$, or second-derivative and boundary behaviour).
  - 4 points: (c) $\mu^*=1$, $s^*=2/3$ (1 point each), $J^*=3+\ln\frac32$ (2 points).
- **r2-001-p03-4** (5, MC): 5 for **B** ($(2,\tfrac13)$); 0 otherwise.
- **r2-001-p03-5** (5, code):
  - 2 points: `kl_to_standard_normal` sums over latents, returns `(B,)`, matches Part 3.1 for row 0.
  - 2 points: `reparameterize` uses `exp(0.5 * logvar)` (not `exp(logvar)`), takes `eps` as an argument, gradient assertions pass.
  - 1 point: answer `0.568147` ($\ln2-\frac18$, tolerance `1e-6`).
- **r2-001-p03-6** (5, code):
  - 3 points: sum over features in the reconstruction, sum over latents in the KL, mean over the batch, β on the KL only (β on the reconstruction earns 0 of these 3).
  - 2 points: assertions present and passing; answer `1.840926` (tolerance `1e-6`), equal to the Part 3.2 value.
- **r2-001-p03-7** (10, code):
  - 3 points: `TinyVAE` to specification (layer order, ReLU placement, `eps` argument).
  - 3 points: protocol exactly as stated (seeding, the two generators, 400 updates in the stated order, held-out rows never in `backward()`), with the per-update identity `total == recon + 2 * kl` asserted.
  - 2 points: certificates: window mean below first total; held-out after `<= 0.8 *` before; gradient-flow probe on the reconstruction term.
  - 2 points: held-out β-weighted objective after training `2.732` (tolerance `0.05`), reported as a β-weighted objective and not as an ELBO.
- **r2-001-p03-8** (5, code):
  - 2 points: per-latent held-out KL computed from posterior means and log-variances (no noise), averaged over rows.
  - 1 point: the β = 8 rerun follows the Part 3.7 protocol.
  - 1 point: answer `1, 0`.
  - 1 point: (c) names posterior collapse (all latents match the prior) and cites a log quantity such as the KL term near 0 or the reconstruction term stuck near the mean-prediction level.

## Problem 4 (Day 2, d2-open, 40 points)

- **r2-001-p04** (40, open-ended): see "Open-ended grading" below.
  Metric: accuracy on the locked test patches (higher is better).
  **B = 0.4850, R = 0.9900, g = 0.5050.**
  Test-score portion (24 points): **24** if accuracy `>= 0.8638`; **14.4** if `> 0.4850`; **6** if `> 0.3588`; **0** otherwise.
  Writeup portion: 16 points (4 per part).

## Problem 5 (Day 2, d2-open, 50 points)

- **r2-001-p05** (50, open-ended): see "Open-ended grading" below.
  Metric: mean permutation-invariant parameter error (lower is better).
  **B = 0.01711, R = 0.005272, g = 0.01184.**
  Test-score portion (30 points): **30** if score `<= 0.008231`; **18** if `< 0.01711`; **7.5** if `< 0.02007`; **0** otherwise.
  Writeup portion: 20 points (5 per part).

## Open-ended grading (Problems 2, 4, 5)

**Test score (60%).** The grader re-executes the notebook on a CPU under `SEED = 20261101` and reads the `.score` point estimate of the single `final_test_score` call.
With B the committed baseline score, R the reference score, and `g = |B - R|`:

| direction | 100% | 60% | 25% | 0% |
|---|---|---|---|---|
| lower is better (P2, P5) | score `<= R + 0.25 g` | score `< B` | score `< B + 0.25 g` | otherwise |
| higher is better (P4) | score `>= R - 0.25 g` | score `> B` | score `> B - 0.25 g` | otherwise |

The test-score portion is **0** for any protocol violation: `final_test_score` called more than once (or the call-count assertions missing or failing); a seam value of `"val"` or `"test"` (P2/P5), or anything other than `"train"`/`"unlabelled"` (P4); an unwrapped optimizer or more optimizer steps than the budget (P2: 3,000; P4: 1,500; P5: 2,000); `budget.elapsed() >= 60` s after the test call; fitting on validation rows (including statistics such as a mean image computed from them), using pool labels, statistics computed across the test batch inside `predict`, or calling `simulate` in P4; using the data generator to recover hidden scanner or generation parameters, or any held-back labels; banned tools (web, downloads, external data, pretrained weights); a notebook that does not run top to bottom.

**Writeup (40%, four equal parts).** Each part is scored on this scale (fractions of that part's points):

- **Approach.** Full: the method, its inputs and preprocessing, and its key settings are stated reproducibly, with a reason tied to this problem (for example the known forward model, the label scarcity, or the peak shape). Half: the method is named but settings or reasons are missing. Zero: missing or inconsistent with the code.
- **Alternatives considered.** Full: at least two alternatives, each with a validation number (or a precise, checked reason) that ruled it out, compared fairly (same data roles and budget). Half: one alternative with evidence, or two without numbers. Zero: none.
- **Evaluation.** Full: the data roles and seeds; the single final test score with its 95% bootstrap interval and `n`; the baseline under the same protocol; at least one validation comparison that justified the final choice. Half: the test score without the interval or without the baseline comparison. Zero: no test score, or numbers that do not appear in the notebook's outputs.
- **Limitations.** Full: at least one concrete failure mode (for example sources close together or near the boundary, a class whose pseudo-labels drift, overlapping or very narrow peaks) and a specific test that would measure it. Half: a generic limitation without a test. Zero: missing.

**Reference approaches (for graders; not the only acceptable methods).**
The published reference solutions (`solutions/p02_solution.ipynb`, `p04_solution.ipynb`, `p05_solution.ipynb`) define R; their `final_test_score` point estimates are the R values above.
P2: a learned inverse (MLP on the 800 training rows plus 20,000 rows from `simulate`, 1,000 steps) gives each row a start, then 300 steps of per-row least squares refine it through the forward model (learning rate 0.01 chosen on validation; 2,200 optimizer steps; validation error 0.00264).
P4: scanner B's fixed per-pixel offset estimated from the pool mean image and removed patch by patch, then closed-form texture features (pixel moments, spectral peakiness, radial power bands, neighbour correlations) with a logistic head, plus three rounds of confidence-thresholded self-training on the corrected pool (1,050 steps; validation accuracy 1.000).
P5: two starts per signal, a learned amortized regressor and a greedy peak picker, each refined by 200 least-squares steps (learning rate 0.02 chosen on validation), keeping the fit with the smaller residual (1,900 steps; validation error 0.00504).
Weaker approaches calibrated by the author also beat B: for P2, an MLP start plus 200 refinement steps (validation error 0.0041); for P4, the labelled-only head applied with per-scanner feature standardization from pool statistics (validation accuracy 0.825, test 0.9250; full credit), while every labelled-only probe stays in the 60% tier (closed-form features + logistic head 0.6250 on test, CNN with flip/rotation augmentation 0.6475); for P5, a peak-picking start plus the baseline start (validation error 0.0060).