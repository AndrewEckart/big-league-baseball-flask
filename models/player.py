import pandas as pd


from models.position import Position


class Player:
    name: str
    position: Position
    mlb_id: int

    def __repr__(self):
        attrs = ["name", "position", "mlb_id"]
        values = ", ".join([f"{attr}={getattr(self, attr)}" for attr in attrs])
        return f"{self.__class__.__name__}({values})"


class Hitter(Player):
    id_map = pd.read_csv("data/hitters.csv", index_col="Name")

    def __init__(self, name: str, position: Position):
        if position == Position.PITCHER:
            raise ValueError("Pitchers cannot be position players!")

        self.name = name
        self.position = position
        self.mlb_id = self.id_map.loc[name, "MLBID"]


class Pitcher(Player):
    id_map = pd.read_csv("data/pitchers.csv", index_col="Name")

    def __init__(self, name: str):
        self.name = name
        self.position = Position.PITCHER
        self.mlb_id = self.id_map.loc[name, "MLBID"]
