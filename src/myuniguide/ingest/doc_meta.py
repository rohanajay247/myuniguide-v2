"""Document-level metadata, derived from the filename and the first page."""

import re
from dataclasses import dataclass
from pathlib import Path

# Higher number wins under lex specialis: programme rules beat general rules.
AUTHORITY = {
    "APO": 1,    # Rheinmark general examination regulation
    "ASPO": 1,   # Velmora general study and examination regulation
    "FSB": 2,    # Rheinmark programme-specific provisions
    "BSPO": 2,   # Velmora programme-specific regulation
    "MHB": 3,    # module handbook
}


@dataclass
class DocMeta:
    doc_code: str          # "V8"
    document: str          # "V8_BSPO-ET.pdf"
    university: str        # "velmora"
    doc_type: str          # "ASPO" | "BSPO" | "APO" | "FSB" | "MHB"
    programme: str | None  # "ET" | "IAI" | "SE" | "IB" | None
    authority: int
    is_amendment: bool = False
    is_consolidated: bool = False
    title: str = ""

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def from_path(path: Path, markdown: str = "") -> DocMeta:
    stem = path.stem                       # "V8_BSPO-ET"
    doc_code = stem.split("_")[0]          # "V8"
    rest = stem.split("_", 1)[1] if "_" in stem else ""
    doc_type = rest.split("-")[0] if rest else "UNKNOWN"
    programme = rest.split("-", 1)[1] if "-" in rest else None

    head = markdown[:4000]
    is_amendment = bool(
        re.search(r"(Ordnung|Satzung)\s+zur\s+Änderung", head, re.I)
        or re.search(r"^##\s+(Artikel|§)\s+[I\d]+\s+Änderungen", head, re.M)
    )
    is_consolidated = bool(re.search(r"Lesefassung|konsolidiert", head, re.I))

    title_match = re.search(r"^##\s+(.{20,200})$", head, re.M)

    return DocMeta(
        doc_code=doc_code,
        document=path.name,
        university=path.parent.name,
        doc_type=doc_type,
        programme=programme,
        authority=AUTHORITY.get(doc_type, 0),
        is_amendment=is_amendment,
        is_consolidated=is_consolidated,
        title=title_match.group(1).strip() if title_match else "",
    )