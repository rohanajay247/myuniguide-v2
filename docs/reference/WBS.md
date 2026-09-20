# MyUniGuide V2 — Work Breakdown Structure

| | |
|---|---|
| **Document** | Work Breakdown Structure (WBS) |
| **Version** | 1.0 |
| **Status** | Draft for approval |
| **Date** | 8 October 2025 |
| **Companion document** | MyUniGuide V2 — Business Requirements Document |
| **Implementation** | Rohan Ajay, in Cursor. Claude advises and explains; Claude does not write system code. |

---

## 1. How to read this

Six phases, 31 work packages. Each package has a single deliverable and an **exit criterion** that is checkable, not a judgement call. A package is done when its exit criterion is met, not when it feels finished.

**Effort bands** are indicative solo-developer ideal hours, assuming the tooling is new: **S** 2–4 h · **M** 5–10 h · **L** 12–20 h · **XL** 25 h+. Treat them as relative weights. Total is roughly 210–280 hours excluding Phase 5.

**Learning objective** is named per phase because framework exposure is a project goal (BRD G3), not a side effect.

### 1.1 Sequencing principle

> Build the eval harness before tuning the retriever.

V1's problem was not its pipeline. It was being unable to see what the pipeline was doing. Phase 0 therefore produces working measurement and two baseline scores *before* a single retrieval decision is made. Every subsequent number is a delta against something recorded.

### 1.2 Gates

| Gate | Condition | Blocks |
|---|---|---|
| **G-1** | Scoring harness proven against a stub system, and both baselines recorded | All of Phase 2 onward |
| **G-2** | Blind re-derivation of benchmark answers complete (BRD R1) | Any number being treated as a *result* — not any commit |
| **G-3** | D-01 closed | WP-1.4 and everything downstream of the metadata schema |
| **G-4** | D-02 closed | WP-0.4 |
| **G-5** | D-03 closed | WP-1.4 module table schema, WP-2.5 |
| **G-6** | Ablation suite complete | Any claim about *why* V2 works |

### 1.3 Critical path

`WP-0.2 → WP-0.4 → WP-1.1 (D-01) → WP-1.4 → WP-1.5 → WP-2.2 → WP-3.2 → WP-4.1 → WP-4.3 → WP-4.4`

Everything else can slip without moving the end date. WP-1.4 (metadata schema) and WP-1.5 (version resolution) are the two packages where a defect propagates into every downstream metric — budget review time there, not elsewhere.

---

## 2. Phase 0 — Foundations and measurement scaffolding

**Learning objective:** evaluation-first engineering; Ragas; Langfuse; experiment discipline.
**Phase exit:** G-1 passed. Two baseline scores exist for all 72 questions, produced by the same harness the final system will use.

| ID | Package | Deliverable | Exit criterion | Depends on | Size |
|---|---|---|---|---|---|
| WP-0.1 | Repo and environment | Python project with pinned dependencies, task runner, pre-commit, Docker Compose for Qdrant and Langfuse, config layer with no absolute paths | `make setup && make check` succeeds from a clean clone; Qdrant and Langfuse reachable | — | S |
| WP-0.2 | Corpus intake and ground-truth loading | Typed loaders for `document_manifest`, `version_relationships`, `dependency_map`, `module_data`, `benchmark_questions`, `benchmark_answers`, `intentional_conflicts`, `abbreviations`; a **question inventory** giving the exact count per category; V1's false-answer rate extracted from the V1 report as the SC-6 reference | All ground-truth files load into typed objects; inventory table committed; SC-6 baseline number recorded | WP-0.1 | M |
| WP-0.3 | Corpus isolation harness | Process/module boundary separating the system under test from `ground_truth/` and `_source/`, plus a test that fails the build if the answer path can reach either | Test present, passing, and demonstrated to fail when deliberately violated | WP-0.1 | S |
| WP-0.4 | Scoring harness | Implementation of every metric in BRD §9: per-category scoring, K∪O three-way confusion matrix, set-F1 for aggregation, decline/false-decline, citation resolvability and version-correctness, decoy citation rate, conditioned conflict reporting | Harness scores a **stub system** with hand-written outputs and returns the arithmetically expected metrics for a perfect stub, an all-DECLINE stub and a deliberately-wrong stub | WP-0.2, G-4 | L |
| WP-0.5 | Run registry, tracing and cost accounting | Langfuse wired; every run tagged with run id, git SHA, model ids, config hash; token and cost totals per run; results persisted to a comparable store | Two runs of the stub appear in the registry with distinct ids and correct cost totals; cost ceiling per full run agreed and recorded | WP-0.1 | M |
| WP-0.6 | **Baseline 1 — long context** | Full 296-page corpus in a single context window, answering all 72 questions through the standard harness | Scored, traced, cost-recorded, committed as `baseline-longcontext` | WP-0.4, WP-0.5 | M |
| WP-0.7 | **Baseline 2 — naive RAG** | Default LlamaIndex ingestion, dense-only, no metadata, no version model, fixed top-k | Scored, traced, cost-recorded, committed as `baseline-naive` | WP-0.4, WP-0.5 | M |
| WP-0.8 | Blind re-derivation of answers (**G-2**) | Independent re-derivation from the PDFs alone of all K-items, all A-items and a stratified ≥30% sample of the remainder; discrepancy log; corrections applied to the source layer and PDFs regenerated if needed | Sample re-derived without consulting `benchmark_answers`; every discrepancy adjudicated and closed | WP-0.2, WP-0.3 | L |

**Note on WP-0.8:** this is the only package that can invalidate everything else. It does not block the first commit, but no number produced before it is complete may be quoted as a result. Run it in parallel with Phase 1 if the schedule tightens — do not run it after Phase 4.

---

## 3. Phase 1 — Ingestion and data model

**Learning objective:** Docling; custom LlamaIndex node parsing; Qdrant payload design. This phase is where five of the twelve V1 problems are fixed once and for all, at zero query-time cost.

**Phase exit:** ingestion audit reconciles against `CORPUS_MANIFEST.md`; version resolution passes all 12 personas as a standalone unit.

| ID | Package | Deliverable | Exit criterion | Depends on | Size |
|---|---|---|---|---|---|
| WP-1.1 | **Close D-01** — version-applicability model | Decision record: chosen model, rejected options, rationale, and the schema implication | Written, dated, committed. G-3 passed. | WP-1.2 spike findings | S |
| WP-1.2 | Docling parsing spike and quality report | Parse of all 19 PDFs; quality report covering § / Artikel boundary detection, numbered-list integrity, table extraction, bilingual column handling, and the two amendment styles (Artikel-structured Velmora vs §-structured Rheinmark) | Section count per document matches the manifest for all 19; zero split numbered lists in a manual audit of 20 sampled lists | WP-0.1 | L |
| WP-1.3 | Custom node parser | LlamaIndex node parser chunking on section boundaries, never splitting a numbered list, never merging two provisions | Chunk-boundary test suite passes; chunk count per document recorded and stable across two runs | WP-1.2 | L |
| WP-1.4 | Metadata schema and population | Schema per FR-1.3 — university, programme, document family and id, authority level, paragraph locus, language and authoritative flag, effective dates, applicable state(s), amendment operation refs — plus the **structured module table** (FR-1.4, 108 modules) | Every chunk validates against the schema; module table row count = 108 and reconciles against `module_data`; state tags reproduce the 6-state model | WP-1.3, G-3, G-5 | L |
| WP-1.5 | Version resolution module | Standalone deterministic resolver: (programme, cohort, matriculation date, election status, as-of date) → one of six states. Implements independent amendment resolution and all three transitional mechanisms. | **12/12 personas resolve correctly** as a unit test, with no retrieval involved. A deliberate "chain" implementation must fail at least one persona — proving the test discriminates. | WP-0.2 | L |
| WP-1.6 | Cross-reference resolution | Reference extractor resolving intra- and cross-document references, including R7's cross-language abbreviation references | All references resolve to a target chunk or appear in an explicit unresolved list; unresolved list reviewed and each entry justified | WP-1.4 | M |
| WP-1.7 | Ingestion pipeline and Qdrant collections | End-to-end deterministic ingest into Qdrant with hybrid-ready payloads; ingestion audit report | Two ingest runs produce identical chunk ids and metadata (NFR-2); audit report reconciles against `CORPUS_MANIFEST.md` | WP-1.4, WP-1.6 | M |

---

## 4. Phase 2 — Retrieval

**Learning objective:** Qdrant hybrid search and payload filtering; multilingual embeddings; cross-encoder reranking; retrieval-level evaluation independent of generation.

**Phase exit:** retrieval-only metrics recorded; decoy retrieval rate measured before and after metadata filtering.

| ID | Package | Deliverable | Exit criterion | Depends on | Size |
|---|---|---|---|---|---|
| WP-2.1 | Hybrid retrieval | Dense + BM25 fusion over multilingual embeddings | Retrieval-only recall@k recorded for all 72 questions; hybrid beats dense-only on the same set | WP-1.7, G-1 | M |
| WP-2.2 | State-aware metadata pre-filtering | Filter applied **before** ranking, driven by the resolved state from WP-1.5 | **State-purity of the retrieved set ≥ 95%**; decoy retrieval rate for the consolidated Lesefassung drops measurably against WP-2.1 — this number is the headline evidence that the version model works | WP-2.1, WP-1.5 | M |
| WP-2.3 | Cross-encoder reranking | Multilingual reranker over the filtered candidate set | Recall@5 after rerank ≥ recall@20 before rerank | WP-2.2 | M |
| WP-2.4 | Retrieval evaluation and tuning | Retrieval-only report: recall@k, state purity, decoy rate, near-duplicate discrimination across the 9 near-duplicate sets | Report committed; tuning decisions recorded with the number that justified each | WP-2.3 | M |
| WP-2.5 | Aggregation path | Per D-03: intent router → deterministic query over the module table (primary) or exhaustive metadata-filtered fetch with no top-k (fallback) | Aggregation questions return **complete** sets; a completeness assertion fails loudly rather than returning a partial answer | WP-1.4, G-5 | L |

---

## 5. Phase 3 — Orchestration and answer synthesis

**Learning objective:** LangGraph stateful graphs; explicit decision policy; abstention. Deliberately deferred to here so LangGraph is learned when conflict detection actually needs it, not before.

**Phase exit:** end-to-end system answers all 72 questions with per-node traces.

| ID | Package | Deliverable | Exit criterion | Depends on | Size |
|---|---|---|---|---|---|
| WP-3.1 | Graph skeleton | LangGraph flow: intake → context extraction → version resolution → intent routing (factual / aggregation / comparison) → retrieval → synthesis | Graph executes all 72 questions without error; each node emits a trace span | WP-2.4, WP-2.5 | M |
| WP-3.2 | Override-vs-conflict discriminator | Node classifying apparent contradictions using lex specialis / lex posterior / lex superior / Abweichungsbefugnis, and emitting which rule it applied | On the 12 K∪O items the node produces a label and a named rule for each; rule attribution reviewed by hand | WP-3.1 | L |
| WP-3.3 | Decision policy | ANSWER / DECLINE / CONFLICT emission with an explicit abstention rule, and conditional multi-state answering when the context is underspecified (FR-2.4) | All 8 absence cases route to DECLINE; a deliberately underspecified persona query yields a conditional multi-state answer, not a silent default | WP-3.2 | M |
| WP-3.4 | Citation assembly and validation | Citations carrying document id, state and locus; programmatic validation of resolvability and state-applicability | Zero unresolvable citations across a full run; citation version-correctness measured | WP-3.3, WP-1.6 | M |
| WP-3.5 | Language-authority handling | German-authoritative V5 with translation divergence flagged; English-authoritative R7 | The planted translation divergence is flagged when it affects the answer; R7 answers cite the English text as authority | WP-3.4 | S |

---

## 6. Phase 4 — Evaluation, attribution and write-up

**Learning objective:** Ragas; ablation design; honest reporting.
**Phase exit:** BRD §9 primary gates assessed; G-6 passed; write-up complete.

| ID | Package | Deliverable | Exit criterion | Depends on | Size |
|---|---|---|---|---|---|
| WP-4.1 | Full benchmark run #1 and failure taxonomy | Complete scored run; every failure classified by cause — parse, chunk, metadata, state resolution, retrieval, discrimination, synthesis, citation | Run recorded; every failure assigned exactly one primary cause; causes tallied | WP-3.5, G-2 | M |
| WP-4.2 | Targeted iteration | **Maximum three** tuning cycles, each fixing the largest cause category from WP-4.1 and re-running. A held-out slice is excluded from tuning (BRD R8). | Each cycle recorded as a separate run id with a one-line hypothesis and the resulting delta; held-out scores reported separately | WP-4.1 | L |
| WP-4.3 | Ablation suite (**G-6**) | Five ablations: metadata filter off; rerank off; dense-only; version resolution off; aggregation path off | Each ablation scored through the same harness; per-component contribution table produced | WP-4.2 | M |
| WP-4.4 | Comparison and results analysis | V2 vs `baseline-longcontext`, vs `baseline-naive`, and against the V1 failure profile; per-category deltas; cost per run alongside accuracy | BRD §9 primary gates SC-1…SC-7 each marked pass or fail with the supporting number. **SC-7 is the one that decides whether V2 avoided V1's central weakness.** | WP-4.3 | M |
| WP-4.5 | Documentation and write-up | README with reproduction steps; architecture document; results write-up; limitations section carrying BRD R1–R8 verbatim in substance; decision records D-01…D-03; framework retrospective for G3 | A reader can reproduce a recorded run from the README alone; every quantitative claim links to a run id | WP-4.4 | L |

---

## 7. Phase 5 — Stretch (only if Phases 0–4 are complete)

| ID | Package | Deliverable | Size |
|---|---|---|---|
| WP-5.1 | Real-PDF robustness spike | Ingest one genuine Prüfungsordnung (Word export or scan); report where the clean-text-layer assumption breaks (BRD R2) | M |
| WP-5.2 | Nice-to-have items | The four deferred items from the V1 audit | L |
| WP-5.3 | Minimal query interface | Thin UI over the graph, showing state resolution and citations | M |
| WP-5.4 | Staleness detection | Generalise the version model into a "is this document superseded?" check — the capability whose absence caused V1's undocumented failure | M |

---

## 8. Effort summary

| Phase | Packages | Band total | Indicative hours |
|---|---|---|---|
| 0 — Foundations and measurement | 8 | 2S · 4M · 2L | 45–65 |
| 1 — Ingestion and data model | 7 | 1S · 2M · 4L | 65–90 |
| 2 — Retrieval | 5 | 4M · 1L | 32–50 |
| 3 — Orchestration | 5 | 1S · 3M · 1L | 29–44 |
| 4 — Evaluation and write-up | 5 | 3M · 2L | 39–60 |
| **Total (0–4)** | **30** | | **210–310** |
| 5 — Stretch | 4 | | 40–60 |

---

## 9. Standing rules

1. **No retriever tuning before G-1.** Numbers on the board first.
2. **No result quoted before G-2.** Commits are fine; claims are not.
3. **One hypothesis per run.** A run that changes two things attributes nothing.
4. **Every tuning decision cites the number that justified it.** If there is no number, it is a preference, and it goes in the decision log as one.
5. **When a framework fights back, time-box it and take the boring option.** G3 is exposure to the tooling, not mastery of it (BRD R5).
6. **Ingestion defects are fixed upstream.** Corpus stays frozen and regenerable; never hand-patched.
7. **Metric definitions freeze at BRD sign-off.** Metrics redefined after results exist are not results.
