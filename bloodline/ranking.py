"""Leaderboard built from stored game records."""

from __future__ import annotations

import pandas as pd

COLUMNS = ["nick", "games", "wins", "perfect", "win_rate", "avg_risk"]


def build_ranking(records: list[dict]) -> pd.DataFrame:
    """One row per player.

    * ``wins``: perfect wins + wins as carrier (luck + skill).
    * ``win_rate``: wins / games.
    * ``avg_risk``: mean exact risk of the pedigrees the player built.
      It ignores the dice roll, so it measures pure decision quality.

    Only the first play of each game code counts per player, so replaying a
    known seed cannot farm the ranking.
    """
    if not records:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(records)
    df["nick"] = df["nick"].astype(str).str.strip()
    df = df[df["nick"] != ""]
    df["key"] = df["nick"].str.casefold()
    df["seed"] = df["seed"].astype(str)
    df["risk"] = pd.to_numeric(df["risk"], errors="coerce")
    df = df.sort_values("timestamp").drop_duplicates(["key", "seed"], keep="first")
    df["is_win"] = df["outcome"].isin(["perfect", "win"])
    df["is_perfect"] = df["outcome"] == "perfect"
    table = df.groupby("key").agg(
        nick=("nick", "last"),
        games=("outcome", "size"),
        wins=("is_win", "sum"),
        perfect=("is_perfect", "sum"),
        avg_risk=("risk", "mean"),
    )
    table["win_rate"] = table["wins"] / table["games"]
    return table.reset_index(drop=True)[COLUMNS]


def by_wins(table: pd.DataFrame) -> pd.DataFrame:
    return table.sort_values(["wins", "perfect", "avg_risk"], ascending=[False, False, True])


def by_win_rate(table: pd.DataFrame, min_games: int) -> pd.DataFrame:
    t = table[table["games"] >= min_games]
    return t.sort_values(["win_rate", "games"], ascending=[False, False])


def by_avg_risk(table: pd.DataFrame, min_games: int) -> pd.DataFrame:
    t = table[table["games"] >= min_games]
    return t.sort_values(["avg_risk", "games"], ascending=[True, False])
