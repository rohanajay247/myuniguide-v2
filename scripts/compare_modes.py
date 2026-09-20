"""Compare dense, sparse and hybrid retrieval on one question."""

import sys

from myuniguide.retrieve.search import retrieve

DEFAULT_Q = "Welche Regelung gilt fuer Studierende der Kohorte WS 2023/24?"


def main() -> None:
    question = " ".join(sys.argv[1:]) or DEFAULT_Q
    print(f"Q: {question}\n")
    for mode in ("default", "sparse", "hybrid"):
        print(f"--- {mode}")
        for n in retrieve(question, mode=mode):
            m = n.metadata
            print(f"  {n.score:.3f}  {m.get('doc_code'):4} {str(m.get('section')):12} "
                  f"{str(m.get('section_title'))[:45]}")
        print()


if __name__ == "__main__":
    main()