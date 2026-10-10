from __future__ import annotations

import re
from pathlib import Path

import yaml

from tools.checks.blueprint import ARC_ROTATION, DEFAULT_ANCHORS, DEFAULT_TIME_BUDGET, is_round2
from tools.model import Blueprint, load_blueprint

DIFFICULTY_DRAW = {"intro": 0.23, "core": 0.45, "advanced": 0.32}


def scaffold_mocktest(
    root: str | Path,
    test_id: str,
    generated_date: str,
    *,
    book_number: int | None = None,
) -> Path:
    root = Path(root)
    blueprint = load_blueprint(root)
    if blueprint.raw.get("status") == "planned":
        raise ValueError("mock-test blueprint is planned; scaffolding is not available")
    declared_book = blueprint.raw.get("book")
    if book_number is None:
        book_number = declared_book if type(declared_book) is int else 1
    if type(book_number) is not int or book_number <= 0:
        raise ValueError("book_number must be a positive integer")
    if type(declared_book) is int and declared_book != book_number:
        raise ValueError(
            f"blueprint declares book {declared_book}, not selected book {book_number}"
        )
    assessment_prefix = f"r{book_number}-"
    declared_prefix = blueprint.raw.get("assessment_prefix")
    if declared_prefix is not None and declared_prefix != assessment_prefix:
        raise ValueError(
            f"blueprint assessment_prefix must be {assessment_prefix!r}, "
            f"got {declared_prefix!r}"
        )
    match = re.fullmatch(rf"{re.escape(assessment_prefix)}(\d{{3}})", test_id)
    if match is None:
        raise ValueError(f"test id must match r{book_number}-NNN")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", generated_date):
        raise ValueError("--date must use YYYY-MM-DD")
    test_dir = root / "mocktests" / test_id
    if test_dir.exists():
        raise FileExistsError(f"{test_dir} already exists")
    for child in ["theory", "problems", "solutions", "data"]:
        (test_dir / child).mkdir(parents=True, exist_ok=True)
    if is_round2(blueprint):
        _scaffold_round2(blueprint, test_dir, test_id, int(match.group(1)), generated_date)
        return test_dir
    (test_dir / "test.md").write_text(
        f"---\ntest: {test_id}\nduration_minutes: {blueprint.raw['duration_minutes']}\ntotal_points: {blueprint.total_points}\n---\n"
    )
    (test_dir / "rubric.md").write_text(f"# {test_id} Rubric\n\n")
    rotation_index = (int(match.group(1)) - 1) % len(ARC_ROTATION)
    arc_clusters = ARC_ROTATION[rotation_index]
    (test_dir / "manifest.yaml").write_text(
        _manifest_text(
            test_id=test_id,
            blueprint_version=blueprint.raw["blueprint_version"],
            generated_date=generated_date,
            duration_minutes=blueprint.raw["duration_minutes"],
            total_points=blueprint.total_points,
            arc_clusters=arc_clusters,
        )
    )
    return test_dir


def _manifest_text(
    *,
    test_id: str,
    blueprint_version: int,
    generated_date: str,
    duration_minutes: int,
    total_points: int,
    arc_clusters: list[str],
) -> str:
    section_points = ", ".join(f"{key}: {value}" for key, value in DEFAULT_ANCHORS.items())
    time_budget = ", ".join(f"{key}: {value}" for key, value in DEFAULT_TIME_BUDGET.items())
    difficulty = ", ".join(f"{key}: {value}" for key, value in DIFFICULTY_DRAW.items())
    return f"""test: {test_id}
blueprint_version: {blueprint_version}
generated: {generated_date}
status: draft
generation_parameters:
  section_points: {{{section_points}}}
  arc_clusters: [{", ".join(arc_clusters)}]
  problem_count: 9
  difficulty_draw: {{{difficulty}}}
duration_minutes: {duration_minutes}
total_points: {total_points}
time_budget: {{{time_budget}}}
problems: []
"""


def _scaffold_round2(
    blueprint: Blueprint, test_dir: Path, test_id: str, number: int, generated_date: str
) -> None:
    """Book 2: every instantiation value comes from the blueprint's default_* keys."""
    raw = blueprint.raw
    rotation = raw["arc_rotation"]
    rotation_index = (number - 1) % len(rotation)
    (test_dir / "test.md").write_text(
        f"---\ntest: {test_id}\ndays: {raw['days']}\n"
        f"day_duration_minutes: {raw['day_duration_minutes']}\n"
        f"total_points: {blueprint.total_points}\n---\n"
    )
    (test_dir / "rubric.md").write_text(f"# {test_id} Rubric\n\n")
    manifest = {
        "test": test_id,
        "blueprint_version": raw["blueprint_version"],
        "generated": generated_date,
        "status": "draft",
        "generation_parameters": {
            "rotation_index": rotation_index,
            "section_points": dict(raw["default_anchors"]),
            "arc_clusters": {key: list(value) for key, value in rotation[rotation_index].items()},
            "problem_count": sum(
                len(value) if isinstance(value, list) else 1
                for value in raw["default_anchors"].values()
            ),
            "difficulty_draw": dict(raw["default_difficulty_draw"]),
        },
        "day_duration_minutes": raw["day_duration_minutes"],
        "total_points": blueprint.total_points,
        "time_budget": {
            str(day): dict(sections) for day, sections in raw["default_time_budget"].items()
        },
        "problems": [],
    }
    (test_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
