from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import List

import yaml

from models.player import Player, Hitter, Pitcher, HitterList, PitcherList
from models.position import Position, infield
from models.role import Role
from models.season import Season, League


def parse_starters(data) -> HitterList:
    if not len(data) == 7:
        raise ValueError("Expected 7 starter positions")

    outfielders = [Hitter(name, Position.OUTFIELD) for name in data["OF"]]
    if len(outfielders) != 3:
        raise ValueError("Expected 3 starting OF")

    infielders = {pos: Hitter(data[pos.value], pos) for pos in infield}
    for p in infield:
        if not isinstance(infielders.get(p), Hitter):
            raise ValueError(f"Expected exactly one starting {p.value}")

    dh = infielders.pop(Position.DESIGNATED_HITTER)
    return HitterList([*infielders.values(), *outfielders, dh], role=Role.STARTER)


def parse_bench(data) -> HitterList:
    if not len(data) == 5:
        raise ValueError("Expected 5 bench hitters")
    return HitterList(
        (Hitter(name, Position(pos)) for pos, name in data), role=Role.BENCH
    )


def parse_rotation(data) -> PitcherList:
    if not len(data) == 8:
        raise ValueError("Expected 8 pitchers")
    return PitcherList(Pitcher(name) for name in data)


def parse_minors(data) -> (HitterList, PitcherList):
    if len(data) > 5:
        raise ValueError("Must have at most 5 players in minors")
    hitters, pitchers = HitterList(role=Role.MINORS), PitcherList()
    for pos, name in data:
        if pos == Position.PITCHER.value:
            pitchers.append(Pitcher(name))
        else:
            hitters.append(Hitter(name, Position(pos)))
    # if len(pitchers) > 3:
    #     raise ValueError("Must have at most 3 pitchers in minors")
    return hitters, pitchers


class Team:
    def __init__(self, manager: str, season: Season):
        self.manager = manager
        self.season = season

        with open(f"data/teams/{manager.lower()}.yaml", "r") as f:
            data = yaml.safe_load(f)
            self.starters = parse_starters(data["starters"])
            self.bench = parse_bench(data["bench"])
            self.rotation = parse_rotation(data["rotation"])
            self.minors_hitters, self.minors_pitchers = parse_minors(data["minors"])

    def __repr__(self):
        return f"{self.__class__.__name__}(manager='{self.manager}')"

    @property
    def players(self) -> List[Player]:
        return [
            *self.starters,
            *self.bench,
            *self.minors_hitters,
            *self.rotation,
            *self.minors_pitchers
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
        rating += (avg * 1000 - 250) * (self.season.avg_games_played / 162)
        return rating

    @property
    def innings_bonus_or_penalty(self) -> float:
        stats = self.rotation.get_summary_stats()
        innings_delta = stats.ip - (1000 * (self.season.avg_games_played / 162))
        if innings_delta >= 0:
            return innings_delta / 5
        else:
            return innings_delta / 3

    @property
    def pitching(self) -> float:
        stats = self.rotation.get_summary_stats()
        rating = stats.wins + stats.saves / 3 + (stats.strikeouts - stats.walks) / 10
        era = 9 * stats.er / stats.ip if stats.ip else 0.0
        rating -= era * self.season.avg_games_played
        return rating


if __name__ == "__main__":
    league = League(103)
    season = Season(year=2021, league=league)
    team = Team("Andrew", season)
