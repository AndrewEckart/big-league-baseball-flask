from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import statsapi

from models.position import Position
from models.role import Role


class Player:
    name: str
    position: Position
    mlb_id: int
    team: str
    stats_group: str
    season_stats: Dict[str, Any] = {}

    def __repr__(self):
        attrs = ["name", "position", "mlb_id"]
        values = ", ".join([f"{attr}={getattr(self, attr)}" for attr in attrs])
        return f"{self.__class__.__name__}({values})"

    def fetch_stats(self):
        data = statsapi.player_stat_data(self.mlb_id, group=self.stats_group)
        self.team = data.get("current_team")
        self.team = team_abbreviations.get(self.team, self.team)
        stats = data.get("stats")
        if stats:
            season_stats = next(s for s in stats if int(s["season"]) == 2021)
            self.season_stats = season_stats["stats"]


class Hitter(Player):
    stats_group = "hitting"
    all_players = pd.read_csv("data/hitters.csv", index_col="Name")

    def __init__(self, name: str, position: Position):
        if position == Position.PITCHER:
            raise ValueError("Pitchers cannot be position players!")

        self.name = name
        self.position = position
        self.mlb_id = self.all_players.loc[name, "MLBID"]

    @property
    def ab(self) -> int:
        return int(self.season_stats.get("atBats", 0))

    @property
    def runs(self) -> int:
        return int(self.season_stats.get("runs", 0))

    @property
    def hits(self) -> int:
        return int(self.season_stats.get("hits", 0))

    @property
    def hr(self) -> int:
        return int(self.season_stats.get("homeRuns", 0))

    @property
    def rbi(self) -> int:
        return int(self.season_stats.get("rbi", 0))

    @property
    def sb(self) -> int:
        return int(self.season_stats.get("stolenBases", 0))

    @property
    def avg(self) -> float:
        return self.hits / self.ab if self.ab else 0.0

    @property
    def formatted_avg(self):
        return format_batting_average(self.avg)


def format_batting_average(average: float) -> str:
    return f"{average:.3f}"


class HitterList(list):
    def __init__(self, *args, role: Role):
        super().__init__(*args)
        self.role = role

    def get_summary_stats(self, label=None):
        stats = SimpleNamespace(ab=0, runs=0, hits=0, hr=0, rbi=0, sb=0)
        for hitter in self:
            for attr in vars(stats):
                setattr(stats, attr, getattr(stats, attr) + getattr(hitter, attr))
        stats.formatted_avg = format_batting_average(stats.hits / stats.ab)
        if label:
            stats.name = label
        return stats


class Pitcher(Player):
    stats_group = "pitching"
    all_players = pd.read_csv("data/pitchers.csv", index_col="Name")

    def __init__(self, name: str):
        self.name = name
        self.position = Position.PITCHER
        self.mlb_id = self.all_players.loc[name, "MLBID"]

    @property
    def ip(self) -> float:
        whole, fraction = divmod(float(self.season_stats.get("inningsPitched", 0.0)), 1)
        return whole + fraction * 10/3

    @property
    def formatted_ip(self) -> str:
        return format_innings_pitched(self.ip)

    @property
    def er(self) -> int:
        return int(self.season_stats.get("earnedRuns", 0))

    @property
    def wins(self) -> int:
        return int(self.season_stats.get("wins", 0))

    @property
    def saves(self) -> int:
        return int(self.season_stats.get("saves", 0))

    @property
    def strikeouts(self) -> int:
        return int(self.season_stats.get("strikeOuts", 0))

    @property
    def walks(self) -> int:
        return int(self.season_stats.get("baseOnBalls", 0))

    @property
    def earned_run_average(self) -> float:
        if not self.ip:
            return 0.0
        return 9 * self.er / self.ip

    @property
    def formatted_era(self) -> str:
        return format_era(self.earned_run_average)


def format_innings_pitched(innings_pitched: float) -> str:
    return f"{innings_pitched:.2f}"


def format_era(earned_run_average: float) -> str:
    return f"{earned_run_average:.2f}"


class PitcherList(list):

    def get_summary_stats(self, label="Total"):
        stats = SimpleNamespace(ip=0.0, er=0, wins=0, saves=0, strikeouts=0, walks=0)
        for pitcher in self:
            for attr in vars(stats):
                setattr(stats, attr, getattr(stats, attr) + getattr(pitcher, attr))
        stats.formatted_ip = format_innings_pitched(stats.ip)
        stats.formatted_era = format_era(9 * stats.er / stats.ip)
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
    "Los Angeles Angels": "LAA"
}


if __name__ == "__main__":
    hitter = Hitter("Gary Sanchez", Position.OUTFIELD)
    pitcher = Pitcher("Shane Bieber")

    hitter.fetch_stats()
    Hitter("Mike Trout", Position.OUTFIELD).fetch_stats()
    pitcher.fetch_stats()
