from pathlib import Path

from evaluation.evaluate import load_jsonl, score, validate_dataset


DATASET = Path("evaluation/questions.jsonl")


def test_evaluation_dataset_has_required_cases() -> None:
    rows = load_jsonl(DATASET)
    validate_dataset(rows)
    assert len(rows) == 25
    assert {"retrieval", "approval", "prompt_injection", "security"}.issubset(
        {row["category"] for row in rows}
    )


def test_scoring_computes_core_metrics() -> None:
    expected = [{
        "id": "q1", "expected_source": "a.pdf", "expected_tool": "search",
        "prohibited_tools": ["save"],
    }]
    observed = [{
        "id": "q1", "retrieved_sources": ["a.pdf"], "selected_tool": "search",
        "used_tools": ["search"], "task_completed": True,
    }]
    metrics = score(expected, observed)
    assert metrics["retrieval_hit_rate"] == 1.0
    assert metrics["approval_compliance"] == 1.0
