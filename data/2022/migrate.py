import pandas as pd


if __name__ == "__main__":
    id_map = pd.read_csv(
        "sfbb-player-id-map.csv", index_col="IDFANGRAPHS", dtype={"MLBID": "Int32"}
    )
    # print(id_map)

    for (infile, outfile) in [
        ("drafted_hitters.csv", "hitters.csv"),
        ("drafted_pitchers.csv", "pitchers.csv"),
    ]:
        drafted_players = pd.read_csv(
            infile, index_col="FanGraphs ID", dtype={"Rd": "Int8"}
        )
        drafted_players.index = drafted_players.index.astype(str)

        players = drafted_players.join(id_map)[["MLBID", "Name", "Team", "Mgr", "Rd"]]
        players.drop_duplicates(subset="MLBID", inplace=True)
        print(players)
        assert len(players) == len(drafted_players)
        players["Acquired"] = "Draft"
        players.to_csv(outfile, index=False)
