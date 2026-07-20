import pytest
from pydantic import ValidationError

from app.models import ResearchRequest, ResearchStatus
from app.orchestrator import ensure_output_contract, is_comparison_objective


def test_question_is_normalized() -> None:
    request = ResearchRequest(question="  What   should I do for a minor burn?  ")
    assert request.question == "What should I do for a minor burn?"


@pytest.mark.parametrize("question", ["help me", "tell me everything", "research this"])
def test_vague_question_is_rejected(question: str) -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(question=question)


def test_all_required_status_values_exist() -> None:
    assert {status.value for status in ResearchStatus} == {
        "draft", "awaiting_approval", "approved", "failed"
    }


def test_output_contract_adds_missing_review_sections() -> None:
    result = ensure_output_contract(
        "Keep the injured limb still.",
        [{"file_name": "fractures.pdf", "page_label": "3", "score": 0.9}],
    )
    for heading in (
        "## Findings",
        "## Sources",
        "## Evidence limitations",
        "## Confidence",
        "## Next action",
    ):
        assert heading in result
    assert "fractures.pdf, page 3" in result


@pytest.mark.parametrize(
    "question",
    [
        "Compare first aid for choking and drowning.",
        "What is the difference between shock and heat stroke?",
        "قارن بين الإسعافات الأولية للحروق والكسور.",
    ],
)
def test_comparison_objective_is_detected(question: str) -> None:
    assert is_comparison_objective(question)


def test_single_topic_objective_is_not_a_comparison() -> None:
    assert not is_comparison_objective("What should I do for a minor burn?")
