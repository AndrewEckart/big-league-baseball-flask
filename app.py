import logging

from flask import Flask, render_template, abort, redirect

from seasons import CURRENT_SEASON, ALL_SEASONS

app = Flask(__name__)


@app.context_processor
def inject_season_list():
    return dict(seasons=sorted(ALL_SEASONS.keys(), reverse=True))


@app.route("/")
def home():
    return redirect(f"/{CURRENT_SEASON.year}")


@app.route("/<int:year>")
def standings(year: int):
    season = ALL_SEASONS.get(year)
    if season is None:
        abort(404)
    return render_template("home.html", season=season)


@app.route("/<int:year>/<manager>")
def team_stats(year: int, manager: str):
    season = ALL_SEASONS.get(year)
    if season is None:
        abort(404)
    team = season.teams.get(manager.lower())
    if team is None:
        abort(404)
    team.fetch_all_stats()
    return render_template("team.html", team=team)


@app.template_filter('pluralize')
def pluralize(number: int, singular='', plural='s') -> str:
    # Ref: https://stackoverflow.com/a/22336061/8534196
    return singular if number == 1 else plural


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-7s %(message)s", level=logging.INFO)
    app.run()
