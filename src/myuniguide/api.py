"""FastAPI wrapper over the graph. Serves the UI and one query endpoint."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from myuniguide.config import settings
from myuniguide.graph.flow import answer as graph_answer
from myuniguide.ratelimit import check as rate_limit

app = FastAPI(title="MyUniGuide V2")

STATIC = Path(__file__).parent / "static"


class Query(BaseModel):
    # The UI caps input at 300 characters, but nothing stops a direct POST.
    question: str = Field(min_length=2, max_length=500)


class RetrievedChunk(BaseModel):
    document: str | None
    section: str | None
    chunk_type: str | None
    score: float | None
    text: str


class QueryResponse(BaseModel):
    decision: str
    answer: str
    citations: list[dict]
    conflicts: list[dict]
    apparent_conflict: bool | None
    override_rule: str | None
    retrieved: list[RetrievedChunk]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict:
    return {
        "model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "top_k": settings.top_k,
        "retrieval_mode": settings.retrieval_mode,
        "rerank": settings.rerank,
    }


@app.post("/api/query", response_model=QueryResponse)
def query(q: Query, request: Request) -> QueryResponse:
    rate_limit(request)

    try:
        response, state = graph_answer(q.question)
    except Exception as exc:  # noqa: BLE001
        # Surface the real cause — a bare 500 sent us looking at Qdrant when
        # the actual problem was an exhausted API quota.
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc

    return QueryResponse(
        decision=response.decision.value,
        answer=response.answer,
        citations=[c.model_dump() for c in response.citations],
        conflicts=[c.model_dump() for c in response.conflicts],
        apparent_conflict=state.get("apparent_conflict"),
        override_rule=state.get("override_rule"),
        retrieved=[
            RetrievedChunk(
                document=n.metadata.get("document"),
                section=n.metadata.get("section"),
                chunk_type=n.metadata.get("chunk_type"),
                score=float(n.score) if n.score is not None else None,
                text=n.get_content()[:600],
            )
            for n in state.get("nodes", [])
        ],
    )