"""Retrieval: fetch wide, dedupe, optionally rerank, return narrow.

Day 4 showed hybrid improved *which* documents reached the top k but not *how
many* of the required ones did — completeness sat at 50.7% either way. Ranking
cannot add an extra document to a fixed-size set, so widening top_k was what
finally moved it (Day 5: 50.7% to 65.2%).

Reranking is off by default. Measured on Day 5 it scored 77.8% against hybrid's
81.9%: a cross-encoder scores each passage independently for relevance, so when
an answer needs several complementary chunks it keeps the ones that most
resemble the question and discards the rest. It stays here behind a flag
because the ablation is part of the write-up.
"""

from functools import lru_cache

from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore, QueryBundle

from myuniguide.config import settings
from myuniguide.ingest.index import load_index


@lru_cache(maxsize=1)
def _reranker() -> SentenceTransformerRerank:
    return SentenceTransformerRerank(
        model=settings.rerank_model,
        top_n=settings.top_k,
    )


def _dedupe(nodes: list[NodeWithScore]) -> list[NodeWithScore]:
    """Drop duplicate chunks, keeping the first (highest-ranked) occurrence.

    Hybrid fusion can return the same chunk from both the dense and the sparse
    path. Left alone that silently halves the effective top_k — a top_k of 8
    delivering only 4 distinct passages.
    """
    seen: set[str] = set()
    unique: list[NodeWithScore] = []
    for n in nodes:
        key = n.node.node_id
        if key not in seen:
            seen.add(key)
            unique.append(n)
    return unique


def retrieve(
    question: str,
    top_k: int | None = None,
    mode: str | None = None,
    rerank: bool | None = None,
) -> list[NodeWithScore]:
    k = top_k or settings.top_k
    use_rerank = settings.rerank if rerank is None else rerank

    # Over-fetch so deduplication does not leave us short of k.
    fetch_k = settings.candidate_k if use_rerank else k * 2

    retriever = load_index().as_retriever(
        vector_store_query_mode=mode or settings.retrieval_mode,
        similarity_top_k=fetch_k,
        sparse_top_k=max(settings.sparse_top_k, fetch_k),
    )
    nodes = _dedupe(retriever.retrieve(question))

    if not use_rerank:
        return nodes[:k]

    reranked = _reranker().postprocess_nodes(nodes, QueryBundle(question))
    return reranked[:k]