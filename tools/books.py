"""Strict registry and cross-book import contracts for complete course books."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.model import load_syllabus_contract

_REGISTRY_KEYS = frozenset({"books_version", "books"})
_BOOK_KEYS = frozenset({"id", "number", "root", "depends_on"})
_IMPORT_KEYS = frozenset({"book", "units", "concepts"})
_EVIDENCE_IMPORT_KEYS = frozenset({"book", "concepts", "lesson_paths", "practices", "assessments"})
_FORBIDDEN_LEGACY_ROOTS = (
    "syllabus.md",
    "curriculum",
    "units",
    "mocktests",
    "reference",
)
_REQUIRED_FILES = (
    "syllabus.md",
    "curriculum/course-schedule.yaml",
    "curriculum/coverage-map.yaml",
    "curriculum/material-inventory.yaml",
    "curriculum/official-topics.yaml",
    "curriculum/source-manifest.yaml",
    "mocktests/blueprint.yaml",
    "docs/course-structure.md",
)
_REQUIRED_TRACKED_DIRECTORIES = ("units", "reference")
_BOOK_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True)
class BookSpec:
    id: str
    number: int
    root: Path
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class BookImports:
    source_book: str
    units: tuple[str, ...]
    concepts: tuple[str, ...]


@dataclass(frozen=True)
class BookEvidenceImports:
    source_book: str
    concepts: tuple[str, ...]
    lesson_paths: tuple[str, ...]
    practices: tuple[str, ...]
    assessments: tuple[str, ...]


@dataclass(frozen=True)
class BookCatalog:
    repo_root: Path
    books: tuple[BookSpec, ...]

    def by_id(self, book_id: str) -> BookSpec:
        for book in self.books:
            if book.id == book_id:
                return book
        available = ", ".join(book.id for book in self.books) or "<none>"
        raise KeyError(f"unknown book id {book_id!r}; available books: {available}")


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot load {label}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: {label} must be a mapping")  # noqa: TRY004
    return raw


def _require_exact_keys(raw: dict[str, Any], expected: frozenset[str], *, label: str) -> None:
    actual = set(raw)
    if actual != expected:
        missing = sorted(repr(key) for key in expected - actual)
        unexpected = sorted(repr(key) for key in actual - expected)
        raise ValueError(
            f"{label} must contain exactly {sorted(expected)}; "
            f"missing={missing}, unexpected={unexpected}"
        )


def _validated_book_id(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _BOOK_ID.fullmatch(value) is None:
        raise ValueError(f"{label} must be a valid lowercase book id")
    return value


def _ordered_unique_strings(value: object, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of strings")  # noqa: TRY004
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item or item.strip() != item:
            raise ValueError(f"{label} must be a list of nonempty strings")
        if ":" in item:
            raise ValueError(f"{label} entries must be unqualified symbols")
        if item in seen:
            raise ValueError(f"{label} contains duplicate value {item!r}")
        seen.add(item)
        result.append(item)
    return tuple(result)


def _reject_symlink_components(repo_root: Path, relative_root: Path) -> None:
    candidate = repo_root
    for part in relative_root.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError(f"book root {relative_root} contains symlink component {candidate}")


def _validated_relative_root(repo_root: Path, value: object, *, book_id: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"book {book_id}: root must be a nonempty relative path")
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(f"book {book_id}: absolute root is forbidden: {value}")
    if (
        relative == Path(".")
        or ".." in relative.parts
        or "\\" in value
        or relative.as_posix() != value
    ):
        raise ValueError(f"book {book_id}: escaping or noncanonical root is forbidden: {value}")
    _reject_symlink_components(repo_root, relative)
    resolved = (repo_root / relative).resolve(strict=False)
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"book {book_id}: escaping root is forbidden: {value}") from exc
    return resolved


def _dependency_order(books: list[BookSpec]) -> tuple[BookSpec, ...]:
    by_id = {book.id: book for book in books}
    for book in books:
        unknown = sorted(set(book.depends_on) - set(by_id))
        if unknown:
            raise ValueError(f"book {book.id}: unknown dependency/dependencies {unknown}")

    remaining = {book.id: set(book.depends_on) for book in books}
    ordered: list[BookSpec] = []
    while remaining:
        ready = sorted(
            (by_id[book_id] for book_id, dependencies in remaining.items() if not dependencies),
            key=lambda book: (book.number, book.id),
        )
        if not ready:
            cycle = ", ".join(sorted(remaining))
            raise ValueError(f"book dependency cycle detected among: {cycle}")
        for book in ready:
            ordered.append(book)
            remaining.pop(book.id)
        completed = {book.id for book in ready}
        for dependencies in remaining.values():
            dependencies.difference_update(completed)
    for book in books:
        for dependency_id in book.depends_on:
            dependency = by_id[dependency_id]
            if dependency.number >= book.number:
                raise ValueError(
                    f"book {book.id}: dependency order requires {dependency.id} "
                    f"to have a lower book number"
                )
    return tuple(ordered)


def load_book_catalog(repo_root: str | Path) -> BookCatalog:
    """Load registry structure without validating any book's content tree."""
    root = Path(repo_root).resolve()
    registry_path = root / "books.yaml"
    raw = _load_yaml_mapping(registry_path, label="book registry")
    _require_exact_keys(raw, _REGISTRY_KEYS, label=str(registry_path))
    if type(raw["books_version"]) is not int or raw["books_version"] != 1:
        raise ValueError(f"{registry_path}: books_version must be integer 1")
    records = raw["books"]
    if not isinstance(records, list) or not records:
        raise ValueError(f"{registry_path}: books must be a nonempty list")

    books: list[BookSpec] = []
    seen_ids: set[str] = set()
    seen_numbers: set[int] = set()
    seen_roots: set[Path] = set()
    for index, record in enumerate(records):
        label = f"{registry_path}: books[{index}]"
        if not isinstance(record, dict):
            raise ValueError(f"{label} must be a mapping")  # noqa: TRY004
        _require_exact_keys(record, _BOOK_KEYS, label=label)
        book_id = _validated_book_id(record["id"], label=f"{label}.id")
        number = record["number"]
        if type(number) is not int or number <= 0:
            raise ValueError(f"{label}.number must be a positive integer")
        dependencies = _ordered_unique_strings(record["depends_on"], label=f"{label}.depends_on")
        book_root = _validated_relative_root(root, record["root"], book_id=book_id)
        if book_id in seen_ids:
            raise ValueError(f"{registry_path}: duplicate book id {book_id!r}")
        if number in seen_numbers:
            raise ValueError(f"{registry_path}: duplicate book number {number}")
        if book_root in seen_roots:
            raise ValueError(f"{registry_path}: duplicate book root {record['root']!r}")
        seen_ids.add(book_id)
        seen_numbers.add(number)
        seen_roots.add(book_root)
        books.append(
            BookSpec(
                id=book_id,
                number=number,
                root=book_root,
                depends_on=dependencies,
            )
        )

    declared_roots = {book.root for book in books}
    for entry in sorted(root.iterdir(), key=lambda path: path.name):
        if not entry.name.startswith("book") or entry.name == "books.yaml":
            continue
        if not (entry.is_dir() or entry.is_symlink()):
            continue
        if entry.resolve(strict=False) not in declared_roots:
            raise ValueError(f"{root}: undeclared book root {entry.name}")
    for legacy in _FORBIDDEN_LEGACY_ROOTS:
        path = root / legacy
        if path.exists() or path.is_symlink():
            raise ValueError(f"{root}: forbidden legacy root {legacy}")

    return BookCatalog(repo_root=root, books=_dependency_order(books))


def _path_has_symlink_component(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def validate_book_root(book: BookSpec) -> list[str]:
    """Return deterministic structural diagnostics for the selected book only."""
    errors: list[str] = []
    for relative in _REQUIRED_FILES:
        path = book.root / relative
        if not path.is_file() or _path_has_symlink_component(book.root, path):
            errors.append(f"{book.id}: missing required tracked file {relative}")
    for relative in _REQUIRED_TRACKED_DIRECTORIES:
        path = book.root / relative
        if not path.is_dir() or path.is_symlink():
            errors.append(f"{book.id}: missing required tracked directory {relative}")
            continue
        tracked_files = sorted(
            candidate
            for candidate in path.rglob("*")
            if candidate.is_file() and not _path_has_symlink_component(book.root, candidate)
        )
        if not tracked_files:
            errors.append(
                f"{book.id}: required directory {relative} needs tracked content or .gitkeep"
            )
    return errors


def _book_contract(book: BookSpec) -> dict[str, Any]:
    try:
        _resolve_owner_path(book, "syllabus.md")
        return load_syllabus_contract(book.root)
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise ValueError(f"{book.root / 'syllabus.md'}: invalid canonical syllabus: {exc}") from exc


def load_book_imports(book: BookSpec) -> BookImports:
    raw = _book_contract(book).get("imports")
    if raw is None:
        return BookImports(source_book="", units=(), concepts=())
    if not isinstance(raw, dict):
        raise ValueError(  # noqa: TRY004
            f"{book.root / 'syllabus.md'}: imports must be a mapping"
        )
    _require_exact_keys(raw, _IMPORT_KEYS, label=f"{book.root / 'syllabus.md'}: imports")
    return BookImports(
        source_book=_validated_book_id(raw["book"], label="imports.book"),
        units=_ordered_unique_strings(raw["units"], label="imports.units"),
        concepts=_ordered_unique_strings(raw["concepts"], label="imports.concepts"),
    )


def load_book_evidence_imports(book: BookSpec) -> BookEvidenceImports:
    raw = _book_contract(book).get("evidence_imports")
    if raw is None:
        return BookEvidenceImports(
            source_book="", concepts=(), lesson_paths=(), practices=(), assessments=()
        )
    if not isinstance(raw, dict):
        raise ValueError(  # noqa: TRY004
            f"{book.root / 'syllabus.md'}: evidence_imports must be a mapping"
        )
    _require_exact_keys(
        raw,
        _EVIDENCE_IMPORT_KEYS,
        label=f"{book.root / 'syllabus.md'}: evidence_imports",
    )
    lesson_paths = _ordered_unique_strings(
        raw["lesson_paths"], label="evidence_imports.lesson_paths"
    )
    for lesson_path in lesson_paths:
        relative = Path(lesson_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative == Path(".")
            or "\\" in lesson_path
            or relative.as_posix() != lesson_path
        ):
            raise ValueError(
                f"evidence_imports.lesson_paths contains escaping path {lesson_path!r}"
            )
    return BookEvidenceImports(
        source_book=_validated_book_id(raw["book"], label="evidence_imports.book"),
        concepts=_ordered_unique_strings(raw["concepts"], label="evidence_imports.concepts"),
        lesson_paths=lesson_paths,
        practices=_ordered_unique_strings(raw["practices"], label="evidence_imports.practices"),
        assessments=_ordered_unique_strings(
            raw["assessments"], label="evidence_imports.assessments"
        ),
    )


def _owner_symbols(owner: BookSpec) -> tuple[set[str], set[str]]:
    raw = _book_contract(owner)
    raw_units = raw.get("units")
    raw_concepts = raw.get("concepts")
    if not isinstance(raw_units, list) or not isinstance(raw_concepts, list):
        raise ValueError(  # noqa: TRY004
            f"{owner.root / 'syllabus.md'}: units and concepts must be lists"
        )
    units = {
        item["id"]
        for item in raw_units
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    concepts = {
        item["id"]
        for item in raw_concepts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    return units, concepts


def _resolve_owner_path(owner: BookSpec, relative_value: str) -> Path:
    relative = Path(relative_value)
    if (
        relative.is_absolute()
        or relative == Path(".")
        or ".." in relative.parts
        or "\\" in relative_value
        or relative.as_posix() != relative_value
    ):
        raise ValueError(f"owner path {relative_value!r} is escaping or absolute")
    target = owner.root / relative
    try:
        target.resolve(strict=False).relative_to(owner.root)
    except ValueError as exc:
        raise ValueError(f"owner path {relative_value!r} escapes {owner.id}") from exc
    if _path_has_symlink_component(owner.root, target):
        raise ValueError(f"owner path {relative_value!r} contains a symlink")
    if not target.is_file():
        raise ValueError(f"owner {owner.id} is missing path {relative_value!r}")
    return target


def _resolve_practice(owner: BookSpec, practice_id: str) -> Path:
    for manifest_path in sorted(owner.root.glob("units/*/manifest.yaml")):
        if _path_has_symlink_component(owner.root, manifest_path):
            continue
        raw = _load_yaml_mapping(manifest_path, label="unit manifest")
        practices = raw.get("practice") or []
        if not isinstance(practices, list):
            raise ValueError(  # noqa: TRY004
                f"{manifest_path}: practice must be a list"
            )
        for row in practices:
            if not isinstance(row, dict) or row.get("id") != practice_id:
                continue
            path = row.get("path")
            if not isinstance(path, str):
                raise ValueError(  # noqa: TRY004
                    f"{manifest_path}: practice {practice_id} has no valid path"
                )
            relative_path = manifest_path.parent.relative_to(owner.root) / path
            return _resolve_owner_path(owner, str(relative_path))
    raise ValueError(f"owner {owner.id} is missing practice {practice_id!r}")


def _resolve_assessment(owner: BookSpec, assessment_id: str) -> Path:
    pattern = f"mocktests/r{owner.number}-*/manifest.yaml"
    for manifest_path in sorted(owner.root.glob(pattern)):
        if _path_has_symlink_component(owner.root, manifest_path):
            continue
        raw = _load_yaml_mapping(manifest_path, label="mock manifest")
        problems = raw.get("problems") or []
        if not isinstance(problems, list):
            raise ValueError(  # noqa: TRY004
                f"{manifest_path}: problems must be a list"
            )
        if any(isinstance(row, dict) and row.get("id") == assessment_id for row in problems):
            return manifest_path
    raise ValueError(f"owner {owner.id} is missing assessment {assessment_id!r}")


def resolve_qualified_import(catalog: BookCatalog, importer: BookSpec, identity: str) -> Path:
    """Resolve one exact, qualified prerequisite or evidence import to its owner."""
    if not isinstance(identity, str) or identity.count(":") != 1:
        raise ValueError(f"import {identity!r} must be qualified as book:id")
    owner_id, local_id = identity.split(":", 1)
    if not owner_id or not local_id:
        raise ValueError(f"import {identity!r} must be qualified as book:id")
    try:
        registered_importer = catalog.by_id(importer.id)
    except KeyError as exc:
        raise ValueError(f"importer {importer.id!r} is not registered") from exc
    if registered_importer != importer:
        raise ValueError(f"importer {importer.id!r} does not match its registered BookSpec")
    if owner_id == importer.id:
        raise ValueError(f"import {identity!r} names the importer as owner")
    try:
        owner = catalog.by_id(owner_id)
    except KeyError as exc:
        raise ValueError(f"import {identity!r} names an unknown owner") from exc
    if owner_id not in importer.depends_on:
        raise ValueError(f"import {identity!r} lacks a declared dependency edge")

    imports = load_book_imports(importer)
    evidence = load_book_evidence_imports(importer)
    categories: list[tuple[str, str]] = []
    if local_id in imports.units:
        categories.append(("unit", imports.source_book))
    if local_id in imports.concepts:
        categories.append(("concept", imports.source_book))
    if local_id in evidence.concepts:
        categories.append(("concept", evidence.source_book))
    if local_id in evidence.lesson_paths:
        categories.append(("lesson", evidence.source_book))
    if local_id in evidence.practices:
        categories.append(("practice", evidence.source_book))
    if local_id in evidence.assessments:
        categories.append(("assessment", evidence.source_book))
    if not categories:
        raise ValueError(f"import {identity!r} is not in an exact import allowlist")
    allowed_categories = [category for category, source in categories if source == owner_id]
    if not allowed_categories:
        raise ValueError(f"import {identity!r} names the wrong owner")

    owner_units, owner_concepts = _owner_symbols(owner)
    importer_units, importer_concepts = _owner_symbols(importer)
    for category in allowed_categories:
        if category == "unit":
            if local_id in importer_units:
                raise ValueError(f"import {identity!r} has an importer ownership collision")
            if local_id not in owner_units:
                raise ValueError(f"owner {owner.id} is missing unit {local_id!r}")
            return owner.root / "syllabus.md"
        if category == "concept":
            if local_id in importer_concepts:
                raise ValueError(f"import {identity!r} has an importer ownership collision")
            if local_id not in owner_concepts:
                raise ValueError(f"owner {owner.id} is missing concept {local_id!r}")
            return owner.root / "syllabus.md"
        if category == "lesson":
            return _resolve_owner_path(owner, local_id)
        if category == "practice":
            return _resolve_practice(owner, local_id)
        if category == "assessment":
            return _resolve_assessment(owner, local_id)
    raise AssertionError("unreachable import category")
