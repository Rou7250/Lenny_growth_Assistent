"""
Placeholder downloader: Lenny's Podcast transcripts are not freely redistributable via API,
so this script documents the expected manual/scraping workflow and validates the local
agent_transcripts/ folder format. Drop .md or .txt transcript files into agent_transcripts/
using the frontmatter format documented in ingest.py, then run ingest.py.
"""
import sys
from pathlib import Path

TRANSCRIPTS_DIR = Path(__file__).resolve().parents[2] / "agent_transcripts"


def main():
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    existing = list(TRANSCRIPTS_DIR.glob("*.md")) + list(TRANSCRIPTS_DIR.glob("*.txt"))
    if existing:
        print(f"Found {len(existing)} transcript file(s) in {TRANSCRIPTS_DIR}")
    else:
        print(
            f"No transcripts found in {TRANSCRIPTS_DIR}.\n"
            "Add .md/.txt files with frontmatter (see ingest.py docstring), "
            "then run: python scripts/ingest.py"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
