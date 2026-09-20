"""The LangGraph flow.

    retrieve -> triage -> [apparent conflict?]
                            no  -> synthesise
                            yes -> discriminate -> synthesise

The discriminate branch exists because the system had started over-calling
CONFLICT once it saw more context: it spotted real tensions between provisions
but reported them instead of resolving them under the override rules that
German examination regulations define.
"""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from myuniguide.graph.nodes import (
    discriminate_node,
    retrieve_node,
    route_after_triage,
    synthesise_node,
    triage_node,
)
from myuniguide.graph.state import GraphState
from myuniguide.schemas import AnswerResponse
from myuniguide.tracing import observe


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(GraphState)

    g.add_node("retrieve", retrieve_node)
    g.add_node("triage", triage_node)
    g.add_node("discriminate", discriminate_node)
    g.add_node("synthesise", synthesise_node)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "triage")
    g.add_conditional_edges(
        "triage",
        route_after_triage,
        {"discriminate": "discriminate", "synthesise": "synthesise"},
    )
    g.add_edge("discriminate", "synthesise")
    g.add_edge("synthesise", END)

    return g.compile()


@observe("answer")
def answer(question: str) -> tuple[AnswerResponse, dict]:
    """Run one question through the graph. Returns the response and final state."""
    state = build_graph().invoke({"question": question})
    return state["response"], state