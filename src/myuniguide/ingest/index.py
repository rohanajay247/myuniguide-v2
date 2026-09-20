"""Step 3 of ingestion: nodes -> embeddings -> Qdrant.

The collection holds two named vectors per chunk: a dense Gemini embedding and
a sparse BM25 vector computed locally by FastEmbed. Qdrant fuses them
server-side with Reciprocal Rank Fusion, so dense / sparse / hybrid is a query
parameter rather than three code paths.

Changing EMBEDDING_MODEL or the hybrid setting changes the collection schema:
drop the collection before re-ingesting.
"""

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import BaseNode
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from myuniguide.config import settings

SPARSE_MODEL = "Qdrant/bm25"


def _client() -> QdrantClient:
    """Embedded when QDRANT_PATH is set, otherwise the server at QDRANT_URL.

    Embedded mode reads a local folder, so the index can be baked into the
    container image — no separate database service to host.
    """
    if settings.qdrant_path:
        return QdrantClient(path=settings.qdrant_path)
    return QdrantClient(url=settings.qdrant_url)


def embedder() -> GoogleGenAIEmbedding:
    return GoogleGenAIEmbedding(
        model_name=settings.embedding_model,
        api_key=settings.google_api_key,
    )


def vector_store() -> QdrantVectorStore:
    return QdrantVectorStore(
        client=_client(),
        collection_name=settings.qdrant_collection,
        enable_hybrid=True,
        fastembed_sparse_model=SPARSE_MODEL,
        batch_size=20,
    )


def build_index(nodes: list[BaseNode]) -> VectorStoreIndex:
    storage = StorageContext.from_defaults(vector_store=vector_store())
    return VectorStoreIndex(
        nodes=nodes,
        storage_context=storage,
        embed_model=embedder(),
        show_progress=True,
    )


def load_index() -> VectorStoreIndex:
    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store(),
        embed_model=embedder(),
    )


def drop_collection() -> None:
    _client().delete_collection(settings.qdrant_collection)