from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


def _analysis() -> str:
    return """# Reference analysis

## Methodology

Derived topic labels only; raw papers stay local and ignored.

| Source | Round | Note |
|---|---|---|
| r1-2026 | R1 | first-round source |
| r2-2026 | R2 | second-round source |
| r1-2025 | R1 | older first-round source |

## Round 1 topic findings

Round 1-only findings.

## Round 2 shape and topics

Round 2 overview that must remain complete.

### Transformers

Round 2-only details.
"""


def _reference_repo(tmp_path: Path, *, unknown: bool = False) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / ".gitignore").write_text(
        "reference/r1-*/\nreference/r2-*/\nreference/cache/\n",
        encoding="utf-8",
    )
    reference = repo / "reference"
    reference.mkdir()
    (reference / ".gitkeep").write_text("", encoding="utf-8")
    (reference / "analysis.md").write_text(_analysis(), encoding="utf-8")
    (reference / "outlines-round1.md").write_text("# Round 1 outlines\n", encoding="utf-8")
    for relative, text in (
        ("r1-2026/raw.pdf", "ignored round 1 raw"),
        ("r2-2026/raw.pdf", "ignored round 2 raw"),
        ("cache/model.bin", "ignored shared cache"),
    ):
        path = reference / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if unknown:
        (reference / "surprise.txt").write_text("unknown\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "reference/.gitkeep", "reference/analysis.md")
    _git(repo, "add", "-f", "reference/outlines-round1.md")
    if unknown:
        _git(repo, "add", "reference/surprise.txt")
    _git(repo, "commit", "-m", "reference fixture")
    return repo


def _install_migrator(repo: Path) -> Path:
    source = ROOT / "scripts" / "migrate-reference-layout.sh"
    assert source.is_file(), "scripts/migrate-reference-layout.sh is the missing producer"
    target = repo / "scripts" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o755)
    return target


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    script = _install_migrator(repo)
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_reference_migration_dry_run_is_nonmutating_and_reports_both_books(
    tmp_path: Path,
) -> None:
    repo = _reference_repo(tmp_path)
    before = _git(repo, "status", "--porcelain", "--ignored").stdout

    proc = _run(repo, "--dry-run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _git(repo, "status", "--porcelain", "--ignored").stdout == before
    assert "book1/reference" in proc.stdout
    assert "book2/reference" in proc.stdout


def test_reference_migration_moves_mixed_tracked_and_ignored_corpus_idempotently(
    tmp_path: Path,
) -> None:
    repo = _reference_repo(tmp_path)

    first = _run(repo)

    assert first.returncode == 0, first.stdout + first.stderr
    assert not (repo / "reference").exists()
    assert (repo / "book1/reference/r1-2026/raw.pdf").read_text() == "ignored round 1 raw"
    assert (repo / "book2/reference/r2-2026/raw.pdf").read_text() == "ignored round 2 raw"
    assert (repo / "book1/reference/cache/model.bin").read_text() == "ignored shared cache"
    assert (repo / "book1/reference/outlines-round1.md").is_file()
    for relative in (
        "book1/reference/r1-2026/raw.pdf",
        "book2/reference/r2-2026/raw.pdf",
        "book1/reference/cache/model.bin",
    ):
        ignored = _git(repo, "check-ignore", relative, check=False)
        assert ignored.returncode == 0, relative
        assert relative not in _git(repo, "ls-files").stdout.splitlines()

    before_rerun = _git(repo, "status", "--porcelain", "--ignored").stdout
    second = _run(repo)
    assert second.returncode == 0, second.stdout + second.stderr
    assert _git(repo, "status", "--porcelain", "--ignored").stdout == before_rerun


def test_reference_migration_refuses_unknown_entries_without_partial_moves(
    tmp_path: Path,
) -> None:
    repo = _reference_repo(tmp_path, unknown=True)

    proc = _run(repo)

    assert proc.returncode != 0
    assert "surprise.txt" in proc.stdout + proc.stderr
    assert (repo / "reference/analysis.md").is_file()
    assert not (repo / "book1/reference").exists()
    assert not (repo / "book2/reference").exists()


def test_reference_analysis_is_split_semantically_at_the_round2_heading(
    tmp_path: Path,
) -> None:
    repo = _reference_repo(tmp_path)

    proc = _run(repo)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    book1 = (repo / "book1/reference/analysis.md").read_text(encoding="utf-8")
    book2 = (repo / "book2/reference/analysis.md").read_text(encoding="utf-8")
    assert "## Methodology" in book1 and "## Methodology" in book2
    assert "r1-2026" in book1 and "r1-2025" in book1
    assert "r2-2026" not in book1
    assert "## Round 1 topic findings" in book1
    assert "## Round 2 shape and topics" not in book1
    assert "r2-2026" in book2
    assert "r1-2026" not in book2 and "r1-2025" not in book2
    assert "## Round 1 topic findings" not in book2
    assert book2.endswith(
        "## Round 2 shape and topics\n\n"
        "Round 2 overview that must remain complete.\n\n"
        "### Transformers\n\nRound 2-only details.\n"
    )
