import importlib
from datetime import date
import re
from pathlib import Path

import pytest
import yaml

from tools.checks.prereq import check_prereq
from tools.model import (
    load_blueprint,
    load_mock_manifests,
    load_syllabus,
    load_syllabus_contract,
    load_unit_manifests,
)

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"


def _books_module():
    try:
        return importlib.import_module("tools.books")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.books":
            raise
        pytest.fail("tools.books is the missing Plan 019 registry producer")


def test_load_syllabus_real_repo():
    syllabus = load_syllabus(BOOK1_ROOT)
    taught = [concept for unit in syllabus.units.values() for concept in unit.teaches]
    assert len(syllabus.units) >= 16
    assert len(syllabus.concepts) >= 100
    assert len(taught) == len(set(taught))
    assert set(taught) == set(syllabus.concepts)
    assert set(syllabus.concepts.values()) <= syllabus.clusters


def test_sentinel_must_be_unique(tmp_path):
    (tmp_path / "syllabus.md").write_text(
        "<!-- syllabus-canonical -->\n```yaml\nbaseline: {}\n```\n<!-- syllabus-canonical -->\n"
    )
    with pytest.raises(ValueError, match="exactly once"):
        load_syllabus(tmp_path)


def test_load_blueprint_real_repo():
    blueprint = load_blueprint(BOOK1_ROOT)
    assert sum(row["target"] for row in blueprint.topic_distribution.values()) == blueprint.total_points


def test_missing_dirs_yield_empty_lists(tmp_path):
    assert load_unit_manifests(tmp_path) == []
    assert load_mock_manifests(tmp_path) == []


def test_load_unit_manifests_rejects_external_unit_directory_symlink(tmp_path):
    outside = tmp_path / "outside" / "escaped-unit"
    outside.mkdir(parents=True)
    (outside / "manifest.yaml").write_text(
        """
unit: escaped-unit
concepts_taught: []
concepts_used: []
prereq_units: []
practice: []
""",
        encoding="utf-8",
    )
    units = tmp_path / "book" / "units"
    units.mkdir(parents=True)
    (units / "escaped-unit").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="unit directory must be a local real directory"):
        load_unit_manifests(tmp_path / "book")


def test_load_unit_manifests_rejects_symlinked_units_directory(tmp_path):
    outside_units = tmp_path / "outside-units"
    unit_dir = outside_units / "escaped-unit"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: escaped-unit
concepts_taught: []
concepts_used: []
prereq_units: []
practice: []
""",
        encoding="utf-8",
    )
    book = tmp_path / "book"
    book.mkdir()
    (book / "units").symlink_to(outside_units, target_is_directory=True)

    with pytest.raises(ValueError, match="unit directory must be a local real directory"):
        load_unit_manifests(book)


def test_unit_manifest_rejects_non_string_solution_policy(tmp_path):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
solution_policy: [required]
concepts_taught: []
concepts_used: []
prereq_units: []
practice: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="solution_policy must be 'required' or a deferred mapping"):
        load_unit_manifests(tmp_path)


def _write_deferred_manifest(
    root: Path,
    *,
    unit: str = "B2-020-language-transformers",
    plan: str = "plan-020",
    expires: str = "2026-09-30",
    with_solution: bool = False,
) -> None:
    unit_dir = root / "units" / unit
    unit_dir.mkdir(parents=True)
    solution_path = "practice/p01_solution.ipynb"
    (unit_dir / "manifest.yaml").write_text(
        f"""
unit: {unit}
book: 2
layer: round-2-extension
round: 2
track: extension
solution_policy: {{status: deferred, plan: {plan}, expires: '{expires}'}}
concepts_taught: []
concepts_used: []
concept_prerequisites: []
prereq_units: []
bridge_diagnostic:
  path: lessons/00-book1-bridge.ipynb
  minutes: 30
  referenced_concepts: []
coverage_claims: []
practice:
  - id: B2-020-p01
    concepts: []
    path: practice/p01.ipynb
    solution_path: {solution_path!r}
    minutes: 20
    after_session: 1
    compute: {{policy: cpu, seed: 20260812}}
""",
        encoding="utf-8",
    )
    if with_solution:
        solution = unit_dir / solution_path
        solution.parent.mkdir(parents=True)
        solution.write_text("{}", encoding="utf-8")


def test_named_b2_020_deferred_policy_is_valid_through_expiry(tmp_path):
    _write_deferred_manifest(tmp_path)

    manifest = load_unit_manifests(tmp_path, as_of_date=date(2026, 9, 30))[0]

    assert manifest.solution_policy == "deferred"
    assert manifest.solution_policy_plan == "plan-020"
    assert manifest.solution_policy_expires == "2026-09-30"


def test_named_b2_020_deferred_policy_expires_after_pinned_date(tmp_path):
    _write_deferred_manifest(tmp_path)

    with pytest.raises(ValueError, match="expired after 2026-09-30"):
        load_unit_manifests(tmp_path, as_of_date=date(2026, 10, 1))


@pytest.mark.parametrize(
    ("unit", "plan", "expires"),
    [
        ("F1-scientific-python", "plan-020", "2026-09-30"),
        ("B2-019-attention-transformers", "plan-020", "2026-09-30"),
        ("B2-020-language-transformers", "plan-019", "2026-09-30"),
        ("B2-020-language-transformers", "plan-020", "2026-10-01"),
    ],
)
def test_deferred_policy_is_narrowly_pinned_to_b2_020_lifecycle(
    tmp_path: Path, unit: str, plan: str, expires: str
) -> None:
    _write_deferred_manifest(tmp_path, unit=unit, plan=plan, expires=expires)

    with pytest.raises(ValueError, match="only B2-020-language-transformers"):
        load_unit_manifests(tmp_path, as_of_date=date(2026, 9, 1))


def test_b2_020_deferred_policy_rejects_even_one_declared_solution(tmp_path: Path) -> None:
    _write_deferred_manifest(tmp_path, with_solution=True)

    with pytest.raises(ValueError, match="must not have a solution file present"):
        load_unit_manifests(tmp_path, as_of_date=date(2026, 9, 1))


def test_environment_cannot_override_deferred_policy_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_deferred_manifest(tmp_path)
    monkeypatch.setenv("USAAIO_HISTORICAL_VERIFY", "1")
    monkeypatch.setenv("USAAIO_AS_OF_DATE", "2026-09-01")

    with pytest.raises(ValueError, match="expired after 2026-09-30"):
        load_unit_manifests(tmp_path, as_of_date=date(2026, 10, 1))


def test_unit_manifest_roundtrip(tmp_path):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: F1-p01
    concepts: [numpy-arrays]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )
    manifests = load_unit_manifests(tmp_path)
    assert manifests[0].unit_id == "F1-scientific-python"
    assert manifests[0].lesson_sessions is None
    assert manifests[0].practice[0].solution_path == "practice/p01_solution.ipynb"
    assert manifests[0].practice[0].minutes is None


def test_unit_manifest_parses_optional_positive_practice_minutes(tmp_path):
    unit_dir = tmp_path / "units" / "C11-neural-training"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: C11-neural-training
concepts_taught: [softmax]
concepts_used: []
prereq_units: []
practice:
  - id: C11-p01
    concepts: [softmax]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
    minutes: 15
"""
    )

    manifests = load_unit_manifests(tmp_path)

    assert manifests[0].practice[0].minutes == 15


@pytest.mark.parametrize("yaml_value", ["0", "-1", "true", "1.5", "'15'", "null"])
def test_unit_manifest_rejects_non_positive_integer_practice_minutes(
    tmp_path, yaml_value
):
    unit_dir = tmp_path / "units" / "C11-neural-training"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: C11-neural-training
concepts_taught: [softmax]
concepts_used: []
prereq_units: []
practice:
  - id: C11-p01
    concepts: [softmax]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
    minutes: {yaml_value}
"""
    )

    message = rf"{re.escape(str(manifest_path))}: practice row 0 minutes must be a positive integer"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


def test_unit_manifest_parses_lesson_sessions(tmp_path):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson: 425
  lesson_sessions: [85, 85, 85, 85, 85]
practice: []
"""
    )

    manifests = load_unit_manifests(tmp_path)

    assert manifests[0].lesson_sessions == [85, 85, 85, 85, 85]


@pytest.mark.parametrize("yaml_value", ["85", "[85]", "null"])
def test_unit_manifest_rejects_non_mapping_estimated_minutes(tmp_path, yaml_value):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F1-scientific-python
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes must be a mapping when present"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


@pytest.mark.parametrize(
    ("yaml_value", "detail"),
    [
        ("85", "must be a list"),
        ("true", "must be a list"),
        ("[true, 85]", "item 0 must be an integer"),
        ("[85, 42.5]", "item 1 must be an integer"),
        ("[85, 0]", "item 1 must be positive"),
        ("[-1, 85]", "item 0 must be positive"),
    ],
)
def test_unit_manifest_rejects_malformed_lesson_sessions(
    tmp_path, yaml_value, detail
):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson_sessions: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes\.lesson_sessions {detail}"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


def _write_session_manifest(tmp_path, *, concept_sessions, practice):
    unit_dir = tmp_path / "units" / "C12-classical-models"
    unit_dir.mkdir(parents=True)
    manifest = {
        "unit": "C12-classical-models",
        "concepts_taught": ["logistic-regression", "svm"],
        "concepts_used": [],
        "prereq_units": [],
        "estimated_minutes": {
            "lesson": 180,
            "lesson_sessions": [90, 90],
            "practice": sum(row.get("minutes", 0) for row in practice),
            "review": 60,
        },
        "concept_sessions": concept_sessions,
        "practice": practice,
    }
    (unit_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))


def _session_problem(*, concepts=None, after_session=1):
    row = {
        "id": "C12-p01",
        "concepts": concepts or ["logistic-regression"],
        "path": "practice/p01.ipynb",
        "solution_path": "practice/p01_solution.ipynb",
        "minutes": 20,
    }
    if after_session is not None:
        row["after_session"] = after_session
    return row


def test_unit_manifest_parses_optional_concept_sessions_and_after_session(tmp_path):
    _write_session_manifest(
        tmp_path,
        concept_sessions={"logistic-regression": 1, "svm": 2},
        practice=[_session_problem()],
    )

    manifest = load_unit_manifests(tmp_path)[0]

    assert manifest.concept_sessions == {"logistic-regression": 1, "svm": 2}
    assert manifest.practice[0].after_session == 1


@pytest.mark.parametrize(
    ("concept_sessions", "practice"),
    [
        pytest.param([], [_session_problem()], id="not-a-mapping"),
        pytest.param(
            {"logistic-regression": 1},
            [_session_problem()],
            id="keys-do-not-equal-owned-concepts",
        ),
        pytest.param(
            {"logistic-regression": True, "svm": 2},
            [_session_problem()],
            id="boolean-session",
        ),
        pytest.param(
            {"logistic-regression": 0, "svm": 2},
            [_session_problem()],
            id="zero-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 3},
            [_session_problem()],
            id="session-past-lesson-count",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(concepts=["foreign-concept"])],
            id="practice-without-owned-concept",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=None)],
            id="missing-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=True)],
            id="boolean-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=0)],
            id="zero-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=3)],
            id="after-session-past-lesson-count",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(concepts=["svm"], after_session=1)],
            id="after-session-before-concept-floor",
        ),
    ],
)
def test_unit_manifest_rejects_malformed_or_closure_invalid_session_contracts(
    tmp_path, concept_sessions, practice
):
    _write_session_manifest(
        tmp_path,
        concept_sessions=concept_sessions,
        practice=practice,
    )

    with pytest.raises(ValueError):
        load_unit_manifests(tmp_path)


BOOK2_UNIT = "B2-019-attention-transformers"
BOOK2_CONCEPTS = [
    "matrix-transpose",
    "query-key-value-attention",
    "scaled-dot-product-attention",
    "attention-mask",
    "causal-self-attention",
    "multi-head-attention",
    "sinusoidal-positional-encoding",
    "attention-complexity",
    "transformer-residual-layernorm",
    "position-wise-feed-forward",
    "transformer-block",
]
BOOK2_UNIT_PREREQS = [
    "C6-pytorch",
    "C7-cnn-transfer",
    "C8-embeddings",
    "C11-neural-training",
]
BOOK2_CONCEPT_PREREQS = [
    "softmax",
    "matrix-multiplication",
    "broadcasting",
    "variance",
    "torch-tensors",
    "nn-module",
    "torch-optimizers",
    "autograd-training",
]
BOOK2_CLAIMS = [
    "attention-mechanism-foundations",
    "self-attention",
    "multi-head-attention",
    "positional-encoding",
    "attention-complexity-analysis",
    "attention-from-scratch",
    "transformer-architecture-foundations",
]
BOOK2_CLAIM_ROWS = [
    (
        "attention-mechanism-foundations",
        1,
        ["theory", "derivation", "implementation"],
        ["query-key-value-attention", "scaled-dot-product-attention"],
    ),
    (
        "self-attention",
        2,
        ["theory", "derivation", "implementation"],
        ["scaled-dot-product-attention", "causal-self-attention", "attention-mask"],
    ),
    (
        "multi-head-attention",
        3,
        ["theory", "derivation", "implementation"],
        ["multi-head-attention"],
    ),
    (
        "positional-encoding",
        3,
        ["theory", "implementation"],
        ["sinusoidal-positional-encoding"],
    ),
    (
        "attention-complexity-analysis",
        3,
        ["theory", "derivation"],
        ["attention-complexity"],
    ),
    (
        "attention-from-scratch",
        4,
        ["theory", "implementation", "model-training"],
        ["scaled-dot-product-attention", "causal-self-attention"],
    ),
    (
        "transformer-architecture-foundations",
        5,
        ["theory", "derivation", "implementation"],
        [
            "transformer-block",
            "transformer-residual-layernorm",
            "position-wise-feed-forward",
        ],
    ),
]


def _write_book2_model_fixture(root: Path) -> None:
    root.joinpath("syllabus.md").write_text(
        "# Fixture\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(
            {
                "baseline": {"math": ["arithmetic"]},
                "clusters": ["fixture"],
                "concepts": [
                    {"id": concept, "cluster": "fixture"}
                    for concept in [*BOOK2_CONCEPT_PREREQS, *BOOK2_CONCEPTS]
                ],
                "units": [
                    {
                        "id": BOOK2_UNIT,
                        "track": "extension",
                        "title": "Attention and Transformer Mechanics",
                        "book": 2,
                        "layer": "round-2-extension",
                        "round": 2,
                        "prereqs": BOOK2_UNIT_PREREQS,
                        "concept_prerequisites": BOOK2_CONCEPT_PREREQS,
                        "teaches": BOOK2_CONCEPTS,
                    }
                ],
            },
            sort_keys=False,
        )
        + "```\n"
    )
    unit_dir = root / "units" / BOOK2_UNIT
    unit_dir.mkdir(parents=True)
    claims = [
        {
            "knowledge_point": point,
            "first_session": session,
            "modalities": modalities,
            "evidence_concepts": evidence_concepts,
            "evidence_by_modality": {},
        }
        for point, session, modalities, evidence_concepts in BOOK2_CLAIM_ROWS
    ]
    manifest = {
        "unit": BOOK2_UNIT,
        "book": 2,
        "layer": "round-2-extension",
        "round": 2,
        "track": "extension",
        "concepts_taught": BOOK2_CONCEPTS,
        "concepts_used": BOOK2_CONCEPT_PREREQS,
        "concept_prerequisites": BOOK2_CONCEPT_PREREQS,
        "prereq_units": BOOK2_UNIT_PREREQS,
        "bridge_diagnostic": {
            "path": "lessons/00-book1-bridge.ipynb",
            "minutes": 30,
            "referenced_concepts": BOOK2_CONCEPT_PREREQS,
        },
        "estimated_minutes": {
            "lesson_sessions": [90, 90, 90, 90, 90],
            "practice": 60,
            "review": 60,
        },
        "coverage_claims": claims,
        "practice": [
            {
                "id": "B2-019-p01",
                "concepts": BOOK2_CONCEPTS,
                "path": "practice/p01.ipynb",
                "solution_path": "practice/p01_solution.ipynb",
                "minutes": 60,
                "compute": {"policy": "cpu", "seed": 20260808},
            }
        ],
    }
    unit_dir.joinpath("manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False)
    )


def test_model_defaults_existing_book1_records_without_collapsing_the_two_dags(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("syllabus.md").write_text(
        """<!-- syllabus-canonical -->
```yaml
baseline: {math: [arithmetic]}
clusters: [fixture]
concepts: [{id: prior-concept, cluster: fixture}, {id: owned-concept, cluster: fixture}]
units:
  - id: C1-book1
    track: core
    title: Book 1
    prereqs: []
    concept_prerequisites: [prior-concept]
    teaches: [owned-concept]
```
"""
    )
    unit_dir = tmp_path / "units" / "C1-book1"
    unit_dir.mkdir(parents=True)
    unit_dir.joinpath("manifest.yaml").write_text(
        """unit: C1-book1
concepts_taught: [owned-concept]
concepts_used: [prior-concept]
prereq_units: []
practice:
  - id: C1-p01
    concepts: [owned-concept]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )

    unit = load_syllabus(tmp_path).units["C1-book1"]
    manifest = load_unit_manifests(tmp_path)[0]

    assert (unit.book, unit.round, unit.layer) == (1, 1, "round-1-core")
    assert unit.prereqs == []
    assert unit.concept_prerequisites == ["prior-concept"]
    assert (manifest.book, manifest.round, manifest.layer, manifest.track) == (
        1,
        1,
        "round-1-core",
        "core",
    )
    assert manifest.prereq_units == []
    assert manifest.concept_prerequisites == ["prior-concept"]
    assert manifest.practice[0].compute.policy == "cpu"


def test_model_parses_the_exact_explicit_book2_contract(tmp_path: Path) -> None:
    _write_book2_model_fixture(tmp_path)

    unit = load_syllabus(tmp_path).units[BOOK2_UNIT]
    manifest = load_unit_manifests(tmp_path)[0]

    assert (unit.book, unit.round, unit.layer, unit.track) == (
        2,
        2,
        "round-2-extension",
        "extension",
    )
    assert unit.prereqs == BOOK2_UNIT_PREREQS
    assert unit.concept_prerequisites == BOOK2_CONCEPT_PREREQS
    assert unit.teaches == BOOK2_CONCEPTS
    assert (manifest.book, manifest.round, manifest.layer, manifest.track) == (
        2,
        2,
        "round-2-extension",
        "extension",
    )
    assert manifest.prereq_units == BOOK2_UNIT_PREREQS
    assert manifest.concept_prerequisites == BOOK2_CONCEPT_PREREQS
    assert manifest.concepts_taught == BOOK2_CONCEPTS
    assert manifest.bridge_diagnostic.minutes == 30
    assert manifest.bridge_diagnostic.path == "lessons/00-book1-bridge.ipynb"
    assert [
        (
            claim.knowledge_point,
            claim.first_session,
            claim.modalities,
            claim.evidence_concepts,
        )
        for claim in manifest.coverage_claims
    ] == BOOK2_CLAIM_ROWS
    assert manifest.practice[0].compute.policy == "cpu"
    assert manifest.practice[0].compute.seed == 20260808


def test_prereq_checker_rejects_book1_concept_prerequisite_drift(tmp_path: Path) -> None:
    tmp_path.joinpath("syllabus.md").write_text(
        """<!-- syllabus-canonical -->
```yaml
baseline: {math: [prior-concept]}
clusters: [fixture]
concepts: [{id: owned-concept, cluster: fixture}]
units:
  - id: C1-book1
    track: core
    title: Book 1
    prereqs: []
    concept_prerequisites: [prior-concept]
    teaches: [owned-concept]
```
"""
    )
    unit_dir = tmp_path / "units" / "C1-book1"
    unit_dir.mkdir(parents=True)
    unit_dir.joinpath("manifest.yaml").write_text(
        """unit: C1-book1
concepts_taught: [owned-concept]
concepts_used: [prior-concept]
concept_prerequisites: []
prereq_units: []
practice: []
"""
    )

    report = check_prereq(tmp_path)

    assert not report.ok
    assert any("concept_prerequisites drift from syllabus" in error for error in report.errors)


def _write_selected_book_model_fixture(repo: Path) -> object:
    (repo / "books.yaml").write_text(
        yaml.safe_dump(
            {
                "books_version": 1,
                "books": [
                    {"id": "book1", "number": 1, "root": "book1", "depends_on": []}
                ],
            },
            sort_keys=False,
        )
    )
    book_root = repo / "book1"
    book_root.mkdir()
    book_root.joinpath("syllabus.md").write_text(
        """<!-- syllabus-canonical -->
```yaml
baseline: {math: [arithmetic]}
clusters: [fixture]
concepts: [{id: owned, cluster: fixture}]
units:
  - id: C1-book1
    track: core
    title: Book 1
    prereqs: []
    teaches: [owned]
```
"""
    )
    unit = book_root / "units" / "C1-book1"
    unit.mkdir(parents=True)
    unit.joinpath("manifest.yaml").write_text(
        """unit: C1-book1
concepts_taught: [owned]
concepts_used: []
prereq_units: []
practice: []
"""
    )
    return _books_module().load_book_catalog(repo).by_id("book1")


def test_model_loaders_receive_the_selected_bookspec_root(tmp_path: Path) -> None:
    book = _write_selected_book_model_fixture(tmp_path)

    assert set(load_syllabus(book.root).units) == {"C1-book1"}
    assert [manifest.unit_id for manifest in load_unit_manifests(book.root)] == [
        "C1-book1"
    ]
    with pytest.raises((FileNotFoundError, ValueError)):
        load_syllabus(tmp_path)


@pytest.mark.parametrize("loader", [load_syllabus_contract, load_syllabus])
def test_syllabus_loaders_reject_post_catalog_root_symlink_swap(
    tmp_path: Path, loader
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    book = _write_selected_book_model_fixture(repo)
    external = tmp_path / "external-book1"
    book.root.rename(external)
    book.root.symlink_to(external, target_is_directory=True)

    with pytest.raises(ValueError, match="content root is symlinked or noncanonical"):
        loader(book.root)


def test_mock_loader_uses_authoritative_book_number_not_directory_basename(
    tmp_path: Path,
) -> None:
    book = _write_selected_book_model_fixture(tmp_path)
    wrong_round = book.root / "mocktests" / "r2-001"
    wrong_round.mkdir(parents=True)
    wrong_round.joinpath("manifest.yaml").write_text(
        """test: r2-001
blueprint_version: 1
generated: null
status: draft
generation_parameters: {}
duration_minutes: 1
total_points: 0
time_budget: {min: 0, max: 0}
problems: []
"""
    )

    with pytest.raises(ValueError, match="book 1.*r1-|r2-001.*book 1"):
        load_mock_manifests(book.root, book_number=book.number)


def test_mock_loader_rejects_symlinked_manifest_directory_outside_book_root(
    tmp_path: Path,
) -> None:
    book_root = tmp_path / "selected"
    mocktests = book_root / "mocktests"
    mocktests.mkdir(parents=True)
    external = tmp_path / "external" / "r2-001"
    external.mkdir(parents=True)
    external.joinpath("manifest.yaml").write_text(
        """test: r2-001
status: draft
problems: []
""",
        encoding="utf-8",
    )
    (mocktests / "r2-001").symlink_to(external, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink|outside selected book root"):
        load_mock_manifests(book_root, book_number=2)
