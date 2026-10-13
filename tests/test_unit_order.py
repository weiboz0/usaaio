"""Plan 031 D1/D8: unit id vs folder resolver, teaching_order, and the unit-order check."""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest
import yaml

from tools.books import BookSpec, live_units, unit_dir, unit_id_of, unit_relpath
from tools.checks.schedule import _parse_book2_schedule, _parse_schedule
from tools.checks.unit_order import check_unit_order

ROOT = Path(__file__).resolve().parents[1]

# A three-week toy schedule: F1, then C1 and F2 in week 2 (allocation order breaks the tie), C2.
SCHEDULE_UNITS = [["F1-a"], ["C1-b", "F2-c"], ["C2-d"]]
ORDER = ["F1-a", "C1-b", "F2-c", "C2-d"]


def _schedule(order: list[str] | None, weeks: list[list[str]] = SCHEDULE_UNITS) -> str:
    raw: dict = {
        "schedule_version": 1,
        "calendar": {"semester_1_weeks": 1, "semester_2_weeks": 2, "total_weeks": 3},
    }
    if order is not None:
        raw["teaching_order"] = order
    raw["weeks"] = [
        {
            "week": index + 1,
            "semester": 1 if index == 0 else 2,
            "allocations": [
                {"kind": "lesson-session", "unit": unit, "session": 1, "minutes": 60}
                for unit in units
            ],
        }
        for index, units in enumerate(weeks)
    ]
    return yaml.safe_dump(raw, sort_keys=False)


def _book(
    tmp_path: Path,
    folders: list[str],
    *,
    order: list[str] | None = ORDER,
    weeks: list[list[str]] = SCHEDULE_UNITS,
    number: int = 1,
) -> BookSpec:
    root = tmp_path / "book"
    (root / "curriculum").mkdir(parents=True)
    (root / "curriculum" / "course-schedule.yaml").write_text(_schedule(order, weeks), encoding="utf-8")
    for folder in folders:
        (root / "units" / folder).mkdir(parents=True)
        (root / "units" / folder / "manifest.yaml").write_text(
            f"unit: {unit_id_of(folder)}\n", encoding="utf-8"
        )
    return BookSpec(id=f"book{number}", number=number, root=root, depends_on=())


GOOD = ["01-F1-a", "02-C1-b", "03-F2-c", "04-C2-d"]


# --- resolver ---------------------------------------------------------------------------------


def test_unit_id_of_strips_only_a_two_digit_prefix() -> None:
    assert unit_id_of("03-F3-multivar-calculus") == "F3-multivar-calculus"
    assert unit_id_of("F3-multivar-calculus") == "F3-multivar-calculus"
    assert unit_id_of("B2-019-attention-transformers") == "B2-019-attention-transformers"


def test_unit_dir_resolves_prefixed_and_unprefixed_folders(tmp_path: Path) -> None:
    (tmp_path / "units" / "03-F3-x").mkdir(parents=True)
    (tmp_path / "units" / "B2-019-y").mkdir(parents=True)
    assert unit_dir(tmp_path, "F3-x") == tmp_path / "units" / "03-F3-x"
    assert unit_dir(tmp_path, "B2-019-y") == tmp_path / "units" / "B2-019-y"
    assert unit_relpath(tmp_path, "F3-x") == "units/03-F3-x"


def test_unit_dir_rejects_missing_and_ambiguous_folders(tmp_path: Path) -> None:
    (tmp_path / "units" / "F3-x").mkdir(parents=True)
    (tmp_path / "units" / "03-F3-x").mkdir(parents=True)
    with pytest.raises(ValueError, match="more than one folder"):
        unit_dir(tmp_path, "F3-x")
    with pytest.raises(ValueError, match="no folder"):
        unit_dir(tmp_path, "F4-y")


def test_live_units_returns_ids_in_folder_order(tmp_path: Path) -> None:
    book = _book(tmp_path, GOOD)
    assert live_units(book) == tuple(ORDER)


def test_live_book1_units_are_prefixed_and_resolve_by_id() -> None:
    folders = sorted(path.name for path in (ROOT / "book1" / "units").iterdir() if path.is_dir())
    assert len(folders) == 19
    for folder in folders:
        assert unit_dir(ROOT / "book1", unit_id_of(folder)).name == folder


# --- teaching_order parsing -------------------------------------------------------------------


def test_schedule_parser_accepts_present_and_absent_teaching_order(tmp_path: Path) -> None:
    present = _book(tmp_path / "a", GOOD)
    errors: list[str] = []
    schedule = _parse_schedule(present.root, errors)
    assert errors == []
    assert schedule.teaching_order == tuple(ORDER)
    absent = _book(tmp_path / "b", GOOD, order=None)
    schedule = _parse_schedule(absent.root, errors)
    assert errors == []
    assert schedule.teaching_order is None


@pytest.mark.parametrize(
    ("order", "message"),
    [
        (["F1-a", "C1-b", "F2-c"], "exactly the scheduled units"),
        (["F1-a", "C1-b", "F2-c", "C2-d", "C3-e"], "exactly the scheduled units"),
        (["F1-a", "F1-a", "C1-b", "F2-c", "C2-d"], "must not repeat"),
        ("F1-a", "nonempty list"),
    ],
)
def test_schedule_parser_rejects_a_wrong_teaching_order(
    tmp_path: Path, order: object, message: str
) -> None:
    book = _book(tmp_path, GOOD, order=order)  # type: ignore[arg-type]
    errors: list[str] = []
    _parse_schedule(book.root, errors)
    assert any(message in error for error in errors), errors


def test_book2_schedule_rejects_teaching_order(tmp_path: Path) -> None:
    raw = yaml.safe_load((ROOT / "book2" / "curriculum" / "course-schedule.yaml").read_text())
    raw["teaching_order"] = ["B2-019-attention-transformers"]
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "curriculum" / "course-schedule.yaml").write_text(yaml.safe_dump(raw))
    errors: list[str] = []
    with contextlib.suppress(ValueError, KeyError, OSError, TypeError):
        _parse_book2_schedule(tmp_path, errors, expected_book_number=2)
    assert any("staged Book 2 schedule keys" in error for error in errors), errors


# --- unit-order check -------------------------------------------------------------------------


def _check(book: BookSpec):
    return check_unit_order(book.root, book_spec=book)


def test_unit_order_passes_a_good_book(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, GOOD))
    assert report.ok, report.errors


def test_unit_order_rejects_a_bad_prefix(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, ["01-F1-a", "C1-b", "03-F2-c", "04-C2-d"]))
    assert not report.ok
    assert any("C1-b must be NN-<unit id>" in error for error in report.errors), report.errors


def test_unit_order_rejects_a_prefix_gap(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, ["01-F1-a", "02-C1-b", "03-F2-c", "05-C2-d"]))
    assert not report.ok
    assert any("no gaps" in error for error in report.errors), report.errors


def test_unit_order_rejects_a_prefix_that_disagrees_with_teaching_order(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, ["01-F1-a", "03-C1-b", "02-F2-c", "04-C2-d"]))
    assert not report.ok
    assert any("teaching_order places C1-b at 02" in error for error in report.errors), report.errors


def test_unit_order_rejects_teaching_order_inconsistent_with_schedule(tmp_path: Path) -> None:
    order = ["F1-a", "F2-c", "C1-b", "C2-d"]
    report = _check(_book(tmp_path, ["01-F1-a", "02-F2-c", "03-C1-b", "04-C2-d"], order=order))
    assert not report.ok
    assert any("schedule first reaches C1-b" in error for error in report.errors), report.errors


def test_unit_order_rejects_codes_that_do_not_count_up(tmp_path: Path) -> None:
    weeks = [["F1-a"], ["C2-b", "F2-c"], ["C1-d"]]
    order = ["F1-a", "C2-b", "F2-c", "C1-d"]
    report = _check(_book(tmp_path, ["01-F1-a", "02-C2-b", "03-F2-c", "04-C1-d"], order=order, weeks=weeks))
    assert not report.ok
    assert any("codes count up" in error for error in report.errors), report.errors


def test_unit_order_requires_a_declared_teaching_order(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, GOOD, order=None))
    assert not report.ok
    assert any("must declare teaching_order" in error for error in report.errors)


def test_unit_order_exempts_book2(tmp_path: Path) -> None:
    report = _check(_book(tmp_path, ["B2-019-x", "C1-b"], order=None, number=2))
    assert report.ok, report.errors


def test_unit_order_passes_the_live_book1() -> None:
    from tools.books import load_book_catalog

    book = load_book_catalog(ROOT).by_id("book1")
    report = check_unit_order(book.root, book_spec=book)
    assert report.ok, report.errors
