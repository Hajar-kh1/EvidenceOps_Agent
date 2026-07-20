import json
from pathlib import Path

import pytest

from app.config import AppConfig
from app.tools.research_tools import (
    record_audit_event,
    save_report,
    structured_comparison,
)


def test_save_report_requires_approval(tmp_path: Path) -> None:
    config = AppConfig(_env_file=None, reports_dir=tmp_path / "reports")
    with pytest.raises(PermissionError):
        save_report("unsafe", "content", "r1", False, config)
    assert not config.reports_dir.exists()


def test_save_report_cannot_escape_reports(tmp_path: Path) -> None:
    config = AppConfig(_env_file=None, reports_dir=tmp_path / "reports")
    message = save_report("../../outside", "# Safe", "r2", True, config)
    files = list(config.reports_dir.glob("*.md"))
    assert len(files) == 1
    assert files[0].parent == config.reports_dir
    assert "saved" in message.lower()


def test_audit_event_contains_report_id(tmp_path: Path) -> None:
    config = AppConfig(_env_file=None, reports_dir=tmp_path / "reports")
    record_audit_event("test", "completed", "r3", config)
    event = json.loads((config.reports_dir / "audit_log.jsonl").read_text())
    assert event["report_id"] == "r3"


def test_structured_comparison_has_required_contract() -> None:
    result = structured_comparison(
        "burns",
        "shock",
        "Cool the burn.",
        "Monitor breathing.",
        ["shared.pdf", "burns.pdf"],
        ["shared.pdf", "shock.pdf"],
    )
    assert result["overlap"]["shared_sources"] == ["shared.pdf"]
    assert result["differences"]["topic_a_only_sources"] == ["burns.pdf"]
    assert result["differences"]["topic_b_only_sources"] == ["shock.pdf"]
    assert result["evidence_limitations"]
