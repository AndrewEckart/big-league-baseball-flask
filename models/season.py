from dataclasses import dataclass

import statsapi


@dataclass
class League:
    league_id: int


@dataclass
class Season:
    year: int
    league: League

    @property
    def avg_games_played(self) -> int:
        standings_data = statsapi.standings_data(
            self.league.league_id, season=self.year
        )
        total_games = 0
        teams = 0
        for _, division in standings_data.items():
            for team in division.get("teams", []):
                teams += 1
                total_games += team.get("w", 0)
                total_games += team.get("l", 0)
        return round(total_games / teams)
