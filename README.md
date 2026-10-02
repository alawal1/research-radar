# Research Radar

A weekly AI agent that monitors new research on AI governance, filters it by relevance and quality, and produces a consultant-ready digest — automatically.

**Portfolio write-up:** https://alawal1.github.io/portfolio-site/projects/research-radar

## What it does

Every Monday, the agent:

1. Searches OpenAlex for AI governance papers published in the last 7 days
2. Filters each paper for relevance (Gate 1) and quality (Gate 2)
3. Scores papers on four feasibility criteria
4. Writes a digest covering everything that passed
5. Commits the digest to this repo
6. Saves the top 5 papers as a CSV for further analysis

## Why

Staying current on AI governance research manually is exhausting and time-consuming. Papers are scattered across arXiv, SSRN, and other journals. This agent does the reading, filtering, and gives you a weekly digest with papers on regulation, compliance, auditing, risk.

## The digest

Every week's digest is committed to [`data/digests/`](data/digests/).

## How it runs

The agent runs every Monday at 08:00 UTC via GitHub Actions. Each run:
- Writes a new digest to `data/digests/`
- Commits it back to the repo
- Uploads a CSV of the top 5 papers as an artifact

The digest is the primary output. The CSV is for those who want the structured data.

**Sample:** [2026-10-02](data/digests/2026-10-02.md)

## How it works

OpenAlex search
    ↓
Gate 1 — Is this about AI governance? (LLM)
    ↓
Gate 2 — Is this real research? (LLM, 6 checks)
    ↓
Extraction — 16 structured fields + feasibility scores (LLM)
    ↓
Digest + top 5 CSV

The agent decides when to stop searching. It scores each paper 0–8 on four criteria (relevant, positioned, practical, rigorous). Only papers scoring 6+ reach the top-5 CSV.

## Stack

- **Python** — agent loop, no framework
- **OpenAI structured outputs** — for consistent JSON from the LLM
- **Pydantic** — schema validation
- **OpenAlex API** — paper search (no key needed)
- **GitHub Actions** — weekly cron

## Run it locally

# Clone
git clone https://github.com/alawal1/research-radar.git
cd research-radar

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Secrets (create .env with these)
OPENAI_API_KEY=sk-...

python run.py


The digest prints to the console and saves to `data/digests/`.

## Local-only: sync CSV to Google Sheets

Download the `outputs` artifact from a GitHub Actions run, then:

python sync_to_sheet.py

This reads `sheet_rows.csv` from your Downloads folder and appends the rows to a Google Sheet.

## Project structure

agent.py            — the agent loop
schemas.py          — Pydantic models
tools.py            — search_papers, append_to_sheet
helpers.py          — config, logging, dedupe
config.yaml         — all tunable values
prompts/            — one prompt per LLM call
.github/workflows/  — weekly cron
data/digests/       — committed weekly digests


## Case study

(coming soon)

## Design notes

- **No LangChain.** The loop is written by hand so every decision is explainable.
- **Metadata from the API, judgments from the LLM.** Years, DOIs, and sources come from OpenAlex. Relevance and quality come from the LLM. They never cross.
- **Strict by default.** Gate 1 rejects borderline papers. A clean digest beats a long one.
- **Abstract-only in V1.** The agent reads abstracts, not full PDFs. Fields not stated in the abstract are marked `"Not stated in abstract"`.

## Status

Running weekly. Actively maintained.