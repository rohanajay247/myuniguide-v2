"""State passed between graph nodes.

LangGraph threads one dict through every node; each node reads what it needs
and writes its own keys. Keeping it typed makes the flow readable and shows up
per-node in tracing.
"""

from typing import TypedDict

from llama_index.core.schema import NodeWithScore

from myuniguide.schemas import AnswerResponse


class GraphState(TypedDict, total=False):
    question: str
    nodes: list[NodeWithScore]
    apparent_conflict: bool
    override_rule: str | None
    prevailing: str
    response: AnswerResponse