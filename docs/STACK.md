# Locked Stack

Fourteen components, three optional. One choice per slot — no alternatives under evaluation.

## Language and tooling
- Python 3.12
- uv (dependency management, lockfile)
- pytest
- Docker + Docker Compose

## Ingestion
- **Docling** — PDF to structured Markdown. Corpus has a clean text layer.
- **LlamaIndex** — Document/Node model, chunking, metadata.

## Storage and retrieval
- **Qdrant** — local via Docker Compose. Named vectors hold dense and sparse in one collection.
- **`gemini-embedding-2`** — dense. GA since August 2026, strong multilingual, covered by existing Gemini credits.
- **FastEmbed `Qdrant/bm25`** — sparse. BM25 inside Qdrant, no second index.
- **Qdrant Query API + RRF** — server-side fusion. Makes dense-only / BM25-only / hybrid a parameter rather than three code paths.
- **`BAAI/bge-reranker-v2-m3`** — multilingual cross-encoder, CPU, top-20 to top-5.

## Orchestration and generation
- **LangGraph** — state as TypedDict, conditional edges for the decision.
- **Pydantic v2** — enforced response schema, provider-side JSON schema mode.
- **`gemini-3.5-flash`** — GA since May 2026. Model name lives in `.env`, swappable in one line. `gemini-3.8-flash` is newer if you want a second row in the results table.

## API and UI
- **FastAPI**
- **React** — optional, Day 10 only if time allows.

## Evaluation and observability
- **Custom scorer** — primary instrument. Scores the 72 labelled questions per category.
- **Ragas** — secondary. Faithfulness, context precision/recall, answer relevancy.
- **Langfuse Cloud** — free tier. Not self-hosted: that needs Postgres + ClickHouse.

## Explicitly not used
LangChain, Ollama, Cloud Run, Postgres, Redis, authentication.

## Notes

**Why sparse vectors inside Qdrant.** The common pattern runs a separate BM25 index and
fuses in Python. Qdrant's named sparse vectors plus server-side RRF does it in one query,
and the retrieval comparison becomes a config flag.

**Why Ragas is secondary.** Faithfulness and context precision are generation metrics.
They cannot tell you whether the system distinguished a genuine conflict from a legitimate
override, or declined correctly on an absence case. Those are categorical and the 72
questions already carry the labels. Ragas must not become the measurement plan.

**Why Gemini rather than OpenAI.** Existing credits. It also removes the cost ceiling
from the design entirely, which means the long-context baseline over all 296 pages becomes
effectively free to run — and that baseline is the single most important control in the
project. Two constraints come with it: `response_schema` does not support Optional fields,
unions or `default_factory`, so `schemas.py` stays flat; and changing `EMBEDDING_MODEL`
changes the vector dimension, so the Qdrant collection must be dropped before re-ingesting.

**Why Langfuse Cloud.** Self-hosting is half a day of Compose debugging that buys nothing
for a portfolio project, and it is exactly the kind of yak-shave that eats Day 8.
