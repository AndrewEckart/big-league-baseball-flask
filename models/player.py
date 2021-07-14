import re
from types import SimpleNamespace
from typing import Any, Dict, List

import pandas as pd
import statsapi

from models.position import Position
from models.role import Role
from models.season import Season


class Player:
    name: str
    position: Position
    mlb_id: int
    team: str
    year: int = 2021
    season: Season
    stats_group: str
    stats: Dict[str, Any] = {}
    all_players: pd.DataFrame

    def __init__(self, name: str, position: Position, season: Season):
        match = re.match(r"^(.*)\s\((\d{4})\)$", name)
        if match is not None:
            name, year = match.groups()
            self.year = int(year)

        self.name = name
        self.position = position
        self.season = season
        self.mlb_id = self.all_players.loc[name, "MLBID"]

    def __repr__(self):
        attrs = ["name", "position", "mlb_id"]
        values = ", ".join([f"{attr}={getattr(self, attr)}" for attr in attrs])
        return f"{self.__class__.__name__}({values})"

    @property
    def notes(self) -> str:
        if self.year != self.season.year:
            return f"({self.year})"
        return ""

    def fetch_stats(self):
        stats_type = "season" if self.year == 2021 else "yearByYear"
        data = statsapi.player_stat_data(
            self.mlb_id, group=self.stats_group, type=stats_type
        )
        self.team = data.get("current_team")
        self.team = team_abbreviations.get(self.team, self.team)
        stats = data.get("stats", [])
        current_season = [s for s in stats if int(s["season"]) == self.year]
        if stats:
            self.stats = current_season[-1]["stats"]


class Hitter(Player):
    stats_group = "hitting"
    all_players = pd.read_csv("data/hitters.csv", index_col="Name")

    def __init__(self, name: str, position: Position, season: Season):
        if position == Position.PITCHER:
            raise ValueError("Pitchers cannot be position players!")
        super().__init__(name, position, season)

    @property
    def ab(self) -> int:
        return int(self.stats.get("atBats", 0))

    @property
    def runs(self) -> int:
        return int(self.stats.get("runs", 0))

    @property
    def hits(self) -> int:
        return int(self.stats.get("hits", 0))

    @property
    def hr(self) -> int:
        return int(self.stats.get("homeRuns", 0))

    @property
    def rbi(self) -> int:
        return int(self.stats.get("rbi", 0))

    @property
    def sb(self) -> int:
        return int(self.stats.get("stolenBases", 0))

    @property
    def avg(self) -> float:
        return self.hits / self.ab if self.ab else 0.0

    @property
    def formatted_avg(self):
        return format_batting_average(self.avg)

    def fetch_stats(self):
        super().fetch_stats()
        if self.year != 2021:
            for key in ["atBats", "runs", "hits", "homeRuns", "rbi", "stolenBases"]:
                if key not in self.stats:
                    continue
                self.stats[key] = round(0.7 * self.stats[key] * self.season.progress)


def format_batting_average(average: float) -> str:
    return f"{average:.3f}"


class HitterList(List[Hitter]):
    def __init__(self, *args, role: Role):
        super().__init__(*args)
        self.role = role

    def get_summary_stats(self, label=None):
        stats = SimpleNamespace(ab=0, runs=0, hits=0, hr=0, rbi=0, sb=0)
        for hitter in self:
            for attr in vars(stats):
                setattr(stats, attr, getattr(stats, attr) + getattr(hitter, attr))
        stats.avg = stats.hits / stats.ab if stats.ab else 0.0
        stats.formatted_avg = format_batting_average(stats.avg)
        if label:
            stats.name = label
        return stats


class Pitcher(Player):
    stats_group = "pitching"
    all_players = pd.read_csv("data/pitchers.csv", index_col="Name")

    def __init__(self, name: str, season: Season):
        super().__init__(name, Position.PITCHER, season)

    @property
    def ip(self) -> float:
        whole, fraction = divmod(float(self.stats.get("inningsPitched", 0.0)), 1)
        return whole + fraction * 10/3

    @property
    def formatted_ip(self) -> str:
        return format_innings_pitched(self.ip)

    @property
    def er(self) -> int:
        return int(self.stats.get("earnedRuns", 0))

    @property
    def wins(self) -> int:
        return int(self.stats.get("wins", 0))

    @property
    def saves(self) -> int:
        return int(self.stats.get("saves", 0))

    @property
    def strikeouts(self) -> int:
        return int(self.stats.get("strikeOuts", 0))

    @property
    def walks(self) -> int:
        return int(self.stats.get("baseOnBalls", 0))

    @property
    def earned_run_average(self) -> float:
        if not self.ip:
            return 0.0
        return 9 * self.er / self.ip

    @property
    def formatted_era(self) -> str:
        return format_era(self.earned_run_average)

    def fetch_stats(self):
        super().fetch_stats()
        if self.year != 2021:
            outs = round(self.stats.get("outs", 0) * 0.8 * self.season.progress)
            whole, fraction = divmod(outs, 3)
            self.stats["inningsPitched"] = f"{whole}.{fraction}"
            er = round(self.stats.get("earnedRuns", 0)*0.8*1.3*self.season.progress)
            self.stats["earnedRuns"] = er
            for key in ["wins", "saves", "strikeOuts", "baseOnBalls"]:
                if key not in self.stats:
                    continue
                self.stats[key] = round(0.7 * self.stats[key] * self.season.progress)


def format_innings_pitched(innings_pitched: float) -> str:
    return f"{innings_pitched:.2f}"


def format_era(earned_run_average: float) -> str:
    return f"{earned_run_average:.2f}"


class PitcherList(List[Pitcher]):

    def get_summary_stats(self, label="Total"):
        stats = SimpleNamespace(ip=0.0, er=0, wins=0, saves=0, strikeouts=0, walks=0)
        for pitcher in self:
            for attr in vars(stats):
                setattr(stats, attr, getattr(stats, attr) + getattr(pitcher, attr))
        stats.formatted_ip = format_innings_pitched(stats.ip)
        stats.era = 9 * stats.er / stats.ip if stats.ip else 0.0
        stats.formatted_era = format_era(stats.era)
        stats.name = label
        return stats


team_abbreviations = {
    "New York Yankees": "NYY",
    "Boston Red Sox": "BOS",
    "Tampa Bay Rays": "TB",
    "Toronto Blue Jays": "TOR",
    "Baltimore Orioles": "BAL",
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
    "Arizona Diamondbacks": "ARI"
}


if __name__ == "__main__":
    pitcher = Pitcher("Shane Bieber")
    pitcher.fetch_stats()
    print(pitcher.stats)

    hitter = Hitter("Albert Pujols (2019)", Position.FIRST_BASE)
    hitter.fetch_stats()
    print(hitter.stats)
