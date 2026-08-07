from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

import yaml

from tools.checks.blueprint import check_blueprint
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.new_mocktest import scaffold_mocktest
from tools.checks.overlap import check_overlap
from tools.checks.prereq import check_prereq
from tools.model import load_syllabus, load_unit_manifests

ROOT = Path(__file__).resolve().parents[1]

NEW_CONCEPT_CLUSTERS = {
    "seaborn-programming": "python-scientific",
    "colab-markdown-solution-authoring": "competition-craft",
    "markdown-code-snippets": "competition-craft",
    "markdown-math-formulae": "competition-craft",
    "colab-coding-submission": "competition-craft",
    "cpu-and-gpu-round-boundary": "competition-craft",
    "conditional-probability": "probability-statistics",
    "bayes-rule": "probability-statistics",
    "hoeffding-inequality": "probability-statistics",
    "linear-regression-estimator-derivation": "ml-concepts",
    "ols-rank-identifiability-and-pseudoinverse": "ml-concepts",
    "pca-centered-covariance-eigenproblem-derivation": "ml-concepts",
    "numpy-pca-class-from-scratch": "ml-concepts",
    "pca-black-box-insufficiency": "ml-concepts",
    "positive-semidefinite-matrices": "linear-algebra",
    "kernel-validity": "linear-algebra",
    "convex-sets": "linear-algebra",
    "convex-functions": "calculus-multivar",
    "first-order-optimality": "calculus-multivar",
    "lagrangians": "calculus-multivar",
    "optimization-duality": "calculus-multivar",
}

EXPECTED_UNIT_SHAPES = {
    "F1-scientific-python": ([75, 90, 75, 70], 24, (310, 515, 50)),
    "C10-competition-craft": ([80, 85, 85, 85], 24, (335, 730, 55)),
    "F5-probability": ([80, 85, 85, 85, 80], 25, (415, 650, 55)),
    "C2-linear-models": ([85, 90, 85], 24, (260, 590, 55)),
    "C9-dimensionality-reduction": ([80, 90, 85, 85], 24, (340, 600, 60)),
    "F7-kernels-convex-optimization": ([85, 85, 85, 85], 20, (340, 640, 45)),
}

PLAN016_C10_PROMOTED_CONCEPTS = (
    "colab-markdown-solution-authoring",
    "markdown-code-snippets",
    "markdown-math-formulae",
    "colab-coding-submission",
    "cpu-and-gpu-round-boundary",
)

F1_SEABORN_ARRAY_ONLY_FILES = {
    Path("lesson.ipynb"),
    Path("lessons/01-arrays-and-indexing.ipynb"),
    Path("lessons/02-broadcasting-and-vectorization.ipynb"),
    Path("lessons/03-randomness-and-plotting.ipynb"),
    Path("lessons/04-seaborn-with-arrays.ipynb"),
    Path("review.ipynb"),
    Path("practice/p22.ipynb"),
    Path("practice/p22_solution.ipynb"),
    Path("practice/p23.ipynb"),
    Path("practice/p23_solution.ipynb"),
    Path("practice/p24.ipynb"),
    Path("practice/p24_solution.ipynb"),
}

C9_PLAN016_CHANGED_NOTEBOOKS = (
    Path("lesson.ipynb"),
    Path("lessons/01-pca.ipynb"),
    Path("lessons/02-pca-covariance-and-numpy-class.ipynb"),
    Path("lessons/03-truncated-svd-practice.ipynb"),
    Path("lessons/04-maps-and-structure.ipynb"),
    Path("review.ipynb"),
    *(Path(f"practice/p{number:02d}.ipynb") for number in range(20, 25)),
)


def _manifest(unit_id: str) -> dict[str, object]:
    return yaml.safe_load((ROOT / "units" / unit_id / "manifest.yaml").read_text())


def _canonical_syllabus_yaml() -> dict[str, object]:
    text = (ROOT / "syllabus.md").read_text()
    fenced = re.search(
        r"<!-- syllabus-canonical -->\s*```yaml\n(.*?)\n```", text, re.DOTALL
    )
    assert fenced is not None
    return yaml.safe_load(fenced.group(1))


def _syllabus_narrative() -> str:
    text = (ROOT / "syllabus.md").read_text()
    canonical_end = re.search(
        r"<!-- syllabus-canonical -->\s*```yaml\n.*?\n```", text, re.DOTALL
    )
    assert canonical_end is not None
    return text[canonical_end.end() :]


def _narrative_section(narrative: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\n\n(.*?)(?=^## |\Z)",
        narrative,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def seed_repo(root: Path) -> None:
    (root / "mocktests").mkdir(parents=True)
    (root / "mocktests" / "blueprint.yaml").write_text((ROOT / "mocktests" / "blueprint.yaml").read_text())
    (root / "syllabus.md").write_text((ROOT / "syllabus.md").read_text())


def test_plan016_c9_changed_markdown_has_no_decoded_tex_control_characters():
    unit = ROOT / "units" / "C9-dimensionality-reduction"
    forbidden = {"\t", "\f", "\r"}
    failures = []
    for relative in C9_PLAN016_CHANGED_NOTEBOOKS:
        notebook = json.loads((unit / relative).read_text())
        for cell_index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "markdown":
                continue
            source = "".join(cell.get("source", []))
            controls = sorted({repr(character) for character in source if character in forbidden})
            if controls:
                failures.append(f"{relative}: cell {cell_index}: {', '.join(controls)}")
    assert not failures, "decoded TeX control characters:\n" + "\n".join(failures)


def test_plan016_new_concepts_have_exact_clusters_and_single_owners():
    syllabus = load_syllabus(ROOT)

    assert len(NEW_CONCEPT_CLUSTERS) == 21
    assert {concept: syllabus.concepts.get(concept) for concept in NEW_CONCEPT_CLUSTERS} == (
        NEW_CONCEPT_CLUSTERS
    )

    syllabus_owner_counts = Counter(
        concept for unit in syllabus.units.values() for concept in unit.teaches
    )
    manifest_owner_counts = Counter(
        concept
        for manifest in load_unit_manifests(ROOT)
        for concept in manifest.concepts_taught
    )
    assert {concept: syllabus_owner_counts[concept] for concept in NEW_CONCEPT_CLUSTERS} == {
        concept: 1 for concept in NEW_CONCEPT_CLUSTERS
    }
    assert {concept: manifest_owner_counts[concept] for concept in NEW_CONCEPT_CLUSTERS} == {
        concept: 1 for concept in NEW_CONCEPT_CLUSTERS
    }


def test_plan016_manifests_have_exact_final_counts_and_minutes():
    for unit_id, (sessions, practice_count, minute_totals) in EXPECTED_UNIT_SHAPES.items():
        manifest = _manifest(unit_id)
        minutes = manifest["estimated_minutes"]
        assert minutes["lesson_sessions"] == sessions
        assert (minutes["lesson"], minutes["practice"], minutes["review"]) == minute_totals
        assert len(manifest["practice"]) == practice_count

    manifests = load_unit_manifests(ROOT)
    assert sum(len(manifest.practice) for manifest in manifests) == 383
    assert sum(len(manifest.lesson_sessions or []) for manifest in manifests) == 57
    assert sum(
        sum(_manifest(manifest.unit_id)["estimated_minutes"][field] for field in (
            "lesson",
            "practice",
            "review",
        ))
        for manifest in manifests
    ) == 14767


def test_plan016_existing_unit_register_extensions_are_exact():
    expected = {
        "F1-scientific-python": {
            "F1-p22": ("A", "constrained-coding", "intro", ["seaborn-programming"]),
            "F1-p23": ("B", "constrained-coding", "core", ["seaborn-programming"]),
            "F1-p24": (
                "C",
                "integrative",
                "advanced",
                ["seaborn-programming", "random-seeding", "aggregation-axis"],
            ),
        },
        "F5-probability": {
            "F5-p20": ("A", "drill", "intro", ["conditional-probability"]),
            "F5-p21": (
                "B",
                "constrained-coding",
                "core",
                ["conditional-probability", "bayes-rule"],
            ),
            "F5-p22": (
                "B",
                "proof",
                "core",
                ["conditional-probability", "bayes-rule"],
            ),
            "F5-p23": ("B", "mc-normal-form", "core", ["hoeffding-inequality"]),
            "F5-p24": (
                "B",
                "constrained-coding",
                "core",
                ["hoeffding-inequality"],
            ),
            "F5-p25": (
                "C",
                "integrative",
                "advanced",
                [
                    "conditional-probability",
                    "bayes-rule",
                    "hoeffding-inequality",
                    "sampling-simulation",
                ],
            ),
        },
        "C2-linear-models": {
            "C2-p19": (
                "B",
                "proof",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p20": (
                "B",
                "constrained-coding",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p21": (
                "C",
                "integrative",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p22": (
                "B",
                "proof",
                "advanced",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
            "C2-p23": (
                "B",
                "constrained-coding",
                "core",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
            "C2-p24": (
                "C",
                "challenge",
                "advanced",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
        },
        "C9-dimensionality-reduction": {
            "C9-p20": (
                "B",
                "proof",
                "core",
                ["pca-centered-covariance-eigenproblem-derivation"],
            ),
            "C9-p21": (
                "B",
                "proof",
                "advanced",
                ["pca-centered-covariance-eigenproblem-derivation"],
            ),
            "C9-p22": (
                "B",
                "constrained-coding",
                "core",
                ["numpy-pca-class-from-scratch", "pca-black-box-insufficiency"],
            ),
            "C9-p23": (
                "C",
                "integrative",
                "advanced",
                [
                    "pca-centered-covariance-eigenproblem-derivation",
                    "numpy-pca-class-from-scratch",
                    "pca-black-box-insufficiency",
                ],
            ),
            "C9-p24": (
                "C",
                "challenge",
                "advanced",
                ["numpy-pca-class-from-scratch", "pca-black-box-insufficiency"],
            ),
        },
    }
    for unit_id, expected_problems in expected.items():
        actual = {
            problem["id"]: (
                problem["set"],
                problem["type"],
                problem["difficulty"],
                problem["concepts"],
            )
            for problem in _manifest(unit_id)["practice"]
            if problem["id"] in expected_problems
        }
        assert actual == expected_problems

    c10 = {
        problem["id"]: problem for problem in _manifest("C10-competition-craft")["practice"]
    }
    expected_c10_concepts = {
        "C10-p15": ["writeup-quality", *PLAN016_C10_PROMOTED_CONCEPTS],
        "C10-p17": [
            "writeup-quality",
            *PLAN016_C10_PROMOTED_CONCEPTS,
            "train-test-split",
            "f1-macro",
            "knn",
            "feature-scaling",
            "sklearn-pipelines",
        ],
        "C10-p18": [
            "writeup-quality",
            *PLAN016_C10_PROMOTED_CONCEPTS,
            "train-test-split",
            "class-imbalance",
            "accuracy-precision-recall",
            "f1-macro",
            "knn",
            "feature-scaling",
            "sklearn-pipelines",
        ],
    }
    for problem_id, expected_concepts in expected_c10_concepts.items():
        assert c10[problem_id]["concepts"] == expected_concepts
    for concept in PLAN016_C10_PROMOTED_CONCEPTS:
        assert [
            problem_id
            for problem_id, problem in c10.items()
            if concept in problem["concepts"]
        ] == ["C10-p15", "C10-p17", "C10-p18"]


def test_plan016_f1_register_rows_are_under_truthful_set_comments():
    text = (ROOT / "units" / "F1-scientific-python" / "manifest.yaml").read_text()
    set_a, after_a = text.split("# --- Set B: exam register ---", 1)
    set_b, set_c = after_a.split("# --- Set C: integration + challenge ---", 1)

    assert "id: F1-p22" in set_a
    assert "id: F1-p23" in set_b
    assert "id: F1-p24" in set_c


def test_f1_seaborn_array_only_boundary():
    unit_dir = ROOT / "units" / "F1-scientific-python"
    actual_files = {
        path.relative_to(unit_dir) for path in (unit_dir / "lessons").glob("*.ipynb")
    }
    actual_files.update(
        path.relative_to(unit_dir)
        for path in (unit_dir / "practice").glob("p2[234]*.ipynb")
    )
    actual_files.update({Path("lesson.ipynb"), Path("review.ipynb")})

    assert len(F1_SEABORN_ARRAY_ONLY_FILES) == 12
    assert actual_files == F1_SEABORN_ARRAY_ONLY_FILES
    assert all((unit_dir / relative).is_file() for relative in F1_SEABORN_ARRAY_ONLY_FILES)

    forbidden = {
        "import pandas": re.compile(r"\bimport\s+pandas\b", re.IGNORECASE),
        "from pandas": re.compile(r"\bfrom\s+pandas\b", re.IGNORECASE),
        "pd.": re.compile(r"\bpd\s*\."),
        "DataFrame": re.compile(r"\bdataframe\b", re.IGNORECASE),
    }
    for relative in sorted(F1_SEABORN_ARRAY_ONLY_FILES):
        text = (unit_dir / relative).read_text()
        hits = [name for name, pattern in forbidden.items() if pattern.search(text)]
        assert hits == [], f"{relative}: forbidden pandas surface {hits}"


def test_plan016_f7_manifest_has_exact_foundation_contract_and_register():
    syllabus = load_syllabus(ROOT)
    unit = syllabus.units["F7-kernels-convex-optimization"]
    assert unit.track == "foundation"
    assert unit.prereqs == [
        "F3-matrices",
        "F4-multivar-calculus",
        "F6-svd-spectral",
        "C3-gradient-descent",
    ]
    assert unit.teaches == [
        "positive-semidefinite-matrices",
        "kernel-validity",
        "convex-sets",
        "convex-functions",
        "first-order-optimality",
        "lagrangians",
        "optimization-duality",
    ]

    manifest = _manifest(unit.id)
    expected_rows = [
        ("F7-p01", "A", "mc", "intro", ["positive-semidefinite-matrices"]),
        ("F7-p02", "A", "mc", "intro", ["kernel-validity"]),
        ("F7-p03", "A", "mc", "intro", ["convex-sets"]),
        ("F7-p04", "B", "mc-normal-form", "core", ["convex-functions", "first-order-optimality"]),
        ("F7-p05", "A", "constrained-coding", "intro", ["positive-semidefinite-matrices"]),
        ("F7-p06", "B", "constrained-coding", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p07", "B", "constrained-coding", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p08", "A", "constrained-coding", "intro", ["convex-sets"]),
        ("F7-p09", "B", "constrained-coding", "core", ["convex-functions"]),
        ("F7-p10", "B", "constrained-coding", "advanced", ["lagrangians", "optimization-duality"]),
        ("F7-p11", "B", "proof", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p12", "B", "proof", "advanced", ["positive-semidefinite-matrices", "convex-functions", "first-order-optimality"]),
        ("F7-p13", "C", "integrative", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p14", "C", "integrative", "advanced", ["convex-sets", "convex-functions", "first-order-optimality", "lagrangians", "optimization-duality"]),
        ("F7-p15", "C", "scenario", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p16", "C", "scenario", "core", ["convex-functions", "first-order-optimality"]),
        ("F7-p17", "C", "challenge", "advanced", ["kernel-validity"]),
        ("F7-p18", "C", "challenge", "advanced", ["lagrangians", "optimization-duality"]),
        ("F7-p19", "A", "drill", "intro", ["convex-sets", "convex-functions"]),
        ("F7-p20", "B", "drill", "core", ["lagrangians", "optimization-duality"]),
    ]
    assert [
        (row["id"], row["set"], row["type"], row["difficulty"], row["concepts"])
        for row in manifest["practice"]
    ] == expected_rows


def test_plan016_coverage_map_conversion_is_controlled():
    roadmap = yaml.safe_load((ROOT / "curriculum" / "coverage-map.yaml").read_text())
    planned = {unit["id"]: unit for unit in roadmap["planned_units"]}
    points = {point["id"]: point for point in roadmap["knowledge_points"]}

    assert "P015-R1-MATH-KERNEL-OPT" not in planned
    assert planned["P015-R1-CLASSICAL-BREADTH"]["prerequisites"] == [
        "C1-ml-fundamentals",
        "C2-linear-models",
        "C3-gradient-descent",
        "C4-classical-ml-practice",
        "F7-kernels-convex-optimization",
    ]
    assert points["seaborn-programming"]["depends_on"] == [
        "numpy-programming",
        "matplotlib-pyplot-programming",
    ]
    assert "array" in points["seaborn-programming"]["rationale"].lower()
    expected_mappings = {
        "valid-kernel-positive-definite-proof": [
            "positive-semidefinite-matrices",
            "kernel-validity",
        ],
        "convex-sets-functions-and-optimality": [
            "convex-sets",
            "convex-functions",
            "first-order-optimality",
        ],
        "constrained-optimization-lagrangian-duality": [
            "lagrangians",
            "optimization-duality",
        ],
    }
    for point_id, shipped_concepts in expected_mappings.items():
        point = points[point_id]
        assert point["coverage"] == "missing"
        assert point["evidence_by_modality"]
        assert all(
            not evidence["lesson_anchors"]
            and not evidence["practices"]
            and not evidence["assessments"]
            for evidence in point["evidence_by_modality"].values()
        )
        assert point["disposition"] == "extend-existing-unit"
        assert point["destination"] == "F7-kernels-convex-optimization"
        assert point["shipped_concepts"] == shipped_concepts


def test_plan016_syllabus_narrative_order_and_dependency_contract():
    syllabus = _canonical_syllabus_yaml()
    units = {unit["id"]: unit for unit in syllabus["units"]}
    assert units["F5-probability"]["length"] == "double"
    assert units["F6-svd-spectral"]["length"] == "double"
    narrative = _syllabus_narrative()
    foundation = _narrative_section(narrative, "Foundation track — rationale")
    core = _narrative_section(narrative, "Core track — rationale")
    normalized_foundation = " ".join(foundation.split())
    normalized_core = " ".join(core.split())
    assert "`F5-probability` is a double-length unit" in normalized_foundation
    assert "`F6-svd-spectral` is the other double-length unit" in normalized_foundation
    assert "`F7-kernels-convex-optimization`" in normalized_foundation
    assert (
        "`C2-linear-models` session 02 ships closed-form unregularized OLS fitting and the "
        "`linear-regression-estimator-derivation`, including rank, identifiability, and "
        "pseudoinverse behavior."
    ) in normalized_core
    assert (
        "Only iterative gradient-based fitting remains deferred to `C3-gradient-descent`."
    ) in normalized_core
    assert "Fitting itself is deferred to `C3-gradient-descent`" not in normalized_core

    order_section = _narrative_section(
        narrative, "Suggested order (one feasible topological sort)"
    )
    order = re.search(r"^F1 → .* → C10$", order_section, re.MULTILINE)
    assert order is not None
    by_short_id = {unit_id.split("-", 1)[0]: unit_id for unit_id in units}
    ordered_unit_ids = [by_short_id[short_id] for short_id in order.group(0).split(" → ")]
    expected_order = [
        "F1-scientific-python",
        "F2-vectors",
        "C1-ml-fundamentals",
        "F4-multivar-calculus",
        "F3-matrices",
        "F5-probability",
        "C4-classical-ml-practice",
        "C2-linear-models",
        "C3-gradient-descent",
        "C5-neural-networks",
        "C6-pytorch",
        "C7-cnn-transfer",
        "C8-embeddings",
        "F6-svd-spectral",
        "F7-kernels-convex-optimization",
        "C9-dimensionality-reduction",
        "C10-competition-craft",
    ]
    assert ordered_unit_ids == expected_order
    assert set(ordered_unit_ids) == set(units)
    assert len(ordered_unit_ids) == len(set(ordered_unit_ids)) == 17
    positions = {unit_id: index for index, unit_id in enumerate(ordered_unit_ids)}
    for unit_id in ordered_unit_ids:
        assert all(
            positions[prereq] < positions[unit_id] for prereq in units[unit_id]["prereqs"]
        )

    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert any(dependency.startswith("seaborn>=") for dependency in project["project"]["dependencies"])
    assert re.search(r'^name = "seaborn"$', (ROOT / "uv.lock").read_text(), re.MULTILINE)
    standards = (ROOT / "docs" / "unit-standards.md").read_text()
    assert "Double-length units (F5, F6) use 4–6 sessions." in standards


def test_plan016_practice_coverage_is_green():
    report = check_coverage(ROOT)

    assert report.ok
    assert report.warnings == []
    assert report.errors == []


def test_ci_checks_other_than_plan016_pending_coverage_are_green():
    reports = [
        check_prereq(ROOT),
        check_hygiene(ROOT),
        check_blueprint(ROOT),
        check_overlap(ROOT),
    ]
    for report in reports:
        assert not report.errors
        assert report.ok
        if report.name == "overlap-scan":
            assert report.skipped is None


def test_cli_exit_codes(tmp_path):
    seed_repo(tmp_path)
    ok = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "prereq-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0
    fail_root = tmp_path / "fail"
    seed_repo(fail_root)
    manifest = fail_root / "mocktests" / "r1-001"
    manifest.mkdir(parents=True)
    manifest.joinpath("manifest.yaml").write_text(
        """
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {}
problems:
  - id: p01
    section: concept-block
    units: [F1-scientific-python]
    concepts: [vectors-and-norms]
    cluster: linear-algebra
    points: 1
    difficulty: intro
    type: theory
    answer_form: short
    provenance: original
    spec: x
    answer_key: x
"""
    )
    fail = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(fail_root), "prereq-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail.returncode == 1
    skip_root = tmp_path / "skip"
    seed_repo(skip_root)
    scaffold_mocktest(skip_root, "r1-001", "2026-08-15")
    skipped = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(skip_root), "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert skipped.returncode == 3


def test_full_pipeline_on_synthetic_test(tmp_path):
    seed_repo(tmp_path)
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    (unit_dir / "practice").mkdir(parents=True)
    for number in range(1, 4):
        (unit_dir / "practice" / f"p{number:02}.ipynb").write_text(
            '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}'
        )
        (unit_dir / "practice" / f"p{number:02}_solution.ipynb").write_text("{}")
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: p01
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - id: p02
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p02.ipynb
    solution_path: practice/p02_solution.ipynb
  - id: p03
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p03.ipynb
    solution_path: practice/p03_solution.ipynb
"""
    )
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    assert check_prereq(tmp_path).ok
    assert check_coverage(tmp_path).ok
    assert check_hygiene(tmp_path).ok
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert report.warnings


def test_ci_flags_draft_manifest_loudly(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3
    assert "DRAFT manifest" in proc.stdout


def test_scope_cli_is_registered_and_loader_errors_are_blocking(tmp_path):
    seed_repo(tmp_path)

    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "scope-check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "curriculum/sources.yaml" in proc.stderr
    assert "invalid choice" not in proc.stderr


def test_ci_local_wires_inventory_scope_and_generated_document_checks():
    script = (ROOT / "scripts" / "ci-local.sh").read_text()

    assert "python -m tools.audit_curriculum --check" in script
    assert 'usaaio-tools "$c"' in script
    assert "scope-check" in script
    assert "python -m tools.render_curriculum_roadmap --check" in script


def test_pre_merge_guard_runs_embedded_yaml_with_uv_python():
    script = (ROOT / "scripts" / "pre-merge-guard.sh").read_text()

    assert "uv run python -" in script
    assert "python3 -" not in script


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _roadmap(destination: str | None, planned_id: str | None) -> str:
    return yaml.safe_dump(
        {
            "roadmap_version": 1,
            "layers": [],
            "planned_units": (
                [{"id": planned_id, "knowledge_points": ["topic-a"]}] if planned_id else []
            ),
            "knowledge_points": (
                [{"id": "topic-a", "destination": destination}] if destination else []
            ),
        },
        sort_keys=False,
    )


def _fake_uv_environment(tmp_path: Path) -> dict[str, str]:
    executable = tmp_path / "bin" / "uv"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ $1 == run ]]\n"
        "shift\n"
        "[[ $1 == python ]]\n"
        "shift\n"
        'exec "$TEST_PYTHON" "$@"\n'
    )
    executable.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{executable.parent}:{env['PATH']}"
    env["TEST_PYTHON"] = sys.executable
    return env


def test_pre_merge_guard_pr_mode_fails_when_origin_main_is_unavailable(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    script = repo / "scripts" / "pre-merge-guard.sh"
    script.parent.mkdir()
    script.write_bytes((ROOT / "scripts" / "pre-merge-guard.sh").read_bytes())
    script.chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "origin/main" in proc.stderr
    assert "unverified" in proc.stderr


def test_pre_merge_guard_rejects_parallel_roadmap_ownership_collisions(tmp_path):
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    other = tmp_path / "other"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    script = repo / "scripts" / "pre-merge-guard.sh"
    script.parent.mkdir()
    script.write_bytes((ROOT / "scripts" / "pre-merge-guard.sh").read_bytes())
    script.chmod(0o755)
    coverage = repo / "curriculum" / "coverage-map.yaml"
    coverage.parent.mkdir()
    coverage.write_text(_roadmap(None, None))
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    coverage.write_text(_roadmap("U-feature", "P-collision"))

    _git(tmp_path, "clone", "-b", "main", str(remote), str(other))
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    other.joinpath("curriculum", "coverage-map.yaml").write_text(
        _roadmap("U-main", "P-collision")
    )
    _git(other, "add", ".")
    _git(other, "commit", "-m", "parallel roadmap")
    _git(other, "push", "origin", "main")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "roadmap knowledge-point ownership collision: topic-a" in proc.stdout
    assert "roadmap planned-unit ownership collision: P-collision" in proc.stdout
