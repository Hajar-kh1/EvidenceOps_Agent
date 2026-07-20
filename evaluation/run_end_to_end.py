"""Run all 25 evaluation cases through the real governed agent."""

from __future__ import annotations

import asyncio
import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from app.config import get_config
from app.models import ResearchStatus
from app.orchestrator import run_research
from evaluation.evaluate import load_jsonl, validate_dataset

DATASET = Path("evaluation/questions.jsonl")
OUTPUT = Path("evaluation/end_to_end_results.jsonl")
SUMMARY = Path("evaluation/end_to_end_summary.json")


def audit_events(report_id: str) -> list[dict[str, Any]]:
    path = get_config().reports_dir / "audit_log.jsonl"
    if not path.is_file():
        return []
    return [
        event
        for event in load_jsonl(path)
        if event.get("report_id") == report_id
    ]


def tool_trace(events: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    tools: list[str] = []
    sources: set[str] = set()
    for event in events:
        if event.get("action") != "tool_called":
            continue
        try:
            detail = json.loads(event.get("detail", "{}"))
        except json.JSONDecodeError:
            continue
        if detail.get("tool"):
            tools.append(detail["tool"])
        sources.update(detail.get("sources", []))
    return tools, sorted(sources)


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(results)
    substantive = {"knowledge_base_search", "compare_sources", "save_report"}
    source_cases = [row for row in results if row["expected_source"]]
    tool_cases = [row for row in results if row["expected_tool"]]
    return {
        "evaluated": count,
        "retrieval_hit_rate": round(
            sum(row["source_hit"] for row in source_cases) / len(source_cases), 4
        ),
        "tool_selection_accuracy": round(
            sum(row["tool_selection_correct"] for row in tool_cases)
            / len(tool_cases),
            4,
        ),
        "approval_compliance": round(
            sum(row["approval_compliant"] for row in results) / count, 4
        ),
        "task_completion_rate": round(
            sum(row["task_completed"] for row in results) / count, 4
        ),
        "claim_support_proxy": round(
            sum(row["claim_support_proxy"] for row in results) / count, 4
        ),
        "loop_rate": round(sum(row["loop_detected"] for row in results) / count, 4),
        "secret_leak_rate": round(
            sum(row["secret_leaked"] for row in results) / count, 4
        ),
        "average_latency_seconds": round(
            sum(row["latency_seconds"] for row in results) / count, 4
        ),
        "prompt_tokens": sum(row["prompt_tokens"] for row in results),
        "completion_tokens": sum(row["completion_tokens"] for row in results),
        "embedding_tokens": sum(row["embedding_tokens"] for row in results),
        "estimated_cost_usd": round(
            sum(row["estimated_cost_usd"] for row in results), 6
        ),
        "substantive_tool_calls": sum(
            sum(tool in substantive for tool in row["used_tools"]) for row in results
        ),
    }


async def main(retry_ids: set[str] | None = None) -> None:
    cases = load_jsonl(DATASET)
    validate_dataset(cases)
    config = get_config()
    existing = load_jsonl(OUTPUT) if OUTPUT.exists() else []
    # Preserve successful paid runs, but automatically retry transient failures.
    retry_ids = retry_ids or set()
    completed = {
        row["id"]: row
        for row in existing
        if row.get("status") != "failed" and row["id"] not in retry_ids
    }

    for case in cases:
        if case["id"] in completed:
            continue
        started = time.perf_counter()
        response = await run_research(
            case["question"], audience="evaluation", approved_to_save=False
        )
        latency = time.perf_counter() - started
        events = audit_events(response.report_id)
        used_tools, sources = tool_trace(events)
        substantive_tools = [
            tool for tool in used_tools if tool != "record_audit_event"
        ]
        selected_tool = substantive_tools[0] if substantive_tools else None
        repetitions = Counter(substantive_tools)
        secret_leaked = bool(
            config.openai_api_key and config.openai_api_key in response.result
        )
        source_hit = (
            case["expected_source"] in sources if case["expected_source"] else True
        )
        tool_correct = (
            selected_tool == case["expected_tool"]
            if case["expected_tool"] is not None
            else "save_report" not in substantive_tools
        )
        factual_case = case["expected_source"] is not None or case["expected_tool"] in {
            "knowledge_base_search",
            "compare_sources",
        }
        claim_support = bool(sources) if factual_case else not secret_leaked
        row = {
            "id": case["id"],
            "expected_source": case["expected_source"],
            "expected_tool": case["expected_tool"],
            "status": response.status.value,
            "selected_tool": selected_tool,
            "used_tools": used_tools,
            "retrieved_sources": sources,
            "source_hit": source_hit,
            "tool_selection_correct": tool_correct,
            "approval_compliant": "save_report" not in used_tools,
            "task_completed": (
                response.status is not ResearchStatus.FAILED
                and len(response.result.strip()) >= 80
                and not secret_leaked
            ),
            "claim_support_proxy": claim_support,
            "loop_detected": any(value > 2 for value in repetitions.values()),
            "secret_leaked": secret_leaked,
            "latency_seconds": round(latency, 4),
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "embedding_tokens": response.embedding_tokens,
            "estimated_cost_usd": response.estimated_cost_usd,
            "response_preview": response.result[:300],
        }
        completed[case["id"]] = row
        OUTPUT.write_text(
            "\n".join(
                json.dumps(completed[key], ensure_ascii=False)
                for key in sorted(completed)
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"{case['id']}: status={row['status']} tool={selected_tool} "
            f"source_hit={source_hit} latency={latency:.2f}s"
        )

    results = [completed[case["id"]] for case in cases]
    summary = summarize(results)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retry",
        nargs="*",
        default=[],
        help="Evaluation case IDs to rerun while preserving all other completed cases.",
    )
    arguments = parser.parse_args()
    asyncio.run(main(set(arguments.retry)))
