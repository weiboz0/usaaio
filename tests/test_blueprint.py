from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.checks.blueprint import check_blueprint


def write_repo(root: Path, problems: list[dict], status: str | None = "final") -> None:
    root.joinpath("mocktests").mkdir()
    Path("mocktests/blueprint.yaml").resolve().read_text()
    root.joinpath("mocktests/blueprint.yaml").write_text(Path("mocktests/blueprint.yaml").read_text())
    root.joinpath("syllabus.md").write_text(Path("syllabus.md").read_text())
    test_dir = root / "mocktests" / "r1-001"
    (test_dir / "data").mkdir(parents=True)
    (test_dir / "data" / "gen.py").write_text("print('ok')\n")
    status_line = "" if status is None else f"status: {status}\n"
    problem_text = "\n".join(render_problem(problem) for problem in problems)
    test_dir.joinpath("manifest.yaml").write_text(
        f"""
test: r1-001
blueprint_version: 1
generated: 2026-08-15
{status_line}generation_parameters: {{}}
duration_minutes: 180
total_points: 300
time_budget: {{concept-block: 20, math-computation: 25, integrative-arc: 55, engineering: 45, open-ended-notebook: 35}}
problems:
{problem_text}
"""
    )


def render_problem(problem: dict) -> str:
    lines = [f"  - id: {problem['id']}"]
    for key, value in problem.items():
        if key == "id":
            continue
        yaml_key = "adapted-from" if key == "adapted_from" else key
        if isinstance(value, list):
            rendered = "[" + ", ".join(str(item) for item in value) + "]"
        elif isinstance(value, dict):
            rendered = "{" + ", ".join(f"{k}: {v}" for k, v in value.items()) + "}"
        else:
            rendered = str(value)
        lines.append(f"    {yaml_key}: {rendered}")
    return "\n".join(lines)


def valid_problems() -> list[dict]:
    rows: list[dict] = []
    rows += [
        problem(
            "p01",
            "concept-block",
            "ml-concepts",
            "C1-ml-fundamentals",
            "supervised-vs-unsupervised",
            5,
            "intro",
            "theory",
        )
        for _ in range(6)
    ]
    rows += [
        problem(
            "p01",
            "concept-block",
            "ml-concepts",
            "C1-ml-fundamentals",
            "supervised-vs-unsupervised",
            20,
            "intro",
            "theory",
        )
    ]
    rows += [
        problem("p02", "math-computation", "linear-algebra", "F2-vectors", "vectors-and-norms", 5, "intro", "theory")
        for _ in range(5)
    ]
    rows += [
        problem("p02", "math-computation", "linear-algebra", "F2-vectors", "vectors-and-norms", 15, "core", "theory"),
        problem("p02", "math-computation", "probability-statistics", "F5-probability", "expectation", 5, "core", "theory"),
    ]
    rows += [
        problem("p03", "integrative-arc", "numpy", "F1-scientific-python", "numpy-arrays", 5, "core", "programming")
        for _ in range(7)
    ]
    rows += [
        problem("p03", "integrative-arc", "numpy", "F1-scientific-python", "numpy-arrays", 5, "core", "theory")
        for _ in range(4)
    ]
    rows += [
        problem("p04", "integrative-arc", "nlp-embeddings", "C8-embeddings", "tokenization", 5, "core", "theory")
        for _ in range(3)
    ]
    rows += [
        problem("p05", "integrative-arc", "linear-algebra", "F2-vectors", "vectors-and-norms", 20, "core", "theory")
    ]
    rows += [
        problem("p06", "engineering", "pytorch", "C6-pytorch", "torch-tensors", 20, "advanced", "programming")
        for _ in range(2)
    ]
    rows += [
        problem("p06", "engineering", "pytorch", "C6-pytorch", "torch-tensors", 5, "advanced", "programming")
        for _ in range(2)
    ]
    rows += [
        problem("p07", "engineering", "cnn-vision", "C7-cnn-transfer", "convolution", 5, "advanced", "programming")
        for _ in range(3)
    ]
    rows += [
        problem("p08", "open-ended-notebook", "applied-ml", "C4-classical-ml-practice", "knn", 5, "advanced", "programming")
        for _ in range(4)
    ]
    rows += [
        problem("p08", "open-ended-notebook", "applied-ml", "C4-classical-ml-practice", "knn", 30, "core", "programming")
    ]
    for index, row in enumerate(rows, start=1):
        row["id"] = f"{row['id']}-{index}"
    return rows


def problem(
    pid: str,
    section: str,
    cluster: str,
    unit: str,
    concept: str,
    points: int,
    difficulty: str,
    ptype: str,
) -> dict:
    return {
        "id": pid,
        "section": section,
        "units": [unit],
        "concepts": [concept],
        "cluster": cluster,
        "points": points,
        "difficulty": difficulty,
        "type": ptype,
        "answer_form": "short",
        "provenance": "original",
        "spec": "non-empty spec",
        "answer_key": "A",
    }


def broken(mutator):
    rows = valid_problems()
    mutator(rows)
    return rows


def test_blueprint_pass_on_fixture_test(tmp_path):
    write_repo(tmp_path, valid_problems())
    assert check_blueprint(tmp_path).ok


def test_blueprint_flags_section_out_of_range(tmp_path):
    def mutate(rows):
        for row in rows[:3]:
            row.update(
                section="engineering",
                cluster="pytorch",
                concepts=["torch-tensors"],
                units=["C6-pytorch"],
            )

    write_repo(tmp_path, broken(mutate))
    assert any("section concept-block" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_topic_distribution_breach(tmp_path):
    write_repo(tmp_path, broken(lambda rows: rows[0].update(cluster="numpy")))
    assert any("topic" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_missing_adapted_tag(tmp_path):
    def mutate(rows):
        rows[0]["provenance"] = "adapted"
    write_repo(tmp_path, broken(mutate))
    assert any("adapted missing" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_atom_share_breach(tmp_path):
    def mutate(rows):
        for row in rows:
            if row["points"] == 5:
                row["points"] = 10

    write_repo(tmp_path, broken(mutate))
    assert any("five-point atom" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_programming_share_breach(tmp_path):
    write_repo(tmp_path, broken(lambda rows: [row.update(type="theory") for row in rows if row["type"] == "programming"]))
    assert any("programming share" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_difficulty_band_breach(tmp_path):
    write_repo(tmp_path, broken(lambda rows: [row.update(difficulty="advanced") for row in rows[:20]]))
    assert any("difficulty" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_provenance_share_breach(tmp_path):
    write_repo(tmp_path, broken(lambda rows: [row.update(provenance="adapted", adapted_from="x") for row in rows[:20]]))
    assert any("original provenance" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_invalid_dominant_cluster(tmp_path):
    write_repo(tmp_path, broken(lambda rows: rows[0].update(cluster="numpy")))
    assert any("invalid dominant cluster" in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_flags_section_cluster_violation(tmp_path):
    def mutate(rows):
        rows[0].update(section="math-computation")
    write_repo(tmp_path, broken(mutate))
    assert any("cluster not allowed in section" in error for error in check_blueprint(tmp_path).errors)


@pytest.mark.parametrize(
    ("name", "mutator", "expected"),
    [
        ("subpart count", lambda rows: [rows.pop() for _ in range(9)], "subparts"),
        ("problem count", lambda rows: rows.clear(), "problem_count"),
        ("missing spec", lambda rows: rows[0].update(spec=""), "missing spec"),
        ("missing answer_key", lambda rows: rows[0].update(answer_key=""), "missing answer_key"),
        ("missing generator_script", lambda rows: rows[0].update(data={"generator_script": "data/missing.py"}), "missing generator_script"),
        ("time-budget sum", lambda rows: None, "time_budget"),
    ],
)
def test_blueprint_flags_remaining_invariants_parametric(tmp_path, name, mutator, expected):
    rows = copy.deepcopy(valid_problems())
    mutator(rows)
    write_repo(tmp_path, rows)
    if name == "time-budget sum":
        path = tmp_path / "mocktests" / "r1-001" / "manifest.yaml"
        path.write_text(path.read_text().replace("open-ended-notebook: 35", "open-ended-notebook: 34"))
    assert any(expected in error for error in check_blueprint(tmp_path).errors)


def test_blueprint_vacuous_without_mocktests(tmp_path):
    (tmp_path / "mocktests").mkdir()
    (tmp_path / "mocktests" / "blueprint.yaml").write_text(Path("mocktests/blueprint.yaml").read_text())
    (tmp_path / "syllabus.md").write_text(Path("syllabus.md").read_text())
    assert check_blueprint(tmp_path).ok
