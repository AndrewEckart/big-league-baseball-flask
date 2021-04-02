from typing import Dict, List, Union

from models.player import Player, Hitter, Pitcher
from models.position import Position
from models.role import Role


class Roster:
    def __init__(
        self, 
        starters: Dict[Position, Union[Hitter, List[Hitter]]],
        bench: List[Hitter],
        rotation: List[Pitcher],
        minors: List[Player]
    ):
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

        self.starters = starters
        self.bench = bench
        self.rotation = rotation
        self.minors = minors
