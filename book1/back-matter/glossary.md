# Glossary

Each entry gives a term in plain words and the unit that teaches it.

**Accuracy, precision, recall** — Accuracy is the share of correct predictions; precision, of predicted positives that are real; recall, of real positives found. *(C1)*
<!-- concept: accuracy-precision-recall -->

**Activation function** — The nonlinear function a neuron applies to its weighted sum, such as ReLU, tanh, or a step. *(C6)*
<!-- concept: activation-functions -->

**Aggregation axis** — The axis a reduction such as `sum` or `mean` collapses: `axis=0` combines rows, `axis=1` combines columns. *(F1)*
<!-- concept: aggregation-axis -->

**API-constraint compliance** — Following the required names, signatures, and allowed or banned tools, which are graded like answers. *(C11)*
<!-- concept: api-constraint-compliance -->

**Autograd training** — Training with PyTorch's automatic gradients: forward pass, `loss.backward()`, then an optimizer step. *(C8)*
<!-- concept: autograd-training -->

**Backpropagation** — Computing every parameter's gradient by applying the chain rule backward through the network, layer by layer. *(C8)*
<!-- concept: manual-backpropagation -->

**Bagging and boosting** — Bagging averages models fit on resampled data; boosting fits models in sequence, each correcting the last. *(C12)*
<!-- concept: bagging-and-boosting -->

**Batch normalization** — Standardizing each feature over the batch, then applying a learned scale $\gamma$ and shift $\beta$. *(C8)*
<!-- concept: batch-normalization -->

**Bayes' rule** — $P(A\mid B)=P(B\mid A)\,P(A)/P(B)$: turning a conditional probability around. *(F5)*
<!-- concept: bayes-rule -->

**Bias–variance tradeoff** — Simple models err by bias (missing the pattern), flexible ones by variance (chasing noise); good models balance both. *(C1)*
<!-- concept: bias-variance-intuition -->

**Bottleneck block** — A residual block that narrows the channels with a $1\times1$ convolution, applies a $3\times3$ one, then widens again. *(C10)*
<!-- concept: bottleneck-blocks -->

**Broadcasting** — NumPy's rule for combining arrays of different shapes by stretching size-1 axes, so `X - m` subtracts a row from every row. *(F1)*
<!-- concept: broadcasting -->

**Class imbalance** — When some classes are much rarer than others, so accuracy alone can hide a model that ignores them. *(C1)*
<!-- concept: class-imbalance -->

**Class inheritance** — Defining a Python class that extends a parent class, calling `super().__init__()` and overriding methods. *(C7)*
<!-- concept: python-inheritance -->

**Classical model comparison** — Choosing among classical models by their assumptions, geometry, scaling needs, outputs, and validated results. *(C12)*
<!-- concept: classical-model-comparison -->

**Clustering** — Grouping unlabeled examples so that examples in the same group are similar to one another. *(C1)*
<!-- concept: clustering-concept -->

**CNN training** — Fitting a convolutional classifier with a loss, an optimizer, and batches, and checking that it learns. *(C10)*
<!-- concept: cnn-training -->

**Colab coding submission** — Restarting and running all cells, checking names and outputs, then downloading and reopening the `.ipynb`. *(C11)*
<!-- concept: colab-coding-submission -->

**Colab solution authoring** — Planning a notebook answer as ordered text cells for claims and code cells for evidence. *(C11)*
<!-- concept: colab-markdown-solution-authoring -->

**Conditional probability** — $P(A\mid B)=P(A\cap B)/P(B)$: the probability of $A$ among the outcomes where $B$ happened. *(F5)*
<!-- concept: conditional-probability -->

**Convex function** — A function whose graph lies on or below every chord; a local minimum of a convex function is global. *(F7)*
<!-- concept: convex-functions -->

**Convex set** — A set that contains the whole line segment between any two of its points. *(F7)*
<!-- concept: convex-sets -->

**Convolution** — Sliding a small learned kernel across an input and taking a weighted sum at each position. *(C10)*
<!-- concept: convolution -->

**Cosine similarity** — $\dfrac{u\cdot v}{\lVert u\rVert\,\lVert v\rVert}$: the cosine of the angle between two vectors, from $-1$ to $1$, ignoring their lengths. *(F2)*
<!-- concept: cosine-similarity -->

**Covariance** — $\operatorname{Cov}(X,Y)=E[(X-E[X])(Y-E[Y])]$: how two variables move together. *(F5)*
<!-- concept: covariance -->

**CPU and GPU round boundary** — Round 1 work must run on a CPU only; Round 2 allows a GPU. *(C11)*
<!-- concept: cpu-and-gpu-round-boundary -->

**Cross-entropy loss** — The mean of $-\log p$ assigned to the true class: the negative log-likelihood of the labels. *(C8)*
<!-- concept: cross-entropy-loss -->

**Cross-validation** — Splitting the data into $k$ folds and validating on each fold in turn to get a steadier performance estimate. *(C4)*
<!-- concept: cross-validation -->

**CSV data loading** — Reading a comma-separated file into a `DataFrame` with `pd.read_csv` and checking its columns and types. *(C4)*
<!-- concept: csv-data-loading -->

**Custom layer** — A layer written as your own `nn.Module` subclass, with its parameters wrapped in `nn.Parameter`. *(C7)*
<!-- concept: custom-layers -->

**Decision boundary** — The surface in input space where a classifier's prediction changes; a single linear unit's boundary is a hyperplane. *(C6)*
<!-- concept: decision-boundaries-geometric -->

**Decision tree** — A model that predicts by asking a sequence of yes/no questions about features, from root to leaf. *(C12)*
<!-- concept: decision-trees -->

**Derivative of tanh** — $\frac{d}{dz}\tanh z=1-\tanh^2 z$, so it can be computed from the activation's own output. *(F3)*
<!-- concept: tanh-derivative -->

**Distance metric** — A rule for the distance between two points, such as Euclidean ($\lVert u-v\rVert$) or Manhattan ($\sum_i\lvert u_i-v_i\rvert$) distance. *(F2)*
<!-- concept: distance-metrics -->

**Dot product** — $u\cdot v=\sum_i u_iv_i$, which also equals $\lVert u\rVert\,\lVert v\rVert\cos\theta$ for the angle $\theta$ between them. *(F2)*
<!-- concept: dot-product -->

**Dropout** — Randomly zeroing activations during training, with rescaling, to reduce overfitting; it is off at evaluation. *(C8)*
<!-- concept: dropout -->

**Eigenvalue and eigenvector** — A nonzero $v$ with $Av=\lambda v$: the map only stretches $v$, by the eigenvalue $\lambda$. *(F6)*
<!-- concept: eigenvalues-eigenvectors -->

**Elementwise operation** — An operation applied entry by entry to arrays of the same (or broadcast) shape, such as `a * b` or `np.exp(a)`. *(F1)*
<!-- concept: elementwise-ops -->

**Embedding matrix** — The table with one embedding vector per vocabulary word; looking up a word selects its row. *(C5)*
<!-- concept: embedding-matrices -->

**Ensemble learning** — Combining several models' predictions to get a better one than any member alone. *(C12)*
<!-- concept: ensemble-learning -->

**Expectation** — The probability-weighted average value $E[X]$ of a random variable; it is linear. *(F5)*
<!-- concept: expectation -->

**F1 score** — The harmonic mean of precision and recall, $2PR/(P+R)$. *(C1)*
<!-- concept: f1-score -->

**Feature hierarchy** — Early layers detect edges and textures; deeper layers combine them into parts and objects. *(C10)*
<!-- concept: feature-hierarchy -->

**Feature map** — The output grid of one convolution channel: the kernel's response at every position. *(C10)*
<!-- concept: feature-maps -->

**Feature scaling** — Putting features on comparable scales, for example by standardizing, so no feature dominates a distance. *(C4)*
<!-- concept: feature-scaling -->

**First-order optimality** — For a differentiable convex function, a point is a global minimizer exactly when the gradient there is zero. *(F7)*
<!-- concept: first-order-optimality -->

**Frobenius norm** — $\lVert A\rVert_F=\sqrt{\sum A_{ij}^2}$, which also equals the square root of the sum of squared singular values. *(F6)*
<!-- concept: frobenius-norm -->

**Gaussian distribution** — The bell-shaped normal distribution $N(\mu,\sigma^2)$, set by its mean $\mu$ and variance $\sigma^2$. *(F5)*
<!-- concept: gaussian-distribution -->

**gensim usage** — Loading pretrained word vectors with `gensim` and querying them for membership, vectors, and neighbors. *(C5)*
<!-- concept: gensim-usage -->

**Gradient** — The vector of all partial derivatives, $\nabla f$; it points in the direction of steepest increase. *(F3)*
<!-- concept: gradient -->

**Gradient descent** — Repeatedly stepping against the gradient, $w\leftarrow w-\eta\nabla L(w)$, to reduce a loss. *(C3)*
<!-- concept: gradient-descent -->

**Gram matrix** — The matrix of all pairwise dot products of a set of vectors, $G=XX^{\mathsf T}$; it is symmetric. *(F4)*
<!-- concept: gram-matrices -->

**Hidden-test protocol** — Grading on held-back data the notebook never reads, so every reported number comes from data it was given. *(C11)*
<!-- concept: hidden-test-protocol -->

**Hoeffding's inequality** — A bound on how far the mean of independent bounded variables strays from its expectation, shrinking exponentially in $n$. *(F5)*
<!-- concept: hoeffding-inequality -->

**Identifiability and the pseudoinverse** — When $X$ lacks full column rank, many weights fit equally well; $X^{+}y$ picks the one of smallest norm. *(C2)*
<!-- concept: ols-rank-identifiability-and-pseudoinverse -->

**Independence** — Events or variables are independent when knowing one does not change the probabilities of the other. *(F5)*
<!-- concept: independence -->

**Indexing and slicing** — Selecting entries, rows, columns, or blocks of an array with `a[i]`, `a[i, j]`, `a[start:stop]`, masks, or index lists. *(F1)*
<!-- concept: array-indexing-slicing -->

**Invertibility via rank** — A square $n\times n$ matrix has an inverse exactly when its rank is $n$. *(F4)*
<!-- concept: invertibility-via-rank -->

**Kernel validity** — A function $k(x,x')$ is a valid kernel when every Gram matrix it produces is symmetric positive semidefinite. *(F7)*
<!-- concept: kernel-validity -->

**k-means** — Clustering into $k$ groups so that the total squared distance from points to their group centers is small. *(C12)*
<!-- concept: k-means -->

**k-nearest neighbors (kNN)** — Predicting from the labels of the $k$ training examples closest to the query point. *(C4)*
<!-- concept: knn -->

**L1 regularization (lasso)** — Adding $\lambda\sum_k\lvert w_k\rvert$ to the loss, which pushes some weights to exactly zero. *(C2)*
<!-- concept: l1-regularization -->

**L2 regularization (ridge)** — Adding $\lambda\sum_k w_k^2$ to the loss, which shrinks all weights toward zero. *(C2)*
<!-- concept: l2-regularization -->

**Lagrangian** — The objective plus multiplier-weighted constraints, $L(x,\lambda,\nu)$, used to solve constrained problems. *(F7)*
<!-- concept: lagrangians -->

**Layer freezing** — Turning off gradient updates for some layers, by setting `requires_grad=False`, so training changes only the rest. *(C10)*
<!-- concept: layer-freezing -->

**Learning rate** — The step size $\eta$ of gradient descent: too small crawls, too large oscillates or diverges. *(C3)*
<!-- concept: learning-rate -->

**Least-squares estimator** — The weights minimizing squared error solve the normal equations $X^{\mathsf T}Xw=X^{\mathsf T}y$. *(C2)*
<!-- concept: linear-regression-estimator-derivation -->

**Limits of black-box PCA** — Why a library call alone is not enough: centering, sign, and fit/transform choices must be checked by hand. *(C9)*
<!-- concept: pca-black-box-insufficiency -->

**Linear independence and span** — Vectors are independent when none is a combination of the others; their span is the set of all their combinations. *(F4)*
<!-- concept: linear-independence-span -->

**Linear regression** — Predicting a number as a weighted sum of features plus a bias, $\hat y=Xw+b$. *(C2)*
<!-- concept: linear-regression -->

**Lloyd's algorithm** — The k-means procedure: assign points to the nearest center, move centers to their means, and repeat. *(C12)*
<!-- concept: lloyd-algorithm -->

**Local versus global structure** — Some maps keep near neighbors together but distort large distances; others keep the overall layout. *(C9)*
<!-- concept: local-vs-global-structure -->

**Logistic regression** — A linear classifier that outputs a probability $\sigma(w\cdot x+b)$, trained with cross-entropy. *(C12)*
<!-- concept: logistic-regression -->

**Loss surface** — The loss drawn as a landscape over parameter space; its minima are the bottoms of basins. *(C3)*
<!-- concept: loss-surfaces -->

**Low-rank approximation** — Keeping only the largest $k$ singular values and their vectors, which gives the best rank-$k$ approximation. *(F6)*
<!-- concept: low-rank-approximation -->

**Macro-F1** — The unweighted mean of the per-class F1 scores, so every class counts equally however rare it is. *(C1)*
<!-- concept: f1-macro -->

**Manual weights** — Wiring hand-chosen weights into a network, for example through its `state_dict`, so you can predict exactly what it computes. *(C7)*
<!-- concept: manual-weights -->

**Margin and hinge loss** — The margin $m=t\,f(x)$ is positive on the correct side; hinge loss $\max(0,1-m)$ penalizes small or wrong margins. *(C12)*
<!-- concept: margin-and-hinge-loss -->

**Markdown code snippet** — A fenced, language-labeled block showing code in a text cell; it never replaces runnable code. *(C11)*
<!-- concept: markdown-code-snippets -->

**Markdown math** — Writing formulas in a text cell with inline `$…$` or display `$$…$$` math, defining every symbol. *(C11)*
<!-- concept: markdown-math-formulae -->

**Matplotlib basics** — Making line, scatter, and histogram plots on an explicit figure and axes, with labels and titles. *(F1)*
<!-- concept: matplotlib-basics -->

**Matrix as a linear map** — A matrix $A$ viewed as a function $x\mapsto Ax$ that preserves sums and scalar multiples. *(F4)*
<!-- concept: matrices-as-linear-maps -->

**Matrix from its action** — Building the matrix of a linear map column by column: column $j$ is where the map sends the $j$-th basis vector. *(F4)*
<!-- concept: matrix-from-action -->

**Matrix multiplication** — The product $AB$, whose entry $(i,j)$ is row $i$ of $A$ dotted with column $j$ of $B$; shapes $(m,n)(n,p)\to(m,p)$. *(F4)*
<!-- concept: matrix-multiplication -->

**Mean squared error (MSE)** — The average of squared prediction errors, $\frac1n\sum_i(\hat y_i-y_i)^2$. *(C2)*
<!-- concept: mse-loss -->

**Metric-driven iteration** — Improving a model one measured change at a time against a fixed validation metric, keeping a log. *(C11)*
<!-- concept: metric-driven-iteration -->

**Model truncation** — Cutting a network after a chosen layer to reuse its intermediate features. *(C10)*
<!-- concept: model-truncation -->

**Multilayer perceptron (MLP)** — A network of fully connected layers, each a linear map followed by an activation. *(C6)*
<!-- concept: mlp-architecture -->

**Multivariable chain rule** — The derivative of a composition is a sum, over every path from input to output, of products of partial derivatives. *(F3)*
<!-- concept: multivar-chain-rule -->

**Nearest-neighbor search** — Finding the stored vectors most similar to a query vector. *(C5)*
<!-- concept: nearest-neighbor-search -->

**`nn.Module`** — PyTorch's base class for layers and models; it registers parameters and submodules and defines `forward`. *(C7)*
<!-- concept: nn-module -->

**Normal-form answer** — An answer in exactly the requested form, such as a fraction in lowest terms with a positive denominator. *(C11)*
<!-- concept: normal-form-answers -->

**Notebook discipline** — Pinned seeds, cells in execution order, no dead cells, and identical results on every fresh run. *(C11)*
<!-- concept: notebook-discipline -->

**NumPy array** — A grid of numbers of one type with a fixed shape, such as `(n, d)`, that supports fast whole-array arithmetic. *(F1)*
<!-- concept: numpy-arrays -->

**Optimization duality** — The dual problem built from the Lagrangian bounds the original problem's optimum, and often matches it. *(F7)*
<!-- concept: optimization-duality -->

**Orthogonal and orthonormal** — Vectors are orthogonal when their dot product is 0, and orthonormal when they are also each of length 1. *(F2)*
<!-- concept: orthogonality-orthonormality -->

**Outer product** — The matrix $u\otimes v$ with entries $u_iv_j$; it always has rank at most 1. *(F4)*
<!-- concept: outer-products -->

**Overfitting** — Fitting the training data so closely that performance on new data gets worse. *(C1)*
<!-- concept: overfitting -->

**pandas basics** — Working with tables as `DataFrame`s and `Series`: selecting, filtering, grouping, and summarizing columns. *(C4)*
<!-- concept: pandas-basics -->

**Parameter counting** — Totaling a model's trainable numbers; a dense layer from $n$ to $m$ has $nm+m$. *(C7)*
<!-- concept: parameter-counting -->

**Partial derivative** — The rate of change of a function of several variables in one variable, with the others held fixed. *(F3)*
<!-- concept: partial-derivatives -->

**PCA as an eigenproblem** — Deriving PCA: the best directions are the top eigenvectors of the centered data's covariance matrix. *(C9)*
<!-- concept: pca-centered-covariance-eigenproblem-derivation -->

**PCA from scratch** — Writing a PCA class in NumPy with `fit` and `transform` that center, decompose, and project. *(C9)*
<!-- concept: numpy-pca-class-from-scratch -->

**Perceptron** — A single unit that outputs a class from the sign of a weighted sum $w\cdot x+b$. *(C6)*
<!-- concept: perceptron -->

**Positive semidefinite matrix** — A symmetric matrix $A$ with $x^{\mathsf T}Ax\ge0$ for every $x$; equivalently, all its eigenvalues are $\ge0$. *(F7)*
<!-- concept: positive-semidefinite-matrices -->

**Prediction-function contract** — The exact required signature and output of a submitted prediction function; any violation scores zero. *(C11)*
<!-- concept: prediction-function-contract -->

**Principal component analysis (PCA)** — Projecting centered data onto the directions of greatest variance to reduce its dimension. *(C9)*
<!-- concept: pca -->

**Projection** — The closest point to a vector along a direction or within a subspace; onto a unit vector $u$ it is $(v\cdot u)\,u$. *(F2)*
<!-- concept: projection -->

**Random seed** — A starting value for a random number generator; fixing it makes every run produce the same random numbers. *(F1)*
<!-- concept: random-seeding -->

**Random variable** — A quantity whose value is decided by chance, described by the probabilities of its possible values. *(F5)*
<!-- concept: random-variables -->

**Rank** — The number of linearly independent columns (equivalently rows) of a matrix: the dimension of its column space. *(F4)*
<!-- concept: rank -->

**Receptive field** — The region of the input image that can affect one unit of a feature map. *(C10)*
<!-- concept: receptive-field -->

**ReLU** — The activation $\mathrm{relu}(z)=\max(0,z)$. *(C6)*
<!-- concept: relu-activation -->

**`requires_grad`** — The tensor flag that tells autograd to track operations on the tensor and compute its gradient. *(C7)*
<!-- concept: requires-grad -->

**Residual** — What is left after a projection or a fit: the vector or value minus its approximation. *(F2)*
<!-- concept: residuals -->

**ResNet** — A deep convolutional network built from residual blocks whose skip connections add a block's input to its output. *(C10)*
<!-- concept: resnet-architecture -->

**Sampling simulation** — Estimating a probability or expectation by drawing many seeded random samples and averaging. *(F5)*
<!-- concept: sampling-simulation -->

**scikit-learn pipeline** — A `Pipeline` that chains preprocessing and a model, so both are fit only on training data. *(C4)*
<!-- concept: sklearn-pipelines -->

**Seaborn plotting** — Statistical plots such as `sns.histplot` and `sns.scatterplot`, drawn onto a given matplotlib axes with named arguments. *(F1)*
<!-- concept: seaborn-programming -->

**Similarity matrix** — The matrix of similarities between every pair of items, such as all pairwise cosine similarities. *(C5)*
<!-- concept: similarity-matrices -->

**Singular value** — A diagonal entry $\sigma_k\ge0$ of $\Sigma$ in the SVD; it measures how much the matrix stretches along one direction. *(F6)*
<!-- concept: singular-values -->

**Singular value decomposition (SVD)** — Writing any matrix as $U\Sigma V^{\mathsf T}$, with orthonormal columns in $U$ and $V$ and nonnegative singular values in $\Sigma$. *(F6)*
<!-- concept: svd -->

**Softmax** — Turning a vector of scores into probabilities: $p_c=e^{z_c}/\sum_k e^{z_k}$. *(C8)*
<!-- concept: softmax -->

**Sparsity** — Having many entries exactly zero; a sparse weight vector uses only a few features. *(C2)*
<!-- concept: sparsity -->

**Spectral decomposition** — Writing a symmetric matrix as $Q\Lambda Q^{\mathsf T}$, with orthonormal eigenvectors in $Q$ and eigenvalues in $\Lambda$. *(F6)*
<!-- concept: spectral-decomposition -->

**Stochastic gradient descent** — Gradient descent using the gradient of a small random batch, a noisy but cheap estimate of the full gradient. *(C3)*
<!-- concept: stochastic-gd -->

**Sum-of-squares gradient** — The gradient of $\sum_i(\hat y_i-y_i)^2$, found with the chain rule: $\sum_i 2(\hat y_i-y_i)\,\partial\hat y_i$. *(F3)*
<!-- concept: sum-of-squares-gradients -->

**Supervised and unsupervised learning** — Supervised learning fits labeled targets; unsupervised learning finds structure, such as groups, in unlabeled data. *(C1)*
<!-- concept: supervised-vs-unsupervised -->

**Support vector machine (SVM)** — A classifier that separates classes with the widest possible margin, optionally through a kernel. *(C12)*
<!-- concept: svm -->

**Tabular feature engineering** — Building, encoding, and transforming table columns to give a model more useful inputs. *(C4)*
<!-- concept: tabular-feature-engineering -->

**Tensor shape tracing** — Following a tensor's shape through every layer, by hand and in code, to find shape bugs. *(C10)*
<!-- concept: tensor-shape-tracing -->

**Threshold activation** — A step function that outputs 1 when its input passes a threshold and 0 otherwise. *(C6)*
<!-- concept: threshold-activation -->

**Tokenization** — Splitting text into tokens, such as words, with stated rules for case, punctuation, and numerals. *(C5)*
<!-- concept: tokenization -->

**Torch optimizer** — An object such as `torch.optim.SGD` or `Adam` that updates parameters from their gradients. *(C8)*
<!-- concept: torch-optimizers -->

**Torch tensor** — PyTorch's array type, with a shape, a dtype, and a device, and optional gradient tracking. *(C7)*
<!-- concept: torch-tensors -->

**Trained MLP** — A multilayer perceptron certified to have learned: under a fixed seed its loss falls, its parameters move, and it behaves as intended. *(C8)*
<!-- concept: trained-mlp -->

**Train/test split** — Holding back part of the data, unseen during fitting, to estimate how a model performs on new data. *(C1)*
<!-- concept: train-test-split -->

**Transfer learning** — Reusing a network trained on one task as the starting point for another, usually with a new output head. *(C10)*
<!-- concept: transfer-learning -->

**Tree split criterion** — A measure, such as Gini impurity or entropy, used to choose the split that makes child nodes purest. *(C12)*
<!-- concept: tree-split-criteria -->

**Truncated SVD** — Keeping only the top singular directions of a data matrix, in practice with library routines. *(C9)*
<!-- concept: truncated-svd-practice -->

**UMAP** — A nonlinear method that maps data to a few dimensions by preserving each point's neighborhood graph. *(C9)*
<!-- concept: umap-concept -->

**Unit vector** — A vector of length 1; dividing a nonzero vector by its norm gives the unit vector in its direction. *(F2)*
<!-- concept: unit-vectors -->

**Variance** — $\operatorname{Var}(X)=E[(X-E[X])^2]$: the average squared distance from the mean. *(F5)*
<!-- concept: variance -->

**Variance of a sum** — $\operatorname{Var}(X+Y)=\operatorname{Var}X+\operatorname{Var}Y+2\operatorname{Cov}(X,Y)$; the covariance term vanishes for independent variables. *(F5)*
<!-- concept: variance-of-sums -->

**Vector norm** — The length of a vector; the Euclidean norm is $\lVert v\rVert=\sqrt{\sum_i v_i^2}$. *(F2)*
<!-- concept: vectors-and-norms -->

**Vectorization** — Replacing a Python loop with whole-array operations, which is shorter and much faster. *(F1)*
<!-- concept: vectorization -->

**Weight-initialization variance** — Choosing the spread of random initial weights from the layer width so signals neither vanish nor explode. *(C6)*
<!-- concept: weight-init-variance -->

**Word embedding** — A dense vector for each word, arranged so that words used in similar ways get nearby vectors. *(C5)*
<!-- concept: word-embeddings -->

**Writeup quality** — A short summary of approach, reasons, and alternatives in which every claim is backed by a printed number. *(C11)*
<!-- concept: writeup-quality -->
