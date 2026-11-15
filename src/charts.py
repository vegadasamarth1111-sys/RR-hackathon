"""Chart generation for the SupeRR methodology report."""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

PINK = "#E91E8C"
NAVY = "#0B1F3A"
TEAL = "#0E7C86"
GOLD = "#D9A441"
GREY = "#8A94A6"
LIGHT = "#F4F6FA"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#CBD2DC",
    "axes.labelcolor": NAVY,
    "xtick.color": "#4A5568",
    "ytick.color": "#4A5568",
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelsize": 10,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def pressure_share(df, path):
    d = df.groupby(["innings", "phase"], observed=True).pressure_rule.mean().reset_index()
    d["phase"] = pd.Categorical(d.phase, ["powerplay", "middle", "death"], ordered=True)
    d = d.sort_values(["innings", "phase"])
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    phases = ["powerplay", "middle", "death"]
    x = np.arange(len(phases))
    w = 0.36
    for i, inn in enumerate([1, 2]):
        vals = [d[(d.innings == inn) & (d.phase == p)].pressure_rule.mean() * 100 for p in phases]
        ax.bar(x + (i - 0.5) * w, vals, w, label=f"Innings {inn}", color=[NAVY, PINK][i])
        for xi, v in zip(x + (i - 0.5) * w, vals):
            ax.text(xi, v + 1, f"{v:.0f}%", ha="center", va="bottom", fontsize=8, color="#4A5568")
    ax.set_xticks(x)
    ax.set_xticklabels(["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"])
    ax.set_ylabel("% of deliveries classed as pressure")
    ax.set_title("Pressure is concentrated in the death overs and in chases")
    ax.legend(frameon=False, loc="upper left")
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def leverage_distribution(df, path):
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    data = [df[df.phase == p].leverage.clip(0, 0.15) for p in ["powerplay", "middle", "death"]]
    bp = ax.boxplot(data, vert=False, patch_artist=True, widths=0.55,
                    medianprops=dict(color="white", linewidth=1.4))
    for patch, color in zip(bp["boxes"], [NAVY, TEAL, PINK]):
        patch.set_facecolor(color)
        patch.set_alpha(0.9)
    ax.set_yticklabels(["Powerplay", "Middle", "Death"])
    ax.set_xlabel("Leverage (expected win-probability swing of the next ball)")
    ax.set_title("Leverage separates ordinary death overs from true nail-biters")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def calibration(wp_val, path):
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4))
    for ax, inn, color in zip(axes, [1, 2], [NAVY, PINK]):
        t = wp_val[inn]["calibration"]
        ax.plot([0, 1], [0, 1], "--", color=GREY, linewidth=1)
        ax.plot(t.pred, t.actual, "o-", color=color, linewidth=2, markersize=5)
        ax.set_title(f"Innings {inn}  |  AUC {wp_val[inn]['auc']:.2f}")
        ax.set_xlabel("Predicted win probability")
        ax.set_ylabel("Observed win rate")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.grid(alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Win-probability model is well calibrated, especially in chases", fontsize=13, fontweight="bold", color=NAVY)
    _save(fig, path)


def top_bar(df, path, title, value_col="PRS", color=PINK, n=10):
    d = df.head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    bars = ax.barh(d.player, d[value_col], color=color, height=0.65)
    for bar, v in zip(bars, d[value_col]):
        ax.text(v + 1, bar.get_y() + bar.get_height() / 2, f"{v:.1f}", va="center", fontsize=8, color="#4A5568")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Pressure Reliability Score (0-100)")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.2)
    _save(fig, path)


def pressure_vs_baseline(df, top_ids, path, title, xlabel, ylabel, color=PINK):
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.scatter(df.impact_nonpressure, df.impact_pressure, s=22, color=GREY, alpha=0.35, edgecolor="none")
    t = df[df.player_id.isin(top_ids)]
    ax.scatter(t.impact_nonpressure, t.impact_pressure, s=60, color=color, edgecolor="white", linewidth=0.8, zorder=3)
    for _, r in t.iterrows():
        ax.annotate(r.player.split()[-1], (r.impact_nonpressure, r.impact_pressure),
                    xytext=(4, 4), textcoords="offset points", fontsize=7, color=NAVY)
    lo = min(df.impact_nonpressure.min(), df.impact_pressure.min()) - 5
    hi = max(df.impact_nonpressure.max(), df.impact_pressure.max()) + 5
    ax.plot([lo, hi], [lo, hi], "--", color=GREY, linewidth=1)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def sensitivity_plot(sens_bat, sens_bowl, path):
    fig, ax = plt.subplots(figsize=(7.8, 3.6))
    labels = sens_bat.config.tolist()
    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w/2, sens_bat.top10_overlap, w, label="Batters", color=NAVY)
    ax.bar(x + w/2, sens_bowl.top10_overlap, w, label="Bowlers", color=PINK)
    for i, (a, b) in enumerate(zip(sens_bat.top10_overlap, sens_bowl.top10_overlap)):
        ax.text(i - w/2, a + 0.15, str(a), ha="center", fontsize=8)
        ax.text(i + w/2, b + 0.15, str(b), ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace(" ", "\n", 1) for l in labels], fontsize=7)
    ax.set_ylim(0, 11)
    ax.set_ylabel("Top-10 players retained")
    ax.set_title("Rankings are stable under plausible weight changes", pad=6)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def bootstrap_plot(df, path, title, color=PINK):
    d = df.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    y = np.arange(len(d))
    ax.errorbar(d.impact_pressure, y,
                xerr=[d.impact_pressure - d.ci_low, d.ci_high - d.impact_pressure],
                fmt="o", color=color, ecolor=GREY, elinewidth=1.6, capsize=3, markersize=6)
    ax.axvline(0, color=GREY, linewidth=1, linestyle="--")
    ax.set_yticks(y); ax.set_yticklabels(d.player)
    ax.set_xlabel("Pressure impact per 100 balls (90% bootstrap CI)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)


def radar(df, top_ids, path, title, metrics, labels, color=PINK):
    """Radar chart for up to 5 players."""
    d = df[df.player_id.isin(top_ids)].head(5)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig, axes = plt.subplots(1, len(d), figsize=(3.0 * len(d), 3.2), subplot_kw=dict(polar=True))
    if len(d) == 1:
        axes = [axes]
    for ax, (_, r) in zip(axes, d.iterrows()):
        vals = [r[m] for m in metrics]
        vals += vals[:1]
        ax.plot(angles, vals, color=color, linewidth=2)
        ax.fill(angles, vals, color=color, alpha=0.18)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=7)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color=GREY)
        ax.set_title(r.player, fontsize=9, pad=12)
    fig.suptitle(title, fontsize=12, fontweight="bold", color=NAVY, y=1.04)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def split_half_plot(split, path):
    """Scatter of first-period vs second-period PRS for players in both."""
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.5))
    for ax, role, color in zip(axes, ["Batter", "Bowler"], [PINK, TEAL]):
        d = split.get(role, {}).get("data", pd.DataFrame())
        if d is None or len(d) == 0:
            ax.axis("off")
            continue
        ax.scatter(d.PRS_A, d.PRS_B, s=30, color=color, alpha=0.75, edgecolor="white", linewidth=0.5)
        lo = min(d.PRS_A.min(), d.PRS_B.min()) - 5
        hi = max(d.PRS_A.max(), d.PRS_B.max()) + 5
        ax.plot([lo, hi], [lo, hi], "--", color=GREY, linewidth=1)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        rho = split[role]["rho"]
        p = split[role]["p"]
        n = split[role]["n"]
        ax.set_title(f"{role}s: rho = {rho:.2f} (p = {p:.2f}, n = {n})")
        ax.set_xlabel("PRS, 2022-24")
        ax.set_ylabel("PRS, 2025-26")
        ax.grid(alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Split-half reliability: pressure bowling repeats better than pressure batting",
                 fontsize=12, fontweight="bold", color=NAVY)
    _save(fig, path)


def overall_vs_pressure(df, path, title, color=PINK):
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(df.overall_rank, df.PRS, s=24, color=GREY, alpha=0.4, edgecolor="none")
    t = df.head(10)
    ax.scatter(t.overall_rank, t.PRS, s=60, color=color, edgecolor="white", linewidth=0.8, zorder=3)
    for _, r in t.iterrows():
        ax.annotate(r.player.split()[-1], (r.overall_rank, r.PRS), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Overall impact rank (all balls)")
    ax.set_ylabel("Pressure Reliability Score")
    ax.set_title(title)
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, path)
