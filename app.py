from flask import Flask, render_template
from flask_bootstrap import Bootstrap

from models.season import League, Season
from models.team import Team

app = Flask(__name__)
bootstrap = Bootstrap(app)

league = League(103)
season = Season(year=2021, league=league)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/teams/<manager>")
def team(manager: str):
    team = Team(manager, season)
    team.fetch_all_stats()
    return render_template("team.html", team=team)


if __name__ == '__main__':
    app.run()
