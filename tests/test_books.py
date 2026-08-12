from __future__ import annotations

import argparse
import importlib
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

REQUIRED_PATHS = (
    "syllabus.md",
    "curriculum/course-schedule.yaml",
    "curriculum/coverage-map.yaml",
    "curriculum/material-inventory.yaml",
    "curriculum/official-topics.yaml",
    "curriculum/source-manifest.yaml",
    "mocktests/blueprint.yaml",
    "docs/course-structure.md",
    "units",
    "reference",
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
        for relative in REQUIRED_PATHS[1:-2]:
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
        *[
            pytest.param(
                lambda repo, legacy=legacy: (
                    (repo / legacy).mkdir()
                    if "." not in legacy
                    else (repo / legacy).write_text("legacy\n")
                ),
                "legacy root",
                id=f"legacy-{legacy.replace('.', '-')}-root",
            )
            for legacy in ("syllabus.md", "curriculum", "units", "mocktests", "reference")
        ],
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
        pytest.param(
            lambda repo: _mutate_registry(
                repo,
                lambda raw: raw["books"][0].update(root=str((repo / "book1").resolve())),
            ),
            "absolute",
            id="absolute-root",
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


def _mutate_syllabus_contract(
    repo: Path, book_id: str, mutate: Callable[[dict[str, Any]], None]
) -> None:
    path = repo / book_id / "syllabus.md"
    before, fenced = path.read_text(encoding="utf-8").split("```yaml\n", 1)
    body, after = fenced.split("\n```", 1)
    raw = yaml.safe_load(body)
    mutate(raw)
    rendered = yaml.safe_dump(raw, sort_keys=False).rstrip()
    path.write_text(f"{before}```yaml\n{rendered}\n```{after}", encoding="utf-8")


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
            lambda repo: _mutate_registry(
                repo, lambda raw: raw["books"][1].update(depends_on=["book9"])
            ),
            "unknown.*depend",
            id="unknown-dependency",
        ),
        pytest.param(
            lambda repo: _mutate_registry(repo, lambda raw: raw.update(extra="forbidden")),
            "unexpected|exactly",
            id="unexpected-registry-key",
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


def test_catalog_rejects_undeclared_symlink_alias_of_declared_book(tmp_path: Path) -> None:
    write_two_book_repo(tmp_path)
    (tmp_path / "book3").symlink_to(tmp_path / "book1", target_is_directory=True)

    with pytest.raises(ValueError) as exc_info:
        _books_module().load_book_catalog(tmp_path)

    assert str(exc_info.value) == f"{tmp_path}: undeclared book root book3 is a symlink"


@pytest.mark.parametrize("consumer", ["validate", "imports", "evidence", "resolve"])
def test_post_catalog_book_root_symlink_swap_fails_closed(tmp_path: Path, consumer: str) -> None:
    write_two_book_repo(tmp_path)
    books = _books_module()
    catalog = books.load_book_catalog(tmp_path)
    selected_id = "book1" if consumer == "resolve" else "book2"
    selected = catalog.by_id(selected_id)
    replacement = tmp_path / f"real-{selected_id}"
    selected.root.rename(replacement)
    selected.root.symlink_to(replacement, target_is_directory=True)

    if consumer == "validate":
        assert books.validate_book_root(selected) == [
            f"{selected_id}: book root is symlinked or no longer canonical: {selected.root}"
        ]
        return
    operation = {
        "imports": lambda: books.load_book_imports(selected),
        "evidence": lambda: books.load_book_evidence_imports(selected),
        "resolve": lambda: books.resolve_qualified_import(
            catalog, catalog.by_id("book2"), "book1:softmax"
        ),
    }[consumer]
    with pytest.raises(ValueError, match="root is symlinked or no longer canonical"):
        operation()


@pytest.mark.parametrize("relative", REQUIRED_PATHS)
def test_selected_book_validation_reports_each_missing_required_file(
    tmp_path: Path, relative: str
) -> None:
    write_two_book_repo(tmp_path)
    missing = tmp_path / "book1" / relative
    if missing.is_dir():
        shutil.rmtree(missing)
    else:
        missing.unlink()
    catalog = _books_module().load_book_catalog(tmp_path)

    errors = _books_module().validate_book_root(catalog.by_id("book1"))

    assert any(relative in error for error in errors), errors


@pytest.mark.parametrize("directory", ["units", "reference"])
def test_empty_required_directories_need_a_tracked_marker(tmp_path: Path, directory: str) -> None:
    write_two_book_repo(tmp_path)
    (tmp_path / "book1" / directory / ".gitkeep").unlink()
    catalog = _books_module().load_book_catalog(tmp_path)

    errors = _books_module().validate_book_root(catalog.by_id("book1"))

    assert any(directory in error and "tracked" in error for error in errors), errors


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


@pytest.mark.parametrize(
    ("mutation", "identity"),
    [
        pytest.param(
            lambda raw: raw["imports"]["concepts"].append("C1-foundation"),
            "C1-foundation",
            id="prerequisite-unit-concept",
        ),
        pytest.param(
            lambda raw: raw["evidence_imports"]["lesson_paths"].append("softmax"),
            "softmax",
            id="prerequisite-concept-evidence-lesson",
        ),
        pytest.param(
            lambda raw: raw["evidence_imports"]["assessments"].append("C8-p01"),
            "C8-p01",
            id="evidence-practice-assessment",
        ),
    ],
)
def test_import_blocks_reject_cross_category_identity_collisions(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    identity: str,
) -> None:
    write_two_book_repo(tmp_path)
    _mutate_syllabus_contract(tmp_path, "book2", mutation)
    books = _books_module()
    book2 = books.load_book_catalog(tmp_path).by_id("book2")

    for loader in (books.load_book_imports, books.load_book_evidence_imports):
        with pytest.raises(ValueError, match=rf"cross-category.*{re.escape(identity)}"):
            loader(book2)


def _write_practice_owner(repo: Path, unit_id: str, practice_id: str) -> None:
    unit = repo / "book1" / "units" / unit_id
    statement = unit / "practice" / "p01.ipynb"
    statement.parent.mkdir(parents=True)
    statement.write_text("{}\n", encoding="utf-8")
    _write_yaml(
        unit / "manifest.yaml",
        {
            "unit": unit_id,
            "practice": [{"id": practice_id, "path": "practice/p01.ipynb"}],
        },
    )


def _write_assessment_owner(repo: Path, test_id: str, assessment_id: str) -> None:
    _write_yaml(
        repo / "book1" / "mocktests" / test_id / "manifest.yaml",
        {"problems": [{"id": assessment_id}]},
    )


@pytest.mark.parametrize("kind", ["practice", "assessment"])
def test_evidence_resolution_rejects_duplicate_owner_matches(tmp_path: Path, kind: str) -> None:
    write_two_book_repo(tmp_path)
    if kind == "practice":
        identity = "C8-p01"
        _write_practice_owner(tmp_path, "C8-first", identity)
        _write_practice_owner(tmp_path, "C8-second", identity)
    else:
        identity = "r1-001-p05-1"
        _write_assessment_owner(tmp_path, "r1-001", identity)
        _write_assessment_owner(tmp_path, "r1-002", identity)
    books = _books_module()
    catalog = books.load_book_catalog(tmp_path)

    with pytest.raises(ValueError, match=rf"duplicate {kind} ownership.*{re.escape(identity)}"):
        books.resolve_qualified_import(catalog, catalog.by_id("book2"), f"book1:{identity}")


def test_book_selection_parser_helper_requires_exactly_one_selection() -> None:
    parser = argparse.ArgumentParser()
    importlib.import_module("tools.cli").add_book_selection_arguments(parser)

    assert parser.parse_args(["--book", "book2"]).book == "book2"
    assert parser.parse_args(["--all"]).all_books is True
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--book", "book1", "--all"])
