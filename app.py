from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import logging

from flask import Flask, render_template, abort
from flask_bootstrap import Bootstrap

from models.season import League, Season
from models.team import Team

app = Flask(__name__)
bootstrap = Bootstrap(app)

league = League(103)
season = Season(year=2021, league=league)
managers = [
    "Andrew",
    "Evans",
    "Jeff",
    "John",
    "Myron",
    "Paula",
    "Rich",
    "Scott",
]
teams = {manager.lower(): Team(manager, season) for manager in managers}


@app.route('/')
def home():
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(lambda t: t.fetch_all_stats(), t) for t in teams.values()
        ]
        wait(futures, return_when=ALL_COMPLETED)
        standings = sorted(teams.values(), key=lambda t: t.rating, reverse=True)
        return render_template("home.html", season=season, teams=standings)


@app.route("/teams/<manager>")
def team(manager: str):
    team = teams.get(manager.lower())
    if team is None:
        abort(404)
    team.fetch_all_stats()
    return render_template("team.html", team=team)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(levelname)-7s %(message)s',
        level=logging.INFO
    )
    app.run()
