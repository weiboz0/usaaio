# Notation

This page lists the symbols the Book 2 lessons use, grouped by unit, with their usual meaning.
Book 2 also uses all of Book 1's notation; see the Notation page of *Machine Learning for the AI Olympiad* for vectors, matrices, gradients, and probability.
When a lesson defines a symbol differently for a moment, the lesson's definition wins.

## Shapes and conventions

| Symbol | Meaning |
|---|---|
| `(B, n, d)` | a batch of $B$ sequences, each of $n$ tokens, each token a vector of width $d$; `(B, N, …)` in some units |
| `(B, C, H, W)` | a batch of images: channels, height, width |
| $A^\top$ | transpose; for a batched tensor, `transpose(-2, -1)` swaps the last two axes |
| $\mathbb{R}^{n\times d}$ | real matrices with $n$ rows and $d$ columns |
| $\odot$ | elementwise product |
| $\log$ | natural logarithm; quantities such as KL divergence are in nats |
| $E_{z\sim q}[\,\cdot\,]$ | expectation when $z$ is drawn from the distribution $q$ |
| `book1:<id>` | a unit or concept taught in Book 1 |

## Attention and Transformers · B2-019, B2-020

| Symbol | Meaning |
|---|---|
| $Q$, $K$, $V$ | queries, keys, values: the token matrix times $W_Q$, $W_K$, $W_V$ |
| $n_q$, $n_k$ | number of queries; number of keys |
| $d_k$ | width of each query and key vector |
| $S = QK^\top/\sqrt{d_k}$ | attention scores, shape $n_q \times n_k$ |
| $A = \operatorname{softmax}(S)$ | attention weights, normalized along each row (over keys) |
| $AV$ | the attention output: each row a weighted average of value rows |
| $h$, $d_h = d/h$ | number of heads; width of each head |
| $W_O$ | the output projection after the heads are merged |
| $-\infty$ | the score given to a forbidden query–key pair by a mask, before the softmax |
| $j \le i$ | the causal rule: position $i$ may attend only to positions up to $i$ |
| $\mathrm{PE}[p]$ | the sinusoidal positional-encoding vector for position $p$ |
| $\omega_i = 10000^{-2i/d}$ | the frequency of coordinate pair $(2i, 2i+1)$ in the encoding |
| $\operatorname{LN}$ | layer normalization over each token's features |
| $\operatorname{FFN}(x) = W_2\,\phi(W_1x + b_1) + b_2$ | the position-wise feed-forward network, with activation $\phi$ |
| $d_{ff}$ | the hidden width of the feed-forward network |
| $\operatorname{MHA}$ | multi-head attention |

## Vision, detection, and graphs · B2-021

| Symbol | Meaning |
|---|---|
| $P$ | patch side length in a Vision Transformer |
| $N$, $N + 1$ | number of patch tokens; with the class token added |
| $D$ | token width |
| $S \times S$ | the grid of cells a detector predicts on |
| `IoU` | intersection over union of two boxes, from 0 to 1 |
| `(x_min, y_min, x_max, y_max)` | a box by its corners; a grid detector re-encodes it as cell offsets plus normalized width and height |

## Latent-variable models · B2-022

| Symbol | Meaning |
|---|---|
| $N(\mu, \Sigma)$ | multivariate Gaussian with mean vector $\mu$ and covariance matrix $\Sigma$ |
| $\Sigma_{ij} = \operatorname{Cov}(x_i, x_j)$ | covariance entries; $\Sigma = E[(x-\mu)(x-\mu)^\top]$ |
| $\det\Sigma$, $\Sigma^{-1}$ | determinant and inverse of the covariance matrix |
| $\operatorname{diag}(\sigma_1^2, \dots, \sigma_d^2)$ | a diagonal covariance |
| $\mathrm{KL}(P\,\|\,Q)$ | Kullback–Leibler divergence: the extra expected log loss from using $Q$ when the data follow $P$ |
| $H(P)$, $H(P, Q)$ | entropy; cross-entropy |
| $x$, $z$ | an observation; its latent code |
| $q(z \mid x)$ | the encoder's distribution over codes for input $x$ |
| $p(x \mid z)$, $p(z)$ | the decoder's distribution; the prior, usually $N(0, I)$ |
| $\mathrm{ELBO}(x)$ | the evidence lower bound on $\log p(x)$ |
| $\mu$, $\log\sigma^2$ | the encoder's mean and log-variance outputs (`logvar` in code) |
| $z = \mu + \sigma \odot \varepsilon$ | the reparameterized sample, with $\varepsilon \sim N(0, I)$ |
| $\beta$ | the weight on the KL term in a β-weighted objective |

## Generative adversarial networks and diffusion · B2-023

| Symbol | Meaning |
|---|---|
| $G$, $D$ | generator; discriminator |
| $p_{\text{data}}$, $p_g$ | the data distribution; the generator's distribution |
| $\ell$, $\sigma(\ell)$ | a discriminator logit; its sigmoid probability |
| $V(D, G)$ | the GAN value function |
| $\mathcal{L}_D$, $\mathcal{L}_G$ | discriminator loss; generator loss |
| $D^*$ | the optimal discriminator for a fixed generator |
| $\mathrm{JS}(P\,\|\,Q)$ | Jensen–Shannon divergence |
| $\mathrm{BCE}$ | binary cross-entropy |
| $T$, $t$ | number of diffusion steps; one step |
| $x_0$, $x_t$ | a clean sample; its noised version at step $t$ |
| $\beta_t$, $\alpha_t = 1 - \beta_t$ | the noise schedule at step $t$ (not the VAE's $\beta$) |
| $\bar\alpha_t = \alpha_1\alpha_2\cdots\alpha_t$ | the cumulative signal factor |
| $x_t = \sqrt{\bar\alpha_t}\,x_0 + \sqrt{1-\bar\alpha_t}\,\varepsilon$ | the closed-form noising step |
| $\varepsilon_\theta(x_t, t)$ | the network's prediction of the added noise |
| $\mathrm{SNR}$ | signal-to-noise ratio |
| $\varepsilon_{\text{cond}}$, $\varepsilon_{\text{uncond}}$ | conditional and unconditional noise predictions |
| $\hat\varepsilon = \varepsilon_{\text{uncond}} + w(\varepsilon_{\text{cond}} - \varepsilon_{\text{uncond}})$ | classifier-free guidance with guidance weight $w$ |

## GPU workflow and scientific modeling · B2-024

| Symbol | Meaning |
|---|---|
| `cuda`, `cpu` | the device a tensor or model lives on |
| `bfloat16`, `float32` | lower- and full-precision number types used with autocast |
| $c_i$, $\tau$ | the confidence of a pseudo-label; the confidence threshold for keeping it |
| $\mathcal{F}$ | the forward operator that maps hidden causes to measurements |
| $A$ | a linearized forward operator on a grid |
| $\lambda$ | the Tikhonov (ridge) regularization strength |
| $\bar X$, $\operatorname{Var}(\bar X) = \sigma^2/n$ | a sample mean and its variance, used for intervals |
| $B$, $R$, $g$ | in the mock test's open-ended problems: the baseline score, the reference score, and the gap $\lvert B-R\rvert$ |
