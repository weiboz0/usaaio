from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.checks import schedule as schedule_checker
from tools.model import load_roadmap, load_syllabus

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-022-probabilistic-latent-models"
B2_021 = "B2-021-cross-modal-transformers-vision"
PREREQUISITES = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:F4-multivar-calculus",
    "book1:F5-probability",
    "book1:F6-svd-spectral",
    "book1:C1-ml-fundamentals",
    "book1:C2-linear-models",
    "book1:C5-neural-networks",
    "book1:C6-pytorch",
    "book1:C9-dimensionality-reduction",
    "book1:C11-neural-training",
    B2_021,
]
OWNED_CONCEPTS = [
    "multivariate-gaussian",
    "kl-divergence",
    "autoencoder",
    "gaussian-reparameterization",
    "variational-autoencoder",
]
KNOWLEDGE_POINTS = [
    "multivariate-gaussian",
    "gaussian-reparameterization",
    "kl-divergence",
    "autoencoder",
    "variational-autoencoder",
]
ROW_MODALITIES = {
    "multivariate-gaussian": ["theory", "derivation", "implementation"],
    "kl-divergence": ["theory", "derivation", "implementation"],
    "gaussian-reparameterization": ["theory", "derivation", "implementation"],
    "autoencoder": ["theory", "implementation", "model-training"],
    "variational-autoencoder": [
        "theory",
        "derivation",
        "implementation",
        "model-training",
    ],
}
# Exact Plan 027 practice ledger: (set, type, difficulty, minutes).
LEDGER = {
    1: ("A", "mc-normal-form", "intro", 20),
    2: ("A", "mc", "intro", 20),
    3: ("A", "mc", "intro", 20),
    4: ("A", "mc", "intro", 20),
    5: ("A", "mc", "core", 20),
    6: ("B", "constrained-coding", "intro", 50),
    7: ("B", "constrained-coding", "core", 50),
    8: ("B", "constrained-coding", "intro", 50),
    9: ("B", "constrained-coding", "core", 50),
    10: ("B", "constrained-coding", "intro", 50),
    11: ("B", "constrained-coding", "core", 50),
    12: ("B", "constrained-coding", "core", 50),
    13: ("B", "proof", "core", 45),
    14: ("B", "proof", "core", 45),
    15: ("B", "proof", "core", 45),
    16: ("B", "proof", "advanced", 45),
    17: ("C", "integrative", "core", 65),
    18: ("C", "integrative", "advanced", 65),
    19: ("C", "integrative", "advanced", 65),
    20: ("C", "integrative", "advanced", 65),
    21: ("C", "scenario", "core", 55),
    22: ("C", "scenario", "core", 55),
    23: ("C", "challenge", "advanced", 55),
    24: ("C", "challenge", "advanced", 55),
}
WEEK_PROBLEMS = (
    ("B2-022-p01", "B2-022-p02", "B2-022-p06", "B2-022-p13"),
    ("B2-022-p03", "B2-022-p07", "B2-022-p08", "B2-022-p14", "B2-022-p15"),
    ("B2-022-p04", "B2-022-p09", "B2-022-p10", "B2-022-p17", "B2-022-p18"),
    ("B2-022-p05", "B2-022-p11", "B2-022-p12", "B2-022-p16", "B2-022-p21"),
    ("B2-022-p19", "B2-022-p20", "B2-022-p22", "B2-022-p23", "B2-022-p24"),
)
WEEK_MINUTES = (255, 300, 340, 310, 385, 60)
SESSIONS = 5
SESSION_MINUTES = 90
BRIDGE_MINUTES = 30
REVIEW_MINUTES = 60
PRACTICE_MINUTES = 1110
BASELINE_WEEKS = 18
BASELINE_MINUTES = 4970
TARGET_WEEKS = 24
TARGET_MINUTES = 6620


def _coverage_map() -> dict[str, Any]:
    raw = yaml.safe_load(
        (BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(raw, dict)
    return raw


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _problem_minutes(problem_id: str) -> int:
    return LEDGER[int(problem_id[-2:])][3]


def test_ledger_and_schedule_minutes_reconcile() -> None:
    assert sorted(LEDGER) == list(range(1, 25))
    assert sum(row[3] for row in LEDGER.values()) == PRACTICE_MINUTES
    types = [row[1] for row in LEDGER.values()]
    assert sum(kind.startswith("mc") for kind in types) == 5
    assert types.count("constrained-coding") == 7
    assert types.count("proof") == 4
    assert types.count("integrative") == 4
    assert types.count("scenario") == 2
    assert types.count("challenge") == 2
    scheduled = [problem for week in WEEK_PROBLEMS for problem in week]
    assert sorted(scheduled) == [f"B2-022-p{n:02}" for n in range(1, 25)]
    computed = [
        (BRIDGE_MINUTES if index == 0 else 0)
        + SESSION_MINUTES
        + sum(_problem_minutes(problem) for problem in problems)
        for index, problems in enumerate(WEEK_PROBLEMS)
    ] + [REVIEW_MINUTES]
    assert tuple(computed) == WEEK_MINUTES
    assert sum(WEEK_MINUTES) == 1650
    assert BASELINE_MINUTES + sum(WEEK_MINUTES) == TARGET_MINUTES


def test_b2_022_planned_row_has_exact_registration_contract() -> None:
    raw = _coverage_map()
    matches = [row for row in raw["planned_units"] if row["id"] == UNIT_ID]

    assert len(matches) == 1
    planned = matches[0]
    assert planned["prerequisites"] == PREREQUISITES
    assert "book1:C7-cnn-transfer" not in planned["prerequisites"]
    assert planned["provisional_concepts"] == OWNED_CONCEPTS
    assert planned["knowledge_points"] == KNOWLEDGE_POINTS
    assert planned["estimated_hours"] == {"min": 22, "max": 28}
    assert planned["schedule_action"] == "extend"

    loaded = next(
        unit for unit in load_roadmap(BOOK2_ROOT).planned_units if unit.id == UNIT_ID
    )
    assert loaded.prerequisites == PREREQUISITES
    assert loaded.provisional_concepts == OWNED_CONCEPTS


def test_b2_022_double_length_standard_is_five_sessions_and_24_practices() -> None:
    standards = (ROOT / "docs" / "unit-standards.md").read_text(encoding="utf-8")
    assert "use 4–6 sessions" in standards
    assert "double-length units: 24–30" in standards
    assert 4 <= SESSIONS <= 6
    assert 24 <= len(LEDGER) <= 30


def test_b2_022_coverage_stays_missing_until_live_sources_exist() -> None:
    raw = _coverage_map()
    rows = {row["id"]: row for row in raw["knowledge_points"]}

    for concept, modalities in ROW_MODALITIES.items():
        row = rows[concept]
        assert row["coverage"] == "missing"
        assert row["destination"] == UNIT_ID
        assert row["shipped_concepts"] == []
        assert list(row["evidence_by_modality"]) == modalities
        assert row["deficits"] == {"modalities_missing": modalities}
        assert all(
            evidence == {"lesson_anchors": [], "practices": [], "assessments": []}
            for evidence in row["evidence_by_modality"].values()
        )

    assert UNIT_ID not in load_syllabus(BOOK2_ROOT).units
    assert not (BOOK2_ROOT / "units" / UNIT_ID).exists()
    assert UNIT_ID not in (
        BOOK2_ROOT / "curriculum" / "course-schedule.yaml"
    ).read_text(encoding="utf-8")
    assert "B2-022" not in (ROOT / "docs" / "unit-standards.md").read_text(
        encoding="utf-8"
    )


def _replace_syllabus_contract(path: Path, raw: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"(<!-- syllabus-canonical -->\s*```yaml\n)(.*?)(\n```)", text, re.DOTALL
    )
    assert match is not None
    replacement = (
        match.group(1) + yaml.safe_dump(raw, sort_keys=False).rstrip() + match.group(3)
    )
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")


def _four_manifest_root(tmp_path: Path) -> Path:
    """Schedule-only fixture: B2-021's tree relabelled as a prospective B2-022."""
    selected = tmp_path / "book2"
    shutil.copytree(BOOK2_ROOT, selected)
    target = selected / "units" / UNIT_ID
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(selected / "units" / B2_021, target)

    after_sessions = {
        problem_id: session
        for session, problem_ids in enumerate(WEEK_PROBLEMS, start=1)
        for problem_id in problem_ids
    }
    manifest_path = target / "manifest.yaml"
    manifest = _load_yaml(manifest_path)
    manifest["unit"] = UNIT_ID
    manifest["prereq_units"] = list(PREREQUISITES)
    manifest["estimated_minutes"]["practice"] = PRACTICE_MINUTES
    for number, problem in enumerate(manifest["practice"], start=1):
        problem_id = f"B2-022-p{number:02}"
        problem["id"] = problem_id
        problem["minutes"] = _problem_minutes(problem_id)
        problem["after_session"] = after_sessions[problem_id]
    _write_yaml(manifest_path, manifest)

    syllabus_path = selected / "syllabus.md"
    contract = yaml.safe_load(
        re.search(
            r"<!-- syllabus-canonical -->\s*```yaml\n(.*?)\n```",
            syllabus_path.read_text(encoding="utf-8"),
            re.DOTALL,
        ).group(1)
    )
    if not any(unit["id"] == UNIT_ID for unit in contract["units"]):
        new_unit = deepcopy(
            next(unit for unit in contract["units"] if unit["id"] == B2_021)
        )
        new_unit.update(
            id=UNIT_ID, title="Probabilistic Latent Models", prereqs=list(PREREQUISITES)
        )
        contract["units"].append(new_unit)
        _replace_syllabus_contract(syllabus_path, contract)

    schedule_path = selected / "curriculum" / "course-schedule.yaml"
    schedule = _load_yaml(schedule_path)
    schedule["weeks"] = schedule["weeks"][:BASELINE_WEEKS]
    schedule["total_book_weeks"] = TARGET_WEEKS
    schedule["total_minutes"] = TARGET_MINUTES
    schedule["final_assessment"]["after_book_week"] = TARGET_WEEKS
    for offset, problem_ids in enumerate(WEEK_PROBLEMS):
        allocations: list[dict[str, Any]] = []
        if offset == 0:
            allocations.append(
                {"kind": "bridge-diagnostic", "unit": UNIT_ID, "minutes": BRIDGE_MINUTES}
            )
        allocations.append(
            {
                "kind": "lesson-session",
                "unit": UNIT_ID,
                "session": offset + 1,
                "minutes": SESSION_MINUTES,
            }
        )
        allocations.append(
            {
                "kind": "practice",
                "unit": UNIT_ID,
                "chunk": offset + 1,
                "minutes": sum(_problem_minutes(problem) for problem in problem_ids),
                "problem_ids": list(problem_ids),
            }
        )
        schedule["weeks"].append(
            {
                "book_week": BASELINE_WEEKS + 1 + offset,
                "global_week": 40 + BASELINE_WEEKS + 1 + offset,
                "allocations": allocations,
            }
        )
    schedule["weeks"].append(
        {
            "book_week": TARGET_WEEKS,
            "global_week": 40 + TARGET_WEEKS,
            "allocations": [
                {"kind": "review", "unit": UNIT_ID, "chunk": 1, "minutes": REVIEW_MINUTES}
            ],
        }
    )
    _write_yaml(schedule_path, schedule)
    return selected


def _report_for_mutation(tmp_path: Path, mutate: Callable[[dict[str, Any]], None]):
    selected = _four_manifest_root(tmp_path)
    schedule_path = selected / "curriculum" / "course-schedule.yaml"
    schedule = _load_yaml(schedule_path)
    mutate(schedule)
    _write_yaml(schedule_path, schedule)
    return schedule_checker.check_schedule(selected, expected_book_number=2)


def test_appending_six_week_ledger_after_b2_021_yields_week_24(tmp_path: Path) -> None:
    selected = _four_manifest_root(tmp_path)
    raw = _load_yaml(selected / "curriculum" / "course-schedule.yaml")
    assert [
        sum(allocation["minutes"] for allocation in week["allocations"])
        for week in raw["weeks"][BASELINE_WEEKS:]
    ] == list(WEEK_MINUTES)

    report = schedule_checker.check_schedule(selected, expected_book_number=2)

    assert report.ok, report.errors
    validated = schedule_checker.load_validated_schedule(selected, expected_book_number=2)
    assert validated.declared_week_count == TARGET_WEEKS
    assert validated.total_minutes == TARGET_MINUTES
    assert list(validated.global_weeks) == list(range(41, 65))
    assert raw["final_assessment"]["after_book_week"] == TARGET_WEEKS
    assert {
        problem_id
        for problem_id in validated.covered_problem_ids
        if problem_id.startswith("B2-022-")
    } == {f"B2-022-p{n:02}" for n in range(1, 25)}


def _move_bridge_before_week_19(schedule: dict[str, Any]) -> None:
    bridge = schedule["weeks"][BASELINE_WEEKS]["allocations"].pop(0)
    schedule["weeks"][BASELINE_WEEKS - 1]["allocations"].insert(0, bridge)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda schedule: schedule["weeks"][BASELINE_WEEKS]["allocations"][2][
                "problem_ids"
            ].__setitem__(0, "B2-022-p02"),
            "B2-022-p02 must appear exactly once",
            id="duplicate-problem-id",
        ),
        pytest.param(
            lambda schedule: (
                schedule["weeks"][BASELINE_WEEKS + 1]["allocations"][0].update(session=3),
                schedule["weeks"][BASELINE_WEEKS + 2]["allocations"][0].update(session=2),
            ),
            f"{UNIT_ID} lesson sessions must appear once in strictly increasing order",
            id="misordered-sessions",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][BASELINE_WEEKS + 2]["allocations"].pop(0),
            f"unallocated lesson session {UNIT_ID}#3",
            id="missing-session-3",
        ),
        pytest.param(
            lambda schedule: (
                schedule["weeks"][BASELINE_WEEKS]["allocations"][2].update(minutes=136),
                schedule.update(total_minutes=TARGET_MINUTES + 1),
            ),
            f"{UNIT_ID} practice chunk 1 problem minutes 135; allocation minutes 136",
            id="minute-mismatch",
        ),
        pytest.param(
            _move_bridge_before_week_19,
            f"{UNIT_ID} bridge-diagnostic allocation must begin after {B2_021} final review",
            id="before-week-19",
        ),
    ],
)
def test_six_week_ledger_rejects_contract_mutations(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], message: str
) -> None:
    report = _report_for_mutation(tmp_path, mutate)

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors
