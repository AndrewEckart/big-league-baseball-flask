from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Union

import yaml

from models.player import Player, Hitter, Pitcher
from models.position import Position
from models.season import Season


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
        self.season = Season

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
        return self.offense_rating + self.pitching_rating

    @property
    def offense_rating(self) -> float:
        rating = 0.0
        for hitter in self.starters:
            rating += hitter.runs / 2
            rating += hitter.rbi / 2
            rating += hitter.home_runs / 4
            rating += hitter.stolen_bases / 5

    
    @property
    def pitching_rating(self) -> float:
        pass


if __name__ == "__main__":
    team = Team("Andrew")
