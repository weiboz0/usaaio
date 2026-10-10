"""Plan 024 Task 1: the live Book 2 (Round 2) blueprint and its blueprint-check branch."""

from __future__ import annotations

import copy
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.checks.blueprint import check_blueprint
from tools.model import Report, load_blueprint, load_mock_manifests

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
BOOK2_ROOT = ROOT / "book2"

EXPECTED_BLUEPRINT: dict[str, Any] = {
    "blueprint_version": 1,
    "book": 2,
    "target": "round-2",
    "status": "live",
    "assessment_prefix": "r2-",
    "derived_from": ["book2:reference/analysis.md", "book2:curriculum/official-topics.yaml"],
    "total_points": 300,
    "days": 2,
    "day_duration_minutes": 240,
    "texture": {
        "problem_count": {"min": 4, "max": 6},
        "subparts": {"min": 22, "max": 32},
        "open_ended_points_share": {"min": 0.45, "max": 0.60},
    },
    "sections": [
        {"id": "d1-arc", "day": 1, "kind": "scaffolded-arc", "points": {"min": 80, "max": 100},
         "subparts": {"min": 10, "max": 16}, "problems": {"min": 1, "max": 1}},
        {"id": "d1-open", "day": 1, "kind": "open-ended", "points": {"min": 60, "max": 80},
         "problems": {"min": 1, "max": 1}},
        {"id": "d2-arc", "day": 2, "kind": "scaffolded-arc", "points": {"min": 40, "max": 60},
         "subparts": {"min": 6, "max": 10}, "problems": {"min": 1, "max": 1}},
        {"id": "d2-open", "day": 2, "kind": "open-ended", "points": {"min": 80, "max": 100},
         "problems": {"min": 2, "max": 2}},
    ],
    "default_anchors": {"d1-arc": 90, "d1-open": 70, "d2-arc": 50, "d2-open": [40, 50]},
    "default_time_budget": {
        1: {"d1-arc": 120, "d1-open": 120},
        2: {"d2-arc": 80, "d2-open": 160},
    },
    "topic_distribution": {
        "attention-transformers": {"target": 50, "min": 30, "max": 90},
        "language-transformers": {"target": 30, "min": 0, "max": 60},
        "cross-modal-vision": {"target": 10, "min": 0, "max": 30},
        "probabilistic-latent-models": {"target": 40, "min": 20, "max": 60},
        "generative-models": {"target": 10, "min": 0, "max": 30},
        "capstone": {"target": 160, "min": 120, "max": 180},
    },
    "difficulty_mix": {
        "intro": {"min": 0.10, "max": 0.30},
        "core": {"min": 0.35, "max": 0.60},
        "advanced": {"min": 0.20, "max": 0.40},
    },
    "default_difficulty_draw": {"intro": 0.20, "core": 0.45, "advanced": 0.35},
    "provenance_rules": {"original_share_min": 0.9},
    "arc_rotation": [
        {"d1": ["attention-transformers", "language-transformers"], "d2": ["probabilistic-latent-models"]},
        {"d1": ["cross-modal-vision", "attention-transformers"], "d2": ["generative-models"]},
        {"d1": ["language-transformers", "attention-transformers"],
         "d2": ["probabilistic-latent-models", "generative-models"]},
    ],
    "open_ended_families": [
        "scientific-ml-inverse-problems",
        "semi-supervised-pseudo-labeling",
        "mixture-parameter-regression",
    ],
}

ATT = "B2-019-attention-transformers"
LANG = "B2-020-language-transformers"
LAT = "B2-022-probabilistic-latent-models"
CAP = "B2-024-gpu-scientific-ml-capstone"

# (suffix, points, difficulty, cluster, units, concepts) for the d1 arc (90 pts, 14 entries)
D1_ARC = [
    ("1", 5, "intro", "attention-transformers", [ATT], ["attention-mask"]),
    ("2", 5, "intro", "attention-transformers", [ATT], ["attention-complexity"]),
    ("3", 5, "core", "attention-transformers", [ATT], ["attention-complexity"]),
    ("4", 10, "core", "attention-transformers", [ATT], ["multi-head-attention"]),
    ("5", 5, "intro", "language-transformers", [LANG], ["language-transformer"]),
    ("6", 5, "intro", "attention-transformers", [ATT], ["sinusoidal-positional-encoding"]),
    ("7", 10, "advanced", "attention-transformers", [ATT], ["sinusoidal-positional-encoding"]),
    ("8", 5, "intro", "language-transformers", [LANG], ["causal-language-modeling"]),
    ("9", 5, "intro", "language-transformers", [LANG], ["causal-language-modeling"]),
    ("10", 5, "core", "language-transformers", [LANG], ["causal-language-modeling"]),
    ("11", 5, "intro", "attention-transformers", [ATT], ["causal-self-attention"]),
    ("12", 10, "core", "attention-transformers", [ATT], ["multi-head-attention"]),
    ("13", 10, "advanced", "language-transformers", [LANG], ["language-transformer"]),
    ("14", 5, "advanced", "attention-transformers", [ATT], ["causal-self-attention"]),
]
# d2 arc (50 pts, 8 entries)
D2_ARC = [
    ("1", 5, "intro", ["kl-divergence"]),
    ("2", 5, "intro", ["variational-autoencoder"]),
    ("3", 10, "advanced", ["variational-autoencoder"]),
    ("4", 5, "core", ["variational-autoencoder"]),
    ("5", 5, "intro", ["gaussian-reparameterization"]),
    ("6", 5, "intro", ["kl-divergence"]),
    ("7", 10, "core", ["variational-autoencoder"]),
    ("8", 5, "intro", ["kl-divergence"]),
]


def _entry(test: str, pid: str, *, day: int, section: str, points: int, difficulty: str,
           cluster: str, units: list[str], concepts: list[str], answer_form: str = "short-answer",
           answer_key: Any = "A") -> dict[str, Any]:
    return {
        "id": f"{test}-{pid}",
        "day": day,
        "section": section,
        "units": units,
        "concepts": concepts,
        "cluster": cluster,
        "points": points,
        "difficulty": difficulty,
        "type": "theory",
        "answer_form": answer_form,
        "provenance": "original",
        "spec": f"fixture slot {pid}",
        "answer_key": answer_key,
    }


def valid_manifest(test: str = "r2-001") -> dict[str, Any]:
    problems: list[dict[str, Any]] = []
    for suffix, points, difficulty, cluster, units, concepts in D1_ARC:
        problems.append(_entry(test, f"p01-{suffix}", day=1, section="d1-arc", points=points,
                               difficulty=difficulty, cluster=cluster, units=units,
                               concepts=concepts))
    problems.append(_entry(test, "p02", day=1, section="d1-open", points=70, difficulty="advanced",
                           cluster="capstone", units=[CAP],
                           concepts=["scientific-ml-inverse-problems", "open-ended-experiment-design"],
                           answer_form="open-ended"))
    for suffix, points, difficulty, concepts in D2_ARC:
        problems.append(_entry(test, f"p03-{suffix}", day=2, section="d2-arc", points=points,
                               difficulty=difficulty, cluster="probabilistic-latent-models",
                               units=[LAT], concepts=concepts))
    problems.append(_entry(test, "p04", day=2, section="d2-open", points=40, difficulty="core",
                           cluster="capstone", units=[CAP],
                           concepts=["semi-supervised-pseudo-labeling"], answer_form="open-ended"))
    problems.append(_entry(test, "p05", day=2, section="d2-open", points=50, difficulty="core",
                           cluster="capstone", units=[CAP],
                           concepts=["mixture-parameter-regression"], answer_form="open-ended"))
    return {
        "test": test,
        "blueprint_version": 1,
        "generated": "2026-10-10",
        "status": "final",
        "generation_parameters": {},
        "day_duration_minutes": 240,
        "total_points": 300,
        "time_budget": {1: {"d1-arc": 120, "d1-open": 120}, 2: {"d2-arc": 80, "d2-open": 160}},
        "problems": problems,
    }


def write_book2(root: Path, manifest: dict[str, Any] | None, *,
                blueprint_mutator: Callable[[dict[str, Any]], None] | None = None) -> Path:
    (root / "mocktests").mkdir(parents=True)
    blueprint = yaml.safe_load((BOOK2_ROOT / "mocktests" / "blueprint.yaml").read_text())
    if blueprint_mutator is not None:
        blueprint_mutator(blueprint)
    (root / "mocktests" / "blueprint.yaml").write_text(yaml.safe_dump(blueprint, sort_keys=False))
    shutil.copyfile(BOOK2_ROOT / "syllabus.md", root / "syllabus.md")
    if manifest is not None:
        test_dir = root / "mocktests" / manifest["test"]
        test_dir.mkdir()
        (test_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return root


def _problem(manifest: dict[str, Any], suffix: str) -> dict[str, Any]:
    return next(p for p in manifest["problems"] if p["id"].endswith(f"-{suffix}"))


def test_live_book2_blueprint_is_the_plan_024_version_1_yaml():
    raw = yaml.safe_load((BOOK2_ROOT / "mocktests" / "blueprint.yaml").read_text())
    assert raw == EXPECTED_BLUEPRINT


def test_live_book2_blueprint_clusters_match_book2_syllabus_and_targets_sum():
    from tools.model import load_syllabus

    blueprint = load_blueprint(BOOK2_ROOT)
    syllabus = load_syllabus(BOOK2_ROOT)
    assert set(blueprint.topic_distribution) == syllabus.clusters
    assert sum(row["target"] for row in blueprint.topic_distribution.values()) == 300
    for rotation in blueprint.raw["arc_rotation"]:
        assert set(rotation["d1"]) | set(rotation["d2"]) <= syllabus.clusters
    for family in blueprint.raw["open_ended_families"]:
        assert syllabus.concepts[family] == "capstone"
    anchors = blueprint.raw["default_anchors"]
    assert anchors["d1-arc"] + anchors["d1-open"] + anchors["d2-arc"] + sum(anchors["d2-open"]) == 300
    for day, budget in blueprint.raw["default_time_budget"].items():
        assert sum(budget.values()) == blueprint.raw["day_duration_minutes"]
        assert set(budget) == {s["id"] for s in blueprint.sections if s["day"] == day}


def test_live_book2_blueprint_check_passes_on_registered_book():
    report = check_blueprint(BOOK2_ROOT)
    assert report.ok, report.errors
    assert report.warnings == []


def test_book1_blueprint_check_result_is_unchanged():
    assert check_blueprint(BOOK1_ROOT) == Report(name="blueprint-check", ok=True)


def test_valid_r2_fixture_manifest_passes(tmp_path):
    write_book2(tmp_path, valid_manifest())
    report = check_blueprint(tmp_path)
    assert report.ok, report.errors


def test_model_parses_day_and_per_day_time_budget(tmp_path):
    write_book2(tmp_path, valid_manifest())
    manifest = load_mock_manifests(tmp_path, book_number=2)[0]
    assert manifest.day_duration_minutes == 240
    assert manifest.day_time_budget == {1: {"d1-arc": 120, "d1-open": 120},
                                        2: {"d2-arc": 80, "d2-open": 160}}
    assert manifest.time_budget == {}
    assert manifest.duration_minutes == 0
    assert {problem.day for problem in manifest.problems} == {1, 2}


def test_model_book1_manifest_has_no_day_fields():
    manifest = load_mock_manifests(BOOK1_ROOT, book_number=1)[0]
    assert manifest.day_duration_minutes == 0
    assert manifest.day_time_budget == {}
    assert all(problem.day is None for problem in manifest.problems)


def _set_points(manifest, suffix, points):
    _problem(manifest, suffix)["points"] = points


def _drop_d2_open_p05(manifest):
    manifest["problems"] = [p for p in manifest["problems"] if not p["id"].endswith("-p05")]
    _problem(manifest, "p04")["points"] = 90


def _collapse_d2_arc(manifest):
    keep = [p for p in manifest["problems"] if not p["id"].split("-", 2)[2].startswith("p03-")]
    arc = [p for p in manifest["problems"] if p["id"].split("-", 2)[2].startswith("p03-")][:5]
    for row, points in zip(arc, [10, 10, 10, 10, 10], strict=True):
        row["points"] = points
    manifest["problems"] = keep + arc


def _wrong_day(manifest):
    _problem(manifest, "p02")["day"] = 2


def _missing_day(manifest):
    del _problem(manifest, "p01-3")["day"]


def _budget_sum(manifest):
    manifest["time_budget"][1]["d1-open"] = 110


def _budget_sections(manifest):
    manifest["time_budget"][1] = {"d1-arc": 120, "d2-open": 120}


def _day_duration(manifest):
    manifest["day_duration_minutes"] = 180
    manifest["time_budget"] = {1: {"d1-arc": 90, "d1-open": 90}, 2: {"d2-arc": 60, "d2-open": 120}}


def _family(manifest):
    _problem(manifest, "p04")["concepts"] = ["open-ended-experiment-design"]


def _second_d1_arc_problem(manifest):
    _problem(manifest, "p01-14")["id"] = "r2-001-p06-1"


@pytest.mark.parametrize(
    ("name", "mutate", "expected"),
    [
        ("section-points", lambda m: (_set_points(m, "p01-4", 25), _set_points(m, "p02", 55)),
         "section d1-arc points out of range"),
        ("section-subparts", _collapse_d2_arc, "section d2-arc subparts out of range"),
        ("section-problems", _drop_d2_open_p05, "section d2-open problems out of range"),
        ("second-arc-problem", _second_d1_arc_problem, "section d1-arc problems out of range"),
        ("entry-day", _wrong_day, "r2-001-p02 day 2 != section d1-open day 1"),
        ("missing-day", _missing_day, "r2-001-p01-3 missing day"),
        ("time-budget-sum", _budget_sum, "time_budget day 1 sums to 230, not day_duration_minutes 240"),
        ("time-budget-sections", _budget_sections, "time_budget day 1 sections"),
        ("day-duration", _day_duration, "day_duration_minutes 180 differs from blueprint 240"),
        ("open-ended-family", _family, "r2-001-p04 open-ended problem lacks an open_ended_families concept"),
        ("total", lambda m: _set_points(m, "p01-1", 10), "points sum 305 != 300"),
        ("difficulty", lambda m: [p.update(difficulty="advanced") for p in m["problems"]
                                  if p["difficulty"] == "core"],
         "difficulty core share out of range"),
        ("provenance", lambda m: _problem(m, "p02").update(provenance="adapted", **{"adapted-from": "x"}),
         "original provenance share below minimum"),
        ("dominant-cluster", lambda m: _problem(m, "p01-2").update(cluster="language-transformers"),
         "r2-001-p01-2 invalid dominant cluster language-transformers"),
    ],
)
def test_book2_rule_rejects_violating_manifest(tmp_path, name, mutate, expected):
    manifest = copy.deepcopy(valid_manifest())
    mutate(manifest)
    write_book2(tmp_path, manifest)
    report = check_blueprint(tmp_path)
    assert not report.ok, name
    assert any(expected in error for error in report.errors), report.errors


def test_arc_clusters_follow_rotation_index_of_test_number(tmp_path):
    # r2-002 uses rotation index 1: d1 = [cross-modal-vision, attention-transformers],
    # so the language-transformers entries of the r2-001-shaped arc are rejected.
    write_book2(tmp_path, valid_manifest("r2-002"))
    report = check_blueprint(tmp_path)
    assert not report.ok
    assert any("r2-002-p01-5 cluster language-transformers not in d1 arc rotation" in error
               for error in report.errors), report.errors
    # r2-004 wraps to index 0 and passes.
    other = tmp_path / "wrap"
    write_book2(other, valid_manifest("r2-004"))
    assert check_blueprint(other).ok


def test_open_ended_points_share_is_enforced(tmp_path):
    def tighten(blueprint):
        blueprint["texture"]["open_ended_points_share"] = {"min": 0.55, "max": 0.60}

    write_book2(tmp_path, valid_manifest(), blueprint_mutator=tighten)
    report = check_blueprint(tmp_path)
    assert not report.ok
    assert any("open-ended points share 0.533 out of range" in error for error in report.errors)


def test_texture_counts_are_enforced(tmp_path):
    def tighten(blueprint):
        blueprint["texture"]["subparts"] = {"min": 26, "max": 32}
        blueprint["texture"]["problem_count"] = {"min": 6, "max": 6}

    write_book2(tmp_path, valid_manifest(), blueprint_mutator=tighten)
    report = check_blueprint(tmp_path)
    assert any(error.endswith("subparts out of range") for error in report.errors)
    assert any(error.endswith("problem_count out of range") for error in report.errors)


def test_book1_only_keys_are_not_applied_to_book2(tmp_path):
    # The valid r2 fixture has no 5-point atom majority, no programming entries, no
    # duration_minutes, and no draws_on_clusters; none of the Book 1 rules fire.
    write_book2(tmp_path, valid_manifest())
    errors = check_blueprint(tmp_path).errors
    for fragment in ("five-point", "programming share", "duration_minutes",
                     "cluster not allowed in section"):
        assert not any(fragment in error for error in errors)


def test_planned_blueprint_status_is_no_longer_accepted(tmp_path):
    (tmp_path / "mocktests").mkdir()
    (tmp_path / "mocktests" / "blueprint.yaml").write_text(
        "blueprint_version: 1\nbook: 2\ntarget: round-2\nstatus: planned\nassessment_prefix: r2-\n"
        "derived_from: [book2:reference/analysis.md, book2:curriculum/official-topics.yaml]\n"
    )
    shutil.copyfile(BOOK2_ROOT / "syllabus.md", tmp_path / "syllabus.md")
    report = check_blueprint(tmp_path)
    assert not report.ok
    assert any("planned" in error for error in report.errors)


def test_draft_r2_manifest_is_skipped_loudly(tmp_path):
    manifest = valid_manifest()
    manifest["status"] = "draft"
    write_book2(tmp_path, manifest)
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert any("DRAFT manifest" in warning for warning in report.warnings)


def test_answerkey_discovers_flat_two_day_r2_manifest(tmp_path):
    from tools.checks.answerkey import check_answerkey

    manifest = valid_manifest()
    write_book2(tmp_path, manifest)
    solutions = tmp_path / "mocktests" / "r2-001" / "solutions"
    solutions.mkdir()
    markers = [f"- {p['id']}: answer: {p['answer_key']}" for p in manifest["problems"]]
    (solutions / "answers.md").write_text("\n".join(markers) + "\n")
    assert check_answerkey(tmp_path, book_number=2).ok

    (solutions / "answers.md").write_text("\n".join(markers[1:]) + "\n")
    report = check_answerkey(tmp_path, book_number=2)
    assert not report.ok
    assert any("missing answer marker for r2-001-p01-1" in error for error in report.errors)


def test_overlap_scan_discovers_flat_two_day_r2_statement_files(tmp_path):
    from tools.checks.overlap import check_overlap

    statement = (
        "Consider an imaginary lighthouse keeper who records the brightness of seven lamps "
        "every evening and wants to predict tomorrow's brightness from the previous week "
        "using a carefully specified recurrence with fixed coefficients and seeded noise."
    )
    manifest = valid_manifest()
    _problem(manifest, "p02")["files"] = ["theory/p02.md"]
    write_book2(tmp_path, manifest)
    (tmp_path / "mocktests" / "r2-001" / "theory").mkdir()
    (tmp_path / "mocktests" / "r2-001" / "theory" / "p02.md").write_text(statement)
    ref = tmp_path / "reference" / "r2-fixture"
    ref.mkdir(parents=True)
    ref.joinpath("index.yaml").write_text(yaml.safe_dump({"problems": [{"id": "x", "text": statement}]}))
    report = check_overlap(tmp_path, book_number=2)
    assert not report.ok
    assert any("r2-001-p02 overlaps" in error for error in report.errors), report.errors
