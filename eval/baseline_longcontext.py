"""Long-context baseline: the whole corpus in one context window.

This is the control V1 tied with. V1 scored 84% on its benchmark and a naive
long-context baseline scored the same, which meant V1's retrieval engineering
had not demonstrably improved anything. If V2 does not beat this control, the
same conclusion applies here.

No retrieval, no chunking, no metadata, no graph. All 19 documents concatenated
and handed to the model with the question.
"""

import json
import sys
import time
from datetime import datetime
from functools import lru_cache

from google import genai
from google.genai import types

from eval.benchmark import questions
from eval.config import eval_settings
from myuniguide.config import settings
from myuniguide.generate.answer import SYSTEM_PROMPT
from myuniguide.ingest.parse import parse_pdf
from myuniguide.schemas import AnswerResponse

MAX_CONSECUTIVE_ERRORS = 3


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


@lru_cache(maxsize=1)
def full_corpus() -> str:
    """Every document, concatenated. Uses the markdown cache, so no re-parsing."""
    parts = []
    for path in settings.pdf_paths:
        parts.append(f"===== DOCUMENT: {path.name} =====\n\n{parse_pdf(path)}")
    return "\n\n".join(parts)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    qs = questions()[: int(args[0])] if args else questions()

    corpus = full_corpus()
    print(f"corpus: {len(corpus):,} chars (~{len(corpus) // 4:,} tokens)")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    consecutive_errors = 0

    print(f"baseline {run_id} — {len(qs)} questions, model={settings.llm_model}\n")

    for i, q in enumerate(qs, start=1):
        started = time.perf_counter()
        try:
            response = _client().models.generate_content(
                model=settings.llm_model,
                contents=f"Documents:\n\n{corpus}\n\nQuestion: {q.text}",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=AnswerResponse,
                    temperature=0,
                ),
            )
            parsed = response.output_parsed if hasattr(response, "output_parsed") \
                else response.parsed
            usage = getattr(response, "usage_metadata", None)
            record = {
                "id": q.id,
                "klass": q.klass,
                "language": q.language,
                "decision": parsed.decision.value,
                "answer": parsed.answer,
                "citations": [c.model_dump() for c in parsed.citations],
                "conflicts": [c.model_dump() for c in parsed.conflicts],
                "retrieved": [],
                "input_tokens": getattr(usage, "prompt_token_count", None),
                "error": None,
            }
            consecutive_errors = 0
        except Exception as exc:  # noqa: BLE001
            record = {"id": q.id, "klass": q.klass, "language": q.language,
                      "decision": None, "error": str(exc)}
            consecutive_errors += 1

        record["seconds"] = round(time.perf_counter() - started, 2)
        results.append(record)
        print(f"[{i:2}/{len(qs)}] {q.id} {q.klass:24} -> {record['decision']} "
              f"({record['seconds']}s)")
        if record["error"]:
            print(f"         ERROR: {record['error'][:160]}")

        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"\nABORTING after {consecutive_errors} consecutive errors.")
            break

    eval_settings.results_dir.mkdir(parents=True, exist_ok=True)
    out = eval_settings.results_dir / f"run_baseline-{run_id}.json"
    out.write_text(
        json.dumps({"run_id": f"baseline-{run_id}", "model": settings.llm_model,
                    "embedding_model": None, "top_k": None,
                    "retrieval_mode": "long_context", "rerank": False,
                    "results": results},
                   indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()