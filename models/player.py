from typing import Any, Dict

import pandas as pd
import statsapi

from models.position import Position


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
    def at_bats(self) -> int:
        return int(self.season_stats.get("atBats", 0))

    @property
    def runs(self) -> int:
        return int(self.season_stats.get("runs", 0))

    @property
    def hits(self) -> int:
        return int(self.season_stats.get("hits", 0))

    @property
    def home_runs(self) -> int:
        return int(self.season_stats.get("homeRuns", 0))

    @property
    def rbi(self) -> int:
        return int(self.season_stats.get("rbi", 0))

    @property
    def stolen_bases(self) -> int:
        return int(self.season_stats.get("stolenBases", 0))

    @property
    def batting_average(self) -> float:
        return self.hits / self.at_bats if self.at_bats else 0.0

    @property
    def batting_average_str(self):
        return f"{self.batting_average:.3f}"


class HitterList(list):
    pass


class Pitcher(Player):
    stats_group = "pitching"
    all_players = pd.read_csv("data/pitchers.csv", index_col="Name")

    def __init__(self, name: str):
        self.name = name
        self.position = Position.PITCHER
        self.mlb_id = self.all_players.loc[name, "MLBID"]

    @property
    def innings_pitched(self) -> float:
        whole, fraction = divmod(float(self.season_stats.get("inningsPitched", 0.0)), 1)
        return whole + fraction * 10/3

    @property
    def innings_pitched_str(self) -> str:
        return f"{self.innings_pitched:.2f}"

    @property
    def earned_runs(self) -> int:
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
        if not self.innings_pitched:
            return 0.0
        return 9 * self.earned_runs / self.innings_pitched

    @property
    def earned_run_average_str(self) -> str:
        return f"{self.earned_run_average:.2f}"


class PitcherList(list):
    pass


if __name__ == "__main__":
    hitter = Hitter("Gary Sanchez", Position.OUTFIELD)
    pitcher = Pitcher("Shane Bieber")

    hitter.fetch_stats()
    Hitter("Mike Trout", Position.OUTFIELD).fetch_stats()
    pitcher.fetch_stats()
