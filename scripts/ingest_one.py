"""Ingest a single PDF end to end: parse -> chunk -> embed -> Qdrant.

Usage:
    uv run python scripts/ingest_one.py
    uv run python scripts/ingest_one.py corpus/velmora/some-file.pdf
"""

import sys
from pathlib import Path

from myuniguide.config import settings
from myuniguide.ingest.chunk import to_nodes
from myuniguide.ingest.index import build_index
from myuniguide.ingest.parse import parse_pdf


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else settings.pdf_paths[0]

    print(f"[1/3] parsing  {path}")
    markdown = parse_pdf(path)

    print("[2/3] chunking")
    nodes = to_nodes(markdown, path)
    print(f"      {len(nodes)} nodes")
    sizes = sorted(len(n.get_content()) for n in nodes)
    print(f"      chunk chars: min={sizes[0]} median={sizes[len(sizes) // 2]} max={sizes[-1]}")

    print(f"[3/3] embedding -> qdrant collection '{settings.qdrant_collection}'")
    build_index(nodes)
    print("done")


if __name__ == "__main__":
    main()
