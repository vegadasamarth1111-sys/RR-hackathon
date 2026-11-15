"""Player aggregation, reliability scoring and validation."""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DEFAULT_WEIGHTS = {"output": 0.35, "uplift": 0.20, "control": 0.20, "consistency": 0.15, "sample": 0.10}
DEFAULT_WEIGHTS_BOWL = {"output": 0.40, "uplift": 0.15, "control": 0.20, "consistency": 0.15, "sample": 0.10}
SHRINK_K = 80.0
MIN_BAT = dict(balls_total=500, balls_pressure=80, pressure_innings6=12, innings_total=15)
MIN_BOWL = dict(balls_total=500, balls_pressure=100, pressure_innings6=10, innings_total=12)


def _wmean(x, w):
    s = np.sum(w)
    return np.sum(x * w) / s if s > 0 else np.nan


def aggregate_batters(df: pd.DataFrame) -> pd.DataFrame:
    b = df[df.is_batter_ball].copy()
    rows = []
    for pid, g in b.groupby("striker_id"):
        p = g[g.pressure_rule]
        q = g[~g.pressure_rule]
        bp = int(p.is_batter_ball.sum())
        bn = int(q.is_batter_ball.sum())
        if bp == 0:
            continue
        imp_p = 100 * _wmean(p.bat_impact, p.pressure_weight)
        imp_n = 100 * _wmean(q.bat_impact, q.pressure_weight) if bn > 0 else np.nan
        pi = (
            p.groupby(["match_id", "innings"])
            .agg(balls=("is_batter_ball", "sum"), imp=("bat_impact", "sum"),
                 runs=("runs", "sum"), outs=("batter_out", "sum"))
            .reset_index()
        )
        pi6 = pi[pi.balls >= 6]
        pos_rate = (pi6.imp > 0).mean() if len(pi6) else np.nan
        rows.append(dict(
            player_id=pid, player=g.striker_name.iloc[0], role="Batter",
            balls_total=int(g.is_batter_ball.sum()), balls_pressure=bp, balls_nonpressure=bn,
            innings_total=int(g.groupby(["match_id", "innings"]).ngroups),
            pressure_innings=int(p.groupby(["match_id", "innings"]).ngroups),
            pressure_innings6=len(pi6),
            runs_total=int(g.runs.sum()), runs_pressure=int(p.runs.sum()),
            sr_total=100 * g.runs.sum() / g.is_batter_ball.sum(),
            sr_pressure=100 * p.runs.sum() / bp,
            boundary_pct=100 * (p.is_four | p.is_six).sum() / bp,
            dot_pct=100 * (p.runs == 0).sum() / bp,
            out_rate=100 * p.batter_out.sum() / bp,
            avg_pressure=(p.runs.sum() / p.batter_out.sum()) if p.batter_out.sum() else np.nan,
            impact_pressure=imp_p, impact_nonpressure=imp_n, uplift=imp_p - imp_n,
            impact_overall=100 * _wmean(g.bat_impact, g.tier),
            pos_rate=pos_rate,
            ipl_balls=int(g[g.is_ipl == 1].is_batter_ball.sum()),
            t20i_balls=int(g[g.is_ipl == 0].is_batter_ball.sum()),
            other_balls=int(g[(g.is_ipl == 0) & (g.match_format != "T20I")].is_batter_ball.sum()),
            seasons=g.season.nunique(),
        ))
    return pd.DataFrame(rows)


def aggregate_bowlers(df: pd.DataFrame) -> pd.DataFrame:
    bo = df[df.is_legal].copy()
    rows = []
    for pid, g in bo.groupby("bowler_id"):
        p = g[g.pressure_rule]
        q = g[~g.pressure_rule]
        bp = int(p.is_legal.sum())
        bn = int(q.is_legal.sum())
        if bp == 0:
            continue
        imp_p = 100 * _wmean(p.bowl_impact, p.pressure_weight)
        imp_n = 100 * _wmean(q.bowl_impact, q.pressure_weight) if bn > 0 else np.nan
        pi = (
            p.groupby(["match_id", "innings"])
            .agg(balls=("is_legal", "sum"), imp=("bowl_impact", "sum"),
                 runs=("bowler_runs", "sum"), wkts=("bowler_wicket", "sum"))
            .reset_index()
        )
        pi6 = pi[pi.balls >= 6]
        pos_rate = (pi6.imp > 0).mean() if len(pi6) else np.nan
        rows.append(dict(
            player_id=pid, player=g.bowler_name.iloc[0], role="Bowler",
            balls_total=int(g.is_legal.sum()), balls_pressure=bp, balls_nonpressure=bn,
            innings_total=int(g.groupby(["match_id", "innings"]).ngroups),
            pressure_innings=int(p.groupby(["match_id", "innings"]).ngroups),
            pressure_innings6=len(pi6),
            runs_pressure=int(p.bowler_runs.sum()), wickets_pressure=int(p.bowler_wicket.sum()),
            economy_total=6 * g.bowler_runs.sum() / g.is_legal.sum(),
            economy_pressure=6 * p.bowler_runs.sum() / bp,
            wicket_rate=100 * p.bowler_wicket.sum() / bp,
            dot_pct=100 * (p.runs == 0).sum() / bp,
            boundary_pct=100 * (p.is_four | p.is_six).sum() / bp,
            impact_pressure=imp_p, impact_nonpressure=imp_n, uplift=imp_p - imp_n,
            impact_overall=100 * _wmean(g.bowl_impact, g.tier),
            pos_rate=pos_rate,
            ipl_balls=int(g[g.is_ipl == 1].is_legal.sum()),
            t20i_balls=int(g[g.is_ipl == 0].is_legal.sum()),
            other_balls=int(g[(g.is_ipl == 0) & (g.match_format != "T20I")].is_legal.sum()),
            seasons=g.season.nunique(),
        ))
    return pd.DataFrame(rows)


def add_scores(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    d = df.copy()
    if weights is None:
        weights = DEFAULT_WEIGHTS_BOWL if (len(d) and d.role.iloc[0] == "Bowler") else DEFAULT_WEIGHTS
    w = weights
    d["sample_conf"] = d.balls_pressure / (d.balls_pressure + SHRINK_K)
    d["impact_adj"] = d.sample_conf * d.impact_pressure
    d["uplift_adj"] = d.sample_conf * d.uplift
    d["pos_rate_shrunk"] = (
        d.pressure_innings6 * d.pos_rate + 5 * 0.5
    ) / (d.pressure_innings6 + 5)
    d["output_pct"] = d.impact_adj.rank(pct=True) * 100
    d["uplift_pct"] = d.uplift_adj.rank(pct=True) * 100
    d["consistency_pct"] = d.pos_rate_shrunk.rank(pct=True) * 100
    d["sample_pct"] = d.sample_conf.rank(pct=True) * 100
    d["overall_rank"] = d.impact_overall.rank(ascending=False, method="min")
    if "role" in d and (d.role == "Bowler").all():
        dot_pct = d.dot_pct.rank(pct=True) * 100
        boundary_pct = (100 - d.boundary_pct).rank(pct=True) * 100
        d["control_pct"] = 0.5 * dot_pct + 0.5 * boundary_pct
    else:
        d["control_pct"] = (100 - d.dot_pct).rank(pct=True) * 100
    d["PRS"] = (
        w["output"] * d.output_pct
        + w["uplift"] * d.uplift_pct
        + w["control"] * d.control_pct
        + w["consistency"] * d.consistency_pct
        + w["sample"] * d.sample_pct
    )
    return d.sort_values("PRS", ascending=False).reset_index(drop=True)


def eligible(df: pd.DataFrame, role: str) -> pd.DataFrame:
    t = MIN_BAT if role == "Batter" else MIN_BOWL
    mask = (
        (df.balls_total >= t["balls_total"])
        & (df.balls_pressure >= t["balls_pressure"])
        & (df.pressure_innings6 >= t["pressure_innings6"])
        & (df.innings_total >= t["innings_total"])
    )
    return df[mask].copy()


def bootstrap_ci(df: pd.DataFrame, player_id: int, role: str, n_boot: int = 1000, seed: int = 42):
    """Bootstrap 90% CI for a player's pressure impact per 100 balls."""
    if role == "Batter":
        g = df[(df.striker_id == player_id) & df.is_batter_ball & df.pressure_rule]
        balls_col, impact_col = "is_batter_ball", "bat_impact"
    else:
        g = df[(df.bowler_id == player_id) & df.is_legal & df.pressure_rule]
        balls_col, impact_col = "is_legal", "bowl_impact"
    innings = (
        g.groupby(["match_id", "innings"])
        .agg(balls=(balls_col, "sum"), impact=(impact_col, "sum"))
        .reset_index()
    )
    innings = innings[innings.balls >= 6]
    if len(innings) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    n = len(innings)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        s = innings.iloc[idx]
        vals[i] = 100 * s.impact.sum() / s.balls.sum()
    return float(np.percentile(vals, 5)), float(np.percentile(vals, 95))


def split_half_validation(df: pd.DataFrame, weights: dict | None = None):
    """Score 2022-24 and 2025-26 separately; correlate for players in both."""
    d = df.copy()
    d["period"] = np.where(d.match_date < pd.Timestamp("2025-01-01"), "A", "B")
    relaxed = dict(balls_total=250, balls_pressure=40, pressure_innings6=6, innings_total=8)
    out = {}
    for role, agg in [("Batter", aggregate_batters), ("Bowler", aggregate_bowlers)]:
        parts = []
        for p in ["A", "B"]:
            sub = d[d.period == p]
            m = agg(sub)
            m = m[
                (m.balls_total >= relaxed["balls_total"])
                & (m.balls_pressure >= relaxed["balls_pressure"])
                & (m.pressure_innings6 >= relaxed["pressure_innings6"])
                & (m.innings_total >= relaxed["innings_total"])
            ].copy()
            if len(m) > 5:
                m = add_scores(m, weights)
                m["period"] = p
                parts.append(m[["player_id", "player", "PRS", "period", "balls_pressure"]])
        if len(parts) == 2:
            a = parts[0].rename(columns={"PRS": "PRS_A", "balls_pressure": "bp_A"})
            b = parts[1].rename(columns={"PRS": "PRS_B", "balls_pressure": "bp_B"})
            m = a.merge(b[["player_id", "PRS_B", "bp_B"]], on="player_id")
            if len(m) >= 8:
                rho, pval = spearmanr(m.PRS_A, m.PRS_B)
                out[role] = dict(rho=float(rho), p=float(pval), n=int(len(m)), data=m)
            else:
                out[role] = dict(rho=np.nan, p=np.nan, n=int(len(m)), data=m)
        else:
            out[role] = dict(rho=np.nan, p=np.nan, n=0, data=pd.DataFrame())
    return out


def player_team_map(base: str) -> pd.DataFrame:
    """Country and IPL team for each player id (most frequent in each pool)."""
    mp = pd.read_csv(os.path.join(base, "competition_team_player_mapping.csv"))
    mp["is_ipl"] = mp.comp_name.str.contains("IPL", case=False, na=False)
    ipl = (
        mp[mp.is_ipl].groupby(["player_id", "team_name"]).size()
        .reset_index(name="n").sort_values(["player_id", "n"], ascending=[True, False])
        .drop_duplicates("player_id").set_index("player_id").team_name.rename("ipl_team")
    )
    country = (
        mp[~mp.is_ipl].groupby(["player_id", "team_name"]).size()
        .reset_index(name="n").sort_values(["player_id", "n"], ascending=[True, False])
        .drop_duplicates("player_id").set_index("player_id").team_name.rename("country")
    )
    return pd.concat([ipl, country], axis=1).reset_index()


def sensitivity(df: pd.DataFrame, role: str, base_top: list[int]):
    """Top-10 overlap and rank correlation across plausible weightings."""
    configs = {
        "Base 35/20/20/15/10": dict(output=0.35, uplift=0.20, control=0.20, consistency=0.15, sample=0.10),
        "Output-heavy 45/15/20/10/10": dict(output=0.45, uplift=0.15, control=0.20, consistency=0.10, sample=0.10),
        "Uplift-heavy 30/30/20/10/10": dict(output=0.30, uplift=0.30, control=0.20, consistency=0.10, sample=0.10),
        "Control-heavy 30/15/30/15/10": dict(output=0.30, uplift=0.15, control=0.30, consistency=0.15, sample=0.10),
        "Consistency-heavy 30/15/20/25/10": dict(output=0.30, uplift=0.15, control=0.20, consistency=0.25, sample=0.10),
    }
    rows = []
    base_rank = add_scores(df, configs["Base 35/20/20/15/10"]).set_index("player_id").PRS
    for name, w in configs.items():
        s = add_scores(df, w)
        top = s.head(10).player_id.tolist()
        overlap = len(set(top) & set(base_top))
        common = base_rank.index.intersection(s.player_id)
        rho = spearmanr(base_rank.loc[common], s.set_index("player_id").PRS.loc[common]).correlation
        rows.append(dict(config=name, top10_overlap=overlap, spearman=float(rho)))
    return pd.DataFrame(rows)
