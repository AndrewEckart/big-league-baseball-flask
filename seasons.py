from __future__ import annotations

from models import Season


seasons: list[Season] = [
    Season(
        2022,
        [
            "Andrew",
            "Evans",
            "Jeff",
            "John",
            "Myron",
            "Paula",
            "Rich",
            "Scott",
            "Ron",
            "Justin",
        ],
    ),  # noqa
    Season(
        2021, ["Andrew", "Evans", "Jeff", "John", "Myron", "Paula", "Rich", "Scott"]
    ),
]

ALL_SEASONS: dict[int, Season] = {season.year: season for season in seasons}
CURRENT_SEASON = max(seasons, key=lambda season: season.year)
