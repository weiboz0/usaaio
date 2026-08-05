# r1-001 — Scoring Rubric (per-problem partial credit)

> Grader note (p05-9): with full_matrices=True the sigma vector REMAINS shape (100,) —
> only U widens to (220, 220). Do not expect a (220,) spectrum.

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

---

# Mock Test r1-001 — P5–P8 Partial-Credit Rubric

- r1-001-p05-1 (5): 2 points for `simple_preprocess(corpus)`; 1 for occurrence count 311; 1 for distinct count 220; 1 for required identifiers/prints.
- r1-001-p05-2 (5): 3 points for process-dependent hash/set iteration order; 2 for a valid lost property such as multiplicity/frequency or sequence position.
- r1-001-p05-3 (5): 2 points for stable first-occurrence deduplication; 1 for vocabulary filtering/OOV separation; 1 for every lookup; 1 for the required per-vector float64 boundary cast.
- r1-001-p05-4 (5): 3 points for stacking one token vector per row into `(220, 100)`; 1 for `W_raw` orientation/name; 1 for float64 and assertions.
- r1-001-p05-5 (5): 2 points for vectorized squared row lengths; 1 for `(N,1)` square-root norms; 2 for broadcast division and unit-row verification. Any loop or `np.linalg` use earns zero by the statement.
- r1-001-p05-6 (5): 2 points for `[-1,1]`; 1.5 for equality at 1 iff identical unit rows; 1.5 for equality at -1 iff opposite unit rows.
- r1-001-p05-7 (15): 5 points for the correct 100-coordinate formula; 5 for symmetry via commutativity/index reversal; 5 for `S_ii=||w_i||^2=1` citing unit rows.
- r1-001-p05-8 (5): 3 points for `np.linalg.svd(W, full_matrices=False)` with all required names; 1 for reporting `sigma`; 1 for descending-order assertion.
- r1-001-p05-9 (5): 2 points for all thin shapes; 1 for all full shapes; 1 for identifying the 100 singular values; 1 for the 120 additional zero eigenvalues of `S`.
- r1-001-p05-10 (5): 2 points for full SVD; 1 for squared singular values; 1 for zero-padding to length 220; 1 for correct reconstruction/assertion.
- r1-001-p05-11 (15): 4 points for spectral residual expansion; 4 for Frobenius orthogonality/Pythagoras; 4 for the fourth-power ratio; 3 for identifying the numerator as the rank-r tail.
- r1-001-p05-12 (5): 2 points for `sigma**4`; 2 for the full error vector using exactly one `np.cumsum`; 1 for no truncated matrix/factorization and required checks.
- r1-001-p05-13 (5): 3 points for smallest feasible rank `3` without another SVD; 2 for preserving both feasibility/minimality certificate assertions.
- r1-001-p05-14 (5): 2 points for `r(N+1)` versus `N^2`; 1 for `r(N+1)<N^2`; 1 for 663 versus 48400; 1 for concluding the factorization is smaller.
- r1-001-p06-1 (5): 2 points for axis-0 mean/std with `keepdims=True`; 2 for non-mutating broadcast standardization; 1 for contract checks. Any loop or `np.linalg` earns zero.
- r1-001-p06-2 (5): 2 points for excluding self without mutating input; 2 for vectorized argmax returning 0; 1 for exact function/return contract. Any banned operation earns zero.
- r1-001-p06-3 (5): 3 points for a correct arithmetic/ReLU representation; 1 for exact breakpoints including -2 and 4; 1 for vectorized shape preservation. Any banned construct earns zero.
- r1-001-p06-4 (5): 2 points for exact local RNG/seed/range/shape/dtype; 1.5 for axis-0 sums; 1.5 for axis-1 positive counts.
- r1-001-p07-1 (5): 2 points for independent frozen `nn.Parameter` copies; 2 for `x @ weight.T + bias`; 1 for exact names and arbitrary leading input dimensions.
- r1-001-p07-2 (5): 3 points for the exact 4-by-3 weight; 1 for exact bias; 1 for correct float64 batch output/shape.
- r1-001-p07-3 (5): 1 point per correct product term (3); 1 for correct addition; 1 for 131648 excluding BatchNorm. Any banned counting helper earns zero.
- r1-001-p07-4 (5): 1 for exact V1 cached weights and immediate `eval`; 2 for the specified six children plus `layer3[:2]`; 1 for cut `eval` and inference mode; 1 for float32 `(1,1024,10,10)`.
- r1-001-p07-5 (5): 2 points for freezing every backbone parameter only; 1 for trainable head; 1 for named-parameter scalar counts; 1 for 4074560 frozen and 11275 trainable with audits.
- r1-001-p08-1 (5): 3 points for inclusive `x>=0`; 1 for dtype preservation; 1 for shape preservation and exact module name.
- r1-001-p08-2 (5): 2 points for exact plane weight; 1 for exact bias; 1 for correct `Half_Plane_Pair` construction; 1 for two inclusive decisions per row.
- r1-001-p08-3 (5): 2 points for composing the pair/readout/step; 1 for AND weights `[1,1]` and a valid inclusive threshold bias (for example -1.5); 1 for eval/inference mode; 1 for exact probe membership.
- r1-001-p08-4 (5): 2 points for half-plane arithmetic `2*2+2=6`; 2 for readout arithmetic `2*1+1=3`; 1 for literal total 9 and no banned helper.

---

# P9 rubric fragment — 50 points

## Eligibility hard gates

Any one of these failures makes the score **0/50** before point scoring:

- The executed submission uses a non-kNN model family, hand-reimplements another family, or imports outside `sklearn`, `numpy`, `pandas`, and `matplotlib`.
- A fresh top-to-bottom run errors or depends on interactive execution order.
- Any prediction clause fails: `predict_labels` is not callable; does not accept a feature `DataFrame` of any length; does not return a `pd.Series`; changes length/order/index; or emits a label outside the training vocabulary.
- The final submitted predictor refits on test input, was not fit on all labeled rows, or uses held-back rows for modeling decisions.

## Scored work after the gates — 50 points

### Model and validation quality — 44 points

- **Validation methodology and reproducibility — 8 points.** Honest validation protocol — a frozen seeded carve OR repeated/cross-validated splits, on equal terms (2), stratification and macro-F1 (2), feature/model decisions use labeled fitting data without heldout leakage (2), deterministic replay plus honest limitation (2).
- **kNN investigation and final recipe — 8 points.** Meaningful scaled baseline (2), bounded comparison of kNN preprocessing/features/distances/hyperparameters (2), results are recorded and the accepted choice follows them (2), accepted model is refit on all labeled rows and prediction does not refit (2).
- **Heldout predictive performance — 28 points.** Apply the course/mock-test's official f1-macro-to-points mapping to the grader-only heldout predictions.

The performance mapping is DEFINED below (see 'Performance-points mapping') — apply it directly.

### Required summary cell — 6 points

Apply the C10 register mechanically, one point each:

- **W-A1:** full recipe: preprocessing, kNN family with hyperparameter values, and feature set.
- **W-A2:** validation carve size, seed policy, stratification, and submitted recipe's validation metric value.
- **W-B1:** model choice grounded in a property of this dataset.
- **W-B2:** macro-F1 grounded in the class imbalance/task priority.
- **W-C1:** at least one concrete alternative with a measured outcome or precise rejection reason.
- **W-C2:** an honest limitation or next step.

The exemplar summary earns **6/6**: every item above is a checkable sentence tied to notebook output.


## Performance-points mapping (defined at reconciliation — the mapping the fragment reserved)

Held-back f1-macro (computed by the grading register) maps to the 28 performance points as:

- f1 < 0.68 → 0 points (the UNMODIFIED supplied starter scores ≈0.674, below this
  floor — performance points reward work beyond it)
- 0.68 ≤ f1 < 0.78 → linear: points = round(28 · (f1 − 0.68) / 0.10)
- f1 ≥ 0.78 → 28 points

Anchors: the exemplar's single-carve campaign (0.686) → 2 points; a cross-validated recipe
measured at 0.7116 → 9 points; strong work at 0.78+ earns full marks;
 the hard gates (contract, kNN-only, imports,
run-clean) remain pass/fail on top and zero the whole problem when violated.
