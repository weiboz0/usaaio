from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_explicit_historical_entry_point_accepts_only_an_iso_date(tmp_path: Path) -> None:
    from tools.verify_historical_deferred_policy import parse_iso_date

    assert parse_iso_date("2026-09-30") == date(2026, 9, 30)
    with pytest.raises(ValueError, match="ISO date"):
        parse_iso_date("30-09-2026")


def test_historical_script_uses_current_verifier_for_pre_verifier_archive() -> None:
    env = os.environ | {"PATH": f"/home/chris/.local/bin:{os.environ['PATH']}"}
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/verify-historical-deferred-policy.sh"),
            "47f50d1",
            "2026-09-30",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "PASS deferred-policy verification at 2026-09-30" in result.stdout
