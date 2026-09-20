"""DAY 1 CHECKPOINT — run this before writing any pipeline code.

Parses one PDF with Docling and reports whether the document structure survived.
If headings and numbered lists do not survive, we change the parsing approach
today rather than discovering it on Day 4.

Usage:
    uv run python scripts/inspect_parse.py
    uv run python scripts/inspect_parse.py corpus/velmora/some-file.pdf
"""

import re
import sys
from pathlib import Path

from myuniguide.config import settings
from myuniguide.ingest.parse import parse_pdf


def report(markdown: str) -> None:
    lines = markdown.splitlines()
    headings = [ln for ln in lines if ln.startswith("#")]
    section_marks = re.findall(r"§\s*\d+|Artikel\s+\d+", markdown)
    numbered = re.findall(r"^\s*\(\d+\)", markdown, flags=re.MULTILINE)
    tables = [ln for ln in lines if ln.strip().startswith("|")]

    print("\n=== STRUCTURE REPORT ===")
    print(f"characters:            {len(markdown):,}")
    print(f"markdown headings:     {len(headings)}")
    print(f"§ / Artikel mentions:  {len(section_marks)}")
    print(f"numbered paragraphs:   {len(numbered)}   e.g. (1) (2) (3)")
    print(f"table rows:            {len(tables)}")

    print("\n=== FIRST 10 HEADINGS ===")
    for h in headings[:10]:
        print(" ", h)

    print("\n=== FIRST 2500 CHARACTERS ===")
    print(markdown[:2500])


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        pdfs = settings.pdf_paths
        if not pdfs:
            raise SystemExit(f"No PDFs found under {settings.corpus_dir.resolve()}")
        path = pdfs[0]

    print(f"Parsing: {path}")
    markdown = parse_pdf(path)

    out = Path("eval/parse_sample.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(f"Full markdown written to: {out}")

    report(markdown)


if __name__ == "__main__":
    main()
