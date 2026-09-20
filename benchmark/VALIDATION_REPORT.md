# VALIDATION_REPORT

Corpus audit run 2026-09-02. **76 checks passed, 0 failed, 0 warnings.**
Corpus: 19 documents, 296 pages, 108 modules, 72 benchmark questions.

The audit script exits non-zero on any failure and is the gate for corpus acceptance.
Raw output: `ground_truth/validation_report.txt`.

## Scope of checks

| Group | What is verified |
|---|---|
| 1 Vollständigkeit | all 19 documents present; page budget; minimum text per document (placeholder detection) |
| 2 Hochschulkonventionen | terminology, governance and amendment-structure divergence actually realised in the rendered text |
| 3 Versionsmodell | paragraph numbering contiguous in all six resolved states; states content-distinct; consolidated versions carry the non-binding notice; all amendment instructions present; transitional wording present |
| 4 Zahlenkonsistenz | every semester sums to its declared total; every programme sums to its regulation figure; contact hours never exceed workload; plan totals appear in the rendered plan |
| 5 Querverweise | every internal § / Abs. reference resolves in at least one applicable version; external statute citations excluded; every module reference resolves; prerequisite graphs acyclic |
| 6 Abkürzungen | every exam abbreviation defined in the correct university's catalogue; plans reference the central catalogue rather than defining locally; exhaustive/open distinction preserved |
| 7 Konflikte | exactly four conflicts, each with rationale and two existing sources; conflict IDs disjoint from override / authority / version / near-duplicate / absence IDs; each conflict physically present in both PDFs; O-05 trap verified |
| 8 Autoritätsebenen | non-binding and partially-binding notices rendered; both language-authority declarations present |
| 9 Benchmark | 60–80 questions; unique IDs; every question has answer, reasoning path and resolvable supporting documents; response-type and class distribution; every conflict exercised |
| 10 Kohortendifferenzierung | personas in the same programme land in different states; at least one pair shares a cohort but differs in state |
| 11 Fiktionalität | no real university or location names; both fictional universities present; both state statutes cited |

## Defects found and fixed during the build

These were found by the checks, not by reading:

1. **IB thesis and colloquium module codes did not exist.** `core.yaml` pointed at
   `IB-6-025` / `IB-6-026`; the actual modules are `IB-6-023` / `IB-6-024`. Caught by the
   thesis-wiring check.
2. **Exam form `LN` was used but undefined.** `IB-5-020` used an abbreviation absent from
   the Rheinmark catalogue. `LN` was added to both catalogue versions as the generic
   ungraded certificate.
3. **Illegal paragraph gap in ASPO § 20.** The base text jumped from Abs. 3 to Abs. 5 to
   leave room for the amendment. Base renumbered so Abs. 4 is the deviation clause and Ä1
   appends Abs. 5; operation `VA1-03` realigned.
4. **Dangling module reference.** `SE-1-001` listed `SE-2-013` as a downstream module; the
   correct code is `SE-3-013`. Caught by the module-reference check.
5. **Terminology leak across universities.** The word *Studienleistungen* — Velmora
   vocabulary — appeared inside the title of a Rheinmark ordinance referenced by APO § 18
   and FSB-IB § 8. Renamed to *Ordnung über die Anerkennung von im Ausland erworbenen
   Leistungen*, restoring a clean vocabulary split between the two universities.
6. **Weak state-distinguishability test.** The first version of the check compared section
   and paragraph *counts*. States A and A0 have identical counts, because Ä2 adds one
   paragraph (§ 33 Abs. 3) and removes one (§ 18 Abs. 3). The check now compares a content
   hash. This is itself a corpus property worth recording: **a system cannot tell ASPO
   states A and A0 apart by structure alone.**
7. **Missing persona.** Benchmark question Q043 exercises a grandfathered IAI student in
   state B0, which no persona covered. Added as `S12`.

Items 1–5 were content defects. Items 6–7 were gaps in the ground truth itself.

## Known limitations

- **Page budget.** 296 pages, inside the 290–320 target. The module handbooks
  set one module per page, which is the convention in real German Modulhandbücher; total
  length is therefore driven by module count (108) rather than by prose volume.
- **Cross-reference checking is textual.** Section and paragraph references are validated
  against the parsed structure. External statute citations (LHG, HochSchG, Grundgesetz)
  are excluded by design and are not verified against the real statutes.
- **Conflicts are declared, not inferred.** The four conflicts are recorded in the source
  layer so the arithmetic validator does not reject them. A system that reads only the
  PDFs must derive them from the documents; the ground truth records how.
- **The benchmark answers have not been independently re-derived.** They were authored
  alongside the source layer and machine-checked for structural completeness and for
  document/section resolvability, not blind-scored by a second pass over the PDFs.

## Result

All checks pass. The corpus is internally consistent, every cross-reference resolves,
every number closes, and the four intentional conflicts are present in the rendered
documents and separable from the 8 legitimate overrides,
9 near-duplicate sets and
8 absence cases.
