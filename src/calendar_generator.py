"""ICS calendar generation utilities."""

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event, vText

from .models import Match


WIB = ZoneInfo("Asia/Jakarta")  # UTC+7
UTC = ZoneInfo("UTC")


def create_calendar() -> Calendar:
    """Create a new ICS calendar with proper headers."""
    cal = Calendar()
    cal.add("prodid", "-//VCT 2026 Calendar//vlr.gg//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "Valorant Champions Tour")
    cal.add("x-wr-timezone", "UTC")
    return cal


def match_to_event(match: Match) -> Optional[Event]:
    """Convert a Match to an ICS Event."""
    if not match.datetime_wib:
        return None

    event = Event()

    event.add("uid", match.uid)
    event.add("summary", match.summary)

    dt_wib = match.datetime_wib.replace(tzinfo=WIB)
    dt_utc = dt_wib.astimezone(UTC)

    event.add("dtstart", dt_utc)
    event.add("dtend", dt_utc + timedelta(hours=2))

    event.add("description", f"Watch: {match.match_url}")
    event.add("url", match.match_url)

    event.add("dtstamp", datetime.now(UTC))

    if match.score1 and match.score2:
        event.add("status", "CONFIRMED")
    else:
        event.add("status", "TENTATIVE")

    return event


def generate_ics(matches: list[Match], output_path: str = "vct-2026.ics") -> str:
    """Generate an ICS file from a list of matches."""
    cal = create_calendar()

    events_added = 0
    for match in matches:
        event = match_to_event(match)
        if event:
            cal.add_component(event)
            events_added += 1

    with open(output_path, "wb") as f:
        f.write(cal.to_ical())

    print(f"Generated {output_path} with {events_added} events")
    return output_path


def append_to_calendar(matches: list[Match], calendar_path: str) -> int:
    """Append new matches to an existing calendar file.
    
    Only adds matches with UIDs that don't already exist.
    Returns the number of events added.
    """
    with open(calendar_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    existing_uids = set()
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get("uid", ""))
            if uid:
                existing_uids.add(uid)

    events_added = 0
    for match in matches:
        if match.uid in existing_uids:
            continue

        event = match_to_event(match)
        if event:
            cal.add_component(event)
            events_added += 1
            print(f"  Added: {match.summary}")

    with open(calendar_path, "wb") as f:
        f.write(cal.to_ical())

    return events_added


def stage_from_summary(summary: str) -> Optional[str]:
    """Infer stage key from event summary."""
    if "Kickoff" in summary:
        return "kickoff"
    if "Masters" in summary:
        return "masters"
    if "Stage 1" in summary:
        return "stage1"
    if "Stage 2" in summary:
        return "stage2"
    if "Champions" in summary:
        return "champions"
    return None


def get_stages_in_calendar(calendar_path: str) -> set[str]:
    """Get the set of stages present in a calendar file."""
    with open(calendar_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    stages = set()
    for component in cal.walk():
        if component.name == "VEVENT":
            summary = str(component.get("summary", ""))
            stage = stage_from_summary(summary)
            if stage:
                stages.add(stage)

    return stages


def get_upcoming_stages_in_calendar(
    calendar_path: str, reference_time: Optional[datetime] = None
) -> set[str]:
    """Get stages that still have at least one event in the future."""
    with open(calendar_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    now = reference_time or datetime.now(UTC)
    upcoming_stages = set()

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("summary", ""))
        stage = stage_from_summary(summary)
        if not stage:
            continue

        dt_value = component.get("dtend") or component.get("dtstart")
        if not dt_value:
            continue

        event_dt = dt_value.dt if hasattr(dt_value, "dt") else dt_value
        if isinstance(event_dt, date) and not isinstance(event_dt, datetime):
            event_dt = datetime.combine(event_dt, time.min).replace(tzinfo=UTC)
        elif event_dt.tzinfo is None:
            event_dt = event_dt.replace(tzinfo=UTC)
        else:
            event_dt = event_dt.astimezone(UTC)

        if event_dt >= now:
            upcoming_stages.add(stage)

    return upcoming_stages
