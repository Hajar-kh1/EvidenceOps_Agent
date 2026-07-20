"""FastAPI REST service and HTML interface."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_config
from app.models import ResearchRequest, ResearchResponse
from app.orchestrator import run_research

app = FastAPI(title="FirstAidOps API", version="1.0.0")
WEB_DIR = Path(__file__).parents[2] / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def web_interface() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str | bool]:
    config = get_config()
    return {
        "status": "ok",
        "index_ready": (config.storage_dir / "index_store.json").is_file(),
    }


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    try:
        return await run_research(
            request.question,
            audience=request.audience,
            approved_to_save=request.approved_to_save,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=type(exc).__name__) from exc
