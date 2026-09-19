from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
PRACTICE = BOOK1_ROOT / "units" / "C12-classical-models" / "practice"
PROBLEMS = tuple(f"p{index:02d}" for index in range(1, 31))

P20_ASCENDING_SEEDS = np.array([20260804, 20260805, 20260806], dtype=np.int64)
P20_PERMUTED_SEEDS = np.array([20260805, 20260804, 20260806], dtype=np.int64)
P20_SELECTOR_FIXTURES = (
    (
        "absolute_and_relative_near_tie",
        P20_ASCENDING_SEEDS,
        np.array([1.0 + 5e-11, 1.0, 2.0], dtype=np.float64),
        0,
        20260804,
    ),
    (
        "relative_term_required",
        P20_ASCENDING_SEEDS,
        np.array([1000.0 + 5e-6, 1000.0, 2000.0], dtype=np.float64),
        0,
        20260804,
    ),
    (
        "absolute_term_required",
        P20_ASCENDING_SEEDS,
        np.array([5e-11, 0.0, 2.0], dtype=np.float64),
        0,
        20260804,
    ),
    (
        "inclusive_absolute_boundary",
        P20_ASCENDING_SEEDS,
        np.array([1e-10, 0.0, 2.0], dtype=np.float64),
        0,
        20260804,
    ),
    (
        "outside_relative_boundary",
        P20_ASCENDING_SEEDS,
        np.array([1000.0 + 2e-5, 1000.0, 2000.0], dtype=np.float64),
        1,
        20260805,
    ),
    (
        "permuted_secondary_key",
        P20_PERMUTED_SEEDS,
        np.array([1.0, 1.0 + 5e-11, 2.0], dtype=np.float64),
        1,
        20260804,
    ),
)

P20_ISCLOSE_EXPRESSION = (
    "np.isclose(inertias, minimum, atol=atol, rtol=rtol)"
)
P20_SECONDARY_KEY_ASSIGNMENT = (
    "best_index = int(candidates[np.argmin(seeds[candidates])])"
)
P20_SELECTOR_MUTANTS = (
    (
        "raw_argmin",
        P20_SECONDARY_KEY_ASSIGNMENT,
        "best_index = int(np.argmin(inertias))",
    ),
    (
        "exact_equality",
        P20_ISCLOSE_EXPRESSION,
        "inertias == minimum",
    ),
    (
        "missing_relative_tolerance",
        "rtol=rtol",
        "rtol=0.0",
    ),
    (
        "missing_absolute_tolerance",
        "atol=atol",
        "atol=0.0",
    ),
    (
        "strict_boundary",
        P20_ISCLOSE_EXPRESSION,
        "np.abs(inertias - minimum) < atol + rtol * abs(minimum)",
    ),
    (
        "all_candidates_eligible",
        P20_ISCLOSE_EXPRESSION,
        "np.ones_like(inertias, dtype=bool)",
    ),
    (
        "first_eligible",
        P20_SECONDARY_KEY_ASSIGNMENT,
        "best_index = int(candidates[0])",
    ),
    (
        "largest_seed",
        "np.argmin(seeds[candidates])",
        "np.argmax(seeds[candidates])",
    ),
)


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


def _p20_selector_cell_source() -> str:
    matches = [
        _source(cell)
        for cell in _notebook("p20", solution=True)["cells"]
        if cell["cell_type"] == "code"
        and "def _lowest_seed_near_minimum" in _source(cell)
    ]
    assert len(matches) == 1, "p20 needs one dedicated selector code cell"
    return matches[0]


def _execute_p20_selector_cell(source: str | None = None) -> dict[str, object]:
    namespace: dict[str, object] = {}
    exec(  # noqa: S102 - execute the production selector cell in isolation
        compile(source or _p20_selector_cell_source(), "p20-selector-cell", "exec"),
        namespace,
    )
    return namespace


def _function_node(source: str, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1, f"expected exactly one definition of {name}"
    return matches[0]


def _mutate_p20_selector_cell(old: str, new: str) -> str:
    source = _p20_selector_cell_source()
    assert source.count(old) == 1, f"mutation target is not unique: {old}"
    return source.replace(old, new, 1)


def _p20_selector_outcomes(
    selector: object,
) -> list[tuple[int, int]]:
    outcomes: list[tuple[int, int]] = []
    for _, seeds, inertias, _, _ in P20_SELECTOR_FIXTURES:
        index = selector(seeds, inertias, atol=1e-10, rtol=1e-8)  # type: ignore[operator]
        outcomes.append((index, int(seeds[index])))
    return outcomes


def test_p20_selector_cell_is_standalone_and_owns_shared_tolerances() -> None:
    source = _p20_selector_cell_source()
    tree = ast.parse(source)
    selector = _function_node(source, "_lowest_seed_near_minimum")

    assert any(
        isinstance(node, ast.Import)
        and any(alias.name == "numpy" and alias.asname == "np" for alias in node.names)
        for node in tree.body
    )
    assert [argument.arg for argument in selector.args.args] == ["seeds", "inertias"]
    assert selector.args.defaults == []
    assert [argument.arg for argument in selector.args.kwonlyargs] == ["atol", "rtol"]
    assert selector.args.kw_defaults == [None, None]
    assert [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    ] == ["_lowest_seed_near_minimum"]

    top_level_assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name)
    }
    assert top_level_assignments == {"ATOL", "RTOL"}

    all_code = _code("p20", solution=True)
    for name in ("ATOL", "RTOL"):
        definitions = [
            node
            for node in ast.walk(ast.parse(all_code))
            if isinstance(node, ast.Name)
            and node.id == name
            and isinstance(node.ctx, ast.Store)
        ]
        assert len(definitions) == 1, f"{name} must have one shared definition"
        assert any(
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
            for node in tree.body
        ), f"{name} must be defined in the selector cell"

    calls = [
        node
        for node in ast.walk(selector)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "np"
        and node.func.attr == "isclose"
    ]
    assert len(calls) == 1
    keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords}
    assert isinstance(keywords.get("atol"), ast.Name)
    assert keywords["atol"].id == "atol"
    assert isinstance(keywords.get("rtol"), ast.Name)
    assert keywords["rtol"].id == "rtol"

    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"_lowest_seed_near_minimum", "kmeans_stability_audit"}
        for node in ast.walk(tree)
    )
    namespace = _execute_p20_selector_cell(source)
    assert namespace["ATOL"] == 1e-10
    assert namespace["RTOL"] == 1e-8
    assert callable(namespace["_lowest_seed_near_minimum"])


def test_p20_audit_uses_the_selector_result_as_its_only_selection_path() -> None:
    code = _code("p20", solution=True)
    code_tree = ast.parse(code)
    audit = _function_node(code, "kmeans_stability_audit")

    selector_calls = [
        node
        for node in ast.walk(code_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_lowest_seed_near_minimum"
    ]
    assert len(selector_calls) == 1

    best_index_assignments = [
        node
        for node in ast.walk(audit)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "best_index"
            for target in node.targets
        )
    ]
    assert len(best_index_assignments) == 1
    assert sum(
        isinstance(node, ast.Name)
        and node.id == "best_index"
        and isinstance(node.ctx, ast.Store)
        for node in ast.walk(audit)
    ) == 1
    selector_call = best_index_assignments[0].value
    assert isinstance(selector_call, ast.Call)
    assert isinstance(selector_call.func, ast.Name)
    assert selector_call.func.id == "_lowest_seed_near_minimum"
    assert [ast.unparse(argument) for argument in selector_call.args] == [
        "seeds",
        "inertias",
    ]
    assert {
        keyword.arg: ast.unparse(keyword.value) for keyword in selector_call.keywords
    } == {"atol": "ATOL", "rtol": "RTOL"}

    best_seed_assignments = [
        node
        for node in ast.walk(audit)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "best_seed"
            for target in node.targets
        )
    ]
    assert len(best_seed_assignments) == 1
    assert sum(
        isinstance(node, ast.Name)
        and node.id == "best_seed"
        and isinstance(node.ctx, ast.Store)
        for node in ast.walk(audit)
    ) == 1
    assert ast.unparse(best_seed_assignments[0].value) == "int(seeds[best_index])"

    returns = [node for node in ast.walk(audit) if isinstance(node, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.Dict)
    returned = {
        key.value: value
        for key, value in zip(returns[0].value.keys, returns[0].value.values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert isinstance(returned["best_index"], ast.Name)
    assert returned["best_index"].id == "best_index"
    assert isinstance(returned["best_seed"], ast.Name)
    assert returned["best_seed"].id == "best_seed"


@pytest.mark.parametrize(
    ("_name", "seeds", "inertias", "expected_index", "expected_seed"),
    P20_SELECTOR_FIXTURES,
    ids=[fixture[0] for fixture in P20_SELECTOR_FIXTURES],
)
def test_p20_production_selector_pins_indices_and_mapped_seeds(
    _name: str,
    seeds: np.ndarray,
    inertias: np.ndarray,
    expected_index: int,
    expected_seed: int,
) -> None:
    namespace = _execute_p20_selector_cell()
    selector = namespace["_lowest_seed_near_minimum"]
    index = selector(seeds, inertias, atol=1e-10, rtol=1e-8)  # type: ignore[operator]

    assert type(index) is int
    assert index == expected_index
    assert int(seeds[index]) == expected_seed


@pytest.mark.parametrize(
    ("mutant_name", "old", "new"),
    P20_SELECTOR_MUTANTS,
    ids=[mutant[0] for mutant in P20_SELECTOR_MUTANTS],
)
def test_p20_selector_fixtures_kill_in_memory_mutants(
    mutant_name: str,
    old: str,
    new: str,
) -> None:
    mutated = _mutate_p20_selector_cell(old, new)
    namespace = _execute_p20_selector_cell(mutated)
    observed = _p20_selector_outcomes(namespace["_lowest_seed_near_minimum"])
    expected = [
        (expected_index, expected_seed)
        for _, _, _, expected_index, expected_seed in P20_SELECTOR_FIXTURES
    ]
    assert observed != expected, f"selector mutant survived: {mutant_name}"


def test_p20_solution_executes_with_the_deterministic_lowest_seed() -> None:
    namespace = _execute_solution("p20")
    audit = namespace["audit_p20"]
    assert audit["best_index"] == 0
    assert audit["best_seed"] == 20260804


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
