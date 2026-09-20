# Corpus placement

```
corpus/
  velmora/      <- Hochschule Velmora PDFs
  rheinmark/    <- Hochschule Rheinmark PDFs
```

PDFs only. Nothing else.

## Keep outside this repository

The YAML ground-truth files and `_source/` must NOT be placed here:
`benchmark_questions`, `benchmark_answers`, `intentional_conflicts`,
`version_relationships`, `dependency_map`, `module_data`, `abbreviations`,
`document_manifest`, `CORPUS_MANIFEST.md`, `VALIDATION_REPORT.md`.

They live in the folder pointed at by `GROUND_TRUTH_DIR` in `.env`, which sits
next to this repository rather than inside it.

The four conflicts, the six version states, the amendment operations and the
persona resolutions are all declared in those files. A system that can read them
has not solved the problem.

`tests/test_corpus_isolation.py` fails the build if any of them appear here, or
if any file under `src/` references them.

See `../SETUP.md` for the full table.
