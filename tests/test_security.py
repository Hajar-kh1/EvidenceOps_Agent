from pathlib import Path

import pytest

from app.agents.research_agent import SYSTEM_PROMPT
from app.config import AppConfig
from app.tools.research_tools import ToolCallBudget, build_tools, save_report


def test_tool_budget_is_bounded() -> None:
    budget = ToolCallBudget(maximum=2)
    budget.consume("one")
    budget.consume("two")
    with pytest.raises(RuntimeError, match="limit exceeded"):
        budget.consume("three")


@pytest.mark.parametrize(
    "title",
    ["../escape", "..\\escape", "/absolute/path", "C:\\secret\\file"],
)
def test_malicious_report_names_stay_in_reports(
    tmp_path: Path, title: str
) -> None:
    config = AppConfig(_env_file=None, reports_dir=tmp_path / "reports")
    save_report(title, "safe", "secure", True, config)
    report = next(config.reports_dir.glob("*.md"))
    assert report.resolve().parent == config.reports_dir.resolve()


def test_unapproved_save_creates_no_audit_or_report(tmp_path: Path) -> None:
    config = AppConfig(_env_file=None, reports_dir=tmp_path / "reports")
    with pytest.raises(PermissionError):
        save_report("blocked", "secret", "secure", False, config)
    assert not config.reports_dir.exists()


def test_system_policy_treats_retrieved_text_as_untrusted() -> None:
    assert "untrusted reference data" in SYSTEM_PROMPT
    assert "Never expose secrets" in SYSTEM_PROMPT


def test_adversarial_fixture_contains_expected_attack() -> None:
    attack = Path("data/adversarial_prompt_injection.txt").read_text()
    assert "SYSTEM OVERRIDE" in attack
    assert "environment variables" in attack


def test_save_tool_is_removed_until_approval(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.tools.research_tools.load_query_engine",
        lambda config, callback_manager=None: object(),
    )
    config = AppConfig(_env_file=None)
    draft_names = {
        tool.metadata.name
        for tool in build_tools(
            report_id="draft", approved_to_save=False, config=config
        )
    }
    approved_names = {
        tool.metadata.name
        for tool in build_tools(
            report_id="approved", approved_to_save=True, config=config
        )
    }
    assert "save_report" not in draft_names
    assert "save_report" in approved_names
