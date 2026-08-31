from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest


def test_explicit_historical_entry_point_accepts_only_an_iso_date(tmp_path: Path) -> None:
    from tools.verify_historical_deferred_policy import parse_iso_date

    assert parse_iso_date("2026-09-30") == date(2026, 9, 30)
    with pytest.raises(ValueError, match="ISO date"):
        parse_iso_date("30-09-2026")

