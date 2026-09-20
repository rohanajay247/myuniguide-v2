"""Guards the chunking bugs that cost the most time.

Three separate bugs this week were monolingual assumptions in a bilingual
corpus: Rheinmark module codes, the English study plan, and German-only
footnote headings. Each surfaced downstream as something other than a
parsing failure.
"""

from pathlib import Path

import pytest

from myuniguide.config import settings
from myuniguide.ingest.chunk import _is_study_plan, to_nodes
from myuniguide.ingest.doc_meta import from_path
from myuniguide.ingest.parse import parse_pdf

CORPUS = Path("corpus")


def _md(name: str) -> str:
    path = next(CORPUS.rglob(name), None)
    if path is None:
        pytest.skip(f"{name} not present")
    return parse_pdf(path)


def _nodes(name: str):
    path = next(CORPUS.rglob(name))
    return to_nodes(parse_pdf(path), path)


def test_every_document_produces_nodes():
    """Six documents once produced zero nodes and it was invisible."""
    empty = []
    for path in settings.pdf_paths:
        if not to_nodes(parse_pdf(path), path):
            empty.append(path.name)
    assert not empty, f"documents produced no chunks: {empty}"


def test_english_study_plan_is_detected():
    """R8 is the English study plan; German-only rules skipped it entirely."""
    assert _is_study_plan(_md("R8_FSB-IB.pdf"))


def test_german_study_plan_is_detected():
    assert _is_study_plan(_md("V9_BSPO-ET.pdf"))


def test_regulation_is_not_mistaken_for_a_study_plan():
    """Every regulation's table of contents contains 'Studien- und Prüfungsplan'."""
    assert not _is_study_plan(_md("R1_APO.pdf"))
    assert not _is_study_plan(_md("V1_ASPO.pdf"))


def test_both_module_code_formats_parse():
    """Velmora uses ET-M-38, Rheinmark uses SE-1-001."""
    for name in ("V10_MHB-ET.pdf", "R6_MHB-SE.pdf"):
        modules = [n for n in _nodes(name)
                   if n.metadata.get("chunk_type") == "module"]
        assert modules, f"{name} produced no module chunks"


def test_both_section_heading_formats_parse():
    """Rheinmark: '## § 1  Title'. Velmora: '## § 1' then '## Title'."""
    for name in ("R1_APO.pdf", "V1_ASPO.pdf"):
        provisions = [n for n in _nodes(name)
                      if n.metadata.get("chunk_type") == "provision"]
        assert len(provisions) > 10, f"{name} produced {len(provisions)} provisions"
        assert all(n.metadata.get("section_title") for n in provisions)


def test_amendment_targets_are_recorded():
    """The § in an amendment operation belongs to the OTHER document."""
    ops = [n for n in _nodes("R2_APO.pdf")
           if n.metadata.get("chunk_type") == "amendment_operation"]
    assert ops
    assert any(n.metadata.get("targets_section") for n in ops)


def test_every_chunk_has_section_metadata():
    """Citation locus depends on this."""
    missing = [
        (n.metadata.get("document"), n.get_content()[:40])
        for path in settings.pdf_paths
        for n in to_nodes(parse_pdf(path), path)
        if not n.metadata.get("section")
    ]
    assert not missing, f"{len(missing)} chunks without section metadata"