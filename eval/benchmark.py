"""Loads the benchmark and normalises citations for comparison."""

import re

from eval.loader import load
from eval.models import ExpectedAnswer, Question


def questions() -> list[Question]:
    return [Question(**q) for q in load("benchmark_questions")["questions"]]


def answers() -> dict[str, ExpectedAnswer]:
    return {a["id"]: ExpectedAnswer(**a) for a in load("benchmark_answers")["answers"]}


def doc_code(filename: str) -> str:
    """'V8_BSPO-ET.pdf' -> 'V8'. The ground truth uses short codes."""
    return filename.split("_")[0].replace(".pdf", "").strip()


def normalise_locus(locus: str) -> str:
    """Canonicalise a citation locus for comparison.

    '§ 4 Abs. 2', '§4 Abs 2' and '§ 4 Absatz 2' must compare equal, and
    'Anlage 1, Semester 4' must compare equal to '4. Fachsemester'.
    """
    s = locus.lower().strip()
    s = re.sub(r"absatz", "abs", s)
    s = re.sub(r"\bziffer\b|\bnummer\b", "nr", s)
    s = re.sub(r"annex|anlage", "anlage", s)
    s = re.sub(r"(\d+)\.\s*fachsemester|semester\s+(\d+)",
               lambda m: f"semester {m.group(1) or m.group(2)}", s)
    s = re.sub(r"[§¶]", " § ", s)
    s = re.sub(r"[.,;]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def locus_matches(cited: set[str], expected: set[str]) -> bool:
    """A citation counts if it names the same locus, allowing partial paragraphs.

    Expected '§ 8 abs 3 und 4' is satisfied by cited '§ 8 abs 4': the section
    is right and the paragraph is one of those named. Citing the right § with
    an incomplete paragraph list is a different failure from citing the wrong
    document, and scoring them identically hides that.
    """
    if cited & expected:
        return True
    for e in expected:
        for c in cited:
            if c and e and (c in e or e in c):
                return True
            # same section, overlapping paragraph numbers
            c_sec = re.match(r"§ \d+[a-z]?", c)
            e_sec = re.match(r"§ \d+[a-z]?", e)
            if c_sec and e_sec and c_sec.group() == e_sec.group():
                c_nums = set(re.findall(r"\b\d+\b", c.split("abs")[-1]))
                e_nums = set(re.findall(r"\b\d+\b", e.split("abs")[-1]))
                if c_nums & e_nums:
                    return True
    return False