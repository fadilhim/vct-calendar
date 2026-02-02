#!/usr/bin/env python3
"""Update existing VCT 2026 ICS calendar with latest data from vlr.gg."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

sys.path.insert(0, str(Path(__file__).parent))

from src.calendar_generator import WIB, UTC, match_to_event, get_stages_in_calendar
from src.scraper import scrape_all_matches


def load_existing_calendar(path: str) -> tuple[Calendar, dict]:
    """Load existing ICS file and extract UIDs."""
    with open(path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    existing_uids = {}
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get("uid", ""))
            if uid:
                existing_uids[uid] = component

    return cal, existing_uids


def update_calendar(input_path: str, output_path: str = None, stages: list[str] = None) -> dict:
    """Update existing calendar with fresh data from vlr.gg.
    
    Only updates existing events, never adds new ones.
    If stages is None, auto-detects stages from the calendar.
    """
    if output_path is None:
        output_path = input_path

    print(f"Loading existing calendar from {input_path}...")
    cal, existing_uids = load_existing_calendar(input_path)
    print(f"Found {len(existing_uids)} existing events")

    if stages is None:
        stages = list(get_stages_in_calendar(input_path))
        print(f"Auto-detected stages: {', '.join(stages)}")

    print(f"\nScraping latest data from vlr.gg...")
    matches = []
    for stage in stages:
        print(f"  Fetching {stage}...")
        stage_matches = scrape_all_matches(stage)
        matches.extend(stage_matches)
    print(f"Found {len(matches)} total matches from vlr.gg")

    stats = {"updated": 0, "unchanged": 0, "skipped_new": 0, "skipped_no_time": 0}

    for match in matches:
        uid = match.uid

        if uid not in existing_uids:
            stats["skipped_new"] += 1
            continue

        if not match.datetime_wib:
            stats["skipped_no_time"] += 1
            continue

        existing_event = existing_uids[uid]
        new_event = match_to_event(match)

        if not new_event:
            stats["skipped_no_time"] += 1
            continue

        changes = []

        old_summary = str(existing_event.get("summary", ""))
        new_summary = str(new_event.get("summary", ""))
        if old_summary != new_summary:
            changes.append(f"summary: '{old_summary}' → '{new_summary}'")

        old_start = existing_event.get("dtstart")
        new_start = new_event.get("dtstart")
        if old_start and new_start:
            old_dt = old_start.dt if hasattr(old_start, 'dt') else old_start
            new_dt = new_start.dt if hasattr(new_start, 'dt') else new_start
            if old_dt != new_dt:
                changes.append(f"time: {old_dt} → {new_dt}")

        old_status = str(existing_event.get("status", ""))
        new_status = str(new_event.get("status", ""))
        if old_status != new_status:
            changes.append(f"status: {old_status} → {new_status}")

        if changes:
            existing_event["summary"] = new_event["summary"]
            existing_event["dtstart"] = new_event["dtstart"]
            existing_event["dtend"] = new_event["dtend"]
            existing_event["status"] = new_event["status"]
            existing_event["dtstamp"] = datetime.now(UTC)

            print(f"  Updated {uid}: {', '.join(changes)}")
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    with open(output_path, "wb") as f:
        f.write(cal.to_ical())

    print(f"\nUpdate complete:")
    print(f"  - Updated: {stats['updated']}")
    print(f"  - Unchanged: {stats['unchanged']}")
    print(f"  - Skipped (new events): {stats['skipped_new']}")
    print(f"  - Skipped (no time): {stats['skipped_no_time']}")
    print(f"\nSaved to {output_path}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Update VCT 2026 calendar with latest data")
    parser.add_argument(
        "--input",
        default="vct-2026.ics",
        help="Input ICS file to update (default: vct-2026.ics)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: same as input)",
    )
    parser.add_argument(
        "--stage",
        choices=["kickoff", "masters", "stage1", "stage2", "champions"],
        action="append",
        dest="stages",
        help="Stage(s) to update. Can be specified multiple times. If not specified, auto-detects from calendar.",
    )
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: {args.input} not found. Run generate_calendar.py first.")
        sys.exit(1)

    update_calendar(args.input, args.output, args.stages)


if __name__ == "__main__":
    main()
