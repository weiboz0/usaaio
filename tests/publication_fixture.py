"""A fixture publication book for the publisher and audit tests (Plan 030)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def write_notebook(path: Path, cells: list[tuple[str, str]], *, output: str | None = None) -> None:
    raw_cells = []
    for kind, source in cells:
        cell: dict[str, object] = {"cell_type": kind, "metadata": {}, "source": source}
        if kind == "code":
            cell["execution_count"] = 1 if output else None
            cell["outputs"] = (
                [{"output_type": "stream", "name": "stdout", "text": output}] if output else []
            )
        raw_cells.append(cell)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cells": raw_cells, "metadata": {}, "nbformat": 4,
                                "nbformat_minor": 5}), encoding="utf-8")


LESSON_DETAILS = (
    "## Checkpoint 1\n\nWhat is 2 + 2?\n\n"
    "<details><summary><b>Checkpoint 1</b></summary>\n\nDETAILSBODY four\n\n</details>\n"
)
OPEN_ANSWERS = "## Collected answers\n\nOPENANSWER the answer is seven\n"


def fixture_book(tmp_path: Path, *, selector: object = None, volumes: object = None) -> Path:
    repo = tmp_path / "repo"
    book = repo / "book1"
    write_yaml(repo / "books.yaml", {"books_version": 1, "books": [{
        "id": "book1", "number": 1, "root": "book1", "depends_on": [],
        "title": "Fixture Book", "subtitle": "Round 1: Fixtures", "publication": True}]})
    # Unit U1: lesson with a <details> block, a session notebook with an open answer section
    # and a planted output, a review, one Set A and one Set B practice.
    u1 = book / "units" / "U1-alpha"
    write_yaml(u1 / "manifest.yaml", {
        "unit": "U1-alpha", "concepts_taught": ["alpha-idea"], "concepts_used": [],
        "practice": [
            {"id": "U1-p01", "set": "A", "path": "practice/p01.ipynb",
             "solution_path": "practice/p01_solution.ipynb"},
            {"id": "U1-p02", "set": "B", "path": "practice/p02.ipynb",
             "solution_path": "practice/p02_solution.ipynb"},
        ]})
    write_notebook(u1 / "lesson.ipynb", [("markdown", "# U1-alpha — Alpha (Unit Overview)\n\nOVERVIEW text.\n\n"
                                           + LESSON_DETAILS)])
    write_notebook(u1 / "lessons" / "01-first.ipynb", [
        ("markdown", "# U1-alpha — Session 01: First Steps\n\nLESSONPROSE about $x$.\n"),
        ("code", "print('LESSONCODE')"),
        ("markdown", OPEN_ANSWERS),
        ("code", "ANSWERCODE = 7"),
        ("markdown", "## Next topic\n\nAFTERSECTION prose.\n"),
        ("markdown", ("**Checkpoint 2.** What is PARAQUESTION?\n\n"
                      "**Collected answers.** PARAANSWER is nine,\nas computed.\n\n"
                      "**Answer C.** WORKEDANSWER stays printed.\n")),
    ], output="PLANTEDOUTPUT\n")
    write_notebook(u1 / "review.ipynb", [("markdown", "# U1-alpha — Review\n\nREVIEWTEXT\n")])
    write_notebook(u1 / "practice" / "p01.ipynb", [
        ("markdown", "# U1-alpha — Practice p01\n\nSTATEMENT1 compute it.\n"),
        ("code", "STARTER1 = ...")])
    write_notebook(u1 / "practice" / "p01_solution.ipynb", [
        ("markdown", "# U1-alpha — Practice p01 — Solution\n"),
        ("code", "SOLUTION1 = 42")])
    write_notebook(u1 / "practice" / "p02.ipynb", [
        ("markdown", "# U1-alpha — Practice p02\n\nSTATEMENT2 prove it.\n"),
        ("code", "STARTER2 = ...")])
    write_notebook(u1 / "practice" / "p02_solution.ipynb", [
        ("markdown", "# U1-alpha — Practice p02 — Solution\n\nSOLUTIONPROSE2\n"),
        ("code", "return_42 = 42")])
    # Unit U2: lesson only plus one Set C practice.
    u2 = book / "units" / "U2-beta"
    write_yaml(u2 / "manifest.yaml", {
        "unit": "U2-beta", "concepts_taught": ["beta-idea"], "concepts_used": ["alpha-idea"],
        "practice": [{"id": "U2-p01", "set": "C", "path": "practice/p01.ipynb",
                      "solution_path": "practice/p01_solution.ipynb"}]})
    write_notebook(u2 / "lesson.ipynb", [("markdown", "# U2-beta — Beta (Unit Overview)\n\nBETATEXT\n")])
    write_notebook(u2 / "practice" / "p01.ipynb", [("markdown", "# U2-beta — Practice p01\n\nSTATEMENTU2\n")])
    write_notebook(u2 / "practice" / "p01_solution.ipynb", [("markdown", "# U2-beta — Practice p01 — Solution\n\nSOLUTIONU2\n")])
    # Mock test with the interleaved r2-001 layout and a repeated file reference.
    mock = book / "mocktests" / "r1-001"
    write_yaml(mock / "manifest.yaml", {"test": "r1-001", "problems": [
        {"id": "r1-001-p01-1", "files": ["theory/p01.md"]},
        {"id": "r1-001-p01-2", "files": ["problems/p01.ipynb"]},
        {"id": "r1-001-p01-3", "files": ["theory/p01.md"]},
        {"id": "r1-001-p02", "files": ["problems/p02.ipynb"]},
    ]})
    (mock / "theory").mkdir(parents=True)
    (mock / "solutions").mkdir(parents=True)
    (mock / "test.md").write_text("---\ntest: r1-001\n---\n\n# Mock r1-001\n\nMOCKINTRO\n")
    (mock / "theory" / "p01.md").write_text("# Problem 1.\n\nMOCKTHEORY1\n")
    write_notebook(mock / "problems" / "p01.ipynb", [("markdown", "# Problem 1 (code)\n\nMOCKPROBLEM1\n")])
    write_notebook(mock / "problems" / "p02.ipynb", [("markdown", "# Problem 2\n\nMOCKPROBLEM2\n")])
    (mock / "solutions" / "answers.md").write_text("# Answers\n\nMOCKANSWERS\n")
    (mock / "rubric.md").write_text("# Rubric\n\nMOCKRUBRIC\n")
    write_notebook(mock / "solutions" / "p01_solution.ipynb", [("markdown", "# Sol 1\n\nMOCKSOL1\n")])
    write_notebook(mock / "solutions" / "p02_solution.ipynb", [("markdown", "# Sol 2\n\nMOCKSOL2\n")])
    # Front and back matter.
    front = book / "front-matter"
    front.mkdir(parents=True)
    for name in ("preface", "how-to-use", "for-teachers", "answer-key-intro"):
        (front / f"{name}.md").write_text(
            f"# {name}\n\nFRONT {name}.\n\n<!-- edition: teacher -->\nTEACHERONLYLINE\n"
            "<!-- /edition -->\n")
    back = book / "back-matter"
    back.mkdir(parents=True)
    (back / "notation.md").write_text("# Notation\n\nNOTATIONTEXT $\\eta$\n")
    (back / "glossary.md").write_text(
        "# Glossary\n\n**Alpha idea** — The first idea. *(U1)*\n<!-- concept: alpha-idea -->\n\n"
        "**Beta idea** — The second idea. *(U2)*\n<!-- concept: beta-idea -->\n")
    config: dict[str, object] = {
        "publication_version": 1,
        "student_answers": selector if selector is not None else {"set": "A"},
        "chapters": [{"unit": "U1-alpha", "title": "Alpha Unit"},
                     {"unit": "U2-beta", "title": "Beta Unit"}],
        "mocktests": ["r1-001"],
        "audit": {"page_warning": 1200},
    }
    if volumes is not None:
        config["volumes"] = volumes
    write_yaml(book / "publication.yaml", config)
    return repo
