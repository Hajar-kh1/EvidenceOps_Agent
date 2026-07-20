"""Governed search, comparison, audit, and approved-save tools."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from llama_index.core.tools import FunctionTool

from app.config import AppConfig, get_config
from app.services.index_service import load_query_engine


@dataclass
class ToolCallBudget:
    maximum: int
    used: int = 0

    def consume(self, tool_name: str) -> None:
        self.used += 1
        if self.used > self.maximum:
            raise RuntimeError(f"Tool-call limit exceeded before {tool_name}")


def structured_comparison(
    topic_a: str,
    topic_b: str,
    answer_a: str,
    answer_b: str,
    sources_a: list[str],
    sources_b: list[str],
) -> dict[str, Any]:
    source_set_a = set(sources_a)
    source_set_b = set(sources_b)
    shared_sources = sorted(source_set_a & source_set_b)
    return {
        "topics": {"topic_a": topic_a, "topic_b": topic_b},
        "evidence": {"topic_a": answer_a, "topic_b": answer_b},
        "overlap": {
            "shared_sources": shared_sources,
            "note": (
                "Both topics are supported by at least one shared source."
                if shared_sources
                else "No shared source was retrieved; conceptual overlap requires review."
            ),
        },
        "differences": {
            "topic_a_only_sources": sorted(source_set_a - source_set_b),
            "topic_b_only_sources": sorted(source_set_b - source_set_a),
            "note": "The two evidence summaries above preserve topic-specific findings.",
        },
        "evidence_limitations": [
            "Retrieved context may omit relevant passages outside the configured top-k.",
            "Shared sources do not by themselves prove that recommendations are equivalent.",
            "A human reviewer should verify conflicts, freshness, and applicability.",
        ],
        "sources": sorted(source_set_a | source_set_b),
    }


def record_audit_event(
    action: str, detail: str, report_id: str, config: AppConfig | None = None
) -> str:
    config = config or get_config()
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_id": report_id,
        "action": action[:80],
        "detail": detail[:1000],
    }
    with (config.reports_dir / "audit_log.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")
    return "Audit event recorded."


def save_report(
    title: str,
    content: str,
    report_id: str,
    approved: bool,
    config: AppConfig | None = None,
) -> str:
    config = config or get_config()
    if not approved:
        raise PermissionError("Report saving requires explicit approval.")
    if not content.strip():
        raise ValueError("Report content cannot be empty.")
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", title.strip()).strip("_")
    path = config.reports_dir / f"{report_id}_{slug[:50] or 'report'}.md"
    record_audit_event("save_report_started", path.name, report_id, config)
    path.write_text(content, encoding="utf-8")
    record_audit_event("save_report_completed", path.name, report_id, config)
    return f"Report saved to {path.as_posix()}"


def build_tools(
    *,
    report_id: str,
    approved_to_save: bool,
    config: AppConfig | None = None,
    callback_manager: CallbackManager | None = None,
    usage: dict[str, Any] | None = None,
    comparison_only: bool = False,
) -> list[FunctionTool]:
    config = config or get_config()
    engine = load_query_engine(config, callback_manager)
    budget = ToolCallBudget(config.max_tool_calls)
    usage = usage if usage is not None else {"embedding_tokens": 0}
    usage.setdefault("sources", [])

    def knowledge_base_search(question: str) -> str:
        budget.consume("knowledge_base_search")
        usage["embedding_tokens"] += len(Settings.tokenizer(question))
        response = engine.query(question)
        sources: list[dict[str, Any]] = []
        for source in response.source_nodes:
            metadata = source.node.metadata
            sources.append(
                {
                    "file_name": metadata.get("file_name", "unknown"),
                    "page_label": metadata.get("page_label"),
                    "score": round(float(source.score), 4)
                    if source.score is not None
                    else None,
                }
            )
        usage["sources"] = sources
        record_audit_event(
            "tool_called",
            json.dumps(
                {
                    "tool": "knowledge_base_search",
                    "sources": [source["file_name"] for source in sources],
                }
            ),
            report_id,
            config,
        )
        return json.dumps(
            {"answer": str(response), "sources": sources}, ensure_ascii=False
        )

    def compare_sources(topic_a: str, topic_b: str) -> str:
        budget.consume("compare_sources")
        usage["embedding_tokens"] += len(Settings.tokenizer(topic_a))
        usage["embedding_tokens"] += len(Settings.tokenizer(topic_b))
        first = engine.query(topic_a)
        second = engine.query(topic_b)
        sources_a = [
            node.node.metadata.get("file_name", "unknown")
            for node in first.source_nodes
        ]
        sources_b = [
            node.node.metadata.get("file_name", "unknown")
            for node in second.source_nodes
        ]
        comparison = structured_comparison(
            topic_a, topic_b, str(first), str(second), sources_a, sources_b
        )
        usage["sources"] = [
            {"file_name": file_name, "page_label": None, "score": None}
            for file_name in comparison["sources"]
        ]
        record_audit_event(
            "tool_called",
            json.dumps({"tool": "compare_sources", "sources": comparison["sources"]}),
            report_id,
            config,
        )
        return json.dumps(comparison, ensure_ascii=False)

    def audit_event(action: str, detail: str) -> str:
        budget.consume("record_audit_event")
        record_audit_event(
            "tool_called",
            json.dumps({"tool": "record_audit_event"}),
            report_id,
            config,
        )
        return record_audit_event(action, detail, report_id, config)

    comparison_tool = FunctionTool.from_defaults(
            fn=compare_sources,
            name="compare_sources",
            description=(
                "Use exactly once for every request that compares two first-aid topics. "
                "It performs both retrievals and returns overlap, differences, sources, "
                "and evidence limitations."
            ),
        )
    tools = [
        comparison_tool,
        FunctionTool.from_defaults(
            fn=audit_event,
            name="record_audit_event",
            description="Record an auditable event for this request.",
        ),
    ]
    if not comparison_only:
        tools.insert(
            0,
            FunctionTool.from_defaults(
                fn=knowledge_base_search,
                name="knowledge_base_search",
                description=(
                    "Search first-aid sources for one topic and return evidence with "
                    "file/page sources. Do not use it for two-topic comparisons; use "
                    "compare_sources instead."
                ),
            ),
        )
    if approved_to_save:

        def approved_save_report(title: str, content: str) -> str:
            budget.consume("save_report")
            record_audit_event(
                "tool_called",
                json.dumps({"tool": "save_report"}),
                report_id,
                config,
            )
            return save_report(title, content, report_id, True, config)

        tools.append(
            FunctionTool.from_defaults(
                fn=approved_save_report,
                name="save_report",
                description="Save the approved final Markdown report.",
            )
        )
    return tools