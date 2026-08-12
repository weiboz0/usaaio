from __future__ import annotations

import re
from pathlib import Path

from tools.checks.blueprint import ARC_ROTATION, DEFAULT_ANCHORS, DEFAULT_TIME_BUDGET
from tools.model import load_blueprint

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
