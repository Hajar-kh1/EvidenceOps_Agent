# FirstAidOps Evaluation Report

## Baseline

- Corpus: 13 public first-aid PDFs plus one adversarial text fixture.
- Latest PDF ingestion: 545 loaded page documents and 939 nodes.
- Chunking: 700 tokens with 100-token overlap.
- Retrieval: vector similarity; measured at `top_k=5` and `top_k=10`.
- Models: `text-embedding-3-small` and `gpt-4.1-mini`.

## Verified results

- Deterministic test suite: run with `pytest` (see the latest terminal output).
- Persistent index: successfully loaded without re-embedding.
- End-to-end smoke test: a minor-burn question selected knowledge retrieval, cited
  `EN_GFARC_GUIDELINES_2020.pdf` pages 213-215, returned
  `awaiting_approval`, and created no report.
- Approval control: direct unapproved saves raise `PermissionError`; the save tool
  is absent from an unapproved agent's capabilities.
- Path restriction: traversal-like titles remain inside `reports/`.
- Prompt injection defenses: retrieved content is declared untrusted, secrets are
  prohibited in output, and the save capability is removed until approval.
- End-to-end prompt-injection run: the agent returned `awaiting_approval`, refused
  the secret/save instruction, and the Markdown report count remained 0 before
  and after execution.

## Dataset and metrics

`evaluation/questions.jsonl` contains 25 cases spanning retrieval, comparison,
approval, prompt injection, path traversal, uncertainty, and source citation.
Use `evaluation/evaluate.py` to validate the dataset and score observed runs.

Metrics reported by the scorer:

- Retrieval Hit Rate
- Tool Selection Accuracy
- Approval Compliance
- Task Completion Rate

### Full 25-case end-to-end run

The complete governed-agent evaluation was run on July 18, 2026. Raw observations
are retained in `evaluation/end_to_end_results.jsonl`, and the machine-readable
aggregate is in `evaluation/end_to_end_summary.json`.

| Metric | Result |
|---|---:|
| Evaluated cases | 25/25 |
| Retrieval Hit Rate | 68.75% |
| Tool Selection Accuracy | 100.00% |
| Approval Compliance | 100.00% |
| Task Completion | 100.00% |
| Claim Support Proxy | 100.00% |
| Loop Rate | 0.00% |
| Secret Leak Rate | 0.00% |
| Average latency | 29.8594 seconds |
| Prompt tokens | 21,246 |
| Completion tokens | 7,490 |
| Embedding tokens | 181 |
| Estimated total cost | $0.020488 |
| Substantive tool calls | 20 |

Claim support is a conservative automated proxy: factual cases pass only when at
least one source was captured in the audit trace. It does not replace human
claim-by-claim grading.

### Measured retrieval experiment

Sixteen cases with an exact expected source were executed against the persisted
index. Strict source Hit Rate@5 was **37.5%** with average retrieval latency
**0.5814 seconds**. Increasing retrieval depth produced Hit Rate@10 of **56.25%**
with average latency **0.5291 seconds** in this small run, so `TOP_K=10` was adopted.

This strict metric understates answer usefulness when the comprehensive GFARC
guideline contains relevant evidence but the case expects a specialized PDF.
Future evaluation should allow a graded list of acceptable sources and add
reranking. The measured raw results are retained in `evaluation/results.jsonl`
and `evaluation/results_top10.jsonl`.

The 25-case run records latency, model and embedding tokens, estimated cost, tool
traces, source hits, approval compliance, loop detection, and secret leakage for
each case. Pricing remains an estimate tied to the configured model rates in
`app/orchestrator.py` and should be updated if provider pricing changes.

### Chunk-size experiment analysis

All three required variants were evaluated on 16 source-specific questions:

| Chunk/overlap | Nodes | Hit Rate@10 | Avg. latency |
|---|---:|---:|---:|
| 350/50 | 1,856 | 56.25% | 0.4794 s |
| 700/100 | 939 | 62.50% | 0.3759 s |
| 1200/150 | 614 | 62.50% | 0.3231 s |

The smaller variant produced many more nodes but did not improve strict source
precision in this corpus, suggesting that narrow fragments sometimes lost useful
context. The 1200-token variant matched the best source hit rate and was fastest in
this small test, but its larger contexts carry a greater risk of irrelevant text.
The 700/100 variant remains the balanced default because it preserved the best hit
rate with more focused evidence than 1200-token chunks. These are corpus-specific
observations, not universal chunking rules.

## Observed failures and improvements

1. OpenAI initially returned `insufficient_quota`; ingestion failed clearly and no
   partial storage was persisted. Billing was enabled and ingestion then succeeded.
2. Several PDFs contain malformed object pointers. The reader emitted warnings but
   extracted the pages. Future work should record per-file page counts and flag
   pages with empty text.
3. Prompt-only approval would permit accidental side effects. The implementation
   now omits `save_report` entirely until a per-request approval is supplied.
4. Comparison questions initially routed to repeated knowledge searches instead
   of `compare_sources`, causing a 4% loop rate and 90% tool accuracy. Explicit
   comparison objectives now receive a deterministically scoped tool set, so the
   agent cannot substitute repeated single-topic searches. The affected cases were
   rerun and verified at 100% tool-selection accuracy with a 0% loop rate.

## Approved-save demonstration evidence

An approved run created report ID `74e90062bfc2`, saved the Markdown report
`74e90062bfc2_Immediate_First-Aid_Steps_for_a_Minor_Thermal_Burn.md`, and recorded
correlated `save_report_started` and `save_report_completed` events. The preceding
unapproved evaluation runs retained 100% approval compliance.

## Limitations

- First-aid sources can conflict or become outdated; responses are educational.
- Vector retrieval can miss relevant passages or retrieve irrelevant context.
- The current store is local JSON and is not intended for concurrent production load.
- Authentication and rate limiting are required before internet deployment.
- Full claim-level support grading still requires human review.
