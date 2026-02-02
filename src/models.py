"""Data models for VCT Calendar."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Tournament:
    event_id: str
    name: str
    slug: str
    region: str
    dates: str
    url: str


@dataclass
class Match:
    match_id: str
    event_name: str
    tournament_phase: str
    team1: str
    team2: str
    datetime_wib: Optional[datetime]
    datetime_str: str
    match_url: str
    score1: Optional[str] = None
    score2: Optional[str] = None

    @property
    def uid(self) -> str:
        return f"match-{self.match_id}@vlr.gg"

    @property
    def summary(self) -> str:
        return f"{self.event_name} - {self.team1} vs {self.team2} ({self.tournament_phase})"
