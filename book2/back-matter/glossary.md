# Glossary

Each entry gives a term in plain words and the unit that teaches it.
Terms that Book 1 introduces, such as gradient descent, softmax, or tokenization, are defined in the glossary of *Machine Learning for the AI Olympiad*.

**Attention complexity** — Full attention over $n$ tokens computes $n^2$ scores, so its time and memory grow quadratically with length. *(B2-019)*
<!-- concept: attention-complexity -->

**Attention mask** — A Boolean pattern of forbidden query–key pairs, applied as $-\infty$ scores before the softmax. *(B2-019)*
<!-- concept: attention-mask -->

**Autoencoder** — A network that compresses its input to a low-dimensional code with an encoder and reconstructs it with a decoder. *(B2-022)*
<!-- concept: autoencoder -->

**Causal language modeling** — Training each position to predict the next token from the tokens before it, with targets shifted by one. *(B2-020)*
<!-- concept: causal-language-modeling -->

**Causal self-attention** — Self-attention in which position $i$ may attend only to positions $j\le i$, so no token sees the future. *(B2-019)*
<!-- concept: causal-self-attention -->

**Denoising diffusion (DDPM)** — A model that adds Gaussian noise over many steps and learns to predict the noise, so it can reverse the process. *(B2-023)*
<!-- concept: denoising-diffusion-probabilistic-models -->

**Embedding-model training** — Learning an embedding table by gradient descent on a prediction loss, so only the rows used receive updates. *(B2-020)*
<!-- concept: embedding-model-training -->

**Fine-tuning protocol** — Adapting a pretrained model to a labeled task by choosing what to freeze or unfreeze and evaluating on held-out data. *(B2-020)*
<!-- concept: nlp-fine-tuning-protocol -->

**Generative adversarial network (GAN)** — A generator and a discriminator trained against each other until generated samples are hard to tell from real ones. *(B2-023)*
<!-- concept: generative-adversarial-network -->

**GPU workflow on Colab L4** — Device-agnostic PyTorch, mixed precision, memory estimates, and checkpoints that let a run move to a Colab L4 GPU. *(B2-024)*
<!-- concept: gpu-colab-l4-workflow -->

**Graph and cross-modal Transformers** — Attention over a graph's neighbors, or across modalities with queries from one input and keys and values from another. *(B2-021)*
<!-- concept: graph-neural-network-transformer-applications -->

**KL divergence** — $\mathrm{KL}(P\|Q)=E_P[\log(P/Q)]\ge0$: how much $Q$ differs from $P$, in nats; it is not symmetric. *(B2-022)*
<!-- concept: kl-divergence -->

**Language Transformer** — A Transformer that maps token IDs, through embeddings and blocks, to logits over the vocabulary. *(B2-020)*
<!-- concept: language-transformer -->

**Learned token embedding** — A trainable table that maps each token ID to a vector; a lookup equals multiplying a one-hot row by the table. *(B2-020)*
<!-- concept: learned-token-embedding -->

**Masked language modeling** — Hiding some input tokens and training the model to recover them from the context on both sides. *(B2-020)*
<!-- concept: masked-language-modeling -->

**Matrix transpose** — Swapping rows and columns, $A^\top_{ij}=A_{ji}$; for batched tensors, swapping the last two axes with `transpose(-2, -1)`. *(B2-019)*
<!-- concept: matrix-transpose -->

**Mixture-parameter regression** — Predicting the parameters of several overlapping components, scored with a metric that ignores their order. *(B2-024)*
<!-- concept: mixture-parameter-regression -->

**Multi-head attention** — Several attention heads of width $d_h=d/h$ run in parallel on split projections, then merged by an output projection. *(B2-019)*
<!-- concept: multi-head-attention -->

**Multivariate Gaussian** — The normal distribution $N(\mu,\Sigma)$ on vectors, with mean vector $\mu$ and covariance matrix $\Sigma$. *(B2-022)*
<!-- concept: multivariate-gaussian -->

**Object detection** — Predicting where objects are, as boxes, and what they are, scored with IoU and cleaned up by non-maximum suppression. *(B2-021)*
<!-- concept: object-detection -->

**Open-ended experiment design** — Planning a modeling study: a hypothesis, a baseline, ablations, a compute budget, and a decision rule fixed in advance. *(B2-024)*
<!-- concept: open-ended-experiment-design -->

**Open-ended model evaluation** — Judging a model with honest data roles, paired comparisons, and a bootstrap interval around its single test score. *(B2-024)*
<!-- concept: open-ended-model-evaluation -->

**Position-wise feed-forward network** — A two-layer MLP, $W_2\phi(W_1x+b_1)+b_2$, applied to every token separately with shared weights. *(B2-019)*
<!-- concept: position-wise-feed-forward -->

**Pretraining objective** — The self-supervised task, such as next-token or masked-token prediction, a model learns on unlabeled text. *(B2-020)*
<!-- concept: nlp-pretraining-objectives -->

**Pseudo-labeling** — Semi-supervised learning that labels confident unlabeled examples with the model's own predictions and retrains. *(B2-024)*
<!-- concept: semi-supervised-pseudo-labeling -->

**Query, key, and value** — Three learned projections of the tokens: queries ask, keys are matched against queries, values carry what is passed on. *(B2-019)*
<!-- concept: query-key-value-attention -->

**Reparameterization trick** — Sampling $z=\mu+\sigma\odot\varepsilon$ with $\varepsilon\sim N(0,I)$, so gradients flow through $\mu$ and $\sigma$. *(B2-022)*
<!-- concept: gaussian-reparameterization -->

**Residual connection and LayerNorm** — Adding a sublayer's input to its output, and normalizing each token's features to zero mean and unit variance. *(B2-019)*
<!-- concept: transformer-residual-layernorm -->

**Scaled dot-product attention** — $\operatorname{softmax}(QK^\top/\sqrt{d_k})\,V$: each query takes a weighted average of values, weighted by key match. *(B2-019)*
<!-- concept: scaled-dot-product-attention -->

**Scientific inverse problem** — Recovering hidden causes from measured effects through a known forward model, with regularization or a learned inverse. *(B2-024)*
<!-- concept: scientific-ml-inverse-problems -->

**Sinusoidal positional encoding** — A fixed table of sines and cosines at different frequencies, added to token vectors to mark their positions. *(B2-019)*
<!-- concept: sinusoidal-positional-encoding -->

**Stable diffusion** — Diffusion in a compressed latent space, conditioned through cross-attention and steered by classifier-free guidance. *(B2-023)*
<!-- concept: stable-diffusion -->

**Task design for Transformers** — Matching a language task to its input format, output head, loss, and evaluation metric. *(B2-020)*
<!-- concept: transformer-nlp-task-design -->

**Transformer block** — Attention and a feed-forward network, each wrapped with a residual connection and LayerNorm. *(B2-019)*
<!-- concept: transformer-block -->

**U-Net** — An encoder–decoder network for dense prediction whose skip connections join each downsampling stage to its upsampling stage. *(B2-021)*
<!-- concept: unet -->

**Variational autoencoder (VAE)** — An autoencoder with a Gaussian code, trained on reconstruction plus a KL term to the prior, so new samples can be drawn. *(B2-022)*
<!-- concept: variational-autoencoder -->

**Vision Transformer (ViT)** — A Transformer for images: the image is cut into patches, each patch becomes a token, and a class token is read out. *(B2-021)*
<!-- concept: vision-transformers -->
