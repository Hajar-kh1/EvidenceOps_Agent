"""Per-request orchestration, approval state, audit, and usage accounting."""

from uuid import uuid4

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

from app.agents.research_agent import build_agent
from app.config import get_config
from app.models import ResearchResponse, ResearchStatus
from app.tools.research_tools import record_audit_event


def is_comparison_objective(question: str) -> bool:
    """Identify explicit comparison objectives for deterministic tool scoping."""

    normalized = question.casefold()
    markers = (
        "compare ",
        "comparison ",
        "difference between",
        "differences between",
        " versus ",
        " vs ",
        "قارن",
        "مقارنة",
        "الفرق بين",
    )
    return any(marker in normalized for marker in markers)


def determine_confidence(sources: list[dict[str, object]]) -> str:
    """Return a conservative confidence level based on retrieved evidence."""

    return "Moderate" if sources else "Low"


def ensure_output_contract(result: str, sources: list[dict[str, object]]) -> str:
    """Deterministically add any review sections omitted by the model."""

    output = result.strip()
    lowered = output.casefold()
    additions: list[str] = []
    if "findings" not in lowered:
        output = f"## Findings\n\n{output}"
    if "sources" not in lowered:
        source_lines = []
        for source in sources:
            file_name = str(source.get("file_name", "unknown"))
            page = source.get("page_label")
            source_lines.append(f"- {file_name}" + (f", page {page}" if page else ""))
        additions.append(
            "## Sources\n\n" + ("\n".join(source_lines) if source_lines else "- No source was retrieved.")
        )
    if "evidence limitations" not in lowered:
        additions.append(
            "## Evidence limitations\n\n"
            "This is general educational guidance based on the retrieved documents; "
            "it does not replace professional medical assessment."
        )
    if "confidence" not in lowered:
        confidence = determine_confidence(sources)
        additions.append(
            f"## Confidence\n\n{confidence}, based on the available retrieved evidence."
        )
    if "next action" not in lowered:
        additions.append(
            "## Next action\n\nKeep the person safe, avoid unnecessary movement, "
            "and seek professional or emergency medical assistance when needed."
        )
    return output + ("\n\n" + "\n\n".join(additions) if additions else "")


async def run_research(
    question: str, *, audience: str = "general", approved_to_save: bool = False
) -> ResearchResponse:
    config = get_config()
    report_id = uuid4().hex[:12]
    status = (
        ResearchStatus.APPROVED
        if approved_to_save
        else ResearchStatus.AWAITING_APPROVAL
    )
    record_audit_event("research_started", question, report_id)
    record_audit_event("draft_created", "Generating draft", report_id)
    token_counter = TokenCountingHandler()
    callback_manager = CallbackManager([token_counter])
    usage: dict[str, object] = {"embedding_tokens": 0, "sources": []}
    try:
        agent = build_agent(
            report_id=report_id,
            approved_to_save=approved_to_save,
            config=config,
            callback_manager=callback_manager,
            usage=usage,
            comparison_only=is_comparison_objective(question),
        )
        instruction = (
            "The user approved saving for this request."
            if approved_to_save
            else "Return a draft only and ask for approval before saving."
        )
        result = await agent.run(
            f"Research objective: {question}\nAudience: {audience}\n{instruction}"
        )
        sources = list(usage.get("sources", []))
        confidence = determine_confidence(sources)
        formatted_result = ensure_output_contract(str(result), sources)
        record_audit_event("research_completed", status.value, report_id)
        estimated_cost = (
            token_counter.prompt_llm_token_count * 0.40 / 1_000_000
            + token_counter.completion_llm_token_count * 1.60 / 1_000_000
            + int(usage["embedding_tokens"]) * 0.02 / 1_000_000
        )
        return ResearchResponse(
            report_id=report_id,
            status=status,
            result=formatted_result,
            sources=sources,
            confidence=confidence,
            prompt_tokens=token_counter.prompt_llm_token_count,
            completion_tokens=token_counter.completion_llm_token_count,
            embedding_tokens=int(usage["embedding_tokens"]),
            estimated_cost_usd=round(estimated_cost, 6),
        )
    except Exception as exc:
        record_audit_event("research_failed", type(exc).__name__, report_id)
        return ResearchResponse(
            report_id=report_id,
            status=ResearchStatus.FAILED,
            result=f"Research failed: {type(exc).__name__}",
            sources=[],
            confidence="Low",
            prompt_tokens=token_counter.prompt_llm_token_count,
            completion_tokens=token_counter.completion_llm_token_count,
            embedding_tokens=token_counter.total_embedding_token_count,
        )
