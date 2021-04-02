from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union

import yaml

from models.player import Player, Hitter, Pitcher
from models.position import Position
from models.role import Role
from models.season import Season, League


def parse_starters(data) -> Dict[Position, Union[Hitter, List[Hitter]]]:
    starters = {Position.OUTFIELD: []}
    for pos, value in data.items():
        position = Position(pos)
        if position == Position.OUTFIELD:
            starters[position] = [Hitter(name, position) for name in value]
        else:
            starters[position] = Hitter(value, position)
    return starters


def parse_bench(data) -> List[Hitter]:
    return [Hitter(name, Position(pos)) for pos, name in data]


def parse_rotation(data) -> List[Pitcher]:
    return [Pitcher(name) for name in data]


def parse_minors(data) -> List[Player]:
    return [Hitter(name, Position(pos)) if pos != "P" else Pitcher(name)
            for pos, name in data]


class Team:
    def __init__(self, manager: str, season: Season):
        self.manager = manager
        self.season = season

        with open(f"data/teams/{manager.lower()}.yaml", "r") as f:
            data = yaml.safe_load(f)
            starters = parse_starters(data["starters"])
            bench = parse_bench(data["bench"])
            rotation = parse_rotation(data["rotation"])
            minors = parse_minors(data["minors"])

        if not len(starters) == 7:
            raise ValueError("Expected 7 starter positions")
        elif not len(bench) == 5:
            raise ValueError("Expected 5 bench hitters")
        elif not len(rotation) == 8:
            raise ValueError("Expected 8 pitchers")
        elif len(minors) > 5:
            raise ValueError("Must have at most 5 players in minors")
        for p in [
            Position.FIRST_BASE,
            Position.SECOND_BASE,
            Position.SHORTSTOP,
            Position.THIRD_BASE,
            Position.CATCHER,
            Position.DESIGNATED_HITTER,
        ]:
            if not isinstance(starters[p], Hitter):
                raise ValueError(f"Expected exactly one starting {p.value}")
        outfielders = starters[Position.OUTFIELD]
        if not isinstance(outfielders, list) or len(outfielders) != 3:
            raise ValueError("Must have a list of 3 starting OF")
        elif len([p for p in minors if isinstance(p, Pitcher)]) > 3:
            raise ValueError("Must have at most 3 pitchers in minors")

        self.starters = [p for k, p in starters.items() if k != Position.OUTFIELD] + \
            starters[Position.OUTFIELD]
        self.bench = bench
        self.rotation = rotation
        self.minors = minors

    def __repr__(self):
        return f"{self.__class__.__name__}(manager='{self.manager}')"

    @property
    def players(self) -> List[Player]:
        return [
            *self.starters,
            *self.bench,
            *self.rotation,
            *self.minors
        ]

    @property
    def minors_hitters(self):
        return [p for p in self.minors if isinstance(p, Hitter)]

    @property
    def minors_pitchers(self):
        return [p for p in self.minors if isinstance(p, Pitcher)]

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
        rating += (hits/ab * 1000 - 250) * (self.season.avg_games_played / 162)
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
        era = 9 * er / ip
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
