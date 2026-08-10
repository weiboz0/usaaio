from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

REQUIRED_FILES = (
    "syllabus.md",
    "curriculum/course-schedule.yaml",
    "curriculum/coverage-map.yaml",
    "curriculum/material-inventory.yaml",
    "curriculum/official-topics.yaml",
    "curriculum/source-manifest.yaml",
    "mocktests/blueprint.yaml",
    "docs/course-structure.md",
)


def _books_module():
    try:
        return importlib.import_module("tools.books")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.books":
            raise
        pytest.fail("tools.books is the missing Plan 019 registry producer")


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _syllabus(
    *,
    unit: str,
    concept: str,
    imports: dict[str, object] | None = None,
    evidence_imports: dict[str, object] | None = None,
) -> str:
    contract: dict[str, Any] = {
        "baseline": {"mathematics": ["arithmetic"]},
        "clusters": ["fixture"],
        "concepts": [{"id": concept, "cluster": "fixture"}],
        "units": [
            {
                "id": unit,
                "track": "fixture",
                "title": unit,
                "prereqs": [],
                "teaches": [concept],
            }
        ],
    }
    if imports is not None:
        contract["imports"] = imports
    if evidence_imports is not None:
        contract["evidence_imports"] = evidence_imports
    return (
        "# Fixture syllabus\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(contract, sort_keys=False)
        + "```\n"
    )


def _write_book(
    repo: Path,
    book_id: str,
    *,
    complete: bool = True,
    corrupt_syllabus: bool = False,
) -> Path:
    root = repo / book_id
    root.mkdir(parents=True, exist_ok=True)
    number = 1 if book_id == "book1" else 2
    unit = "C1-foundation" if number == 1 else "B2-019-attention-transformers"
    concept = "softmax" if number == 1 else "query-key-value-attention"
    imports = None
    evidence = None
    if number == 2:
        imports = {"book": "book1", "units": ["C1-foundation"], "concepts": ["softmax"]}
        evidence = {
            "book": "book1",
            "concepts": ["tokenization"],
            "lesson_paths": ["units/C8-embeddings/lessons/01-tokens-and-embeddings.ipynb"],
            "practices": ["C8-p01"],
            "assessments": ["r1-001-p05-1"],
        }
    syllabus = (
        "not a canonical syllabus\n"
        if corrupt_syllabus
        else _syllabus(
            unit=unit,
            concept=concept,
            imports=imports,
            evidence_imports=evidence,
        )
    )
    (root / "syllabus.md").write_text(syllabus, encoding="utf-8")
    if complete:
        for relative in REQUIRED_FILES[1:]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".yaml":
                path.write_text("{}\n", encoding="utf-8")
            else:
                path.write_text(f"# {book_id}\n", encoding="utf-8")
        for directory in ("units", "reference"):
            marker = root / directory / ".gitkeep"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("", encoding="utf-8")
    return root


def write_two_book_repo(repo: Path, *, corrupt_book2: bool = False) -> None:
    _write_yaml(
        repo / "books.yaml",
        {
            "books_version": 1,
            "books": [
                {"id": "book1", "number": 1, "root": "book1", "depends_on": []},
                {
                    "id": "book2",
                    "number": 2,
                    "root": "book2",
                    "depends_on": ["book1"],
                },
            ],
        },
    )
    _write_book(repo, "book1")
    _write_book(repo, "book2", corrupt_syllabus=corrupt_book2)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        pytest.param(
            lambda repo: (repo / "units").mkdir(),
            "legacy root",
            id="legacy-units-root",
        ),
        pytest.param(
            lambda repo: _write_yaml(
                repo / "books.yaml",
                {
                    "books_version": 1,
                    "books": [
                        {"id": "book1", "number": 1, "root": "../escape", "depends_on": []},
                        {
                            "id": "book2",
                            "number": 2,
                            "root": "book2",
                            "depends_on": ["book1"],
                        },
                    ],
                },
            ),
            "escaping",
            id="escaping-root",
        ),
    ],
)
def test_catalog_rejects_legacy_root_and_escaping_book_roots(
    tmp_path: Path,
    mutation: Callable[[Path], None],
    message: str,
) -> None:
    write_two_book_repo(tmp_path)
    mutation(tmp_path)

    with pytest.raises(ValueError, match=message):
        _books_module().load_book_catalog(tmp_path)


def _mutate_registry(repo: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    path = repo / "books.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(raw)
    _write_yaml(path, raw)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        pytest.param(
            lambda repo: _mutate_registry(repo, lambda raw: raw["books"][1].update(id="book1")),
            "duplicate.*id",
            id="duplicate-id",
        ),
        pytest.param(
            lambda repo: _mutate_registry(repo, lambda raw: raw["books"][1].update(number=1)),
            "duplicate.*number",
            id="duplicate-number",
        ),
        pytest.param(
            lambda repo: _mutate_registry(repo, lambda raw: raw["books"][1].update(root="book1")),
            "duplicate.*root",
            id="duplicate-root",
        ),
        pytest.param(
            lambda repo: _mutate_registry(
                repo, lambda raw: raw["books"][0].update(depends_on=["book2"])
            ),
            "cycle",
            id="dependency-cycle",
        ),
        pytest.param(
            lambda repo: (
                (repo / "book2").rename(repo / "real-book2"),
                (repo / "book2").symlink_to(repo / "real-book2", target_is_directory=True),
            ),
            "symlink",
            id="symlink-root",
        ),
        pytest.param(
            lambda repo: (repo / "book3").mkdir(),
            "undeclared.*book3",
            id="undeclared-book3",
        ),
    ],
)
def test_catalog_structure_mutation_matrix(
    tmp_path: Path,
    mutation: Callable[[Path], object],
    message: str,
) -> None:
    write_two_book_repo(tmp_path)
    mutation(tmp_path)

    with pytest.raises(ValueError, match=message):
        _books_module().load_book_catalog(tmp_path)


@pytest.mark.parametrize("relative", REQUIRED_FILES)
def test_selected_book_validation_reports_each_missing_required_file(
    tmp_path: Path, relative: str
) -> None:
    write_two_book_repo(tmp_path)
    missing = tmp_path / "book1" / relative
    missing.unlink()
    catalog = _books_module().load_book_catalog(tmp_path)

    errors = _books_module().validate_book_root(catalog.by_id("book1"))

    assert any(relative in error for error in errors), errors


def test_book1_selection_does_not_validate_missing_or_corrupt_book2_content(
    tmp_path: Path,
) -> None:
    write_two_book_repo(tmp_path, corrupt_book2=True)
    (tmp_path / "book2" / "curriculum" / "coverage-map.yaml").unlink()

    catalog = _books_module().load_book_catalog(tmp_path)
    book1 = catalog.by_id("book1")

    assert _books_module().validate_book_root(book1) == []


def test_book2_selection_loads_only_its_declared_book1_import_surface(
    tmp_path: Path,
) -> None:
    write_two_book_repo(tmp_path)
    # An unrelated required Book 1 document is not part of Book 2's import surface.
    (tmp_path / "book1" / "docs" / "course-structure.md").unlink()
    catalog = _books_module().load_book_catalog(tmp_path)
    book2 = catalog.by_id("book2")

    imported = _books_module().load_book_imports(book2)
    resolved = _books_module().resolve_qualified_import(catalog, book2, "book1:softmax")

    assert imported.source_book == "book1"
    assert imported.units == ("C1-foundation",)
    assert imported.concepts == ("softmax",)
    assert resolved.is_relative_to(catalog.by_id("book1").root)


def test_cross_book_import_requires_registry_dependency_and_qualified_owner(
    tmp_path: Path,
) -> None:
    write_two_book_repo(tmp_path)
    books = _books_module()
    catalog = books.load_book_catalog(tmp_path)
    book2 = catalog.by_id("book2")

    assert books.resolve_qualified_import(catalog, book2, "book1:softmax").is_relative_to(
        catalog.by_id("book1").root
    )
    for identity, message in (
        ("softmax", "qualified"),
        ("book2:softmax", "owner"),
        ("book1:not-imported", "allowlist"),
    ):
        with pytest.raises(ValueError, match=message):
            books.resolve_qualified_import(catalog, book2, identity)

    _mutate_registry(tmp_path, lambda raw: raw["books"][1].update(depends_on=[]))
    catalog = books.load_book_catalog(tmp_path)
    with pytest.raises(ValueError, match="dependency"):
        books.resolve_qualified_import(catalog, catalog.by_id("book2"), "book1:softmax")
