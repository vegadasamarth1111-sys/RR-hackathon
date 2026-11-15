"""Data preparation for SupeRR Selector Season 2.

Turns the raw ball-by-ball file into a delivery-level state table:
score before the ball, wickets in hand, balls remaining, target, required rate,
phase, competition tier and a transparent rule-based pressure flag.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd


# The refreshed data pack ships the ball-by-ball file under its original
# upload name. Prefer it when present, and fall back to the legacy filename
# so the pipeline still runs on the first data drop.
BALL_BY_BALL_CANDIDATES = ("6af855c0e8386_ball_by_ball.csv", "ball_by_ball.csv")


def load_raw(base: str):
    comp = pd.read_csv(os.path.join(base, "competitions.csv"))
    matches = pd.read_csv(os.path.join(base, "matches.csv"))
    bb_file = next(
        (f for f in BALL_BY_BALL_CANDIDATES if os.path.exists(os.path.join(base, f))),
        BALL_BY_BALL_CANDIDATES[-1],
    )
    bb = pd.read_csv(os.path.join(base, bb_file))
    teams = pd.read_csv(os.path.join(base, "teams.csv"))
    players = pd.read_csv(os.path.join(base, "competition_team_player_mapping.csv"))
    xi = pd.read_csv(os.path.join(base, "playing_eleven.csv"))
    return comp, matches, bb, teams, players, xi


def build_state(bb: pd.DataFrame, matches: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    m = matches.merge(comp[["comp_id", "comp_name", "match_format", "season"]], on="comp_id", how="left")
    m["match_date"] = pd.to_datetime(m["match_date"], errors="coerce")
    m["is_ipl"] = m["comp_name"].str.contains("IPL", case=False, na=False).astype(int)
    m["tier"] = np.select(
        [m["is_ipl"].eq(1), m["match_format"].eq("T20I")],
        [1.0, 0.9],
        default=0.75,
    )
    m["stakes"] = 1.0 + 0.35 * m["knock_out"].fillna(0).astype(int)
    m.loc[m["stage"].eq("Final"), "stakes"] += 0.15

    keep = [
        "match_id", "comp_id", "comp_name", "match_format", "season", "is_ipl", "tier", "stakes",
        "knock_out", "stage", "win_team_id", "revised_target",
        "first_inn_revised_overs", "second_inn_revised_overs", "result", "venue_id",
        "match_date",
    ]
    df = bb[bb.innings.isin([1, 2])].copy()
    df = df.merge(m[keep], on="match_id", how="left")
    df = df.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)

    # --- delivery accounting -------------------------------------------------
    # `runs` is runs off the bat. The refreshed data pack stores the actual
    # number of extra runs in extras1_runs / extras_2_runs (0 on a normal
    # ball), so use those directly. The legacy pack stored type codes in
    # extras1_runs (6 = no extra), so fall back to the conservative estimates
    # in that case: 1 for a wide / no-ball, 5 for a penalty, 1 for bye/legbye.
    df["is_legal"] = ~df.extras_type.isin(["wide", "Overstep"])
    df["is_batter_ball"] = df.extras_type.ne("wide")
    e1 = pd.to_numeric(df.get("extras1_runs"), errors="coerce").fillna(0.0)
    e2 = pd.to_numeric(df.get("extras_2_runs"), errors="coerce").fillna(0.0)
    no_extra = df.extras_type.isna()
    actual_extras = bool(len(df) and (e1[no_extra] == 0).mean() > 0.99)
    if actual_extras:
        df["extra_est"] = e1 + e2
        # Wides and no-balls (incl. the "other" no-ball code) are charged to
        # the bowler; byes, leg-byes and penalties are not.
        charged = df.extras_type.isin(["wide", "Overstep", "other"])
        df["bowler_runs"] = df.runs + np.where(charged, e1 + e2, 0.0)
    else:
        df["extra_est"] = 0.0
        df.loc[df.extras_type.eq("wide"), "extra_est"] = 1.0
        df.loc[df.extras_type.eq("Overstep"), "extra_est"] = 1.0
        df.loc[df.extras_type.eq("Penalty"), "extra_est"] = 5.0
        df.loc[df.extras_type.isin(["byes", "legbyes"]), "extra_est"] = 1.0
        df["bowler_runs"] = df.runs + np.where(
            df.extras_type.isin(["wide", "Overstep"]), 1.0, 0.0
        )
    df["total_runs"] = df.runs + df.extra_est
    df["bowler_wicket"] = df.is_wicket & df.dismissal_type.isin(
        ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
    )
    df["batter_out"] = (
        df.is_wicket
        & (df.dismissed_player_id == df.striker_id)
        & df.dismissal_type.ne("Retire Out")
    )
    df["phase"] = pd.cut(
        df.overid, bins=[0, 6, 15, 20], labels=["powerplay", "middle", "death"]
    )

    # --- pre-ball state ------------------------------------------------------
    g = df.groupby(["match_id", "innings"], sort=False)
    df["score_before"] = g.total_runs.cumsum() - df.total_runs
    df["wkts_before"] = g.is_wicket.cumsum() - df.is_wicket.astype(int)
    df["legal_before"] = g.is_legal.cumsum() - df.is_legal.astype(int)
    # The *_revised_overs columns in this data pack store balls, not overs
    # (e.g. 114 means a 19-over innings), so use them directly.
    df["max_balls"] = 120.0
    inn1_rev = df.first_inn_revised_overs.notna() & (df.innings == 1)
    inn2_rev = df.second_inn_revised_overs.notna() & (df.innings == 2)
    df.loc[inn1_rev, "max_balls"] = df.loc[inn1_rev, "first_inn_revised_overs"].round()
    df.loc[inn2_rev, "max_balls"] = df.loc[inn2_rev, "second_inn_revised_overs"].round()
    df["balls_remaining"] = (df.max_balls - df.legal_before).clip(lower=0)
    df["over_before"] = df.legal_before // 6
    df["current_rr"] = np.where(df.legal_before > 0, df.score_before / (df.legal_before / 6), 0.0)
    df["projected_score"] = df.score_before + df.current_rr * (df.balls_remaining / 6)

    # --- target / chase state ------------------------------------------------
    inn = (
        df.groupby(["match_id", "innings"])
        .agg(total=("total_runs", "sum"), bat=("runs", "sum"),
             wkts=("is_wicket", "sum"), legal=("is_legal", "sum"))
        .reset_index()
    )
    inn1 = inn[inn.innings == 1].set_index("match_id")
    df["inn1_total"] = df.match_id.map(inn1.total)
    df["target"] = np.where(df.innings == 2, df.inn1_total + 1, np.nan)
    df.loc[df.revised_target.notna(), "target"] = df.loc[df.revised_target.notna(), "revised_target"]
    df["runs_needed"] = df.target - df.score_before
    df["rrr"] = np.where(
        df.balls_remaining > 0, df.runs_needed / (df.balls_remaining / 6), np.nan
    )

    # --- par score -----------------------------------------------------------
    par = (
        inn1.reset_index()
        .merge(m[["match_id", "comp_id", "season"]], on="match_id", how="left")
        .groupby(["comp_id", "season"])
        .total.median()
        .rename("par_score")
    )
    df = df.merge(par, left_on=["comp_id", "season"], right_index=True, how="left")
    df["par_score"] = df.par_score.fillna(inn1.total.median())
    # In a chase, compare the runs still needed with what a par 9-an-over chase
    # would require from the same point; negative = ahead of the game.
    df["score_vs_par"] = np.where(
        df.innings == 1,
        df.projected_score - df.par_score,
        df.runs_needed - 9.0 * (df.balls_remaining / 6),
    )

    # --- transparent pressure rules -----------------------------------------
    # 1) Chase pressure: required rate above 9 with wickets in hand.
    chase_pressure = (
        (df.innings == 2) & (df.over_before >= 4) & (df.rrr >= 10.0) & (df.wkts_before <= 5)
    )
    # 2) Death pressure: last five overs, game within ~20 runs of par.
    death_close = (
        (df.phase == "death") & (df.wkts_before <= 7) & (df.score_vs_par.abs() <= 15)
    )
    # 3) Collapse pressure: top/middle order gone and the team is behind the game,
    #    or the tail is exposed in the last six overs.
    collapse = (
        ((df.wkts_before >= 4) & (df.balls_remaining >= 24) & (df.score_vs_par < -20))
        | ((df.wkts_before >= 6) & (df.balls_remaining <= 30))
    )
    # 4) Knockout pressure: a knockout game in the closing overs, still close.
    knockout_close = (
        (df.knock_out == 1)
        & (df.phase != "powerplay")
        & (df.balls_remaining <= 42)
        & (df.score_vs_par.abs() <= 25)
    )
    # 5) Early collapse: two early wickets in a must-score situation.
    early_collapse = (
        (df.over_before <= 6) & (df.wkts_before >= 3) & (df.score_vs_par < -20)
    )
    df["chase_pressure"] = chase_pressure
    df["death_close"] = death_close
    df["collapse"] = collapse
    df["knockout_close"] = knockout_close
    df["early_collapse"] = early_collapse
    df["pressure_rule"] = df[
        ["chase_pressure", "death_close", "collapse", "knockout_close", "early_collapse"]
    ].any(axis=1)

    return df
