"""Scraper for vlr.gg VCT data."""

import re
import time
from datetime import datetime
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


def parse_wib_datetime(datetime_str: str, year: int = 2026) -> Optional[datetime]:
    """Parse WIB datetime string like '11:00 pm WIB, Jan 20' to datetime."""
    if not datetime_str or datetime_str == "-":
        return None

    datetime_str = datetime_str.replace("WIB,", "").replace("WIB", "").strip()
    datetime_str = re.sub(r"\s+", " ", datetime_str)

    try:
        dt = date_parser.parse(datetime_str, fuzzy=True)
        if dt.year == 1900 or dt.year < 2020:
            dt = dt.replace(year=year)
        return dt
    except (ValueError, TypeError):
        return None


def get_matches_from_tournament(tournament: Tournament) -> list[Match]:
    """Fetch all matches from a tournament page."""
    soup = get_soup(tournament.url)
    matches = []

    match_links = soup.select('a[href*="/"][href$="-ur1"], a[href*="/"][href$="-ur2"], '
                              'a[href*="/"][href$="-ur3"], a[href*="/"][href$="-ubf"], '
                              'a[href*="/"][href$="-mr1"], a[href*="/"][href$="-mr2"], '
                              'a[href*="/"][href$="-mr3"], a[href*="/"][href$="-mr4"], '
                              'a[href*="/"][href$="-mbf"], '
                              'a[href*="/"][href$="-lr1"], a[href*="/"][href$="-lr2"], '
                              'a[href*="/"][href$="-lr3"], a[href*="/"][href$="-lr4"], '
                              'a[href*="/"][href$="-lr5"], a[href*="/"][href$="-lbf"], '
                              'a[href*="/"][href$="-gf"]')

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
            phase_header = phase_parent.find_previous(string=re.compile(r"(Upper|Lower|Middle|Round|Final)", re.I))
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

        tournament_phase = phase_from_url or current_phase or "Match"

        team1 = "TBD"
        team2 = "TBD"
        score1 = None
        score2 = None

        match_rows = link.select("div > div")
        team_data = []
        for row in match_rows:
            img = row.select_one("img")
            if img:
                team_name_el = row.select_one("div:not(:has(img))")
                if team_name_el:
                    team_name = team_name_el.get_text(strip=True)
                else:
                    text_parts = [t for t in row.stripped_strings]
                    team_name = text_parts[0] if text_parts else ""

                score_el = row.find_next_sibling("div") or row.select_one("div:last-child")
                score = None
                if score_el:
                    score_text = score_el.get_text(strip=True)
                    if score_text.isdigit():
                        score = score_text

                if team_name and team_name not in ["-", "WIB"]:
                    team_data.append((team_name, score))

        if not team_data:
            link_text = link.get_text(separator="|", strip=True)
            parts = link_text.split("|")
            team_candidates = []
            for part in parts:
                part = part.strip()
                if part and not re.match(r"^[\d:\s]+[ap]m", part, re.I) and part not in ["-", "WIB"] and not re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", part):
                    score_match = re.match(r"^(.+?)(\d)$", part)
                    if score_match:
                        team_candidates.append((score_match.group(1).strip(), score_match.group(2)))
                    elif len(part) > 2 and not part.isdigit():
                        team_candidates.append((part, None))
            team_data = team_candidates[:2]

        if len(team_data) >= 2:
            team1, score1 = team_data[0]
            team2, score2 = team_data[1]
        elif len(team_data) == 1:
            team1, score1 = team_data[0]

        link_text = link.get_text(separator=" ", strip=True)
        datetime_match = re.search(r"(\d{1,2}:\d{2}\s*[ap]m\s*WIB,?\s*\w+\s*\d{1,2})", link_text, re.I)
        datetime_str = datetime_match.group(1) if datetime_match else ""

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
    """Scrape all matches from all tournaments in a stage."""
    tournaments = get_tournaments(stage_key)
    print(f"Found {len(tournaments)} tournaments for {stage_key}")

    all_matches = []
    for tournament in tournaments:
        print(f"  Scraping {tournament.name}...")
        matches = get_matches_from_tournament(tournament)
        print(f"    Found {len(matches)} matches")
        all_matches.extend(matches)

    return all_matches
