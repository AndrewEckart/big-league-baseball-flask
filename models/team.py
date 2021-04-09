from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union

import yaml

from models.player import Player, Hitter, Pitcher, HitterList, PitcherList
from models.position import Position
from models.role import Role
from models.season import Season, League


def parse_starters(data) -> HitterList:
    if not len(data) == 7:
        raise ValueError("Expected 7 starter positions")

    outfielders = HitterList(
        Hitter(name, Position.OUTFIELD) for name in data[Position.OUTFIELD.value]
    )
    if len(outfielders) != 3:
        raise ValueError("Expected 3 starting OF")

    infield = set(Position.__members__.values())\
        .difference({Position.OUTFIELD, Position.PITCHER})
    infielders: Dict[Position, Hitter] = {
        pos: Hitter(data[pos.value], pos) for pos in infield
    }
    for p in infield:
        if not isinstance(infielders.get(p), Hitter):
            raise ValueError(f"Expected exactly one starting {p.value}")

    return HitterList([*infielders.values(), *outfielders])


def parse_bench(data) -> HitterList:
    if not len(data) == 5:
        raise ValueError("Expected 5 bench hitters")
    return HitterList(Hitter(name, Position(pos)) for pos, name in data)


def parse_rotation(data) -> List[Pitcher]:
    if not len(data) == 8:
        raise ValueError("Expected 8 pitchers")
    return PitcherList(Pitcher(name) for name in data)


def parse_minors(data) -> (HitterList, PitcherList):
    if len(data) > 5:
        raise ValueError("Must have at most 5 players in minors")
    hitters, pitchers = HitterList(), PitcherList()
    for pos, name in data:
        if pos == Position.PITCHER.value:
            pitchers.append(Pitcher(name))
        else:
            hitters.append(Hitter(name, Position(pos)))
    if len(pitchers) > 3:
        raise ValueError("Must have at most 3 pitchers in minors")
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
    def rating(self):
        return self.offense - self.pitching

    @property
    def offense(self) -> float:
        rating = ab = hits = 0.0
        for hitter, role in [
            *[(p, Role.STARTER) for p in self.starters],
            *[(p, Role.BENCH) for p in self.bench]
        ]:
            factor = role.value / 100
            rating += factor * hitter.runs / 2
            rating += factor * hitter.rbi / 2
            rating += factor * hitter.home_runs / 4
            rating += factor * hitter.stolen_bases / 5
            hits += factor * hitter.hits
            ab += factor * hitter.at_bats
        avg = hits/ab if ab else 0.0
        rating += (avg * 1000 - 250) * (self.season.avg_games_played / 162)
        return rating

    @property
    def pitching(self) -> float:
        rating = ip = 0.0
        er = strikeouts = walks = 0
        for pitcher in self.rotation:
            rating -= pitcher.wins
            rating -= pitcher.saves / 3
            ip += pitcher.innings_pitched
            er += pitcher.earned_runs
            strikeouts += pitcher.strikeouts
            walks += pitcher.walks
        era = 9 * er / ip if ip else 0.0
        rating += era * self.season.avg_games_played
        innings_delta = ip - 1000
        if innings_delta < 0:
            rating -= innings_delta / 3 * (self.season.avg_games_played / 162)
        else:
            rating -= innings_delta / 5
        rating -= (strikeouts - walks) / 10
        return rating


if __name__ == "__main__":
    league = League(103)
    season = Season(year=2021, league=league)
    team = Team("Andrew", season)
