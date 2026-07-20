# FirstAidOps

FirstAidOps is a governed, evidence-grounded first-aid research agent built with
LlamaIndex. It searches a private collection of public first-aid documents,
separates evidence from inference, requires per-request approval before saving,
and records consequential actions in a JSONL audit trail.

Dependencies are managed reproducibly with `uv` through `pyproject.toml` and
`uv.lock`. A compatible `requirements.txt` is also included for conventional pip
environments.

> Educational use only. FirstAidOps is not emergency dispatch, medical diagnosis,
> or a substitute for a qualified clinician. Contact local emergency services for
> urgent or life-threatening situations.

## Features

- Persistent `VectorStoreIndex` over PDF sources with measured `top_k=10`
- Explicit 700/100 chunking and source/page metadata
- Knowledge search and two-topic comparison tools
- `FunctionAgent` with bounded, non-parallel tool execution
- Structured comparison output with overlap, differences, and evidence limitations
- Save capability omitted until explicit request-level approval
- Restricted Markdown reports and correlated JSONL audit events
- Interactive CLI and FastAPI interface
- Deterministic security tests and a 25-case evaluation dataset

See [architecture](docs/architecture.md), [evaluation report](docs/evaluation_report.md),
and [demonstration script](docs/demo_script.md).

## Files You Need to Know

- `main.py`: a backward-compatible launcher for CLI and ingestion.
- `app/`: the real modular implementation for agents, API, LLM/index services,
  tools, models, ingestion, CLI, and orchestration.
- `data/`: the PDF knowledge sources.
- `storage/`: the persisted vector index.
- `reports/`: reports saved after approval.

The `tests/`, `evaluation/`, and `docs/` folders support testing and submission.

## Setup with uv (Windows PowerShell)

```powershell
uv sync
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Never place the key in `.env.example`, source
control, reports, logs, or chat messages.

At startup the application logs only the provider and model names; it never logs
credentials. The LLM temperature is fixed at `0.1` because evidence-oriented work
benefits from repeatable tool selection and restrained synthesis rather than highly
varied creative output. `MODEL_PROVIDER` is validated now so another provider such
as Ollama can be added later without silently falling back to an unintended model.

## Ingest and reload

```powershell
uv run python main.py ingest
```

The index is persisted in `storage/`. Normal queries reload it without embedding
the entire corpus again. Re-run ingestion when corpus files or chunking settings
change.

## CLI

```powershell
uv run python main.py
```

The first run returns a draft. Only a separate explicit `y` approval creates an
agent that possesses the save capability.

## API

```powershell
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
# Equivalent guide-compatible import path:
uv run uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

- Web interface: `http://127.0.0.1:8000/`
- Documentation: `http://127.0.0.1:8000/docs`
- Health: `GET http://127.0.0.1:8000/health`
- Research: `POST http://127.0.0.1:8000/research`

Draft request:

```json
{
  "question": "What immediate first-aid steps are recommended for a minor burn?",
  "audience": "first-aid trainee",
  "approved_to_save": false
}
```

`approved_to_save: true` is scoped to that single API request. Every request gets
a fresh report ID, approval state, agent, and tool-call budget.

## Tests and evaluation

```powershell
uv run python -m pytest -q
uv run python evaluation/evaluate.py
uv run python evaluation/evaluate.py --results evaluation/results.jsonl
uv run python -m evaluation.run_end_to_end
uv run python -m evaluation.run_chunk_experiments
```

The end-to-end scorer reports retrieval hit rate, claim-support proxy,
tool-selection accuracy, approval compliance, task completion, loop rate, latency,
token usage, and estimated cost. Failed network runs are retried automatically.

## Security design

- `.env`, reports, storage, and caches are excluded from Git.
- Retrieved instructions are treated as untrusted data.
- The agent cannot access the save tool before approval.
- Report paths are sanitized and fixed beneath `reports/`.
- Tool calls and wall-clock execution are bounded.
- Parallel tool calls are disabled.
- Errors returned by the API expose exception types rather than secrets.

## Known limitations

- Source quality and freshness determine medical reliability.
- Retrieval and LLM output remain probabilistic and require evaluation.
- The local JSON vector store is for training/demo use, not production scale.
- The API needs authentication, rate limiting, and production observability before
  external deployment.
- Model/API costs and latency vary with input size and provider pricing.
