import base64
import json
from pathlib import Path

import pytest
import yaml

from tools import audit_curriculum as audit

REPO_ROOT = Path(__file__).parents[1]


def _write_notebook(path: Path, cells: list[dict], *, metadata: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cells": cells,
                "metadata": metadata or {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )


def _markdown(source: str, **extra: object) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source, **extra}


def _code(source: str, **extra: object) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
        **extra,
    }


def _make_minimal_repo(root: Path) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "course-structure.md").write_text("# Schedule\n\nOne debrief.\n")
    (root / "syllabus.md").write_text(
        """# Syllabus

<!-- syllabus-canonical -->
```yaml
baseline:
  mathematics: [arithmetic]
clusters: [foundation]
concepts:
  - id: vectors
    cluster: foundation
units:
  - id: U1-vectors
    track: foundation
    title: Vectors
    prereqs: []
    teaches: [vectors]
```
"""
    )

    unit = root / "units" / "U1-vectors"
    unit.mkdir(parents=True)
    (unit / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "unit": "U1-vectors",
                "concepts_taught": ["vectors"],
                "concepts_used": [],
                "prereq_units": [],
                "estimated_minutes": {
                    "lesson_sessions": [10],
                    "practice": 20,
                    "review": 5,
                },
                "practice": [
                    {
                        "id": "U1-p01",
                        "concepts": ["vectors"],
                        "path": "practice/p01.ipynb",
                        "solution_path": "practice/p01_solution.ipynb",
                    }
                ],
            },
            sort_keys=False,
        )
    )
    _write_notebook(unit / "lesson.ipynb", [_markdown("# Vectors\n")])
    _write_notebook(unit / "lessons" / "01-vectors.ipynb", [_markdown("Vectors\n=======\n")])
    _write_notebook(unit / "review.ipynb", [_markdown("# Review\n")])
    _write_notebook(unit / "practice" / "p01.ipynb", [_markdown("# U1-p01\n")])
    _write_notebook(
        unit / "practice" / "p01_solution.ipynb",
        [_code("answer = np.linalg.norm([3, 4])\n")],
    )

    mock = root / "mocktests" / "r1-mini"
    mock.mkdir(parents=True)
    (mock / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "test": "r1-mini",
                "duration_minutes": 30,
                "problems": [
                    {
                        "id": "r1-mini-p01",
                        "units": ["U1-vectors"],
                        "concepts": ["vectors"],
                        "files": ["problems/p01.ipynb"],
                    }
                ],
            },
            sort_keys=False,
        )
    )
    _write_notebook(mock / "problems" / "p01.ipynb", [_markdown("# Problem 1\n")])
    _write_notebook(mock / "solutions" / "p01_solution.ipynb", [_code("answer = 5\n")])


def test_notebook_digest_ignores_transient_notebook_fields(tmp_path: Path) -> None:
    first = tmp_path / "first.ipynb"
    second = tmp_path / "second.ipynb"
    _write_notebook(
        first,
        [
            _markdown("# Stable\n", id="cell-a", metadata={"collapsed": True}),
            _code(
                "value = 1\n",
                id="cell-b",
                execution_count=1,
                outputs=[{"output_type": "stream", "name": "stdout", "text": "one\n"}],
                metadata={"tags": ["keep"]},
            ),
        ],
        metadata={"kernelspec": {"name": "python3"}},
    )
    _write_notebook(
        second,
        [
            _markdown("# Stable\n", id="different-a", metadata={"collapsed": False}),
            _code(
                "value = 1\n",
                id="different-b",
                execution_count=99,
                outputs=[{"output_type": "stream", "name": "stdout", "text": "changed\n"}],
                metadata={"tags": ["different"]},
            ),
        ],
        metadata={"language_info": {"version": "different"}},
    )

    first_record = audit.notebook_record(first, "same.ipynb")
    second_record = audit.notebook_record(second, "same.ipynb")

    assert first_record == second_record


def test_notebook_digest_normalizes_line_endings_and_unicode(tmp_path: Path) -> None:
    decomposed = tmp_path / "decomposed.ipynb"
    composed = tmp_path / "composed.ipynb"
    _write_notebook(decomposed, [_markdown("# Cafe\u0301\r\n\rBody\r\n")])
    _write_notebook(composed, [_markdown("# Caf\u00e9\n\nBody\n")])

    assert audit.notebook_record(decomposed, "same.ipynb") == audit.notebook_record(
        composed, "same.ipynb"
    )


def test_notebook_digest_changes_with_source_or_attachment_bytes(tmp_path: Path) -> None:
    attachment_a = {"plot.png": {"image/png": base64.b64encode(b"first").decode()}}
    attachment_b = {"plot.png": {"image/png": base64.b64encode(b"second").decode()}}
    baseline = tmp_path / "baseline.ipynb"
    changed_source = tmp_path / "changed-source.ipynb"
    changed_attachment = tmp_path / "changed-attachment.ipynb"
    _write_notebook(baseline, [_markdown("# Evidence\n", attachments=attachment_a)])
    _write_notebook(changed_source, [_markdown("# Different\n", attachments=attachment_a)])
    _write_notebook(changed_attachment, [_markdown("# Evidence\n", attachments=attachment_b)])

    baseline_digest = audit.notebook_record(baseline, "same.ipynb")["semantic_sha256"]

    assert audit.notebook_record(changed_source, "same.ipynb")["semantic_sha256"] != baseline_digest
    assert (
        audit.notebook_record(changed_attachment, "same.ipynb")["semantic_sha256"]
        != baseline_digest
    )


def test_atx_setext_and_repeated_headings_have_stable_distinct_anchors(tmp_path: Path) -> None:
    path = tmp_path / "headings.ipynb"
    _write_notebook(
        path,
        [
            _markdown("# Top\n"),
            _markdown("First body\n"),
            _markdown("Subsection\n----------\n"),
            _code("np.linalg.svd(matrix)\nmodel.fit(x, y)\n"),
            _markdown("# Top\n"),
            _markdown("Second body\n"),
        ],
    )

    record = audit.notebook_record(path, "units/U1/lesson.ipynb")
    anchors = record["anchors"]

    assert [entry["heading_path"] for entry in anchors] == [
        ["Top"],
        ["Top"],
        ["Top", "Subsection"],
        ["Top", "Subsection"],
        ["Top"],
        ["Top"],
    ]
    assert [entry["cell_ordinal"] for entry in anchors] == [1, 2, 1, 2, 3, 4]
    assert len({entry["anchor"] for entry in anchors}) == len(anchors)
    assert {"np.linalg.svd", "model.fit"} <= set(record["api_tokens"])


def test_manifest_digest_is_semantic_not_textual(tmp_path: Path) -> None:
    first = tmp_path / "first.yaml"
    reordered = tmp_path / "reordered.yaml"
    changed = tmp_path / "changed.yaml"
    first.write_text("outer:\n  alpha: 1\n  beta: [2, 3]\n")
    reordered.write_text("outer:\n  beta: [2, 3]\n  alpha: 1\n")
    changed.write_text("outer:\n  beta: [2, 4]\n  alpha: 1\n")

    first_digest = audit.manifest_record(first, "manifest.yaml")["semantic_sha256"]

    assert audit.manifest_record(reordered, "manifest.yaml")["semantic_sha256"] == first_digest
    assert audit.manifest_record(changed, "manifest.yaml")["semantic_sha256"] != first_digest


def test_manifest_digest_rejects_non_string_keys_without_collisions(tmp_path: Path) -> None:
    path = tmp_path / "colliding.yaml"
    path.write_text("outer:\n  1: numeric\n  '1': textual\n")

    with pytest.raises(audit.InventoryError, match="keys must be strings"):
        audit.manifest_record(path, "colliding.yaml")


def test_inventory_paths_and_rendering_are_deterministic(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)

    first = audit.build_inventory(tmp_path)
    second = audit.build_inventory(tmp_path)
    inventoried_paths = first["input_paths"]

    assert inventoried_paths == sorted(inventoried_paths, key=str.encode)
    assert first == second
    assert audit.render_inventory(first) == audit.render_inventory(second)


def test_declared_ids_are_recorded_without_coverage_inference(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)

    inventory = audit.build_inventory(tmp_path)
    statement = next(
        entry for entry in inventory["notebooks"] if entry["path"].endswith("practice/p01.ipynb")
    )

    assert statement["declared_unit_ids"] == ["U1-vectors"]
    assert statement["declared_concept_ids"] == ["vectors"]
    assert statement["declared_problem_ids"] == ["U1-p01"]
    assert "coverage" not in statement


def test_synthesis_notebooks_keep_nearest_manifest_declarations(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)
    synthesis = tmp_path / "synthesis" / "bridge"
    synthesis.mkdir(parents=True)
    (synthesis / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "unit": "S-bridge",
                "concepts_taught": ["vectors"],
                "practice": [
                    {
                        "id": "S-p01",
                        "concepts": ["vectors"],
                        "path": "practice/p01.ipynb",
                    }
                ],
            }
        )
    )
    _write_notebook(synthesis / "practice" / "p01.ipynb", [_markdown("# Bridge\n")])

    inventory = audit.build_inventory(tmp_path)
    record = next(
        item
        for item in inventory["notebooks"]
        if item["path"] == "synthesis/bridge/practice/p01.ipynb"
    )

    assert record["declared_unit_ids"] == ["S-bridge"]
    assert record["declared_concept_ids"] == ["vectors"]
    assert record["declared_problem_ids"] == ["S-p01"]

    (synthesis / "practice" / "p01.ipynb").unlink()
    with pytest.raises(audit.InventoryError, match="declared notebook is missing"):
        audit.build_inventory(tmp_path)


def test_all_mock_rounds_are_discovered(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)
    source = tmp_path / "mocktests" / "r1-mini"
    destination = tmp_path / "mocktests" / "r2-mini"
    source.rename(destination)

    counts = audit.build_inventory(tmp_path)["counts"]

    assert counts["mocktests"] == 1
    assert counts["mock_notebooks"] == 2


def test_missing_declared_unit_notebook_fails_loudly(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)
    missing = tmp_path / "units" / "U1-vectors" / "practice" / "p01_solution.ipynb"
    missing.unlink()

    with pytest.raises(audit.InventoryError, match="declared notebook is missing"):
        audit.build_inventory(tmp_path)


@pytest.mark.parametrize("escape_kind", ["parent", "symlink"])
def test_declared_unit_notebooks_cannot_escape_the_unit(
    tmp_path: Path, escape_kind: str
) -> None:
    _make_minimal_repo(tmp_path)
    outside = tmp_path / "outside.ipynb"
    _write_notebook(outside, [_code("answer = 5\n")])
    unit = tmp_path / "units" / "U1-vectors"
    if escape_kind == "parent":
        declared = "../../outside.ipynb"
    else:
        link = unit / "practice" / "escape.ipynb"
        link.symlink_to(outside)
        declared = "practice/escape.ipynb"
    manifest_path = unit / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["practice"][0]["solution_path"] = declared
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    with pytest.raises(audit.InventoryError, match="escapes its material directory"):
        audit.build_inventory(tmp_path)


@pytest.mark.parametrize("material_tree", ["unit", "mock", "synthesis"])
def test_undeclared_notebook_symlinks_are_rejected(
    tmp_path: Path, material_tree: str
) -> None:
    _make_minimal_repo(tmp_path)
    outside = tmp_path / "outside.ipynb"
    _write_notebook(outside, [_code("external.secret_api()\n")])
    if material_tree == "unit":
        link = tmp_path / "units" / "U1-vectors" / "orphan.ipynb"
    elif material_tree == "mock":
        link = tmp_path / "mocktests" / "r1-mini" / "problems" / "orphan.ipynb"
    else:
        synthesis = tmp_path / "synthesis" / "bridge"
        synthesis.mkdir(parents=True)
        (synthesis / "manifest.yaml").write_text(
            yaml.safe_dump({"unit": "S-bridge", "concepts_taught": ["vectors"]})
        )
        link = synthesis / "orphan.ipynb"
    link.symlink_to(outside)

    with pytest.raises(audit.InventoryError, match="notebook symlinks are not allowed"):
        audit.build_inventory(tmp_path)


def test_missing_declared_mock_notebook_fails_loudly(tmp_path: Path) -> None:
    _make_minimal_repo(tmp_path)
    missing = tmp_path / "mocktests" / "r1-mini" / "solutions" / "p01_solution.ipynb"
    missing.unlink()

    with pytest.raises(audit.InventoryError, match="declared notebook is missing"):
        audit.build_inventory(tmp_path)


def test_imported_bare_api_calls_are_recorded(tmp_path: Path) -> None:
    path = tmp_path / "api.ipynb"
    _write_notebook(path, [_code("from torch import softmax\nsoftmax(values)\n")])

    record = audit.notebook_record(path, "api.ipynb")

    assert "torch.softmax" in record["api_tokens"]


def test_check_mode_catches_missing_and_stale_inventory_then_passes(tmp_path: Path, capsys) -> None:
    _make_minimal_repo(tmp_path)

    assert audit.main(["--root", str(tmp_path), "--check"]) == 1
    assert "missing" in capsys.readouterr().err

    assert audit.main(["--root", str(tmp_path)]) == 0
    output = tmp_path / "curriculum" / "material-inventory.yaml"
    assert output.is_file()
    assert audit.main(["--root", str(tmp_path), "--check"]) == 0

    output.write_text(output.read_text() + "# stale\n")
    assert audit.main(["--root", str(tmp_path), "--check"]) == 1
    assert "stale" in capsys.readouterr().err


def test_real_repository_inventory_counts() -> None:
    counts = audit.build_inventory(REPO_ROOT)["counts"]

    assert counts == {
        "units": 16,
        "concepts": 109,
        "unit_practices": 343,
        "lesson_sessions": 47,
        "unit_nonpractice_notebooks": 79,
        "unit_notebooks": 765,
        "mocktests": 1,
        "mock_notebooks": 10,
        "manifested_minutes": 12_347,
        "scheduled_minutes": 12_587,
    }


@pytest.mark.parametrize(
    ("relative_path", "contents"),
    [
        ("units/U1/lesson.ipynb", "{not-json"),
        ("units/U1/manifest.yaml", "practice: [\n"),
    ],
)
def test_malformed_inputs_fail_loudly(
    tmp_path: Path, relative_path: str, contents: str
) -> None:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True)
    path.write_text(contents)

    with pytest.raises(audit.InventoryError, match=relative_path):
        if path.suffix == ".ipynb":
            audit.notebook_record(path, relative_path)
        else:
            audit.manifest_record(path, relative_path)


def test_read_failures_fail_loudly(tmp_path: Path) -> None:
    unreadable_as_file = tmp_path / "broken.ipynb"
    unreadable_as_file.mkdir()

    with pytest.raises(audit.InventoryError, match="broken.ipynb"):
        audit.notebook_record(unreadable_as_file, "broken.ipynb")
