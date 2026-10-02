"""
Publish the weekly digest to a Google Doc.

Run manually after downloading the `outputs` artifact from GitHub Actions:
    python publish_digest.py

Requires:
- service_account.json in the project root
- DIGEST_SHARE_EMAIL in .env (your email address)
- digest.md in ~/Downloads (from a recent cloud run)
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from tools import publish_digest_to_doc


DOWNLOADS_DIR = Path.home() / "Downloads"
DIGEST_FILENAME = "digest.md"
SEARCH_DIRS = [DOWNLOADS_DIR, DOWNLOADS_DIR / "outputs"]
SERVICE_ACCOUNT_PATH = "service_account.json"


def find_digest() -> Path | None:
    """Look for digest.md in Downloads and Downloads/outputs, newest first."""
    candidates = []
    for d in SEARCH_DIRS:
        if d.exists():
            candidates.extend(d.glob(f"{DIGEST_FILENAME}*"))
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def main():
    digest_path = find_digest()
    if not digest_path:
        print(f"No digest found in {DOWNLOADS_DIR}. Download the outputs artifact from GitHub Actions first.")
        return

    print(f"Using: {digest_path.name}")
    digest_text = digest_path.read_text()

    title = f"AI Research Radar — {datetime.now().strftime('%Y-%m-%d')}"
    share_email = os.environ["DIGEST_SHARE_EMAIL"]

    url = publish_digest_to_doc(
        digest_text=digest_text,
        title=title,
        service_account_path=SERVICE_ACCOUNT_PATH,
        share_with_email=share_email,
        folder_id=os.environ.get("DIGEST_FOLDER_ID"),
    )
    print(f"Published: {url}")

    # Move the digest out of Downloads so we don't process it again.
    synced_dir = Path("data/published")
    synced_dir.mkdir(parents=True, exist_ok=True)
    new_path = synced_dir / digest_path.name
    digest_path.rename(new_path)
    print(f"Moved published digest to {new_path}")


if __name__ == "__main__":
    main()