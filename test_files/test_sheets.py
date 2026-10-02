from schemas import Paper, GateResult, SheetRow
from tools import append_to_sheet

# Fake paper + gate
paper = Paper(
    id="W999",
    title="Test paper for sheet write",
    type="peer-reviewed",
    source_type="journal",
    publication_date="2025-10-01",
    url="https://example.com",
    authors=["Doe, Jane"],
)

gate = GateResult(
    relevant=True,
    relevance_reason="Test",
    check_doi=True,
    check_venue=True,
    check_abstract=True,
    check_method=True,
    check_findings=True,
    check_on_topic=True,
    gate2_verdict="sound",
    score_relevant=2,
    score_positioned=2,
    score_practical=2,
    score_rigorous=2,
    theme="Other",
    one_line_summary="A test row.",
    insights="Test insights.",
    conclusions="Test conclusions.",
    methods="Test methods.",
    limitations="Test limitations.",
    contributions="Test contributions.",
    summary_abstract="Test abstract.",
    results="Test results.",
    literature_survey="Test survey.",
    practical_implications="Test implications.",
    objectives="Test objectives.",
    findings="Test findings.",
    research_gap="Test gap.",
    future_research="Test future.",
    dataset="Not stated in abstract.",
    challenges="Test challenges.",
    applications="Test applications.",
)

row = SheetRow.from_paper_and_gate(paper, gate)

count = append_to_sheet(
    rows=[row],
    sheet_id="YOUR SHEET ID HERE",
    service_account_path="service_account.json",
    tab_name="Main",
)

print(f"Appended {count} row(s).")