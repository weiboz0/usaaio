"""Plan 031 D1/D8: Book 1 unit folders follow the declared teaching order.

Applies only to the registry's Book 1 (the `books.yaml` entry with number 1, selected by its
id); Book 2 folders are named by their ids and are exempt. Rules:

* `course-schedule.yaml` declares `teaching_order:`, the unit ids in folder order;
* every unit folder is `NN-<id>`, the `NN` prefixes are 01..N with no gaps, and `NN` is the
  id's 1-based position in `teaching_order`; each folder's manifest `unit` is that id;
* `teaching_order` is consistent with the schedule: it equals the units sorted by first
  appearance (week order, then allocation order within the week);
* within F and within C, the codes count up 1, 2, 3, ... along `teaching_order`.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from tools.books import BookSpec, unit_id_of
from tools.checks.schedule import _parse_schedule, _registered_book
from tools.model import Report

NAME = "unit-order-check"
_FOLDER = re.compile(r"(?P<order>\d{2})-(?P<id>.+)\Z")
_CODE = re.compile(r"(?P<track>[FC])(?P<number>\d+)-")


def _book(root: Path, book_spec: BookSpec | None) -> BookSpec | None:
    registered = _registered_book(root)
    if registered is not None:
        if book_spec is not None and book_spec.id != registered.id:
            raise ValueError(f"BookSpec for {book_spec.id} does not match books.yaml")
        return registered
    return book_spec


def check_unit_order(root: str | Path, *, book_spec: BookSpec | None = None) -> Report:
    root = Path(root).resolve()
    book = _book(root, book_spec)
    if book is None or book.number != 1:
        # Keyed on the registry's Book 1 id: every other book is exempt.
        return Report(name=NAME, ok=True)
    errors: list[str] = []
    schedule = _parse_schedule(root, errors)
    if schedule is None:
        return Report(name=NAME, ok=False, errors=errors)
    errors.clear()  # schedule shape is schedule-check's job; keep only what this check needs
    order = schedule.teaching_order
    if order is None:
        errors.append(f"{book.id}: course-schedule.yaml must declare teaching_order (Plan 031 D8)")
        return Report(name=NAME, ok=False, errors=errors)
    position = {unit: index + 1 for index, unit in enumerate(order)}

    units_root = root / "units"
    folders = sorted(
        path for path in units_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    prefixes: list[int] = []
    seen: set[str] = set()
    for folder in folders:
        match = _FOLDER.match(folder.name)
        if match is None:
            errors.append(f"{book.id}: unit folder {folder.name} must be NN-<unit id>")
            continue
        number, unit = int(match["order"]), match["id"]
        prefixes.append(number)
        seen.add(unit)
        if unit not in position:
            errors.append(f"{book.id}: unit folder {folder.name} names a unit not in teaching_order")
            continue
        if number != position[unit]:
            errors.append(
                f"{book.id}: unit folder {folder.name} has prefix {match['order']}; "
                f"teaching_order places {unit} at {position[unit]:02d}"
            )
        manifest = folder / "manifest.yaml"
        if manifest.is_file():
            raw = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            if str(raw.get("unit")) != unit_id_of(folder.name):
                errors.append(f"{book.id}: {folder.name}/manifest.yaml unit must be {unit}")
    if len(set(prefixes)) != len(prefixes):
        errors.append(f"{book.id}: unit folder prefixes repeat")
    if sorted(prefixes) != list(range(1, len(prefixes) + 1)):
        errors.append(f"{book.id}: unit folder prefixes must be 01..{len(prefixes):02d} with no gaps")
    for unit in order:
        if unit not in seen:
            errors.append(f"{book.id}: teaching_order unit {unit} has no NN-{unit} folder")

    first: dict[str, tuple[int, int]] = {}
    for week_index, week in enumerate(schedule.weeks):
        for allocation_index, allocation in enumerate(week.allocations):
            if allocation.unit is not None:
                first.setdefault(allocation.unit, (week_index, allocation_index))
    by_schedule = sorted(first, key=first.__getitem__)
    if list(order) != by_schedule:
        for index, (declared, scheduled) in enumerate(zip(order, by_schedule, strict=False)):
            if declared != scheduled:
                errors.append(
                    f"{book.id}: teaching_order position {index + 1:02d} is {declared}, but the "
                    f"schedule first reaches {scheduled} there"
                )
                break
        else:
            errors.append(f"{book.id}: teaching_order and the schedule list different units")

    expected = {"F": 1, "C": 1}
    for unit in order:
        code = _CODE.match(unit)
        if code is None:
            errors.append(f"{book.id}: teaching_order unit {unit} has no F/C code")
            continue
        track, number = code["track"], int(code["number"])
        if number != expected[track]:
            errors.append(
                f"{book.id}: {unit} is {track}{number} but is {track}{expected[track]} in "
                "teaching order (codes count up within F and within C)"
            )
        expected[track] = number + 1
    return Report(name=NAME, ok=not errors, errors=errors)
