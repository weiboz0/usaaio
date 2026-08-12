"""Build the deterministic evidence inventory used by the curriculum audit.

This module deliberately records candidates, not coverage judgments.  Notebook
source participates in a semantic digest, but raw source is not copied into the
generated inventory.
"""

from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from tools.books import BookSpec
from tools.checks.schedule import load_validated_schedule, scheduled_baseline_minutes
from tools.model import CourseSchedule

INVENTORY_PATH = Path("curriculum/material-inventory.yaml")
ScheduleLoader = Callable[[str | Path], CourseSchedule]


class InventoryError(ValueError):
    """An inventory input could not be read or parsed."""


def _normalized_text(value: object) -> str:
    if isinstance(value, list):
        value = "".join(str(part) for part in value)
    if not isinstance(value, str):
        raise TypeError(f"expected text source, got {type(value).__name__}")
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _jsonable(value: Any) -> Any:
    """Retain YAML scalar types while producing stable JSON-compatible data."""
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("YAML mapping keys must be strings")
        return {
            key: _jsonable(item)
            for key, item in sorted(value.items(), key=lambda pair: pair[0].encode("utf-8"))
        }
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dt.datetime):
        return {"__yaml_datetime__": value.isoformat()}
    if isinstance(value, dt.date):
        return {"__yaml_date__": value.isoformat()}
    if isinstance(value, bytes):
        return {"__yaml_bytes__": base64.b64encode(value).decode("ascii")}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"unsupported YAML value {type(value).__name__}")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_text(path: Path, relative_path: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InventoryError(f"{relative_path}: cannot read: {exc}") from exc


def _load_yaml(path: Path, relative_path: str) -> Any:
    try:
        return yaml.safe_load(_read_text(path, relative_path))
    except yaml.YAMLError as exc:
        raise InventoryError(f"{relative_path}: invalid YAML: {exc}") from exc


def manifest_record(path: Path, relative_path: str) -> dict[str, Any]:
    """Return a full-object semantic hash for a YAML manifest."""
    try:
        parsed = _load_yaml(path, relative_path)
        digest = _sha256(_canonical_json(parsed))
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InventoryError):
            raise
        raise InventoryError(f"{relative_path}: cannot canonicalize YAML: {exc}") from exc
    return {"path": relative_path, "kind": "yaml", "semantic_sha256": digest}


_ATX_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_SETEXT_HEADING = re.compile(r"^[ \t]*(=+|-+)[ \t]*$")
_API_CALL = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w+)+(?=\s*\()")


def _api_calls(source: str) -> set[str]:
    tokens = set(_API_CALL.findall(source))
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return tokens
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in imported
        ):
            tokens.add(imported[node.func.id])
    return tokens


def _headings(source: str) -> list[tuple[int, str]]:
    lines = source.splitlines()
    result: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        atx = _ATX_HEADING.match(line)
        if atx:
            result.append((len(atx.group(1)), atx.group(2).strip()))
            continue
        setext = _SETEXT_HEADING.match(line)
        if setext and index and lines[index - 1].strip():
            level = 1 if setext.group(1).startswith("=") else 2
            result.append((level, lines[index - 1].strip()))
    return result


def _attachment_view(raw: object) -> list[dict[str, str]]:
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise TypeError("attachments must be a mapping")
    result: list[dict[str, str]] = []
    for name in sorted(raw, key=lambda item: str(item).encode("utf-8")):
        mime_map = raw[name]
        if not isinstance(name, str) or not isinstance(mime_map, dict):
            raise TypeError("attachment names and MIME maps must be mappings of strings")
        for mime in sorted(mime_map, key=lambda item: str(item).encode("utf-8")):
            encoded = mime_map[mime]
            if isinstance(encoded, list):
                encoded = "".join(str(part) for part in encoded)
            if not isinstance(mime, str) or not isinstance(encoded, str):
                raise TypeError("attachment MIME payloads must be strings")
            try:
                payload = base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise ValueError(f"invalid base64 attachment {name!r}/{mime!r}") from exc
            result.append({"name": name, "mime": mime, "sha256": _sha256(payload)})
    return result


def notebook_record(path: Path, relative_path: str) -> dict[str, Any]:
    """Return canonical notebook evidence without retaining raw source."""
    try:
        raw = json.loads(_read_text(path, relative_path))
        cells = raw["cells"]
        if not isinstance(cells, list):
            raise TypeError("cells must be a list")
        semantic_cells: list[dict[str, Any]] = []
        anchors: list[dict[str, Any]] = []
        heading_path: list[str] = []
        ordinals: defaultdict[tuple[str, ...], int] = defaultdict(int)
        api_tokens: set[str] = set()

        for cell in cells:
            if not isinstance(cell, dict):
                raise TypeError("each cell must be a mapping")
            cell_type = cell["cell_type"]
            source = _normalized_text(cell.get("source", ""))
            if not isinstance(cell_type, str):
                raise TypeError("cell_type must be a string")
            attachments = _attachment_view(cell.get("attachments")) if cell_type == "markdown" else []
            semantic_cells.append(
                {"cell_type": cell_type, "source": source, "attachments": attachments}
            )

            if cell_type == "markdown":
                for level, title in _headings(source):
                    heading_path = heading_path[: level - 1]
                    heading_path.append(title)
            elif cell_type == "code":
                api_tokens.update(_api_calls(source))

            heading_key = tuple(heading_path)
            ordinals[heading_key] += 1
            ordinal = ordinals[heading_key]
            human_heading = " > ".join(heading_path) if heading_path else "(document root)"
            anchors.append(
                {
                    "anchor": f"{relative_path} :: {human_heading} :: cell {ordinal}",
                    "heading_path": list(heading_path),
                    "cell_ordinal": ordinal,
                }
            )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, InventoryError):
            raise
        raise InventoryError(f"{relative_path}: invalid notebook: {exc}") from exc

    return {
        "path": relative_path,
        "kind": "notebook",
        "semantic_sha256": _sha256(_canonical_json(semantic_cells)),
        "anchors": anchors,
        "declared_unit_ids": [],
        "declared_concept_ids": [],
        "declared_problem_ids": [],
        "api_tokens": sorted(api_tokens, key=str.encode),
    }


def _canonical_syllabus(text: str) -> Any:
    sentinel = "<!-- syllabus-canonical -->"
    if text.count(sentinel) != 1:
        raise ValueError("syllabus canonical sentinel must appear exactly once")
    after = text.split(sentinel, 1)[1]
    match = re.search(r"```yaml\n(.*?)\n```", after, re.DOTALL)
    if match is None:
        raise ValueError("missing syllabus canonical YAML fence")
    return yaml.safe_load(match.group(1))


def _syllabus_record(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    relative = "syllabus.md"
    try:
        raw = _canonical_syllabus(_read_text(path, relative))
        digest = _sha256(_canonical_json(raw))
    except (yaml.YAMLError, TypeError, ValueError) as exc:
        raise InventoryError(f"{relative}: invalid canonical syllabus: {exc}") from exc
    return ({"path": relative, "kind": "canonical-yaml", "semantic_sha256": digest}, raw)


def _document_record(path: Path, relative_path: str) -> dict[str, Any]:
    text = _normalized_text(_read_text(path, relative_path))
    return {"path": relative_path, "kind": "document", "semantic_sha256": _sha256(text.encode("utf-8"))}


def _posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _validate_input_file(path: Path, base: Path, relative_path: str, kind: str) -> None:
    if path.is_symlink():
        raise InventoryError(f"{relative_path}: {kind} symlinks are not allowed")
    if not path.is_file():
        raise InventoryError(f"{relative_path}: {kind} is missing")
    try:
        path.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise InventoryError(f"{relative_path}: {kind} escapes the repository") from exc


def _declared_notebook(
    base: Path, declared: object, manifest_relative: str, label: str
) -> Path:
    if not isinstance(declared, str):
        raise InventoryError(f"{manifest_relative}: {label} must be a notebook path")
    relative = Path(declared)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".ipynb":
        raise InventoryError(f"{manifest_relative}: {label} escapes its material directory")
    candidate = base / relative
    if not candidate.is_file():
        raise InventoryError(f"{candidate.as_posix()}: declared notebook is missing")
    try:
        candidate.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise InventoryError(
            f"{manifest_relative}: {label} escapes its material directory"
        ) from exc
    return candidate


def _validate_discovered_notebook(path: Path, base: Path, relative_path: str) -> None:
    if path.is_symlink():
        raise InventoryError(f"{relative_path}: notebook symlinks are not allowed")
    try:
        path.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise InventoryError(
            f"{relative_path}: discovered notebook escapes its material directory"
        ) from exc


def _inject_declarations(
    record: dict[str, Any],
    *,
    unit_id: str,
    concept_ids: list[str],
    problem_ids: list[str],
) -> None:
    record["declared_unit_ids"] = [unit_id] if unit_id else []
    record["declared_concept_ids"] = sorted(set(concept_ids), key=str.encode)
    record["declared_problem_ids"] = sorted(set(problem_ids), key=str.encode)


def _unit_notebooks(root: Path, manifest_paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    manifests_by_dir = {path.parent: _load_yaml(path, _posix(path, root)) for path in manifest_paths}
    paths = set(root.glob("units/**/*.ipynb"))
    declared_paths: set[Path] = set()
    for unit_dir, manifest in manifests_by_dir.items():
        manifest_relative = _posix(unit_dir / "manifest.yaml", root)
        if not isinstance(manifest, dict):
            raise InventoryError(f"{manifest_relative}: manifest must be a mapping")
        for problem in manifest.get("practice") or []:
            for field in ("path", "solution_path"):
                declared = problem.get(field)
                candidate = _declared_notebook(
                    unit_dir,
                    declared,
                    manifest_relative,
                    f"practice {problem.get('id')} {field}",
                )
                relative = _posix(candidate, root)
                if candidate in declared_paths:
                    raise InventoryError(f"{relative}: notebook is declared more than once")
                declared_paths.add(candidate)
    if not declared_paths.issubset(paths):
        raise InventoryError("unit manifests declare notebooks that were not inventoried")
    for path in sorted(paths, key=lambda item: _posix(item, root).encode("utf-8")):
        relative = _posix(path, root)
        unit_dir = root / "units" / path.relative_to(root / "units").parts[0]
        manifest = manifests_by_dir.get(unit_dir)
        if not isinstance(manifest, dict):
            raise InventoryError(f"{relative}: no unit manifest found")
        _validate_discovered_notebook(path, unit_dir, relative)
        unit_id = str(manifest.get("unit", ""))
        within_unit = path.relative_to(unit_dir).as_posix()
        concepts = list(manifest.get("concepts_taught") or [])
        problem_ids: list[str] = []
        for problem in manifest.get("practice") or []:
            if within_unit in {problem.get("path"), problem.get("solution_path")}:
                concepts = list(problem.get("concepts") or [])
                problem_ids = [str(problem.get("id", ""))]
                break
        record = notebook_record(path, relative)
        _inject_declarations(
            record,
            unit_id=unit_id,
            concept_ids=[str(item) for item in concepts],
            problem_ids=problem_ids,
        )
        records.append(record)
    return records


def _mock_notebooks(root: Path, manifest_paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    manifest_by_dir = {path.parent: _load_yaml(path, _posix(path, root)) for path in manifest_paths}
    paths = {path for mock_dir in manifest_by_dir for path in mock_dir.rglob("*.ipynb")}
    for path in sorted(paths, key=lambda item: _posix(item, root).encode("utf-8")):
        relative = _posix(path, root)
        candidates = [directory for directory in manifest_by_dir if directory in path.parents]
        if not candidates:
            raise InventoryError(f"{relative}: no mock manifest found")
        mock_dir = max(candidates, key=lambda item: len(item.parts))
        manifest = manifest_by_dir.get(mock_dir)
        if not isinstance(manifest, dict):
            raise InventoryError(f"{relative}: no mock manifest found")
        _validate_discovered_notebook(path, mock_dir, relative)
        within_mock = path.relative_to(mock_dir).as_posix()
        concepts: list[str] = []
        units: list[str] = []
        problem_ids: list[str] = []
        for problem in manifest.get("problems") or []:
            files = {str(item) for item in problem.get("files") or []}
            solution_candidates = {
                f"solutions/{Path(item).stem}_solution.ipynb"
                for item in files
                if str(item).endswith(".ipynb")
            }
            if within_mock in files | solution_candidates:
                concepts.extend(str(item) for item in problem.get("concepts") or [])
                units.extend(str(item) for item in problem.get("units") or [])
                problem_ids.append(str(problem.get("id", "")))
        record = notebook_record(path, relative)
        record["declared_unit_ids"] = sorted(set(units), key=str.encode)
        record["declared_concept_ids"] = sorted(set(concepts), key=str.encode)
        record["declared_problem_ids"] = sorted(set(problem_ids), key=str.encode)
        records.append(record)
    for mock_dir, manifest in manifest_by_dir.items():
        manifest_relative = _posix(mock_dir / "manifest.yaml", root)
        if not isinstance(manifest, dict):
            raise InventoryError(f"{manifest_relative}: manifest must be a mapping")
        declared_paths: set[Path] = set()
        for problem in manifest.get("problems") or []:
            for declared in problem.get("files") or []:
                if not str(declared).endswith(".ipynb"):
                    continue
                statement = _declared_notebook(
                    mock_dir, declared, manifest_relative, f"problem {problem.get('id')} file"
                )
                solution_relative = f"solutions/{statement.stem}_solution.ipynb"
                solution = _declared_notebook(
                    mock_dir,
                    solution_relative,
                    manifest_relative,
                    f"problem {problem.get('id')} solution",
                )
                for candidate in (statement, solution):
                    declared_paths.add(candidate)
        if not declared_paths.issubset(paths):
            raise InventoryError(f"{manifest_relative}: declared notebooks were not inventoried")
    return records


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _synthesis_notebooks(root: Path, manifest_paths: list[Path]) -> list[dict[str, Any]]:
    """Inventory optional synthesis trees using their nearest manifest declarations."""
    manifests = {
        path.parent: _load_yaml(path, _posix(path, root)) for path in manifest_paths
    }
    records: list[dict[str, Any]] = []
    paths = sorted(
        root.glob("synthesis/**/*.ipynb"),
        key=lambda item: _posix(item, root).encode("utf-8"),
    )
    inventoried_paths = set(paths)
    for manifest_dir, manifest in manifests.items():
        manifest_relative = _posix(manifest_dir / "manifest.yaml", root)
        if not isinstance(manifest, dict):
            raise InventoryError(f"{manifest_relative}: manifest must be a mapping")
        for problem in (manifest.get("practice") or []) + (manifest.get("problems") or []):
            if not isinstance(problem, dict):
                continue
            declared_values = (
                _string_list(problem.get("files"))
                + _string_list(problem.get("path"))
                + _string_list(problem.get("solution_path"))
            )
            for declared in declared_values:
                if not declared.endswith(".ipynb"):
                    continue
                candidate = _declared_notebook(
                    manifest_dir,
                    declared,
                    manifest_relative,
                    f"problem {problem.get('id')} file",
                )
                relative = _posix(candidate, root)
                if candidate not in inventoried_paths:
                    raise InventoryError(f"{relative}: declared notebook was not inventoried")
    for path in paths:
        relative = _posix(path, root)
        candidates = [directory for directory in manifests if directory in path.parents]
        if not candidates:
            raise InventoryError(f"{relative}: no synthesis manifest found")
        manifest_dir = max(candidates, key=lambda item: len(item.parts))
        manifest = manifests[manifest_dir]
        if not isinstance(manifest, dict):
            raise InventoryError(f"{relative}: synthesis manifest must be a mapping")
        _validate_discovered_notebook(path, manifest_dir, relative)
        within_manifest = path.relative_to(manifest_dir).as_posix()
        units = _string_list(
            manifest.get("unit_ids", manifest.get("units", manifest.get("unit")))
        )
        concepts = _string_list(
            manifest.get("concepts", manifest.get("concepts_taught"))
        )
        problem_ids: list[str] = []
        for problem in (manifest.get("practice") or []) + (manifest.get("problems") or []):
            if not isinstance(problem, dict):
                continue
            declared_paths = set(
                _string_list(problem.get("files"))
                + _string_list(problem.get("path"))
                + _string_list(problem.get("solution_path"))
            )
            if within_manifest in declared_paths:
                units = _string_list(problem.get("unit_ids", problem.get("units"))) or units
                concepts = _string_list(problem.get("concepts")) or concepts
                problem_ids = _string_list(problem.get("id"))
                break
        record = notebook_record(path, relative)
        record["declared_unit_ids"] = sorted(set(units), key=str.encode)
        record["declared_concept_ids"] = sorted(set(concepts), key=str.encode)
        record["declared_problem_ids"] = sorted(set(problem_ids), key=str.encode)
        records.append(record)
    return records


def build_inventory(
    root: str | Path,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    _validate_input_file(root / "syllabus.md", root, "syllabus.md", "syllabus")
    syllabus_record, syllabus = _syllabus_record(root / "syllabus.md")
    unit_manifests = sorted(root.glob("units/*/manifest.yaml"), key=lambda item: _posix(item, root).encode("utf-8"))
    mock_manifests = sorted(root.glob("mocktests/*/manifest.yaml"), key=lambda item: _posix(item, root).encode("utf-8"))
    synthesis_manifests = sorted(root.glob("synthesis/**/manifest.yaml"), key=lambda item: _posix(item, root).encode("utf-8"))
    for path in unit_manifests:
        _validate_input_file(path, root / "units", _posix(path, root), "manifest")
    for path in mock_manifests:
        _validate_input_file(path, root / "mocktests", _posix(path, root), "manifest")
    for path in synthesis_manifests:
        _validate_input_file(path, root / "synthesis", _posix(path, root), "manifest")
    manifest_paths = unit_manifests + mock_manifests + synthesis_manifests
    manifests = [syllabus_record] + [manifest_record(path, _posix(path, root)) for path in manifest_paths]

    notebooks = _unit_notebooks(root, unit_manifests) + _mock_notebooks(root, mock_manifests)
    notebooks.extend(_synthesis_notebooks(root, synthesis_manifests))
    notebooks.sort(key=lambda item: item["path"].encode("utf-8"))
    manifests.sort(key=lambda item: item["path"].encode("utf-8"))

    course_path = root / "docs/course-structure.md"
    _validate_input_file(
        course_path, root / "docs", "docs/course-structure.md", "course structure"
    )
    documents = [_document_record(course_path, "docs/course-structure.md")]

    parsed_unit_manifests = [_load_yaml(path, _posix(path, root)) for path in unit_manifests]
    lesson_minutes = sum(sum(item["estimated_minutes"].get("lesson_sessions") or []) for item in parsed_unit_manifests)
    practice_minutes = sum(int(item["estimated_minutes"].get("practice", 0)) for item in parsed_unit_manifests)
    review_minutes = sum(int(item["estimated_minutes"].get("review", 0)) for item in parsed_unit_manifests)
    manifested_minutes = lesson_minutes + practice_minutes + review_minutes
    try:
        if _schedule_loader is load_validated_schedule:
            schedule = _schedule_loader(
                root,
                book_spec=book_spec,
                expected_book_number=expected_book_number,
            )
        else:
            schedule = _schedule_loader(root)
    except ValueError as exc:
        raise InventoryError(str(exc)) from exc

    unit_notebook_paths = [item for item in notebooks if item["path"].startswith("units/")]
    mock_notebook_paths = [item for item in notebooks if item["path"].startswith("mocktests/")]
    counts = {
        "units": len(unit_manifests),
        "concepts": len(syllabus.get("concepts") or []),
        "unit_practices": sum(len(item.get("practice") or []) for item in parsed_unit_manifests),
        "lesson_sessions": len(list(root.glob("units/*/lessons/*.ipynb"))),
        "unit_nonpractice_notebooks": sum("/practice/" not in item["path"] for item in unit_notebook_paths),
        "unit_notebooks": len(unit_notebook_paths),
        "mocktests": len(mock_manifests),
        "mock_notebooks": len(mock_notebook_paths),
        "manifested_minutes": manifested_minutes,
        "scheduled_minutes": scheduled_baseline_minutes(schedule),
    }
    all_input_paths = sorted(
        [item["path"] for item in manifests + notebooks + documents], key=str.encode
    )
    return {
        "inventory_version": 1,
        "counts": counts,
        "input_paths": all_input_paths,
        "documents": documents,
        "manifests": manifests,
        "notebooks": notebooks,
    }


def render_inventory(inventory: dict[str, Any]) -> str:
    return yaml.safe_dump(inventory, allow_unicode=True, sort_keys=False, width=120)


def main(
    argv: list[str] | None = None,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--check", action="store_true", help="fail if the generated inventory is missing or stale")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    output = root / INVENTORY_PATH
    try:
        rendered = render_inventory(
            build_inventory(root, _schedule_loader=_schedule_loader)
        )
        if args.check:
            if not output.exists():
                print(f"ERROR material inventory missing: {INVENTORY_PATH}", file=sys.stderr)
                return 1
            if output.read_text(encoding="utf-8") != rendered:
                print(f"ERROR material inventory stale: {INVENTORY_PATH}", file=sys.stderr)
                return 1
            print(f"PASS material inventory current: {INVENTORY_PATH}")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"wrote {INVENTORY_PATH}")
        return 0
    except (InventoryError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR material inventory: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
