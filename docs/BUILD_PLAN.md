# Build Plan — 10 working days

Active plan. Supersedes the phased plan in `reference/WBS.md`.

Two deliberate changes from the original day-by-day sketch:
measurement moves from Day 7 to Day 2, and version-state resolution is cut to backlog.

| Day | Outcome | Done when |
|---|---|---|
| 1 | Vertical slice | One PDF ingested; `scripts/ask.py` returns a cited answer |
| 2 | Measurement | 72 questions loaded; scoring script prints per-category pass rates; first number recorded |
| 3 | Structure | §-aware chunking + metadata; re-scored against Day 2 |
| 4 | Hybrid retrieval | Dense + BM25 via Qdrant named vectors; re-scored |
| 5 | Reranking | bge-reranker-v2-m3; four-way comparison table produced |
| 6 | Orchestration | LangGraph graph; Pydantic-enforced ANSWER / DECLINE / CONFLICT |
| 7 | Discrimination | Conflict vs legitimate override; citation validation |
| 8 | Instrumentation | Ragas metrics; Langfuse traces with latency, tokens, cost |
| 9 | Hardening | Docker, tests, long-context baseline run |
| 10 | Packaging | README, architecture diagram, demo |

After Day 10: stop. Move to Project 2.

## Day 1 checkpoint

Run `make inspect` before writing any pipeline code. It parses one PDF and reports
whether headings, § / Artikel markers, numbered paragraphs and tables survived Docling.

Everything from Day 3 onward depends on that answer. If the structure is mangled,
the parsing approach changes on Day 1, not on Day 4.

## Scope guard

Not in this project: authentication, billing, user accounts, admin panels,
Kubernetes, microservices, multiple LLM providers, multi-agent systems,
fine-tuning, Ollama, cloud deployment.

If one of these appears mid-build, it is scope creep. Backlog it.
