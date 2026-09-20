"""Scores a benchmark run against ground truth.

Deterministic metrics first. Answer correctness needs a judge because the
expected answers are free-text German; that is reported separately and
clearly labelled, so the headline numbers stay checkable by hand.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

from eval.benchmark import answers, doc_code, locus_matches, normalise_locus, questions
from eval.config import eval_settings
from myuniguide.config import settings


class Verdict(BaseModel):
    correct: bool
    reason: str


JUDGE_PROMPT = """You compare a system's answer to a reference answer about German
university examination regulations.

Return correct=true only if the system's answer states the same substantive fact as
the reference. Ignore language, phrasing, verbosity and extra context. A system
answer that adds correct detail is still correct. A system answer that contradicts
the reference, or omits the key fact, is not."""


def judge(question: str, expected: str, actual: str) -> Verdict:
    client = genai.Client(api_key=settings.google_api_key)
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=(
            f"Question: {question}\n\n"
            f"Reference answer: {expected}\n\n"
            f"System answer: {actual}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_PROMPT,
            response_mime_type="application/json",
            response_schema=Verdict,
            temperature=0,
        ),
    )
    return response.parsed


def latest_run() -> Path:
    """Newest run file by mtime, excluding scorer output and baselines."""
    runs = [
        p for p in eval_settings.results_dir.glob("run_*.json")
        if not p.stem.endswith("_scored")
    ]
    if not runs:
        raise SystemExit(f"no runs found in {eval_settings.results_dir}")
    return max(runs, key=lambda p: p.stat().st_mtime)


def score_run(path: Path, use_judge: bool = True) -> dict:
    run = json.loads(path.read_text(encoding="utf-8"))
    if "results" not in run:
        raise SystemExit(f"{path.name} is not a benchmark run (no 'results' key)")

    expected = answers()
    qs = {q.id: q for q in questions()}

    rows = []
    for r in run["results"]:
        exp = expected.get(r["id"])
        q = qs.get(r["id"])
        if exp is None or q is None:
            continue

        exp_docs = {s.doc for s in exp.support}
        exp_loci = {normalise_locus(s.locus) for s in exp.support}

        cited_docs = {doc_code(c["document"]) for c in r.get("citations", [])}
        cited_loci = {normalise_locus(c["locus"]) for c in r.get("citations", [])}
        retrieved_docs = {doc_code(n["document"]) for n in r.get("retrieved", [])}

        row = {
            "id": r["id"],
            "klass": r["klass"],
            "language": r["language"],
            "expected_decision": exp.response_type,
            "actual_decision": r["decision"],
            "decision_match": r["decision"] == exp.response_type,
            "retrieval_hit": bool(exp_docs & retrieved_docs) if exp_docs else None,
            "retrieval_complete": exp_docs <= retrieved_docs if exp_docs else None,
            "citation_doc_match": bool(exp_docs & cited_docs) if exp_docs else None,
             "citation_locus_match": locus_matches(cited_loci, exp_loci) if exp_loci else None,
            "expected_answer": exp.answer,
            "actual_answer": r.get("answer", ""),
            "error": r.get("error"),
            "answer_correct": None,
            "judge_reason": None,
        }

        if use_judge and exp.response_type == "ANSWER" and r["decision"] == "ANSWER":
            try:
                v = judge(q.text, exp.answer, r.get("answer", ""))
                row["answer_correct"] = v.correct
                row["judge_reason"] = v.reason
            except Exception as exc:  # noqa: BLE001
                row["judge_reason"] = f"judge failed: {exc}"

        rows.append(row)

    return {
        "run_id": run["run_id"],
        "model": run["model"],
        "top_k": run.get("top_k"),
        "rows": rows,
    }


def rate(rows: list[dict], key: str) -> tuple[int, int]:
    vals = [r[key] for r in rows if r[key] is not None]
    return sum(vals), len(vals)


def fmt(hit: int, total: int) -> str:
    if total == 0:
        return "   n/a"
    return f"{hit:3}/{total:<3} {hit / total * 100:5.1f}%"


def report(scored: dict) -> None:
    rows = scored["rows"]
    errored = [r for r in rows if r["error"]]

    print(f"\nrun {scored['run_id']}  model={scored['model']}  "
          f"top_k={scored['top_k']}  n={len(rows)}")

    if errored:
        print(f"\n  !! {len(errored)} questions FAILED to execute. "
              f"Percentages below are not comparable to a clean run.")
        print(f"     first error: {errored[0]['error'][:100]}")

    print("\n=== OVERALL ===")
    for key, label in [
        ("decision_match", "decision correct"),
        ("retrieval_hit", "retrieval: any expected doc"),
        ("retrieval_complete", "retrieval: all expected docs"),
        ("citation_doc_match", "citation: document"),
        ("citation_locus_match", "citation: locus"),
        ("answer_correct", "answer correct (judged)"),
    ]:
        hit, total = rate(rows, key)
        print(f"  {label:32} {fmt(hit, total)}")

    print("\n=== DECISION CONFUSION ===")
    conf = defaultdict(int)
    for r in rows:
        conf[(r["expected_decision"], r["actual_decision"])] += 1
    labels = ["ANSWER", "DECLINE", "CONFLICT", None]
    print(f"  {'expected \\ actual':20}" + "".join(f"{str(a):>10}" for a in labels))
    for e in ["ANSWER", "DECLINE", "CONFLICT"]:
        print(f"  {e:20}" + "".join(f"{conf[(e, a)]:>10}" for a in labels))

    false_answers = [
        r for r in rows
        if r["expected_decision"] == "DECLINE" and r["actual_decision"] == "ANSWER"
    ]
    print(f"\n  FALSE ANSWERS (should have declined): {len(false_answers)}")
    for r in false_answers:
        print(f"    {r['id']} [{r['klass']}] {r['actual_answer'][:70]}")

    false_declines = [
        r for r in rows
        if r["expected_decision"] == "ANSWER" and r["actual_decision"] == "DECLINE"
    ]
    print(f"  FALSE DECLINES (should have answered): {len(false_declines)}")

    print("\n=== BY CATEGORY ===")
    by_klass = defaultdict(list)
    for r in rows:
        by_klass[r["klass"]].append(r)
    print(f"  {'klass':24}{'n':>4}{'decision':>12}{'retr':>10}{'cite doc':>11}{'answer':>10}")

    def pct(t: tuple[int, int]) -> str:
        return f"{t[0]}/{t[1]}" if t[1] else "-"

    for klass in sorted(by_klass, key=lambda k: -len(by_klass[k])):
        rs = by_klass[klass]
        print(f"  {klass:24}{len(rs):>4}"
              f"{pct(rate(rs, 'decision_match')):>12}"
              f"{pct(rate(rs, 'retrieval_hit')):>10}"
              f"{pct(rate(rs, 'citation_doc_match')):>11}"
              f"{pct(rate(rs, 'answer_correct')):>10}")

    print("\n=== FAILURES ===")
    for r in rows:
        if r["error"]:
            continue
        if not r["decision_match"] or r["answer_correct"] is False:
            print(f"  {r['id']} [{r['klass']}] expected={r['expected_decision']} "
                  f"got={r['actual_decision']}")
            if r["answer_correct"] is False:
                print(f"       expected: {r['expected_answer'][:80]}")
                print(f"       got:      {r['actual_answer'][:80]}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_judge = "--no-judge" not in sys.argv

    path = Path(args[0]) if args else latest_run()
    scored = score_run(path, use_judge=use_judge)
    report(scored)

    out = path.with_name(path.name.replace("run_", "scored_"))
    out.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()