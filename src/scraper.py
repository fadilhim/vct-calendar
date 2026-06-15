"""Scraper for vlr.gg VCT data."""

import re
import time
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .config import BASE_URL, EXCLUDED_REGIONS, HEADERS, REQUEST_DELAY, STAGES
from .models import Match, Tournament


def get_soup(url: str) -> BeautifulSoup:
    """Fetch a page and return BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return BeautifulSoup(response.text, "html.parser")


def get_tournaments(stage_key: str = "kickoff") -> list[Tournament]:
    """Fetch all tournaments for a given stage, excluding specified regions."""
    stage = STAGES.get(stage_key)
    if not stage:
        raise ValueError(f"Unknown stage: {stage_key}")

    url = f"{BASE_URL}/vct/?region=all&stage={stage['id']}"
    soup = get_soup(url)

    tournaments = []
    event_links = soup.select('a[href^="/event/"]')

    for link in event_links:
        href = link.get("href", "")
        if not href.startswith("/event/"):
            continue

        parts = href.split("/")
        if len(parts) < 3:
            continue

        event_id = parts[2]
        slug = parts[3] if len(parts) > 3 else ""

        name = extract_tournament_name(slug)
        if not name:
            continue

        region = ""
        for r in ["Americas", "EMEA", "Pacific", "China"]:
            if r.lower() in name.lower():
                region = r
                break

        if region in EXCLUDED_REGIONS:
            continue

        dates_el = link.select_one(".event-item-desc-item-value, div:nth-child(3)")
        dates = dates_el.get_text(strip=True) if dates_el else ""

        tournament = Tournament(
            event_id=event_id,
            name=name,
            slug=slug,
            region=region,
            dates=dates,
            url=urljoin(BASE_URL, href),
        )

        if not any(t.event_id == tournament.event_id for t in tournaments):
            tournaments.append(tournament)

    return tournaments


def extract_tournament_name(slug: str) -> str:
    """Extract tournament name from URL slug."""
    if not slug:
        return ""
    name = slug.replace("-", " ").title()
    name = name.replace("Vct", "VCT").replace("Emea", "EMEA")
    return name


def parse_tournament_dates(dates: str, year: int = 2026) -> tuple[Optional[date], Optional[date]]:
    """Parse a VLR tournament date range into start and end dates."""
    if not dates:
        return None, None

    normalized = dates.replace("Dates", "").strip()
    parts = [part.strip() for part in re.split(r"[—-]", normalized, maxsplit=1)]
    if not parts:
        return None, None

    start = parse_tournament_date_part(parts[0], year)
    end = None
    if len(parts) > 1 and parts[1].upper() != "TBD":
        end = parse_tournament_date_part(parts[1], year, default_month=start.month if start else None)

    return start, end


def parse_tournament_date_part(
    value: str, year: int, default_month: Optional[int] = None
) -> Optional[date]:
    """Parse one side of a VLR tournament date range."""
    value = value.strip()
    if not value or value.upper() == "TBD":
        return None

    if default_month and not re.search(r"[A-Za-z]", value):
        value = f"{date(year, default_month, 1).strftime('%b')} {value}"

    try:
        dt = date_parser.parse(value, default=datetime(year, 1, 1), fuzzy=True)
        return dt.date()
    except (ValueError, TypeError):
        return None


def should_scrape_tournament(tournament: Tournament, reference_date: Optional[date] = None) -> bool:
    """Return whether a tournament is current or upcoming."""
    today = reference_date or datetime.now().date()
    start, end = parse_tournament_dates(tournament.dates)

    if end:
        return end >= today
    if start:
        return start >= today
    return True


def parse_wib_datetime(
    datetime_str: str,
    year: int = 2026,
    reference_datetime: Optional[datetime] = None,
) -> Optional[datetime]:
    """Parse WIB datetime string from VLR cards into a naive datetime.

    Supports explicit dates and relative labels such as "Today"/"Tomorrow".
    """
    if not datetime_str or datetime_str == "-":
        return None

    ref = reference_datetime or datetime.now()
    normalized = datetime_str.strip()

    # Handle relative labels commonly used on current match cards.
    lowered = normalized.lower()
    relative_day = None
    if lowered.startswith("today"):
        relative_day = ref.date()
    elif lowered.startswith("tomorrow"):
        relative_day = (ref + timedelta(days=1)).date()
    elif lowered.startswith("yesterday"):
        relative_day = (ref - timedelta(days=1)).date()

    if relative_day is not None:
        time_match = re.search(r"\b(\d{1,2}:\d{2}\s*[ap]m)\b", normalized, re.I)
        if time_match:
            normalized = f"{time_match.group(1)} {relative_day.strftime('%b %d %Y')}"

    normalized = normalized.replace("WIB,", "").replace("WIB", "").strip()
    normalized = re.sub(r"\s+", " ", normalized)

    try:
        dt = date_parser.parse(normalized, fuzzy=True)
        if dt.year == 1900 or dt.year < 2020:
            dt = dt.replace(year=year)
        return dt
    except (ValueError, TypeError):
        return None


def extract_match_datetime_str(link_text: str) -> str:
    """Extract a datetime text from a match card text blob.

    Supports:
    - "11:00 pm WIB, Jan 20"
    - "Mar 1 12:00 am" (date + time without WIB)
    """
    if not link_text:
        return ""

    # Legacy VLR format with explicit WIB marker.
    match = re.search(
        r"(\d{1,2}:\d{2}\s*[ap]m\s*WIB,?\s*\w+\s*\d{1,2})",
        link_text,
        re.I,
    )
    if match:
        return match.group(1)

    # Current event-card format: "Mar 1 ... 12:00 am"
    compact = re.sub(r"\s+", " ", link_text).strip()

    # Relative labels used in some list/cards (e.g. "Today 4:00 PM").
    match = re.search(
        r"\b(Today|Tomorrow|Yesterday)\b.*?\b(\d{1,2}:\d{2}\s*[ap]m)\b",
        compact,
        re.I,
    )
    if match:
        return f"{match.group(1)} {match.group(2)}"

    match = re.search(
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\b.*?\b(\d{1,2}:\d{2}\s*[ap]m)\b",
        compact,
        re.I,
    )
    if match:
        # Normalize to parser-friendly token order.
        return f"{match.group(2)} {match.group(1)}"

    # Full month names (e.g. "March 8, 2026 ... 4:00 PM").
    match = re.search(
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?)\b.*?\b(\d{1,2}:\d{2}\s*[ap]m)\b",
        compact,
        re.I,
    )
    if match:
        return f"{match.group(2)} {match.group(1)}"

    # Inverse ordering occasionally appears: "4:00 PM ... March 8, 2026".
    match = re.search(
        r"\b(\d{1,2}:\d{2}\s*[ap]m)\b.*?\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?)\b",
        compact,
        re.I,
    )
    if match:
        return f"{match.group(1)} {match.group(2)}"

    return ""


def extract_match_teams(link) -> tuple[str, str, Optional[str], Optional[str]]:
    """Extract team names and optional scores from a match link/card."""
    team1 = "TBD"
    team2 = "TBD"
    score1 = None
    score2 = None

    # Main bracket card format (e.g. Masters event page).
    bracket_names = [
        el.get_text(strip=True)
        for el in link.select(".team-name div")
        if el.get_text(strip=True)
    ]
    if len(bracket_names) >= 2:
        team1, team2 = bracket_names[0], bracket_names[1]

        left = link.select_one(".score-left")
        right = link.select_one(".score-right")
        if left:
            left_text = left.get_text(strip=True)
            if left_text.isdigit():
                score1 = left_text
        if right:
            right_text = right.get_text(strip=True)
            if right_text.isdigit():
                score2 = right_text
        return team1, team2, score1, score2

    # Sidebar/upcoming list format.
    sidebar_names = [
        el.get_text(strip=True)
        for el in link.select(".event-sidebar-matches-team .name span")
        if el.get_text(strip=True)
    ]
    if len(sidebar_names) >= 2:
        return sidebar_names[0], sidebar_names[1], None, None

    # Legacy generic fallback.
    link_text = link.get_text(separator="|", strip=True)
    parts = [p.strip() for p in link_text.split("|") if p.strip()]
    team_candidates = []
    for part in parts:
        if re.match(r"^[\d:\s]+[ap]m$", part, re.I):
            continue
        if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", part):
            continue
        if re.match(r"^(Round|Upper|Lower|Middle|Grand|Final|Bo\\d+)$", part, re.I):
            continue
        if part in {"-", "WIB"}:
            continue
        if len(part) > 1 and not part.isdigit():
            team_candidates.append(part)

    if len(team_candidates) >= 2:
        return team_candidates[0], team_candidates[1], None, None
    if len(team_candidates) == 1:
        return team_candidates[0], "TBD", None, None
    return team1, team2, score1, score2


def get_matches_from_tournament(tournament: Tournament) -> list[Match]:
    """Fetch all matches from a tournament page."""
    matches = []
    # Some events (e.g. Masters) keep bracket matches on dedicated tabs like /playoffs.
    # Scrape all known tabs and dedupe by match_id at the end.
    page_urls = [
        tournament.url,
        f"{tournament.url}/playoffs",
        f"{tournament.url}/swiss-stage",
        f"{tournament.url}/group-stage",
        f"{tournament.url}/matches",
    ]
    seen_pages = set()

    for page_url in page_urls:
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)

        try:
            soup = get_soup(page_url)
        except requests.RequestException:
            continue

        match_links = soup.select('a[href*="/"][href$="-ur1"], a[href*="/"][href$="-ur2"], '
                                  'a[href*="/"][href$="-ur3"], a[href*="/"][href$="-ubf"], '
                                  'a[href*="/"][href$="-ubqf"], a[href*="/"][href$="-uqf"], '
                                  'a[href*="/"][href$="-usf"], a[href*="/"][href$="-ubsf"], '
                                  'a[href*="/"][href$="-mr1"], a[href*="/"][href$="-mr2"], '
                                  'a[href*="/"][href$="-mr3"], a[href*="/"][href$="-mr4"], '
                                  'a[href*="/"][href$="-mbf"], '
                                  'a[href*="/"][href$="-lr1"], a[href*="/"][href$="-lr2"], '
                                  'a[href*="/"][href$="-lr3"], a[href*="/"][href$="-lr4"], '
                                  'a[href*="/"][href$="-lr5"], a[href*="/"][href$="-lbf"], '
                                  'a[href*="/"][href$="-gf"], a[href*="/"][href$="-r1"], '
                                  'a[href*="/"][href$="-r2"], a[href*="/"][href$="-r3"]')

        if not match_links:
            match_links = soup.select('a[href^="/"][class*="match"]')

        if not match_links:
            bracket_container = soup.select_one(".event-bracket, .bracket")
            if bracket_container:
                match_links = bracket_container.select("a[href]")

        if not match_links:
            all_links = soup.select('a[href^="/"]')
            match_pattern = re.compile(r"^/\d{5,7}/")
            match_links = [link for link in all_links if match_pattern.match(link.get("href", ""))]

        current_phase = ""

        for link in match_links:
            href = link.get("href", "")

            match_id_match = re.search(r"/(\d{5,7})/", href)
            if not match_id_match:
                continue

            match_id = match_id_match.group(1)

            phase_parent = link.find_parent(class_=lambda x: x and "round" in x.lower()) if hasattr(link, 'find_parent') else None
            if phase_parent:
                phase_header = phase_parent.find_previous(string=re.compile(r"(Upper|Lower|Middle|Round|Final|Quarterfinal|Semifinal)", re.I))
                if phase_header:
                    current_phase = phase_header.strip()

            phase_from_url = ""
            url_parts = href.lower()
            if "-ur1" in url_parts:
                phase_from_url = "Upper Round 1"
            elif "-ur2" in url_parts:
                phase_from_url = "Upper Round 2"
            elif "-ur3" in url_parts:
                phase_from_url = "Upper Round 3"
            elif "-ubqf" in url_parts:
                phase_from_url = "Upper Quarterfinals"
            elif "-uqf" in url_parts:
                phase_from_url = "Upper Quarterfinals"
            elif "-usf" in url_parts or "-ubsf" in url_parts:
                phase_from_url = "Upper Semifinals"
            elif "-ubf" in url_parts:
                phase_from_url = "Upper Final"
            elif "-mr1" in url_parts:
                phase_from_url = "Middle Round 1"
            elif "-mr2" in url_parts:
                phase_from_url = "Middle Round 2"
            elif "-mr3" in url_parts:
                phase_from_url = "Middle Round 3"
            elif "-mr4" in url_parts:
                phase_from_url = "Middle Round 4"
            elif "-mbf" in url_parts:
                phase_from_url = "Middle Final"
            elif "-lr1" in url_parts:
                phase_from_url = "Lower Round 1"
            elif "-lr2" in url_parts:
                phase_from_url = "Lower Round 2"
            elif "-lr3" in url_parts:
                phase_from_url = "Lower Round 3"
            elif "-lr4" in url_parts:
                phase_from_url = "Lower Round 4"
            elif "-lr5" in url_parts:
                phase_from_url = "Lower Round 5"
            elif "-lbf" in url_parts:
                phase_from_url = "Lower Final"
            elif "-gf" in url_parts:
                phase_from_url = "Grand Final"
            elif "-r1" in url_parts:
                phase_from_url = "Round 1"
            elif "-r2" in url_parts:
                phase_from_url = "Round 2"
            elif "-r3" in url_parts:
                phase_from_url = "Round 3"

            tournament_phase = phase_from_url or current_phase or "Match"

            team1, team2, score1, score2 = extract_match_teams(link)

            link_text = link.get_text(separator=" ", strip=True)
            datetime_str = extract_match_datetime_str(link_text)

            dt = parse_wib_datetime(datetime_str)

            match = Match(
                match_id=match_id,
                event_name=tournament.name,
                tournament_phase=tournament_phase,
                team1=team1 or "TBD",
                team2=team2 or "TBD",
                datetime_wib=dt,
                datetime_str=datetime_str,
                match_url=urljoin(BASE_URL, href),
                score1=score1,
                score2=score2,
            )

            if not any(m.match_id == match.match_id for m in matches):
                matches.append(match)

    return matches


def scrape_all_matches(stage_key: str = "kickoff") -> list[Match]:
    """Scrape matches from current and upcoming tournaments in a stage."""
    tournaments = get_tournaments(stage_key)
    print(f"Found {len(tournaments)} tournaments for {stage_key}")

    all_matches = []
    for tournament in tournaments:
        if not should_scrape_tournament(tournament):
            print(f"  Skipping past tournament {tournament.name} ({tournament.dates})")
            continue

        print(f"  Scraping {tournament.name} ({tournament.dates})...")
        matches = get_matches_from_tournament(tournament)
        print(f"    Found {len(matches)} matches")
        all_matches.extend(matches)

    return all_matches
