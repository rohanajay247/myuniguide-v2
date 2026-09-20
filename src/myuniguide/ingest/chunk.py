"""Markdown -> nodes, with structured metadata.

Five document shapes in this corpus, four strategies:

  regulation  Rheinmark puts "§ 1   Geltungsbereich" on one heading line.
              Velmora splits it: "§ 1" then "Geltungsbereich". Both handled.
  amendment   Chunks are operations. The § in "2. § 16 Absatz 3 wird wie folgt
              gefasst" is the TARGET section in another document, recorded as
              `targets_section`, never as this chunk's own locus.
  handbook    Chunks are modules, keyed by module code. Velmora uses ET-M-38,
              Rheinmark uses SE-1-001 — both patterns accepted.
  study_plan  Studien- und Prüfungsplan: mostly tables, organised by semester.
              Footnotes are appended to every semester chunk, because a
              footnote can carry a binding requirement that contradicts the
              main regulation and is useless retrieved on its own.

Every pattern here accepts both German and English forms. The corpus is
bilingual, and each monolingual rule written so far has silently skipped half
the corpus while looking like a reasoning failure downstream.
"""

import re
from pathlib import Path

from llama_index.core.schema import BaseNode, TextNode

from myuniguide.ingest.doc_meta import DocMeta, from_path

SECTION_INLINE = re.compile(r"^##+\s+(§\s*\d+[a-z]?)\s{2,}(.+)$")
SECTION_ALONE = re.compile(r"^##+\s+(§\s*\d+[a-z]?)\s*$")
ARTICLE = re.compile(r"^##+\s+(Artikel\s+[IVXL\d]+)\s*(.*)$")
GROUP = re.compile(r"^##+\s+(Abschnitt\s+[IVXL\d]+)\s*(.*)$", re.I)
AMENDMENT_OP = re.compile(r"^##+\s+(\d+)\.\s+(.*?§\s*\d+[a-z]?.*)$")
OP_ANY = re.compile(r"^(?:##+\s+)?(\d{1,2})\.\s+(.+)$")
ARTICLE_HEAD = re.compile(r"^##+\s+(§\s*\d+[a-z]?|Artikel\s+[IVXL\d]+)\b\s*(.*)$")
# Velmora "ET-M-38" and Rheinmark "SE-1-001"
MODULE = re.compile(r"^##+\s+([A-Z]{2,4}-[A-Z0-9]{1,2}-\d{2,3})\s{2,}(.+)$")
# re.M is required: findall over a multi-line string needs ^ to match line starts
SEMESTER = re.compile(r"^##+\s+(\d+\.\s*Fachsemester|Semester\s+\d+)\s*$", re.I | re.M)
NOTES = re.compile(r"^##+\s+(Fu.noten|Legende|Anmerkungen|Footnotes|Legend|Notes)", re.I)
TOC = re.compile(r"^##+\s+(Inhalts.bersicht|Table of Contents)\s*$", re.I)
ANY_HEADING = re.compile(r"^##+\s+(.*)$")
PLAN_TITLE = re.compile(
    r"Studien-\s*und\s*Pr.fungsplan|Study\s+and\s+Examination\s+Plan", re.I
)

MAX_CHARS = 3000


def _clean(section: str) -> str:
    return re.sub(r"§\s*", "§ ", section).strip()


def _split_oversized(text: str) -> list[str]:
    """Split a chunk over MAX_CHARS on blank lines, never mid-table-row."""
    if len(text) <= MAX_CHARS:
        return [text]
    parts, current, size = [], [], 0
    for block in text.split("\n\n"):
        if size + len(block) > MAX_CHARS and current:
            parts.append("\n\n".join(current))
            current, size = [], 0
        current.append(block)
        size += len(block) + 2
    if current:
        parts.append("\n\n".join(current))
    return parts


def _nodes(text: str, meta: DocMeta, extra: dict) -> list[TextNode]:
    body = text.strip()
    if len(body) < 40:
        return []
    parts = _split_oversized(body)
    out = []
    for i, part in enumerate(parts):
        md = {**meta.as_dict(), **extra}
        if len(parts) > 1:
            md["part"] = f"{i + 1}/{len(parts)}"
        out.append(TextNode(text=part, metadata=md))
    return out


def _split_blocks(markdown: str) -> list[tuple[str, str]]:
    """[(heading_line, body_text)] — body runs until the next heading."""
    blocks: list[tuple[str, list[str]]] = []
    for line in markdown.splitlines():
        if ANY_HEADING.match(line):
            blocks.append((line, []))
        elif blocks:
            blocks[-1][1].append(line)
    return [(h, "\n".join(b).strip()) for h, b in blocks]


def _chunk_regulation(markdown: str, meta: DocMeta) -> list[BaseNode]:
    nodes: list[BaseNode] = []
    group = None
    pending_section: str | None = None
    in_toc = False

    for heading, body in _split_blocks(markdown):
        if TOC.match(heading):
            in_toc = True
            continue

        if m := GROUP.match(heading):
            group = f"{m.group(1)} {m.group(2)}".strip()
            in_toc = False
            continue

        if m := SECTION_INLINE.match(heading):
            in_toc, pending_section = False, None
            nodes += _nodes(
                f"{_clean(m.group(1))} {m.group(2)}\n\n{body}", meta,
                {"section": _clean(m.group(1)), "section_title": m.group(2).strip(),
                 "section_group": group, "chunk_type": "provision"})
            continue

        if m := SECTION_ALONE.match(heading):
            in_toc = False
            pending_section = _clean(m.group(1))
            continue

        if pending_section:
            title = ANY_HEADING.match(heading).group(1).strip()
            nodes += _nodes(
                f"{pending_section} {title}\n\n{body}", meta,
                {"section": pending_section, "section_title": title,
                 "section_group": group, "chunk_type": "provision"})
            pending_section = None
            continue

        if not in_toc and body:
            title = ANY_HEADING.match(heading).group(1).strip()
            nodes += _nodes(
                f"{title}\n\n{body}", meta,
                {"section": title[:60], "section_title": title,
                 "section_group": group, "chunk_type": "preamble"})

    return nodes


def _chunk_amendment(markdown: str, meta: DocMeta) -> list[BaseNode]:
    """Split on numbered operations, whether Docling made them headings or not.

    A quoted heading like "## ' § 11a …" is inserted text belonging to the
    operation above it, not a new section — hence the quote check below.
    """
    nodes: list[BaseNode] = []
    article: str | None = None
    op_no: str | None = None
    op_title: str = ""
    buffer: list[str] = []

    def flush() -> None:
        nonlocal nodes
        text = "\n".join(buffer).strip()
        if not text:
            return
        if op_no:
            targets = re.findall(r"§\s*\d+[a-z]?|Anlage\s+\d+", op_title)
            nodes += _nodes(
                f"{op_no}. {op_title}\n\n{text}", meta,
                {"section": article, "section_title": op_title[:120],
                 "targets_section": _clean(targets[0]) if targets else None,
                 "operation_no": op_no, "chunk_type": "amendment_operation"})
        else:
            nodes += _nodes(
                text, meta,
                {"section": article or "preamble",
                 "section_title": (article or "preamble")[:120],
                 "chunk_type": "amendment_text"})

    for line in markdown.splitlines():
        stripped = line.strip()

        if m := OP_ANY.match(stripped):
            flush()
            op_no, op_title, buffer = m.group(1), m.group(2).strip(), []
            continue

        if (m := ARTICLE_HEAD.match(stripped)) and "'" not in stripped:
            flush()
            article = f"{_clean(m.group(1))} {m.group(2)}".strip()
            op_no, op_title, buffer = None, "", []
            continue

        buffer.append(line)

    flush()
    return nodes


def _chunk_handbook(markdown: str, meta: DocMeta) -> list[BaseNode]:
    nodes: list[BaseNode] = []
    code = title = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal nodes
        if code and buffer:
            nodes += _nodes(
                f"{code} {title}\n\n" + "\n\n".join(buffer), meta,
                {"section": code, "section_title": title,
                 "module_code": code, "chunk_type": "module"})

    for heading, body in _split_blocks(markdown):
        if TOC.match(heading):
            continue
        if m := MODULE.match(heading):
            flush()
            code, title, buffer = m.group(1), m.group(2).strip(), []
            if body:
                buffer.append(body)
            continue
        if code:
            sub = ANY_HEADING.match(heading).group(1).strip()
            buffer.append(f"{sub}\n{body}" if body else sub)

    flush()
    return nodes


def _chunk_study_plan(markdown: str, meta: DocMeta) -> list[BaseNode]:
    """One chunk per semester, with the document's footnotes appended to each.

    Footnotes sit under their own heading but qualify the tables above them.
    A footnote can carry a binding requirement that contradicts the main
    regulation — split apart, the annotation is unretrievable alongside what
    it annotates, and any conflict between them becomes invisible.
    """
    blocks = [(h, b) for h, b in _split_blocks(markdown) if b and not TOC.match(h)]

    notes = "\n\n".join(
        f"{ANY_HEADING.match(h).group(1).strip()}\n{b}"
        for h, b in blocks
        if NOTES.match(h)
    )

    nodes: list[BaseNode] = []
    for heading, body in blocks:
        if NOTES.match(heading):
            continue
        title = ANY_HEADING.match(heading).group(1).strip()
        text = f"{title}\n\n{body}"
        if notes:
            text += f"\n\n{notes}"
        nodes += _nodes(text, meta, {
            "section": title[:60], "section_title": title,
            "chunk_type": "study_plan"})

    if notes:
        nodes += _nodes(notes, meta, {
            "section": "Fußnoten", "section_title": "Fußnoten",
            "chunk_type": "study_plan_notes"})

    return nodes


def _is_study_plan(markdown: str) -> bool:
    """A study plan, not a regulation that merely mentions one.

    Every German regulation's table of contents contains a line like
    "§ 6   Studien- und Prüfungsplan", so the phrase must appear in one of the
    document's own title headings — but not necessarily the first, which is
    often just the university name.
    """
    if len(SEMESTER.findall(markdown)) >= 3:
        return True
    headings = re.findall(r"^##\s+(.*)$", markdown[:3000], re.M)[:4]
    return any(PLAN_TITLE.search(h) for h in headings)


def to_nodes(markdown: str, source: Path) -> list[BaseNode]:
    meta = from_path(source, markdown)
    if meta.doc_type == "MHB":
        return _chunk_handbook(markdown, meta)
    if meta.is_amendment:
        return _chunk_amendment(markdown, meta)
    if _is_study_plan(markdown):
        return _chunk_study_plan(markdown, meta)
    return _chunk_regulation(markdown, meta)