"""The answering path must never be able to read the ground truth.

The four conflicts, the six version states, the module data and the persona
resolutions are all declared in the corpus source layer. A system that reads
them has not solved the problem — it has been handed the answers.

This test fails the build if that boundary is crossed.
"""

from pathlib import Path

import pytest

FORBIDDEN_TERMS = (
    "ground" + "_truth",
    "_source",
    "benchmark_answers",
    "intentional_conflicts",
    "version_relationships",
    "module_data",
    "dependency_map",
)

REPO = Path(__file__).parent.parent
SRC = REPO / "src"
CORPUS = REPO / "corpus"

SRC_FILES = sorted(SRC.rglob("*.py"))


@pytest.mark.parametrize("py_file", SRC_FILES, ids=lambda p: p.name)
def test_src_never_references_ground_truth(py_file: Path) -> None:
    """No file under src/ may name a ground-truth artefact, even in a string."""
    body = "\n".join(
        line
        for line in py_file.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("#")
    )
    for term in FORBIDDEN_TERMS:
        assert term not in body, f"{py_file.relative_to(REPO)} references '{term}'"


@pytest.mark.parametrize("py_file", SRC_FILES, ids=lambda p: p.name)
def test_src_never_imports_the_harness(py_file: Path) -> None:
    """The system under test must not import its own evaluator."""
    body = py_file.read_text(encoding="utf-8")
    assert "import eval" not in body and "from eval" not in body, (
        f"{py_file.relative_to(REPO)} imports the evaluation harness"
    )


def test_ground_truth_is_not_inside_the_corpus_directory() -> None:
    if not CORPUS.exists():
        pytest.skip("corpus not present")
    offenders = [
        p.name
        for p in CORPUS.iterdir()
        if any(term in p.name for term in FORBIDDEN_TERMS)
    ]
    assert not offenders, (
        f"corpus/ contains {offenders} — move them outside the repository. "
        "The answering path must only ever see the PDFs."
    )


def test_corpus_contains_only_pdfs_and_docs() -> None:
    if not CORPUS.exists():
        pytest.skip("corpus not present")
    allowed = {".pdf", ".md", ".gitkeep", ""}
    strays = [
        p.relative_to(REPO).as_posix()
        for p in CORPUS.rglob("*")
        if p.is_file() and p.suffix.lower() not in allowed and p.name != ".gitkeep"
    ]
    assert not strays, f"unexpected files under corpus/: {strays}"
