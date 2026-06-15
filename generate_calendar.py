#!/usr/bin/env python3
"""Generate VCT 2026 ICS calendar from vlr.gg data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.calendar_generator import generate_ics
from src.config import STAGES
from src.scraper import scrape_all_matches

OUTPUT_FILE = "vct-2026.ics"


def main():
    stages = list(STAGES)
    print(f"Scraping current and upcoming VCT 2026 matches from vlr.gg: {', '.join(stages)}")

    matches = []
    for stage in stages:
        print(f"  Fetching {stage}...")
        matches.extend(scrape_all_matches(stage))

    print(f"\nTotal matches found: {len(matches)}")

    for match in matches[:5]:
        print(f"  - {match.summary} @ {match.datetime_str}")
    if len(matches) > 5:
        print(f"  ... and {len(matches) - 5} more")

    print(f"\nGenerating ICS calendar...")
    generate_ics(matches, OUTPUT_FILE)
    print(f"Created {OUTPUT_FILE}")

    print("\nDone!")


if __name__ == "__main__":
    main()
