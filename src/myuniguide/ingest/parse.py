"""Step 1 of ingestion: PDF -> structured Markdown, via Docling.

Parsed markdown is cached on disk. Docling takes ~5s per document and we
re-parse constantly while tuning the chunker; delete .cache/markdown to
force a re-parse.
"""

import hashlib
from functools import lru_cache
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from myuniguide.config import settings

CACHE = Path(".cache/markdown")


@lru_cache(maxsize=1)
def _converter() -> DocumentConverter:
    opts = PdfPipelineOptions()
    opts.do_ocr = settings.enable_ocr
    opts.do_table_structure = True
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )


def _cache_path(path: Path) -> Path:
    """Key on file content, not path or mtime.

    A path-based key misses whenever the corpus moves — a different machine,
    a container mount — and mtime changes on copy. Content hashing makes the
    cache portable and makes the cached markdown the reproducible artifact.
    """
    digest = hashlib.md5(
        path.read_bytes() + str(settings.enable_ocr).encode()
    ).hexdigest()[:16]
    return CACHE / f"{path.stem}_{digest}.md"


def parse_pdf(path: Path, use_cache: bool = True) -> str:
    """Convert one PDF to Markdown, preserving headings, lists and tables."""
    cached = _cache_path(path)
    if use_cache and cached.exists():
        return cached.read_text(encoding="utf-8")

    markdown = _converter().convert(str(path)).document.export_to_markdown()

    if use_cache:
        CACHE.mkdir(parents=True, exist_ok=True)
        cached.write_text(markdown, encoding="utf-8")
    return markdown