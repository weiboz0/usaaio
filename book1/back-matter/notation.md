# Notation

This page lists the symbols the lessons use, grouped by topic, with the unit where each first appears.
Use it as a reminder after you have met a symbol in its unit.
When a lesson defines a symbol differently for a moment, the lesson's definition wins.

## Numbers, sets, and shapes · F1–F3

| Symbol | Meaning |
|---|---|
| $\mathbb{R}$, $\mathbb{R}^n$, $\mathbb{R}^{m\times n}$ | real numbers; vectors with $n$ entries; matrices with $m$ rows and $n$ columns |
| $(n, d)$ | the shape of an array or matrix: $n$ rows, $d$ columns; one row per example by convention |
| $x_i$, $X_{ik}$ | entry $i$ of a vector; entry in row $i$, column $k$ of a matrix |
| $\sum_{i=1}^{n}$, $\prod$ | sum and product over the stated range |
| $\lfloor t \rfloor$ | floor: the largest integer not above $t$ |
| $\gcd(a, b)$ | greatest common divisor, used to state a fraction in lowest terms |
| $\approx$ | approximately equal; used only for rounded decimals |
| $\mathbf{1}$ | the all-ones vector of the stated length |

## Vectors · F2

| Symbol | Meaning |
|---|---|
| $u, v, w, x$ | vectors (lowercase letters) |
| $u \cdot v$ | dot product $\sum_i u_i v_i$ |
| $\lVert v \rVert$, $\|v\|$ | Euclidean length (2-norm) $\sqrt{v \cdot v}$; both spellings appear |
| $\lVert v \rVert_1$, $\sum_k \lvert w_k \rvert$ | 1-norm: the sum of absolute entries |
| $v / \lVert v \rVert$ | the unit vector in the direction of $v \ne 0$ |
| $\cos\theta = \dfrac{u\cdot v}{\lVert u\rVert\,\lVert v\rVert}$ | cosine similarity of $u$ and $v$ |
| $u \perp v$ | $u$ and $v$ are orthogonal: $u \cdot v = 0$ |

## Matrices · F3, F6

| Symbol | Meaning |
|---|---|
| $A, W, X$ | matrices (uppercase letters); $X$ is usually the data matrix |
| $A^T$, $A^{\mathsf T}$, $A^\top$ | the transpose of $A$; all three spellings appear and mean the same thing |
| $AB$ | the matrix product |
| $A^{-1}$ | the inverse of a square, invertible matrix |
| $X^{+}$ | the pseudoinverse; $X^{+}y$ is the minimum-norm least-squares solution |
| $u \otimes v$ | outer product, the matrix with entries $u_i v_j$ |
| $u \odot v$ | elementwise (Hadamard) product |
| $\operatorname{rank}(A)$ | the number of linearly independent columns of $A$ |
| $\operatorname{col}(A)$, $\operatorname{row}(A)$ | column space and row space |
| $\operatorname{diag}(d_1,\dots,d_n)$ | the diagonal matrix with the listed entries |
| $\operatorname{tr}(A)$ | trace: the sum of the diagonal entries |
| $I$ | the identity matrix |
| $\lambda$, $\Lambda$ | an eigenvalue; the diagonal matrix of eigenvalues |
| $A = U\Sigma V^{\mathsf T}$ | singular value decomposition, with singular values $\sigma_1 \ge \sigma_2 \ge \dots \ge 0$ on the diagonal of $\Sigma$ |
| $\lVert A \rVert_F$ | Frobenius norm $\sqrt{\sum_{i,k} A_{ik}^2}$ |

## Calculus and optimization · F4, F7, C3

| Symbol | Meaning |
|---|---|
| $\dfrac{\partial f}{\partial x}$ | partial derivative of $f$ with respect to $x$, other inputs held fixed |
| $\nabla f$, $\nabla L(w)$ | gradient: the vector of all partial derivatives |
| $L$, $L(w, b)$ | a loss function of the parameters |
| $\eta$ | learning rate (step size) |
| $w \leftarrow w - \eta \nabla L(w)$ | one gradient-descent update |
| $\theta$ | a model parameter (C11), or the angle between two vectors (F2) |
| $\arg\min_w L(w)$ | the value of $w$ that minimizes $L$ |
| $L(x, \lambda, \nu)$ | the Lagrangian, with inequality multipliers $\lambda_i \ge 0$ and equality multipliers $\nu_j$ |
| $\tanh$, $\tanh' = 1 - \tanh^2$ | hyperbolic tangent and its derivative |

## Probability · F5

| Symbol | Meaning |
|---|---|
| $P(A)$, $P(A \mid B)$ | probability of event $A$; probability of $A$ given $B$ |
| $A \cap B$, $A \cup B$ | both events; at least one of the events |
| $E[X]$ | expected value (mean) of a random variable |
| $\operatorname{Var}(X)$, $\operatorname{sd}(X)$ | variance $E[(X - E[X])^2]$; standard deviation $\sqrt{\operatorname{Var}(X)}$ |
| $\operatorname{Cov}(X, Y)$ | covariance $E[(X - E[X])(Y - E[Y])]$ |
| $\mu$, $\sigma$, $\sigma^2$ | mean, standard deviation, variance |
| $X \sim \mathcal{N}(\mu, \sigma^2)$ | $X$ has a Gaussian (normal) distribution; $N(\mu,\sigma^2)$ means the same |
| $\bar X$ | the sample mean of $X_1, \dots, X_n$ |
| $\binom{n}{k}$ | the number of ways to choose $k$ items from $n$ |
| $\varepsilon$ | a small tolerance or deviation, or a noise term, as the lesson says |

## Models and learning · C1–C12

| Symbol | Meaning |
|---|---|
| $n$, $d$ | number of examples; number of features |
| $X$, $y$ | data matrix (one row per example); target vector |
| $\hat y$ | the model's prediction |
| $w$, $b$ | weights and bias of a linear model or layer |
| $\hat y = Xw + b\mathbf{1}$ | a linear model's predictions for all $n$ examples |
| $\mathrm{MSE}$ | mean squared error $\frac1n\sum_i (\hat y_i - y_i)^2$ |
| $\lambda$ | regularization strength (in C2 and C12; elsewhere $\lambda$ is an eigenvalue or a multiplier) |
| $\sigma(z)$ | the logistic sigmoid $1/(1 + e^{-z})$ (in F6, $\sigma_k$ is a singular value instead) |
| $\mathrm{relu}(z)$, $\operatorname{ReLU}$ | $\max(0, z)$ |
| $Z$, $P$, $Y$ | logits, softmax probabilities, one-hot labels (C11), each of shape $(N, C)$ |
| $N$, $C$ | batch size; number of classes (C11) |
| $\gamma$, $\beta$ | batch-normalization scale and shift (C11) |
| $\widehat X$ | batch-normalized values before the scale and shift (C11) |
| $t_i \in \{-1, +1\}$ | class labels for a support vector machine (C12) |
| $\xi_i$ | slack of example $i$ in a soft-margin SVM (C12) |
| $C$ | the SVM penalty parameter, written `C` in code (C12) |
| $n_{\text{out}} = \left\lfloor \frac{n_{\text{in}} + 2p - K}{s} \right\rfloor + 1$ | convolution output size with padding $p$, kernel size $K$, stride $s$ (C7) |

## Logarithms

$\log$ means the natural logarithm (base $e$) unless a base is written.
C12's entropy uses $\log_2$ and says so.
