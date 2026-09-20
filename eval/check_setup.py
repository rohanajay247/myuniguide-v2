"""Pre-flight check. Run this before ingesting or benchmarking.

Verifies the corpus is placed correctly, the ground truth is reachable but kept
out of the answering path, Qdrant is up and the API key is set.

Usage:
    uv run python -m eval.check_setup
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO = Path(__file__).parent.parent
CORPUS = REPO / "corpus"

ok = True


def check(label: str, passed: bool, detail: str = "") -> None:
    global ok
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not passed:
        ok = False


def main() -> None:
    print("MyUniGuide V2 — setup check\n")

    pdfs = list(CORPUS.rglob("*.pdf"))
    check("corpus PDFs present", len(pdfs) == 19, f"found {len(pdfs)}, expected 19")

    for folder in ("velmora", "rheinmark"):
        n = len(list((CORPUS / folder).glob("*.pdf"))) if (CORPUS / folder).exists() else 0
        check(f"corpus/{folder}", n > 0, f"{n} PDFs")

    leaked = [
        name
        for name in ("ground_truth", "_source", "benchmark_answers.yaml", "module_data.yaml")
        if (CORPUS / name).exists()
    ]
    check("no ground truth inside corpus/", not leaked, f"found {leaked}" if leaked else "")

    from eval.config import eval_settings

    gt = eval_settings.ground_truth_dir
    check("ground truth directory reachable", gt.exists(), str(gt.resolve()))

    if gt.exists():
        # The ground truth lives in the repo so the benchmark is reproducible by
        # anyone who clones it. The boundary that matters is that src/ cannot
        # reach it — enforced by tests/test_corpus_isolation.py, not by where
        # the files happen to sit.
        check(
            "ground truth outside corpus/",
            CORPUS.resolve() not in [gt.resolve(), *gt.resolve().parents],
        )

        from eval.loader import EXPECTED, find

        found = [s for s in EXPECTED if find(s)]
        check("ground truth files", len(found) >= 6, f"{len(found)}/{len(EXPECTED)} found")

    check("GOOGLE_API_KEY set", bool(os.getenv("GOOGLE_API_KEY")))

    try:
        import httpx

        r = httpx.get("http://localhost:6333/healthz", timeout=3)
        check("qdrant reachable", r.status_code == 200)
    except Exception as exc:  # noqa: BLE001
        check("qdrant reachable", False, str(exc)[:60])

    print("\n" + ("Ready." if ok else "Fix the failures above first."))


if __name__ == "__main__":
    main()