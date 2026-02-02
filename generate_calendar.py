#!/usr/bin/env python3
"""Generate VCT 2026 ICS calendar from vlr.gg data."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.calendar_generator import generate_ics, append_to_calendar
from src.scraper import scrape_all_matches


def main():
    parser = argparse.ArgumentParser(description="Generate VCT 2026 calendar")
    parser.add_argument(
        "--stage",
        default="kickoff",
        choices=["kickoff", "masters", "stage1", "stage2", "champions"],
        help="Stage to generate calendar for (default: kickoff)",
    )
    parser.add_argument(
        "--output",
        default="vct-2026.ics",
        help="Output file path (default: vct-2026.ics)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing calendar instead of overwriting",
    )
    parser.add_argument(
        "--save-stage",
        action="store_true",
        help="Also save individual stage calendar to calendars/ folder",
    )
    args = parser.parse_args()

    print(f"Scraping VCT 2026 {args.stage} matches from vlr.gg...")
    matches = scrape_all_matches(args.stage)

    print(f"\nTotal matches found: {len(matches)}")

    for match in matches[:5]:
        print(f"  - {match.summary} @ {match.datetime_str}")
    if len(matches) > 5:
        print(f"  ... and {len(matches) - 5} more")

    if args.save_stage:
        calendars_dir = Path("calendars")
        calendars_dir.mkdir(exist_ok=True)
        stage_file = calendars_dir / f"{args.stage}.ics"
        print(f"\nSaving stage calendar to {stage_file}...")
        generate_ics(matches, str(stage_file))

    print(f"\nGenerating ICS calendar...")
    if args.append and Path(args.output).exists():
        added = append_to_calendar(matches, args.output)
        print(f"Appended {added} new events to {args.output}")
    else:
        generate_ics(matches, args.output)
        print(f"Created {args.output}")

    print("\nDone!")


if __name__ == "__main__":
    main()
