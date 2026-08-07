from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
PRACTICE = ROOT / "units" / "C12-classical-models" / "practice"


def _source(number: int) -> str:
    notebook = json.loads((PRACTICE / f"p{number:02}.ipynb").read_text())
    return "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", ""), list)
        else str(cell.get("source", ""))
        for cell in notebook["cells"]
    )


def _assigned_names(number: int) -> set[str]:
    notebook = json.loads((PRACTICE / f"p{number:02}.ipynb").read_text())
    names: set[str] = set()
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        tree = ast.parse(source)
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def test_integrative_statements_pin_exact_return_schemas() -> None:
    required = {
        18: [
            "`logistic_pipeline`", "`svm_pipeline`", "`logistic_probabilities`",
            "`logistic_scores`", "`logistic_predictions`", "`svm_scores`",
            "`svm_predictions`",
        ],
        19: [
            "`tree_models`", "`bagging_models`", "`tree_predictions`",
            "`bagging_predictions`", "`tree_accuracies`", "`bagging_accuracies`",
            "`tree_disagreement`", "`bagging_disagreement`",
            "`tree_mean_prediction_variance`", "`bagging_mean_prediction_variance`",
        ],
        20: [
            "`seeds`", "`models`", "`inertias`", "`iterations`", "`labels`",
            "`centers`", "`co_clustering`", "`best_index`", "`best_seed`",
            "`agreements_to_best`",
        ],
    }
    for number, fields in required.items():
        source = _source(number)
        assert "Return exactly one dictionary" in source
        for field in fields:
            assert field in source, (number, field)


def test_p19_pins_deterministic_bagging_and_base_tree_parameters() -> None:
    source = _source(19)
    for literal in (
        "`DecisionTreeClassifier(criterion=\"gini\", splitter=\"best\", max_depth=None,",
        "`BaggingClassifier(estimator=base_tree, n_estimators=25, max_samples=1.0,",
        "`max_features=1.0, bootstrap=True, bootstrap_features=False, oob_score=False,",
        "`warm_start=False, n_jobs=1, random_state=seed)`",
    ):
        assert literal in source


def test_p21_pins_nested_schema_and_default_sensitive_parameters() -> None:
    source = _source(21)
    compact = " ".join(source.split())
    assert "top-level keys are exactly `split`, `supervised`, and `kmeans`" in compact
    assert "exactly `logistic_regression`, `svm`, `decision_tree`, and `random_forest`" in compact
    for field in (
        "`candidate_names`", "`fold_scores`", "`mean_scores`", "`selected_index`",
        "`selected_params`", "`estimator`", "`test_predictions`", "`test_scores`",
        "`score_kind`", "`test_accuracy`",
    ):
        assert field in source
    for literal in (
        "`penalty=\"l2\"`", "`fit_intercept=True`", "`tol=1e-4`",
        "`shrinking=True`", "`probability=False`", "`break_ties=False`",
        "`criterion=\"gini\"`", "`splitter=\"best\"`", "`ccp_alpha=0.0`",
        "`max_features=\"sqrt\"`", "`bootstrap=True`", "`n_jobs=1`",
        "shuffle=True", "`dual=False`", "`max_leaf_nodes=None`",
        "`min_impurity_decrease=0.0`", "`oob_score=False`", "`warm_start=False`",
        "`max_samples=None`", "copy_x=True",
        "algorithm=\"lloyd\"",
        "`logistic_C_0.25`", "`logistic_C_1.0`",
        "`svm_linear_C_1.0`", "`svm_rbf_C_1.0_gamma_1.0`",
        "`tree_depth_2`", "`tree_depth_4`",
        "`forest_depth_3`", "`forest_depth_None`",
        "exactly `{\"C\": selected_C}`",
        "exactly `{\"kernel\": selected_kernel, \"C\": 1.0, \"gamma\": 1.0}`",
        "exactly `{\"max_depth\": selected_max_depth}`",
    ):
        assert literal in compact


def test_p21_defines_primary_kmeans_fit_and_supplies_public_scaffold() -> None:
    source = _source(21)
    for literal in (
        "primary fit is exactly `models[0]`",
        "seed `20260804`",
        "P21_FAMILY_ORDER",
        "P21_CANDIDATE_NAMES",
        "P21_KMEANS_SEEDS",
        "P21_PRIMARY_KMEANS_INDEX = 0",
    ):
        assert literal in source


def test_challenge_statements_pin_exact_return_schemas() -> None:
    required = {
        26: ["`losses`", "`probabilities`", "`gradients`", "`predictions`", "`accuracies`"],
        27: ["`kernel_matrix`", "`contributions`", "`scores`", "`predictions`"],
        29: [
            "`q1`", "`error1`", "`alpha1`", "`unnormalized_q2`", "`Z1`", "`q2`",
            "`error2`", "`alpha2`", "`unnormalized_q3`", "`Z2`", "`q3`",
            "`scores`", "`predictions`",
        ],
        30: ["`labels`", "`centroids`", "`objective_trace`", "`n_iter`", "`repair_count`"],
    }
    for number, fields in required.items():
        source = _source(number)
        assert re.search(r"exactly\s+one dictionary", source)
        for field in fields:
            assert field in source, (number, field)


def test_p28_pins_tree_path_and_certificate_containers() -> None:
    source = _source(28)
    assert "`trace_tree_paths(tree, X)`" in source
    assert "`split_ledger_p28`" in source
    assert "`certificates_p28`" in source
    for field in (
        "`node_path`", "`candidates`", "`feature`", "`threshold`", "`left_counts`",
        "`right_counts`", "`weighted_impurity`", "`gain`", "`steps`", "`prediction`",
    ):
        assert field in source


def test_required_top_level_submission_variables_are_literal_assignments() -> None:
    required = {
        18: {
            "comparison_p18", "logistic_accuracy_p18", "svm_accuracy_p18",
            "logistic_brier_p18", "t_validation_p18", "svm_margins_p18",
            "svm_mean_hinge_p18", "comparison_axes_p18",
        },
        19: {"audit_p19", "diagnosis_p19"},
        20: {"audit_p20", "interpretation_p20"},
        21: {"benchmark_p21", "comparison_axes_p21"},
        26: {"trace_p26", "analysis_p26"},
        27: {"result_p27", "first_probe_derivation_p27", "support_audit_p27"},
        28: {"tree_p28", "split_ledger_p28", "predictions_p28", "paths_p28", "certificates_p28"},
        29: {"ledger_p29", "symbolic_ledger_p29", "interpretation_p29"},
        30: {
            "runs_p30", "selected_index_p30", "co_clustering_p30",
            "pairwise_agreements_p30", "sklearn_model_p30", "sklearn_inertia_p30",
            "sklearn_centers_p30", "center_matching_p30", "comparison_p30",
        },
    }
    for number, expected in required.items():
        assert expected <= _assigned_names(number), (number, expected - _assigned_names(number))


def test_session1_teaches_the_complete_p06_validation_policy_executably() -> None:
    path = ROOT / "units" / "C12-classical-models" / "lessons" / "01-logistic-regression.ipynb"
    notebook = json.loads(path.read_text())
    source = "\n".join(str(cell.get("source", "")) for cell in notebook["cells"])
    for marker in (
        "numeric array", "must be nonempty", "must contain only finite values",
        "must contain only 0 or 1", "z and y must have the same shape",
    ):
        assert marker in source
    for invalid_probe in (
        "bad_nonnumeric_p06", "bad_shape_p06", "bad_empty_p06",
        "bad_nonfinite_p06", "bad_label_p06",
    ):
        assert invalid_probe in source


def test_session3_teaches_alpha_box_cases_and_limits() -> None:
    path = ROOT / "units" / "C12-classical-models" / "lessons" / "03-kernel-svm-and-dual-intuition.ipynb"
    notebook = json.loads(path.read_text())
    source = "\n".join(str(cell.get("source", "")) for cell in notebook["cells"])
    for marker in (
        "$\\alpha_i=0$", "$0<\\alpha_i<C$", "$\\alpha_i=C$",
        "does not prove", "complementary slackness",
    ):
        assert marker in source
