"""Build and compare the three chunking variants required by the project guide."""

from __future__ import annotations

import json
import time
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core.node_parser import SentenceSplitter

from app.config import get_config
from app.services.index_service import load_index
from app.services.llm import configure_models
from evaluation.evaluate import load_jsonl, validate_dataset


VARIANTS = [(350, 50), (700, 100), (1200, 150)]


def load_documents():
    config = get_config()
    documents = SimpleDirectoryReader(
        input_dir=str(config.data_dir), recursive=True
    ).load_data()
    for document in documents:
        file_name = document.metadata.get("file_name", "unknown")
        document.metadata.update(
            source_type=Path(file_name).suffix.lower(),
            collection="first_aid_knowledge",
            trust_level="untrusted_reference",
        )
    return documents


def main() -> None:
    config = get_config()
    cases = [
        row
        for row in load_jsonl(Path("evaluation/questions.jsonl"))
        if row["expected_source"] is not None
    ]
    validate_dataset(load_jsonl(Path("evaluation/questions.jsonl")))
    documents = load_documents()
    summaries = []

    for chunk_size, overlap in VARIANTS:
        counter = TokenCountingHandler()
        callbacks = CallbackManager([counter])
        configure_models(config, callbacks)
        started_build = time.perf_counter()
        if (chunk_size, overlap) == (config.chunk_size, config.chunk_overlap):
            index = load_index(config, callbacks)
            node_count = 939
            build_seconds = 0.0
            reused = True
        else:
            nodes = SentenceSplitter(
                chunk_size=chunk_size, chunk_overlap=overlap
            ).get_nodes_from_documents(documents)
            node_count = len(nodes)
            index = VectorStoreIndex(nodes, show_progress=True)
            persist_dir = config.storage_dir / f"chunk_{chunk_size}_{overlap}"
            persist_dir.mkdir(parents=True, exist_ok=True)
            index.storage_context.persist(persist_dir=str(persist_dir))
            build_seconds = time.perf_counter() - started_build
            reused = False

        retriever = index.as_retriever(similarity_top_k=config.top_k)
        hits = 0
        latencies = []
        for case in cases:
            query_started = time.perf_counter()
            nodes = retriever.retrieve(case["question"])
            latencies.append(time.perf_counter() - query_started)
            sources = {
                node.node.metadata.get("file_name", "unknown") for node in nodes
            }
            hits += int(case["expected_source"] in sources)

        summary = {
            "chunk_size": chunk_size,
            "chunk_overlap": overlap,
            "document_count": len(documents),
            "node_count": node_count,
            "top_k": config.top_k,
            "evaluated_questions": len(cases),
            "retrieval_hits": hits,
            "retrieval_hit_rate": round(hits / len(cases), 4),
            "average_retrieval_latency_seconds": round(
                sum(latencies) / len(latencies), 4
            ),
            "build_seconds": round(build_seconds, 2),
            "embedding_tokens": counter.total_embedding_token_count,
            "reused_existing_index": reused,
        }
        summaries.append(summary)
        print(json.dumps(summary, indent=2))

    output = Path("evaluation/chunk_experiment_results.json")
    output.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    best = max(summaries, key=lambda row: row["retrieval_hit_rate"])
    print(f"Best measured variant: {best['chunk_size']}/{best['chunk_overlap']}")


if __name__ == "__main__":
    main()
