# Reference — Portfolio context

Background on why this project exists and where it sits in the wider portfolio.

## Position

M.Sc. Industrial Artificial Intelligence, Hochschule Albstadt-Sigmaringen.
Previously Frontend Engineer at Viamagus Technologies, Bengaluru (2025–2026):
VR industrial platform for oil & gas, conversational AI assistant with voice and
text, remote scientific experiment platform, warehouse automation platform, AMR
interface, real-time mission tracking, WebSocket updates, dashboards.

Target positioning: *software engineer transitioning into AI engineering, with
experience building practical AI systems, RAG applications, agents, APIs and
business automation.* Not "beginner AI developer."

Applying for: Werkstudent AI, AI Automation, Agentic AI, AI Engineering, GenAI,
RAG, software/AI hybrid, Industrial AI. Germany, based in Albstadt, German A2 —
so remote/hybrid and English-working roles. The portfolio compensates for the
language constraint by demonstrating practical capability.

## Portfolio arc

Software engineering → GenAI → RAG → production RAG → agents → tools/MCP →
evaluation → observability → business automation → industrial AI.

The goal is not twenty projects. It is visible increasing technical maturity.

## Project set

1. **MyUniGuide V2** — production-oriented RAG *(this project)*
2. **Expense Intelligence** — invoice PDF → OCR/extraction → Pydantic schema →
   vendor extraction → expense classification → policy RAG → decision →
   human approval → n8n. Target 2–4 days.
3. **MCP Operations Agent** — agent → MCP → business tools → results → agent →
   human approval for write actions. Target 3–4 days.
4. **Claude Vitals** — github.com/rohanajay247/claude-vitals. Open-source Python
   Windows utility for monitoring Claude usage limits. Developer tooling. Do not rebuild.
5. **MyUniGuide V1** — github.com/rohanajay247/myuniguide. Fundamentals, historical progression.

Also: RoomEase, InsightFlow — broader software experience, should not dominate.

Existing n8n work: AI lead/spam classifier, Gmail assistant, LinkedIn data
automation, maintenance RAG assistant. No more trivial n8n projects needed.

## The story

> I originally built MyUniGuide as a RAG system to help international students
> navigate German university regulations. That first version taught me the
> fundamentals, but I was building too much infrastructure myself. For V2 I
> rebuilt the system around frameworks used in modern AI engineering —
> LlamaIndex for retrieval, Qdrant for vector search, LangGraph for stateful
> orchestration, Ragas for evaluation, Langfuse for observability.
>
> I specifically experimented with hybrid retrieval and reranking and measured
> whether they actually improved retrieval quality.
>
> I also added structured outputs, conflict detection and explicit decline
> behaviour instead of letting the LLM answer everything.

## Framework priorities

**Tier 1 — actively use:** LangGraph, LlamaIndex, Qdrant, Ragas, Langfuse,
Pydantic, FastAPI, Docker.
**Tier 2 — learn through the project:** Docling, BM25, hybrid search, reranking,
structured outputs, tool calling, evaluation datasets, latency and cost tracking.
**Tier 3 — awareness only, no separate projects:** CrewAI, AutoGen, PydanticAI,
OpenAI Agents SDK, DSPy, Haystack, A2A.
**Later:** fine-tuning, LoRA/QLoRA, PyTorch, advanced MLOps, Kubernetes, multimodal.

Principle: use frameworks to solve real problems, not because the framework is
fashionable.

## What a good README answers

Problem. Architecture. Why these technologies. Evaluation — how do we know it
works. Experiments — what was compared. Reliability — what happens when retrieval
fails or the LLM produces invalid output. Observability — where do latency, cost
and failures come from. Deployment. Limitations. Future work.

Do not fabricate results. If something got worse, document it. That is useful
engineering evidence.

## Working style

Shortest useful explanation, then what to build, then the implementation steps.
Keep the architecture simple. Point out overengineering. Prefer official
documentation; verify APIs that may have changed; never invent APIs. Where there
are several ways to implement something, recommend one and explain why.
