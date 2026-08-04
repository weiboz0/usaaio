from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Unit:
    id: str
    track: str
    title: str
    prereqs: list[str]
    teaches: list[str]
    length: str | None = None


@dataclass
class Syllabus:
    baseline: set[str]
    clusters: set[str]
    concepts: dict[str, str]
    units: dict[str, Unit]


@dataclass
class Blueprint:
    raw: dict[str, Any]

    @property
    def total_points(self) -> int:
        return int(self.raw["total_points"])

    @property
    def texture(self) -> dict[str, Any]:
        return self.raw.get("texture", {})

    @property
    def sections(self) -> list[dict[str, Any]]:
        return self.raw.get("sections", [])

    @property
    def topic_distribution(self) -> dict[str, Any]:
        return self.raw.get("topic_distribution", {})

    @property
    def cluster_fold(self) -> dict[str, str]:
        return self.raw.get("cluster_fold", {})

    @property
    def difficulty_mix(self) -> dict[str, Any]:
        return self.raw.get("difficulty_mix", {})

    @property
    def provenance_rules(self) -> dict[str, Any]:
        return self.raw.get("provenance_rules", {})


@dataclass(frozen=True)
class PracticeProblem:
    id: str
    concepts: list[str]
    path: str
    solution_path: str


@dataclass
class UnitManifest:
    unit_id: str
    concepts_taught: list[str]
    concepts_used: list[str]
    prereq_units: list[str]
    practice: list[PracticeProblem]
    path: Path


@dataclass
class ManifestProblem:
    id: str
    section: str
    units: list[str]
    concepts: list[str]
    points: int
    difficulty: str
    type: str
    answer_form: str
    provenance: str
    adapted_from: str | None
    spec: str
    answer_key: Any
    data: dict[str, Any] | None
    cluster: str | None
    files: list[str]


@dataclass
class MockManifest:
    test: str
    blueprint_version: int
    generated: str | None
    status: str
    generation_parameters: dict[str, Any]
    duration_minutes: int
    total_points: int
    time_budget: dict[str, int]
    problems: list[ManifestProblem]
    path: Path


@dataclass
class Report:
    name: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: str | None = None


def _strip_comment(line: str) -> str:
    quote: str | None = None
    for i, ch in enumerate(line):
        if ch in {"'", '"'} and (i == 0 or line[i - 1] != "\\"):
            quote = None if quote == ch else ch if quote is None else quote
        if ch == "#" and quote is None:
            return line[:i]
    return line


def _split_top_level(text: str) -> list[str]:
    out: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for i, ch in enumerate(text):
        if ch in {"'", '"'}:
            quote = None if quote == ch else ch if quote is None else quote
        elif quote is None:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append(text[start:i].strip())
                start = i + 1
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return ""
    if text in {"[]", "{}"}:
        return [] if text == "[]" else {}
    if text.startswith("[") and text.endswith("]"):
        return [_parse_scalar(part) for part in _split_top_level(text[1:-1])]
    if text.startswith("{") and text.endswith("}"):
        result: dict[str, Any] = {}
        for part in _split_top_level(text[1:-1]):
            key, value = part.split(":", 1)
            result[str(_parse_scalar(key))] = _parse_scalar(value)
        return result
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return ast.literal_eval(text)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def _parse_yaml(text: str) -> Any:
    try:
        import yaml  # type: ignore[import-not-found]

        return yaml.safe_load(text)
    except ModuleNotFoundError:
        return _parse_yaml_subset(text)


def _parse_yaml_subset(text: str) -> Any:
    raw_lines = text.splitlines()
    stripped: list[tuple[int, str]] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        cleaned = _strip_comment(line).rstrip()
        if cleaned.strip():
            indent = len(cleaned) - len(cleaned.lstrip(" "))
            body = cleaned.strip()
            if body.endswith(": >") or body.endswith(": |"):
                key = body[:-3].strip()
                i += 1
                parts: list[str] = []
                while i < len(raw_lines):
                    nxt = raw_lines[i]
                    nclean = _strip_comment(nxt).rstrip()
                    nindent = len(nclean) - len(nclean.lstrip(" ")) if nclean.strip() else indent + 2
                    if nclean.strip() and nindent <= indent:
                        i -= 1
                        break
                    if nclean.strip():
                        parts.append(nclean.strip())
                    i += 1
                stripped.append((indent, f"{key}: {' '.join(parts)}"))
            else:
                depth = body.count("[") + body.count("{") - body.count("]") - body.count("}")
                while depth > 0 and i + 1 < len(raw_lines):
                    i += 1
                    continuation = _strip_comment(raw_lines[i]).strip()
                    if continuation:
                        body = f"{body} {continuation}"
                        depth = body.count("[") + body.count("{") - body.count("]") - body.count("}")
                stripped.append((indent, body))
        i += 1

    def parse_block(pos: int, indent: int) -> tuple[Any, int]:
        if stripped[pos][1].startswith("- "):
            seq: list[Any] = []
            while pos < len(stripped) and stripped[pos][0] == indent and stripped[pos][1].startswith("- "):
                item = stripped[pos][1][2:].strip()
                if item == "":
                    value, pos = parse_block(pos + 1, indent + 2)
                    seq.append(value)
                elif ":" in item and not item.startswith(("[", "{")):
                    key, value_text = item.split(":", 1)
                    item_map: dict[str, Any] = {key: _parse_scalar(value_text.strip()) if value_text.strip() else {}}
                    pos += 1
                    while pos < len(stripped) and stripped[pos][0] > indent:
                        child_indent, child = stripped[pos]
                        if child_indent != indent + 2:
                            break
                        ckey, ctext = child.split(":", 1)
                        if ctext.strip():
                            item_map[ckey] = _parse_scalar(ctext.strip())
                            pos += 1
                        else:
                            item_map[ckey], pos = parse_block(pos + 1, child_indent + 2)
                    seq.append(item_map)
                else:
                    seq.append(_parse_scalar(item))
                    pos += 1
            return seq, pos
        mapping: dict[str, Any] = {}
        while pos < len(stripped) and stripped[pos][0] == indent:
            _, body = stripped[pos]
            key, value_text = body.split(":", 1)
            if value_text.strip():
                mapping[key] = _parse_scalar(value_text.strip())
                pos += 1
            else:
                mapping[key], pos = parse_block(pos + 1, indent + 2)
        return mapping, pos

    if not stripped:
        return None
    data, _ = parse_block(0, stripped[0][0])
    return data


def _canonical_yaml(markdown: str) -> str:
    sentinel = "<!-- syllabus-canonical -->"
    if markdown.count(sentinel) != 1:
        raise ValueError("syllabus canonical sentinel must appear exactly once")
    after = markdown.split(sentinel, 1)[1]
    match = re.search(r"```yaml\n(.*?)\n```", after, re.S)
    if match is None:
        raise ValueError("missing syllabus canonical yaml fence")
    return match.group(1)


def load_syllabus(root: str | Path) -> Syllabus:
    root = Path(root)
    raw = _parse_yaml(_canonical_yaml((root / "syllabus.md").read_text()))
    baseline = {item for values in raw["baseline"].values() for item in values}
    concepts = {entry["id"]: entry["cluster"] for entry in raw["concepts"]}
    units = {
        entry["id"]: Unit(
            id=entry["id"],
            track=entry["track"],
            title=entry["title"],
            prereqs=list(entry.get("prereqs", [])),
            teaches=list(entry.get("teaches", [])),
            length=entry.get("length"),
        )
        for entry in raw["units"]
    }
    return Syllabus(baseline=baseline, clusters=set(raw["clusters"]), concepts=concepts, units=units)


def load_blueprint(root: str | Path) -> Blueprint:
    raw = _parse_yaml((Path(root) / "mocktests" / "blueprint.yaml").read_text())
    return Blueprint(raw=raw)


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return _parse_yaml(path.read_text())


def load_unit_manifests(root: str | Path) -> list[UnitManifest]:
    manifests = sorted(Path(root).glob("units/*/manifest.yaml"))
    result: list[UnitManifest] = []
    for path in manifests:
        raw = _read_manifest(path)
        result.append(
            UnitManifest(
                unit_id=raw["unit"],
                concepts_taught=list(raw.get("concepts_taught", [])),
                concepts_used=list(raw.get("concepts_used", [])),
                prereq_units=list(raw.get("prereq_units", [])),
                practice=[
                    PracticeProblem(
                        id=item["id"],
                        concepts=list(item.get("concepts", [])),
                        path=item["path"],
                        solution_path=item["solution_path"],
                    )
                    for item in raw.get("practice", [])
                ],
                path=path,
            )
        )
    return result


def load_mock_manifests(root: str | Path) -> list[MockManifest]:
    result: list[MockManifest] = []
    for path in sorted(Path(root).glob("mocktests/r1-*/manifest.yaml")):
        raw = _read_manifest(path)
        problems = []
        for item in raw.get("problems", []):
            problems.append(
                ManifestProblem(
                    id=item["id"],
                    section=item["section"],
                    units=list(item.get("units", [])),
                    concepts=list(item.get("concepts", [])),
                    points=int(item.get("points", 0)),
                    difficulty=item.get("difficulty", ""),
                    type=item.get("type", ""),
                    answer_form=item.get("answer_form", ""),
                    provenance=item.get("provenance", ""),
                    adapted_from=item.get("adapted-from") or item.get("adapted_from"),
                    spec=item.get("spec", ""),
                    answer_key=item.get("answer_key"),
                    data=item.get("data"),
                    cluster=item.get("cluster"),
                    files=list(item.get("files", [])),
                )
            )
        result.append(
            MockManifest(
                test=raw["test"],
                blueprint_version=int(raw.get("blueprint_version", 0)),
                generated=str(raw["generated"]) if raw.get("generated") is not None else None,
                status=raw.get("status", "final"),
                generation_parameters=dict(raw.get("generation_parameters", {})),
                duration_minutes=int(raw.get("duration_minutes", 0)),
                total_points=int(raw.get("total_points", 0)),
                time_budget={k: int(v) for k, v in raw.get("time_budget", {}).items()},
                problems=problems,
                path=path,
            )
        )
    return result
