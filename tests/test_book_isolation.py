from __future__ import annotations

import dataclasses
import importlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools import audit_curriculum, render_course_structure
from tools.checks.answerkey import check_answerkey
from tools.checks.schedule import load_validated_schedule
from tools.model import load_syllabus

ROOT = Path(__file__).parents[1]
TEMP_BOOK1_SENTINEL = "TEMP_BOOK1_ONLY"
TEMP_BOOK2_COLLISION = "TEMP_BOOK2_COLLISION"


def _books_module():
    try:
        return importlib.import_module("tools.books")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.books":
            raise
        pytest.fail("tools.books is the missing Plan 019 registry producer")


def _write_registry(repo: Path, *, include_book2: bool) -> None:
    books: list[dict[str, Any]] = [{"id": "book1", "number": 1, "root": "book1", "depends_on": []}]
    if include_book2:
        books.append({"id": "book2", "number": 2, "root": "book2", "depends_on": ["book1"]})
    (repo / "books.yaml").write_text(
        yaml.safe_dump({"books_version": 1, "books": books}, sort_keys=False),
        encoding="utf-8",
    )


def _copy_book(repo: Path, book_id: str) -> None:
    source = ROOT / book_id
    assert source.is_dir(), f"{book_id}/ is the missing migrated root"
    shutil.copytree(source, repo / book_id, ignore=shutil.ignore_patterns("build"))


def _pdf_inputs(repo: Path, book_id: str) -> bytes:
    script = ROOT / "scripts" / "build-pdf.sh"
    proc = subprocess.run(
        ["bash", str(script), "--root", str(repo), "--book", book_id, "--list-inputs"],
        cwd=repo,
        env={**os.environ, "LC_ALL": "C"},
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout.decode() + proc.stderr.decode()
    return proc.stdout


def _book1_fingerprint(repo: Path) -> dict[str, bytes]:
    books = _books_module()
    catalog = books.load_book_catalog(repo)
    book1 = catalog.by_id("book1")
    assert books.validate_book_root(book1) == []
    syllabus = load_syllabus(book1.root)
    schedule = load_validated_schedule(book1.root)
    inventory = audit_curriculum.build_inventory(book1.root)
    renderer = render_course_structure.render_document(book1.root)
    answer_key = check_answerkey(book1.root)
    return {
        "syllabus": json.dumps(
            dataclasses.asdict(syllabus), sort_keys=True, default=sorted
        ).encode(),
        "schedule": repr(schedule).encode(),
        "inventory": audit_curriculum.render_inventory(inventory).encode(),
        "renderer": renderer.encode(),
        "answer-key": json.dumps(
            {"ok": answer_key.ok, "errors": answer_key.errors}, sort_keys=True
        ).encode(),
        "pdf-inputs": _pdf_inputs(repo, "book1"),
    }


def _seed_book1_temp_root_inputs(repo: Path) -> None:
    book1 = repo / "book1"
    syllabus_path = book1 / "syllabus.md"
    syllabus_text = syllabus_path.read_text(encoding="utf-8")
    mutated_syllabus = syllabus_text.replace(
        "title: Scientific Python and NumPy",
        f"title: Scientific Python and NumPy {TEMP_BOOK1_SENTINEL}",
        1,
    )
    assert mutated_syllabus != syllabus_text
    syllabus_path.write_text(
        mutated_syllabus,
        encoding="utf-8",
    )

    schedule_path = book1 / "curriculum" / "course-schedule.yaml"
    schedule = yaml.safe_load(schedule_path.read_text(encoding="utf-8"))
    practices = [
        allocation
        for week in schedule["weeks"]
        for allocation in week["allocations"]
        if allocation["kind"] == "practice" and allocation.get("unit") == "F1-scientific-python"
    ]
    practices[0]["minutes"] += 1
    practices[1]["minutes"] -= 1
    schedule_path.write_text(yaml.safe_dump(schedule, sort_keys=False), encoding="utf-8")

    inventory_sentinel = book1 / "units" / "F1-scientific-python" / f"{TEMP_BOOK1_SENTINEL}.ipynb"
    inventory_sentinel.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "metadata": {}, "source": [TEMP_BOOK1_SENTINEL]}
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )

    structure = book1 / "docs" / "course-structure.md"
    structure.write_text(
        structure.read_text(encoding="utf-8") + f"\n{TEMP_BOOK1_SENTINEL}\n",
        encoding="utf-8",
    )
    answers = book1 / "mocktests" / "r1-001" / "solutions" / "answers.md"
    answers.write_text(
        answers.read_text(encoding="utf-8").replace(
            "- r1-001-p01-1: answer: C",
            f"- r1-001-p01-1: answer: {TEMP_BOOK1_SENTINEL}",
            1,
        ),
        encoding="utf-8",
    )
    pdf_sentinel = book1 / "mocktests" / "r1-001" / "theory" / f"{TEMP_BOOK1_SENTINEL}.md"
    pdf_sentinel.parent.mkdir(exist_ok=True)
    pdf_sentinel.write_text(TEMP_BOOK1_SENTINEL + "\n", encoding="utf-8")


def _seed_book2_collision(repo: Path) -> None:
    collision = repo / "book2" / "mocktests" / "r1-001" / "theory" / f"{TEMP_BOOK1_SENTINEL}.md"
    collision.parent.mkdir(parents=True, exist_ok=True)
    collision.write_text(TEMP_BOOK2_COLLISION + "\n", encoding="utf-8")


def test_book1_results_are_byte_identical_after_valid_book2_fixture(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _copy_book(repo, "book1")
    _write_registry(repo, include_book2=False)
    _seed_book1_temp_root_inputs(repo)
    before = _book1_fingerprint(repo)

    _copy_book(repo, "book2")
    _seed_book2_collision(repo)
    _write_registry(repo, include_book2=True)
    after = _book1_fingerprint(repo)

    assert after == before
    assert TEMP_BOOK1_SENTINEL.encode() in before["pdf-inputs"]
    assert TEMP_BOOK2_COLLISION.encode() not in before["pdf-inputs"]
    assert str(ROOT).encode() not in before["pdf-inputs"]


def test_every_fingerprint_facet_rejects_module_global_root_fallback(tmp_path: Path) -> None:
    selected_repo = tmp_path / "selected"
    fallback_repo = tmp_path / "global-fallback"
    selected_repo.mkdir()
    fallback_repo.mkdir()
    for repo in (selected_repo, fallback_repo):
        _copy_book(repo, "book1")
        _write_registry(repo, include_book2=False)
    _seed_book1_temp_root_inputs(selected_repo)

    selected = _book1_fingerprint(selected_repo)
    global_fallback = _book1_fingerprint(fallback_repo)

    assert set(selected) == set(global_fallback)
    assert all(selected[facet] != global_fallback[facet] for facet in selected), {
        facet: selected[facet] == global_fallback[facet] for facet in selected
    }


def test_each_registered_book_has_an_independent_complete_root() -> None:
    catalog = _books_module().load_book_catalog(ROOT)
    required = {
        "syllabus.md",
        "curriculum/course-schedule.yaml",
        "curriculum/coverage-map.yaml",
        "curriculum/material-inventory.yaml",
        "curriculum/official-topics.yaml",
        "curriculum/source-manifest.yaml",
        "units",
        "mocktests/blueprint.yaml",
        "reference",
        "docs/course-structure.md",
    }
    for book in catalog.books:
        assert _books_module().validate_book_root(book) == []
        assert all((book.root / relative).exists() for relative in required)
        assert book.root.parent == catalog.repo_root
