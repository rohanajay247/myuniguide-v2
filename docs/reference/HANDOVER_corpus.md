# Reference — V2 design and corpus handover

Historical. Describes the completed corpus and the original V2 design intent.
Kept for the corpus properties in section 3, which remain accurate and load-bearing.
The planning approach it describes is superseded by `../BUILD_PLAN.md`.

## 1. Project

MyUniGuide V2 — RAG question answering over German university examination
regulations (Prüfungsordnungen).

## 2. V1 outcome

V1 scored 84% on a 50-question benchmark. Documented failure modes:

- Conflict detection: 3/6 against a goal of >= 5/6
- Aggregation queries failed as a category
- A long-context baseline scored identically, so V1's real contribution was
  inverting the failure profile, not improving absolute accuracy
- Undocumented: the Master-StuPO used (v22.1) had been superseded by v24.1
  roughly two and a half years earlier — a version-staleness failure the
  system had no way to detect

Twelve problems catalogued; 9 to fix, 4 nice-to-have. Five of the twelve are
data-modelling or ingestion problems, not retrieval problems — they cost
nothing at query time.

## 3. The synthetic corpus (complete)

19 PDFs, 296 pages, generated deterministically from a machine-readable source
layer. 76 audit checks pass, 0 failures.

Two fictional universities with divergent conventions:

- **Hochschule Velmora** (Baden-Württemberg, LHG): ECTS-Punkte, Studienleistung,
  Artikel-structured amendments, Senat + Rektorat, exhaustive exam-form catalogue
  after its second amendment, descriptive module handbook
- **Hochschule Rheinmark** (Rheinland-Pfalz, HochSchG): Leistungspunkte,
  Leistungsnachweis, §-structured amendments, Fachbereichsrat + Präsident,
  open catalogue, module handbook binding for three named fields

Four programmes, 108 modules: IAI (M.Sc., English, 90 ECTS, 3 sem),
ET (B.Eng., German, 210 ECTS, 7 sem), SE (M.Sc., German, 120 LP, 4 sem),
IB (B.A., English, 180 LP, 6 sem).

### Critical corpus properties

- Amendments resolve INDEPENDENTLY, not as a chain. A student who missed
  amendment 1 by cohort still gets amendment 2 by date. Six resolved states:
  ASPO A/B/A0/B0 and APO P/Q.
- The consolidated Lesefassung is correct for only ONE of four ASPO states,
  yet it is the longest and most retrievable document in its family. This is
  the corpus's flagship semantic-decoy trap.
- ASPO states A and A0 have identical section and paragraph counts but
  different text — structure alone cannot distinguish them.
- Exactly 4 genuine conflicts (K-01…K-04), separable from 8 legitimate
  overrides, 3 authority cases, 4 version-dependent references, 9 near-duplicate
  sets and 8 absence cases. Two conflicts are version-gated and do not exist
  for grandfathered cohorts.
- Three transitional mechanisms: cohort-based, date-based grandfathering,
  and irrevocable written election.
- Language authority is asymmetric: V5 is bilingual with German authoritative
  (plus a planted translation divergence); R7 is adopted in English with the
  ENGLISH text authoritative, while citing abbreviations defined only in a
  German document.
- Corpus as-of date: 1 October 2025 (WS 2025/26).

### Deliverables

- `velmora/` and `rheinmark/` — the 19 PDFs
- `ground_truth/` — document_manifest, version_relationships (6 states, 18
  amendment operations, 12 personas, resolution procedure), dependency_map
  (10 chains), module_data, benchmark_questions and benchmark_answers
  (72 questions), intentional_conflicts, abbreviations, validation_report
- `CORPUS_MANIFEST.md`, `VALIDATION_REPORT.md`
- `_source/` — the full generator and audit scripts

## 4. Known limitations to carry into the README

- The 72 benchmark answers were authored alongside the corpus and machine-checked
  for structural completeness and citation resolvability. They have NOT been blind
  re-derived from the PDFs.
- The PDFs are ReportLab-generated with a clean text layer, so they are easier to
  parse than real Prüfungsordnungen (often Word exports or scans). A clean parse
  here does not prove real-world robustness.
- At ~296 pages the whole corpus fits in a long-context window. That enables the
  long-context comparison, but means the corpus tests retrieval quality, not
  retrieval at scale.
- The four conflicts are declared in the source layer so the arithmetic validator
  does not reject them. A system reading only the PDFs must derive them from the
  documents.
