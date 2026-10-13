from __future__ import annotations

import dataclasses
import importlib
import json
import os
import shutil
import subprocess
import sys
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

    inventory_sentinel = book1 / "units" / "01-F1-scientific-python" / f"{TEMP_BOOK1_SENTINEL}.ipynb"
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
    # Plan 030 D4: the paper's sources are the manifest's item files, so the sentinel joins the
    # first problem's file list (first occurrence in manifest order).
    manifest_path = book1 / "mocktests" / "r1-001" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["problems"][0]["files"] = [
        f"theory/{TEMP_BOOK1_SENTINEL}.md", *manifest["problems"][0]["files"]
    ]
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


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


def test_book1_pdf_inputs_follow_noncanonical_registered_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / "book1", repo / "round1", ignore=shutil.ignore_patterns("build"))
    (repo / "books.yaml").write_text(
        "books_version: 1\n"
        "books:\n"
        "  - {id: book1, number: 1, root: round1, depends_on: []}\n",
        encoding="utf-8",
    )
    script = ROOT / "scripts" / "build-pdf.sh"

    proc = subprocess.run(
        [
            "bash",
            str(script),
            "--root",
            str(repo),
            "--book",
            "book1",
            "--list-inputs",
        ],
        cwd=repo,
        env={**os.environ, "USAAIO_PYTHON": sys.executable},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    inputs = proc.stdout.splitlines()
    assert all(path.startswith("round1/") for path in inputs)
    paper = [
        path for path in inputs
        if path.startswith("round1/mocktests/r1-001/")
        and "/solutions/" not in path and not path.endswith("rubric.md")
    ]
    assert len(paper) == 10
    assert "round1/docs/course-structure.md" in inputs
    assert "round1/units/08-C3-gradient-descent/practice/p01.ipynb" in inputs
    assert not any(path.endswith("_solution.ipynb") and "/units/" in path for path in inputs)


def test_fetch_reference_follows_noncanonical_registered_book1_root(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    paper = repo / "round1" / "reference" / "r1-2026" / "paper.pdf"
    paper.parent.mkdir(parents=True)
    paper.write_bytes(b"%PDF-1.4 fixture\n%%EOF\n")
    (repo / "books.yaml").write_text(
        "books_version: 1\n"
        "books:\n"
        "  - {id: book1, number: 1, root: round1, depends_on: []}\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "fetch-bin"
    fake_file = bin_dir / "file"
    fake_file.parent.mkdir()
    fake_file.write_text(
        "#!/usr/bin/env bash\nprintf 'PDF document, fixture\\n'\n",
        encoding="utf-8",
    )
    fake_file.chmod(0o755)
    script = ROOT / "scripts" / "fetch-reference.sh"

    proc = subprocess.run(
        ["bash", str(script), "--root", str(repo), "--book", "book1"],
        cwd=repo,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "USAAIO_PYTHON": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert f"exists: {paper}" in proc.stdout
    assert not (repo / "book1").exists()


def _write_fake_lualatex(bin_dir: Path) -> None:
    """A stand-in lualatex: writes <stem>.pdf and <stem>.log in the working directory."""
    lualatex = bin_dir / "lualatex"
    lualatex.parent.mkdir(parents=True)
    lualatex.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
tex=${@: -1}
stem=${tex%.tex}
printf 'This is a fake LuaHBTeX log\\n' > "$stem.log"
case ${FAKE_LUALATEX_MODE:-pass} in
  glyph) printf 'Missing character: There is no X (U+2192) in font Fake!\\n' >> "$stem.log" ;;
  fail) exit 1 ;;
esac
if [[ ${FAKE_LUALATEX_MODE:-pass} == zero && $stem == B2-019-attention-transformers ]]; then
  : > "$stem.pdf"
elif [[ ${FAKE_LUALATEX_MODE:-pass} == omit && $stem == B2-019-attention-transformers ]]; then
  rm -f "$stem.pdf"
else
  printf '%%PDF-1.4 fixture\\n%%%%EOF\\n' > "$stem.pdf"
fi
""",
        encoding="utf-8",
    )
    lualatex.chmod(0o755)


def _notebook_json(text: str) -> str:
    return json.dumps({
        "cells": [{"cell_type": "markdown", "metadata": {}, "source": text}],
        "metadata": {}, "nbformat": 4, "nbformat_minor": 5,
    })


def _live_noncanonical_book2_pdf_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    book = repo / "advanced"
    unit = book / "units" / "B2-019-attention-transformers"
    for relative in (
        "lesson.ipynb",
        "lessons/01-attention.ipynb",
        "review.ipynb",
        "practice/p01.ipynb",
        "practice/p01_solution.ipynb",
    ):
        path = unit / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_notebook_json(f"# {relative}\n\nText of {relative}.\n"), encoding="utf-8")
    (unit / "manifest.yaml").write_text(
        "unit: B2-019-attention-transformers\nbook: 2\nstatus: live\n",
        encoding="utf-8",
    )
    (repo / "books.yaml").write_text(
        "books_version: 1\n"
        "books:\n"
        "  - {id: book2, number: 2, root: advanced, depends_on: []}\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    _write_fake_lualatex(bin_dir)
    return repo, bin_dir


def _run_fixture_pdf_build(repo: Path, bin_dir: Path, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / "scripts" / "build-pdf.sh"), "--root", str(repo), "--book", "book2"],
        cwd=repo,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "FAKE_LUALATEX_MODE": mode,
            "USAAIO_PYTHON": sys.executable,
        },
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("mode", "expected_fragment"),
    [
        pytest.param("pass", "rendered 1 PDF(s)", id="one-handout"),
        pytest.param("omit", "missing PDF output", id="omitted-output"),
        pytest.param("zero", "zero-byte PDF output", id="zero-byte-output"),
        pytest.param("glyph", "Missing character", id="missing-glyph-log"),
        pytest.param("fail", "lualatex failed", id="render-error"),
    ],
)
def test_book2_pdf_build_uses_registered_root_and_owns_its_output_files(
    tmp_path: Path, mode: str, expected_fragment: str
) -> None:
    repo, bin_dir = _live_noncanonical_book2_pdf_fixture(tmp_path)
    proc = _run_fixture_pdf_build(repo, bin_dir, mode)
    output = proc.stdout + proc.stderr

    if mode == "pass":
        assert proc.returncode == 0, output
        handout = repo / "output" / "book2" / "handouts" / "B2-019-attention-transformers.pdf"
        assert handout.read_bytes().startswith(b"%PDF")
        build = repo / "advanced" / "build" / "pdf" / "handouts"
        # The handout is the practice statement only, through the shared converter, and the
        # LaTeX log is kept next to the PDF.
        markdown = (build / "B2-019-attention-transformers.md").read_text(encoding="utf-8")
        assert "Text of practice/p01.ipynb." in markdown
        assert "p01_solution" not in markdown and "lessons/01-attention" not in markdown
        assert (build / "B2-019-attention-transformers.log").is_file()
        assert not any(path.name == ".gitignore" for path in (repo / "advanced").rglob("*"))
    else:
        assert proc.returncode == 1, output
    assert expected_fragment in output


def test_pdf_build_refreshes_only_its_own_output_files(tmp_path: Path) -> None:
    repo, bin_dir = _live_noncanonical_book2_pdf_fixture(tmp_path)
    target = repo / "output" / "book2"
    (target / "handouts").mkdir(parents=True)
    stale = target / "handouts" / "B2-000-removed.pdf"
    stale.write_bytes(b"%PDF stale")
    edition = target / "book2-student.pdf"
    edition.write_bytes(b"%PDF edition")
    proc = _run_fixture_pdf_build(repo, bin_dir, "pass")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not stale.exists()
    assert edition.read_bytes() == b"%PDF edition"


def test_pdf_build_skips_with_exit_3_without_lualatex(tmp_path: Path) -> None:
    repo, _ = _live_noncanonical_book2_pdf_fixture(tmp_path)
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    for tool in ("bash", "env", "dirname", "pwd"):
        located = shutil.which(tool)
        if located:
            (empty_bin / tool).symlink_to(located)
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "build-pdf.sh"), "--root", str(repo), "--book", "book2"],
        cwd=repo,
        env={**os.environ, "PATH": str(empty_bin), "HOME": str(tmp_path),
             "USAAIO_PYTHON": sys.executable},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "SKIP build-pdf" in proc.stderr


def test_book2_pdf_rejects_student_source_symlink_outside_registered_root(
    tmp_path: Path,
) -> None:
    repo, _ = _live_noncanonical_book2_pdf_fixture(tmp_path)
    source = repo / "advanced/units/B2-019-attention-transformers/practice/p01.ipynb"
    outside = tmp_path / "outside.ipynb"
    outside.write_text("{}\n", encoding="utf-8")
    source.unlink()
    source.symlink_to(outside)

    proc = subprocess.run(
        [
            "bash", str(ROOT / "scripts/build-pdf.sh"), "--root", str(repo),
            "--book", "book2", "--list-inputs",
        ],
        cwd=repo,
        env={**os.environ, "USAAIO_PYTHON": sys.executable},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "symlink component is forbidden" in proc.stdout + proc.stderr


def test_fetch_reference_rejects_symlinked_reference_destination(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    book = repo / "round1"
    book.mkdir(parents=True)
    outside = tmp_path / "outside-reference"
    outside.mkdir()
    (book / "reference").symlink_to(outside, target_is_directory=True)
    (repo / "books.yaml").write_text(
        "books_version: 1\nbooks:\n"
        "  - {id: book1, number: 1, root: round1, depends_on: []}\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            "bash", str(ROOT / "scripts/fetch-reference.sh"), "--root", str(repo),
            "--book", "book1",
        ],
        cwd=repo,
        env={**os.environ, "USAAIO_PYTHON": sys.executable},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "symlink component is forbidden" in proc.stdout + proc.stderr
    assert list(outside.iterdir()) == []
