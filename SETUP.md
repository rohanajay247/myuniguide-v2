# Setup

## 1. Folder layout

Two folders side by side. The repository, and the ground truth outside it.

```
somewhere/
├── myuniguide-v2/          <- this repo, open in Cursor
│   └── corpus/
│       ├── velmora/        <- Velmora PDFs go here
│       └── rheinmark/      <- Rheinmark PDFs go here
└── corpus-ground-truth/    <- NOT in the repo, NOT in git
    ├── benchmark_questions.yaml
    ├── benchmark_answers.yaml
    ├── intentional_conflicts.yaml
    ├── version_relationships.yaml
    ├── dependency_map.yaml
    ├── module_data.yaml
    ├── abbreviations.yaml
    ├── document_manifest.yaml
    ├── CORPUS_MANIFEST.md
    └── VALIDATION_REPORT.md
```

## 2. Where each file goes

| File | Location | Why |
|---|---|---|
| Velmora PDFs | `corpus/velmora/` | The system may read these |
| Rheinmark PDFs | `corpus/rheinmark/` | The system may read these |
| `benchmark_questions` | ground truth | The questions |
| `benchmark_answers` | ground truth | The answers |
| `intentional_conflicts` | ground truth | Declares the four conflicts — must be derived from the PDFs |
| `version_relationships` | ground truth | Six states, 18 amendment operations, 12 personas |
| `dependency_map` | ground truth | Ten reference chains, pre-resolved |
| `module_data` | ground truth | 108 modules as structured data — if aggregation reads this, aggregation is not solved |
| `abbreviations` | ground truth | Pre-resolved, including cross-language ones |
| `document_manifest` | ground truth | Keep the boundary simple |
| `CORPUS_MANIFEST.md` | ground truth | Reference |
| `VALIDATION_REPORT.md` | ground truth | Reference |

The rule: if the system could cheat by reading it, it does not live in this repo.

`src/myuniguide` is the system under test and may never touch the ground truth.
`eval/` is the harness and may. `tests/test_corpus_isolation.py` enforces this.

## 3. Install

```bash
uv sync
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_API_KEY=...
GROUND_TRUTH_DIR=../corpus-ground-truth
```

## 4. Start Qdrant

```bash
make up
```

## 5. Verify

```bash
make check-setup
```

Checks PDF count is 19, ground truth is reachable and outside the repo, API key is set, Qdrant is up, and nothing has leaked into `corpus/`.

```bash
make test
```

## 6. Look at the ground truth shape

```bash
make gt-inspect
```

Prints the structure of each ground-truth file. The loaders are deliberately
schema-agnostic until we have seen the real shapes — typed models get written
on Day 2 against what is actually there.

## 7. Day 1 checkpoint

```bash
make inspect
```

Parses one PDF with Docling and reports whether headings, § / Artikel markers,
numbered paragraphs and tables survived. Full output written to
`eval/parse_sample.md`.

Everything from Day 3 onward depends on this. Send the report before building further.
