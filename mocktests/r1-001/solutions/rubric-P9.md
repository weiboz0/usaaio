# P9 rubric fragment — 50 points

## Eligibility hard gates

Any one of these failures makes the score **0/50** before point scoring:

- The executed submission uses a non-kNN model family, hand-reimplements another family, or imports outside `sklearn`, `numpy`, `pandas`, and `matplotlib`.
- A fresh top-to-bottom run errors or depends on interactive execution order.
- Any prediction clause fails: `predict_labels` is not callable; does not accept a feature `DataFrame` of any length; does not return a `pd.Series`; changes length/order/index; or emits a label outside the training vocabulary.
- The final submitted predictor refits on test input, was not fit on all labeled rows, or uses held-back rows for modeling decisions.

## Scored work after the gates — 50 points

### Model and validation quality — 44 points

- **Validation methodology and reproducibility — 8 points.** Frozen seeded carve (2), stratification and macro-F1 (2), feature/model decisions use labeled fitting data without heldout leakage (2), deterministic replay plus honest limitation (2).
- **kNN investigation and final recipe — 8 points.** Meaningful scaled baseline (2), bounded comparison of kNN preprocessing/features/distances/hyperparameters (2), results are recorded and the accepted choice follows them (2), accepted model is refit on all labeled rows and prediction does not refit (2).
- **Heldout predictive performance — 28 points.** Apply the course/mock-test's official f1-macro-to-points mapping to the grader-only heldout predictions.

**REGISTER AMBIGUITY:** neither `p09.ipynb` nor the `r1-001-p09` manifest entry supplies performance bands or a formula for the 28-point heldout component. This fragment therefore preserves the 28-point allocation but does not fabricate cutoffs. A coordinator must bind an official mapping before summative grading; until then, report raw heldout f1-macro alongside the 16 auditable methodology/model points.

### Required summary cell — 6 points

Apply the C10 register mechanically, one point each:

- **W-A1:** full recipe: preprocessing, kNN family with hyperparameter values, and feature set.
- **W-A2:** validation carve size, seed policy, stratification, and submitted recipe's validation metric value.
- **W-B1:** model choice grounded in a property of this dataset.
- **W-B2:** macro-F1 grounded in the class imbalance/task priority.
- **W-C1:** at least one concrete alternative with a measured outcome or precise rejection reason.
- **W-C2:** an honest limitation or next step.

The exemplar summary earns **6/6**: every item above is a checkable sentence tied to notebook output.
