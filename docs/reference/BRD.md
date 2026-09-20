# MyUniGuide V2 — Business Requirements Document

| | |
|---|---|
| **Document** | Business Requirements Document (BRD) |
| **Project** | MyUniGuide V2 — RAG QA over German examination regulations |
| **Version** | 1.0 |
| **Status** | Draft for approval |
| **Date** | 8 October 2025 |
| **Owner / Implementer** | Rohan Ajay |
| **Predecessor** | MyUniGuide V1 — github.com/rohanajay247/myuniguide |
| **Companion document** | MyUniGuide V2 — Work Breakdown Structure |

---

## 1. Purpose

This document defines what MyUniGuide V2 must do, how its success will be measured, and what is explicitly out of scope. It is the reference against which the Work Breakdown Structure is sequenced and against which the final results write-up is judged.

It does not specify implementation. Three design decisions remain open and are recorded in §11 with the work packages they block.

---

## 2. Background

### 2.1 V1 outcome

V1 scored 84% on a 50-question benchmark over real Prüfungsordnungen. Three findings from the audit matter more than the headline number:

- **Conflict detection was the primary unmet target.** 3/6 against a goal of ≥5/6.
- **Aggregation queries failed** as a category.
- **A long-context baseline scored identically.** V1's measurable contribution was therefore inverting the *failure profile* — changing which questions failed — not improving accuracy. A system that does not beat a naive baseline has not demonstrated that its engineering did anything.

A fourth finding was undocumented at the time: the Master-StuPO in V1's corpus (v22.1) had been superseded by v24.1 roughly two and a half years before V1 was built. V1 had no mechanism to detect this and no concept of "which version applies to whom". It answered confidently from a stale document.

Twelve problems were catalogued from the audit — nine to fix, four nice-to-have. **Five of the twelve are data-modelling or ingestion problems, not retrieval problems.** They are fixed once, upstream, and cost nothing at query time. This is the single highest-leverage observation carried into V2.

### 2.2 Corpus (complete)

A synthetic benchmark corpus is finished and validated: 19 PDFs, 296 pages, generated deterministically from a machine-readable source layer, with 76 audit checks passing and 0 failures. Two fictional universities with genuinely divergent conventions (Hochschule Velmora, LHG Baden-Württemberg; Hochschule Rheinmark, HochSchG Rheinland-Pfalz), four programmes, 108 modules, 72 benchmark questions with authored answers.

The corpus properties that drive the requirements below:

| Property | Consequence for V2 |
|---|---|
| Amendments resolve **independently**, not as a chain — a student who misses amendment 1 by cohort can still receive amendment 2 by date | Six resolved states (ASPO A/B/A0/B0, APO P/Q). A linear "latest version wins" model is wrong by construction. |
| The consolidated Lesefassung is correct for only **one of four** ASPO states, yet is the longest and most retrievable document in its family | Flagship semantic-decoy trap. Similarity retrieval will prefer it. Requires metadata filtering, not better embeddings. |
| ASPO states A and A0 have identical section and paragraph counts but different text | Structural heuristics cannot distinguish states. Applicability must be modelled explicitly. |
| Exactly 4 genuine conflicts, deliberately separable from 8 legitimate overrides, 3 authority cases, 4 version-dependent references, 9 near-duplicate sets, 8 absence cases | Conflict detection is a *discrimination* task, not a detection task. Recall alone is not a valid metric. |
| Two of the four conflicts are version-gated and do not exist for grandfathered cohorts | Conflict correctness is conditional on version resolution being correct first. |
| Three transitional mechanisms: cohort-based, date-based grandfathering, irrevocable written election | Version resolution needs a real rule engine, not a date comparison. |
| Asymmetric language authority: V5 bilingual with German authoritative (plus a planted translation divergence); R7 adopted in English with the **English** text authoritative, citing abbreviations defined only in a German document | Language ≠ authority. Cross-language reference resolution required. |
| As-of date 1 October 2025 (WS 2025/26) | Fixed evaluation datum. |

---

## 3. Goals and non-goals

### 3.1 Goals

- **G1 — Measurably beat V1's specific failure modes** on conflict discrimination, aggregation, and version applicability, without regressing the false-answer rate.
- **G2 — Beat both control baselines** on the same 72 questions. V1's central weakness was that it did not.
- **G3 — Gain hands-on exposure to industry-standard AI engineering tooling.** Framework use is a project objective in its own right, not only a means to G1.
- **G4 — Produce evidence, not assertions.** Every claim in the final write-up traceable to a recorded, reproducible run.

### 3.2 Non-goals

Not failures if absent: a production user interface; authentication or multi-tenancy; ingestion of real university regulations; scaling beyond ~300 pages; model fine-tuning; agentic web retrieval; legal-advice-grade guarantees; German-language UX polish; latency optimisation.

---

## 4. Stakeholders

| Role | Holder | Interest |
|---|---|---|
| Product owner / implementer | Rohan Ajay | All requirements; sole decision authority |
| Technical mentor | Claude | Design review, sequencing, concept explanation; produces planning artefacts, not system code |
| Proxy end user | The 12 benchmark personas | Correct, version-appropriate, cited answers |
| Downstream audience | Portfolio reviewers / hiring readers | Reproducibility and honest limitations |

---

## 5. Scope

**In scope:** ingestion and structural parsing of the 19 corpus PDFs; explicit version-applicability modelling; hybrid metadata-filtered retrieval; a completeness path for aggregation; override-vs-conflict discrimination; ANSWER / DECLINE / CONFLICT decisioning with version-correct citations; a full evaluation harness with baselines and ablations; tracing and cost accounting; documentation and results write-up.

**Out of scope:** everything in §3.2, plus the four nice-to-have items from the V1 audit unless Phase 5 is reached.

---

## 6. Assumptions

- **A1** The corpus is frozen. Any defect found during ingestion is fixed in the source layer and the PDFs regenerated; the corpus is never hand-patched.
- **A2** The 72 authored answers are correct. This assumption is **not yet validated** — see R1 and gate G-2 in the WBS.
- **A3** The as-of date is 1 October 2025 for all evaluation unless a question states otherwise.
- **A4** Local-first infrastructure (Docker Compose) is acceptable; no cloud deployment required.
- **A5** LLM API spend is bounded but real; the cost ceiling is set in WP-0.5.

---

## 7. Functional requirements

### FR-0 — Corpus isolation (hard constraint)

**FR-0.1** The ingestion and answering path may read **only** `/corpus/velmora/` and `/corpus/rheinmark/` — the PDFs. It must never read `/corpus/ground_truth/` or `/corpus/_source/`.

**FR-0.2** The four conflicts, the six resolved states, the amendment operations and the persona resolutions are all *declared* in the source layer. A system that reads them has not solved the problem. The separation must be enforced by an automated test that fails the build, not by convention.

**FR-0.3** The ground-truth tree is available to the evaluation harness only, in a separate process boundary from the system under test.

### FR-1 — Ingestion and data model

**FR-1.1** Parse all 19 PDFs preserving section (§ / Artikel) structure, numbered-list integrity, table structure, and bilingual layout.

**FR-1.2** Chunk on section boundaries. Never split a numbered list across chunks. Never merge two provisions into one chunk.

**FR-1.3** Every chunk carries, at minimum: university, programme(s), document family and document id, authority level, paragraph locus, language and authoritative-text flag, effective dates, applicable version state(s), and any amendment operation that created or modified it.

**FR-1.4** Ingestion emits a **structured module table** (108 modules with their attributes) as a queryable artefact distinct from the text chunks. This is the substrate for aggregation.

**FR-1.5** Ingestion is deterministic and idempotent, and emits an audit report reconcilable against `CORPUS_MANIFEST.md` — document count, page count, section count per document, chunk count per document, orphaned-reference count.

**FR-1.6** Cross-document references (including cross-language abbreviation references, e.g. R7 citing abbreviations defined only in a German document) resolve to a target chunk or are reported as unresolved.

### FR-2 — Version applicability

**FR-2.1** Given a query context (programme, cohort, matriculation date, election status, as-of date), the system resolves exactly one of the six states — ASPO A / B / A0 / B0, APO P / Q.

**FR-2.2** Amendments are evaluated **independently**. Amendment 2 applying does not require amendment 1 to apply.

**FR-2.3** Retrieval is restricted to material applicable in the resolved state before ranking, not filtered after.

**FR-2.4** If the context is underspecified, the system must not silently pick a state. It answers conditionally, naming each state and its answer, or asks for the missing attribute. Silently defaulting to "the newest version" is the V1 failure and is prohibited.

**FR-2.5** The consolidated Lesefassung must never be cited as authority for a state it does not encode.

**FR-2.6** The three transitional mechanisms (cohort, date-based grandfathering, irrevocable election) are all implemented; election status overrides grandfathering where the regulation says so.

### FR-3 — Retrieval

**FR-3.1** Hybrid dense + BM25 retrieval over a multilingual embedding space.

**FR-3.2** Metadata pre-filtering by resolved state, university, programme and authority level applied **before** ranking.

**FR-3.3** Cross-encoder reranking of the filtered candidate set.

**FR-3.4** A separate **exhaustive, metadata-filtered fetch path** with no top-k cut-off, for completeness-sensitive queries. Top-k similarity is structurally incapable of guaranteeing completeness; aggregation must not depend on it.

### FR-4 — Reasoning and decisioning

**FR-4.1** When two provisions appear to contradict, the system classifies the relationship as a **legitimate override** (lex specialis, lex posterior, lex superior, or an exercised Abweichungsbefugnis) or a **genuine conflict**, and states which rule it applied.

**FR-4.2** The system emits exactly one of ANSWER, DECLINE, CONFLICT.

**FR-4.3** DECLINE is emitted when the corpus does not contain the answer. Fabricating an answer for an absence case is the most severe failure class.

**FR-4.4** A CONFLICT output names both provisions, both loci, and why they cannot be reconciled by any override rule.

**FR-4.5** Language authority is respected: German authoritative for V5 (with translation divergence flagged where it affects the answer), English authoritative for R7.

### FR-5 — Citations

**FR-5.1** Every ANSWER cites document id, version/state, and paragraph locus.

**FR-5.2** Citations are validated programmatically: the locus must exist, and the cited document must be applicable in the resolved state.

### FR-6 — Evaluation and observability

**FR-6.1** A harness executes all 72 questions and reports metrics per category, not only in aggregate.

**FR-6.2** Every run is traced end-to-end and cost-accounted, tagged with a run id, git SHA, model identifiers and config hash.

**FR-6.3** Baselines and ablations execute through the same harness and scoring code as the full system.

---

## 8. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Reproducibility.** Pinned dependencies, pinned model versions, fixed seeds, committed configs. Re-running a recorded run id reproduces its metrics within a stated tolerance. |
| NFR-2 | **Determinism of ingestion.** Two ingest runs over the same corpus produce identical chunk ids and metadata. |
| NFR-3 | **Cost ceiling.** A full 72-question run stays within the budget set in WP-0.5. Cost per run is reported alongside accuracy; an accuracy gain bought with a 10× cost increase is reported as such. |
| NFR-4 | **Observability.** 100% of evaluation runs traced. Per-node latency and token counts visible. |
| NFR-5 | **Local-first.** Qdrant and tracing run under Docker Compose; no cloud dependency beyond LLM and embedding APIs. |
| NFR-6 | **Latency.** Measured and reported, not gated. No optimisation work in scope. |
| NFR-7 | **Portability.** No absolute paths; corpus location configurable. |

---

## 9. Success criteria

All metrics are over the 72-question benchmark at the as-of date, scored by the harness in WP-0.4.

### 9.1 Primary gates (V2 is a success only if all pass)

| ID | Criterion | Target | Stretch | V1 reference |
|---|---|---|---|---|
| SC-1 | **Conflict recall** — genuine conflicts (K-01…K-04) reported as CONFLICT | ≥ 3/4 | 4/4 | 3/6 against ≥5/6 |
| SC-2 | **Override precision** — legitimate overrides (O-01…O-08) *not* reported as conflict, and answered with the prevailing rule | ≥ 7/8 | 8/8 | not measured |
| SC-3 | **Version-state resolution** across the 12 personas | ≥ 11/12 | 12/12 | no such capability |
| SC-4 | **Aggregation** — exact set match on aggregation questions | ≥ 80% | ≥ 90% | category failed |
| SC-5 | **Absence handling** — absence cases (A-01…A-08) correctly DECLINEd | ≥ 7/8 | 8/8 | to be read from V1 report |
| SC-6 | **False-answer rate** — confident wrong ANSWER on any question | ≤ V1's measured rate | strictly below | measured in WP-0.2 |
| SC-7 | **Beats both baselines** — overall accuracy exceeds long-context and naive-RAG baselines by > 10 points, *and* exceeds both on the conflict and version categories specifically | required | — | V1 tied its baseline |

SC-1 and SC-2 are scored together as a single discrimination task over the 12 K∪O items; reporting either alone is invalid. See D-02.

### 9.2 Secondary metrics (reported, not gated)

- **Decoy citation rate** — proportion of answers citing the consolidated Lesefassung for a state it does not encode. Target < 5%. This is the direct measure of the corpus's flagship trap.
- **Citation version-correctness** — cited document applicable in the resolved state. Target ≥ 95%.
- **False-decline rate** — DECLINE on an answerable question. Target ≤ 5%. Guards against passing SC-5 by declining everything.
- **Retrieval recall@k** and **state-purity of the retrieved set** (proportion of retrieved chunks applicable in the resolved state).
- **Cost and token count per run.**

### 9.3 Learning goal completion (G3)

Demonstrably used, with a written note on what each was good and bad for: Docling, LlamaIndex (custom node parser + retrieval), LangGraph (stateful decision graph), Qdrant (hybrid + payload filtering), Ragas, Langfuse.

---

## 10. Evaluation design

Three properties distinguish V2's evaluation from V1's:

**Two baselines, run before the system is built.**
- *Baseline 1 — long context:* the whole 296-page corpus in a single context window. This is the control V1 tied with.
- *Baseline 2 — naive RAG:* default LlamaIndex ingestion, dense-only retrieval, no metadata, no version model, fixed top-k. This is the "did my engineering do anything" control.

Both are recorded before any retriever tuning. Numbers on the board first.

**Ablations, run at the end.** With the metadata filter off; with reranking off; with hybrid reduced to dense-only; with version resolution off; with the aggregation path off. Each ablation attributes a share of the delta to a specific engineering decision. V1 could not do this, which is why "84%" carried no information about what caused it.

**Conditioned reporting.** Because two conflicts are version-gated, conflict metrics are reported twice: unconditionally, and conditioned on correct state resolution. This separates "failed to detect the conflict" from "was looking at the wrong version".

---

## 11. Open decisions

These block specific work packages. Each must be closed by its stated gate.

### D-01 — Version-applicability model
**Blocks:** WP-1.4 (metadata schema), and transitively WP-1.6, WP-2.2. **Close by:** end of WP-1.2. **Priority:** highest.

| Option | Description | For | Against |
|---|---|---|---|
| A | Per-chunk `applicable_states` tag set; single index; filter at query time | One index; teaches Qdrant payload filtering; supports "what changed between states" queries; storage-efficient | Filter logic must be exactly right; a bug is silent |
| B | Materialise six document sets as six collections | Retrieval trivially correct once state is known; easy to audit; 6× of 296 pages is negligible | Hides amendment structure; cross-state queries need a separate path; 6× embedding cost and re-index churn |
| C | Validity intervals + amendment operation records, resolved at query time | Most faithful to the legal structure | Most complex; highest risk of being the whole project |

**Recommendation (pending confirmation):** Option A, with the refinement that chunks whose text is identical across states carry multiple state tags, while chunks whose text differs are duplicated per state. Note that A and A0 have identical structure but different text, so partial duplication is unavoidable under any option. This is Option B stored efficiently: it retains B's auditability, adds A's cross-state query capability, and exercises the payload-filtering skill that is the point of using Qdrant.

### D-02 — Conflict scoring rule
**Blocks:** WP-0.4 (metric implementation). **Close by:** start of WP-0.4.

With 4 genuine conflicts and 8 legitimate overrides, a system reporting 12 conflicts and one reporting 4 both achieve perfect conflict recall. Recall alone reproduces V1's mistake in a new form.

**Recommendation (pending confirmation):** score the 12 K∪O items as one three-way classification — CONFLICT / OVERRIDE-RESOLVED / neither. Headline metric is macro-F1 over {CONFLICT, OVERRIDE}, gated by SC-2 (at most one override misreported as conflict). Report the full 3×3 confusion matrix, and report conditioned on correct version resolution as well as unconditionally.

### D-03 — Aggregation strategy
**Blocks:** WP-1.4 (module table schema) and WP-2.5. **Close by:** end of WP-1.2.

The proposed pipeline does not solve aggregation. Aggregation needs completeness; top-k similarity retrieval cannot guarantee it at any k.

| Option | Description | Assessment |
|---|---|---|
| a | Intent router → deterministic query over the structured module table built at ingest | Correct for module-level aggregation ("how many modules…", "which modules…"); 108 modules is genuinely tabular data |
| b | Intent router → exhaustive metadata-filtered fetch, no top-k, map-reduce synthesis | Needed for aggregations over regulation *text* that has no tabular form |
| c | Large k and trust the LLM | Rejected — this is what V1 did |

**Recommendation (pending confirmation):** (a) as the primary path with (b) as fallback, selected by an intent router. This makes FR-1.4 load-bearing and is a direct instance of the "five of twelve problems are ingestion problems" finding: aggregation is fixed at ingest, not at query time.

---

## 12. Risks and limitations

| ID | Risk / limitation | Impact | Mitigation |
|---|---|---|---|
| R1 | The 72 answers were authored alongside the corpus and machine-checked for structural completeness and citation resolvability, but have **not** been blind re-derived from the PDFs. Errors would be invisible and self-confirming. | Every metric in §9 is unsound | Blind re-derivation of a stratified sample (all K and A items, plus ≥ 30% of the rest) before the first measurement run. Gate G-2. Not required before the first commit. |
| R2 | PDFs are ReportLab-generated with a clean text layer; real Prüfungsordnungen are Word exports or scans. A clean parse proves nothing about real-world robustness. | Overclaiming in the write-up | Stated as a limitation in the results document. Optional Phase 5 spike against one real PDF. |
| R3 | At 296 pages the corpus fits in a long-context window. It tests retrieval *quality*, not retrieval *at scale*. | Result does not generalise to large corpora | Stated explicitly. It is also what makes the long-context baseline possible, which is the point. |
| R4 | The four conflicts are declared in the source layer. | A leak would invalidate the headline result | FR-0, enforced by an automated test that fails the build |
| R5 | Six frameworks are new simultaneously. Framework learning could consume the schedule. | G1 sacrificed to G3 | Sequence them: LlamaIndex first, LangGraph only on reaching conflict detection. Time-box each spike. Prefer the boring option when a framework fights back. |
| R6 | Version resolution is a hard dependency of conflict detection, aggregation and citation correctness. A bug there corrupts every downstream metric. | Systemic | Unit-test against all 12 personas as a standalone module (WP-1.5) before it is wired into the graph |
| R7 | The evaluator and the system may share an LLM and its biases. | Inflated scores | Deterministic scoring wherever the answer is a set, a state, a citation or a label. LLM-as-judge only for free-text justification quality, and flagged as such. |
| R8 | Tuning against a 72-question benchmark risks overfitting to it. | Reported gains do not transfer | Hold out a slice during tuning; report held-out scores separately. Cap tuning cycles (WP-4.2). |

---

## 13. Approval

| Item | Status |
|---|---|
| Scope §5 | Pending sign-off |
| Success criteria §9 | Pending sign-off |
| D-01, D-02, D-03 recommendations §11 | Pending confirmation — WBS assumes recommendations hold |

Once §9 is signed off it is frozen. Metric definitions changed after results exist are not results.
