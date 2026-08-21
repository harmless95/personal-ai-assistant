from unittest.mock import Mock

import pytest

from app.tasks import deps
from app.tasks.components.providers import DaySummaryProvider
from app.tasks.deps import get_day_summary_processor, get_summary_client
from app.tasks.services.day_summary_processor import DaySummaryProcessor


def test_get_summary_client_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Mock()
    monkeypatch.setitem(deps._CLIENT_FACTORIES, DaySummaryProvider.OPENAI, lambda: client)

    assert get_summary_client(DaySummaryProvider.OPENAI) is client


def test_get_summary_client_template(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Mock()
    monkeypatch.setitem(deps._CLIENT_FACTORIES, DaySummaryProvider.TEMPLATE, lambda: client)

    assert get_summary_client(DaySummaryProvider.TEMPLATE) is client


def test_get_summary_client_uses_settings_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Mock()
    monkeypatch.setitem(deps._CLIENT_FACTORIES, DaySummaryProvider.OPENAI, lambda: client)
    monkeypatch.setattr(
        "app.tasks.deps.settings.day_summary.provider",
        DaySummaryProvider.OPENAI,
    )

    assert get_summary_client() is client


def test_get_summary_client_unknown_provider() -> None:
    with pytest.raises(ValueError, match="unsupported day summary provider: unknown"):
        get_summary_client("unknown")


def test_get_day_summary_processor() -> None:
    repo = Mock()
    summary_client = Mock()
    processor = get_day_summary_processor(repo, summary_client)
    assert isinstance(processor, DaySummaryProcessor)
    assert processor.repository is repo
    assert processor.summary_client is summary_client
