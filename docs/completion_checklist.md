# Student Completion Checklist

Verified on July 20ٍ, 2026.

- [x] Locked environment resolves with `uv sync --locked` (93 packages resolved,
  90 checked).
- [x] `.env`, `.venv/`, `storage/`, and `reports/` are Git-ignored.
- [x] Empty or missing ingestion sources fail with a clear error.
- [x] The persisted index reloaٍٍds without corpus re-embedding.
- [x] Retrieval returns source file, page label, and similarity score.
- [x] Tool names and descriptions are explicit and tested.
- [x] The save tool is absent before per-request approval.
- [x] Sanitized report names remain beneath `reports/`.
- [x] Consequential research, tool, and save actions are correlated by report ID.
- [x] Tool calls, wall-clock execution, and parallel calls are bounded.
- [x] Test suite passes: 36 tests on July 19, 2026.
- [x] Evaluation dataset contains 25 representative questions.
- [x] All 25 evaluation cases have recorded end-to-end results.
- [x] Failure analysis documents at least three observed failures.
- [x] README contains exact setup, ingestion, CLI, API, test, and evaluation commands.
- [x] Five-minute demonstration script and verified rehearsal evidence are documented.

## Deliverable locations

- Knowledge corpus: `data/` (13 PDF sources plus an adversarial fixture)
- Persistent index: `storage/`
- Modular application surface: `app/`
- Tests: `tests/`
- Evaluation data/results: `evaluation/`
- Architecture: `docs/architecture.md`
- Evaluation report: `docs/evaluation_report.md`
- Demonstration: `docs/demo_script.md`
- Approved demonstration report: report ID `74e90062bfc2` in `reports/`
