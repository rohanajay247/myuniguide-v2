"""Run the benchmark. Saves raw results; scoring is a separate step.

Three guards worth keeping: the run aborts after a handful of consecutive API
errors rather than silently losing half the questions; the save uses
default=str so an unexpected type cannot destroy a completed run at the last
step; and traces are flushed before the save, because Langfuse batches in the
background and the last few would otherwise never arrive.
"""

import json
import sys
import time
from datetime import datetime

from eval.benchmark import questions
from eval.config import eval_settings
from myuniguide.config import settings
from myuniguide.graph.flow import answer as graph_answer
from myuniguide.tracing import flush

MAX_CONSECUTIVE_ERRORS = 5


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    klass = next(
        (a.split("=", 1)[1] for a in sys.argv if a.startswith("--klass=")), None
    )

    qs = questions()
    if klass:
        wanted = set(klass.split(","))
        qs = [q for q in qs if q.klass in wanted]
    elif args:
        qs = qs[: int(args[0])]

    if not qs:
        raise SystemExit("no questions selected")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    consecutive_errors = 0

    print(f"run {run_id} — {len(qs)} questions, model={settings.llm_model}, "
          f"top_k={settings.top_k}, mode={settings.retrieval_mode}, "
          f"rerank={settings.rerank}, tracing={settings.tracing_enabled}\n")

    for i, q in enumerate(qs, start=1):
        started = time.perf_counter()
        try:
            response, state = graph_answer(q.text)
            nodes = state.get("nodes", [])
            record = {
                "id": q.id,
                "klass": q.klass,
                "language": q.language,
                "decision": response.decision.value,
                "answer": response.answer,
                "citations": [c.model_dump() for c in response.citations],
                "conflicts": [c.model_dump() for c in response.conflicts],
                "apparent_conflict": state.get("apparent_conflict"),
                "override_rule": state.get("override_rule"),
                "retrieved": [
                    {
                        "document": n.metadata.get("document"),
                        "section": n.metadata.get("section"),
                        "chunk_type": n.metadata.get("chunk_type"),
                        "score": float(n.score) if n.score is not None else None,
                    }
                    for n in nodes
                ],
                "error": None,
            }
            consecutive_errors = 0
        except Exception as exc:  # noqa: BLE001
            record = {
                "id": q.id,
                "klass": q.klass,
                "language": q.language,
                "decision": None,
                "error": str(exc),
            }
            consecutive_errors += 1

        record["seconds"] = round(time.perf_counter() - started, 2)
        results.append(record)

        print(f"[{i:2}/{len(qs)}] {q.id} {q.klass:24} -> {record['decision']} "
              f"({record['seconds']}s)")
        if record["error"]:
            print(f"         ERROR: {record['error'][:140]}")

        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"\nABORTING after {consecutive_errors} consecutive errors. "
                  f"{len(qs) - i} questions not run.")
            break

    flush()

    eval_settings.results_dir.mkdir(parents=True, exist_ok=True)
    out = eval_settings.results_dir / f"run_{run_id}.json"

    payload = {
        "run_id": run_id,
        "model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "top_k": settings.top_k,
        "retrieval_mode": settings.retrieval_mode,
        "rerank": settings.rerank,
        "rerank_model": settings.rerank_model if settings.rerank else None,
        "candidate_k": settings.candidate_k if settings.rerank else None,
        "results": results,
    }

    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    failed = sum(1 for r in results if r["error"])
    total_seconds = sum(r["seconds"] for r in results)
    print(f"\nsaved {out}")
    print(f"{len(results)} questions in {total_seconds / 60:.1f} min "
          f"({total_seconds / len(results):.1f}s each)")
    if failed:
        print(f"{failed}/{len(results)} questions failed — this run is not "
              f"comparable to a clean baseline.")


if __name__ == "__main__":
    main()