# Mock Test r1-001: Rubric Fragments for Problems 1–4

## Problem 1

- r1-001-p01-1 — 10 points, all or nothing: 10 for C; 0 otherwise.
- r1-001-p01-2 — 10 points, all or nothing: 10 for D; 0 otherwise.
- r1-001-p01-3 — 10 points, all or nothing: 10 for B; 0 otherwise.
- r1-001-p01-4 — 10 points, all or nothing: 10 for E; 0 otherwise.
- r1-001-p01-5 — 10 points, all or nothing: 10 for A; 0 otherwise.

## Problem 2

- r1-001-p02-1 — 5 points, all or nothing: 5 for C; 0 otherwise.
- r1-001-p02-2 — 5-point short answer, all or nothing: 5 for the exact value \(775/24\); 0 otherwise.
- r1-001-p02-3 — 5-point derivation:
  - 2 points: establishes \(\mathbb E[W_kx_k]=0\) and \(\operatorname{Var}(W_kx_k)=\sigma^2\) using the stated independence and moments.
  - 2 points: uses independence across terms to obtain \(\operatorname{Var}(z)=169\sigma^2\) and sets it equal to \(1\).
  - 1 point: concludes \(\sigma=1/13\), selecting the positive root because \(\sigma>0\).

## Problem 3

- r1-001-p03-1 — 5 points, all or nothing: 5 for D; 0 otherwise.
- r1-001-p03-2 — 10-point derivation:
  - 3 points: correctly expresses row dependence, for example \(r_2=cr_1\) with \(c=(-4-\lambda)/13\), and equates the remaining components.
  - 3 points: obtains and correctly simplifies the quadratic \(\lambda^2-7\lambda-18=0\) without relying on determinant vocabulary.
  - 3 points: solves the quadratic to get both values \(9\) and \(-2\).
  - 1 point: lists them in descending order (and, equivalently, may explicitly verify the dependent rows at the two values).

## Problem 4

- r1-001-p04-1 — 5 points, all or nothing: 5 for C; 0 otherwise.
- r1-001-p04-2 — 10-point derivation:
  - 4 points: defines the residual and correctly applies the chain rule to derive \(\partial Q/\partial w_j=-2\sum_{n=0}^2X_{n,j}(y_n-\sum_{k=0}^2X_{n,k}w_k)\).
  - 3 points: correctly computes \(Xw=(19,-10,1)^\mathsf T\) and residuals \(y-Xw=(-8,2,8)^\mathsf T\).
  - 3 points: uses column \(j=1\), computes the inner sum as \(82\), and concludes \(\partial Q/\partial w_1=-164\).
