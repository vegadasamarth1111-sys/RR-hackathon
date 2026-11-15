"""Presentation deck for the SupeRR submission (16:9, 9 slides)."""
from __future__ import annotations

import os

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from .narrative import f, pct

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
NAVY_2 = RGBColor(0x13, 0x2A, 0x4A)
PINK = RGBColor(0xE9, 0x1E, 0x8C)
PINK_LIGHT = RGBColor(0xFC, 0xE7, 0xF3)
TEAL = RGBColor(0x0E, 0x7C, 0x86)
TEAL_LIGHT = RGBColor(0xDD, 0xF3, 0xF3)
GOLD = RGBColor(0xD9, 0xA4, 0x41)
GREY = RGBColor(0x6B, 0x72, 0x80)
MID = RGBColor(0x8A, 0x94, 0xA6)
LIGHT = RGBColor(0xF4, 0xF6, 0xFA)
LINE = RGBColor(0xDC, 0xE3, 0xEC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xB4, 0x23, 0x18)

FONT = "Arial"


def _bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _rect(slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE, line=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    return s


def _text(slide, x, y, w, h, text, size=12, bold=False, color=NAVY,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, spacing=0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_after = Pt(spacing)
    r = p.add_run()
    r.text = str(text)
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return box


def _rich(slide, x, y, w, h, parts, size=12, color=NAVY, align=PP_ALIGN.LEFT):
    """parts: list of (text, bold, color) tuples."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    for text, bold, col in parts:
        r = p.add_run()
        r.text = str(text)
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = col if col is not None else color
    return box


def _title(slide, kicker, title, dark=False):
    fg = WHITE if dark else NAVY
    _text(slide, 0.6, 0.38, 6.5, 0.25, kicker.upper(), 9, True, PINK)
    _text(slide, 0.6, 0.64, 12.1, 0.55, title, 28, True, fg)
    _rect(slide, 0.6, 1.25, 12.1, 0.035, PINK)


def _footer(slide, page):
    _text(slide, 0.6, 7.18, 8.0, 0.2, "IPL & T20I, 2022–2026. Rankings are model estimates, not guarantees.",
          7, False, MID)
    _text(slide, 11.7, 7.18, 1.0, 0.2, str(page), 8, False, MID, PP_ALIGN.RIGHT)


def _image(slide, path, x, y, w, h):
    if not os.path.exists(path):
        return
    iw, ih = PILImage.open(path).size
    scale = min(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    slide.shapes.add_picture(path, Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2),
                             Inches(nw), Inches(nh))


def _table(slide, rows, x, y, w, h, widths, font=8.5, header=True, highlight=(1, 2, 3),
           align_right=(), highlight_color=PINK_LIGHT):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    for i, cw in enumerate(widths):
        tbl.columns[i].width = Inches(cw)
    for ri in range(len(rows)):
        tbl.rows[ri].height = Inches(h / len(rows))
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_left = Inches(0.05)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if header and ri == 0:
                cell.fill.fore_color.rgb = NAVY
            elif ri in highlight:
                cell.fill.fore_color.rgb = highlight_color
            else:
                cell.fill.fore_color.rgb = WHITE if ri % 2 else LIGHT
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT if ci in align_right else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(font)
            r.font.bold = (header and ri == 0) or (ci == 1 and ri > 0)
            r.font.color.rgb = WHITE if (header and ri == 0) else NAVY
    return tbl


def _batter_rows(df, n=10):
    rows = [["#", "Player", "Team / country", "PRS", "Impact", "Uplift", "SR", "Dot%", "Bdry"]]
    for i, (_, r) in enumerate(df.head(n).iterrows(), start=1):
        team = str(r.get("team_label", "") or "")
        rows.append([i, r.player, team, f"{r.PRS:.1f}", f(r.impact_pressure), f(r.uplift, plus=True),
                     f(r.sr_pressure), pct(r.dot_pct), pct(r.boundary_pct)])
    return rows


def _bowler_rows(df, n=10):
    rows = [["#", "Player", "Team / country", "PRS", "Impact", "Uplift", "Econ", "Dot%", "Bdry"]]
    for i, (_, r) in enumerate(df.head(n).iterrows(), start=1):
        team = str(r.get("team_label", "") or "")
        rows.append([i, r.player, team, f"{r.PRS:.1f}", f(r.impact_pressure), f(r.uplift, plus=True),
                     f(r.economy_pressure, 2), pct(r.dot_pct), pct(r.boundary_pct)])
    return rows


def _title_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, NAVY)
    _rect(s, 10.0, -1.0, 4.6, 4.6, RGBColor(0x3A, 0x1D, 0x4D), MSO_SHAPE.OVAL)
    _rect(s, -2.5, 6.0, 3.0, 3.0, RGBColor(0x0D, 0x3D, 0x45), MSO_SHAPE.OVAL)
    _text(s, 0.7, 0.65, 10.0, 0.3, "SUPERR SELECTOR  ·  SEASON 2  ·  ROUND 1", 10, True, PINK)
    _text(s, 0.7, 1.15, 10.6, 1.6, "When the game gets loud,\nwho holds up?", 40, True, WHITE)
    _text(s, 0.7, 2.75, 9.8, 0.8,
          "A reproducible pressure-performance model for T20 batting and bowling, built from the supplied IPL and T20I ball-by-ball data.",
          14, False, RGBColor(0xC9, 0xD6, 0xE8))
    tb, tw = ctx["top_bat"], ctx["top_bowl"]
    _text(s, 0.7, 4.0, 4.8, 0.25, "TOP 3 BATTERS", 9, True, PINK)
    _text(s, 0.7, 4.3, 4.8, 1.5,
          f"1  {tb.iloc[0].player}   {tb.iloc[0].PRS:.1f}\n"
          f"2  {tb.iloc[1].player}   {tb.iloc[1].PRS:.1f}\n"
          f"3  {tb.iloc[2].player}   {tb.iloc[2].PRS:.1f}",
          15, False, WHITE, spacing=7)
    _text(s, 6.6, 4.0, 5.8, 0.25, "TOP 3 BOWLERS", 9, True, PINK)
    _text(s, 6.6, 4.3, 5.8, 1.5,
          f"1  {tw.iloc[0].player}   {tw.iloc[0].PRS:.1f}\n"
          f"2  {tw.iloc[1].player}   {tw.iloc[1].PRS:.1f}\n"
          f"3  {tw.iloc[2].player}   {tw.iloc[2].PRS:.1f}",
          15, False, WHITE, spacing=7)
    _text(s, 0.7, 6.55, 10.0, 0.3, "Full top 10s, pressure definition, scoring logic, validation and limitations inside.",
          9, False, RGBColor(0xAF, 0xC0, 0xD6))
    return s


def _answer_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "The answer", "Two pressure top 10s — ordered by PRS")
    _text(s, 0.6, 1.42, 5.8, 0.25, "TOP 10 BATTERS", 10, True, PINK)
    _text(s, 6.8, 1.42, 5.8, 0.25, "TOP 10 BOWLERS", 10, True, TEAL)
    _table(s, _batter_rows(ctx["top_bat"]), 0.6, 1.72, 6.0, 4.75,
           [0.27, 1.10, 1.92, 0.44, 0.58, 0.48, 0.44, 0.40, 0.40],
           font=7.7, highlight_color=PINK_LIGHT)
    _table(s, _bowler_rows(ctx["top_bowl"]), 6.8, 1.72, 6.0, 4.75,
           [0.27, 1.10, 1.92, 0.44, 0.58, 0.48, 0.44, 0.40, 0.40],
           font=7.7, highlight_color=TEAL_LIGHT)
    _text(s, 0.6, 6.62, 12.1, 0.35,
          "PRS is a 0–100 percentile composite. Impact is context-adjusted runs (batters) or runs saved (bowlers) "
          "per 100 pressure balls. Uplift is the change from the player's own non-pressure baseline.",
          8.5, False, GREY)
    _footer(s, 2)
    return s


def _pressure_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "Pressure definition", "Five observable states — not just 'the death overs'")
    rules = [
        ("1", "Chase pressure", "2nd innings, after over 4, RRR ≥ 10, ≤ 5 wickets in hand"),
        ("2", "Death pressure", "Overs 16–20, within 15 runs of par"),
        ("3", "Collapse pressure", "4+ down and behind the game, or 6+ down in the last five overs"),
        ("4", "Knockout pressure", "Knockout match, overs 10–20, within 25 runs"),
        ("5", "Early collapse", "3+ wickets down in the powerplay and behind the game"),
        ("=", "One pressure flag", "A ball is pressure if any rule fires; the flags stay separate for diagnostics."),
    ]
    for i, (num, name, desc) in enumerate(rules):
        row, col = divmod(i, 3)
        x = 0.6 + col * 3.55
        y = 1.55 + row * 1.65
        accent = PINK if row == 0 else (GOLD if i == 5 else TEAL)
        _rect(s, x, y, 3.3, 1.42, LIGHT)
        _rect(s, x, y, 0.06, 1.42, accent)
        _text(s, x + 0.15, y + 0.10, 0.35, 0.35, num, 16, True, accent)
        _text(s, x + 0.52, y + 0.12, 2.6, 0.25, name, 12, True, NAVY)
        _text(s, x + 0.52, y + 0.43, 2.6, 0.8, desc, 8.8, False, GREY)
    summary = ctx["summary"]
    kpis = [
        (f"{summary['pressure_share']:.1%}", "of deliveries meet at least one rule", PINK),
        (f"{summary['pressure_deliveries']:,}", "pressure deliveries", TEAL),
        (f"{summary['multi_rule_share']:.1%}", "of pressure balls trigger 2+ rules", GOLD),
        (f"{summary['pressure_rules']['Death']:.1%}", "of all deliveries qualify via death", NAVY),
    ]
    for i, (val, lab, col) in enumerate(kpis):
        x = 0.6 + i * 3.08
        _rect(s, x, 5.35, 2.9, 0.95, LIGHT)
        _rect(s, x, 5.35, 0.06, 0.95, col)
        _text(s, x + 0.18, 5.43, 2.5, 0.35, val, 18, True, NAVY)
        _text(s, x + 0.18, 5.82, 2.6, 0.35, lab, 8, False, GREY)
    _text(s, 0.6, 6.5, 12.1, 0.3,
          "A delivery can satisfy multiple rules. We keep the flags, then use one pressure flag for aggregation.",
          8.5, False, GREY)
    _footer(s, 3)
    return s


def _model_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "Model", "From match state to a Pressure Reliability Score")
    stages = [
        ("1. State", "Score, wickets, balls, target, RRR, phase, stakes"),
        ("2. Pressure", "Five rules + leverage weight from win probability"),
        ("3. Impact", "Runs above par for batters; runs saved for bowlers"),
        ("4. Uplift", "Pressure impact minus the player's own baseline"),
        ("5. PRS", "Output, uplift, control, consistency, sample"),
    ]
    for i, (head, desc) in enumerate(stages):
        x = 0.6 + i * 2.42
        _rect(s, x, 1.65, 2.18, 1.0, NAVY if i % 2 == 0 else NAVY_2, MSO_SHAPE.CHEVRON)
        _text(s, x + 0.48, 1.83, 1.55, 0.25, head, 11.5, True, WHITE)
        _text(s, x + 0.05, 2.85, 2.05, 0.95, desc, 8.8, False, GREY)
    _rect(s, 0.6, 4.15, 12.1, 0.9, LIGHT)
    _rect(s, 0.6, 4.15, 0.06, 0.9, PINK)
    _text(s, 0.8, 4.25, 11.7, 0.25, "PRESSURE RELIABILITY SCORE", 9, True, PINK)
    _text(s, 0.8, 4.50, 11.7, 0.35,
          "PRS = 0.35 Output + 0.20 Uplift + 0.20 Control + 0.15 Consistency + 0.10 Sample",
          14, True, NAVY)
    _text(s, 0.6, 5.35, 12.1, 0.6,
          "Bowlers use 0.40 / 0.15 / 0.20 / 0.15 / 0.10. Every component is a percentile rank in the eligible pool. "
          "Impact and uplift are shrunk by n/(n+80) so small samples cannot dominate.",
          9.5, False, GREY)
    _text(s, 0.6, 6.25, 12.1, 0.35,
          "No player identity, team reputation, age, salary or nationality enters the model.",
          10, True, NAVY)
    _footer(s, 4)
    return s


def _ranking_slide(prs, ctx, role):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    color = PINK if role == "Batter" else TEAL
    title = "Top 10 batters under pressure" if role == "Batter" else "Top 10 bowlers under pressure"
    _title(s, "The ranking", title)
    rows = _batter_rows(ctx["top_bat"]) if role == "Batter" else _bowler_rows(ctx["top_bowl"])
    _table(s, rows, 0.6, 1.52, 7.45, 5.05,
           [0.27, 1.45, 2.15, 0.50, 0.68, 0.58, 0.54, 0.50, 0.50],
           font=8.0, highlight_color=PINK_LIGHT if role == "Batter" else TEAL_LIGHT)
    img = "top_batters.png" if role == "Batter" else "top_bowlers.png"
    _image(s, os.path.join(ctx["figdir"], img), 8.25, 1.52, 4.45, 2.65)
    if role == "Batter":
        lead = ctx["top_bat"].iloc[0]
        bullets = [
            f"{lead.player} pairs top-decile output with {lead.dot_pct:.0f}% dots, the lowest in the top 10.",
            "Uplift moves high-volume stars down when they do not raise their game.",
            "Treat ranks 4–10 as a tier; the bootstrap intervals overlap.",
        ]
    else:
        bullets = [
            "Sunil Narine combines economy, dots and a positive-innings rate.",
            "Control is the common thread across the top five.",
            "Pressure bowling is the more repeatable side of the model.",
        ]
    _text(s, 8.25, 4.35, 4.45, 0.25, "WHY THIS ORDER", 9, True, color)
    _text(s, 8.25, 4.65, 4.45, 1.9, "\n".join("•  " + b for b in bullets), 9.2, False, GREY, spacing=4)
    _text(s, 0.6, 6.72, 12.1, 0.3,
          "Impact = context-adjusted runs per 100 pressure balls (batters) or runs saved per 100 (bowlers). "
          "The 90% CI is in the PDF tables.", 7.8, False, GREY)
    _footer(s, 5 if role == "Batter" else 6)
    return s


def _evidence_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "Evidence", "The lists are not just overall-impact lists")
    _image(s, os.path.join(ctx["figdir"], "bat_baseline.png"), 0.6, 1.5, 5.9, 3.4)
    _image(s, os.path.join(ctx["figdir"], "bowl_baseline.png"), 6.8, 1.5, 5.9, 3.4)
    _text(s, 0.6, 5.05, 5.9, 0.3, "BATTERS: PRESSURE VS OWN BASELINE", 9, True, PINK)
    _text(s, 6.8, 5.05, 5.9, 0.3, "BOWLERS: PRESSURE VS OWN BASELINE", 9, True, TEAL)
    _text(s, 0.6, 5.42, 12.1, 0.8,
          "Above the diagonal means a player is better under pressure than in non-pressure balls. The highlighted "
          "players are the top 10. The gap between the lists and the all-ball impact ranking is the point: context "
          "changes who looks best.",
          10, False, GREY)
    _rect(s, 0.6, 6.32, 12.1, 0.6, LIGHT)
    _rect(s, 0.6, 6.32, 0.06, 0.6, TEAL)
    overlap_b = int((ctx["top_bat"].overall_rank <= 20).sum())
    overlap_w = int((ctx["top_bowl"].overall_rank <= 20).sum())
    _text(s, 0.82, 6.42, 11.6, 0.35,
          f"Only {overlap_b} of the top 10 batters and {overlap_w} of the top 10 bowlers are also top 20 on all-ball impact.",
          10, True, NAVY)
    _footer(s, 7)
    return s


def _validation_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "Reliability", "Does the ranking survive scrutiny?")
    _image(s, os.path.join(ctx["figdir"], "split_half.png"), 0.6, 1.45, 5.9, 3.0)
    _image(s, os.path.join(ctx["figdir"], "sensitivity.png"), 6.8, 1.45, 5.9, 3.0)
    sb, sw = ctx["split"]["Batter"], ctx["split"]["Bowler"]
    wp = ctx["wp_val"]
    sens_min = min(ctx["sens_bat"].top10_overlap.min(), ctx["sens_bowl"].top10_overlap.min())
    sens_max = max(ctx["sens_bat"].top10_overlap.max(), ctx["sens_bowl"].top10_overlap.max())
    kpis = [
        (f"{sb['rho']:.2f}", "batter split-half rho", "noisy", PINK),
        (f"{sw['rho']:.2f}", "bowler split-half rho", "repeatable", TEAL),
        (f"{sens_min}–{sens_max}/10", "top-10 names retained", "weight sensitivity", GOLD),
        (f"{wp[1]['auc']:.2f} / {wp[2]['auc']:.2f}", "WP AUC, innings 1 / 2", "held-out matches", NAVY),
    ]
    for i, (val, lab, note, col) in enumerate(kpis):
        x = 0.6 + i * 3.08
        _rect(s, x, 4.75, 2.9, 1.05, LIGHT)
        _rect(s, x, 4.75, 0.06, 1.05, col)
        _text(s, x + 0.18, 4.83, 2.5, 0.35, val, 18, True, NAVY)
        _text(s, x + 0.18, 5.2, 2.6, 0.22, lab, 8, True, GREY)
        _text(s, x + 0.18, 5.43, 2.6, 0.22, note, 7.5, False, GREY)
    _text(s, 0.6, 6.12, 12.1, 0.65,
          "Batting pressure is noisy; bowling pressure is moderately repeatable. Membership survives plausible "
          "weight changes, but adjacent ranks often overlap. The report treats the list as tiers, not a precise verdict.",
          10, False, GREY)
    _footer(s, 8)
    return s


def _limits_slide(prs, ctx):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s, WHITE)
    _title(s, "Discussion", "Limitations, and how to use the list")
    _text(s, 0.6, 1.5, 5.8, 0.25, "WHAT THE MODEL DOES NOT KNOW", 9, True, PINK)
    limits = [
        "No age or date of birth in the pack — no youngest-player analysis.",
        "Pressure is observational; we do not measure temperament.",
        "No ball-tracking, field placement or catch difficulty.",
        "Role and team context are only partly observed.",
        "Competition weights are a judgment call.",
        "This is a historical ranking, not a forecast.",
    ]
    _text(s, 0.6, 1.82, 5.8, 1.7, "\n".join("•  " + x for x in limits), 9.6, False, GREY, spacing=6)
    sm = ctx["summary"]
    _text(s, 0.6, 3.62, 5.8, 0.25, "WHAT WE ANALYSED", 9, True, TEAL)
    _text(
        s, 0.6, 3.92, 5.8, 1.2,
        f"{sm['deliveries']:,} deliveries across {sm['matches']} matches, {sm['seasons'][0]}–{sm['seasons'][-1]}.\n"
        f"IPL, T20I and other T20; {sm['pressure_share'] * 100:.1f}% of deliveries meet a pressure rule.\n"
        f"{sm['matches_without_ball_data']} matches have no ball-by-ball data; {sm['matches_without_winner']} have no winner.",
        9.2, False, GREY, spacing=6,
    )
    _rect(s, 0.6, 5.55, 5.8, 0.8, LIGHT)
    _rect(s, 0.6, 5.55, 0.06, 0.8, PINK)
    _text(s, 0.82, 5.66, 5.4, 0.55,
          "Data-sharing warning: raw CSVs are not redistributed. The deck contains only aggregated metrics and derived charts.",
          8.2, False, GREY)
    _text(s, 6.9, 1.5, 5.8, 0.25, "HOW A SELECTOR SHOULD USE IT", 9, True, TEAL)
    _text(s, 6.9, 1.82, 5.8, 1.15,
          "Use the top tier as a shortlist, not a verdict. Pair the pressure profile with role fit, availability, "
          "recent form and the balance of the XI. The model is strongest when it challenges reputation.",
          10, False, GREY)
    picks = [
        ["Role", "Player", "Why"],
        ["Batter", ctx["top_bat"].iloc[0].player, "Best output + uplift + control"],
        ["Bowler", ctx["top_bowl"].iloc[0].player, "Best economy + dots + consistency"],
        ["Value", ctx["top_bat"].iloc[4].player, "High upside; sample is the caveat"],
    ]
    _table(s, picks, 6.9, 3.15, 5.85, 1.55, [0.8, 1.55, 3.5], font=8.6, highlight=(1, 2, 3),
           highlight_color=TEAL_LIGHT)
    _text(s, 6.9, 4.95, 5.8, 0.25, "BOTTOM LINE", 9, True, PINK)
    _text(s, 6.9, 5.25, 5.8, 1.2,
          "Pressure is a narrow, identifiable state. The players who perform in it are not simply the players with "
          "the best overall numbers. Take the tiers seriously; take the exact order lightly.",
          10.5, False, NAVY)
    _text(s, 0.6, 6.55, 12.1, 0.3,
          "Full methodology, validation and player-by-player risk notes are in the PDF report.",
          8.5, False, GREY)
    _footer(s, 9)
    return s


def build_pptx(ctx):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    _title_slide(prs, ctx)
    _answer_slide(prs, ctx)
    _pressure_slide(prs, ctx)
    _model_slide(prs, ctx)
    _ranking_slide(prs, ctx, "Batter")
    _ranking_slide(prs, ctx, "Bowler")
    _evidence_slide(prs, ctx)
    _validation_slide(prs, ctx)
    _limits_slide(prs, ctx)
    path = os.path.join(ctx["out"], "SupeRR_Selector_Deck.pptx")
    prs.save(path)
    return path
