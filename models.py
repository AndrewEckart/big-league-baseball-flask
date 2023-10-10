from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from dataclasses import dataclass, field
import logging
import re
from types import SimpleNamespace
from typing import Any, Dict, List
from utils.cached_property import cached_property

import pandas as pd
import statsapi
import yaml

from constants import Position, Role, INFIELD_POSITIONS, TEAM_ABBREVIATIONS


@dataclass
class Rules:
    num_reserve_hitters: int
    num_pitchers: int
    team_innings_threshold: int
    innings_deficit_multiplier: float
    innings_surplus_multiplier: float
    injured_pitcher_innings_multiplier: float
    injured_pitcher_era_multiplier: float


@dataclass
class Season:
    year: int
    managers: list[str]
    rules: Rules
    teams: dict[str, "Team"] = field(init=False)
    league_id: int = 103  # Defaults to American League
    all_hitters: pd.DataFrame = field(init=False)
    all_pitchers: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.all_hitters = pd.read_csv(
            f"data/{self.year}/hitters.csv", index_col="Name"
        )
        self.all_pitchers = pd.read_csv(
            f"data/{self.year}/pitchers.csv", index_col="Name"
        )
        self.teams = {manager.lower(): Team(manager, self) for manager in self.managers}

    def fetch_all_stats(self):
        teams = self.teams.values()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(lambda t: t.fetch_all_stats(), t) for t in teams]
            wait(futures, return_when=ALL_COMPLETED)

    @property
    def standings(self) -> list["Team"]:
        self.fetch_all_stats()
        return sorted(self.teams.values(), key=lambda t: t.rating, reverse=True)

    @cached_property(ttl=10800)
    def avg_games_played(self) -> int:
        standings_data = statsapi.standings_data(self.league_id, season=self.year)
        total_games = 0
        teams = 0
        for _, division in standings_data.items():
            for team in division.get("teams", []):
                teams += 1
                total_games += team.get("w", 0)
                total_games += team.get("l", 0)
        result = round(total_games / teams)
        logging.info(f"Computed average games played: {result}")
        return result

    @property
    def progress(self) -> float:
        return self.avg_games_played / 162

    @property
    def last_year(self) -> int:
        if self.year == 2021:
            return 2019
        return self.year - 1


@dataclass
class Team:
    manager: str
    season: Season
    starters: "HitterList" = field(init=False)
    bench: "HitterList" = field(init=False)
    rotation: "PitcherList" = field(init=False)
    minors_hitters: "HitterList" = field(init=False)
    minors_pitchers: "PitcherList" = field(init=False)

    def __post_init__(self):
        path = f"data/{self.season.year}/teams/{self.manager.lower()}.yaml"
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            self.starters = self.parse_starters(data["starters"])
            self.bench = self.parse_bench(data["bench"])
            self.rotation = self.parse_rotation(data["rotation"])
            self.minors_hitters, self.minors_pitchers = self.parse_minors(
                data["minors"]
            )
        except FileNotFoundError:
            logging.warning(f"Team file not found: {path}")

    def __repr__(self):
        return f"{self.__class__.__name__}(manager='{self.manager}')"

    def parse_starters(self, data: Dict[str, Any]) -> "HitterList":
        if not len(data) == 7:
            raise ValueError("Expected 7 starter positions")

        outfielders = [
            Hitter(name, Position.OUTFIELD, self.season) for name in data["OF"]
        ]
        if len(outfielders) != 3:
            raise ValueError("Expected 3 starting OF")

        infielders = {
            pos: Hitter(data[pos.value], pos, self.season) for pos in INFIELD_POSITIONS
        }
        for p in INFIELD_POSITIONS:
            if not isinstance(infielders.get(p), Hitter):
                raise ValueError(f"Expected exactly one starting {p.value}")

        dh = infielders.pop(Position.DESIGNATED_HITTER)
        return HitterList([*infielders.values(), *outfielders, dh], role=Role.STARTER)

    def parse_bench(self, data: list[list[str]]) -> "HitterList":
        num_players_expected = self.season.rules.num_reserve_hitters
        if not len(data) == num_players_expected:
            raise ValueError(
                f"Expected {num_players_expected} bench hitters, not {len(data)}"
            )
        return HitterList(
            (Hitter(name, Position(pos), self.season) for pos, name in data),
            role=Role.BENCH,
        )

    def parse_rotation(self, data: list[str]) -> "PitcherList":
        num_players_expected = self.season.rules.num_pitchers
        if not len(data) == num_players_expected:
            raise ValueError(
                f"Expected {self.season.rules.num_pitchers} pitchers, not {len(data)}"
            )
        return PitcherList(Pitcher(name, self.season) for name in data)

    def parse_minors(self, data: list[list[str]]) -> tuple["HitterList", "PitcherList"]:
        if len(data) > 5:
            raise ValueError("Must have at most 5 players in minors")
        hitters, pitchers = HitterList(role=Role.MINORS), PitcherList()
        for pos, name in data:
            if pos == Position.PITCHER.value:
                pitchers.append(Pitcher(name, self.season))
            else:
                hitters.append(Hitter(name, Position(pos), self.season))
        # if len(pitchers) > 3:
        #     raise ValueError("Must have at most 3 pitchers in minors")
        return hitters, pitchers

    @property
    def players(self) -> List["Player"]:
        return [
            *self.starters,
            *self.bench,
            *self.minors_hitters,
            *self.rotation,
            *self.minors_pitchers,
        ]

    def fetch_all_stats(self):
        with ThreadPoolExecutor() as executor:
            executor.map(lambda p: p.fetch_stats(), self.players)

    @property
    def rating(self) -> float:
        return self.offense + self.pitching + self.innings_bonus_or_penalty

    @property
    def hitting_totals(self):
        starters = self.starters.get_summary_stats()
        bench = self.bench.get_summary_stats()
        totals = {}
        for v in vars(bench):
            if v in {"name", "formatted_avg"}:
                continue
            totals[v] = getattr(starters, v) + getattr(bench, v) / 2
        return SimpleNamespace(**totals)

    @property
    def offense(self) -> float:
        stats = self.hitting_totals
        rating = (stats.runs + stats.rbi) / 2 + stats.hr / 4 + stats.sb / 5
        avg = stats.hits / stats.ab if stats.ab else 0.0
        rating += (avg * 1000 - 250) * self.season.progress
        return rating

    @property
    def innings_bonus_or_penalty(self) -> float:
        stats = self.rotation.get_summary_stats()
        rules = self.season.rules
        innings_delta = stats.ip - (rules.team_innings_threshold * self.season.progress)
        if innings_delta >= 0:
            return innings_delta * rules.innings_surplus_multiplier
        else:
            return innings_delta * rules.innings_deficit_multiplier

    @property
    def pitching(self) -> float:
        stats = self.rotation.get_summary_stats()
        rating = stats.wins + stats.saves / 3 + (stats.strikeouts - stats.walks) / 10
        era = 9 * stats.er / stats.ip if stats.ip else 0.0
        rating -= era * self.season.avg_games_played
        return rating


class Player:
    name: str
    position: Position
    mlb_id: int
    team: str
    year: int
    season: Season
    stats_group: str
    stats: Dict[str, Any] = {}
    multiplier: float = 1

    def __init__(self, name: str, position: Position, season: Season):
        self.year = season.year
        match = re.match(r"^(.*)\s\((\d{4})\)$", name)
        if match is not None:
            name, year = match.groups()
            self.year = int(year)
            self.multiplier = 0.7 * season.progress

        self.name = name
        self.position = position
        self.season = season

    def __repr__(self):
        attrs = ["name", "position", "mlb_id"]
        values = ", ".join([f"{attr}={getattr(self, attr)}" for attr in attrs])
        return f"{self.__class__.__name__}({values})"

    @property
    def mlb_profile_url(self) -> str:
        return f"https://www.mlb.com/player/{self.mlb_id}"

    @property
    def notes(self) -> str:
        notes = ""
        if self.multiplier != 1:
            notes += f"{round(self.multiplier * 100)}%"
        if self.year != self.season.year:
            notes += f" of {self.year}"
        return notes

    def fetch_stats(self):
        data = statsapi.player_stat_data(
            self.mlb_id, group=self.stats_group, type="yearByYear"
        )
        self.team = data.get("current_team")
        self.team = TEAM_ABBREVIATIONS.get(self.team, self.team)
        results = data.get("stats", [])
        stats = [s["stats"] for s in results if int(s["season"]) == self.year]
        if stats:
            self.stats = max(stats, key=lambda s: s["gamesPlayed"])


class Hitter(Player):
    stats_group = "hitting"

    def __init__(self, name: str, position: Position, season: Season):
        if position == Position.PITCHER:
            raise ValueError("Pitchers cannot be position players!")

        match = re.match(r"^(.*)\s\(90%\)$", name)
        if match is not None:
            name = match.groups()[0]
            self.multiplier = 0.9

        super().__init__(name, position, season)
        self.mlb_id = season.all_hitters.loc[self.name, "MLBID"]

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
        if self.multiplier != 1:
            for key in ["atBats", "runs", "hits", "homeRuns", "rbi", "stolenBases"]:
                if key not in self.stats:
                    continue
                self.stats[key] = self.multiplier * self.stats[key]


def format_batting_average(average: float) -> str:
    return f"{average:.3f}"


class HitterList(List[Hitter]):
    def __init__(self, *args, role: Role):
        super().__init__(*args)
        self.role = role

    def get_summary_stats(self, label="Total"):
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

    def __init__(self, name: str, season: Season):
        super().__init__(name, Position.PITCHER, season)
        self.mlb_id = season.all_pitchers.loc[self.name, "MLBID"]

    @property
    def ip(self) -> float:
        whole, fraction = divmod(float(self.stats.get("inningsPitched", 0.0)), 1)
        return whole + fraction * 10 / 3

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
        season, stats = self.season, self.stats
        if self.year != season.year:
            rules = season.rules
            ip_multiplier = rules.injured_pitcher_innings_multiplier
            er_multiplier = rules.injured_pitcher_era_multiplier
            outs = stats.get("outs", 0) * ip_multiplier * season.progress
            whole, fraction = divmod(outs, 3)
            stats["inningsPitched"] = f"{whole}.{fraction}"
            er = (stats.get("earnedRuns", 0)
                * ip_multiplier
                * er_multiplier
                * season.progress
            )
            stats["earnedRuns"] = er
        if self.multiplier != 1:
            for key in ["wins", "saves", "strikeOuts", "baseOnBalls"]:
                if key not in stats:
                    continue
                stats[key] = self.multiplier * stats[key]


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


if __name__ == "__main__":
    rules = Rules(
        num_reserve_hitters=4,
        num_pitchers=7,
        team_innings_threshold=900,
        innings_deficit_multiplier=1/3,
        innings_surplus_multiplier=0,
        injured_pitcher_innings_multiplier=0.8,
        injured_pitcher_era_multiplier=1.3,
    )
    szn = Season(year=2023, managers=["Andrew"], rules=rules)
    andrew = Team("Andrew", szn)

    pitcher = Pitcher("Shane Bieber", szn)
    pitcher.fetch_stats()
    print(pitcher.stats)

    hitter = Hitter("Aaron Judge", Position.OUTFIELD, szn)
    hitter.fetch_stats()
    print(hitter.stats)
    print(HitterList([hitter], role=Role.STARTER).get_summary_stats().mlb_profile_url)

