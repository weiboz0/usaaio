"""Plan 030 Task 1: registry publication keys and `<book>/publication.yaml` validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tools.books import (
    load_book_catalog,
    load_publication_config,
    output_pdf_name,
    publication_config_errors,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _registry(**extra: object) -> dict[str, object]:
    record: dict[str, object] = {"id": "book1", "number": 1, "root": "book1", "depends_on": []}
    record.update(extra)
    return {"books_version": 1, "books": [record]}


def _config(**overrides: object) -> dict[str, object]:
    config: dict[str, object] = {
        "publication_version": 1,
        "student_answers": {"set": "A"},
        "chapters": [
            {"unit": "U1-alpha", "title": "Alpha"},
            {
                "unit": "U2-beta",
                "title": "A Title That Is Certainly Longer Than Thirty-Two",
                "head": "Short Beta",
            },
        ],
        "mocktests": ["r1-001"],
        "audit": {"page_warning": 1200},
    }
    config.update(overrides)
    return config


def _repo(tmp_path: Path, config: dict[str, object] | None = None, **registry: object) -> Path:
    repo = tmp_path / "repo"
    book = repo / "book1"
    for unit in ("U1-alpha", "U2-beta"):
        _write_yaml(book / "units" / unit / "manifest.yaml", {"unit": unit})
    _write_yaml(book / "mocktests" / "r1-001" / "manifest.yaml", {"test": "r1-001"})
    entry = {"publication": True, "title": "Fixture Book", "subtitle": "A fixture"}
    entry.update(registry)
    _write_yaml(repo / "books.yaml", _registry(**entry))
    if config is not None:
        _write_yaml(book / "publication.yaml", config)
    return repo


def test_real_books_are_publication_books_with_valid_configs() -> None:
    catalog = load_book_catalog(ROOT)
    for book in catalog.books:
        assert book.publication is True
        assert book.title and book.subtitle
        assert publication_config_errors(ROOT, book.id) == []


def test_old_format_registry_without_publication_keys_stays_valid(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "book1").mkdir(parents=True)
    _write_yaml(repo / "books.yaml", _registry())
    book = load_book_catalog(repo).by_id("book1")
    assert (book.title, book.subtitle, book.publication) == ("", "", False)
    assert publication_config_errors(repo, "book1") == [
        "book1: not a publication book (books.yaml publication: true)"
    ]


def test_registry_rejects_unknown_key(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _config(), colour="blue")
    with pytest.raises(ValueError, match="unexpected=.*colour"):
        load_book_catalog(repo)


def test_registry_rejects_missing_required_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "book1").mkdir(parents=True)
    _write_yaml(
        repo / "books.yaml",
        {"books_version": 1, "books": [{"id": "book1", "number": 1, "root": "book1"}]},
    )
    with pytest.raises(ValueError, match="missing=\\[\"'depends_on'\"\\]"):
        load_book_catalog(repo)


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"title": ""}, "needs a nonempty title"),
        ({"subtitle": ""}, "needs a nonempty subtitle"),
        ({"publication": "yes"}, "publication must be a boolean"),
        ({"title": " Padded"}, "single-line string"),
    ],
)
def test_registry_publication_fields_are_validated(
    tmp_path: Path, extra: dict[str, object], message: str
) -> None:
    repo = _repo(tmp_path, _config(), **extra)
    with pytest.raises(ValueError, match=message):
        load_book_catalog(repo)


def test_valid_fixture_config_loads(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _config())
    assert publication_config_errors(repo, "book1") == []
    config = load_publication_config(load_book_catalog(repo).by_id("book1"))
    assert config.units == ("U1-alpha", "U2-beta")
    assert config.chapter("U1-alpha").head == "Alpha"
    assert config.chapter("U2-beta").head == "Short Beta"
    assert config.student_answers == {"set": ("A",)}
    assert config.mocktests == ("r1-001",)
    assert config.volumes == ()


def test_missing_config_is_an_error(tmp_path: Path) -> None:
    repo = _repo(tmp_path, None)
    assert publication_config_errors(repo, "book1") == [
        "book1/publication.yaml: missing (every publication book needs one; Plan 030 D1)"
    ]


def test_missing_and_unknown_config_keys(tmp_path: Path) -> None:
    config = _config(extra_key=1)
    del config["audit"]
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert "book1/publication.yaml: missing key(s) ['audit']" in errors
    assert "book1/publication.yaml: unknown key(s) ['extra_key']" in errors


def test_chapter_list_must_match_live_units(tmp_path: Path) -> None:
    config = _config(
        chapters=[
            {"unit": "U1-alpha", "title": "Alpha"},
            {"unit": "U9-ghost", "title": "Ghost"},
        ]
    )
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert "book1/publication.yaml: chapters omit live unit(s) ['U2-beta']" in errors
    assert "book1/publication.yaml: chapters list unit(s) that are not live ['U9-ghost']" in errors


def test_duplicate_chapter_unit_is_an_error(tmp_path: Path) -> None:
    chapters = _config()["chapters"]
    assert isinstance(chapters, list)
    config = _config(chapters=[*chapters, {"unit": "U1-alpha", "title": "Again"}])
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert any("duplicate unit U1-alpha" in error for error in errors)


def test_long_title_needs_a_running_head(tmp_path: Path) -> None:
    config = _config(
        chapters=[
            {"unit": "U1-alpha", "title": "Alpha"},
            {"unit": "U2-beta", "title": "A Title That Is Certainly Longer Than Thirty-Two"},
        ]
    )
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert any("needs a running head" in error and "U2-beta" in error for error in errors)


def test_running_head_itself_is_limited(tmp_path: Path) -> None:
    config = _config(
        chapters=[
            {"unit": "U1-alpha", "title": "Alpha"},
            {"unit": "U2-beta", "title": "Beta", "head": "x" * 33},
        ]
    )
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert any("head must be a single-line string of at most 32" in error for error in errors)


def test_listed_but_absent_mock_test_is_an_error(tmp_path: Path) -> None:
    config = _config(mocktests=["r1-001", "r1-002"])
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    expected = (
        "book1/publication.yaml: mock test r1-002 is listed but absent "
        "(mocktests/r1-002/manifest.yaml)"
    )
    assert errors == [expected]


def test_student_answer_selector_is_validated(tmp_path: Path) -> None:
    config = _config(student_answers={"set": ["A", "B"], "colour": "red"})
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert errors == ["book1/publication.yaml: student_answers has unknown key(s) ['colour']"]


@pytest.mark.parametrize("value", [5, 2.5, None])
def test_overfull_max_pt_accepts_a_positive_number_or_no_key(tmp_path: Path, value: object) -> None:
    """Plan 033 D3: a positive number sets the threshold; a missing key disables the check."""
    audit = {"page_warning": 1200} if value is None else {"page_warning": 1200, "overfull_max_pt": value}
    assert publication_config_errors(_repo(tmp_path, _config(audit=audit)), "book1") == []


@pytest.mark.parametrize("value", [0, -3, 0.0, "5", True, [5], float("nan")])
def test_overfull_max_pt_rejects_zero_negative_and_non_numeric(tmp_path: Path, value: object) -> None:
    config = _config(audit={"page_warning": 1200, "overfull_max_pt": value})
    errors = publication_config_errors(_repo(tmp_path, config), "book1")
    assert errors == ["book1/publication.yaml: audit.overfull_max_pt must be a positive number"]


def test_volumes_must_be_contiguous_and_cover_every_chapter(tmp_path: Path) -> None:
    good = _config(
        volumes={
            "editions": ["teacher"],
            "parts": [
                {"title": "One", "first": "U1-alpha", "last": "U1-alpha"},
                {"title": "Two", "first": "U2-beta", "last": "U2-beta"},
            ],
        }
    )
    repo = _repo(tmp_path, good)
    assert publication_config_errors(repo, "book1") == []
    config = load_publication_config(load_book_catalog(repo).by_id("book1"))
    assert [volume.units for volume in config.volumes] == [("U1-alpha",), ("U2-beta",)]
    assert config.volume_editions == ("teacher",)

    gap = _config(
        volumes={
            "editions": ["teacher"],
            "parts": [
                {"title": "One", "first": "U1-alpha", "last": "U1-alpha"},
                {"title": "Two", "first": "U1-alpha", "last": "U2-beta"},
            ],
        }
    )
    errors = publication_config_errors(_repo(tmp_path / "gap", gap), "book1")
    assert any("contiguous" in error for error in errors)

    bad_edition = _config(
        volumes={
            "editions": ["deluxe"],
            "parts": [
                {"title": "One", "first": "U1-alpha", "last": "U1-alpha"},
                {"title": "Two", "first": "U2-beta", "last": "U2-beta"},
            ],
        }
    )
    errors = publication_config_errors(_repo(tmp_path / "ed", bad_edition), "book1")
    assert any("volumes.editions" in error for error in errors)


def test_output_pdf_name() -> None:
    assert output_pdf_name("book1", "student") == "book1-student.pdf"
    assert output_pdf_name("book1", "teacher", 2) == "book1-teacher-vol2.pdf"
