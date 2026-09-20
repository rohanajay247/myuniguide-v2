"""Graph nodes. Each is a plain function: state in, partial state out.

Every node is traced. The decorator is a no-op when Langfuse keys are absent,
so the system runs identically without a tracing backend.
"""

from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from myuniguide.config import settings
from myuniguide.generate.answer import generate
from myuniguide.retrieve.search import retrieve
from myuniguide.schemas import AnswerResponse, Decision
from myuniguide.tracing import observe, update_generation


class ConflictCheck(BaseModel):
    apparent_conflict: bool = Field(
        description="True if two retrieved provisions appear to state "
                    "incompatible rules on the same question"
    )
    reason: str


class OverrideRuling(BaseModel):
    is_genuine_conflict: bool = Field(
        description="True only if no override rule resolves the tension"
    )
    rule: str = Field(
        description="lex_specialis | lex_posterior | lex_superior | "
                    "abweichungsbefugnis | none"
    )
    prevailing: str = Field(description="Which provision prevails, and why")


TRIAGE_PROMPT = """You inspect retrieved provisions from German university
examination regulations and decide whether any two of them appear to state
incompatible rules on the same question.

Provisions from DIFFERENT universities are never in conflict. Each university's
regulations are a separate legal instrument governing only that university.
Velmora documents (V-prefixed) and Rheinmark documents (R-prefixed) cannot
contradict each other, no matter how different their rules are.

Apparent incompatibility within ONE university is enough at this stage — do not
attempt to resolve it. Different provisions covering different topics are not a
conflict."""

DISCRIMINATOR_PROMPT = """Two provisions of German university examination
regulations appear to conflict. Decide whether one legitimately overrides the
other, or whether this is a genuine unresolvable conflict.

FIRST: if the provisions belong to different universities (V-prefixed documents
are Hochschule Velmora, R-prefixed are Hochschule Rheinmark), there is no
conflict at all. Set is_genuine_conflict=false and rule="none". Separate
institutions with different rules are not contradicting each other.

Within one university, an override applies ONLY when you can name the mechanism:

- lex specialis: a programme-specific regulation (FSB, BSPO, authority 2)
  prevails over a general one (APO, ASPO, authority 1) on the same matter —
  AND the general regulation does not reserve that matter to itself
- abweichungsbefugnis: the general regulation contains an explicit clause
  permitting deviation on this specific matter. Quote it, or the rule does
  not apply.
- lex posterior: one provision is a named amendment to the other. An
  amendment relationship must be visible in the text.
- lex superior: applies only where no more specific rule governs

Set is_genuine_conflict=true when ALL of these hold:
- both provisions belong to the SAME university
- both sit at the SAME authority level
- no amendment relationship connects them
- you cannot point to the specific clause that authorises the deviation

Do not resolve a tension by reasoning about which rule seems more sensible.
If the mechanism is not present in the text, it is a genuine conflict."""

@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(api_key=settings.google_api_key)


def _structured(system: str, content: str, schema: type[BaseModel]):
    response = _client().models.generate_content(
        model=settings.llm_model,
        contents=content,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0,
        ),
    )
    update_generation(settings.llm_model, getattr(response, "usage_metadata", None))
    return response.parsed


def _context(nodes) -> str:
    blocks = []
    for i, n in enumerate(nodes, start=1):
        m = n.metadata
        blocks.append(
            f"[{i}] document={m.get('document')} type={m.get('doc_type')} "
            f"authority={m.get('authority')} section={m.get('section')}\n"
            f"{n.get_content()}"
        )
    return "\n\n---\n\n".join(blocks)


@observe("retrieve")
def retrieve_node(state: dict) -> dict:
    return {"nodes": retrieve(state["question"])}


@observe("triage")
def triage_node(state: dict) -> dict:
    """Cheap check: is there anything that looks like a contradiction?"""
    check = _structured(
        TRIAGE_PROMPT,
        f"Question: {state['question']}\n\nProvisions:\n\n{_context(state['nodes'])}",
        ConflictCheck,
    )
    return {"apparent_conflict": bool(check and check.apparent_conflict)}


@observe("discriminate")
def discriminate_node(state: dict) -> dict:
    """Resolve the tension: legitimate override, or genuine conflict?"""
    ruling = _structured(
        DISCRIMINATOR_PROMPT,
        f"Question: {state['question']}\n\nProvisions:\n\n{_context(state['nodes'])}",
        OverrideRuling,
    )
    if ruling is None:
        return {"override_rule": None}
    return {
        "override_rule": None if ruling.is_genuine_conflict else ruling.rule,
        "prevailing": ruling.prevailing,
    }


@observe("synthesise")
def synthesise_node(state: dict) -> dict:
    """Produce the answer. If an override resolved the tension, say which rule."""
    question = state["question"]
    rule = state.get("override_rule")

    if rule and rule != "none":
        question = (
            f"{question}\n\n[The apparent contradiction in these provisions is a "
            f"legitimate override under {rule}: {state.get('prevailing', '')}. "
            f"Answer with the prevailing rule. Do NOT report a conflict.]"
        )

    response = generate(question, state["nodes"])

    # A resolved override must never surface as CONFLICT.
    if rule and rule != "none" and response.decision == Decision.CONFLICT:
        response = AnswerResponse(
            decision=Decision.ANSWER,
            answer=response.answer,
            citations=response.citations,
            conflicts=[],
        )
    return {"response": response}


def route_after_triage(state: dict) -> str:
    return "discriminate" if state.get("apparent_conflict") else "synthesise"