from flask import Flask
import statsapi

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    # app.run()
    # players = statsapi.get("sports_players", {"season": 2021})["people"]
    # print(players[0])
    gary_sanchez = statsapi.player_stat_data(596142)
    print(gary_sanchez)
