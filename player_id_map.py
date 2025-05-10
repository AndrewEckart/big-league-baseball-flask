import pandas as pd

path = "data/2025/2025_SFBB_Player_ID_Map.csv"
PLAYER_ID_MAP = pd.read_csv(path)

MLBID_TO_NAME: dict[int, str] = {
    row.MLBID: row.MLBNAME for row in PLAYER_ID_MAP.itertuples()
}

# Fix-up some players missing from the SFBB list.
MLBID_TO_NAME.update({
    681343: "Shane Smith",
})
