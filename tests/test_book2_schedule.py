from __future__ import annotations

import hashlib
import importlib.util
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools import audit_curriculum, render_course_structure, render_curriculum_roadmap
from tools.books import BookSpec, load_book_catalog, validate_book_root
from tools.checks import schedule as schedule_checker
from tools.model import load_syllabus

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
BOOK2_ROOT = ROOT / "book2"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "two-books-valid"
BOOK1_SCHEDULE_SHA256 = "6c1f4f6eeb518930e5772ef0f14d8bba18be1f191114c91edfae52ef8811eb4d"
BOOK1_STRUCTURE_SHA256 = "75518825359dd1e0ed3501c0301fbdfb1fc685d6944465f924f1f88c0d25e642"


def _load_schedule(root: Path = BOOK2_ROOT) -> dict[str, Any]:
    raw = yaml.safe_load(
        (root / "curriculum" / "course-schedule.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(raw, dict)
    return raw


def _mutated_report(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
):
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    schedule = _load_schedule(selected)
    mutate(schedule)
    (selected / "curriculum" / "course-schedule.yaml").write_text(
        yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8"
    )
    return schedule_checker.check_schedule(selected, expected_book_number=2)


def _mutated_root(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> Path:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    schedule = _load_schedule(selected)
    mutate(schedule)
    (selected / "curriculum" / "course-schedule.yaml").write_text(
        yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8"
    )
    return selected


def test_parallel_book2_schedule_and_renderer_modules_remain_forbidden() -> None:
    assert importlib.util.find_spec("tools.checks.book2_schedule") is None
    assert importlib.util.find_spec("tools.render_book2_structure") is None


def test_schedule_dispatch_uses_explicit_book_policies() -> None:
    assert hasattr(schedule_checker, "Book1SchedulePolicy")
    assert hasattr(schedule_checker, "Book2SchedulePolicy")
    assert isinstance(
        schedule_checker.schedule_policy(BOOK1_ROOT),
        schedule_checker.Book1SchedulePolicy,
    )
    assert isinstance(
        schedule_checker.schedule_policy(BOOK2_ROOT),
        schedule_checker.Book2SchedulePolicy,
    )


def test_registered_book2_schedule_is_exact_six_week_staged_ledger() -> None:
    raw = _load_schedule()

    assert raw["schedule_version"] == 1
    assert raw["book"] == 2
    assert raw["status"] == "staged"
    assert raw["starts_after_global_week"] == 40
    assert raw["total_book_weeks"] == 6
    assert raw["total_minutes"] == 1660
    assert raw["final_assessment"] == {
        "kind": "future-r2-mock",
        "status": "planned",
        "after_book_week": 6,
    }
    assert [week["book_week"] for week in raw["weeks"]] == list(range(1, 7))
    assert [week["global_week"] for week in raw["weeks"]] == list(range(41, 47))
    assert [
        sum(allocation["minutes"] for allocation in week["allocations"])
        for week in raw["weeks"]
    ] == [255, 275, 420, 325, 325, 60]

    problem_ids = [
        problem_id
        for week in raw["weeks"]
        for allocation in week["allocations"]
        for problem_id in allocation.get("problem_ids", [])
    ]
    assert sorted(problem_ids) == [
        f"B2-019-p{number:02}" for number in range(1, 25)
    ]
    assert len(problem_ids) == len(set(problem_ids)) == 24

    report = schedule_checker.check_schedule(BOOK2_ROOT)
    assert report.ok, report.errors
    validated = schedule_checker.load_validated_schedule(BOOK2_ROOT)
    assert validated.status == "staged"
    assert [week.week for week in validated.weeks] == list(range(1, 7))
    assert list(validated.global_weeks) == list(range(41, 47))
    assert validated.total_minutes == 1660
    assert validated.covered_problem_ids == frozenset()
    inventory = audit_curriculum.build_inventory(BOOK2_ROOT)
    assert inventory["counts"]["scheduled_minutes"] == 0
    assert inventory["counts"]["unit_practices"] == 0


def test_staged_book2_minutes_are_not_double_counted_in_aggregate_baseline() -> None:
    rendered = render_course_structure.render_document(BOOK2_ROOT)
    aggregate = audit_curriculum.build_inventory(BOOK2_ROOT)

    assert aggregate["counts"]["scheduled_minutes"] == 0
    assert "1,660 minutes" in rendered
    assert "staged schedule grants no live coverage" in rendered

    documents = render_curriculum_roadmap.render_documents(ROOT)
    for document in documents.values():
        assert "Current scheduled baseline: **18875 minutes / 314.58 hours**." in document
        assert "Current scheduled baseline: **20535 minutes" not in document
        assert "| **Planned-unit subtotal** | **142** | **182** |" in document
    roadmap = documents[Path("docs/curriculum-roadmap.md")]
    assert (
        "| book2 | book2:B2-019-attention-transformers | Attention and Transformer "
        "Mechanics | round-2-extension | 22–28 |"
    ) in roadmap


def test_live_book2_baseline_is_explicitly_deferred_until_task5(tmp_path: Path) -> None:
    selected = _mutated_root(
        tmp_path,
        lambda schedule: schedule.update(status="live"),
    )

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("live schedule support is deferred until Task 5" in error for error in report.errors)


def test_two_book_schedule_fixture_is_valid_and_isolated(tmp_path: Path) -> None:
    fixture = tmp_path / "repo"
    shutil.copytree(FIXTURE_ROOT, fixture)
    catalog = load_book_catalog(fixture)

    book1, book2 = catalog.books
    book1_report = schedule_checker.check_schedule(book1.root, book_spec=book1)
    book2_report = schedule_checker.check_schedule(book2.root, book_spec=book2)

    assert all(validate_book_root(book) == [] for book in catalog.books)
    assert book1_report.ok, book1_report.errors
    assert book2_report.ok, book2_report.errors
    assert len(load_syllabus(book1.root).concepts) == 1
    assert len(load_syllabus(book2.root).concepts) == 1
    assert isinstance(
        schedule_checker.schedule_policy(book1.root, book_spec=book1),
        schedule_checker.Book1SchedulePolicy,
    )
    assert isinstance(
        schedule_checker.schedule_policy(book2.root, book_spec=book2),
        schedule_checker.Book2SchedulePolicy,
    )


def test_schedule_dispatch_rejects_registry_number_schedule_mismatch(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "repo"
    shutil.copytree(FIXTURE_ROOT, fixture)
    registry_path = fixture / "books.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["books"][1]["number"] = 3
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    book2 = load_book_catalog(fixture).by_id("book2")

    report = schedule_checker.check_schedule(book2.root, book_spec=book2)

    assert not report.ok
    assert any(
        "schedule book 2 does not match registered book number 3" in error
        for error in report.errors
    )


def test_unregistered_direct_schedule_api_requires_explicit_identity(
    tmp_path: Path,
) -> None:
    selected = tmp_path / "advanced"
    shutil.copytree(BOOK2_ROOT, selected)

    with pytest.raises(ValueError, match="expected_book_number or BookSpec"):
        schedule_checker.schedule_policy(selected)
    assert schedule_checker.check_schedule(selected, expected_book_number=2).ok

    mismatched = BookSpec(id="book2", number=2, root=selected.parent, depends_on=())
    report = schedule_checker.check_schedule(selected, book_spec=mismatched)
    assert not report.ok
    assert any("does not match selected root" in error for error in report.errors)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda schedule: schedule["weeks"][2].update(book_week=2),
            "book_week rows must be ordered consecutively 1..6",
            id="local-numbering",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][2].update(global_week=99),
            "global_week rows must be 41..46",
            id="global-numbering",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][2].update(
                minutes=134
            ),
            "practice allocation minutes 134; expected 135",
            id="allocation-minutes",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][2][
                "problem_ids"
            ].__setitem__(0, "B2-019-p02"),
            "B2-019-p01 must appear exactly once",
            id="duplicate-and-omitted-id",
        ),
        pytest.param(
            lambda schedule: schedule["final_assessment"].update(
                after_book_week=5
            ),
            "planned final assessment marker must follow book week 6",
            id="stale-final-marker",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][0].update(
                kind="reading"
            ),
            "unknown Book 2 allocation kind reading",
            id="unknown-kind",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][1].update(
                unit="book1:C6-pytorch"
            ),
            "cross-book unit reference book1:C6-pytorch",
            id="cross-book-reference",
        ),
    ],
)
def test_staged_book2_schedule_rejects_contract_mutations(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    report = _mutated_report(tmp_path, mutate)

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        pytest.param(
            "starts_after_global_week", 40.0,
            "starts_after_global_week must be an integer", id="offset-float",
        ),
        pytest.param(
            "starts_after_global_week", True,
            "starts_after_global_week must be an integer", id="offset-bool",
        ),
        pytest.param(
            "total_book_weeks", 6.0,
            "total_book_weeks must be an integer", id="weeks-float",
        ),
        pytest.param(
            "total_book_weeks", True,
            "total_book_weeks must be an integer", id="weeks-bool",
        ),
        pytest.param(
            "total_minutes", 1660.0,
            "total_minutes must be an integer", id="total-float",
        ),
        pytest.param(
            "total_minutes", True,
            "total_minutes must be an integer", id="total-bool",
        ),
        pytest.param(
            "final_assessment.after_book_week", 6.0,
            "final_assessment.after_book_week must be an integer", id="marker-float",
        ),
        pytest.param(
            "final_assessment.after_book_week", True,
            "final_assessment.after_book_week must be an integer", id="marker-bool",
        ),
    ],
)
def test_book2_integer_fields_reject_float_and_bool_through_both_apis(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(schedule: dict[str, Any]) -> None:
        if field == "final_assessment.after_book_week":
            schedule["final_assessment"]["after_book_week"] = value
        else:
            schedule[field] = value

    selected = _mutated_root(tmp_path, mutate)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)
    assert not report.ok
    assert any(message in error for error in report.errors), report.errors
    with pytest.raises(ValueError, match=message):
        schedule_checker.load_validated_schedule(selected, expected_book_number=2)


def test_staged_book2_schedule_rejects_first_live_manifest(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest = selected / "units" / "B2-019-attention-transformers" / "manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("unit: B2-019-attention-transformers\n", encoding="utf-8")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(
        "staged Book 2 schedule is forbidden once a live manifest exists" in error
        for error in report.errors
    )


def test_shared_renderer_supports_staged_book2_without_manifest_coverage() -> None:
    rendered = render_course_structure.render_document(BOOK2_ROOT)

    assert "Book 2 Schedule" in rendered
    assert "local weeks 1–6" in rendered
    assert "display weeks 41–46" in rendered
    assert "1,660 minutes" in rendered
    assert "staged schedule grants no live coverage" in rendered
    assert "derivation-heavy Week 3" in rendered
    assert "planned future `r2-*` final assessment follows local Week 6" in rendered


def test_book1_bytes_remain_pinned_while_valid_book2_fixture_renders(
    tmp_path: Path,
) -> None:
    schedule_path = BOOK1_ROOT / "curriculum" / "course-schedule.yaml"
    structure_path = BOOK1_ROOT / "docs" / "course-structure.md"
    schedule_bytes = schedule_path.read_bytes()
    structure_bytes = structure_path.read_bytes()

    assert hashlib.sha256(schedule_bytes).hexdigest() == BOOK1_SCHEDULE_SHA256
    assert hashlib.sha256(structure_bytes).hexdigest() == BOOK1_STRUCTURE_SHA256
    assert render_course_structure.render_document(BOOK1_ROOT).encode() == structure_bytes

    fixture = tmp_path / "repo"
    shutil.copytree(FIXTURE_ROOT, fixture)
    fixture_catalog = load_book_catalog(fixture)
    fixture_book2 = fixture_catalog.by_id("book2")
    assert schedule_checker.check_schedule(
        fixture_book2.root, book_spec=fixture_book2
    ).ok
    fixture_rendered = render_course_structure.render_document(
        fixture_book2.root, book_spec=fixture_book2
    )
    assert "Book 2 Schedule" in fixture_rendered
    assert str(BOOK2_ROOT) not in fixture_rendered

    assert hashlib.sha256(schedule_path.read_bytes()).hexdigest() == BOOK1_SCHEDULE_SHA256
    assert hashlib.sha256(structure_path.read_bytes()).hexdigest() == BOOK1_STRUCTURE_SHA256

    mutated = bytearray(schedule_bytes)
    mutated[0] ^= 1
    assert hashlib.sha256(mutated).hexdigest() != BOOK1_SCHEDULE_SHA256
