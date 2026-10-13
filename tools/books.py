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
# Optional publication keys (Plan 030 D1). A `publication: true` book must carry a title and a
# subtitle; tools key on the `publication` flag, never on book ids.
_BOOK_OPTIONAL_KEYS = frozenset({"title", "subtitle", "publication"})
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
    title: str = ""
    subtitle: str = ""
    publication: bool = False


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


def resolve_contained_path(
    root: str | Path,
    relative: str | Path,
    *,
    label: str = "content path",
    must_exist: bool = True,
) -> Path:
    """Resolve a book-local path without permitting traversal or symlink indirection."""
    canonical_root = Path(root)
    if (
        not canonical_root.is_absolute()
        or canonical_root.is_symlink()
        or canonical_root.resolve(strict=False) != canonical_root
    ):
        raise ValueError(f"{label}: selected book root is not canonical: {canonical_root}")
    requested = Path(relative)
    if requested.is_absolute():
        candidate = requested
    else:
        if ".." in requested.parts:
            raise ValueError(f"{label}: path escapes selected book root: {relative}")
        candidate = canonical_root / requested
    try:
        lexical = candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes selected book root: {relative}") from exc
    current = canonical_root
    for part in lexical.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label}: symlink component is forbidden: {current}")
    if must_exist and not candidate.exists():
        raise ValueError(f"{label}: path does not exist: {relative}")
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError(f"{label}: resolved path escapes selected book root: {relative}") from exc
    return resolved


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


def _require_book_keys(raw: dict[str, Any], *, label: str) -> None:
    actual = set(raw)
    missing = sorted(repr(key) for key in _BOOK_KEYS - actual)
    unexpected = sorted(repr(key) for key in actual - _BOOK_KEYS - _BOOK_OPTIONAL_KEYS)
    if missing or unexpected:
        raise ValueError(
            f"{label} must contain exactly {sorted(_BOOK_KEYS)} plus optional "
            f"{sorted(_BOOK_OPTIONAL_KEYS)}; missing={missing}, unexpected={unexpected}"
        )


def _publication_fields(raw: dict[str, Any], *, label: str) -> tuple[str, str, bool]:
    publication = raw.get("publication", False)
    if type(publication) is not bool:
        raise ValueError(f"{label}.publication must be a boolean")
    texts: list[str] = []
    for key in ("title", "subtitle"):
        value = raw.get(key, "")
        if not isinstance(value, str) or value.strip() != value or "\n" in value:
            raise ValueError(f"{label}.{key} must be a single-line string without edge spaces")
        if publication and not value:
            raise ValueError(f"{label}: a publication book needs a nonempty {key}")
        texts.append(value)
    return texts[0], texts[1], publication


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
        _require_book_keys(record, label=label)
        title, subtitle, publication = _publication_fields(record, label=label)
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
                title=title,
                subtitle=subtitle,
                publication=publication,
            )
        )

    declared_roots = {book.root for book in books}
    for entry in sorted(root.iterdir(), key=lambda path: path.name):
        if not entry.name.startswith("book") or entry.name == "books.yaml":
            continue
        if not (entry.is_dir() or entry.is_symlink()):
            continue
        if entry.is_symlink():
            raise ValueError(f"{root}: undeclared book root {entry.name} is a symlink")
        if entry.resolve(strict=False) not in declared_roots:
            raise ValueError(f"{root}: undeclared book root {entry.name}")
    for legacy in _FORBIDDEN_LEGACY_ROOTS:
        path = root / legacy
        if path.exists() or path.is_symlink():
            raise ValueError(f"{root}: forbidden legacy root {legacy}")

    return BookCatalog(repo_root=root, books=_dependency_order(books))


def _path_has_symlink_component(root: Path, path: Path) -> bool:
    if not root.is_absolute() or root.is_symlink() or root.resolve(strict=False) != root:
        return True
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _book_root_diagnostic(book: BookSpec) -> str | None:
    root = book.root
    if not root.is_absolute() or root.is_symlink() or root.resolve(strict=False) != root:
        return f"{book.id}: book root is symlinked or no longer canonical: {root}"
    if not root.is_dir():
        return f"{book.id}: book root is missing or not a directory: {root}"
    return None


def _require_book_root(book: BookSpec) -> None:
    diagnostic = _book_root_diagnostic(book)
    if diagnostic is not None:
        raise ValueError(diagnostic)


def validate_book_root(book: BookSpec) -> list[str]:
    """Return deterministic structural diagnostics for the selected book only."""
    root_diagnostic = _book_root_diagnostic(book)
    if root_diagnostic is not None:
        return [root_diagnostic]
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


def _parse_book_imports(book: BookSpec, contract: dict[str, Any]) -> BookImports:
    raw = contract.get("imports")
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


def _parse_book_evidence_imports(book: BookSpec, contract: dict[str, Any]) -> BookEvidenceImports:
    raw = contract.get("evidence_imports")
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


def _load_validated_import_blocks(
    book: BookSpec,
) -> tuple[BookImports, BookEvidenceImports]:
    contract = _book_contract(book)
    imports = _parse_book_imports(book, contract)
    evidence = _parse_book_evidence_imports(book, contract)
    categories = (
        ("prerequisite units", imports.units),
        ("prerequisite concepts", imports.concepts),
        ("evidence concepts", evidence.concepts),
        ("evidence lesson paths", evidence.lesson_paths),
        ("evidence practices", evidence.practices),
        ("evidence assessments", evidence.assessments),
    )
    owners: dict[str, str] = {}
    for category, identities in categories:
        for identity in identities:
            previous = owners.get(identity)
            if previous is not None:
                raise ValueError(
                    f"{book.root / 'syllabus.md'}: cross-category import identity "
                    f"{identity!r} appears in {previous} and {category}"
                )
            owners[identity] = category
    return imports, evidence


def load_book_imports(book: BookSpec) -> BookImports:
    imports, _ = _load_validated_import_blocks(book)
    return imports


def load_book_evidence_imports(book: BookSpec) -> BookEvidenceImports:
    _, evidence = _load_validated_import_blocks(book)
    return evidence


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
    _require_book_root(owner)
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
    matches: list[tuple[Path, object]] = []
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
            matches.append((manifest_path, row.get("path")))
    if not matches:
        raise ValueError(f"owner {owner.id} is missing practice {practice_id!r}")
    if len(matches) > 1:
        locations = ", ".join(str(manifest) for manifest, _ in matches)
        raise ValueError(
            f"owner {owner.id} has duplicate practice ownership for {practice_id!r}: {locations}"
        )
    manifest_path, path = matches[0]
    if not isinstance(path, str):
        raise ValueError(  # noqa: TRY004
            f"{manifest_path}: practice {practice_id} has no valid path"
        )
    relative_path = manifest_path.parent.relative_to(owner.root) / path
    return _resolve_owner_path(owner, str(relative_path))


def _resolve_assessment(owner: BookSpec, assessment_id: str) -> Path:
    pattern = f"mocktests/r{owner.number}-*/manifest.yaml"
    matches: list[Path] = []
    for manifest_path in sorted(owner.root.glob(pattern)):
        if _path_has_symlink_component(owner.root, manifest_path):
            continue
        raw = _load_yaml_mapping(manifest_path, label="mock manifest")
        problems = raw.get("problems") or []
        if not isinstance(problems, list):
            raise ValueError(  # noqa: TRY004
                f"{manifest_path}: problems must be a list"
            )
        matches.extend(
            manifest_path
            for row in problems
            if isinstance(row, dict) and row.get("id") == assessment_id
        )
    if not matches:
        raise ValueError(f"owner {owner.id} is missing assessment {assessment_id!r}")
    if len(matches) > 1:
        locations = ", ".join(str(manifest) for manifest in matches)
        raise ValueError(
            f"owner {owner.id} has duplicate assessment ownership for "
            f"{assessment_id!r}: {locations}"
        )
    return matches[0]


def _require_catalog_book(catalog: BookCatalog, book: BookSpec) -> BookSpec:
    repo_root = catalog.repo_root
    if (
        not repo_root.is_absolute()
        or repo_root.is_symlink()
        or repo_root.resolve(strict=False) != repo_root
        or not repo_root.is_dir()
    ):
        raise ValueError(f"catalog repository root is no longer canonical: {repo_root}")
    try:
        registered = catalog.by_id(book.id)
    except KeyError as exc:
        raise ValueError(f"book {book.id!r} is not registered") from exc
    if registered != book:
        raise ValueError(f"book {book.id!r} does not match its registered BookSpec")
    try:
        book.root.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"book {book.id!r} root escapes the catalog repository") from exc
    _require_book_root(book)
    return registered


def resolve_qualified_import(catalog: BookCatalog, importer: BookSpec, identity: str) -> Path:
    """Resolve one exact, qualified prerequisite or evidence import to its owner."""
    _require_catalog_book(catalog, importer)
    if not isinstance(identity, str) or identity.count(":") != 1:
        raise ValueError(f"import {identity!r} must be qualified as book:id")
    owner_id, local_id = identity.split(":", 1)
    if not owner_id or not local_id:
        raise ValueError(f"import {identity!r} must be qualified as book:id")
    if owner_id == importer.id:
        raise ValueError(f"import {identity!r} names the importer as owner")
    try:
        owner = catalog.by_id(owner_id)
    except KeyError as exc:
        raise ValueError(f"import {identity!r} names an unknown owner") from exc
    _require_catalog_book(catalog, owner)
    if owner_id not in importer.depends_on:
        raise ValueError(f"import {identity!r} lacks a declared dependency edge")

    imports, evidence = _load_validated_import_blocks(importer)
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


# --- per-book publication config (Plan 030 D1; py4kids `publication_config_errors`) ----------

PUBLICATION_CONFIG = "publication.yaml"
RUNNING_HEAD_MAX = 32
_PUBLICATION_KEYS = frozenset({"publication_version", "student_answers", "chapters", "mocktests", "audit"})
_PUBLICATION_OPTIONAL_KEYS = frozenset({"volumes"})
_CHAPTER_KEYS = frozenset({"unit", "title"})
_CHAPTER_OPTIONAL_KEYS = frozenset({"head"})
_SELECTOR_KEYS = frozenset({"set", "type", "difficulty"})
_VOLUME_KEYS = frozenset({"title", "first", "last"})
_VOLUMES_KEYS = frozenset({"editions", "parts"})
_AUDIT_KEYS = frozenset({"page_warning"})
_MOCKTEST_ID = re.compile(r"r\d+-\d{3}\Z")
# The edition names (tools.publish.EDITIONS holds their profiles and must use exactly these).
EDITION_NAMES = ("student-print", "student", "answer-key", "teacher")


@dataclass(frozen=True)
class ChapterSpec:
    unit: str
    title: str
    head: str


@dataclass(frozen=True)
class VolumeSpec:
    number: int
    title: str
    units: tuple[str, ...]


@dataclass(frozen=True)
class PublicationConfig:
    """Everything book-specific the publisher and the audit need (`<book>/publication.yaml`)."""

    chapters: tuple[ChapterSpec, ...]
    student_answers: dict[str, tuple[str, ...]]
    mocktests: tuple[str, ...]
    volume_editions: tuple[str, ...]
    volumes: tuple[VolumeSpec, ...]
    audit: dict[str, Any]

    def chapter(self, unit: str) -> ChapterSpec:
        for chapter in self.chapters:
            if chapter.unit == unit:
                return chapter
        raise KeyError(unit)

    @property
    def units(self) -> tuple[str, ...]:
        return tuple(chapter.unit for chapter in self.chapters)


def output_pdf_name(book_id: str, edition: str, volume: int | None = None) -> str:
    """An edition PDF's file name: `<book>-<edition>.pdf` or `<book>-<edition>-vol<N>.pdf`."""
    suffix = "" if volume is None else f"-vol{volume}"
    return f"{book_id}-{edition}{suffix}.pdf"


# Plan 031 D1: a unit's id (`F3-multivar-calculus`) and its folder are separate.
# Book 1 folders carry a two-digit teaching-order prefix (`03-F3-multivar-calculus`);
# Book 2 folders and unprefixed fixture trees are named by the id itself.
_UNIT_FOLDER = re.compile(r"(?P<order>\d{2})-(?P<id>[A-Za-z].*)\Z")


def unit_id_of(folder: str) -> str:
    """The unit id a folder name holds: `NN-<id>` -> `<id>`; any other name is its own id."""
    match = _UNIT_FOLDER.match(folder)
    return match.group("id") if match else folder


def unit_dir(book_root: Path, unit_id: str) -> Path:
    """The folder of `unit_id` under `<book_root>/units`: `NN-<id>` or `<id>`, exactly one."""
    units = Path(book_root) / "units"
    found = []
    if (units / unit_id).is_dir():
        found.append(units / unit_id)
    if units.is_dir():
        found.extend(
            path
            for path in sorted(units.iterdir())
            if path.is_dir() and _UNIT_FOLDER.match(path.name) and unit_id_of(path.name) == unit_id
        )
    if not found:
        raise ValueError(f"{units}: no folder for unit {unit_id!r} (expected NN-{unit_id} or {unit_id})")
    if len(found) > 1:
        names = ", ".join(path.name for path in found)
        raise ValueError(f"{units}: unit {unit_id!r} has more than one folder: {names}")
    return found[0]


def unit_relpath(book_root: Path, unit_id: str) -> str:
    """`units/<folder>` for `unit_id`, relative to the book root (POSIX)."""
    return unit_dir(book_root, unit_id).relative_to(Path(book_root)).as_posix()


def live_units(book: BookSpec) -> tuple[str, ...]:
    """The book's live unit ids: `units/<folder>/` directories that hold a `manifest.yaml`."""
    _require_book_root(book)
    return tuple(
        unit_id_of(manifest.parent.name)
        for manifest in sorted(book.root.glob("units/*/manifest.yaml"))
        if not _path_has_symlink_component(book.root, manifest)
    )


def live_mocktests(book: BookSpec) -> tuple[str, ...]:
    _require_book_root(book)
    return tuple(
        manifest.parent.name
        for manifest in sorted(book.root.glob("mocktests/*/manifest.yaml"))
        if not _path_has_symlink_component(book.root, manifest)
    )


def _key_errors(raw: dict[str, Any], required: frozenset[str], optional: frozenset[str],
                label: str) -> list[str]:
    errors: list[str] = []
    missing = sorted(required - set(raw))
    unexpected = sorted(set(raw) - required - optional)
    if missing:
        errors.append(f"{label}: missing key(s) {missing}")
    if unexpected:
        errors.append(f"{label}: unknown key(s) {unexpected}")
    return errors


def _single_line(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value and "\n" not in value


def _parse_publication_config(
    book: BookSpec,
) -> tuple[PublicationConfig | None, list[str]]:
    where = f"{book.id}/{PUBLICATION_CONFIG}"
    if not book.publication:
        return None, [f"{book.id}: not a publication book (books.yaml publication: true)"]
    diagnostic = _book_root_diagnostic(book)
    if diagnostic is not None:
        return None, [diagnostic]
    path = book.root / PUBLICATION_CONFIG
    if not path.is_file() or _path_has_symlink_component(book.root, path):
        return None, [f"{where}: missing (every publication book needs one; Plan 030 D1)"]
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"{where}: cannot load: {exc}"]
    if not isinstance(raw, dict):
        return None, [f"{where}: must be a mapping"]
    errors = _key_errors(raw, _PUBLICATION_KEYS, _PUBLICATION_OPTIONAL_KEYS, where)
    if errors:
        return None, errors

    if raw["publication_version"] != 1 or type(raw["publication_version"]) is not int:
        errors.append(f"{where}: publication_version must be integer 1")

    # chapters: the unit order, explicit titles, and running heads for long titles.
    chapters: list[ChapterSpec] = []
    raw_chapters = raw["chapters"]
    if not isinstance(raw_chapters, list) or not raw_chapters:
        errors.append(f"{where}: chapters must be a nonempty list")
        raw_chapters = []
    seen_units: set[str] = set()
    for index, entry in enumerate(raw_chapters):
        label = f"{where}: chapters[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        entry_errors = _key_errors(entry, _CHAPTER_KEYS, _CHAPTER_OPTIONAL_KEYS, label)
        if entry_errors:
            errors.extend(entry_errors)
            continue
        unit, title, head = entry["unit"], entry["title"], entry.get("head")
        if not _single_line(unit) or not _single_line(title):
            errors.append(f"{label}: unit and title must be nonempty single-line strings")
            continue
        if unit in seen_units:
            errors.append(f"{label}: duplicate unit {unit}")
            continue
        seen_units.add(unit)
        if head is None:
            if len(title) > RUNNING_HEAD_MAX:
                errors.append(
                    f"{label}: title of {unit} is over {RUNNING_HEAD_MAX} characters and "
                    "needs a running head (head:)"
                )
                continue
            head = title
        elif not _single_line(head) or len(head) > RUNNING_HEAD_MAX:
            errors.append(
                f"{label}: head must be a single-line string of at most {RUNNING_HEAD_MAX} characters"
            )
            continue
        chapters.append(ChapterSpec(unit=unit, title=title, head=head))
    live = live_units(book)
    missing_units = sorted(set(live) - seen_units)
    extra_units = sorted(seen_units - set(live))
    if missing_units:
        errors.append(f"{where}: chapters omit live unit(s) {missing_units}")
    if extra_units:
        errors.append(f"{where}: chapters list unit(s) that are not live {extra_units}")

    # student_answers: a manifest practice-row selector (default {set: A}).
    selector: dict[str, tuple[str, ...]] = {}
    raw_selector = raw["student_answers"]
    if not isinstance(raw_selector, dict) or not raw_selector:
        errors.append(f"{where}: student_answers must be a nonempty mapping")
    else:
        unknown = sorted(set(raw_selector) - _SELECTOR_KEYS)
        if unknown:
            errors.append(f"{where}: student_answers has unknown key(s) {unknown}")
        for key, value in raw_selector.items():
            if key not in _SELECTOR_KEYS:
                continue
            values = [value] if isinstance(value, str) else value
            if not isinstance(values, list) or not values or not all(
                _single_line(item) for item in values
            ):
                errors.append(f"{where}: student_answers.{key} must be a string or list of strings")
                continue
            selector[key] = tuple(values)

    # mocktests: the Teacher's Edition mock part.
    mocktests: list[str] = []
    raw_mocktests = raw["mocktests"]
    if not isinstance(raw_mocktests, list):
        errors.append(f"{where}: mocktests must be a list")
        raw_mocktests = []
    present = set(live_mocktests(book))
    for test in raw_mocktests:
        if not isinstance(test, str) or _MOCKTEST_ID.fullmatch(test) is None:
            errors.append(f"{where}: mocktests entry {test!r} is not a mock-test id")
            continue
        if test in mocktests:
            errors.append(f"{where}: duplicate mock test {test}")
            continue
        if test not in present:
            errors.append(f"{where}: mock test {test} is listed but absent (mocktests/{test}/manifest.yaml)")
            continue
        mocktests.append(test)

    # volumes (optional, D8): contiguous unit ranges covering every chapter, in order.
    volume_editions: tuple[str, ...] = ()
    volumes: list[VolumeSpec] = []
    if "volumes" in raw:
        raw_volumes = raw["volumes"]
        if not isinstance(raw_volumes, dict):
            errors.append(f"{where}: volumes must be a mapping")
        else:
            volume_errors = _key_errors(raw_volumes, _VOLUMES_KEYS, frozenset(), f"{where}: volumes")
            errors.extend(volume_errors)
            if not volume_errors:
                editions = raw_volumes["editions"]
                if not isinstance(editions, list) or not editions or not all(
                    _single_line(item) for item in editions
                ):
                    errors.append(f"{where}: volumes.editions must be a nonempty list of edition names")
                elif sorted(set(editions) - set(EDITION_NAMES)) or len(set(editions)) != len(editions):
                    errors.append(
                        f"{where}: volumes.editions must be distinct names from {list(EDITION_NAMES)}"
                    )
                else:
                    volume_editions = tuple(editions)
                volumes, part_errors = _parse_volumes(raw_volumes["parts"], chapters, where)
                errors.extend(part_errors)

    audit = raw["audit"]
    if not isinstance(audit, dict):
        errors.append(f"{where}: audit must be a mapping")
        audit = {}
    else:
        errors.extend(_key_errors(audit, frozenset(), _AUDIT_KEYS, f"{where}: audit"))
        page_warning = audit.get("page_warning")
        if page_warning is not None and (type(page_warning) is not int or page_warning <= 0):
            errors.append(f"{where}: audit.page_warning must be a positive integer")

    if errors:
        return None, errors
    return (
        PublicationConfig(
            chapters=tuple(chapters),
            student_answers=selector,
            mocktests=tuple(mocktests),
            volume_editions=volume_editions,
            volumes=tuple(volumes),
            audit=dict(audit),
        ),
        [],
    )


def _parse_volumes(
    raw_parts: object, chapters: list[ChapterSpec], where: str
) -> tuple[list[VolumeSpec], list[str]]:
    if not isinstance(raw_parts, list) or len(raw_parts) < 2:
        return [], [f"{where}: volumes.parts must list at least two volumes"]
    order = [chapter.unit for chapter in chapters]
    errors: list[str] = []
    volumes: list[VolumeSpec] = []
    expected_start = 0
    for index, part in enumerate(raw_parts):
        label = f"{where}: volumes.parts[{index}]"
        if not isinstance(part, dict):
            errors.append(f"{label}: must be a mapping")
            return [], errors
        part_errors = _key_errors(part, _VOLUME_KEYS, frozenset(), label)
        if part_errors:
            return [], errors + part_errors
        if not _single_line(part["title"]):
            errors.append(f"{label}: title must be a nonempty single-line string")
        first, last = part["first"], part["last"]
        if first not in order or last not in order:
            errors.append(f"{label}: first/last must be configured chapter units")
            return [], errors
        start, stop = order.index(first), order.index(last)
        if start != expected_start or stop < start:
            errors.append(
                f"{label}: volumes must be contiguous chapter ranges in config order "
                f"(expected to start at {order[expected_start] if expected_start < len(order) else 'end'})"
            )
            return [], errors
        volumes.append(VolumeSpec(number=index + 1, title=str(part["title"]),
                                  units=tuple(order[start:stop + 1])))
        expected_start = stop + 1
    if expected_start != len(order):
        errors.append(f"{where}: volumes leave chapter(s) {order[expected_start:]} uncovered")
    return volumes, errors


def publication_config_errors(repo_root: str | Path, book_id: str) -> list[str]:
    """Every problem with a book's `publication.yaml` (empty when it is valid)."""
    try:
        book = load_book_catalog(repo_root).by_id(book_id)
    except (KeyError, ValueError) as exc:
        return [str(exc)]
    return _parse_publication_config(book)[1]


def load_publication_config(book: BookSpec) -> PublicationConfig:
    """Load and validate a publication book's `publication.yaml`; fail loudly when it is bad."""
    config, errors = _parse_publication_config(book)
    if config is None:
        raise ValueError("; ".join(errors))
    return config
