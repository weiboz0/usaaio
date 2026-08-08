from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
PRACTICE = ROOT / "units" / "C12-classical-models" / "practice"
PROBLEMS = tuple(f"p{index:02d}" for index in range(1, 31))


def _source(cell: dict[str, object]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _notebook(problem: str, *, solution: bool) -> dict[str, object]:
    suffix = "_solution" if solution else ""
    return json.loads((PRACTICE / f"{problem}{suffix}.ipynb").read_text())


def _code(problem: str, *, solution: bool) -> str:
    return "\n".join(
        _source(cell)
        for cell in _notebook(problem, solution=solution)["cells"]
        if cell["cell_type"] == "code"
    )


def _probe_assignments(problem: str, *, solution: bool) -> dict[str, str]:
    """Return non-placeholder top-level pNN assignments."""
    tree = ast.parse(_code(problem, solution=solution))
    assignments: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id.endswith(f"_{problem}"):
                value = node.value
                if isinstance(value, ast.Constant) and value.value in (None, ""):
                    continue
                assignments[target.id] = ast.dump(node, include_attributes=False)
    return assignments


def _execute_solution(problem: str) -> dict[str, object]:
    namespace: dict[str, object] = {}
    for cell_index, cell in enumerate(_notebook(problem, solution=True)["cells"]):
        if cell["cell_type"] == "code":
            exec(  # noqa: S102 - execute the notebook's actual answer-check cells
                compile(_source(cell), f"{problem}_solution.ipynb:cell-{cell_index}", "exec"),
                namespace,
            )
    return namespace


@pytest.mark.parametrize("problem", PROBLEMS)
def test_statement_notebooks_have_no_stored_outputs(problem: str) -> None:
    notebook = _notebook(problem, solution=False)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell.get("outputs", []) == []
            assert cell.get("execution_count") is None


@pytest.mark.parametrize("problem", PROBLEMS)
def test_solution_ends_with_executable_answer_check(problem: str) -> None:
    cells = _notebook(problem, solution=True)["cells"]
    assert cells[-2]["cell_type"] == "markdown"
    assert _source(cells[-2]).strip() == "### Answer check"
    assert cells[-1]["cell_type"] == "code"
    assert "assert " in _source(cells[-1])


@pytest.mark.parametrize(
    "problem",
    (
        "p06", "p07", "p08", "p09", "p10", "p11", "p12", "p13",
        "p18", "p19", "p20", "p21", "p26", "p27", "p28", "p29", "p30",
    ),
)
def test_solution_preserves_statement_probe_assignments(problem: str) -> None:
    declared = _probe_assignments(problem, solution=False)
    assert declared
    solution = _probe_assignments(problem, solution=True)
    assert {name: solution[name] for name in declared} == declared


@pytest.mark.parametrize(
    ("problem", "target_family", "check_family"),
    (
        ("p07", "C12-p07-logistic-mean-factor", "C12-p07-logistic-training"),
        ("p08", "C12-p08-signed-hinge-branch", "C12-p08-hinge-subgradient"),
        ("p10", "C12-p10-best-split", "C12-p10-best-split"),
        ("p13", "C12-p13-centroid-update", "C12-p13-lloyd-update"),
        ("p29", "C12-p29-weight-update", "C12-p29-adaboost-ledger"),
    ),
)
def test_mutation_family_markers_are_paired(
    problem: str, target_family: str, check_family: str
) -> None:
    code = _code(problem, solution=True)
    assert code.count(f"PLAN018_MUTATION_TARGET: {target_family}") == 1
    assert code.count(f"PLAN018_ANSWER_CHECK: {check_family}") == 1


def test_five_family_answer_checks_pin_independent_references() -> None:
    p07 = _execute_solution("p07")["result_p07"]
    assert np.allclose(p07["w"], [3.433187300731305, 1.657175809164489], atol=1e-10, rtol=1e-8)
    assert np.isclose(p07["b"], -0.13786707666108447, atol=1e-10, rtol=1e-8)
    assert np.isclose(p07["losses"][-1], 0.04833379931283665, atol=1e-10, rtol=1e-8)

    p08 = _execute_solution("p08")["result_p08"]
    assert np.allclose(p08["margins"], [0.9, 0.4, 0.75, 1.2], atol=1e-12, rtol=1e-10)
    assert np.isclose(p08["objective"], 0.55625, atol=1e-12, rtol=1e-10)
    assert np.allclose(p08["grad_w"], [-0.61875, 0.175], atol=1e-12, rtol=1e-10)

    p10 = _execute_solution("p10")["split_p10"]
    assert p10["feature"] == 0
    assert np.isclose(p10["threshold"], 2.5, atol=1e-12, rtol=1e-10)
    assert np.isclose(p10["weighted_impurity"], 0.0, atol=1e-12, rtol=1e-10)
    assert np.isclose(p10["gain"], 0.5, atol=1e-12, rtol=1e-10)

    p13_namespace = _execute_solution("p13")
    assert np.array_equal(p13_namespace["labels_p13"], [0, 1, 0, 2, 2, 2])
    assert np.allclose(
        p13_namespace["centroids_p13"],
        [[0.5, 0.5], [0.0, 2.0], [25.0 / 3.0, 9.0]],
        atol=1e-10,
        rtol=1e-8,
    )
    assert np.allclose(
        p13_namespace["objective_trace_p13"],
        [11.0 / 3.0, 11.0 / 3.0],
        atol=1e-10,
        rtol=1e-8,
    )

    p29 = _execute_solution("p29")["ledger_p29"]
    assert np.isclose(p29["error1"], 0.25, atol=1e-12, rtol=1e-10)
    assert np.isclose(p29["error2"], 1.0 / 6.0, atol=1e-12, rtol=1e-10)
    assert np.allclose(p29["q2"], [1 / 6, 1 / 2, 1 / 6, 1 / 6], atol=1e-12, rtol=1e-10)
    assert np.allclose(p29["q3"], [0.1, 0.3, 0.5, 0.1], atol=1e-12, rtol=1e-10)


@pytest.mark.parametrize("bad_learning_rate", ["0.2", True, np.bool_(False)])
def test_p07_rejects_nonnumeric_and_boolean_learning_rates(
    bad_learning_rate: object,
) -> None:
    namespace = _execute_solution("p07")
    with pytest.raises(ValueError):
        namespace["train_logistic"](
            namespace["X_p07"],
            namespace["y_p07"],
            learning_rate=bad_learning_rate,
        )


@pytest.mark.parametrize("bad_steps", ["300", True, np.bool_(False)])
def test_p07_rejects_nonnumeric_and_boolean_steps(bad_steps: object) -> None:
    namespace = _execute_solution("p07")
    with pytest.raises(ValueError):
        namespace["train_logistic"](
            namespace["X_p07"], namespace["y_p07"], steps=bad_steps
        )


@pytest.mark.parametrize("parameter", ["b", "C", "learning_rate"])
@pytest.mark.parametrize("bad_value", ["1.0", True, np.bool_(False)])
def test_p08_rejects_nonnumeric_and_boolean_scalars(
    parameter: str, bad_value: object
) -> None:
    namespace = _execute_solution("p08")
    arguments = {"b": namespace["b_p08"], "C": 1.5, "learning_rate": 0.1}
    arguments[parameter] = bad_value
    with pytest.raises(ValueError):
        namespace["hinge_step"](
            namespace["X_p08"],
            namespace["t_p08"],
            namespace["w_p08"],
            **arguments,
        )


def test_p15_answer_check_pins_all_three_kkt_box_regimes() -> None:
    namespace = _execute_solution("p15")
    witnesses = namespace["kkt_witnesses_p15"]

    assert np.array_equal(witnesses["alpha"], [0.0, 0.0, 0.4, 1.0, 1.0, 1.0])
    assert np.array_equal(witnesses["xi"], [0.0, 0.0, 0.0, 0.0, 0.5, 2.0])
    assert np.array_equal(witnesses["margin"], [1.2, 1.0, 1.0, 1.0, 0.5, -1.0])
    assert namespace["kkt_regimes_p15"] == (
        "zero-outside",
        "zero-equality",
        "middle-margin",
        "saturated-margin",
        "saturated-inside",
        "saturated-misclassified",
    )


def test_p17_repair_witness_pins_combined_nonincrease() -> None:
    namespace = _execute_solution("p17")
    witness = namespace["repair_witness_p17"]

    assert np.array_equal(witness["assignment_labels"], [0, 0, 2])
    assert np.array_equal(witness["repaired_labels"], [0, 1, 2])
    assert np.isclose(witness["assignment_wcss"], 4.0, atol=1e-12, rtol=1e-10)
    assert np.isclose(witness["repaired_wcss"], 0.0, atol=1e-12, rtol=1e-10)


@pytest.mark.parametrize("problem", ["p22", "p23", "p24", "p25"])
def test_scenario_solutions_expose_structured_audit_evidence(problem: str) -> None:
    namespace = _execute_solution(problem)
    structured_name = {
        "p22": "audit_protocol_p22",
        "p23": "control_plan_p23",
        "p24": "team_decisions_p24",
        "p25": "audit_protocol_p25",
    }[problem]
    assert isinstance(namespace[structured_name], dict)


def test_p25_protocol_pins_reproducible_clustering_controls() -> None:
    protocol = _execute_solution("p25")["audit_protocol_p25"]

    assert protocol["primary_k"] == 4
    assert protocol["k_grid"] == (2, 3, 4, 5, 6)
    assert protocol["init"] == "k-means++"
    assert protocol["n_init"] == 50
    assert protocol["seed"] == 20260804
    assert protocol["scaling_fit_scope"] == "modeling sample only"
    assert protocol["empty_cluster_policy"] == "farthest eligible row, then row index"


def test_p22_cost_threshold_remains_symbolic() -> None:
    namespace = _execute_solution("p22")

    assert namespace["cost_assumptions_p22"] == ("C_FP > 0", "C_FN > C_FP")
    assert namespace["threshold_expression_p22"] == "C_FP / (C_FP + C_FN)"
    assert namespace["threshold_properties_p22"] == ("threshold > 0", "threshold < 1/2")

    source = _code("p22", solution=True)
    assert "cost_fp_p22 = 1.0" not in source
    assert "cost_fn_p22 = 4.0" not in source
    assert "0.2" not in source
