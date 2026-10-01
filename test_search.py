from tools import search_papers
from datetime import datetime, timedelta

from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

papers = search_papers('"AI regulation"|"AI governance"', from_date, limit=10)

print(f"Found {len(papers)} papers.\n")
for p in papers[:5]:
    print(f"- [{p.type}] {p.title}")
    print(f"  {p.publication_date} | {p.source_name}")
    if p.abstract:
        print(f"  Abstract: {p.abstract[:150]}...")
    print()