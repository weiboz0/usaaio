"""Plan 030 Task 3: the edition publisher (tools/publish.py) on a fixture book."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tools import publish
from tools.publish import (
    EDITIONS,
    PublishError,
    build,
    build_all,
    filter_edition_blocks,
    mock_paper_sources,
    mock_solution_sources,
    output_stem,
    parse_details,
)
from tools.publish_output import refresh_output


def _yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _nb(path: Path, cells: list[tuple[str, str]], *, output: str | None = None) -> None:
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


def _fixture(tmp_path: Path, *, selector: object = None, volumes: object = None) -> Path:
    repo = tmp_path / "repo"
    book = repo / "book1"
    _yaml(repo / "books.yaml", {"books_version": 1, "books": [{
        "id": "book1", "number": 1, "root": "book1", "depends_on": [],
        "title": "Fixture Book", "subtitle": "Round 1: Fixtures", "publication": True}]})
    # Unit U1: lesson with a <details> block, a session notebook with an open answer section
    # and a planted output, a review, one Set A and one Set B practice.
    u1 = book / "units" / "U1-alpha"
    _yaml(u1 / "manifest.yaml", {
        "unit": "U1-alpha", "concepts_taught": ["alpha-idea"], "concepts_used": [],
        "practice": [
            {"id": "U1-p01", "set": "A", "path": "practice/p01.ipynb",
             "solution_path": "practice/p01_solution.ipynb"},
            {"id": "U1-p02", "set": "B", "path": "practice/p02.ipynb",
             "solution_path": "practice/p02_solution.ipynb"},
        ]})
    _nb(u1 / "lesson.ipynb", [("markdown", "# U1-alpha — Alpha (Unit Overview)\n\nOVERVIEW text.\n\n"
                                           + LESSON_DETAILS)])
    _nb(u1 / "lessons" / "01-first.ipynb", [
        ("markdown", "# U1-alpha — Session 01: First Steps\n\nLESSONPROSE about $x$.\n"),
        ("code", "print('LESSONCODE')"),
        ("markdown", OPEN_ANSWERS),
        ("code", "ANSWERCODE = 7"),
        ("markdown", "## Next topic\n\nAFTERSECTION prose.\n"),
    ], output="PLANTEDOUTPUT\n")
    _nb(u1 / "review.ipynb", [("markdown", "# U1-alpha — Review\n\nREVIEWTEXT\n")])
    _nb(u1 / "practice" / "p01.ipynb", [
        ("markdown", "# U1-alpha — Practice p01\n\nSTATEMENT1 compute it.\n"),
        ("code", "STARTER1 = ...")])
    _nb(u1 / "practice" / "p01_solution.ipynb", [
        ("markdown", "# U1-alpha — Practice p01 — Solution\n"),
        ("code", "SOLUTION1 = 42")])
    _nb(u1 / "practice" / "p02.ipynb", [
        ("markdown", "# U1-alpha — Practice p02\n\nSTATEMENT2 prove it.\n"),
        ("code", "STARTER2 = ...")])
    _nb(u1 / "practice" / "p02_solution.ipynb", [
        ("markdown", "# U1-alpha — Practice p02 — Solution\n\nSOLUTIONPROSE2\n"),
        ("code", "return_42 = 42")])
    # Unit U2: lesson only plus one Set C practice.
    u2 = book / "units" / "U2-beta"
    _yaml(u2 / "manifest.yaml", {
        "unit": "U2-beta", "concepts_taught": ["beta-idea"], "concepts_used": ["alpha-idea"],
        "practice": [{"id": "U2-p01", "set": "C", "path": "practice/p01.ipynb",
                      "solution_path": "practice/p01_solution.ipynb"}]})
    _nb(u2 / "lesson.ipynb", [("markdown", "# U2-beta — Beta (Unit Overview)\n\nBETATEXT\n")])
    _nb(u2 / "practice" / "p01.ipynb", [("markdown", "# U2-beta — Practice p01\n\nSTATEMENTU2\n")])
    _nb(u2 / "practice" / "p01_solution.ipynb", [("markdown", "# U2-beta — Practice p01 — Solution\n\nSOLUTIONU2\n")])
    # Mock test with the interleaved r2-001 layout and a repeated file reference.
    mock = book / "mocktests" / "r1-001"
    _yaml(mock / "manifest.yaml", {"test": "r1-001", "problems": [
        {"id": "r1-001-p01-1", "files": ["theory/p01.md"]},
        {"id": "r1-001-p01-2", "files": ["problems/p01.ipynb"]},
        {"id": "r1-001-p01-3", "files": ["theory/p01.md"]},
        {"id": "r1-001-p02", "files": ["problems/p02.ipynb"]},
    ]})
    (mock / "theory").mkdir(parents=True)
    (mock / "solutions").mkdir(parents=True)
    (mock / "test.md").write_text("---\ntest: r1-001\n---\n\n# Mock r1-001\n\nMOCKINTRO\n")
    (mock / "theory" / "p01.md").write_text("# Problem 1.\n\nMOCKTHEORY1\n")
    _nb(mock / "problems" / "p01.ipynb", [("markdown", "# Problem 1 (code)\n\nMOCKPROBLEM1\n")])
    _nb(mock / "problems" / "p02.ipynb", [("markdown", "# Problem 2\n\nMOCKPROBLEM2\n")])
    (mock / "solutions" / "answers.md").write_text("# Answers\n\nMOCKANSWERS\n")
    (mock / "rubric.md").write_text("# Rubric\n\nMOCKRUBRIC\n")
    _nb(mock / "solutions" / "p01_solution.ipynb", [("markdown", "# Sol 1\n\nMOCKSOL1\n")])
    _nb(mock / "solutions" / "p02_solution.ipynb", [("markdown", "# Sol 2\n\nMOCKSOL2\n")])
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
    _yaml(book / "publication.yaml", config)
    return repo


def _project_text(project: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(project.glob("*.qmd")))


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _fixture(tmp_path)


# --- edition markers (ported from py4kids' tests) ------------------------------------------


def test_edition_markers_keep_shared_and_selected_text() -> None:
    text = "A\n<!-- edition: teacher -->\nT\n<!-- /edition -->\nB\n"
    assert filter_edition_blocks(text, "teacher") == "A\nT\nB\n"
    assert filter_edition_blocks(text, "student") == "A\nB\n"


def test_edition_markers_accept_several_names_and_collapse_blank_lines() -> None:
    text = "A\n\n<!-- edition: student|student-print -->\nS\n<!-- /edition -->\n\nB\n"
    assert filter_edition_blocks(text, "student-print") == "A\n\nS\n\nB\n"
    assert filter_edition_blocks(text, "teacher") == "A\n\nB\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("<!-- edition: deluxe -->\nX\n<!-- /edition -->\n", "unknown edition deluxe"),
        ("<!-- edition: teacher -->\n<!-- edition: student -->\n", "opened inside line 1"),
        ("X\n<!-- /edition -->\n", "closed but never opened"),
        ("<!-- edition: teacher -->\nX\n", "never closed"),
        ("<!-- edition teacher -->\n", "malformed edition marker"),
    ],
)
def test_edition_marker_errors_fail(text: str, message: str) -> None:
    with pytest.raises(PublishError, match=message):
        filter_edition_blocks(text, "teacher", "front-matter/x.md")


def test_output_stem_names() -> None:
    assert output_stem("book1", "student-print") == "book1-student-print"
    assert output_stem("book1", "teacher", 3) == "book1-teacher-vol3"
    assert set(EDITIONS) == {"student-print", "student", "answer-key", "teacher"}


# --- chapter lists -------------------------------------------------------------------------


def _chapters(project: Path) -> list[str]:
    inventory = json.loads((project / "inventory.json").read_text())
    return [chapter["file"] for chapter in inventory["chapters"]]


def test_each_edition_chapter_list(repo: Path) -> None:
    lists = {edition: _chapters(build(repo, "book1", edition).path) for edition in EDITIONS}
    assert lists["student-print"] == [
        "index.qmd", "how-to-use.qmd", "U1-alpha.qmd", "U2-beta.qmd",
        "notation.qmd", "glossary.qmd", "the-index.qmd"]
    assert lists["student"] == [
        "index.qmd", "how-to-use.qmd", "U1-alpha.qmd", "U2-beta.qmd", "answers.qmd",
        "notation.qmd", "glossary.qmd", "the-index.qmd"]
    # U2 has no selected (Set A) practice, so it has no Answer Key chapter.
    assert lists["answer-key"] == ["index.qmd", "answers-U1-alpha.qmd"]
    assert lists["teacher"] == [
        "index.qmd", "how-to-use.qmd", "for-teachers.qmd", "U1-alpha.qmd", "U2-beta.qmd",
        "mock-r1-001.qmd", "notation.qmd", "glossary.qmd", "the-index.qmd"]
    quarto = (repo / "book1/build/publish/teacher/_quarto.yml").read_text()
    assert '- part: "Mock Tests"' in quarto
    assert "TEACHERONLYLINE" in (repo / "book1/build/publish/teacher/index.qmd").read_text()
    assert "TEACHERONLYLINE" not in (repo / "book1/build/publish/student/index.qmd").read_text()


def test_outputs_are_stripped_and_code_kept(repo: Path) -> None:
    for edition in EDITIONS:
        assert "PLANTEDOUTPUT" not in _project_text(build(repo, "book1", edition).path)
    assert "print('LESSONCODE')" in _project_text(build(repo, "book1", "student").path)


def test_print_practice_is_markdown_only_with_file_pointer(repo: Path) -> None:
    print_text = (build(repo, "book1", "student-print").path / "U1-alpha.qmd").read_text()
    full_text = (build(repo, "book1", "student").path / "U1-alpha.qmd").read_text()
    assert "STATEMENT1" in print_text and "STARTER1" not in print_text
    assert "*Practice file:* `units/U1-alpha/practice/p01.ipynb`" in print_text
    assert "STARTER1" in full_text and "Practice file:" not in full_text
    # Lesson code is still printed in the print edition.
    assert "LESSONCODE" in print_text


def test_student_answers_selector(repo: Path, tmp_path: Path) -> None:
    student = build(repo, "book1", "student").path
    appendix = (student / "answers.qmd").read_text()
    assert "SOLUTION1 = 42" in appendix
    assert "return_42" not in appendix and "SOLUTIONU2" not in appendix
    unit = (student / "U1-alpha.qmd").read_text()
    assert "*Answer: see page \\pageref{ans-U1-p01}.*" in unit
    assert "ans-U1-p02" not in unit
    for edition in ("student-print", "student", "answer-key"):
        text = _project_text(build(repo, "book1", edition).path)
        assert "return_42" not in text and "SOLUTIONPROSE2" not in text
    key = _project_text(build(repo, "book1", "answer-key").path)
    assert "SOLUTION1 = 42" in key and "STATEMENT1" not in key

    wider = _fixture(tmp_path / "wide", selector={"set": ["A", "B"]})
    key = _project_text(build(wider, "book1", "answer-key").path)
    assert "SOLUTION1 = 42" in key and "return_42 = 42" in key and "SOLUTIONU2" not in key


def test_teacher_prints_every_solution(repo: Path) -> None:
    text = (build(repo, "book1", "teacher").path / "U1-alpha.qmd").read_text()
    for marker in ("SOLUTION1 = 42", "return_42 = 42", "SOLUTIONPROSE2"):
        assert marker in text
    assert "SOLUTIONU2" in (build(repo, "book1", "teacher").path / "U2-beta.qmd").read_text()


# --- <details> and open answer sections ------------------------------------------------------


def test_details_handling_per_edition(repo: Path) -> None:
    printed = (build(repo, "book1", "student-print").path / "U1-alpha.qmd").read_text()
    assert "DETAILSBODY" not in printed
    assert ("*Answers (Checkpoint 1): open this notebook, or see the Teacher's Edition.*"
            in printed)

    student = build(repo, "book1", "student").path
    unit = (student / "U1-alpha.qmd").read_text()
    label = "U1-alpha-lesson-d1"
    assert "DETAILSBODY" not in unit
    assert f"*Answers: Checkpoint 1 (page \\pageref{{{label}}}).*" in unit
    appendix = (student / "answers.qmd").read_text()
    assert f"### Unit Overview — Checkpoint 1 {{#{label}}}" in appendix
    assert "DETAILSBODY four" in appendix

    teacher = (build(repo, "book1", "teacher").path / "U1-alpha.qmd").read_text()
    assert "::: {.answers}\n\n**Checkpoint 1**\n\nDETAILSBODY four\n\n:::" in teacher
    assert "<details>" not in teacher and "<summary>" not in teacher


def test_open_answer_sections_are_handled_like_details(repo: Path) -> None:
    printed = (build(repo, "book1", "student-print").path / "U1-alpha.qmd").read_text()
    assert "OPENANSWER" not in printed and "ANSWERCODE" not in printed
    assert "### Collected answers\n\n*Answers: open this notebook" in printed
    assert "AFTERSECTION" in printed  # the next heading closes the section

    student = build(repo, "book1", "student").path
    unit = (student / "U1-alpha.qmd").read_text()
    assert "OPENANSWER" not in unit and "ANSWERCODE" not in unit
    assert "*Answers: page \\pageref{U1-alpha-01-first-d1}.*" in unit
    appendix = (student / "answers.qmd").read_text()
    assert "### Session 01: First Steps — Collected answers {#U1-alpha-01-first-d1}" in appendix
    assert "OPENANSWER the answer is seven" in appendix and "ANSWERCODE = 7" in appendix

    teacher = (build(repo, "book1", "teacher").path / "U1-alpha.qmd").read_text()
    assert "::: {.answers}\n\nOPENANSWER the answer is seven" in teacher
    assert "ANSWERCODE = 7" in teacher


def test_answer_heading_pattern() -> None:
    pattern = publish.ANSWER_HEADING
    for heading in ("## Checkpoint Answers", "### Checkpoint 3 answers", "## Self-quiz answers",
                    "## Collected checkpoint answers", "## Quiz answers",
                    "## Answers (open only when done)", "## Answers"):
        assert pattern.match(heading), heading
    for heading in ("## Answering questions", "## Checkpoint 3", "Answers"):
        assert not pattern.match(heading), heading


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("<details><summary>A</summary>\n\nbody\n", "unclosed <details>"),
        ("<details>\n<details>x</details>\n</details>\n", "nested <details>"),
        ("body\n</details>\n", "without an opening"),
    ],
)
def test_malformed_details_fail(text: str, message: str) -> None:
    with pytest.raises(PublishError, match=message):
        parse_details(text, "fixture")


def test_malformed_details_fails_the_build(repo: Path) -> None:
    _nb(repo / "book1/units/U2-beta/lesson.ipynb",
        [("markdown", "# U2-beta — Beta\n\n<details><summary>x</summary>\n\nopen\n")])
    with pytest.raises(PublishError, match="unclosed <details>"):
        build(repo, "book1", "student")


def test_details_inside_fenced_code_are_ignored() -> None:
    assert parse_details("```\n<details>\n```\n", "fixture") == []


# --- mock tests ---------------------------------------------------------------------------


def test_mock_paper_and_solution_order_first_occurrence(repo: Path) -> None:
    root = repo / "book1/mocktests/r1-001"
    assert [p.relative_to(root).as_posix() for p in mock_paper_sources(root)] == [
        "test.md", "theory/p01.md", "problems/p01.ipynb", "problems/p02.ipynb"]
    assert [p.relative_to(root).as_posix() for p in mock_solution_sources(root)] == [
        "solutions/answers.md", "rubric.md", "solutions/p01_solution.ipynb",
        "solutions/p02_solution.ipynb"]


def test_teacher_mock_part(repo: Path) -> None:
    text = (build(repo, "book1", "teacher").path / "mock-r1-001.qmd").read_text()
    order = ["MOCKINTRO", "MOCKTHEORY1", "MOCKPROBLEM1", "MOCKPROBLEM2", "MOCKANSWERS",
             "MOCKRUBRIC", "MOCKSOL1", "MOCKSOL2"]
    positions = [text.index(marker) for marker in order]
    assert positions == sorted(positions)
    assert text.count("MOCKTHEORY1") == 1
    assert "test: r1-001" not in text  # YAML front matter is not printed
    for edition in ("student-print", "student", "answer-key"):
        assert "MOCK" not in _project_text(build(repo, "book1", edition).path)


# --- index ---------------------------------------------------------------------------------


def test_index_entries_at_introducing_unit_and_in_glossary(repo: Path) -> None:
    project = build(repo, "book1", "student").path
    u1 = (project / "U1-alpha.qmd").read_text()
    u2 = (project / "U2-beta.qmd").read_text()
    assert "\\index{alpha idea@Alpha idea}" in u1 and "beta idea" not in u1
    assert "\\index{beta idea@Beta idea}" in u2
    glossary = (project / "glossary.qmd").read_text()
    assert "`\\index{alpha idea@Alpha idea}`{=latex}" in glossary
    assert (project / "the-index.qmd").is_file()
    key = build(repo, "book1", "answer-key").path
    assert "\\index" not in _project_text(key)


# --- provenance, scope and volumes ----------------------------------------------------------


def test_provenance_concatenates_to_each_chapter(repo: Path) -> None:
    for edition in EDITIONS:
        project = build(repo, "book1", edition).path
        for qmd in project.glob("*.qmd"):
            sidecar = json.loads((project / "provenance" / (qmd.stem + ".json")).read_text())
            joined = "".join(seg["sep"] + seg["text"] for seg in sidecar["segments"])
            assert joined.lstrip("\n") + "\n" == qmd.read_text()
            for seg in sidecar["segments"]:
                if seg["kind"] != "scaffold":
                    assert seg["source"] and len(seg["span"]) == 2
    student = build(repo, "book1", "student").path
    kinds = {seg["kind"] for seg in json.loads(
        (student / "provenance" / "answers.json").read_text())["segments"]}
    assert {"details-body", "answer-body", "answer-code", "code"} <= kinds
    printed = build(repo, "book1", "student-print").path
    kinds = {seg["kind"] for seg in json.loads(
        (printed / "provenance" / "U1-alpha.json").read_text())["segments"]}
    assert "details-body" not in kinds and "answer-body" not in kinds


def test_scoped_build_writes_publish_check_and_scope(repo: Path) -> None:
    project = build(repo, "book1", "teacher", units=["U2-beta"], mocktests=[])
    assert project.path == repo / "book1/build/publish-check/teacher"
    scope = json.loads((project.path / "scope.json").read_text())
    assert scope["mode"] == "scoped" and scope["units"] == ["U2-beta"] and scope["mocktests"] == []
    assert "U1-alpha.qmd" not in _chapters(project.path)

    mock_only = build(repo, "book1", "teacher", units=[], mocktests=["r1-001"])
    assert [f for f in _chapters(mock_only.path) if f.startswith(("U", "mock"))] == ["mock-r1-001.qmd"]
    student = build(repo, "book1", "student", units=[], mocktests=["r1-001"])
    assert "MOCK" not in _project_text(student.path)

    full = build(repo, "book1", "student")
    assert json.loads((full.path / "scope.json").read_text())["mode"] == "full"
    with pytest.raises(ValueError, match="not configured chapters"):
        build(repo, "book1", "student", units=["U9-ghost"])


def test_volumes_split_configured_editions(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, volumes={"editions": ["teacher"], "parts": [
        {"title": "First", "first": "U1-alpha", "last": "U1-alpha"},
        {"title": "Second", "first": "U2-beta", "last": "U2-beta"}]})
    projects = build_all(repo, "book1")
    names = [(p.edition, p.volume, p.output_stem) for p in projects]
    assert ("teacher", 1, "book1-teacher-vol1") in names
    assert ("teacher", 2, "book1-teacher-vol2") in names
    assert ("student", None, "book1-student") in names
    vol1 = _chapters(repo / "book1/build/publish/teacher-vol1")
    vol2 = _chapters(repo / "book1/build/publish/teacher-vol2")
    assert "U1-alpha.qmd" in vol1 and "U2-beta.qmd" not in vol1 and "mock-r1-001.qmd" not in vol1
    assert "U2-beta.qmd" in vol2 and "mock-r1-001.qmd" in vol2
    assert "Volume 2: Second" in (repo / "book1/build/publish/teacher-vol2/_quarto.yml").read_text()


def test_non_publication_book_is_refused(repo: Path) -> None:
    registry = yaml.safe_load((repo / "books.yaml").read_text())
    registry["books"][0]["publication"] = False
    _yaml(repo / "books.yaml", registry)
    with pytest.raises(ValueError, match="not a publication book"):
        build(repo, "book1", "student")


def test_math_spaces_inside_inline_dollars_are_trimmed() -> None:
    assert publish.normalize_math("$E[x] = $ the") == "$E[x] =$ the"
    assert publish.normalize_math("`$ a $` and $$ a $$") == "`$ a $` and $$ a $$"


# --- output folder ------------------------------------------------------------------------


def test_publish_output_owners(tmp_path: Path) -> None:
    built = tmp_path / "built"
    built.mkdir()
    pdf = built / "book1-student.pdf"
    pdf.write_bytes(b"%PDF")
    stale = tmp_path / "output/book1/book1-old.pdf"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"%PDF")
    keep = tmp_path / "output/book1/syllabus.pdf"
    keep.write_bytes(b"%PDF")
    refresh_output(tmp_path, "book1", "book", [pdf])
    assert not stale.exists() and keep.exists()
    assert (tmp_path / "output/book1/book1-student.pdf").exists()
    with pytest.raises(ValueError, match="build-book owns only"):
        refresh_output(tmp_path, "book1", "book", [keep])
