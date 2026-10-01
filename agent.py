"""
The agent loop for AI Research Radar.

Flow:
1. Ask LLM to group keywords into queries.
2. Run queries one at a time. After each, ask LLM: keep searching?
3. For each candidate paper, ask LLM for gates + scores + 16 fields.
4. Score, filter, sort. Top 5 → Google Sheet.
5. Write digest.
6. Log the run.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import json
from datetime import datetime, timedelta

from openai import OpenAI

from helpers import (
    build_paper_list_for_digest,
    feasibility_total,
    get_already_seen_papers,
    load_config,
    log_run,
    save_seen_papers,
)
from schemas import GateResult, Paper, SheetRow
from tools import append_to_sheet, search_papers


# Load config once at import.
config = load_config()
client = OpenAI()


def _read_prompt(name: str) -> str:
    with open(f"prompts/{name}.txt", "r") as f:
        return f.read()


def _fill(template: str, **values) -> str:
    """Replace {key} placeholders in a template string. No format() magic."""
    result = template
    for key, value in values.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def _llm_json(system_prompt: str, user_content: str, schema: dict) -> dict:
    """Call OpenAI with structured outputs and return the parsed dict."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": schema,
            },
        },
    )
    return json.loads(response.choices[0].message.content)


# --- Schemas for structured outputs ---

GROUPING_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "keywords"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["queries"],
    "additionalProperties": False,
}

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "relevant": {"type": "boolean"},
        "relevance_reason": {"type": "string"},
        "check_doi": {"type": "boolean"},
        "check_venue": {"type": "boolean"},
        "check_abstract": {"type": "boolean"},
        "check_method": {"type": "boolean"},
        "check_findings": {"type": "boolean"},
        "check_on_topic": {"type": "boolean"},
        "gate2_verdict": {"type": "string"},
        "gate2_reason": {"type": "string"},
    },
    "required": [
        "relevant", "relevance_reason",
        "check_doi", "check_venue", "check_abstract",
        "check_method", "check_findings", "check_on_topic",
        "gate2_verdict", "gate2_reason",
    ],
    "additionalProperties": False,
}

STOPPING_SCHEMA = {
    "type": "object",
    "properties": {
        "should_search_again": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["should_search_again", "reason"],
    "additionalProperties": False,
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "score_relevant": {"type": "integer"},
        "score_positioned": {"type": "integer"},
        "score_practical": {"type": "integer"},
        "score_rigorous": {"type": "integer"},
        "theme": {"type": "string"},
        "one_line_summary": {"type": "string"},
        "insights": {"type": "string"},
        "conclusions": {"type": "string"},
        "methods": {"type": "string"},
        "limitations": {"type": "string"},
        "contributions": {"type": "string"},
        "summary_abstract": {"type": "string"},
        "results": {"type": "string"},
        "literature_survey": {"type": "string"},
        "practical_implications": {"type": "string"},
        "objectives": {"type": "string"},
        "findings": {"type": "string"},
        "research_gap": {"type": "string"},
        "future_research": {"type": "string"},
        "dataset": {"type": "string"},
        "challenges": {"type": "string"},
        "applications": {"type": "string"},
    },
    "required": [
        "score_relevant", "score_positioned", "score_practical", "score_rigorous",
        "theme", "one_line_summary",
        "insights", "conclusions", "methods", "limitations", "contributions",
        "summary_abstract", "results", "literature_survey", "practical_implications",
        "objectives", "findings", "research_gap", "future_research",
        "dataset", "challenges", "applications",
    ],
    "additionalProperties": False,
}


# --- Agent steps ---

def group_keywords(keywords: list[str]) -> list[dict]:
    prompt = _read_prompt("grouping")
    user = _fill(prompt, keywords=", ".join(keywords))
    result = _llm_json("You group keywords.", user, GROUPING_SCHEMA)
    return result["queries"]

def evaluate_paper(paper: Paper) -> dict:
    prompt = _read_prompt("gates")
    user = _fill(
        prompt,
        title=paper.title,
        authors="; ".join(paper.authors),
        year=paper.year or "",
        type=paper.type,
        source_name=paper.source_name or "",
        doi=paper.doi or "",
        abstract=paper.abstract or "",
    )   
    return _llm_json("You screen papers.", user, GATE_SCHEMA)


def extract_fields(paper: Paper) -> dict:
    prompt = _read_prompt("extraction")
    user = _fill(
        prompt,
        title=paper.title,
        type=paper.type,
        year=paper.year or "",
        source_name=paper.source_name or "",
        abstract=paper.abstract or "",
    )
    return _llm_json("You extract fields from papers.", user, EXTRACTION_SCHEMA)


def should_keep_searching(state: dict) -> dict:
    prompt = _read_prompt("stopping")
    user = _fill(prompt, **state)
    return _llm_json("You decide when to stop.", user, STOPPING_SCHEMA)


# --- Main loop ---

def run():
    trace = {"queries": [], "papers_found": 0, "papers_kept": 0, "papers_added": 0}
    
    from_date = (datetime.now() - timedelta(days=config["search"]["lookback_days"])).strftime("%Y-%m-%d")
    seen = get_already_seen_papers(config["paths"]["seen_papers"])

    # 1. Group keywords
    queries = group_keywords(config["search"]["keywords"])
    trace["queries_planned"] = [q["name"] for q in queries]

    # 2. Search one query at a time
    all_papers: dict[str, Paper] = {}
    queries_run = []

    for q in queries:
        query_string = "|".join(f'"{kw}"' for kw in q["keywords"])
        papers = search_papers(query_string, from_date, config["search"]["results_per_query"])
        new_papers = [p for p in papers if p.id not in all_papers and p.id not in seen]
        for p in new_papers:
            all_papers[p.id] = p
        queries_run.append(q["name"])

        state = {
            "paper_count": len(all_papers),
            "searches_run": len(queries_run),
            "queries_used": ", ".join(queries_run),
            "queries_remaining": ", ".join([x["name"] for x in queries if x["name"] not in queries_run]),
            "relevant_count": len(all_papers),
            "themes_covered": "TBD",
            "themes_missing": "TBD",
        }
        decision = should_keep_searching(state)
        if not decision["should_search_again"]:
            trace["stop_reason"] = decision["reason"]
            break

    trace["papers_found"] = len(all_papers)

    # 3. Evaluate each paper
    gates: dict[str, GateResult] = {}
    kept_papers: list[Paper] = []
    max_eval = config["agent"].get("max_papers_to_evaluate")
    papers_to_eval = list(all_papers.values())
    if max_eval:
        papers_to_eval = papers_to_eval[:max_eval]
    for i, paper in enumerate(all_papers.values(), 1):
        gate = evaluate_paper(paper)
        if not gate["relevant"]:
            continue
        if gate["gate2_verdict"] == "fail":
            continue
        extracted = extract_fields(paper)
        merged = {**gate, **extracted}
        gates[paper.id] = GateResult(**merged)
        kept_papers.append(paper)

    trace["papers_kept"] = len(kept_papers)

    # 4. Score, sort, top 5
    scored = [(p, gates[p.id], feasibility_total(gates[p.id])) for p in kept_papers]
    scored.sort(key=lambda x: x[2], reverse=True)
    threshold = config["feasibility"]["score_floor"]
    top_n = config["feasibility"]["top_n"]
    sheet_rows = [
        SheetRow.from_paper_and_gate(p, g)
        for p, g, s in scored[:top_n] if s >= threshold
    ]

    # 5. Write to sheet
    added = append_to_sheet(
        rows=sheet_rows,
        sheet_id=os.environ["GOOGLE_SHEET_ID"],
        service_account_path="service_account.json",
        tab_name="Main",
    )
    trace["papers_added"] = added

    # 6. Digest
    papers_list = build_paper_list_for_digest(kept_papers, gates)
    digest_prompt = _fill(
        _read_prompt("digest"),
        date=datetime.now().strftime("%Y-%m-%d"),
        total_count=len(kept_papers),
        peer_reviewed_count=sum(1 for p in kept_papers if p.type == "peer-reviewed"),
        preprint_count=sum(1 for p in kept_papers if p.type == "preprint"),
        papers_list=papers_list,
    )
    digest_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": digest_prompt}],
    )
    digest_text = digest_response.choices[0].message.content
    print("=== DIGEST ===")
    print(digest_text)
    print("=== END DIGEST ===")

    # 7. Save seen
    save_seen_papers(seen | set(all_papers.keys()), config["paths"]["seen_papers"])

    # 8. Log
    log_run(trace)