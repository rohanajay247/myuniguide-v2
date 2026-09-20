"""Chunk every document and report structure. No embedding, no API cost."""

from collections import Counter

from myuniguide.config import settings
from myuniguide.ingest.chunk import to_nodes
from myuniguide.ingest.doc_meta import from_path
from myuniguide.ingest.parse import parse_pdf


def main() -> None:
    total: list = []
    sizes: list[int] = []
    types: Counter = Counter()
    missing_section = 0

    for path in settings.pdf_paths:
        md = parse_pdf(path)
        meta = from_path(path, md)
        nodes = to_nodes(md, path)
        total.extend(nodes)

        flags = []
        if meta.is_amendment:
            flags.append("amendment")
        if meta.is_consolidated:
            flags.append("consolidated")
        print(f"{path.name:22} {meta.doc_type:5} {str(meta.programme):5} "
              f"{len(nodes):4} nodes  {' '.join(flags)}")

        for n in nodes:
            sizes.append(len(n.get_content()))
            types[n.metadata.get("chunk_type")] += 1
            if not n.metadata.get("section"):
                missing_section += 1

    sizes.sort()
    print(f"\ntotal nodes: {len(total)}")
    print(f"chunk chars: min={sizes[0]} median={sizes[len(sizes)//2]} max={sizes[-1]}")
    print(f"under 50 chars:  {sum(1 for s in sizes if s < 50)}")
    print(f"over 3000 chars: {sum(1 for s in sizes if s > 3000)}")
    print(f"missing section metadata: {missing_section}")
    print(f"chunk types: {dict(types)}")

    print("\n--- provisions (first 25) ---")
    shown = 0
    for n in total:
        if n.metadata.get("chunk_type") == "provision" and shown < 25:
            m = n.metadata
            print(f"  [{m['doc_code']}] {m['section']:8} {m['section_title'][:55]}")
            shown += 1

    print("\n--- amendment operations ---")
    for n in total:
        if n.metadata.get("chunk_type") == "amendment_operation":
            m = n.metadata
            print(f"  [{m['doc_code']}] op {m['operation_no']} -> "
                  f"{str(m.get('targets_section')):8} {m['section_title'][:50]}")

    print("\n--- modules (first 10) ---")
    shown = 0
    for n in total:
        if n.metadata.get("chunk_type") == "module" and shown < 10:
            m = n.metadata
            print(f"  [{m['doc_code']}] {m['module_code']:12} {m['section_title'][:50]}")
            shown += 1


if __name__ == "__main__":
    main()