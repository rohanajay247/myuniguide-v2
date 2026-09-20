"""Ingest the whole corpus. Use --reset to drop the collection first."""

import sys

from myuniguide.config import settings
from myuniguide.ingest.chunk import to_nodes
from myuniguide.ingest.index import build_index, drop_collection
from myuniguide.ingest.parse import parse_pdf


def main() -> None:
    if "--reset" in sys.argv:
        try:
            drop_collection()
            print(f"dropped collection '{settings.qdrant_collection}'")
        except Exception as exc:  # noqa: BLE001
            print(f"nothing to drop ({exc})")

    paths = settings.pdf_paths
    print(f"{len(paths)} PDFs\n")

    all_nodes = []
    for i, path in enumerate(paths, start=1):
        print(f"[{i:2}/{len(paths)}] {path.name:24}", end=" ", flush=True)
        try:
            nodes = to_nodes(parse_pdf(path), path)
            all_nodes.extend(nodes)
            print(f"-> {len(nodes):3} nodes")
        except Exception as exc:  # noqa: BLE001
            print(f"-> FAILED: {exc}")

    print(f"\ntotal {len(all_nodes)} nodes, embedding...")
    build_index(all_nodes)

    sizes = sorted(len(n.get_content()) for n in all_nodes)
    print(f"chunk chars: min={sizes[0]} median={sizes[len(sizes) // 2]} max={sizes[-1]}")
    print(f"chunks under 50 chars: {sum(1 for s in sizes if s < 50)}")


if __name__ == "__main__":
    main()