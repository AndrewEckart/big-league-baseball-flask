from __future__ import annotations

from enum import Enum


class Role(Enum):
    STARTER = 100
    BENCH = 50
    MINORS = 0


class Position(Enum):
    FIRST_BASE = "1B"
    SECOND_BASE = "2B"
    SHORTSTOP = "SS"
    THIRD_BASE = "3B"
    CATCHER = "C"
    DESIGNATED_HITTER = "DH"
    OUTFIELD = "OF"
    PITCHER = "P"

    def __str__(self):
        return self.value


INFIELD_POSITIONS: list[Position] = [
    Position.FIRST_BASE,
    Position.SECOND_BASE,
    Position.SHORTSTOP,
    Position.THIRD_BASE,
    Position.CATCHER,
    Position.DESIGNATED_HITTER,
]


TEAM_ABBREVIATIONS: dict[str, str] = {
    "New York Yankees": "NYY",
    "Boston Red Sox": "BOS",
    "Tampa Bay Rays": "TB",
    "Toronto Blue Jays": "TOR",
    "Baltimore Orioles": "BAL",
    "Cleveland Guardians": "CLE",
    "Cleveland Indians": "CLE",
    "Detroit Tigers": "DET",
    "Minnesota Twins": "MIN",
    "Chicago White Sox": "CWS",
    "Kansas City Royals": "KC",
    "Texas Rangers": "TEX",
    "Houston Astros": "HOU",
    "Seattle Mariners": "SEA",
    "Oakland Athletics": "OAK",
    "Los Angeles Angels": "LAA",
    "New York Mets": "NYM",
    "Atlanta Braves": "ATL",
    "Philadelphia Phillies": "PHI",
    "Washington Nationals": "WSH",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Chicago Cubs": "CHC",
    "St. Louis Cardinals": "STL",
    "Cincinnati Reds": "CIN",
    "Pittsburgh Pirates": "PIT",
    "San Francisco Giants": "SFG",
    "San Diego Padres": "SD",
    "Los Angeles Dodgers": "LAD",
    "Colorado Rockies": "COL",
    "Arizona Diamondbacks": "ARI",
}
