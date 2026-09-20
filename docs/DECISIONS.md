# Decision Log

## D-01 — Version-applicability model
**Status:** DEFERRED to backlog.

The corpus models six resolved states (ASPO A/B/A0/B0, APO P/Q) with amendments that
resolve independently rather than as a chain. Building the resolver is the single largest
time sink in the design and it does not appear in the portfolio story.

**Consequence:** two of the four genuine conflicts are version-gated and become ambiguous
without state resolution. Conflict detection is therefore scored on the two non-version-gated
conflicts plus the eight legitimate overrides — ten items, still a real discrimination metric.

**Must be stated in the README as a known limitation.**

## D-02 — Conflict scoring rule
**Status:** DECIDED.

With genuine conflicts and legitimate overrides in the same corpus, a system flagging
everything as a conflict achieves perfect recall. Recall alone is not a valid metric.

Score the K-items and O-items together as one three-way classification:
CONFLICT / OVERRIDE-RESOLVED / neither. Report the confusion matrix, not a single number.

## D-03 — Aggregation strategy
**Status:** OPEN — decide by Day 3.

Aggregation needs completeness. Top-k similarity retrieval cannot guarantee it at any k.
This was one of V1's two headline failures and is currently not in the MVP checklist.

Options: (a) build a structured module table at ingest and route aggregation queries to it;
(b) exhaustive metadata-filtered fetch with no top-k; (c) ship without it and say so.

Option (c) is defensible. Silence is not.

## D-04 — Corpus choice
**Status:** DECIDED.

Use the 19-PDF synthetic corpus and its 72 labelled questions, not V1's 50-question set.
V1's questions were written against V1's real documents and do not apply here.

The synthetic corpus is validated, has per-category ground truth, and costs nothing more to
produce. The "why synthetic" question has a strong answer: it was built to isolate specific
failure modes that real documents cannot isolate.

## D-05 — No V1-to-V2 accuracy comparison
**Status:** DECIDED.

Different corpus, different questions. "V1 84% to V2 X%" is not a comparable number and an
informed reader will spot it immediately. Compare V2 against baselines on the *same* corpus:
a naive dense-only RAG, and a long-context baseline over the full 296 pages.

The long-context baseline is non-negotiable. V1's most interesting finding was that it tied
one; not checking again would repeat the mistake.

## D-06 — LLM and embedding provider
**Status:** DECIDED.

Gemini, not OpenAI. Existing credits cover it.

- LLM: `gemini-3.5-flash` (GA since May 2026)
- Embeddings: `gemini-embedding-2` (GA since August 2026, replaces `gemini-embedding-001`)
- SDK: `google-genai`, used directly in `generate/answer.py` for schema enforcement
- LlamaIndex integrations: `llama-index-embeddings-google-genai`, `llama-index-llms-google-genai`

**Consequence 1 — the cost ceiling disappears.** This mainly matters for the long-context
baseline over all 296 pages, which was the most expensive planned run and is now effectively
free. That baseline stays non-negotiable.

**Consequence 2 — schema constraints.** Gemini's `response_schema` does not support Optional
fields, unions, or `default_factory`. `schemas.py` is therefore flat: every field required,
lists returned empty rather than absent.

**Consequence 3 — vector dimension is tied to the embedding model.** Changing
`EMBEDDING_MODEL` requires dropping the Qdrant collection first. `drop_collection()` in
`ingest/index.py` exists for this.

**Still worth doing on Day 8:** run the benchmark on a second model (`gemini-3.8-flash`, or
`gemini-3.1-flash-lite` at the cheap end). One command, one extra row, and "here is what the
cheaper model costs you in accuracy" is a question senior people actually ask.
