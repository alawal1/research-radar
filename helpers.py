"""Small utilities used across the agent."""

import json
from datetime import datetime
from pathlib import Path
import yaml
import re

from schemas import GateResult, Paper, SheetRow


def load_config(path: str = "config.yaml") -> dict:
    """Load config.yaml and return it as a dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def feasibility_total(gate: GateResult) -> int:
    """Sum the four feasibility scores into a 0-8 total."""
    return (
        gate.score_relevant
        + gate.score_positioned
        + gate.score_practical
        + gate.score_rigorous
    )


def get_already_seen_papers(path: str) -> set[str]:
    """Read the seen-papers file and return a set of paper IDs."""
    file = Path(path)
    if not file.exists():
        return set()
    with open(file, "r") as f:
        return set(json.load(f))


def save_seen_papers(ids: set[str], path: str) -> None:
    """Write the updated set of seen paper IDs back to disk."""
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, "w") as f:
        json.dump(sorted(ids), f, indent=2)


def log_run(trace: dict) -> None:
    """Print the run log to stdout. GitHub Actions captures it."""
    trace["timestamp"] = datetime.now().isoformat()
    print("=== RUN LOG ===")
    print(json.dumps(trace, indent=2, default=str))
    print("=== END RUN LOG ===")


def build_paper_list_for_digest(
    papers: list[Paper],
    gates: dict[str, GateResult],
) -> str:
    """Format the papers list for the digest prompt."""
    lines = []
    for paper in papers:
        gate = gates.get(paper.id)
        if gate is None:
            continue
        lines.append(f"- Title: {paper.title}")
        lines.append(f"  Type: {paper.type}")
        lines.append(f"  Theme: {gate.theme}")
        lines.append(f"  Summary: {gate.one_line_summary}")
        lines.append(f"  URL: {paper.url}")
        lines.append("")
    return "\n".join(lines)

def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation and extra spaces."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)   # remove punctuation
    title = re.sub(r"\s+", " ", title)      # collapse whitespace
    return title.strip()


def dedupe_papers(papers: list[Paper]) -> list[Paper]:
    """Remove papers with duplicate normalized titles. Keeps first occurrence."""
    seen_titles = set()
    result = []
    for paper in papers:
        key = _normalize_title(paper.title)
        if key in seen_titles:
            continue
        seen_titles.add(key)
        result.append(paper)
    return result