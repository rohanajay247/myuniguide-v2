"""Central configuration. Everything tunable lives here, nothing is hardcoded elsewhere."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str

    llm_model: str = "gemini-3.5-flash"
    embedding_model: str = "gemini-embedding-2"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "myuniguide_v2"
    qdrant_path: str = ""   # set → embedded on-disk Qdrant; empty → server at qdrant_url

    corpus_dir: Path = Path("./corpus")
    top_k: int = 5

    enable_ocr: bool = False

    retrieval_mode: str = "hybrid"   # "default" (dense) | "sparse" (BM25) | "hybrid"
    sparse_top_k: int = 12

    rerank: bool = False
    rerank_model: str = "BAAI/bge-reranker-base"
    candidate_k: int = 20          # fetched before reranking

    @property
    def pdf_paths(self) -> list[Path]:
        """All corpus PDFs. Only ever reads velmora/ and rheinmark/."""
        return sorted(self.corpus_dir.rglob("*.pdf"))


    langfuse_public_key: str = "pk-lf-c80e2973-93ae-44e4-bae4-60384c3cea91"
    langfuse_secret_key: str = "sk-lf-8b95c447-4e18-4273-8f64-b3ca1fba930a"
    langfuse_host: str = "https://cloud.langfuse.com"

    @property
    def tracing_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


settings = Settings()
