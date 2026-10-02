"""
Tools for AI Research Radar.

Two tools:
  - search_papers(query, from_date, limit) -> list[Paper]
  - append_to_sheet(rows) -> int   (we'll add this next)

Both raise RuntimeError on failure. No LLM calls here.
"""

import requests
from datetime import datetime, timedelta
from schemas import Paper
from helpers import load_config


OPENALEX_URL = "https://api.openalex.org/works"

POLITE_EMAIL = "akuosaladi@gmail.com"


def _reconstruct_abstract(inverted_index: dict | None) -> str | None: # this is the inverted-index flip. Sort by position, join with spaces. Six lines. Read it twice.
    """Turn OpenAlex's inverted index into a plain-text abstract."""
    if not inverted_index:
        return None

    # Build a list of (position, word) then sort by position.
    positioned = []
    for word, positions in inverted_index.items():
        for pos in positions:
            positioned.append((pos, word))

    positioned.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positioned)

"""maps OpenAlex's type and source.type into your four labels (peer-reviewed, preprint, review, other). 
If OpenAlex says preprint or the source is a repository, we call it a preprint. 
The Gate 2 whitelist check happens later. This function just labels."""
def _map_type(
    openalex_type: str,
    source_type: str,
    source_name: str | None,
    whitelist: list[str],
) -> str:
    """
    Map OpenAlex types to our four categories.

    Whitelist rule: a repository paper is only 'preprint' if the repository
    name matches a known preprint server (arXiv, SSRN, etc). Otherwise it's
    'other' — usually meaning a general-purpose dump like Zenodo.
    """
    name = (source_name or "").lower()

    if openalex_type == "review":
        return "review"

    if openalex_type == "preprint" or source_type == "repository":
        if any(repo in name for repo in whitelist):
            return "preprint"
        return "other"

    if openalex_type == "article" and source_type in ("journal", "conference"):
        return "peer-reviewed"
    
    if openalex_type == "preprint" or source_type == "repository":
        if any(repo in name for repo in whitelist):
            return "preprint"
        return "other"

    return "other"

"""takes OpenAlex's display_name (e.g. "Jane Doe") and turns it into "Doe, Jane". 
Single-name authors fall through as-is."""
def _format_authors(authorships: list[dict]) -> list[str]:
    """Convert OpenAlex authorships into ['Last, First', ...]."""
    result = []
    for a in authorships:
        name = a.get("author", {}).get("display_name")
        if not name:
            continue
        parts = name.split()
        if len(parts) >= 2:
            last = parts[-1]
            first = " ".join(parts[:-1])
            result.append(f"{last}, {first}")
        else:
            result.append(name)
    return result

def _get_source_info(item: dict) -> tuple[str, str | None]:
    """Safely extract source_type and source_name from an OpenAlex item."""
    location = item.get("primary_location") or {}
    source = location.get("source") or {}
    return (
        source.get("type") or "",
        source.get("display_name"),
    )

def search_papers(query: str, from_date: str, limit: int = 50) -> list[Paper]:
    """
    Search OpenAlex for papers matching `query`, published on or after `from_date`.

    Retries twice on network failure, then raises RuntimeError.
    """
    config = load_config()
    retries = config["agent"]["api_retries"]
    whitelist = [r.lower() for r in config["gate2"]["preprint_repositories"]]
    
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date}",
        "per-page": limit,
        "mailto": POLITE_EMAIL,
    }

    last_error = None
    data = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(OPENALEX_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            last_error = e
            if attempt < retries:
                continue
            raise RuntimeError(f"OpenAlex failed after {retries + 1} attempts: {e}")

    if data is None:
        raise RuntimeError("OpenAlex returned no data.")

    papers = []
    for item in data.get("results", []):
        source_type, source_name = _get_source_info(item)
        papers.append(
            Paper(
                id=item["id"],
                doi=item.get("doi"),
                title=item.get("title") or "",
                abstract=_reconstruct_abstract(item.get("abstract_inverted_index")),
                year=item.get("publication_year"),
                authors=_format_authors(item.get("authorships", [])),
                type=_map_type(item.get("type", ""), source_type, source_name, whitelist),
                source_type=source_type,
                source_name=source_name,
                publication_date=item.get("publication_date") or "",
                url=item.get("id", ""),
            )
        )
    return papers

import gspread
from google.oauth2.service_account import Credentials
from schemas import SheetRow


GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


def _get_sheet_client(service_account_path: str):
    """Create and return an authorized gspread client."""
    creds = Credentials.from_service_account_file(
        service_account_path,
        scopes=GOOGLE_SCOPES,
    )
    return gspread.authorize(creds)


def append_to_sheet(
    rows: list[SheetRow],
    sheet_id: str,
    service_account_path: str,
    tab_name: str = "Main",
) -> int:
    """
    Append SheetRows to the given Google Sheet tab.

    Args:
        rows:                 List of SheetRow objects.
        sheet_id:             The Google Sheet ID (from the URL).
        service_account_path: Path to service_account.json.
        tab_name:             Worksheet tab name. Default "Main".

    Returns:
        Number of rows appended.

    Raises RuntimeError on any failure.
    """
    if not rows:
        return 0

    try:
        client = _get_sheet_client(service_account_path)
        sheet = client.open_by_key(sheet_id.strip())
        worksheet = sheet.worksheet(tab_name)

        # Convert each SheetRow to a list in column order.
        values = []
        for row in rows:
            values.append([
                row.title,
                row.type,
                row.year if row.year is not None else "",
                row.authors,
                row.insights,
                row.conclusions,
                row.methods,
                row.limitations,
                row.contributions,
                row.summary_abstract,
                row.results,
                row.literature_survey,
                row.practical_implications,
                row.objectives,
                row.findings,
                row.research_gap,
                row.future_research,
                row.dataset,
                row.challenges,
                row.applications,
            ])

        worksheet.append_rows(values)
        return len(values)

    except Exception as e:
        raise RuntimeError(f"Failed to append to sheet: {e}")

