from __future__ import annotations

from models import Rules, Season


seasons: list[Season] = [
    Season(
        year=2025,
        # fmt: off
        managers=["Andrew", "Justin", "Ron", "Myron"],
        # fmt: on
        rules=Rules(
            num_reserve_hitters=4,
            num_pitchers=7,
            team_innings_threshold=900,
            innings_deficit_multiplier=1/3,
            innings_surplus_multiplier=0,
            injured_pitcher_innings_multiplier=0.7,
            injured_pitcher_era_multiplier=1.15,
        )
    ),
    Season(
        year=2024,
        # fmt: off
        managers=["Andrew", "Justin", "Rich", "Jeff", "Scott", "Evans", "Myron", "John", "Paula", "Ron"],
        # fmt: on
        rules=Rules(
            num_reserve_hitters=4,
            num_pitchers=7,
            team_innings_threshold=900,
            innings_deficit_multiplier=1/3,
            innings_surplus_multiplier=0,
            injured_pitcher_innings_multiplier=0.7,
            injured_pitcher_era_multiplier=1.15,
        )
    ),
    Season(
        year=2023,
        # fmt: off
        managers=["Andrew", "Evans", "Jeff", "John", "Justin", "Myron", "Paula", "Rich", "Ron", "Scott"],
        # fmt: on
        rules=Rules(
            num_reserve_hitters=4,
            num_pitchers=7,
            team_innings_threshold=900,
            innings_deficit_multiplier=1 / 3,
            innings_surplus_multiplier=0,
            injured_pitcher_innings_multiplier=0.7,
            injured_pitcher_era_multiplier=1.15,
        ),
    ),
    Season(
        year=2022,
        # fmt: off
        managers=["Andrew", "Evans", "Jeff", "John", "Myron", "Paula", "Rich", "Scott", "Ron", "Justin"],
        # fmt: on
        rules=Rules(
            num_reserve_hitters=4,
            num_pitchers=7,
            team_innings_threshold=900,
            innings_deficit_multiplier=1 / 3,
            innings_surplus_multiplier=1 / 5,
            injured_pitcher_innings_multiplier=0.7,
            injured_pitcher_era_multiplier=1.15,
        ),
    ),
    Season(
        year=2021,
        managers=["Andrew", "Evans", "Jeff", "John", "Myron", "Paula", "Rich", "Scott"],
        rules=Rules(
            num_reserve_hitters=5,
            num_pitchers=8,
            team_innings_threshold=1000,
            innings_deficit_multiplier=1 / 3,
            innings_surplus_multiplier=1 / 5,
            injured_pitcher_innings_multiplier=0.8,
            injured_pitcher_era_multiplier=1.3,
        ),
    ),
]

ALL_SEASONS: dict[int, Season] = {season.year: season for season in seasons}
CURRENT_SEASON = max(seasons, key=lambda season: season.year)
