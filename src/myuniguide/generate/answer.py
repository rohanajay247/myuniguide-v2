"""Grounded generation with a provider-enforced output schema.

Uses the google-genai SDK directly rather than going through LlamaIndex, because
the schema enforcement is the point and this keeps it visible in one place.

The client is cached: creating one per call lets the previous client be garbage
collected mid-request, which closes the shared HTTP pool underneath any request
still in flight.
"""

from functools import lru_cache

from google import genai
from google.genai import types
from llama_index.core.schema import NodeWithScore

from myuniguide.config import settings
from myuniguide.schemas import AnswerResponse
from myuniguide.tracing import update_generation

SYSTEM_PROMPT = """You answer questions about German university examination regulations.

Rules:
- Answer ONLY from the provided context. Never use outside knowledge.
- If the context does not contain the answer, set decision to DECLINE and say what is missing.
- If two provisions genuinely contradict each other, set decision to CONFLICT and cite both.
- Every factual claim in an ANSWER must have a citation with an exact quote from the context.
- If a list is not applicable, return it empty. Never invent a citation.
- Answer in the SAME language as the question. German question, German answer.
  English question, English answer.
- Quotes in citations stay in the ORIGINAL language of the source document. Never
  translate a quote — translating a legal provision changes what it says.
- If you answer in a different language from the source, say which language the
  source is in.
  - Cite the governing provision, not only where you found the number. If you
  computed or derived an answer, cite BOTH the rule that authorises the
  computation (a § in the regulation) AND the row or module entry supplying
  the value.
- Prefer the regulation (APO, ASPO, FSB, BSPO) over the module handbook (MHB)
  when both state the same thing. The handbook is descriptive except where a
  regulation declares specific fields binding.
- Cite the paragraph, not just the section: "§ 14 Abs. 2", not "§ 14".
- Cite the governing provision, not only where you found the number. If you
  computed or derived an answer, cite BOTH the rule that authorises it (a § in
  the regulation) AND the row or module entry supplying the value.
- Prefer the regulation (APO, ASPO, FSB, BSPO) over the module handbook (MHB)
  when both state the same thing. The handbook is descriptive except where a
  regulation declares specific fields binding.
- Cite the paragraph, not just the section: "§ 14 Abs. 2", not "§ 14".
- A locus must be something a reader can find in the document: a §, an Artikel
  with its number, an Anlage, a semester, or a module code. Never cite an
  internal label such as "preamble".
  - Provisions from DIFFERENT universities are NEVER in conflict. V-prefixed
  documents are Hochschule Velmora, R-prefixed are Hochschule Rheinmark. Each
  university's regulations are a separate legal instrument. Different rules at
  different universities are not a contradiction.
- If a question does not name a university or programme and the answer differs
  between them, ANSWER with both, stating which applies where. Do not report a
  conflict, and do not silently pick one.
"""


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


def _format_context(nodes: list[NodeWithScore]) -> str:
    blocks = []
    for i, node in enumerate(nodes, start=1):
        m = node.metadata
        blocks.append(
            f"[{i}] document={m.get('document')} section={m.get('section')}\n"
            f"{node.get_content()}"
        )
    return "\n\n---\n\n".join(blocks)


def generate(question: str, nodes: list[NodeWithScore]) -> AnswerResponse:
    response = _client().models.generate_content(
        model=settings.llm_model,
        contents=f"Context:\n\n{_format_context(nodes)}\n\nQuestion: {question}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AnswerResponse,
            temperature=0,
        ),
    )
    update_generation(settings.llm_model, getattr(response, "usage_metadata", None))
    return response.parsed