from typing import Dict, List, Union

import yaml

from models.roster import Roster
from models.player import Player, Hitter, Pitcher
from models.position import Position


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
    def __init__(self, manager: str):
        self.manager = manager

        bench: List[Hitter] = []
        rotation: List[Pitcher] = []
        minors: List[Player] = []

        with open(f"data/teams/{manager.lower()}.yaml", "r") as f:
            data = yaml.safe_load(f)
            # print(data)
            starters = parse_starters(data["starters"])
            bench = parse_bench(data["bench"])
            rotation = parse_rotation(data["rotation"])
            minors = parse_minors(data["minors"])
            self.roster = Roster(starters, bench, rotation, minors)
            print(self.roster.starters)


if __name__ == "__main__":
    team = Team("Andrew")
