"""Plan 030 Task 5 and Plan 033: the publication audit (tools/publish_audit.py), rules 1-7, on a\nfixture book."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from publication_fixture import fixture_book, write_yaml

from tools.publish import build_all
from tools.publish_audit import audit


def _render_stub(projects) -> None:
    """Stand in for the LaTeX render: a clean draft-mode log and a page count per project."""
    for project in projects:
        (project.path / f"{project.output_stem}.log").write_text("clean log\n", encoding="utf-8")
        (project.path / "latex-audit.log").write_text("clean log\n", encoding="utf-8")
        tex = "\\begin{document}\n"
        if project.index:
            tex += "\\printindex\n"
            (project.path / f"{project.output_stem}.ind").write_text(
                "\\begin{theindex}\n\\end{theindex}\n", encoding="utf-8")
        (project.path / f"{project.output_stem}.tex").write_text(tex, encoding="utf-8")
        (project.path / "pages.txt").write_text("12\n", encoding="utf-8")


@pytest.fixture
def built(tmp_path: Path) -> Path:
    repo = fixture_book(tmp_path)
    rubric = repo / "book1/mocktests/r1-001/rubric.md"
    rubric.write_text(rubric.read_text() + "\nAward full marks only when the derivation names the stationary point.\n")
    _render_stub(build_all(repo, "book1"))
    return repo


def _errors(repo: Path, **kwargs) -> list[str]:
    return audit(repo, "book1", **kwargs).errors


def _project(repo: Path, name: str, folder: str = "publish") -> Path:
    return repo / "book1" / "build" / folder / name


def _append_segment(project: Path, chapter: str, segment: dict) -> None:
    """Plant a block that the sidecar declares (a forged provenance entry)."""
    sidecar = project / "provenance" / f"{chapter}.json"
    raw = json.loads(sidecar.read_text())
    raw["segments"].append(segment)
    sidecar.write_text(json.dumps(raw))
    qmd = project / f"{chapter}.qmd"
    qmd.write_text(qmd.read_text() + segment["sep"] + segment["text"] + "\n")


def _strip_final_newline_join(project: Path, chapter: str) -> None:
    """Rewrite the chapter so it equals the sidecar concatenation (after planting)."""
    raw = json.loads((project / "provenance" / f"{chapter}.json").read_text())
    text = "".join(seg["sep"] + seg["text"] for seg in raw["segments"]).lstrip("\n") + "\n"
    (project / f"{chapter}.qmd").write_text(text)


def test_clean_full_build_passes(built: Path) -> None:
    result = audit(built, "book1")
    assert result.errors == []
    assert any("student-print: 12 pages" in line for line in result.info)


def test_clean_full_build_passes_with_teaching_order_prefixed_folders(tmp_path: Path) -> None:
    """Plan 031: unit folders are `NN-<id>`; chapters, titles and practice paths use ids."""
    repo = fixture_book(tmp_path, prefixed=True)
    assert (repo / "book1" / "units" / "01-U1-alpha").is_dir()
    rubric = repo / "book1/mocktests/r1-001/rubric.md"
    rubric.write_text(rubric.read_text() + "\nAward full marks only when the derivation names the stationary point.\n")
    _render_stub(build_all(repo, "book1"))
    result = audit(repo, "book1")
    assert result.errors == []
    print_qmd = (_project(repo, "student-print") / "U1-alpha.qmd").read_text()
    assert "`units/01-U1-alpha/practice/p01.ipynb`" in print_qmd


def test_planted_solution_chapter_in_a_student_edition(built: Path) -> None:
    project = _project(built, "student-print")
    key = _project(built, "answer-key")
    (project / "answers-U1-alpha.qmd").write_text((key / "answers-U1-alpha.qmd").read_text())
    (project / "provenance" / "answers-U1-alpha.json").write_text(
        (key / "provenance" / "answers-U1-alpha.json").read_text())
    quarto = yaml.safe_load((project / "_quarto.yml").read_text())
    quarto["book"]["chapters"].insert(3, "answers-U1-alpha.qmd")
    (project / "_quarto.yml").write_text(yaml.safe_dump(quarto))
    errors = _errors(built)
    assert any("student-print: chapters" in error for error in errors)
    assert any("answers-U1-alpha.qmd" in error and "not allowed" in error for error in errors)


def test_undeclared_solution_code_in_a_student_unit_chapter(built: Path) -> None:
    project = _project(built, "student-print")
    qmd = project / "U1-alpha.qmd"
    qmd.write_text(qmd.read_text() + "\n```python\nreturn_42 = 42\n```\n")  # a short leak
    errors = _errors(built)
    assert any("U1-alpha.qmd: chapter text is not the concatenation" in error for error in errors)


def test_forged_sidecar_entry_declaring_a_solution_block(built: Path) -> None:
    project = _project(built, "student")
    _append_segment(project, "U1-alpha", {
        "kind": "code", "sep": "\n\n", "source": "units/U1-alpha/practice/p02_solution.ipynb",
        "cell": 1, "span": [0, 14], "text": "```python\nreturn_42 = 42\n```", "transform": "fence"})
    _strip_final_newline_join(project, "U1-alpha")
    errors = _errors(built)
    assert any("U1-alpha.qmd" in error and "p02_solution.ipynb is not allowed" in error
               for error in errors)


def test_forged_sidecar_labelling_a_details_body_as_markdown(built: Path) -> None:
    lesson = json.loads((built / "book1/units/U1-alpha/lesson.ipynb").read_text())
    source = lesson["cells"][0]["source"]
    start = source.index("DETAILSBODY")
    end = start + len("DETAILSBODY four")
    project = _project(built, "student-print")
    _append_segment(project, "U1-alpha", {
        "kind": "markdown", "sep": "\n\n", "source": "units/U1-alpha/lesson.ipynb", "cell": 0,
        "span": [start, end], "text": "DETAILSBODY four", "shift": 1})
    _strip_final_newline_join(project, "U1-alpha")
    errors = _errors(built)
    assert any("overlaps an answer body" in error for error in errors)


def test_short_details_body_leak_is_caught(built: Path) -> None:
    project = _project(built, "student")
    qmd = project / "U1-alpha.qmd"
    qmd.write_text(qmd.read_text() + "\nfour\n")  # a one-word <details> answer
    assert any("U1-alpha.qmd: chapter text is not the concatenation" in error
               for error in _errors(built))


def test_open_answer_section_body_declared_in_print_is_rejected(built: Path) -> None:
    project = _project(built, "student-print")
    notebook = json.loads((built / "book1/units/U1-alpha/lessons/01-first.ipynb").read_text())
    cell = notebook["cells"][2]["source"]
    start = cell.index("OPENANSWER")
    _append_segment(project, "U1-alpha", {
        "kind": "answer-body", "sep": "\n\n", "source": "units/U1-alpha/lessons/01-first.ipynb",
        "cell": 2, "span": [start, len(cell.rstrip())], "text": cell[start:].rstrip(), "shift": 4})
    _strip_final_newline_join(project, "U1-alpha")
    assert any("answer-body block" in error and "not allowed" in error
               for error in _errors(built))


def test_planted_rubric_line_is_fingerprinted(built: Path) -> None:
    project = _project(built, "student")
    qmd = project / "U2-beta.qmd"
    line = "Award full marks only when the derivation names the stationary point."
    _append_segment(project, "U2-beta", {"kind": "scaffold", "sep": "\n\n", "text": line})
    _strip_final_newline_join(project, "U2-beta")
    errors = _errors(built)
    assert any("U2-beta.qmd: fingerprint of mock material" in error for error in errors)
    assert any("scaffold text is not a fixed publisher pattern" in error for error in errors)
    assert qmd.is_file()


def test_planted_details_body_line_is_fingerprinted(tmp_path: Path) -> None:
    repo = fixture_book(tmp_path)
    lesson = repo / "book1/units/U1-alpha/lesson.ipynb"
    raw = json.loads(lesson.read_text())
    long_answer = "The derivative vanishes at the stationary point, so x equals three."
    raw["cells"][0]["source"] = raw["cells"][0]["source"].replace("DETAILSBODY four", long_answer)
    lesson.write_text(json.dumps(raw))
    _render_stub(build_all(repo, "book1"))
    project = _project(repo, "student-print")
    qmd = project / "U2-beta.qmd"
    qmd.write_text(qmd.read_text() + long_answer + "\n")
    errors = _errors(repo)
    assert any("U2-beta.qmd: fingerprint of details material" in error for error in errors)


def test_scope_json_disagreeing_with_the_invocation(built: Path) -> None:
    project = _project(built, "teacher")
    scope = json.loads((project / "scope.json").read_text())
    scope["mode"] = "scoped"
    (project / "scope.json").write_text(json.dumps(scope))
    assert any("teacher: scope.json scoped" in error and "disagrees" in error
               for error in _errors(built))


def test_missing_character_in_any_latex_log(built: Path) -> None:
    project = _project(built, "answer-key")
    (project / "latex-audit.log").write_text(
        "Missing character: There is no ⧵ (U+29F5) in font latinmodern-math!\n")
    assert any("answer-key/latex-audit.log: Missing character" in error
               for error in _errors(built))


def test_missing_character_in_a_build_pdf_log(built: Path) -> None:
    log = built / "book1/build/pdf/handouts/U1-alpha.log"
    log.parent.mkdir(parents=True)
    log.write_text("Missing character: There is no → (U+2192) in font Atkinson!\n")
    assert any("handouts/U1-alpha.log: Missing character" in error for error in _errors(built))


def test_undefined_reference_in_draft_log(built: Path) -> None:
    log = _project(built, "student") / "book1-student.log"
    log.write_text("LaTeX Warning: Reference `ans-U1-p01' on page 3 undefined on input line 9.\n")
    assert any("undefined" in error for error in _errors(built))


def test_full_build_missing_a_live_unit(built: Path) -> None:
    project = _project(built, "teacher")
    quarto = yaml.safe_load((project / "_quarto.yml").read_text())
    quarto["book"]["chapters"].remove("U2-beta.qmd")
    (project / "_quarto.yml").write_text(yaml.safe_dump(quarto))
    assert any("teacher: chapters" in error for error in _errors(built))


def test_scoped_check_and_a_scoped_project_missing_a_requested_unit(tmp_path: Path) -> None:
    repo = fixture_book(tmp_path)
    _render_stub(build_all(repo, "book1", units=["U2-beta"], mocktests=[]))
    assert audit(repo, "book1", units=["U2-beta"], mocktests=[]).errors == []
    errors = audit(repo, "book1", units=["U1-alpha", "U2-beta"], mocktests=[]).errors
    assert any("disagrees" in error for error in errors)
    assert any("student-print: chapters" in error and "U1-alpha.qmd" in error for error in errors)


def test_mock_only_scoped_check(tmp_path: Path) -> None:
    repo = fixture_book(tmp_path)
    _render_stub(build_all(repo, "book1", units=[], mocktests=["r1-001"]))
    assert audit(repo, "book1", units=[], mocktests=["r1-001"]).errors == []
    chapters = yaml.safe_load(
        (_project(repo, "teacher", "publish-check") / "_quarto.yml").read_text())
    assert "mock-r1-001.qmd" in str(chapters)


def test_mock_material_in_a_student_inventory(built: Path) -> None:
    project = _project(built, "student")
    inventory = json.loads((project / "inventory.json").read_text())
    inventory["chapters"][2]["sources"].append("mocktests/r1-001/rubric.md")
    (project / "inventory.json").write_text(json.dumps(inventory))
    assert any("student edition lists mock-test material" in error for error in _errors(built))


def test_glossary_rules(built: Path) -> None:
    glossary = built / "book1/back-matter/glossary.md"
    glossary.write_text(
        "# Glossary\n\n**Alpha idea** — The first idea. *(U1)*\n<!-- concept: alpha-idea -->\n\n"
        "**Loose term** — No concept note.\n")
    errors = _errors(built, glossary_only=True)
    assert any("misses introduced concept(s) ['beta-idea']" in error for error in errors)
    assert any("glossary entry without" in error for error in errors)
    # A scoped check limits rule 5 to the in-scope units' concepts.
    scoped = audit(built, "book1", units=["U1-alpha"], glossary_only=True).errors
    assert not any("misses" in error for error in scoped)


def test_page_count_warning(tmp_path: Path) -> None:
    repo = fixture_book(tmp_path)
    config = yaml.safe_load((repo / "book1/publication.yaml").read_text())
    config["audit"]["page_warning"] = 10
    write_yaml(repo / "book1/publication.yaml", config)
    _render_stub(build_all(repo, "book1"))
    result = audit(repo, "book1")
    assert result.errors == []
    assert any("12 pages is over 10" in warning for warning in result.warnings)


def test_inline_answer_paragraph_planted_as_plain_markdown(built: Path) -> None:
    notebook = json.loads((built / "book1/units/U1-alpha/lessons/01-first.ipynb").read_text())
    cell = notebook["cells"][5]["source"]
    start = cell.index("**Collected answers.**")
    end = cell.index("\n\n**Answer C.**")
    project = _project(built, "student-print")
    _append_segment(project, "U1-alpha", {
        "kind": "markdown", "sep": "\n\n", "source": "units/U1-alpha/lessons/01-first.ipynb",
        "cell": 5, "span": [start, end], "text": cell[start:end], "shift": 1})
    _strip_final_newline_join(project, "U1-alpha")
    errors = _errors(built)
    assert any("overlaps an answer body" in error for error in errors)
    assert any("printed answer lead-in" in error for error in errors)


def test_answer_lead_in_safety_net(built: Path) -> None:
    project = _project(built, "student")
    _append_segment(project, "U2-beta", {
        "kind": "scaffold", "sep": "\n\n", "text": "Collected checkpoint answers: x = 2"})
    _strip_final_newline_join(project, "U2-beta")
    assert any("U2-beta.qmd: printed answer lead-in" in error for error in _errors(built))


def test_publisher_command_printed_as_text_and_missing_index(built: Path) -> None:
    project = _project(built, "student-print")
    (project / "book1-student-print.tex").write_text("\\textbackslash{}printindex\n")
    errors = _errors(built)
    assert any("publisher command printed as text" in error for error in errors)
    assert any("index edition has no \\printindex" in error for error in errors)
    (project / "book1-student-print.ind").unlink()
    assert any("has no Index chapter" in error for error in _errors(built))


# --- rule 7: overfull boxes (Plan 033 D3) --------------------------------------------------------


def _set_overfull_max(repo: Path, value: object) -> None:
    config = yaml.safe_load((repo / "book1/publication.yaml").read_text())
    if value is None:
        config["audit"].pop("overfull_max_pt", None)
    else:
        config["audit"]["overfull_max_pt"] = value
    write_yaml(repo / "book1/publication.yaml", config)


def _plant_overfull(project: Path, widths: list[float]) -> None:
    """A final draft-mode log with overfull boxes at TeX lines 3, 4, ...; and a kept .tex whose
    chapter starts at line 2."""
    stem = next(project.glob("*.tex")).stem
    (project / f"{stem}.tex").write_text(
        "\\begin{document}\n\\chapter*{Planted {Chapter} Title}\\label{ch-x}\n"
        + "text\n" * len(widths) + "\\printindex\n", encoding="utf-8")
    (project / "latex-audit.log").write_text("".join(
        f"Overfull \\hbox ({width}pt too wide) in paragraph at lines {3 + i}--{3 + i}\n"
        f"\\TU/FiraMono(2)/m/n/10 something\n" for i, width in enumerate(widths)))


def test_overfull_boxes_under_the_threshold_pass_and_are_reported(built: Path) -> None:
    _set_overfull_max(built, 5)
    _plant_overfull(_project(built, "student"), [1.5, 4.9, 3.25])
    result = audit(built, "book1")
    assert result.errors == []
    assert ("student: 3 overfull \\hbox (2 over 2 pt), widest 4.9 pt at book1-student.tex:4 "
            "(chapter 'Planted {Chapter} Title')") in result.info
    assert "teacher: 0 overfull \\hbox" in result.info


def test_overfull_box_over_the_threshold_fails_with_the_widest_box(built: Path) -> None:
    _set_overfull_max(built, 5)
    _plant_overfull(_project(built, "teacher"), [6.0, 51.48883, 2.0])
    errors = _errors(built)
    assert ("teacher: 2 overfull \\hbox over audit.overfull_max_pt 5 pt; widest 51.4888 pt at "
            "book1-teacher.tex:4 (chapter 'Planted {Chapter} Title')") in errors


def test_overfull_box_detected_in_a_read_file_is_measured(built: Path) -> None:
    _set_overfull_max(built, 5)
    project = _project(built, "teacher")
    (project / "latex-audit.log").write_text(
        "(./book1-teacher.toc\nOverfull \\hbox (5.61996pt too wide) detected at line 950\n")
    assert any("teacher: 1 overfull" in error and "line 950 of a file book1-teacher.tex reads"
               in error for error in _errors(built))


def test_missing_overfull_key_reports_only(built: Path) -> None:
    _set_overfull_max(built, None)
    _plant_overfull(_project(built, "teacher"), [60.0])
    result = audit(built, "book1")
    assert result.errors == []
    assert any(line.startswith("teacher: 1 overfull \\hbox (1 over 2 pt), widest 60 pt")
               for line in result.info)


def test_rendered_edition_without_latex_audit_log_fails(built: Path) -> None:
    (_project(built, "answer-key") / "latex-audit.log").unlink()
    assert any("answer-key: latex-audit.log missing" in error for error in _errors(built))


def test_planted_overfull_box_in_a_build_pdf_log_fails(built: Path) -> None:
    _set_overfull_max(built, 5)
    log = built / "book1/build/pdf/handouts/U1-alpha.log"
    log.parent.mkdir(parents=True)
    log.write_text("Overfull \\hbox (6pt too wide) in paragraph at lines 12--14\n")
    errors = _errors(built)
    assert any(error.startswith("build/pdf/handouts/U1-alpha.log: 1 overfull \\hbox over "
                                "audit.overfull_max_pt 5 pt; widest 6 pt") for error in errors)
    log.write_text("Overfull \\hbox (4pt too wide) in paragraph at lines 12--14\n")
    assert _errors(built) == []
