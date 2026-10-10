# r2-001 — Canonical Answer Key and Worked Solutions

## Answer key

One marker per manifest entry; `answerkey-check` compares each with the manifest `answer_key`.
Programming values are reproduced by the tagged `answer:<id>` cells in `pNN_solution.ipynb`.
Open-ended entries carry the scoring marker `metric; direction; B; R; tiers` (4 significant digits): R is the reference solution's `final_test_score` below, and the cutoffs are `R ± 0.25g`, `B`, `B ± 0.25g` with `g = |B - R|`.

- r2-001-p01-1: answer: B
- r2-001-p01-2: answer: 73728
- r2-001-p01-3: answer: C
- r2-001-p01-4: answer: 8544
- r2-001-p01-5: answer: 18712
- r2-001-p01-6: answer: D
- r2-001-p01-7: answer: cos(4) + cos(1/25) ≈ 0.3456
- r2-001-p01-8: answer: A
- r2-001-p01-9: answer: D
- r2-001-p01-10: answer: 2^(7/4)
- r2-001-p01-11: answer: 2.333333
- r2-001-p01-12: answer: 0.167092
- r2-001-p01-13: answer: 1.132
- r2-001-p01-14: answer: 3^(1/12) ≈ 1.0959
- r2-001-p02: answer: metric=position_error; direction=lower; B=0.04810; R=0.001541; tiers=0.01318,0.04810,0.05974
- r2-001-p03-1: answer: B
- r2-001-p03-2: answer: 35/16 - (1/2) ln 2
- r2-001-p03-3: answer: mu* = 1, s* = 2/3, J* = 3 + ln(3/2)
- r2-001-p03-4: answer: B
- r2-001-p03-5: answer: 0.568147
- r2-001-p03-6: answer: 1.840926
- r2-001-p03-7: answer: 2.732
- r2-001-p03-8: answer: 1, 0
- r2-001-p04: answer: metric=accuracy; direction=higher; B=0.4850; R=0.9900; tiers=0.8638,0.4850,0.3588
- r2-001-p05: answer: metric=parameter_error; direction=lower; B=0.01711; R=0.005272; tiers=0.008231,0.01711,0.02007

Blind solve from the student-facing bundle only (`test.md`, `theory/*.md`, `problems/*.ipynb`, `data/`).
Programming values are the ones printed by `pNN_solution.ipynb` when run from `r2-001/solutions/` (they locate `../data`).

## Problem 1. A tiny causal language model

### Part 1.1 — answer: **B** ($p+q=35$)

The mask allows $(i,j)$ iff $j\le i$, so row $i$ forbids the $n-1-i$ entries with $j>i$.
Forbidden total $=\sum_{i=0}^{n-1}(n-1-i)=n(n-1)/2=66$ for $n=12$.
Fraction $66/144=11/24$, so $p+q=11+24=35$.

### Part 1.2 — answer: **73728**

Per head, $Q_rK_r^\top$ is $(n\times d_h)(d_h\times n)$ per batch row: $n\cdot d_h\cdot n=12\cdot8\cdot12=1152$ multiply-adds; $A_rV_r$ is $(n\times n)(n\times d_h)$: $n\cdot n\cdot d_h=1152$.
Per head and row $2304$; times $h=4$ heads and $B=8$ rows: $2304\cdot32=73728$.
(General form: $2Bn^2d_h h=2Bn^2d$.)

### Part 1.3 — answer: **C** ($n=65$)

Projections: four $(Bn\times d)(d\times d)$ products, $4Bnd^2=4096\,Bn$.
Attention products: $2Bn^2d=64\,Bn^2$.
$64Bn^2>4096Bn\iff n>64$, so the smallest integer is $65$ (at $n=64$ they are equal, not strictly more).

### Part 1.4 — answers: (a) $4d^2+4d$, independent of $h$; (b) $P_{\text{block}}=4d^2+2d\,d_{ff}+9d+d_{ff}$; (c) $8544$

(a) MHA has exactly four learned maps $W_Q,W_K,W_V,W_O\in\mathbb R^{d\times d}$, each with a bias in $\mathbb R^d$: $4(d^2+d)=4d^2+4d$ parameters.
Heads are not separate parameters: head $r$ uses the column slice $rd_h,\dots,(r+1)d_h-1$ of the same $Q,K,V$, and the concatenation is mapped by the single $W_O$.
Changing $h$ (with $h\mid d$) only changes how the $d$ columns are partitioned into $h$ blocks of width $d/h$; the matrix shapes $d\times d$ and bias lengths $d$ never involve $h$, so the count $4d^2+4d$ does not depend on $h$.

(b) Two LayerNorms: $2\cdot 2d=4d$ (scale and shift each of length $d$).
Feed-forward: $W_1,b_1$: $d\,d_{ff}+d_{ff}$; $W_2,b_2$: $d_{ff}d+d$.
Total $P_{\text{block}}=4d+(4d^2+4d)+(2d\,d_{ff}+d_{ff}+d)=4d^2+2d\,d_{ff}+9d+d_{ff}$.

(c) $d=32,d_{ff}=64$: $4096+4096+288+64=8544$.

**Classmate's error.** Going from 4 to 8 heads at fixed $d$ does not create more query/key/value matrices: there is still one $d\times d$ matrix each for $Q,K,V$ (and $O$); 8 heads just cut the same $d=32$ columns into 8 slices of width 4 instead of 4 slices of width 8.
By (a) the attention parameter count is $4d^2+4d=4224$ for both, so it does not double — it is unchanged.
(Only the per-head width $d_h=d/h$ halves.)

### Part 1.5 — answer: **18712**

Token embedding $24\cdot32=768$; two blocks $2\cdot8544=17088$; final LayerNorm $2\cdot32=64$; head $32\cdot24+24=792$.
Total $768+17088+64+792=18712$ (the sinusoidal table is a buffer, not counted).

### Part 1.6 — answer: **D** ($a=200$)

$\omega_8=10000^{-16/32}=10000^{-1/2}=1/100$.
$(\sin(p/100),\cos(p/100))$ has least period $2\pi/\omega_8=200\pi$, so $a=200$.

### Part 1.7 — answers: (a) proof; (b) $\lVert\mathrm{PE}[p]\rVert^2=d/2$, $\lVert\mathrm{PE}[p]-\mathrm{PE}[q]\rVert^2=d-2\sum_i\cos((p-q)\omega_i)=4\sum_i\sin^2\!\big(\tfrac{(p-q)\omega_i}{2}\big)$; (c) $\cos 4+\cos\frac1{25}\approx0.3456$

(a) Group coordinates in pairs $(2i,2i+1)$:
$$\langle\mathrm{PE}[p],\mathrm{PE}[q]\rangle=\sum_{i=0}^{d/2-1}\big[\sin(p\omega_i)\sin(q\omega_i)+\cos(p\omega_i)\cos(q\omega_i)\big]=\sum_{i=0}^{d/2-1}\cos\big((p-q)\omega_i\big),$$
by $\cos(A-B)=\cos A\cos B+\sin A\sin B$.
The right side involves $p,q$ only through $p-q$.

(b) Put $q=p$: $\lVert\mathrm{PE}[p]\rVert^2=\sum_{i=0}^{d/2-1}\cos0=d/2$ for every $p$.
Then $\lVert\mathrm{PE}[p]-\mathrm{PE}[q]\rVert^2=\lVert\mathrm{PE}[p]\rVert^2+\lVert\mathrm{PE}[q]\rVert^2-2\langle\mathrm{PE}[p],\mathrm{PE}[q]\rangle=d-2\sum_{i}\cos((p-q)\omega_i)=\sum_i 2(1-\cos((p-q)\omega_i))=4\sum_i\sin^2\!\big((p-q)\omega_i/2\big)$, a function of $p-q$ only.

(c) $d=4$: $\omega_0=1$, $\omega_1=10000^{-2/4}=1/100$; offset $p-q=4$:
$\langle\mathrm{PE}[7],\mathrm{PE}[3]\rangle=\cos4+\cos(4/100)=\cos 4+\cos\frac{1}{25}\approx-0.653644+0.999200=0.3456$ (more precisely $0.345556$).

### Part 1.8 — answer: **A**

Output position $i$ reads input $t_i$ and is scored against target $t_{i+1}$ (`targets = tokens[:, 1:]`); with the causal mask its logits depend only on inputs at positions $\le i$, i.e. $t_0,\dots,t_i$.

### Part 1.9 — answer: **D** ($24$)

Equal logits give $p=1/24$ for every target, so mean cross-entropy is $\ln24$ and $\mathrm{PPL}=e^{\ln24}=24$.

### Part 1.10 — answer: $2^{7/4}$ ($a=7$, $b=4$)

Scored positions: row 1 positions 0–2 and row 2 position 0, so $N=4$.
$-\sum\ln p=\ln2+\ln4+\ln8+\ln2=(1+2+3+1)\ln2=7\ln2$.
$\mathrm{PPL}=\exp(7\ln2/4)=2^{7/4}$.

### Part 1.11 (programming) — answer: **2.333333**

`masked_softmax(S, causal_mask(4))[2]` has weights $\propto(1,2,3)$, so $\mathrm{out}[2]=(1+4+9)/6=7/3$; printed `2.333333`.
(Generally $\mathrm{out}[i]=(2i+3)/3$: `[1, 5/3, 7/3, 3]`.)

### Part 1.12 (programming) — answer: **probe_value = 0.167092**

`n_params = 4224` matches 1.4(a) at $d=32$; positions 0–6 are bit-for-bit unchanged by perturbing positions 7–11.

### Part 1.13 (programming) — answer: **val_ppl_after = 1.132** (tolerance 0.03)

The key is `1.132`.
The last digit depends on the CPU kernels and thread count: a run of `p01_solution.ipynb` in this repository's CI environment (AVX2 kernels, one thread) prints `val_ppl_after = 1.130` (unrounded 1.13023), and the same code with other kernel or thread settings prints values from 1.128 to 1.131; all lie well inside the stated tolerance of 0.03, so any of them earns full credit.
From that CI run: `val_ppl_before = 27.188`; losses $3.3136\to0.0838$; trainable parameters $18712$; per-position validation PPL `[4.277, 1.007, 1.003, 1.001, 1.001, 1.001, 1.001, 1.001, 1.001, 1.001, 1.001, 1.001]` (position 0 largest).
Explanation: at position 0 only $t_0$ is visible and $k$ is independent of $t_0$, so no predictor can beat probability $1/3$ there, while from position 1 on the next token is determined.

### Part 1.14 — answers: (a) $3^{1/12}\approx1.0959$; (b) proof; (c) two errors

(a) A complete row has 12 scored positions.
Position 0: the true $t_1=(t_0+k)\bmod24$ with $k\in\{1,2,3\}$ is one of the three tokens given $1/3$, so $-\ln p=\ln3$.
Positions $i\ge1$: $t_i-t_{i-1}\equiv k$, so $2t_i-t_{i-1}\equiv t_i+k\equiv t_{i+1}\pmod{24}$ and $p=1$, $-\ln p=0$.
Per row the mean cross-entropy is $\ln3/12$, the same for every row, so on any set of complete rows $\mathrm{PPL}=\exp(\ln3/12)=3^{1/12}\approx1.0959$.

(b) Let $h^{(0)}_j=\mathrm{Emb}(t_j)+\mathrm{PE}[j]$ and $h^{(\ell)}$ the output of block $\ell$.
Claim $C(\ell)$: for every $i$, $h^{(\ell)}_i$ is a function of $t_0,\dots,t_i$ only.
*Base* $\ell=0$: $h^{(0)}_i$ depends only on $t_i$.
*Step*: assume $C(\ell)$.
In block $\ell+1$, $u_j=\mathrm{LN}_1(h^{(\ell)}_j)$ acts per position, so $u_j$ depends on $t_0..t_j$; hence so do $Q_j,K_j,V_j$ (per-position affine maps).
In each head, row $i$ of the scores has entries $j>i$ replaced by $-\infty$ before softmax, so $A_r[i,j]=0$ exactly for $j>i$, and the softmax over row $i$ uses only $S_r[i,j]$ for $j\le i$, which depend on $Q_i$ and $K_j$ ($j\le i$), i.e. on $t_0..t_i$.
Thus $H_r[i]=\sum_{j\le i}A_r[i,j]V_r[j]$ depends only on $t_0..t_i$; the concatenation and $W_O$ act per position, so $\mathrm{MHA}(u)_i$ does too, and $y_i=h^{(\ell)}_i+\mathrm{MHA}(u)_i$ does.
$\mathrm{LN}_2$ and the feed-forward sublayer act per position, so $z_i=h^{(\ell+1)}_i$ depends only on $t_0..t_i$: $C(\ell+1)$ holds.
After $L=2$ blocks, the final LayerNorm and the vocabulary head act per position, so the logits at position $i$ are functions of $t_0,\dots,t_i$ and do not change when any of $t_{i+1},\dots,t_{11}$ change.

(c) By (a) and the independence of $k$ from $t_0$, no causal model can get below $3^{1/12}\approx1.096$ on average (position 0 is irreducibly uncertain), so $1.001$ means the model sees the answer:
1. *Missing or broken causal mask* (no mask, mask transposed to allow $j\ge i$, or mask applied after the softmax so forbidden weights are not zeroed/renormalized): the logits at position 0 can see future inputs, in particular $t_1$ — the very token they are scored on — so position 0 becomes trivial.
2. *Wrong shift: targets not shifted* (e.g. `targets = tokens[:, :-1]`, the same as the inputs, or inputs taken as `tokens[:, 1:]`): the model is scored on predicting the token it is reading; the logits at position 0 see only $t_0$ (its own input), which is then the target, so copying gives near-zero loss.

## Problem 3. A β-weighted VAE

### Part 3.1 — answer: **B** ($2-\ln2$)

$\mathrm{KL}=\frac12[(1+1-0-1)+(0+4-\ln4-1)]=\frac12(4-2\ln2)=2-\ln2$.

### Part 3.2 — answer: $\dfrac{35}{16}-\dfrac12\ln2$

Example 1: recon $=\frac12(0.25+0+1)=\frac58$; KL $=\frac12(0.25+0)=\frac18$ (both logvars 0 contribute $1-0-1=0$); $\mathcal L_2=\frac58+\frac14=\frac78$.
Example 2: recon $=\frac12(0+1+0)=\frac12$; KL $=\frac12[(1+1-0-1)+(1+2-\ln2-1)]=\frac32-\frac12\ln2$; $\mathcal L_2=\frac12+3-\ln2=\frac72-\ln2$.
Mean: $\frac12\big(\frac78+\frac72-\ln2\big)=\frac{35}{16}-\frac12\ln2\approx1.840926$ (so $r=35/16$, $s=1/2$).

### Part 3.3 — answers: (a) proof; (b) $\mu^*=\dfrac{x}{1+\beta}$, $s^*=\dfrac{\beta}{1+\beta}$; (c) $\mu^*=1$, $s^*=\frac23$, $J_{\min}=3+\ln\frac32$

(a) Write $z=\mu+\sqrt s\,\varepsilon$ with $E\varepsilon=0$, $E\varepsilon^2=1$:
$E(x-z)^2=E[(x-\mu)-\sqrt s\varepsilon]^2=(x-\mu)^2-2(x-\mu)\sqrt s\,E\varepsilon+s\,E\varepsilon^2=(x-\mu)^2+s$.

(b) By (a), $J(\mu,s)=\underbrace{\tfrac12(x-\mu)^2+\tfrac\beta2\mu^2}_{g(\mu)}+\underbrace{\tfrac12 s+\tfrac\beta2(s-\ln s)}_{h(s)}-\tfrac\beta2$, separable.
$g$ is a strictly convex quadratic: $g'(\mu)=-(x-\mu)+\beta\mu=0\Rightarrow\mu^*=x/(1+\beta)$, its unique global minimizer on $\mathbb R$.
On $s>0$: $h'(s)=\frac12+\frac\beta2(1-\frac1s)$, $h''(s)=\frac{\beta}{2s^2}>0$, so $h$ is strictly convex; $h'(s)=0\iff(1+\beta)s=\beta\iff s^*=\beta/(1+\beta)\in(0,1)$; $h\to\infty$ as $s\to0^+$ and as $s\to\infty$, so $s^*$ is its unique global minimizer.
Since $J$ is a sum of a function of $\mu$ alone and a function of $s$ alone, $(\mu^*,s^*)$ is the unique global minimizer of $J$.

(c) $x=3,\beta=2$: $\mu^*=1$, $s^*=\frac23$.
$J=\frac12\big((3-1)^2+\frac23\big)+\big(1+\frac23-\ln\frac23-1\big)=\frac73+\frac23+\ln\frac32=3+\ln\frac32\approx3.405465$.

### Part 3.4 — answer: **B** $(2,\tfrac13)$

$J_{\text{bug}}=\frac\beta2((x-\mu)^2+s)+\frac12(\mu^2+s-\ln s-1)$.
$\partial_\mu:\ -\beta(x-\mu)+\mu=0\Rightarrow\mu=\beta x/(1+\beta)=6/3=2$.
$\partial_s:\ \frac\beta2+\frac12-\frac1{2s}=0\Rightarrow s=1/(1+\beta)=1/3$ (strictly convex as in 3.3).

### Part 3.5 (programming) — answer: **kl[1] = 0.568147**

$\mathrm{kl}[1]=\frac12[(0.25+0.25-\ln0.25-1)+(0.25+1-0-1)]=\ln2-\frac18\approx0.568147$; `kl[0]` $=2-\ln2$ and `z = [[2, -2], [1.5, -0.5]]` as required.

### Part 3.6 (programming) — answer: **total = 1.840926**

`recon_mean = 0.5625`, `kl_mean = 0.639213`, `total = 35/16 - ln2/2`.

### Part 3.7 (programming) — answer: **2.732**

Held-out β-weighted objective (β = 2), nats per example, constant dropped: before training 3.779, after training **2.732** ($\le0.8\times3.779$).
First logged total 3.976, mean of last 20 totals 2.427; the recon-only gradient reaches `mu_head.weight`.

### Part 3.8 (programming) — answer: **1, 0**

β = 2 per-latent held-out KL `[0.5214, 0.0003]` (1 active); β = 8 `[0.0005, 0.0001]` (0 active).
(c) Posterior collapse: at β = 8 the encoder sets $q(z\mid x)\approx p(z)$ for both latents; revealed by the logged `kl_mean` falling to ≈0.0008 nats while `recon_mean` stays ≈3.56 (vs 1.21 at β = 2).

## Problem 2 (open-ended) — test score **0.001541** (95% CI [0.00083, 0.00287], n = 200)

Learned inverse (MLP on 800 train + 20,000 simulated rows, 1,000 steps) as initializer, then 300 per-row least-squares steps (lr 0.01 chosen on validation).
Validation: fixed-start LS 0.03777, MLP alone 0.03144, MLP + LS 0.00264 (lr 0.01) / 0.00282 (lr 0.005).
Baseline under the protocol 0.04810. Steps 2,200 / 3,000; `budget.elapsed()` ≈ 8 s. Full-credit tier (≤ 0.01318).

## Problem 4 (open-ended) — test accuracy **0.9900** (95% CI [0.9800, 0.9975], n = 400)

Scanner B's fixed per-pixel offset is estimated from the pool (pool mean image minus the labelled global mean) and removed patch by patch; then closed-form texture features (pixel moments, spectral peakiness, radial power bands, neighbour correlations) + logistic head + 3 rounds of confidence-thresholded self-training on the corrected pool.
Validation: raw-pixel CNN 0.550, features labelled-only (no pool) 0.550, per-scanner feature standardization 0.825, offset correction 0.950, with self-training 1.000.
Baseline 0.4850. Steps 1,050 / 1,500; `budget.elapsed()` ≈ 2 s. Full-credit tier (≥ 0.8638).
Labelled-only probes at the frozen seed (test accuracy; none reaches the full-credit tier): closed-form features + logistic head 0.6250, raw-pixel CNN (baseline) 0.4850, CNN with flip/rotation augmentation (1,000 steps) 0.6475, nearest prototype on standardized features 0.6175.

## Problem 5 (open-ended) — test score **0.005272** (95% CI [0.00484, 0.00568], n = 200)

Two initializers per signal — learned amortized regressor (MLP, 700 steps on 800 train + 20,000 simulated signals) and a closed-form greedy peak picker — each refined by 200 LS steps (lr 0.02 chosen on validation), keep the lower-residual fit.
Validation: learned regressor alone 0.05056, greedy alone 0.01831, learned + LS 0.00592, greedy + LS 0.00597, best-of-two 0.00504.
Baseline 0.01711. Steps 1,900 / 2,000; `budget.elapsed()` ≈ 7 s. Full-credit tier (≤ 0.008231).
