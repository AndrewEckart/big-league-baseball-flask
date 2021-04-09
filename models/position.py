from enum import Enum


class Position(Enum):
    FIRST_BASE = "1B"
    SECOND_BASE = "2B"
    SHORTSTOP = "SS"
    THIRD_BASE = "3B"
    CATCHER = "C"
    DESIGNATED_HITTER = "DH"
    OUTFIELD = "OF"
    PITCHER = "P"

    def __str__(self):
        return self.value


infield = [
    Position.FIRST_BASE,
    Position.SECOND_BASE,
    Position.SHORTSTOP,
    Position.THIRD_BASE,
    Position.CATCHER,
    Position.DESIGNATED_HITTER
]
