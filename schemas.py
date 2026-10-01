"""
Three schemas for AI Research Radar.

1. Paper       - what OpenAlex returns, trimmed to what we need
2. GateResult  - what the LLM returns for one paper (gates + scoring + 20 fields)
3. SheetRow    - what gets written to Google Sheets

Rule: facts come from the API (Paper). Judgments come from the LLM (GateResult).
SheetRow is the merge of the two.
"""

from pydantic import BaseModel, Field

""" Every field here comes from OpenAlex. 
No LLM touches this model. 
If you ever add a field that requires the LLM to fill it, it belongs in GateResult, not here. """
# facts only
class Paper(BaseModel): 
    """One paper from OpenAlex. Facts only. No LLM involved."""

    id: str = Field(description="OpenAlex ID, e.g. 'W1234567890'")
    doi: str | None = Field(default=None, description="DOI URL or None")
    title: str
    abstract: str | None = Field(
        default=None,
        description="Reconstructed from OpenAlex's inverted index. None if unavailable."
    )
    year: int | None = None
    authors: list[str] = Field(
        default_factory=list,
        description="List of 'Last, First' strings"
    )
    type: str = Field(
        description="One of: peer-reviewed, preprint, review, other"
    )
    source_type: str = Field(
        description="OpenAlex source.type: journal, conference, repository, etc."
    )
    source_name: str | None = None
    publication_date: str = Field(description="ISO date, YYYY-MM-DD")
    url: str = Field(description="Landing page URL")

class GateResult(BaseModel): # Judgements only
    """One LLM judgment for one paper. Judgments only. No facts from OpenAlex here."""

    # --- Gate 1: relevance ---
    relevant: bool = Field(description="Is the paper about AI governance?")
    relevance_reason: str = Field(description="One-line reason for the relevance call")

    # --- Gate 2: quality, 6 checks ---
    check_doi: bool
    check_venue: bool
    check_abstract: bool
    check_method: bool
    check_findings: bool
    check_on_topic: bool
    gate2_verdict: str = Field(
        description="One of: sound, uncertain, fail"
    )

    # --- Feasibility: 4 criteria, each 0-2 ---
    score_relevant: int = Field(ge=0, le=2)
    score_positioned: int = Field(ge=0, le=2, description="Positioned against prior work")
    score_practical: int = Field(ge=0, le=2)
    score_rigorous: int = Field(ge=0, le=2)

    # --- Digest helpers ---
    theme: str = Field(description="Theme label, e.g. 'EU regulation'")
    one_line_summary: str = Field(description="One sentence for the digest")

    # --- The 16 sheet fields from the LLM (columns 5-20) ---
    insights: str
    conclusions: str
    methods: str
    limitations: str
    contributions: str
    summary_abstract: str
    results: str
    literature_survey: str
    practical_implications: str
    objectives: str
    findings: str
    research_gap: str
    future_research: str
    dataset: str
    challenges: str
    applications: str

""" only place where Paper and GateResult meet. 
If you ever need to change how they merge, you change one function. """
class SheetRow(BaseModel): # the merge
    """One row in the Google Sheet. Merge of Paper (cols 1-4) + GateResult (cols 5-20)."""

    # Columns 1-4: from Paper
    title: str
    type: str
    year: int | None
    authors: str  # joined "Last, First; Last, First"

    # Columns 5-20: from GateResult
    insights: str
    conclusions: str
    methods: str
    limitations: str
    contributions: str
    summary_abstract: str
    results: str
    literature_survey: str
    practical_implications: str
    objectives: str
    findings: str
    research_gap: str
    future_research: str
    dataset: str
    challenges: str
    applications: str

    @classmethod
    def from_paper_and_gate(cls, paper: Paper, gate: GateResult) -> "SheetRow":
        """Merge a Paper and a GateResult into a SheetRow."""
        return cls(
            title=paper.title,
            type=paper.type,
            year=paper.year,
            authors="; ".join(paper.authors),
            insights=gate.insights,
            conclusions=gate.conclusions,
            methods=gate.methods,
            limitations=gate.limitations,
            contributions=gate.contributions,
            summary_abstract=gate.summary_abstract,
            results=gate.results,
            literature_survey=gate.literature_survey,
            practical_implications=gate.practical_implications,
            objectives=gate.objectives,
            findings=gate.findings,
            research_gap=gate.research_gap,
            future_research=gate.future_research,
            dataset=gate.dataset,
            challenges=gate.challenges,
            applications=gate.applications,
        )

class GateResultFilter(BaseModel):
    """Output of the gate1_and_gate2 prompt. Subset of GateResult."""
    relevant: bool
    relevance_reason: str
    check_doi: bool
    check_venue: bool
    check_abstract: bool
    check_method: bool
    check_findings: bool
    check_on_topic: bool
    gate2_verdict: str
    gate2_reason: str       