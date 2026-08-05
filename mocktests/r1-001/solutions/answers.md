# r1-001 — Canonical Answer Key and Worked Solutions

# Mock Test r1-001: Blind Answers for Problems 1–4

## Problem 1

- r1-001-p01-1: answer: C

  Supervised learning requires labeled targets. Option C supplies only unlabeled recordings and asks for groups based on similarity, so it is an unsupervised clustering task.

  - A is wrong because measured next-hour use is a target label for supervised regression.
  - B is wrong because approved/denied labels define supervised classification.
  - D is wrong because recorded delay in minutes is a target label for supervised regression.
  - E is wrong because defective/acceptable inspector tags define supervised classification.

- r1-001-p01-2: answer: D

  Through epoch 7, both training and validation loss fall, so improvements on the training set still transfer to unseen validation data. After epoch 7, training loss continues to fall while validation loss rises. The growing generalization gap means the model is fitting training-specific patterns rather than improving out-of-sample performance. Thus overfitting begins at about epoch 7, and the epoch with the minimum validation loss is the best listed checkpoint for generalization.

  - A is wrong because underfitting would ordinarily leave both training and validation performance poor; here training loss keeps becoming very small while validation loss worsens.
  - B is wrong because equal training and validation set sizes are not required to diagnose a diverging learning curve.
  - C is wrong because the continuing fall in training loss shows that the optimizer is still changing the model successfully on its training objective.
  - E is wrong because divergence alone does not prove that validation examples were used for fitting; it is the standard pattern of overfitting even when the split is respected.

- r1-001-p01-3: answer: B

  The validation set is supposed to simulate unseen data. Computing medians, means, and standard deviations from all 1,260 rows lets the later validation rows influence the fitted preprocessing parameters. Information from validation therefore enters the training pipeline before the classifier is assessed, which is data leakage.

  - A is wrong because seeded shuffling before a random split does not itself transfer validation information into training.
  - C is wrong because choosing a 25% validation fraction is a design choice, not leakage.
  - D is wrong because applying parameters fitted on training rows only to validation rows is the correct leakage-free procedure.
  - E is wrong because fitting the classifier only on training rows is also correct; the leakage occurred earlier when preprocessing parameters were fitted globally.

- r1-001-p01-4: answer: E

  For class A, the all-A classifier has precision \(800/1000=4/5\) and recall \(800/800=1\), so

  \[
  F1_A=\frac{2(4/5)(1)}{4/5+1}=\frac89.
  \]

  For class B, it predicts no B examples, so recall is \(0/200=0\) and \(F1_B=0\). Hence

  \[
  \operatorname{macro\text{-}F1}=\frac{F1_A+F1_B}{2}
  =\frac{8/9+0}{2}=\frac49\approx 0.44.
  \]

  Accuracy instead counts the 800 majority-class successes among all 1,000 examples, giving \(800/1000=0.80\). Thus accuracy is majority-dominated, whereas macro-F1 gives the failed minority class equal classwise weight.

  Verified via direct Python computation: exact `Fraction` arithmetic produced $F1_A=8/9$, $F1_B=0$, and macro-F1 $=4/9$ (approximately $0.444444$).

  - A is wrong because macro-F1 averages the F1 score computed separately for each class; it does not average accuracy, precision, recall, and F1.
  - B is wrong because accuracy does count the 800 correctly classified A examples.
  - C is wrong because macro-F1 uses an arithmetic mean of classwise F1 scores, not a geometric mean of class sizes.
  - D is wrong because the classifier has perfect recall for A and zero recall for B, so the two classes are not predicted equally well.

- r1-001-p01-5: answer: A

  Clustering is the unsupervised task of grouping unlabeled observations by a similarity criterion. The traces have no operating-state labels, and the desired result is precisely a grouping by similar vibration patterns, so A is the correct framing.

  - B is wrong because producing several groups does not make a task classification; classification predicts predefined labels.
  - C is wrong because numerical features can be used in either supervised or unsupervised learning and do not create labels.
  - D is wrong because clustering is specifically useful without preassigned group labels.
  - E is wrong because unsupervised machine learning is designed for tasks in which target labels are absent.

## Problem 2

- r1-001-p02-1: answer: C

  By the chain rule and \(d(\tanh u)/du=1-\tanh^2u\),

  \[
  f'(x)=4\left(1-\tanh^2(4x-7)\right).
  \]

  At \(x_0\),

  \[
  f'(x_0)=4\left(1-\left(\frac5{13}\right)^2\right)
  =4\left(\frac{169-25}{169}\right)
  =\frac{576}{169}.
  \]

  Since \(576=2^6\cdot3^2\) and \(169=13^2\), the fraction is reduced. Therefore \(p+q=576+169=745\), which is C.

  Verified via direct Python computation: exact `Fraction` arithmetic evaluated $4(1-(5/13)^2)=576/169$ and returned numerator plus denominator $745$.

  - A is wrong because \(45\ne745\).
  - B is wrong because \(313\ne745\).
  - D is wrong because \(945\ne745\).
  - E is wrong because \(2473\ne745\).

- r1-001-p02-2: answer: 775/24

  Independence makes all covariance terms zero. Scaling a random variable by \(a\) scales its variance by \(a^2\), so

  \[
  \begin{aligned}
  \operatorname{Var}[z]
  &=2^2\operatorname{Var}[X]+(-3)^2\operatorname{Var}[Y]
    +\left(\frac12\right)^2\operatorname{Var}[T]\\
  &=4\left(\frac73\right)+9\left(\frac52\right)
    +\frac14\left(\frac{11}{6}\right)\\
  &=\frac{28}{3}+\frac{45}{2}+\frac{11}{24}\\
  &=\frac{224+540+11}{24}=\frac{775}{24}.
  \end{aligned}
  \]

  Verified via direct Python computation: exact `Fraction` arithmetic summed the three scaled variances and produced $775/24$.

- r1-001-p02-3: answer: 1/13

  For each term \(W_kx_k\), independence of the weight and input gives

  \[
  \mathbb E[W_kx_k]=\mathbb E[W_k]\mathbb E[x_k]=0.
  \]

  Also, since both factors have mean zero,

  \[
  \begin{aligned}
  \operatorname{Var}[W_kx_k]
  &=\mathbb E[W_k^2x_k^2]
    -\bigl(\mathbb E[W_kx_k]\bigr)^2\\
  &=\mathbb E[W_k^2]\mathbb E[x_k^2]\\
  &=\operatorname{Var}[W_k]\operatorname{Var}[x_k]
  =\sigma^2.
  \end{aligned}
  \]

  The products \(W_kx_k\) are mutually independent because they are functions of mutually independent, disjoint weight-input pairs. Therefore their covariance terms vanish and

  \[
  \operatorname{Var}[z]
  =\sum_{k=1}^{169}\operatorname{Var}[W_kx_k]
  =169\sigma^2.
  \]

  Requiring this variance to equal \(1\) gives \(\sigma^2=1/169\). Because the problem specifies \(\sigma>0\),

  \[
  \boxed{\sigma=\frac1{13}}.
  \]

  Verified via direct Python computation: exact `Fraction` arithmetic checked $169(1/13)^2=1$.

## Problem 3

- r1-001-p03-1: answer: D

  Direct multiplication checks all five numbered pairs:

  \[
  \begin{array}{c|c|c}
  \text{pair}&Sq&\lambda q\\ \hline
  1&(16,12)^\mathsf T&(12,9)^\mathsf T\\
  2&(-4,0)^\mathsf T&(0,0)^\mathsf T\\
  3&(-16,-12)^\mathsf T&(16,12)^\mathsf T\\
  4&(16,12)^\mathsf T&(16,12)^\mathsf T\\
  5&(7,3)^\mathsf T&(7,0)^\mathsf T
  \end{array}
  \]

  Only numbered pair 4 satisfies \(Sq=\lambda q\), so its eigenvalue is \(\lambda=4=4/1\). Thus \(p+q_0=4+1=5\), which is answer D.

  Verified via direct Python computation: integer matrix-vector multiplication compared \(Sq\) with \(\lambda q\) for all five pairs, found equality only for pair 4, and computed \(4+1=5\).

  - A is wrong because \(-3\ne5\).
  - B is wrong because \(1\ne5\).
  - C is wrong because \(4\ne5\).
  - E is wrong because \(8\ne5\).

- r1-001-p03-2: answer: 9, -2

  The rows of \(S-\lambda I\) are

  \[
  r_1=(11-\lambda,13),\qquad r_2=(-2,-4-\lambda).
  \]

  Because the second component of \(r_1\) is \(13\ne0\), dependence requires \(r_2=c r_1\) with

  \[
  c=\frac{-4-\lambda}{13}.
  \]

  Matching the first components then requires

  \[
  -2=\frac{-4-\lambda}{13}(11-\lambda).
  \]

  Multiplying by \(13\) and expanding gives

  \[
  -26=(-4-\lambda)(11-\lambda)
  =\lambda^2-7\lambda-44,
  \]

  and hence the required quadratic equation is

  \[
  \lambda^2-7\lambda-18=0.
  \]

  Factoring,

  \[
  (\lambda-9)(\lambda+2)=0,
  \]

  so the eigenvalues, in descending order, are

  \[
  \boxed{9,\ -2}.
  \]

  The dependence is visible at each value: for \(\lambda=9\), the rows are \((2,13)\) and \((-2,-13)=-(2,13)\); for \(\lambda=-2\), they are \((13,13)\) and \((-2,-2)=(-2/13)(13,13)\).

  Verified via direct Python computation: substitution gave zero for \(\lambda^2-7\lambda-18\) at both \(9\) and \(-2\), and the printed row pairs confirmed that the second row is a scalar multiple of the first at each value.

## Problem 4

- r1-001-p04-1: answer: C

  The squared Frobenius norm is the sum of the squares of all six entries:

  \[
  \lVert A\rVert_F^2
  =(-7)^2+2^2+5^2+(-4)^2+1^2+8^2
  =49+4+25+16+1+64=159.
  \]

  Therefore

  \[
  \lVert A\rVert_F=\sqrt{159}=\sqrt{\frac{159}{1}}.
  \]

  Thus \(p=159\), \(q=1\), and \(p+q=160\), which is C.

  Verified via direct Python computation: summing the six integer squares produced $159$, so the normal-form numerator plus denominator is $159+1=160$.

  - A is wrong because \(55\ne160\).
  - B is wrong because \(65\ne160\).
  - D is wrong because \(730\ne160\).
  - E is wrong because \(25282\ne160\).

- r1-001-p04-2: answer: -164

  Define the residual for row \(n\) by

  \[
  r_n(w)=y_n-\sum_{k=0}^{2}X_{n,k}w_k,
  \qquad Q(w)=\sum_{n=0}^{2}r_n(w)^2.
  \]

  For a fixed component \(w_j\),

  \[
  \frac{\partial r_n}{\partial w_j}=-X_{n,j}.
  \]

  Applying the chain rule term by term therefore gives the component formula

  \[
  \boxed{
  \frac{\partial Q}{\partial w_j}
  =-2\sum_{n=0}^{2}X_{n,j}
  \left(y_n-\sum_{k=0}^{2}X_{n,k}w_k\right)
  }.
  \]

  At \(w=(2,-1,3)^\mathsf T\), direct row products give

  \[
  Xw=
  \begin{pmatrix}
  3(2)-7(-1)+2(3)\\
  -4(2)+5(-1)+1(3)\\
  6(2)+2(-1)-3(3)
  \end{pmatrix}
  =\begin{pmatrix}19\\-10\\1\end{pmatrix}.
  \]

  Hence

  \[
  r=y-Xw=\begin{pmatrix}11-19\\-8-(-10)\\9-1\end{pmatrix}
  =\begin{pmatrix}-8\\2\\8\end{pmatrix}.
  \]

  The \(j=1\) column of \(X\) is \((-7,5,2)^\mathsf T\), so

  \[
  \begin{aligned}
  \left.\frac{\partial Q}{\partial w_1}\right|_w
  &=-2\left[(-7)(-8)+5(2)+2(8)\right]\\
  &=-2(56+10+16)\\
  &=\boxed{-164}.
  \end{aligned}
  \]

  Verified via direct Python computation: integer matrix-vector multiplication produced \(Xw=(19,-10,1)\), residuals \((-8,2,8)\), column-residual dot product \(82\), and derivative \(-2(82)=-164\).

---

# Mock Test r1-001 — P5–P8 Answers

- r1-001-p05-1: answer: 311
  (Invariant: token-count invariant)
- r1-001-p05-2: answer: hash-dependent set order; multiplicity and sequence order are lost
- r1-001-p05-3: answer: 220
  (Invariant: embedded-token-count invariant; OOV count is 0)
- r1-001-p05-4: answer: 220
  (Invariant: row-count invariant for `W_raw.shape == (220, 100)`)
- r1-001-p05-5: answer: 220
  (Invariant: unit-row-count invariant)
- r1-001-p05-6: answer: [-1, 1]; -1 for opposite unit rows, 1 for identical unit rows
- r1-001-p05-7: answer: S is symmetric and every diagonal entry is 1
- r1-001-p05-8: answer: 100
  (Invariant: singular-value-count invariant)
- r1-001-p05-9: answer: thin: (220,100),(100,),(100,100); full: (220,220),(100,),(100,100); S adds 120 zeros
- r1-001-p05-10: answer: 220.0
  (Invariant: sum-of-full-eigenvalues invariant)
- r1-001-p05-11: answer: sum(sigma[r:]**4) / sum(sigma**4)
- r1-001-p05-12: answer: 100
  (Invariant: relative-error-vector-length invariant)
- r1-001-p05-13: answer: 3
- r1-001-p05-14: answer: 663
  (Invariant: stored-scalar-count invariant; dense S stores 48400)
- r1-001-p06-1: answer: 20.0
  (Invariant: standardized-array squared-energy invariant)
- r1-001-p06-2: answer: 0
- r1-001-p06-3: answer: 24.0
  (Invariant: sum of supplied-probe outputs invariant)
- r1-001-p06-4: answer: 86
  (Invariant: sum of seeded census array invariant)
- r1-001-p07-1: answer: 16
  (Invariant: registered-scalar-count invariant for supplied shape probe)
- r1-001-p07-2: answer: -3.5
  (Invariant: sum of `manual_output` invariant)
- r1-001-p07-3: answer: 131648
- r1-001-p07-4: answer: 1024
  (Invariant: output-channel-count invariant; shape is (1,1024,10,10))
- r1-001-p07-5: answer: 4074560
  (Invariant: frozen-scalar-count invariant; trainable count is 11275)
- r1-001-p08-1: answer: 2.0
  (Invariant: sum of inclusive-step probe outputs invariant)
- r1-001-p08-2: answer: -5.0
  (Invariant: sum of all plane weights and biases invariant)
- r1-001-p08-3: answer: 2.0
  (Invariant: sum of region-membership probe outputs invariant)
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

---

- r1-001-p09: answer: 0.6860096566841435

Methodology: one frozen, stratified 150-row validation carve (`random_state=20260804`) from the 600 labeled rows; feature effects computed on the 450-row fitting partition only; a bounded kNN-only campaign over three feature counts, two allowed scalers, Manhattan/Euclidean distance, uniform/distance voting, and seven odd `k` values. The accepted `RobustScaler` + uniform Manhattan 5-NN uses the seven strongest fitting-partition features, scores validation f1-macro `0.7896213183730716`, and is refit on all labeled rows before `predict_labels` is defined.

The conversion is defined in rubric.md's Performance-points mapping.

The grading register regenerates the held-back split hermetically in a temporary directory (see p09_solution.ipynb).
