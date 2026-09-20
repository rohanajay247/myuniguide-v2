"""Ask one question and print a structured, cited answer.

Usage:
    uv run python scripts/ask.py "Wie viele ECTS hat das Modul X?"
"""

import sys

from myuniguide.generate.answer import generate
from myuniguide.retrieve.search import retrieve


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Question: ")

    nodes = retrieve(question)
    print(f"\nretrieved {len(nodes)} chunks:")
    for n in nodes:
        print(f"  {n.score:.3f}  {n.metadata.get('document')}  {n.get_content()[:80]!r}")

    response = generate(question, nodes)

    print(f"\n=== {response.decision.value} ===")
    print(response.answer)

    if response.citations:
        print("\nCitations:")
        for c in response.citations:
            print(f"  - {c.document} {c.locus}: {c.quote[:120]}")

    for conflict in response.conflicts:
        print(f"\nConflict: {conflict.summary}")
        for c in conflict.citations:
            print(f"  - {c.document} {c.locus}")


if __name__ == "__main__":
    main()
