"""
Sync script: reads the sheet CSV from Downloads and appends it to the Google Sheet.

Run manually when you want to push new rows:
    python sync_to_sheet.py

Requires:
- service_account.json in the project root
- GOOGLE_SHEET_ID in .env
- sheet_rows.csv in ~/Downloads (from a recent cloud run)
"""

import csv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from schemas import SheetRow
from tools import append_to_sheet


DOWNLOADS_DIR = Path.home() / "Downloads"
CSV_FILENAME = "sheet_rows.csv"
SERVICE_ACCOUNT_PATH = "service_account.json"
TAB_NAME = "Main"


def find_csv() -> Path | None:
    """Look for sheet_rows.csv in Downloads. Handles the (1) suffix for duplicates."""
    candidates = sorted(DOWNLOADS_DIR.glob(f"{CSV_FILENAME}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_rows_from_csv(path: Path) -> list[SheetRow]:
    """Read the CSV and return SheetRow objects."""
    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                SheetRow(
                    title=row["Title"],
                    type=row["Type"],
                    year=int(row["Year"]) if row["Year"] else None,
                    authors=row["Authors"],
                    insights=row["Insights"],
                    conclusions=row["Conclusions"],
                    methods=row["Methods"],
                    limitations=row["Limitations"],
                    contributions=row["Contributions"],
                    summary_abstract=row["Summary Abstract"],
                    results=row["Results"],
                    literature_survey=row["Literature Survey"],
                    practical_implications=row["Practical Implications"],
                    objectives=row["Objectives"],
                    findings=row["Findings"],
                    research_gap=row["Research Gap"],
                    future_research=row["Future Research"],
                    dataset=row["Dataset"],
                    challenges=row["Challenges"],
                    applications=row["Applications"],
                )
            )
    return rows


def main():
    csv_path = find_csv()
    if not csv_path:
        print(f"No CSV found in {DOWNLOADS_DIR}. Download sheet_rows.csv from GitHub Actions first.")
        return

    print(f"Using: {csv_path.name}")
    rows = load_rows_from_csv(csv_path)
    if not rows:
        print("CSV is empty. Nothing to sync.")
        return

    print(f"Loaded {len(rows)} rows.")
    added = append_to_sheet(
        rows=rows,
        sheet_id=os.environ["GOOGLE_SHEET_ID"].strip(),
        service_account_path=SERVICE_ACCOUNT_PATH,
        tab_name=TAB_NAME,
    )
    print(f"Appended {added} rows to the sheet.")

    # Move the CSV out of Downloads so we don't process it again.
    synced_dir = Path("data/synced")
    synced_dir.mkdir(parents=True, exist_ok=True)
    new_path = synced_dir / csv_path.name
    csv_path.rename(new_path)
    print(f"Moved synced CSV to {new_path}")


if __name__ == "__main__":
    main()