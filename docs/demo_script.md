# Five-Minute Demonstration

1. Show `app/`, `tests/`, `evaluation/`, `data/`, and the protected `.env` setup.
2. Explain the persisted files in `storage/` and run the health endpoint.
3. Ask a factual burn question and point out the returned source and page.
4. Ask a comparison question about heat stroke and shock.
5. attempt an unapproved save and show that no save tool/report exists.
6. Approve one request, then show the Markdown report and correlated JSONL events.
   A verified example is report ID `74e90062bfc2` and the matching Markdown file in
   `reports/`.
7. Call `POST /research` from `/docs` or PowerShell.
8. Run `pytest -q` and validate the 25-question evaluation dataset.
9. Explain the malformed-PDF warning and the stronger tool-removal approval design.

## Verified rehearsal evidence

- `pytest -q`: 36 tests passed on July 19, 2026.
- Evaluation: 25/25 cases completed; approval compliance was 100%.
- Approved save: report `74e90062bfc2` was written with correlated audit events.
- Architecture and exact commands are available in `docs/architecture.md` and
  `README.md`.
