from __future__ import annotations

from datetime import UTC, datetime

import pytest

import tools.checks.schedule
import tools.model

# The B2-020 deferred solution policy was live only through 2026-09-30.
# Tests that exercise the live-policy path pin every live-clock read on that
# path (manifest loading and the Book 2 schedule's policy check) inside the
# window so they stay meaningful after the policy expired.
DEFERRED_POLICY_WINDOW_NOW = datetime(2026, 9, 15, 12, tzinfo=UTC)


class _DeferredPolicyWindowDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return DEFERRED_POLICY_WINDOW_NOW.replace(tzinfo=None)
        return DEFERRED_POLICY_WINDOW_NOW.astimezone(tz)


@pytest.fixture
def deferred_policy_window(monkeypatch: pytest.MonkeyPatch) -> None:
    for module in (tools.model, tools.checks.schedule):
        monkeypatch.setattr(module, "datetime", _DeferredPolicyWindowDatetime)
