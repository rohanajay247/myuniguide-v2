"""Typed models for the benchmark, written against the actual YAML schema.

`assumptions` is a list of dicts, not strings: a persona question carries
structured attributes (as_of, cohort, matriculation date, election status)
that the system needs in order to resolve which version applies.
"""

from pydantic import BaseModel, Field


class Support(BaseModel):
    """One expected citation. `doc` is a short code, not a filename."""

    doc: str          # "V8", "R4"
    locus: str        # "§ 4 Abs. 2"


class Question(BaseModel):
    id: str
    klass: str
    programme: str | None = None
    question_de: str | None = None
    question_en: str | None = None
    assumptions: list[dict] = Field(default_factory=list)

    @property
    def text(self) -> str:
        """The question as asked, with assumptions appended as context.

        Without the assumptions the question is not uniquely answerable — the
        benchmark's own meta note says so.
        """
        base = self.question_de or self.question_en or ""
        if not self.assumptions:
            return base
        pairs = [f"{k}: {v}" for d in self.assumptions for k, v in d.items()]
        return f"{base}\n\n[{'; '.join(pairs)}]"

    @property
    def language(self) -> str:
        return "de" if self.question_de else "en"


class ExpectedAnswer(BaseModel):
    id: str
    response_type: str          # ANSWER | DECLINE | CONFLICT
    answer: str
    support: list[Support] = Field(default_factory=list)
    reasoning: str | None = None