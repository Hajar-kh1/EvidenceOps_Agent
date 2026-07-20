from __future__ import annotations

import json
import time
import argparse
from pathlib import Path

from app.config import get_config
from app.services.index_service import load_index
from evaluation.evaluate import load_jsonl, validate_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--output", type=Path, default=Path("evaluation/results.jsonl"))
    args = parser.parse_args()
    dataset = load_jsonl(Path("evaluation/questions.jsonl"))
    validate_dataset(dataset)
    config = get_config()
    top_k = args.top_k or config.top_k
    retriever = load_index(config).as_retriever(similarity_top_k=top_k)
    output = args.output
    results = []
    for case in dataset:
        expected_source = case["expected_source"]
        if expected_source is None:
            continue
        started = time.perf_counter()
        nodes = retriever.retrieve(case["question"])
        latency = time.perf_counter() - started
        sources = sorted(
            {
                node.node.metadata.get("file_name", "unknown")
                for node in nodes
            }
        )
        hit = expected_source in sources
        results.append(
            {
                "id": case["id"],
                "retrieved_sources": sources,
                "selected_tool": "knowledge_base_search",
                "used_tools": ["knowledge_base_search"],
                "task_completed": hit,
                "latency_seconds": round(latency, 4),
            }
        )
        print(f"{case['id']}: {'HIT' if hit else 'MISS'} ({latency:.2f}s)")
    output.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in results) + "\n",
        encoding="utf-8",
    )
    average = sum(row["latency_seconds"] for row in results) / len(results)
    print(f"Wrote {len(results)} top-{top_k} results to {output}")
    print(f"Average retrieval latency: {average:.4f}s")


if __name__ == "__main__":
    main()
