from evaluation.run_end_to_end import summarize


def test_end_to_end_summary_contains_required_metrics() -> None:
    row = {
        "expected_source": "a.pdf",
        "expected_tool": "knowledge_base_search",
        "source_hit": True,
        "tool_selection_correct": True,
        "approval_compliant": True,
        "task_completed": True,
        "claim_support_proxy": True,
        "loop_detected": False,
        "secret_leaked": False,
        "latency_seconds": 1.0,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "embedding_tokens": 2,
        "estimated_cost_usd": 0.001,
        "used_tools": ["knowledge_base_search"],
    }
    metrics = summarize([row])
    assert metrics["retrieval_hit_rate"] == 1.0
    assert metrics["loop_rate"] == 0.0
    assert metrics["estimated_cost_usd"] == 0.001
