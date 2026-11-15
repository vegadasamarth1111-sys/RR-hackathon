"""End-to-end pipeline for SupeRR Selector Season 2, Round 1.

Run:  python run_all.py
Outputs are written to ./outputs
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from src.prep import load_raw, build_state
from src.model import add_win_probability, add_leverage, add_context_impact, validate_win_probability
from src.metrics import (
    aggregate_batters, aggregate_bowlers, add_scores, eligible,
    bootstrap_ci, split_half_validation, sensitivity, player_team_map,
)
from src import charts
from src.report import build_pdf, build_pptx, build_dashboard


def main():
    t0 = time.time()
    out = os.path.join(BASE, "outputs")
    figdir = os.path.join(out, "figures")
    os.makedirs(figdir, exist_ok=True)

    print("[1/7] Loading and preparing data ...")
    comp, matches, bb, teams, players, xi = load_raw(BASE)
    df = build_state(bb, matches, comp)
    print(f"      {len(df):,} deliveries | {df.match_id.nunique():,} matches | pressure share {df.pressure_rule.mean():.1%}")

    print("[2/7] Win-probability model and leverage ...")
    df, models, feats = add_win_probability(df)
    df = add_leverage(df, models, feats)
    df = add_context_impact(df)
    wp_val = validate_win_probability(df)

    print("[3/7] Aggregating players and scoring ...")
    B = aggregate_batters(df)
    BO = aggregate_bowlers(df)
    EB = eligible(B, "Batter")
    EBO = eligible(BO, "Bowler")
    SB = add_scores(EB)
    SBO = add_scores(EBO)

    # team / country labels
    tm = player_team_map(BASE)
    SB = SB.merge(tm, on="player_id", how="left")
    SBO = SBO.merge(tm, on="player_id", how="left")

    def team_label(r):
        c = r.country if isinstance(r.country, str) else ""
        i = r.ipl_team if isinstance(r.ipl_team, str) else ""
        return " · ".join([x for x in [c, i] if x])

    SB["team_label"] = SB.apply(team_label, axis=1)
    SBO["team_label"] = SBO.apply(team_label, axis=1)
    SB["rank"] = np.arange(1, len(SB) + 1)
    SBO["rank"] = np.arange(1, len(SBO) + 1)
    top_bat = SB.head(10).copy()
    top_bowl = SBO.head(10).copy()

    print("[4/7] Bootstrap and validation ...")
    for d, role in [(top_bat, "Batter"), (top_bowl, "Bowler")]:
        lows, highs = [], []
        for pid in d.player_id:
            lo, hi = bootstrap_ci(df, pid, role, n_boot=1000)
            lows.append(lo); highs.append(hi)
        d["ci_low"] = lows
        d["ci_high"] = highs
    SB = SB.merge(top_bat[["player_id", "ci_low", "ci_high"]], on="player_id", how="left")
    SBO = SBO.merge(top_bowl[["player_id", "ci_low", "ci_high"]], on="player_id", how="left")

    split = split_half_validation(df)
    sens_bat = sensitivity(EB, "Batter", top_bat.player_id.tolist())
    sens_bowl = sensitivity(EBO, "Bowler", top_bowl.player_id.tolist())

    print("[5/7] Saving tables ...")
    SB.to_csv(os.path.join(out, "all_batters_scored.csv"), index=False)
    SBO.to_csv(os.path.join(out, "all_bowlers_scored.csv"), index=False)
    top_bat.to_csv(os.path.join(out, "top10_batters.csv"), index=False)
    top_bowl.to_csv(os.path.join(out, "top10_bowlers.csv"), index=False)

    summary = {
        "deliveries": int(len(df)),
        "matches": int(df.match_id.nunique()),
        "matches_in_metadata": int(matches.match_id.nunique()),
        "matches_without_ball_data": int(len(set(matches.match_id) - set(bb.match_id))),
        "matches_without_winner": int(matches.win_team_id.isna().sum()),
        "completed_matches_wp": int(df[df.win_team_id.notna()].match_id.nunique()),
        "batters": int(df.striker_id.nunique()),
        "bowlers": int(df.bowler_id.nunique()),
        "competitions": int(df.comp_id.nunique()),
        "seasons": [str(s) for s in sorted(df.season.dropna().unique().tolist())],
        "pressure_share": float(df.pressure_rule.mean()),
        "pressure_deliveries": int(df.pressure_rule.sum()),
        "multi_rule_share": float(
            (
                df[["chase_pressure", "death_close", "collapse", "knockout_close", "early_collapse"]]
                .sum(axis=1)[df.pressure_rule] >= 2
            ).mean()
        ),
        "pressure_rules": {
            "Chase": float(df.chase_pressure.mean()),
            "Death": float(df.death_close.mean()),
            "Collapse": float(df.collapse.mean()),
            "Knockout": float(df.knockout_close.mean()),
            "Early collapse": float(df.early_collapse.mean()),
        },
        "competition_mix": {
            str(k): int(v) for k, v in
            df.groupby("comp_name").match_id.nunique().sort_values(ascending=False)
            .head(12).items()
        },
        "eligible_batters": int(len(EB)),
        "eligible_bowlers": int(len(EBO)),
        "wp": {str(k): {"auc": v["auc"], "brier": v["brier"], "n": v["n"]} for k, v in wp_val.items()},
        "split_half": {k: {"rho": v["rho"], "p": v["p"], "n": v["n"]} for k, v in split.items()},
    }
    with open(os.path.join(out, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("[6/7] Building charts ...")
    charts.pressure_share(df, os.path.join(figdir, "pressure_share.png"))
    charts.leverage_distribution(df, os.path.join(figdir, "leverage.png"))
    charts.calibration(wp_val, os.path.join(figdir, "calibration.png"))
    charts.top_bar(top_bat, os.path.join(figdir, "top_batters.png"),
                   "Top 10 batters under pressure", color=charts.PINK)
    charts.top_bar(top_bowl, os.path.join(figdir, "top_bowlers.png"),
                   "Top 10 bowlers under pressure", color=charts.TEAL)
    charts.pressure_vs_baseline(
        SB, top_bat.player_id.tolist(), os.path.join(figdir, "bat_baseline.png"),
        "Pressure output vs own baseline (batters)",
        "Non-pressure impact / 100 balls", "Pressure impact / 100 balls", charts.PINK,
    )
    charts.pressure_vs_baseline(
        SBO, top_bowl.player_id.tolist(), os.path.join(figdir, "bowl_baseline.png"),
        "Pressure output vs own baseline (bowlers)",
        "Non-pressure impact / 100 balls", "Pressure impact / 100 balls", charts.TEAL,
    )
    charts.sensitivity_plot(sens_bat, sens_bowl, os.path.join(figdir, "sensitivity.png"))
    charts.split_half_plot(split, os.path.join(figdir, "split_half.png"))
    charts.bootstrap_plot(top_bat, os.path.join(figdir, "boot_bat.png"),
                          "Batter pressure impact with 90% bootstrap CI", charts.PINK)
    charts.bootstrap_plot(top_bowl, os.path.join(figdir, "boot_bowl.png"),
                          "Bowler pressure impact with 90% bootstrap CI", charts.TEAL)
    charts.overall_vs_pressure(SB, os.path.join(figdir, "overall_vs_pressure_bat.png"),
                               "Pressure ranking is not just an overall ranking (batters)", charts.PINK)
    charts.overall_vs_pressure(SBO, os.path.join(figdir, "overall_vs_pressure_bowl.png"),
                               "Pressure ranking is not just an overall ranking (bowlers)", charts.TEAL)
    charts.radar(
        SB, top_bat.head(5).player_id.tolist(), os.path.join(figdir, "radar_bat.png"),
        "Top 5 batters: percentile profile",
        ["output_pct", "uplift_pct", "control_pct", "consistency_pct", "sample_pct"],
        ["Output", "Uplift", "Control", "Consistency", "Sample"],
        charts.PINK,
    )
    charts.radar(
        SBO, top_bowl.head(5).player_id.tolist(), os.path.join(figdir, "radar_bowl.png"),
        "Top 5 bowlers: percentile profile",
        ["output_pct", "uplift_pct", "control_pct", "consistency_pct", "sample_pct"],
        ["Output", "Uplift", "Control", "Consistency", "Sample"],
        charts.TEAL,
    )

    print("[7/7] Building report ...")
    context = dict(
        summary=summary, top_bat=top_bat, top_bowl=top_bowl,
        SB=SB, SBO=SBO, sens_bat=sens_bat, sens_bowl=sens_bowl,
        wp_val=wp_val, split=split, figdir=figdir, out=out,
        df=df, comp=comp, matches=matches, players=players, xi=xi,
    )
    build_pdf(context)
    build_pptx(context)
    build_dashboard(context)
    print(f"Done in {time.time() - t0:.1f}s. Outputs in {out}")


if __name__ == "__main__":
    main()
