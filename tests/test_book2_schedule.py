from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
from collections.abc import Callable
from copy import deepcopy
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
BOOK2_SCHEDULE_SHA256 = "435ac290b1b09d9308c6151c4c69f28dd72d0fdccf82ad3fd5045d230ce35f48"
BOOK2_MANIFEST_SHA256 = "c50be81714b421e85f1e3e3afdf0eddd65352ae7c0f94ba5f655cb2716e9d5c1"
B2_019 = "B2-019-attention-transformers"
B2_020 = "B2-020-language-transformers"
B2_020_WEEK_PROBLEMS = (
    ("B2-020-p01", "B2-020-p02", "B2-020-p06", "B2-020-p13"),
    ("B2-020-p03", "B2-020-p04", "B2-020-p07", "B2-020-p08", "B2-020-p14"),
    (
        "B2-020-p05",
        "B2-020-p09",
        "B2-020-p10",
        "B2-020-p15",
        "B2-020-p16",
        "B2-020-p17",
        "B2-020-p23",
    ),
    ("B2-020-p12", "B2-020-p18", "B2-020-p21"),
    ("B2-020-p11", "B2-020-p19", "B2-020-p20", "B2-020-p22", "B2-020-p24"),
)


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


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _register_b2_020(root: Path) -> None:
    syllabus_path = root / "syllabus.md"
    document = syllabus_path.read_text(encoding="utf-8")
    match = re.search(
        r"(<!-- syllabus-canonical -->\n```yaml\n)(.*?)(\n```)\n",
        document,
        re.DOTALL,
    )
    assert match is not None
    syllabus = yaml.safe_load(match.group(2))
    unit = deepcopy(syllabus["units"][0])
    unit.update(
        id=B2_020,
        title="Language Transformers",
        prereqs=[B2_019],
        concept_prerequisites=[],
        teaches=[],
    )
    syllabus["units"].append(unit)
    replacement = match.group(1) + yaml.safe_dump(syllabus, sort_keys=False).rstrip() + match.group(3) + "\n"
    syllabus_path.write_text(
        document[: match.start()] + replacement + document[match.end() :],
        encoding="utf-8",
    )


def _two_manifest_root(tmp_path: Path) -> Path:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    _register_b2_020(selected)

    source = selected / "units" / B2_019
    target = selected / "units" / B2_020
    shutil.copytree(source, target)
    manifest_path = target / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["unit"] = B2_020
    manifest["prereq_units"] = [B2_019]
    manifest["concept_prerequisites"] = []
    scheduled_session = {
        problem_id: session
        for session, problem_ids in enumerate(B2_020_WEEK_PROBLEMS, start=1)
        for problem_id in problem_ids
    }
    for problem in manifest["practice"]:
        problem["id"] = problem["id"].replace("B2-019-", "B2-020-")
        problem["after_session"] = min(
            problem["after_session"], scheduled_session[problem["id"]]
        )
    _write_yaml(manifest_path, manifest)

    schedule_path = selected / "curriculum" / "course-schedule.yaml"
    schedule = _load_schedule(selected)
    appended = deepcopy(schedule["weeks"])
    for index, week in enumerate(appended):
        week["book_week"] += 6
        week["global_week"] += 6
        for allocation in week["allocations"]:
            allocation["unit"] = B2_020
            if allocation["kind"] == "practice":
                allocation["problem_ids"] = list(B2_020_WEEK_PROBLEMS[index])
    schedule["weeks"].extend(appended)
    schedule["total_book_weeks"] = 12
    schedule["total_minutes"] = 3320
    schedule["final_assessment"]["after_book_week"] = 12
    _write_yaml(schedule_path, schedule)
    return selected


def _report_for_two_manifest_mutation(
    tmp_path: Path,
    *,
    schedule_mutation: Callable[[dict[str, Any]], None] | None = None,
    manifest_mutation: Callable[[dict[str, Any]], None] | None = None,
):
    selected = _two_manifest_root(tmp_path)
    if schedule_mutation is not None:
        schedule_path = selected / "curriculum" / "course-schedule.yaml"
        schedule = _load_schedule(selected)
        schedule_mutation(schedule)
        _write_yaml(schedule_path, schedule)
    if manifest_mutation is not None:
        manifest_path = selected / "units" / B2_020 / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest_mutation(manifest)
        _write_yaml(manifest_path, manifest)
    return schedule_checker.check_schedule(selected, expected_book_number=2)


def _assert_both_schedule_apis_reject(root: Path, message: str) -> None:
    report = schedule_checker.check_schedule(root, expected_book_number=2)
    assert not report.ok
    assert any(message in error for error in report.errors), report.errors
    with pytest.raises(ValueError) as exc_info:
        schedule_checker.load_validated_schedule(root, expected_book_number=2)
    assert message in str(exc_info.value)


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


def test_registered_book2_schedule_is_exact_six_week_live_ledger() -> None:
    raw = _load_schedule()

    assert raw["schedule_version"] == 1
    assert raw["book"] == 2
    assert raw["status"] == "live"
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
    ] == [255, 275, 420, 270, 380, 60]

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
    assert validated.status == "live"
    assert [week.week for week in validated.weeks] == list(range(1, 7))
    assert list(validated.global_weeks) == list(range(41, 47))
    assert validated.total_minutes == 1660
    assert validated.covered_problem_ids == frozenset(problem_ids)
    inventory = audit_curriculum.build_inventory(BOOK2_ROOT)
    assert inventory["counts"]["scheduled_minutes"] == 1660
    assert inventory["counts"]["unit_practices"] == 24


def test_live_book2_minutes_enter_the_aggregate_baseline() -> None:
    rendered = render_course_structure.render_document(BOOK2_ROOT)
    aggregate = audit_curriculum.build_inventory(BOOK2_ROOT)

    assert aggregate["counts"]["scheduled_minutes"] == 1660
    assert "1,660 minutes" in rendered
    assert "live manifest reconciles every lesson, practice ID, path, and minute" in rendered
    assert "255/275/420/270/380/60-minute progression" in rendered

    documents = render_curriculum_roadmap.render_documents(ROOT)
    for document in documents.values():
        assert "Current scheduled baseline: **20535 minutes / 342.25 hours**." in document
        assert "| **Planned-unit subtotal** | **142** | **182** |" in document
    roadmap = documents[Path("docs/curriculum-roadmap.md")]
    assert (
        "| book2 | book2:B2-019-attention-transformers | Attention and Transformer "
        "Mechanics | round-2-extension | 22–28 |"
    ) in roadmap


def test_live_book2_schedule_reconciles_manifest_minutes_ids_and_paths() -> None:
    report = schedule_checker.check_schedule(BOOK2_ROOT, expected_book_number=2)

    assert report.ok, report.errors


def test_generic_book2_schedule_accepts_two_manifest_ledger(tmp_path: Path) -> None:
    selected = _two_manifest_root(tmp_path)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert report.ok, report.errors
    validated = schedule_checker.load_validated_schedule(
        selected, expected_book_number=2
    )
    assert validated.declared_week_count == 12
    assert validated.total_minutes == 3320
    assert validated.covered_problem_ids == frozenset(
        [f"B2-019-p{number:02}" for number in range(1, 25)]
        + [f"B2-020-p{number:02}" for number in range(1, 25)]
    )
    inventory = audit_curriculum.build_inventory(selected, expected_book_number=2)
    assert inventory["counts"]["scheduled_minutes"] == 3320
    assert inventory["counts"]["unit_practices"] == 48


def test_two_manifest_ledger_rejects_reversed_session_order(tmp_path: Path) -> None:
    def reverse_sessions(schedule: dict[str, Any]) -> None:
        for week in schedule["weeks"][6:11]:
            lesson = next(
                allocation
                for allocation in week["allocations"]
                if allocation["kind"] == "lesson-session"
            )
            lesson["session"] = 6 - lesson["session"]

    def make_after_session_compatible(manifest: dict[str, Any]) -> None:
        for problem in manifest["practice"]:
            problem["after_session"] = 5

    report = _report_for_two_manifest_mutation(
        tmp_path,
        schedule_mutation=reverse_sessions,
        manifest_mutation=make_after_session_compatible,
    )

    assert not report.ok
    assert any(
        f"{B2_020} lesson sessions must appear once in strictly increasing order"
        in error
        for error in report.errors
    ), report.errors


def test_two_manifest_ledger_rejects_practices_collapsed_into_review_week(
    tmp_path: Path,
) -> None:
    def collapse_practices(schedule: dict[str, Any]) -> None:
        practices = []
        for week in schedule["weeks"][6:11]:
            practice_index = next(
                index
                for index, allocation in enumerate(week["allocations"])
                if allocation["kind"] == "practice"
            )
            practices.append(week["allocations"].pop(practice_index))
        schedule["weeks"][11]["allocations"][:0] = practices

    report = _report_for_two_manifest_mutation(
        tmp_path, schedule_mutation=collapse_practices
    )

    assert not report.ok
    assert any(
        f"{B2_020} practice chunks must cover its instructional weeks in order"
        in error
        for error in report.errors
    ), report.errors


@pytest.mark.parametrize(
    ("schedule_mutation", "manifest_mutation", "message"),
    [
        pytest.param(
            lambda schedule: schedule["weeks"][6]["allocations"][2][
                "problem_ids"
            ].__setitem__(0, "B2-019-p01"),
            None,
            "B2-019-p01 must appear exactly once",
            id="duplicate-problem-across-units",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][8]["allocations"].pop(0),
            None,
            f"unallocated lesson session {B2_020}#3",
            id="missing-lesson-allocation",
        ),
        pytest.param(
            None,
            lambda manifest: manifest["practice"][0].update(minutes=21),
            f"{B2_020} practice chunk 1 problem minutes 136; allocation minutes 135",
            id="mismatched-practice-minute",
        ),
        pytest.param(
            None,
            lambda manifest: manifest["practice"][0].update(after_session=2),
            "B2-020-p01 requires session 2 before its scheduled practice allocation",
            id="after-session",
        ),
        pytest.param(
            lambda schedule: schedule.update(total_minutes=3319),
            None,
            "Book 2 declared total 3319; actual 3320",
            id="stale-total",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][0].update(
                minutes=31
            ),
            None,
            "B2-019 pre-existing ledger must remain unchanged",
            id="mutated-b2-019-ledger",
        ),
    ],
)
def test_two_manifest_ledger_rejects_contract_mutations(
    tmp_path: Path,
    schedule_mutation: Callable[[dict[str, Any]], None] | None,
    manifest_mutation: Callable[[dict[str, Any]], None] | None,
    message: str,
) -> None:
    report = _report_for_two_manifest_mutation(
        tmp_path,
        schedule_mutation=schedule_mutation,
        manifest_mutation=manifest_mutation,
    )

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors


@pytest.mark.parametrize("kind", ["bridge-diagnostic", "lesson-session", "practice", "review"])
def test_b2_020_allocations_must_follow_b2_019_final_review(
    tmp_path: Path, kind: str
) -> None:
    def move_early(schedule: dict[str, Any]) -> None:
        source_week = next(
            week
            for week in schedule["weeks"][6:]
            if any(allocation["kind"] == kind for allocation in week["allocations"])
        )
        source_index = next(
            index
            for index, allocation in enumerate(source_week["allocations"])
            if allocation["kind"] == kind
        )
        allocation = source_week["allocations"].pop(source_index)
        schedule["weeks"][5]["allocations"].insert(0, allocation)

    report = _report_for_two_manifest_mutation(
        tmp_path, schedule_mutation=move_early
    )

    assert not report.ok
    assert any(
        f"{B2_020} {kind} allocation must begin after {B2_019} final review"
        in error
        for error in report.errors
    ), report.errors


def test_live_book2_rejects_unit_directory_without_manifest(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    (selected / "units" / "B2-999-missing-manifest").mkdir()

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("must contain exactly one regular manifest.yaml; found 0" in error for error in report.errors)


def test_live_book2_rejects_extra_unregistered_manifest(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    extra = selected / "units" / "B2-999-extra"
    shutil.copytree(selected / "units" / B2_019, extra)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("unregistered Book 2 unit directory B2-999-extra" in error for error in report.errors)


def test_live_book2_rejects_extra_manifest_in_unit_directory(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    unit = selected / "units" / B2_019
    shutil.copy2(unit / "manifest.yaml", unit / "manifest-copy.yaml")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(
        "must contain exactly one regular manifest.yaml; found 2" in error
        for error in report.errors
    )


def test_live_book2_rejects_nonregular_manifest(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest = selected / "units" / B2_019 / "manifest.yaml"
    manifest.unlink()
    manifest.mkdir()

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("manifest.yaml must be a regular file" in error for error in report.errors)


def test_live_book2_rejects_non_directory_units_entry(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    (selected / "units" / "README.txt").write_text("not a unit", encoding="utf-8")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("units entry README.txt must be a regular directory" in error for error in report.errors)


@pytest.mark.parametrize("mode", ["symlink", "directory", "nonempty"])
def test_live_book2_rejects_malformed_gitkeep_sentinel(
    tmp_path: Path, mode: str
) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    sentinel = selected / "units" / ".gitkeep"
    sentinel.unlink()
    if mode == "symlink":
        sentinel.symlink_to(selected / "units" / B2_019, target_is_directory=True)
    elif mode == "directory":
        sentinel.mkdir()
    else:
        sentinel.write_text("not empty\n", encoding="utf-8")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(
        ".gitkeep sentinel must be a regular, nonsymlink, empty file" in error
        for error in report.errors
    ), report.errors


def test_live_book2_rejects_symlinked_unit_directory(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    (selected / "units" / "B2-999-linked-unit").symlink_to(
        selected / "units" / B2_019, target_is_directory=True
    )

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("unit directory symlink is forbidden" in error for error in report.errors)


def test_live_book2_rejects_symlinked_manifest(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    unit = selected / "units" / B2_019
    manifest = unit / "manifest.yaml"
    manifest.rename(unit / "real-manifest.yaml")
    manifest.symlink_to(unit / "real-manifest.yaml")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("manifest symlink is forbidden" in error for error in report.errors)


def test_live_book2_required_solution_path_uses_containment(tmp_path: Path) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest_path = selected / "units" / B2_019 / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["practice"][0]["solution_path"] = "practice/missing_solution.ipynb"
    _write_yaml(manifest_path, manifest)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(
        "path does not exist: units/B2-019-attention-transformers/practice/missing_solution.ipynb"
        in error
        for error in report.errors
    ), report.errors


def test_live_book2_rejects_unknown_policy_and_symlinked_solution_path(
    tmp_path: Path,
) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    unit = selected / "units" / B2_019
    linked = unit / "practice" / "linked_solution.ipynb"
    linked.symlink_to(unit / "practice" / "p02_solution.ipynb")
    manifest_path = unit / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["solution_policy"] = "optional"
    manifest["practice"][0]["solution_path"] = "practice/linked_solution.ipynb"
    _write_yaml(manifest_path, manifest)

    _assert_both_schedule_apis_reject(
        selected, "solution_policy must be 'required' or a valid deferred mapping"
    )
    report = schedule_checker.check_schedule(selected, expected_book_number=2)
    assert any("solution_path: declared manifest path" in error for error in report.errors)


def test_live_book2_deferred_solution_path_still_uses_containment(
    tmp_path: Path,
) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest_path = selected / "units" / B2_019 / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["solution_policy"] = {
        "status": "deferred",
        "plan": "plan-020",
        "expires": "2099-12-31",
    }
    manifest["practice"][0]["id"] = None
    manifest["practice"][0]["solution_path"] = "../../syllabus.md"
    _write_yaml(manifest_path, manifest)

    _assert_both_schedule_apis_reject(
        selected, "solution_path: declared manifest path: path escapes selected book root"
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda manifest: manifest.update(coverage_claims={"bad": "shape"}),
            "coverage_claims must be a list",
            id="claims-container",
        ),
        pytest.param(
            lambda manifest: manifest["coverage_claims"][0].update(
                evidence_by_modality=[]
            ),
            "coverage_claims row 0 evidence_by_modality must be a mapping",
            id="evidence-container",
        ),
        pytest.param(
            lambda manifest: next(
                iter(
                    manifest["coverage_claims"][0]["evidence_by_modality"].values()
                )
            ).update(lesson_anchors=7),
            "coverage_claims row 0 lesson_anchors must be a list",
            id="anchors-container",
        ),
    ],
)
def test_live_book2_rejects_malformed_coverage_path_containers_through_both_apis(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest_path = selected / "units" / B2_019 / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    _write_yaml(manifest_path, manifest)

    _assert_both_schedule_apis_reject(selected, message)


@pytest.mark.parametrize("mode", ["traversal", "symlink"])
def test_live_book2_paths_use_realpath_containment(tmp_path: Path, mode: str) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    unit = selected / "units" / B2_019
    manifest_path = unit / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if mode == "traversal":
        manifest["practice"][0]["path"] = "../../syllabus.md"
    else:
        linked = unit / "practice" / "linked.ipynb"
        linked.symlink_to(unit / "practice" / "p02.ipynb")
        manifest["practice"][0]["path"] = "practice/linked.ipynb"
    _write_yaml(manifest_path, manifest)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any("declared manifest path" in error for error in report.errors), report.errors


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda manifest: manifest["practice"][0].update(minutes=21),
            "B2-019-attention-transformers practice chunk 1 problem minutes 136; allocation minutes 135",
            id="manifest-minute",
        ),
        pytest.param(
            lambda manifest: manifest["practice"][0].update(id="B2-019-p99"),
            "live manifest problem IDs must exactly match scheduled problem_ids",
            id="manifest-id",
        ),
        pytest.param(
            lambda manifest: manifest["practice"][0].update(path="practice/missing.ipynb"),
            "path does not exist: units/B2-019-attention-transformers/practice/missing.ipynb",
            id="manifest-path",
        ),
        pytest.param(
            lambda manifest: manifest["practice"][21].update(after_session=6),
            "B2-019-p22 requires session 6 before its scheduled practice allocation",
            id="manifest-after-session",
        ),
    ],
)
def test_live_book2_schedule_rejects_manifest_drift(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    manifest_path = selected / "units" / "B2-019-attention-transformers" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors


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
            "practice chunk 1 problem minutes 135; allocation minutes 134",
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
    schedule_path = selected / "curriculum/course-schedule.yaml"
    schedule = yaml.safe_load(schedule_path.read_text(encoding="utf-8"))
    schedule["status"] = "staged"
    schedule_path.write_text(yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8")
    manifest = selected / "units" / "B2-019-attention-transformers" / "manifest.yaml"
    assert manifest.is_file()

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert not report.ok
    assert any(
        "staged Book 2 schedule is forbidden once a live manifest exists" in error
        for error in report.errors
    )


def test_shared_renderer_supports_live_book2_manifest_coverage() -> None:
    rendered = render_course_structure.render_document(BOOK2_ROOT)

    assert "Book 2 Schedule" in rendered
    assert "local weeks 1–6" in rendered
    assert "display weeks 41–46" in rendered
    assert "1,660 minutes" in rendered
    assert "Status: live." in rendered
    assert "live manifest reconciles every lesson, practice ID, path, and minute" in rendered
    assert "derivation-heavy Week 3" in rendered
    assert "planned future `r2-*` final assessment follows local Week 6" in rendered


def test_two_manifest_renderer_derives_ranges_cadences_and_final_week(
    tmp_path: Path,
) -> None:
    selected = _two_manifest_root(tmp_path)

    rendered = render_course_structure.render_document(
        selected, expected_book_number=2
    )

    assert "local weeks 1–12" in rendered
    assert "display weeks 41–52" in rendered
    assert rendered.count("255/275/420/270/380/60-minute progression") == 2
    assert "planned future `r2-*` final assessment follows local Week 12" in rendered


def test_live_book2_ledger_bytes_and_absence_of_b2_020_are_pinned() -> None:
    schedule_path = BOOK2_ROOT / "curriculum" / "course-schedule.yaml"
    manifest_path = BOOK2_ROOT / "units" / B2_019 / "manifest.yaml"

    assert hashlib.sha256(schedule_path.read_bytes()).hexdigest() == BOOK2_SCHEDULE_SHA256
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == BOOK2_MANIFEST_SHA256
    assert not (BOOK2_ROOT / "units" / B2_020).exists()
    assert B2_020 not in schedule_path.read_text(encoding="utf-8")


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
