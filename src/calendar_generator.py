"""ICS calendar generation utilities."""

from datetime import datetime, timedelta
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
