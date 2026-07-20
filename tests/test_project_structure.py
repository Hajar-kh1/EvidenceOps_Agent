from app.agents.research_agent import build_agent
from app.api.main import app
from app.models import ResearchRequest
from app.orchestrator import run_research
from app.services.index_service import load_query_engine
from app.tools.research_tools import structured_comparison


def test_required_modular_import_surface_is_available() -> None:
    assert app.title == "FirstAidOps API"
    assert ResearchRequest(question="What should I do for a minor burn?")
    assert all(
        callable(item)
        for item in (
            build_agent,
            run_research,
            load_query_engine,
            structured_comparison,
        )
    )
