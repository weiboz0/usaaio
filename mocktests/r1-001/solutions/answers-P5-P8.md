# Mock Test r1-001 — P5–P8 Answers

- r1-001-p05-1: answer: 311 (token-count invariant)
- r1-001-p05-2: answer: hash-dependent set order; multiplicity and sequence order are lost
- r1-001-p05-3: answer: 220 (embedded-token-count invariant; OOV count is 0)
- r1-001-p05-4: answer: 220 (row-count invariant for `W_raw.shape == (220, 100)`)
- r1-001-p05-5: answer: 220 (unit-row-count invariant)
- r1-001-p05-6: answer: [-1, 1]; -1 for opposite unit rows, 1 for identical unit rows
- r1-001-p05-7: answer: S is symmetric and every diagonal entry is 1
- r1-001-p05-8: answer: 100 (singular-value-count invariant)
- r1-001-p05-9: answer: thin: (220,100),(100,),(100,100); full: (220,220),(100,),(100,100); S adds 120 zeros
- r1-001-p05-10: answer: 220.0 (sum-of-full-eigenvalues invariant)
- r1-001-p05-11: answer: sum(sigma[r:]**4) / sum(sigma**4)
- r1-001-p05-12: answer: 100 (relative-error-vector-length invariant)
- r1-001-p05-13: answer: 3
- r1-001-p05-14: answer: 663 (stored-scalar-count invariant; dense S stores 48400)
- r1-001-p06-1: answer: 20.0 (standardized-array squared-energy invariant)
- r1-001-p06-2: answer: 0
- r1-001-p06-3: answer: 24.0 (sum of supplied-probe outputs invariant)
- r1-001-p06-4: answer: 86 (sum of seeded census array invariant)
- r1-001-p07-1: answer: 16 (registered-scalar-count invariant for supplied shape probe)
- r1-001-p07-2: answer: -3.5 (sum of `manual_output` invariant)
- r1-001-p07-3: answer: 131648
- r1-001-p07-4: answer: 1024 (output-channel-count invariant; shape is (1,1024,10,10))
- r1-001-p07-5: answer: 4074560 (frozen-scalar-count invariant; trainable count is 11275)
- r1-001-p08-1: answer: 2.0 (sum of inclusive-step probe outputs invariant)
- r1-001-p08-2: answer: -5.0 (sum of all plane weights and biases invariant)
- r1-001-p08-3: answer: 2.0 (sum of region-membership probe outputs invariant)
- r1-001-p08-4: answer: 9

## Full proof for Part 5.7

Let row $i$ of $W$ be $w_i=(w_{i1},\ldots,w_{i,100})$. By the entrywise
definition of matrix multiplication,

$$
S_{ij}=(WW^T)_{ij}
=\sum_{k=1}^{100}W_{ik}(W^T)_{kj}
=\sum_{k=1}^{100}w_{ik}w_{jk}.
$$

For symmetry, real scalar multiplication commutes, so

$$
S_{ji}=\sum_{k=1}^{100}w_{jk}w_{ik}
=\sum_{k=1}^{100}w_{ik}w_{jk}=S_{ij}.
$$

Thus $S=S^T$. This step uses that both entries are formed from the same real rows
of $W$. For a diagonal entry,

$$
S_{ii}=\sum_{k=1}^{100}w_{ik}^2=w_i\cdot w_i=\lVert w_i\rVert_2^2=1.
$$

The last equality uses Part 5.5's row-normalization property: every row of $W$ is
a unit vector. Therefore $S$ is symmetric and every diagonal entry is exactly one.

## Full proof for Part 5.11

Part 5.10 gives the orthogonal spectral decomposition
$S=U\operatorname{diag}(\lambda_1,\ldots,\lambda_N)U^T$. If
$q=\min(N,100)$, then $\lambda_k=\sigma_k^2$ for $1\le k\le q$ and
$\lambda_k=0$ for $k>q$. Retaining the first $r$ eigenpairs leaves

$$
S-S_r=\sum_{k=r+1}^{N}\lambda_k u_k u_k^T.
$$

The rank-one matrices $u_k u_k^T$ are orthonormal in the Frobenius inner
product, since
$\langle u_i u_i^T,u_j u_j^T\rangle_F=(u_i^T u_j)^2$, which is one for
$i=j$ and zero otherwise. Pythagoras therefore yields

$$
\lVert S-S_r\rVert_F^2
=\sum_{k=r+1}^{N}\lambda_k^2
=\sum_{k=r+1}^{q}(\sigma_k^2)^2
=\sum_{k=r+1}^{q}\sigma_k^4.
$$

Likewise, $\lVert S\rVert_F^2=\sum_{k=1}^{q}\sigma_k^4$. Fourth powers
appear because $S=WW^T$ first squares each singular value of $W$ to obtain an
eigenvalue of $S$, and the squared Frobenius norm then squares that eigenvalue.
Consequently,

$$
\frac{\lVert S-S_r\rVert_F^2}{\lVert S\rVert_F^2}
=\frac{\sum_{k=r+1}^{q}\sigma_k^4}{\sum_{k=1}^{q}\sigma_k^4}.
$$

The numerator is precisely the tail spectral energy omitted after the first
$r$ eigenpairs.
