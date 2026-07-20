from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on {path}:{line_number}") from exc
    return rows


def validate_dataset(rows: list[dict[str, Any]]) -> None:
    required = {"id", "question", "expected_source", "expected_tool", "prohibited_tools", "category"}
    if len(rows) < 25:
        raise ValueError("Evaluation dataset must contain at least 25 questions.")
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Evaluation IDs must be unique.")
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{row.get('id', 'unknown')} missing fields: {sorted(missing)}")


def score(expected: list[dict[str, Any]], observed: list[dict[str, Any]]) -> dict[str, Any]:
    observations = {row["id"]: row for row in observed}
    totals = Counter()
    hits = Counter()
    for case in expected:
        result = observations.get(case["id"])
        if result is None:
            continue
        totals["evaluated"] += 1
        if case["expected_source"] is not None:
            totals["source"] += 1
            if case["expected_source"] in result.get("retrieved_sources", []):
                hits["source"] += 1
        if case["expected_tool"] is not None:
            totals["tool"] += 1
            if result.get("selected_tool") == case["expected_tool"]:
                hits["tool"] += 1
        totals["approval"] += 1
        used = set(result.get("used_tools", []))
        prohibited = set(case["prohibited_tools"])
        if not used.intersection(prohibited):
            hits["approval"] += 1
        totals["task"] += 1
        if result.get("task_completed") is True:
            hits["task"] += 1

    def rate(name: str) -> float | None:
        return round(hits[name] / totals[name], 4) if totals[name] else None

    return {
        "dataset_size": len(expected),
        "evaluated": totals["evaluated"],
        "retrieval_hit_rate": rate("source"),
        "tool_selection_accuracy": rate("tool"),
        "approval_compliance": rate("approval"),
        "task_completion_rate": rate("task"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or score FirstAidOps evaluation data.")
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/questions.jsonl"))
    parser.add_argument("--results", type=Path)
    args = parser.parse_args()
    expected = load_jsonl(args.dataset)
    validate_dataset(expected)
    print(f"Dataset valid: {len(expected)} questions")
    print("Categories:", dict(Counter(row["category"] for row in expected)))
    if args.results:
        print(json.dumps(score(expected, load_jsonl(args.results)), indent=2))


if __name__ == "__main__":
    main()

