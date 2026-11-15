"""Win-probability, leverage and context-adjusted impact models."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEAT1 = ["score_before", "wkts_before", "balls_remaining", "current_rr",
         "projected_score", "par_score", "knock_out", "is_ipl"]
FEAT2 = ["runs_needed", "wkts_before", "balls_remaining", "rrr", "current_rr",
         "target", "par_score", "knock_out", "is_ipl"]
OUTCOMES = [0, 1, 2, 3, 4, 5, 6, "W"]


def _clean(X: pd.DataFrame) -> pd.DataFrame:
    return X.replace([np.inf, -np.inf], np.nan).fillna(0)


def add_win_probability(df: pd.DataFrame):
    """Fit innings-specific logistic win-probability models and add p_win."""
    live = df[
        df.win_team_id.notna()
        & (df.balls_remaining > 0)
        & (df.wkts_before < 10)
    ].copy()
    live["bat_won"] = (live.win_team_id == live.batting_team_id).astype(int)

    train = {
        1: live[live.innings == 1],
        2: live[(live.innings == 2) & (live.runs_needed > 0)],
    }
    feats = {1: FEAT1, 2: FEAT2}
    models = {}
    for inn in (1, 2):
        X = _clean(train[inn][feats[inn]])
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        clf.fit(X, train[inn].bat_won)
        models[inn] = clf

    df["p_win"] = np.nan
    for inn in (1, 2):
        mask = (df.innings == inn) & (df.balls_remaining > 0) & (df.wkts_before < 10)
        if mask.any():
            df.loc[mask, "p_win"] = models[inn].predict_proba(
                _clean(df.loc[mask, feats[inn]])
            )[:, 1]

    # deterministic states
    m2 = df.innings == 2
    df.loc[m2, "p_win"] = np.where(
        df.loc[m2, "runs_needed"] <= 0, 1.0, df.loc[m2, "p_win"]
    )
    df.loc[df.wkts_before >= 10, "p_win"] = 0.0
    dead1 = (df.balls_remaining <= 0) & (df.innings == 1)
    df.loc[dead1, "p_win"] = df.loc[dead1, "p_win"].fillna(0.5)
    dead2 = (df.balls_remaining <= 0) & (df.innings == 2)
    df.loc[dead2, "p_win"] = np.where(
        df.loc[dead2, "runs_needed"] <= 0, 1.0, 0.0
    )
    return df, models, feats


def add_leverage(df: pd.DataFrame, models: dict, feats: dict) -> pd.DataFrame:
    """Add win-probability leverage (expected WP swing of the next ball)."""
    # empirical outcome distribution by innings / phase
    legal = df[df.is_legal].copy()
    legal["outcome"] = np.where(
        legal.is_wicket, "W", legal.runs.clip(0, 6).astype(int)
    )
    op = (
        legal.groupby(["innings", "phase"], observed=True)
        .outcome.value_counts(normalize=True)
        .rename("prob")
        .reset_index()
    )

    cols = ["match_id", "innings", "innings_ball_num", "phase", "score_before",
            "wkts_before", "balls_remaining", "current_rr", "projected_score",
            "runs_needed", "rrr", "target", "par_score", "knock_out", "is_ipl",
            "max_balls", "p_win"]
    base = df[cols].copy()
    parts = []
    for o in OUTCOMES:
        s = base.copy()
        s["outcome"] = o
        runs = 0 if o == "W" else o
        wicket = 1 if o == "W" else 0
        s["score_before"] = s.score_before + runs
        s["wkts_before"] = s.wkts_before + wicket
        s["balls_remaining"] = (s.balls_remaining - 1).clip(lower=0)
        s["current_rr"] = s.score_before / (
            (s.max_balls - s.balls_remaining) / 6
        ).clip(lower=0.1)
        s["projected_score"] = s.score_before + s.current_rr * (s.balls_remaining / 6)
        s["runs_needed"] = s.runs_needed - runs
        s["rrr"] = np.where(
            s.balls_remaining > 0, s.runs_needed / (s.balls_remaining / 6), 99.0
        )
        parts.append(s)
    sim = pd.concat(parts, ignore_index=True)

    sim["p_after"] = np.nan
    for inn in (1, 2):
        mask = (sim.innings == inn) & (sim.balls_remaining > 0) & (sim.wkts_before < 10)
        if mask.any():
            sim.loc[mask, "p_after"] = models[inn].predict_proba(
                _clean(sim.loc[mask, feats[inn]])
            )[:, 1]
    m2 = sim.innings == 2
    sim.loc[m2 & (sim.runs_needed <= 0), "p_after"] = 1.0
    sim.loc[m2 & (sim.wkts_before >= 10) & (sim.runs_needed > 0), "p_after"] = 0.0
    sim.loc[m2 & (sim.balls_remaining <= 0) & (sim.runs_needed > 0), "p_after"] = 0.0
    m1 = sim.innings == 1
    sim.loc[m1 & (sim.wkts_before >= 10), "p_after"] = 0.0
    sim["p_after"] = sim.p_after.fillna(sim.p_win)

    sim = sim.merge(op, on=["innings", "phase", "outcome"], how="left")
    sim["prob"] = sim.prob.fillna(0)
    sim["sq"] = sim.prob * (sim.p_after - sim.p_win) ** 2
    lev = (
        sim.groupby(["match_id", "innings", "innings_ball_num"]).sq.sum()
        .pow(0.5)
        .rename("leverage")
        .reset_index()
    )
    df = df.merge(lev, on=["match_id", "innings", "innings_ball_num"], how="left")
    df["leverage"] = df.leverage.fillna(0.0)
    df.loc[df.balls_remaining <= 0, "leverage"] = 0.0
    df["closeness"] = 4 * df.p_win * (1 - df.p_win)
    df["lev_pct"] = df.groupby("innings").leverage.rank(pct=True)
    df["pressure_weight"] = np.where(
        df.pressure_rule, 1.0 + df.lev_pct, 1.0
    ) * df.tier
    return df


def add_context_impact(df: pd.DataFrame) -> pd.DataFrame:
    """Context-adjusted runs above par for batters and bowlers."""
    df["pace_or_spin"] = df.pace_or_spin.fillna("Unknown")
    df["batting_type"] = df.batting_type.fillna("Unknown")

    exp_bat = (
        df.groupby(["phase", "pace_or_spin", "is_ipl"], observed=True)
        .runs.mean().rename("exp_bat_runs")
    )
    exp_bat_out = (
        df.groupby(["phase", "is_ipl"], observed=True)
        .batter_out.mean().rename("exp_bat_out")
    )
    exp_bowl = (
        df.groupby(["phase", "batting_type", "is_ipl"], observed=True)
        .bowler_runs.mean().rename("exp_bowl_runs")
    )
    exp_bowl_wkt = (
        df.groupby(["phase", "is_ipl"], observed=True)
        .bowler_wicket.mean().rename("exp_bowl_wkt")
    )
    df = df.merge(exp_bat, left_on=["phase", "pace_or_spin", "is_ipl"], right_index=True, how="left")
    df = df.merge(exp_bat_out, left_on=["phase", "is_ipl"], right_index=True, how="left")
    df = df.merge(exp_bowl, left_on=["phase", "batting_type", "is_ipl"], right_index=True, how="left")
    df = df.merge(exp_bowl_wkt, left_on=["phase", "is_ipl"], right_index=True, how="left")

    # A wicket is worth ~1.5 runs to a batter and ~2.0 runs to a bowler.
    df["bat_impact"] = (
        df.runs
        - df.exp_bat_runs
        - 1.5 * (df.batter_out.astype(int) - df.exp_bat_out)
    )
    df["bowl_impact"] = (
        df.exp_bowl_runs
        - df.bowler_runs
        + 2.0 * (df.bowler_wicket.astype(int) - df.exp_bowl_wkt)
    )
    return df


def validate_win_probability(df: pd.DataFrame) -> dict:
    """Out-of-fold AUC/Brier and a calibration table for the WP models."""
    live = df[
        df.win_team_id.notna()
        & (df.balls_remaining > 0)
        & (df.wkts_before < 10)
    ].copy()
    live["bat_won"] = (live.win_team_id == live.batting_team_id).astype(int)
    out = {}
    for inn, feats in [(1, FEAT1), (2, FEAT2)]:
        d = live[(live.innings == inn) & ((live.innings == 1) | (live.runs_needed > 0))]
        X = _clean(d[feats])
        y = d.bat_won.values
        groups = d.match_id.values
        oof = np.zeros(len(d))
        for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
            clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
            clf.fit(X.iloc[tr], y[tr])
            oof[te] = clf.predict_proba(X.iloc[te])[:, 1]
        cal = pd.DataFrame({"p": oof, "y": y})
        cal["bin"] = pd.cut(cal.p, bins=np.linspace(0, 1, 11), include_lowest=True)
        table = cal.groupby("bin", observed=True).agg(pred=("p", "mean"), actual=("y", "mean"), n=("y", "size")).reset_index()
        out[inn] = dict(
            auc=float(roc_auc_score(y, oof)),
            brier=float(brier_score_loss(y, oof)),
            n=int(len(d)),
            calibration=table,
        )
    return out
