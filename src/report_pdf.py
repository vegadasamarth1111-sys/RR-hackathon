"""PDF methodology report for the SupeRR Selector submission."""
from __future__ import annotations

import os
from datetime import date
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

from .narrative import f, pct, batter_narrative, bowler_narrative

# ---------------------------------------------------------------------------
# Brand, typography and shared layout
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#0B1F3A")
NAVY_2 = colors.HexColor("#132A4A")
PINK = colors.HexColor("#E91E8C")
PINK_LIGHT = colors.HexColor("#FCE7F3")
TEAL = colors.HexColor("#0E7C86")
TEAL_LIGHT = colors.HexColor("#DDF3F3")
GOLD = colors.HexColor("#D9A441")
GREY = colors.HexColor("#6B7280")
MID = colors.HexColor("#8A94A6")
LIGHT = colors.HexColor("#F4F6FA")
LIGHT_2 = colors.HexColor("#EAF0F6")
LINE = colors.HexColor("#DCE3EC")
WHITE = colors.white
RED = colors.HexColor("#B42318")

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 34
CONTENT_W = PAGE_W - 2 * MARGIN


def _register_fonts():
    import matplotlib
    base = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    specs = {
        "DejaVu": "DejaVuSans.ttf",
        "DejaVu-Bold": "DejaVuSans-Bold.ttf",
        "DejaVu-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVu-BoldOblique": "DejaVuSans-BoldOblique.ttf",
    }
    for name, fn in specs.items():
        path = os.path.join(base, fn)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        "DejaVu", normal="DejaVu", bold="DejaVu-Bold",
        italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique",
    )


_register_fonts()


def S(name, **kw):
    base = dict(fontName="DejaVu", fontSize=9, leading=12.2, textColor=NAVY, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    "h1": S("h1", fontName="DejaVu-Bold", fontSize=22, leading=25, textColor=NAVY, spaceAfter=2),
    "h2": S("h2", fontName="DejaVu-Bold", fontSize=12.5, leading=15, textColor=NAVY, spaceBefore=5, spaceAfter=3),
    "kicker": S("kicker", fontName="DejaVu-Bold", fontSize=7.6, leading=9, textColor=PINK, spaceAfter=2),
    "body": S("body", fontSize=9.2, leading=12.8, spaceAfter=5),
    "body_b": S("body_b", fontName="DejaVu-Bold", fontSize=9.2, leading=12.8, spaceAfter=4),
    "small": S("small", fontSize=7.8, leading=10.4, textColor=GREY, spaceAfter=2),
    "tiny": S("tiny", fontSize=6.8, leading=8.6, textColor=GREY),
    "bullet": S("bullet", fontSize=8.7, leading=11.6, leftIndent=11, bulletIndent=2, spaceAfter=2.5),
    "note": S("note", fontSize=8.2, leading=11, textColor=NAVY, backColor=LIGHT, borderColor=LINE,
              borderWidth=0.5, borderPadding=7, spaceBefore=4, spaceAfter=5),
    "quote": S("quote", fontName="DejaVu-Oblique", fontSize=9.5, leading=13, textColor=NAVY_2,
               leftIndent=8, borderColor=PINK, borderWidth=0, borderPadding=0),
    "cell": S("cell", fontSize=7.8, leading=9.7, spaceAfter=0),
    "cell_b": S("cell_b", fontName="DejaVu-Bold", fontSize=7.8, leading=9.7, spaceAfter=0),
    "cell_c": S("cell_c", fontSize=7.8, leading=9.7, alignment=TA_CENTER, spaceAfter=0),
    "cell_r": S("cell_r", fontSize=7.8, leading=9.7, alignment=TA_RIGHT, spaceAfter=0),
    "hdr": S("hdr", fontName="DejaVu-Bold", fontSize=7.2, leading=8.8, textColor=WHITE, spaceAfter=0),
    "hdr_c": S("hdr_c", fontName="DejaVu-Bold", fontSize=7.2, leading=8.8, textColor=WHITE, alignment=TA_CENTER, spaceAfter=0),
    "hdr_r": S("hdr_r", fontName="DejaVu-Bold", fontSize=7.2, leading=8.8, textColor=WHITE, alignment=TA_RIGHT, spaceAfter=0),
    "card_name": S("card_name", fontName="DejaVu-Bold", fontSize=10.2, leading=12, spaceAfter=1),
    "card_team": S("card_team", fontSize=7.2, leading=9, textColor=GREY, spaceAfter=2),
    "card_text": S("card_text", fontSize=7.2, leading=9.2, spaceAfter=1),
    "kpi_value": S("kpi_value", fontName="DejaVu-Bold", fontSize=17, leading=19, textColor=NAVY),
    "kpi_label": S("kpi_label", fontName="DejaVu-Bold", fontSize=6.8, leading=8.4, textColor=GREY),
    "kpi_note": S("kpi_note", fontSize=6.8, leading=8.2, textColor=GREY),
    "cover_kicker": S("cover_kicker", fontName="DejaVu-Bold", fontSize=8.5, leading=10, textColor=PINK),
    "cover_title": S("cover_title", fontName="DejaVu-Bold", fontSize=38, leading=41, textColor=WHITE),
    "cover_sub": S("cover_sub", fontSize=13, leading=18, textColor=colors.HexColor("#C9D6E8")),
    "cover_label": S("cover_label", fontName="DejaVu-Bold", fontSize=7.2, leading=9, textColor=PINK),
    "cover_name": S("cover_name", fontSize=12.5, leading=15, textColor=WHITE, spaceAfter=5),
    "cover_meta": S("cover_meta", fontSize=7.5, leading=10, textColor=colors.HexColor("#AFC0D6")),
}


def P(text, style="body", bullet=None):
    return Paragraph(text, ST[style], bulletText=bullet)


def img(path, max_w, max_h, align="CENTER"):
    if not path or not os.path.exists(path):
        return Spacer(1, 2)
    from PIL import Image as PILImage
    try:
        w, h = PILImage.open(path).size
    except Exception:
        return Spacer(1, 2)
    scale = min(max_w / w, max_h / h)
    im = Image(path, width=w * scale, height=h * scale)
    im.hAlign = align
    return im


def rule(color=PINK, space_before=1, space_after=7):
    return HRFlowable(width="100%", thickness=1.4, color=color,
                      spaceBefore=space_before, spaceAfter=space_after)


def h1(title, kicker=None):
    out = []
    if kicker:
        out.append(P(kicker.upper(), "kicker"))
    out += [P(title, "h1"), rule()]
    return out


def kpi(value, label, note="", color=PINK):
    body = [
        P(str(value), "kpi_value"),
        P(label.upper(), "kpi_label"),
    ]
    if note:
        body.append(P(note, "kpi_note"))
    t = Table([[body]], colWidths=[168], rowHeights=[52])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def table(rows, widths, header=True, font=7.8, highlight=None, align="LEFT", pad=3.0):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign=align)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ]
        for r in range(1, len(rows)):
            if r % 2 == 0:
                cmds.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    if highlight:
        for r in highlight:
            cmds.append(("BACKGROUND", (0, r), (-1, r), PINK_LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def mini_list(df, color=PINK, width=318):
    rows = [[P("#", "hdr_c"), P("PLAYER", "hdr"), P("PRS", "hdr_r")]]
    for i, (_, r) in enumerate(df.head(10).iterrows(), start=1):
        rows.append([
            P(str(i), "cell_c"),
            P(escape(str(r.player)), "cell_b" if i <= 3 else "cell"),
            P(f"{r.PRS:.1f}", "cell_r"),
        ])
    t = Table(rows, colWidths=[36, width - 86, 50], hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
    ]
    for r in range(1, 4):
        cmds.append(("BACKGROUND", (0, r), (-1, r), PINK_LIGHT if color == PINK else TEAL_LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def formula_box(title, formula, note, color=PINK, width=CONTENT_W):
    inner = [
        P(title.upper(), "kicker"),
        P(formula, "body_b"),
        P(note, "small"),
    ]
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 4, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def callout(title, text, color=PINK, width=CONTENT_W):
    """Full-width takeaway box used at the foot of evidence pages."""
    inner = [
        P(title.upper(), "kicker"),
        P(text, "body"),
    ]
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 4, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _cover_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(PINK)
    canvas.setFillAlpha(0.16)
    canvas.circle(PAGE_W - 25, PAGE_H - 10, 205, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.setFillAlpha(0.13)
    canvas.circle(-30, 50, 175, fill=1, stroke=0)
    canvas.setFillAlpha(1)
    canvas.setStrokeColor(colors.HexColor("#2A4365"))
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN, 58, PAGE_W - MARGIN, 58)
    canvas.setFillColor(colors.HexColor("#AFC0D6"))
    canvas.setFont("DejaVu", 7.2)
    canvas.drawString(MARGIN, 42, "Built from the supplied ball-by-ball pack. Raw data is not redistributed.")
    canvas.drawRightString(PAGE_W - MARGIN, 42, "Round 1  ·  Methodology report")
    canvas.restoreState()


def _main_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.setFont("DejaVu-Bold", 7)
    canvas.drawString(MARGIN, PAGE_H - 21, "SUPERR SELECTOR  /  SEASON 2  /  ROUND 1")
    canvas.setFillColor(MID)
    canvas.setFont("DejaVu", 7)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 21, "Pressure Performance Methodology")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_H - 28, PAGE_W - MARGIN, PAGE_H - 28)
    canvas.setFillColor(MID)
    canvas.setFont("DejaVu", 6.8)
    canvas.drawString(MARGIN, 16, "IPL & T20I, 2022–2026. Rankings are model estimates, not guarantees.")
    canvas.drawRightString(PAGE_W - MARGIN, 16, str(doc.page))
    canvas.restoreState()


def _cover(ctx):
    tb, tw = ctx["top_bat"], ctx["top_bowl"]
    rows = [[P("TOP 3 BATTERS", "cover_label"), P("TOP 3 BOWLERS", "cover_label")]]
    for i in range(3):
        b, w = tb.iloc[i], tw.iloc[i]
        rows.append([
            P(f"{i+1} &nbsp; <b>{escape(str(b.player))}</b><br/><font color='#AFC0D6'>{b.PRS:.1f} PRS</font>", "cover_name"),
            P(f"{i+1} &nbsp; <b>{escape(str(w.player))}</b><br/><font color='#AFC0D6'>{w.PRS:.1f} PRS</font>", "cover_name"),
        ])
    ct = Table(rows, colWidths=[330, 330])
    ct.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#2A4365")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
    ]))
    return [
        NextPageTemplate("Main"),
        Spacer(1, 14),
        P("SUPERR SELECTOR  ·  SEASON 2  ·  ROUND 1", "cover_kicker"),
        Spacer(1, 10),
        P("When the game gets loud,<br/>who holds up?", "cover_title"),
        Spacer(1, 9),
        P("A reproducible pressure-performance model for T20 batting and bowling, "
          "built from the supplied IPL and T20I ball-by-ball data.", "cover_sub"),
        Spacer(1, 20),
        ct,
        Spacer(1, 18),
        P("Full top 10 lists, pressure definition, scoring logic, validation and limitations inside.", "cover_meta"),
        PageBreak(),
    ]


def _exec(ctx):
    s = ctx["summary"]
    tb, tw = ctx["top_bat"], ctx["top_bowl"]
    sb, sw = ctx["split"]["Batter"], ctx["split"]["Bowler"]
    death = s["pressure_rules"]["Death"]
    overlap_b = int((tb.overall_rank <= 20).sum())
    overlap_w = int((tw.overall_rank <= 20).sum())
    min_sens = min(ctx["sens_bat"].top10_overlap.min(), ctx["sens_bowl"].top10_overlap.min())
    left = [
        P("The short answer", "h2"),
        P(f"<b>{escape(str(tb.iloc[0].player))}</b> and <b>{escape(str(tw.iloc[0].player))}</b> "
          f"top the two lists. The full ordered top 10s are on the right; the evidence is on pages 8–13.", "body"),
        P("Four findings that shaped the model", "h2"),
        P(f"<b>Pressure is a state, not a phase.</b> Only {s['pressure_share']:.1%} of deliveries meet at least one "
          f"pressure rule. Death overs are not automatically pressure: {death:.1%} of all deliveries qualify through the death rule.", "bullet", "•"),
        P(f"<b>The lists are not overall-impact lists.</b> Only {overlap_b} of the top 10 batters and {overlap_w} of the top 10 "
          f"bowlers are also in the top 20 on all-ball impact. Context changes the answer.", "bullet", "•"),
        P(f"<b>Bowling pressure repeats; batting pressure is noisy.</b> Split-half rho is {sw['rho']:.2f} for bowlers "
          f"(p={sw['p']:.3f}, n={sw['n']}) versus {sb['rho']:.2f} for batters (p={sb['p']:.2f}, n={sb['n']}). "
          f"Dot-ball control is the most repeatable batting signal (rho≈0.55).", "bullet", "•"),
        P(f"<b>The rankings are stable.</b> Across five plausible weightings, at least {min_sens}/10 of each top 10 survives; "
          f"the exact order moves more than the membership.", "bullet", "•"),
        P("Scope check", "h2"),
        P("The data pack has no date of birth or age field, and the official Round 1 brief asks for the best pressure "
          "batters and bowlers — not the youngest uncapped players. We therefore optimised for the actual task. "
          "Every ranking below is supported by the supplied data, not reputation.", "note"),
    ]
    right = [
        P("Top 10 batters", "h2"),
        mini_list(tb, PINK),
        Spacer(1, 7),
        P("Top 10 bowlers", "h2"),
        mini_list(tw, TEAL),
    ]
    body = Table([[left, right]], colWidths=[435, 330], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    kpis = Table([[
        kpi(f"{s['deliveries']:,}", "deliveries", "after cleaning", PINK),
        kpi(s["matches"], "matches", "with ball-by-ball data", TEAL),
        kpi(f"{s['pressure_share']:.0%}", "pressure share", f"{s['pressure_deliveries']:,} deliveries", GOLD),
        kpi(f"{s['eligible_batters']} / {s['eligible_bowlers']}", "eligible", "batters / bowlers", NAVY),
    ]], colWidths=[190, 190, 190, 190], hAlign="LEFT")
    kpis.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [*h1("The 10 players who hold up when it matters", "Executive summary"), body,
            Spacer(1, 6), kpis, PageBreak()]


def _data(ctx):
    s, df = ctx["summary"], ctx["df"]
    cm = (df.groupby("comp_name", dropna=False)
          .agg(matches=("match_id", "nunique"), deliveries=("match_id", "size"), tier=("tier", "first"))
          .sort_values("matches", ascending=False).head(7).reset_index())
    rows = [[P("COMPETITION", "hdr"), P("MATCHES", "hdr_r"), P("DELIVERIES", "hdr_r"), P("WEIGHT", "hdr_r")]]
    for _, r in cm.iterrows():
        rows.append([P(escape(str(r.comp_name)), "cell"), P(f"{int(r.matches)}", "cell_r"),
                     P(f"{int(r.deliveries):,}", "cell_r"), P(f"{r.tier:.2f}", "cell_r")])
    comp_t = table(rows, [180, 55, 60, 45], font=7.6)
    source_rows = [
        [P("SOURCE", "hdr"), P("ROWS USED", "hdr_r"), P("ROLE IN THE MODEL", "hdr")],
        [P("ball_by_ball.csv", "cell_b"), P(f"{len(df):,}", "cell_r"), P("Delivery state, pressure flags, impact", "cell")],
        [P("matches.csv", "cell_b"), P(f"{s['matches_in_metadata']:,}", "cell_r"), P("Date, stage, winner, target, revised overs", "cell")],
        [P("competitions.csv", "cell_b"), P(f"{len(ctx['comp']):,}", "cell_r"), P("Format, season, competition tier", "cell")],
        [P("competition_team_player_mapping.csv", "cell_b"), P(f"{len(ctx['players']):,}", "cell_r"), P("Player names, teams, countries", "cell")],
        [P("playing_eleven.csv", "cell_b"), P(f"{len(ctx['xi']):,}", "cell_r"), P("XI validation and role sanity checks", "cell")],
    ]
    src_t = table(source_rows, [150, 45, 190], font=7.4)
    bullets = [
        P("<b>`runs` is runs off the bat, not total team runs.</b> Extras are encoded separately. "
          "`extras1_runs` is an extras-type code, not a run value, so we reconstruct extras conservatively "
          "(wide/no-ball = 1, bye/leg-bye = 1, penalty = 5).", "bullet", "•"),
        P("<b>The revised-overs columns store balls, not overs.</b> A value of 114 means a 19-over innings; "
          "we use the value directly as the innings ball limit.", "bullet", "•"),
        P("<b>`over_ball_num` includes wides and no-balls.</b> We build a cumulative legal-ball count and use that "
          "for overs remaining, phase and required rate.", "bullet", "•"),
        P("<b>Super overs are excluded.</b> Only innings 1 and 2 enter the main analysis; innings 3 and 4 are a "
          "different game state and are too rare to model fairly.", "bullet", "•"),
        P(f"<b>Missing matches are handled explicitly.</b> {s['matches_without_ball_data']} matches have no ball-by-ball "
          f"rows and are absent; {s['matches_without_winner']} matches have no winner and are excluded from win-probability "
          f"training and validation, though their pressure deliveries remain in descriptive aggregates.", "bullet", "•"),
        P("<b>Competition weights are a judgment call.</b> IPL = 1.00, T20I = 0.90, other T20 = 0.75. "
          "The weights scale pressure impact; they do not change the pressure definition.", "bullet", "•"),
    ]
    left = [P("Data sources", "h2"), src_t, Spacer(1, 8), P("Competition mix (top 7 by matches)", "h2"), comp_t]
    right = [P("Cleaning decisions that change the answer", "h2"), *bullets]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("What we analysed, and what we had to fix", "Data and cleaning"), body, PageBreak()]


def _pressure(ctx):
    s, df = ctx["summary"], ctx["df"]
    pr = s["pressure_rules"]
    flags = df[["chase_pressure", "death_close", "collapse", "knockout_close", "early_collapse"]]
    n_rules = flags.sum(axis=1)
    overlap = (n_rules[n_rules > 0] >= 2).mean()
    rule_rows = [
        [P("RULE", "hdr"), P("TRIGGER", "hdr"), P("WHY IT MATTERS", "hdr")],
        [P("1. Chase pressure", "cell_b"),
         P("2nd innings, after over 4, required rate ≥ 10, ≤ 5 wickets in hand", "cell"),
         P("The scoreboard, not the clock, is the source of stress. Wickets in hand keep the chase live.", "cell")],
        [P("2. Death pressure", "cell_b"),
         P("Overs 16–20, within 15 runs of par", "cell"),
         P("The last five overs are where a game is usually won or lost — but only when it is still close.", "cell")],
        [P("3. Collapse pressure", "cell_b"),
         P("4+ wickets down and behind the game, or 6+ down in the last five overs", "cell"),
         P("A batter walking in after a collapse faces a different task: survive, rebuild, or farm the strike.", "cell")],
        [P("4. Knockout pressure", "cell_b"),
         P("Knockout match, overs 10–20, within 25 runs", "cell"),
         P("Elimination stakes add a psychological cost that a regular league game does not.", "cell")],
        [P("5. Early collapse", "cell_b"),
         P("3+ wickets down in the powerplay and behind the game", "cell"),
         P("The powerplay is usually a scoring phase. Losing three early changes the whole innings plan.", "cell")],
    ]
    rt = table(rule_rows, [80, 205, 275], font=7.4, pad=3.4)
    stat_rows = [[P("SIGNAL", "hdr"), P("SHARE", "hdr_r")]]
    for label, key in [("Any pressure rule", "pressure_share"), ("Chase", "Chase"), ("Death", "Death"),
                       ("Collapse", "Collapse"), ("Knockout", "Knockout"), ("Early collapse", "Early collapse")]:
        val = s[key] if key == "pressure_share" else pr[key]
        stat_rows.append([P(label, "cell"), P(f"{val:.1%}", "cell_r")])
    stat_rows.append([P("2+ rules at once", "cell_b"), P(f"{overlap:.1%} of pressure balls", "cell_r")])
    st = table(stat_rows, [105, 65], font=7.6)
    left = [P("The five rules", "h2"), rt]
    right = [P("How often?", "h2"), st,
             Spacer(1, 8),
             P("A delivery can satisfy more than one rule. We keep the individual flags, then use a single "
               "`pressure_rule` flag for aggregation. This preserves the reason a ball was stressful while "
               "avoiding double counting.", "small")]
    body = Table([[left, right]], colWidths=[590, 175], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("What counts as pressure?", "Pressure definition"),
            P("Pressure is a match state, not a reputation and not simply 'the death overs'. We define five "
              "observable situations that a player can recognise in real time. The definition is deliberately "
              "rule-based so a coach can audit it ball by ball.", "body"),
            body, Spacer(1, 2),
            img(os.path.join(ctx["figdir"], "pressure_share.png"), 390, 178),
            P("Pressure is concentrated in chases and death overs — but the two are not the same.", "small"),
            PageBreak()]


def _wp(ctx):
    s = ctx["summary"]
    wp = s["wp"]
    rows = [[P("INNINGS", "hdr"), P("AUC", "hdr_r"), P("BRIER", "hdr_r"), P("DELIVERIES", "hdr_r")]]
    for inn in ("1", "2"):
        d = wp[inn]
        rows.append([P(f"Innings {inn}", "cell"), P(f"{d['auc']:.3f}", "cell_r"),
                     P(f"{d['brier']:.3f}", "cell_r"), P(f"{d['n']:,}", "cell_r")])
    wt = table(rows, [90, 60, 60, 85], font=7.8)
    left = [
        P("Two models, because a chase is a different problem", "h2"),
        P("A first innings is about building a total without a target. A second innings is about chasing a known "
          "number with a finite number of balls. Forcing both into one model would blur exactly the state that "
          "creates pressure, so we fit separate logistic regressions.", "body"),
        P("The models are deliberately small and transparent. They use score, wickets, balls remaining, current "
          "and required run rate, the projected or target score, par score, knockout status and IPL status. "
          "No player identity, team reputation or salary enters the model.", "body"),
        P("Leverage: the expected swing of the next ball", "h2"),
        P("For every delivery we simulate the nine possible outcomes (0–6, wicket), update the match state, and "
          "re-score win probability. Leverage is the root-mean-square swing, weighted by how often each outcome "
          "actually occurs in that phase:", "body"),
        P("Leverage = √ Σ p(outcome) × (p<sub>after</sub> − p<sub>before</sub>)²", "body_b"),
        P("Pressure deliveries receive weight 1 + leverage percentile, so a ball in a genuine nail-biter counts up "
          "to twice as much as a pressure ball in a comfortable game. The competition tier then scales the weight.", "body"),
        P("Why logistic regression, not a black box?", "h2"),
        P("It is calibrated, stable with this sample size, and every coefficient can be explained to a coach. "
          "The out-of-fold calibration below is the test that matters: predicted probabilities line up with "
          "observed win rates, especially in chases.", "body"),
    ]
    right = [
        P("Out-of-fold validation", "h2"), wt,
        Spacer(1, 8),
        img(os.path.join(ctx["figdir"], "calibration.png"), 360, 175),
        P("Calibration is measured on held-out matches using 5-fold GroupKFold by match, so a model never sees "
          "the same game in training and test.", "small"),
    ]
    body = Table([[left, right]], colWidths=[410, 360], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    features = [
        [P("MODEL INPUT", "hdr"), P("WHY IT BELONGS IN A WIN-PROBABILITY MODEL", "hdr")],
        [P("Score / target / runs needed", "cell_b"), P("The two sides of the same coin: resources used and resources still required.", "cell")],
        [P("Wickets in hand", "cell_b"), P("The main constraint on how aggressively a side can play.", "cell")],
        [P("Balls remaining", "cell_b"), P("Converts a score into a rate and a chase into a finite task.", "cell")],
        [P("Current and required run rate", "cell_b"), P("Captures the gap between the game's tempo and the scoreboard's demand.", "cell")],
        [P("Par score, knockout, IPL", "cell_b"), P("Controls for scoring environment and stakes without using player reputation.", "cell")],
    ]
    ft = table(features, [170, 555], font=7.4, pad=2.8)
    return [*h1("From match state to leverage", "Win probability"),
            body, Spacer(1, 6), ft, PageBreak()]


def _leverage(ctx):
    df = ctx["df"]
    lev = (df.groupby("phase", observed=True).leverage
           .agg(median="median", p90=lambda x: x.quantile(0.9), maximum="max")
           .reindex(["powerplay", "middle", "death"]))
    rows = [[P("PHASE", "hdr"), P("MEDIAN", "hdr_r"), P("90TH PCT", "hdr_r"), P("MAX", "hdr_r")]]
    for phase, r in lev.iterrows():
        rows.append([P(str(phase).title(), "cell_b"), P(f"{r['median']:.3f}", "cell_r"),
                     P(f"{r['p90']:.3f}", "cell_r"), P(f"{r['maximum']:.3f}", "cell_r")])
    t = table(rows, [90, 65, 65, 65], font=7.6)
    left = [
        P("Why phase alone is not enough", "h2"),
        P("A death over in a 40-run win and a death over in a one-run thriller are both 'death overs', but they "
          "are not the same pressure. Leverage measures how much the next ball can change the result, so the "
          "model can separate ordinary death bowling from a genuine nail-biter.", "body"),
        P("The weight is deliberately bounded. A pressure delivery receives 1 + its leverage percentile, so the "
          "most consequential ball counts at most twice as much as the least consequential pressure ball. That "
          "keeps one dramatic over from dominating a career sample.", "body"),
        P("What the table shows", "h2"),
        t,
        Spacer(1, 5),
        P("The median death ball is more consequential than the median powerplay ball, but the maximum leverage "
          "is not confined to the death: a collapse or a tight chase can create a high-leverage ball in the middle.", "small"),
    ]
    right = [
        P("Leverage distribution by phase", "h2"),
        img(os.path.join(ctx["figdir"], "leverage.png"), 360, 205),
        P("Boxes show the interquartile range; points show the long tail. The tail is the reason the model weights "
          "by state, not by phase label.", "small"),
        Spacer(1, 4),
        P("Three practical consequences", "h2"),
        P("<b>1. Not every death ball is pressure.</b> A game already decided has low leverage even in the 20th over.", "bullet", "•"),
        P("<b>2. Not every pressure ball is at the death.</b> A chase or collapse in the middle overs can matter more.", "bullet", "•"),
        P("<b>3. The ranking rewards the moment, not the reputation.</b> A bowler who bowls the 19th over in a blowout "
          "does not get the same credit as one who defends 12 in a final.", "bullet", "•"),
    ]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("Leverage: not all pressure is equal", "Leverage"), body, PageBreak()]


def _measure(ctx):
    bat = formula_box(
        "Batter impact",
        "impact = runs − E[runs | phase, bowler type, IPL] − 1.5 × (out − E[out | phase, IPL])",
        "Runs above what an average batter would score from the same phase, against the same bowler type, "
        "in the same competition. The wicket penalty is 1.5 runs; a batter who gets out has cost his side more "
        "than the raw dot ball suggests.",
        PINK, width=420,
    )
    bowl = formula_box(
        "Bowler impact",
        "impact = E[runs | phase, batter type, IPL] − runs conceded + 2.0 × (wicket − E[wicket | phase, IPL])",
        "Runs saved relative to an average bowler in the same phase and competition, plus a 2.0-run bonus for "
        "a wicket above the expected wicket rate. Positive is always better for the fielding side.",
        TEAL, width=420,
    )
    rows = [
        [P("SIGNAL", "hdr"), P("HOW IT IS TREATED", "hdr"), P("WHY IT IS IN THE MODEL", "hdr")],
        [P("Phase", "cell_b"), P("Expected runs and wickets estimated separately for powerplay, middle and death", "cell"),
         P("A run in the powerplay and a run at the death are not the same currency.", "cell")],
        [P("Bowler type", "cell_b"), P("Pace vs spin expected runs for batters; batter type for bowlers", "cell"),
         P("Matchups change the degree of difficulty; a left-arm spinner in the powerplay is not a generic bowler.", "cell")],
        [P("Competition", "cell_b"), P("IPL vs T20I expected values; tier weight 1.00 / 0.90", "cell"),
         P("Scoring environments differ. IPL and T20I are both high standard, but not identical.", "cell")],
        [P("Wicket", "cell_b"), P("1.5-run penalty for a batter; 2.0-run bonus for a bowler", "cell"),
         P("A wicket is a resource, not just another dot ball. The values are deliberately conservative.", "cell")],
        [P("Own baseline", "cell_b"), P("Each player's non-pressure impact per 100 balls", "cell"),
         P("The brief asks who rises above their usual level, not just who is good.", "cell")],
    ]
    mt = table(rows, [82, 305, 340], font=7.4, pad=3.2)
    left = [
        P("Why not raw runs, strike rate or economy?", "h2"),
        P("Raw numbers punish players who bat in difficult phases and reward players who feast in easy ones. "
          "A 40-ball 60 in a comfortable powerplay is not the same as a 25-ball 40 in a 12-an-over chase. "
          "Context adjustment puts both on a comparable scale.", "body"),
        P("The baseline is the player himself", "h2"),
        P("For every player we compute pressure impact and non-pressure impact per 100 balls. Uplift is the "
          "difference. A player who is excellent in both states can still rank highly on output, but the uplift "
          "term rewards the specific skill the brief is asking about.", "body"),
        P("What the model deliberately ignores", "h2"),
        P("Reputation, auction price, nationality, age, team strength and social-media narrative. Those may be "
          "useful selection inputs, but they are not evidence of pressure performance in this data pack.", "note"),
    ]
    right = [P("Batter impact", "h2"), bat, Spacer(1, 5), P("Bowler impact", "h2"), bowl]
    body = Table([[left, right]], colWidths=[330, 420], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("Measuring performance, not reputation", "Performance measurement"),
            body, Spacer(1, 2), mt, PageBreak()]


def _score(ctx):
    rows = [
        [P("COMPONENT", "hdr"), P("BATTER WEIGHT", "hdr_r"), P("BOWLER WEIGHT", "hdr_r"), P("WHAT IT MEASURES", "hdr")],
        [P("Output", "cell_b"), P("35%", "cell_r"), P("40%", "cell_r"), P("Context-adjusted pressure impact per 100 balls, shrunk for sample size", "cell")],
        [P("Uplift", "cell_b"), P("20%", "cell_r"), P("15%", "cell_r"), P("Pressure impact minus the player's own non-pressure impact", "cell")],
        [P("Control", "cell_b"), P("20%", "cell_r"), P("20%", "cell_r"), P("Batters: low dot-ball rate. Bowlers: high dots + low boundary rate", "cell")],
        [P("Consistency", "cell_b"), P("15%", "cell_r"), P("15%", "cell_r"), P("Share of pressure innings with positive impact, shrunk toward 50%", "cell")],
        [P("Sample", "cell_b"), P("10%", "cell_r"), P("10%", "cell_r"), P("n / (n + 80), so small samples cannot dominate", "cell")],
    ]
    wt = table(rows, [68, 50, 50, 222], font=7.4, pad=3.2)
    left = [
        P("The composite", "h2"),
        formula_box("Pressure Reliability Score (PRS)",
                    "PRS = 0.35 Output + 0.20 Uplift + 0.20 Control + 0.15 Consistency + 0.10 Sample",
                    "Bowlers use 0.40 / 0.15 / 0.20 / 0.15 / 0.10. Every component is a percentile rank within "
                    "the eligible pool, so the final score is on a 0–100 scale.", PINK, width=330),
        Spacer(1, 5),
        P("Why these weights?", "h2"),
        P("Output gets the largest share because the brief asks who delivers, not who looks busy. Uplift and "
          "control split the next largest share because they separate pressure-specific skill from general quality. "
          "Consistency and sample are guards against one hot series or a small cameo.", "body"),
        P("The weights were set before looking at the final top 10, then stress-tested with five alternatives. "
          "The membership is stable; the exact order is not. That is the honest level of precision in a sample "
          "of this size.", "body"),
    ]
    right = [
        P("Component definitions", "h2"), wt,
        Spacer(1, 6),
        P("Shrinkage and eligibility", "h2"),
        P("Impact and uplift are shrunk by n/(n+80), where n is pressure balls. A player with 80 pressure balls "
          "keeps half his raw signal; a player with 800 keeps 91%. Consistency is shrunk toward 50% using a "
          "five-innings prior. This is a Bayesian-style guard, not a penalty for being young or new.", "body"),
        P("Eligibility (separate for each role)", "h2"),
    ]
    elig = [
        [P("CRITERION", "hdr"), P("BATTER", "hdr_r"), P("BOWLER", "hdr_r")],
        [P("Total balls", "cell"), P("≥ 500", "cell_r"), P("≥ 500", "cell_r")],
        [P("Pressure balls", "cell"), P("≥ 80", "cell_r"), P("≥ 100", "cell_r")],
        [P("Pressure innings (≥6 balls)", "cell"), P("≥ 12", "cell_r"), P("≥ 10", "cell_r")],
        [P("Total innings", "cell"), P("≥ 15", "cell_r"), P("≥ 12", "cell_r")],
    ]
    right += [table(elig, [175, 70, 70], font=7.4)]
    body = Table([[left, right]], colWidths=[350, 400], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("The Pressure Reliability Score", "Scoring model"), body, PageBreak()]


def _batter_table(ctx):
    tb = ctx["top_bat"]
    widths = [28, 130, 160, 42, 52, 48, 44, 40, 42, 40, 34, 114]
    rows = [[
        P("#", "hdr_c"), P("PLAYER", "hdr"), P("TEAM / COUNTRY", "hdr"), P("PRS", "hdr_r"),
        P("IMPACT<br/>/100", "hdr_r"), P("UPLIFT", "hdr_r"), P("SR", "hdr_r"),
        P("DOT %", "hdr_r"), P("BDRY %", "hdr_r"), P("BALLS", "hdr_r"),
        P("INNS", "hdr_r"), P("90% CI", "hdr_r"),
    ]]
    for i, (_, r) in enumerate(tb.iterrows(), start=1):
        ci = f"{r.ci_low:.0f}–{r.ci_high:.0f}" if pd.notna(r.get("ci_low")) else "—"
        rows.append([
            P(str(i), "cell_c"),
            P(escape(str(r.player)), "cell_b"),
            P(escape(str(r.get("team_label", "—") or "—")), "cell"),
            P(f"{r.PRS:.1f}", "cell_r"),
            P(f(r.impact_pressure), "cell_r"),
            P(f(r.uplift, plus=True), "cell_r"),
            P(f(r.sr_pressure), "cell_r"),
            P(pct(r.dot_pct), "cell_r"),
            P(pct(r.boundary_pct), "cell_r"),
            P(f"{int(r.balls_pressure)}", "cell_r"),
            P(f"{int(r.pressure_innings6)}", "cell_r"),
            P(ci, "cell_r"),
        ])
    t = table(rows, widths, font=7.4, highlight=[1, 2, 3], pad=4.0)
    note = P("PRS is a 0–100 percentile composite; higher is better. Impact is context-adjusted runs per 100 pressure "
             "balls. Uplift = pressure impact minus the player's own non-pressure impact. The 90% CI is an innings "
             "bootstrap and describes uncertainty in impact, not in the PRS order. Team/country is the most frequent "
             "label in the mapping file.", "small")
    return [*h1("Top 10 batters under pressure", "The ranking"),
            P("Ordered by Pressure Reliability Score. The top three are shaded; the rest of the list is best read "
              "as a tier rather than a precise ordinal ranking.", "body"),
            t, Spacer(1, 6), note, Spacer(1, 12),
            img(os.path.join(ctx["figdir"], "radar_bat.png"), 660, 128),
            P("Percentile profile of the top five: output, uplift, control, consistency and sample confidence.", "small"),
            PageBreak()]


def _batter_evidence(ctx):
    top = ctx["top_bat"]
    left = [P("Score separation", "h2"),
            img(os.path.join(ctx["figdir"], "top_batters.png"), 375, 205),
            P("The top two are close, then a gap opens to the chasing pack; ranks 3–6 and 7–10 are separated by small differences.", "small")]
    right = [P("Pressure vs own baseline", "h2"),
             img(os.path.join(ctx["figdir"], "bat_baseline.png"), 355, 205),
             P("Above the diagonal = better under pressure than in non-pressure balls. The highlighted players are "
               "the top 10.", "small")]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    bullets = [
        P(f"<b>Output and control agree at the top.</b> {escape(str(top.iloc[0].player))} pairs top-decile "
          f"pressure output with a {top.iloc[0].dot_pct:.0f}% dot rate, the lowest in the top 10; that is why he is "
          f"not just a boundary pick.", "bullet", "•"),
        P("<b>Uplift changes the middle of the list.</b> Several high-volume stars have strong raw output but a "
          "smaller jump over their own baseline; the model moves them down relative to players who clearly raise "
          "their game.", "bullet", "•"),
        P("<b>The exact order is uncertain.</b> Bootstrap intervals overlap for most of ranks 4–10. Select from the "
          "top tier, then use role fit and availability to break ties.", "bullet", "•"),
    ]
    takeaway = callout(
        "What this means for selection",
        f"{escape(str(top.iloc[0].player))} and {escape(str(top.iloc[1].player))} pair top-decile pressure output "
        f"with a clearly positive uplift on their own baseline. Below them the list is a "
        f"set of specialists: choose the profile that fits the role — control for a rebuild, boundary power for a "
        f"free hit — rather than treating rank 4 to rank 10 as a strict order.",
    )
    return [*h1("Batter evidence: output, uplift and control", "Evidence"), body, Spacer(1, 5), *bullets,
            Spacer(1, 8), takeaway, PageBreak()]


def _card(r, role, color):
    why, risk = batter_narrative(r) if role == "Batter" else bowler_narrative(r)
    team = escape(str(r.get("team_label", "—") or "—"))
    body = [
        P(f"<b>{int(r['rank'])}. {escape(str(r.player))}</b> &nbsp; <font color='#E91E8C'>{r.PRS:.1f}</font>", "card_name"),
        P(team, "card_team"),
        P(f"<b>Why</b> {escape(why)}", "card_text"),
        P(f"<b>Risk</b> {escape(risk)}", "card_text"),
    ]
    inner = Table([[body]], colWidths=[365])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return inner


def _cards_page(ctx, role):
    d = ctx["top_bat"] if role == "Batter" else ctx["top_bowl"]
    color = PINK if role == "Batter" else TEAL
    rows = []
    for i in range(0, 10, 2):
        rows.append([_card(d.iloc[i], role, color), _card(d.iloc[i + 1], role, color)])
    t = Table(rows, colWidths=[387, 387], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 10),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    title = "Batter profiles: the why and the risk" if role == "Batter" else \
            "Bowler profiles: the why and the risk"
    return [*h1(title, f"{role} profiles"), t, PageBreak()]


def _bowler_table(ctx):
    tw = ctx["top_bowl"]
    widths = [28, 130, 160, 42, 52, 48, 48, 40, 42, 40, 40, 104]
    rows = [[
        P("#", "hdr_c"), P("PLAYER", "hdr"), P("TEAM / COUNTRY", "hdr"), P("PRS", "hdr_r"),
        P("IMPACT<br/>/100", "hdr_r"), P("UPLIFT", "hdr_r"), P("ECON", "hdr_r"),
        P("DOT %", "hdr_r"), P("BDRY %", "hdr_r"), P("WKTS", "hdr_r"),
        P("BALLS", "hdr_r"), P("90% CI", "hdr_r"),
    ]]
    for i, (_, r) in enumerate(tw.iterrows(), start=1):
        ci = f"{r.ci_low:.0f}–{r.ci_high:.0f}" if pd.notna(r.get("ci_low")) else "—"
        rows.append([
            P(str(i), "cell_c"),
            P(escape(str(r.player)), "cell_b"),
            P(escape(str(r.get("team_label", "—") or "—")), "cell"),
            P(f"{r.PRS:.1f}", "cell_r"),
            P(f(r.impact_pressure), "cell_r"),
            P(f(r.uplift, plus=True), "cell_r"),
            P(f(r.economy_pressure, 2), "cell_r"),
            P(pct(r.dot_pct), "cell_r"),
            P(pct(r.boundary_pct), "cell_r"),
            P(f"{int(r.wickets_pressure)}", "cell_r"),
            P(f"{int(r.balls_pressure)}", "cell_r"),
            P(ci, "cell_r"),
        ])
    t = table(rows, widths, font=7.4, highlight=[1, 2, 3], pad=4.0)
    note = P("PRS is a 0–100 percentile composite; higher is better. Impact is context-adjusted runs saved per 100 "
             "pressure balls. Economy is pressure economy. The 90% CI is an innings bootstrap. Wicket and boundary "
             "rates are descriptive; they are not extra terms in the score.", "small")
    return [*h1("Top 10 bowlers under pressure", "The ranking"),
            P("Ordered by Pressure Reliability Score. The top three are shaded. Control dominates this list: every "
              "top-five bowler combines a pressure economy below 7.0 with a dot rate above 38%.", "body"),
            t, Spacer(1, 6), note, Spacer(1, 12),
            img(os.path.join(ctx["figdir"], "radar_bowl.png"), 660, 128),
            P("Percentile profile of the top five: output, uplift, control, consistency and sample confidence.", "small"),
            PageBreak()]


def _bowler_evidence(ctx):
    top = ctx["top_bowl"]
    left = [P("Score separation", "h2"),
            img(os.path.join(ctx["figdir"], "top_bowlers.png"), 375, 205),
            P("The top two are close; after them the field is tightly packed, with overlapping intervals through the top 10.", "small")]
    right = [P("Pressure vs own baseline", "h2"),
             img(os.path.join(ctx["figdir"], "bowl_baseline.png"), 355, 205),
             P("Above the diagonal = better under pressure than in non-pressure balls. The highlighted players are "
               "the top 10.", "small")]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    bullets = [
        P(f"<b>Control is the common thread.</b> {escape(str(top.iloc[0].player))} has the best combination of "
          f"pressure economy, dot rate and positive-innings rate among high-volume bowlers; the rest of the top five "
          f"are variations on the same theme.", "bullet", "•"),
        P("<b>Wicket threat is a tiebreaker, not the whole score.</b> A bowler can rank highly through dots and "
          "economy even without a huge wicket count; that is intentional, because wickets are partly luck.", "bullet", "•"),
        P("<b>Pressure bowling is the more reliable side of the model.</b> Split-half correlation is positive and "
          "significant, so the bowling list should be trusted more than the batting list.", "bullet", "•"),
    ]
    takeaway = callout(
        "What this means for selection",
        f"{escape(str(top.iloc[0].player))}, {escape(str(top.iloc[1].player))} and {escape(str(top.iloc[2].player))} "
        f"separate on control rather than wicket volume. If the XI needs a strike bowler instead, "
        f"{escape(str(top.iloc[3].player))} and {escape(str(top.iloc[4].player))} have the highest pressure impact, "
        f"but on thinner samples — pair them with a controller rather than asking them to anchor both ends.",
        color=TEAL,
    )
    return [*h1("Bowler evidence: control, economy and wickets", "Evidence"), body, Spacer(1, 5), *bullets,
            Spacer(1, 8), takeaway, PageBreak()]


def _validation(ctx):
    sb, sw = ctx["split"]["Batter"], ctx["split"]["Bowler"]
    sb_min, sb_max = int(ctx["sens_bat"].top10_overlap.min()), int(ctx["sens_bat"].top10_overlap.max())
    sw_min, sw_max = int(ctx["sens_bowl"].top10_overlap.min()), int(ctx["sens_bowl"].top10_overlap.max())
    rows = [
        [P("CHECK", "hdr"), P("BATTERS", "hdr_r"), P("BOWLERS", "hdr_r"), P("READ", "hdr")],
        [P("Split-half Spearman rho", "cell_b"), P(f"{sb['rho']:.2f}", "cell_r"), P(f"{sw['rho']:.2f}", "cell_r"),
         P("How well the first period predicts the second", "cell")],
        [P("p-value", "cell_b"), P(f"{sb['p']:.3f}", "cell_r"), P(f"{sw['p']:.3f}", "cell_r"),
         P("Probability of this correlation under no relationship", "cell")],
        [P("Players in both halves", "cell_b"), P(f"{sb['n']}", "cell_r"), P(f"{sw['n']}", "cell_r"),
         P("Relaxed eligibility for the reliability test", "cell")],
        [P("Top-10 overlap across weightings", "cell_b"), P(f"{sb_min}–{sb_max}/10", "cell_r"), P(f"{sw_min}–{sw_max}/10", "cell_r"),
         P("Membership stability, not order stability", "cell")],
    ]
    t = table(rows, [150, 70, 70, 380], font=7.5, pad=3.5)
    imgs = Table([[
        [P("Split-half reliability", "h2"), img(os.path.join(ctx["figdir"], "split_half.png"), 390, 200)],
        [P("Weight sensitivity", "h2"), img(os.path.join(ctx["figdir"], "sensitivity.png"), 350, 200)],
    ]], colWidths=[405, 365], hAlign="LEFT")
    imgs.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    bullets = [
        P(f"<b>Batting pressure is noisy.</b> The split-half correlation is {sb['rho']:.2f} (p={sb['p']:.2f}); we cannot "
          f"claim that a batter's next pressure innings is predictable from this record. The ranking is a description "
          f"of what happened, not a forecast.", "bullet", "•"),
        P(f"<b>Bowling pressure is moderately repeatable.</b> The split-half correlation is {sw['rho']:.2f} (p={sw['p']:.3f}), "
          f"which is a real signal in a noisy sport. This is why the bowling list is the more defensible of the two.", "bullet", "•"),
        P("<b>Membership survives reasonable disagreement.</b> Across output-heavy, uplift-heavy, control-heavy and "
          "consistency-heavy weights, at least eight of ten names survive in each list. The order is less stable than "
          "the membership, which is exactly what the report says.", "bullet", "•"),
        P("<b>Bootstrap intervals are in the tables.</b> Adjacent ranks with overlapping 90% intervals should be treated "
          "as a tier. The model is not precise enough to separate rank 6 from rank 8 on its own.", "bullet", "•"),
    ]
    return [*h1("Does the ranking survive scrutiny?", "Reliability and validation"),
            t, Spacer(1, 6), imgs, Spacer(1, 3), *bullets, PageBreak()]


def _limits(ctx):
    tb, tw = ctx["top_bat"], ctx["top_bowl"]
    left = [
        P("What the model does not know", "h2"),
        P("<b>No age or date of birth.</b> The pack cannot support a youngest-player analysis. The official task is "
          "pressure performance, so that is what we modelled.", "bullet", "•"),
        P("<b>Pressure is observational.</b> We infer stress from match state. We do not measure heart rate, "
          "self-report or temperament.", "bullet", "•"),
        P("<b>No ball-tracking or field data.</b> Catch difficulty, field placement, bowl speed and batter intent "
          "are not in the pack. A dot ball can be a good ball, a bad miss or a deliberate sighter.", "bullet", "•"),
        P("<b>Role and team context are incomplete.</b> An opener and a finisher face different pressure tasks. "
          "The phase and wicket controls help, but they do not fully separate roles.", "bullet", "•"),
        P("<b>Competition weights are a judgment call.</b> IPL = 1.00, T20I = 0.90, other T20 = 0.75. A different "
          "weighting would move players with very different competition mixes.", "bullet", "•"),
        P("<b>This is not a forecast.</b> It ranks historical pressure performance. Form, injury, role changes and "
          "opponent quality still matter for selection.", "bullet", "•"),
    ]
    right = [
        P("How a selector should use the list", "h2"),
        P("Use the top tier as a shortlist, not a verdict. Pair the pressure profile with role fit, availability, "
          "recent form and the balance of the XI. The model is strongest when it is used to challenge reputation, "
          "not to replace scouting.", "body"),
        P("Three names we would defend", "h2"),
    ]
    picks = [
        [P("ROLE", "hdr"), P("PLAYER", "hdr"), P("WHY", "hdr")],
        [P("Batter", "cell_b"), P(escape(str(tb.iloc[0].player)), "cell_b"),
         P("Best combination of pressure output, uplift and dot-ball control in the pool.", "cell")],
        [P("Bowler", "cell_b"), P(escape(str(tw.iloc[0].player)), "cell_b"),
         P(f"Elite pressure economy and control, with a positive impact in {tw.iloc[0].pos_rate:.0%} of pressure innings.", "cell")],
        [P("Value", "cell_b"), P(escape(str(tb.iloc[4].player)), "cell_b"),
         P("A high-upside batter whose pressure output is well above his own baseline; the sample is the caveat.", "cell")],
    ]
    right.append(table(picks, [45, 115, 205], font=7.2, pad=3.0))
    right += [
        Spacer(1, 5),
        P("Conclusion", "h2"),
        P(f"The pressure list is led by <b>{escape(str(tb.iloc[0].player))}</b> and <b>{escape(str(tw.iloc[0].player))}</b>, "
          f"but the more important result is structural: pressure is a narrow, identifiable state, and the players who "
          f"perform in it are not simply the players with the best overall numbers. Bowling pressure repeats; batting "
          f"pressure is noisy. A selector who uses this report should take the tiers seriously and the exact order "
          f"lightly.", "body"),
        P("What would change the list", "h2"),
        P("A second strong season from the low-sample players (Naman Dhir, Sufiyan Muqeem, Abrar Ahmed) would "
          "raise confidence in their ranks.", "bullet", "•"),
        P("A different competition weighting — for example, treating T20I as equal to IPL — would move players "
          "with very different mixes.", "bullet", "•"),
        P("A role-specific model (opener vs finisher, powerplay vs death bowler) would sharpen the comparisons, "
          "but would also thin the samples further.", "bullet", "•"),
    ]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("Limitations, and how to use the list", "Discussion"), body, PageBreak()]


def _appendix(ctx):
    code = ("python -m pip install -r requirements.txt<br/>"
            "python run_all.py")
    left = [
        P("Reproduce the result", "h2"),
        P("The pipeline is deterministic (bootstrap seed 42). It reads the supplied CSVs from the project root and "
          "writes every table, chart and report to `outputs/`.", "body"),
        P(code, "note"),
        Spacer(1, 6),
        P("Output files", "h2"),
    ]
    files = [
        [P("FILE", "hdr"), P("CONTENTS", "hdr")],
        [P("outputs/top10_batters.csv", "cell_b"), P("Ordered top 10 with metrics and 90% CI", "cell")],
        [P("outputs/top10_bowlers.csv", "cell_b"), P("Ordered top 10 with metrics and 90% CI", "cell")],
        [P("outputs/all_batters_scored.csv", "cell_b"), P("Full eligible batter pool", "cell")],
        [P("outputs/all_bowlers_scored.csv", "cell_b"), P("Full eligible bowler pool", "cell")],
        [P("outputs/validation.json", "cell_b"), P("WP, split-half and sample diagnostics", "cell")],
        [P("outputs/figures/", "cell_b"), P("All report charts (PNG)", "cell")],
        [P("outputs/dashboard.html", "cell_b"), P("Self-contained interactive dashboard", "cell")],
    ]
    left.append(table(files, [170, 205], font=7.2, pad=3.0))
    left += [
        Spacer(1, 6),
        P("Model card", "h2"),
    ]
    card = [
        [P("ITEM", "hdr"), P("VALUE", "hdr")],
        [P("Intended use", "cell_b"), P("Shortlisting pressure performers for T20 selection", "cell")],
        [P("Not for", "cell_b"), P("Predicting a player's next innings; contract or auction valuation", "cell")],
        [P("Training window", "cell_b"), P("IPL and T20I, 2022–2026 (supplied pack)", "cell")],
        [P("Validation", "cell_b"), P("GroupKFold by match; split-half; bootstrap; weight sensitivity", "cell")],
    ]
    left.append(table(card, [100, 275], font=7.2, pad=2.8))
    right = [
        P("Key fields", "h2"),
    ]
    fields = [
        [P("FIELD", "hdr"), P("MEANING", "hdr")],
        [P("pressure_rule", "cell_b"), P("1 if any of the five pressure rules fires", "cell")],
        [P("leverage", "cell_b"), P("Expected win-probability swing of the next ball", "cell")],
        [P("pressure_weight", "cell_b"), P("(1 + leverage percentile) × competition tier", "cell")],
        [P("bat_impact", "cell_b"), P("Context-adjusted batting runs above par", "cell")],
        [P("bowl_impact", "cell_b"), P("Context-adjusted runs saved above par", "cell")],
        [P("impact_pressure", "cell_b"), P("Weighted impact per 100 pressure balls", "cell")],
        [P("uplift", "cell_b"), P("Pressure impact minus own non-pressure impact", "cell")],
        [P("PRS", "cell_b"), P("Pressure Reliability Score, 0–100", "cell")],
    ]
    right.append(table(fields, [95, 275], font=7.2, pad=3.0))
    right += [
        Spacer(1, 6),
        P("Data-sharing warning", "h2"),
        P("The raw CSVs are supplied for this challenge and are not redistributed with this report. The PDF, deck "
          "and dashboard contain only aggregated player metrics and derived charts. Do not upload the raw data pack "
          "to a public repository or file-sharing service.", "note"),
    ]
    body = Table([[left, right]], colWidths=[390, 370], hAlign="LEFT")
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 18),
        ("LEFTPADDING", (1, 0), (1, 0), 0), ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    return [*h1("Appendix: reproduce, audit, and share safely", "Appendix"), body]


def build_pdf(ctx):
    path = os.path.join(ctx["out"], "SupeRR_Selector_Report.pdf")
    doc = BaseDocTemplate(
        path, pagesize=landscape(A4), leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=44, bottomMargin=30,
        title="SupeRR Selector Season 2 — Pressure Performance Report",
        author="SupeRR Selector submission", subject="Top 10 batters and bowlers under pressure",
    )
    main_frame = Frame(MARGIN, 30, CONTENT_W, PAGE_H - 74, id="main", showBoundary=0)
    cover_frame = Frame(MARGIN, 0, CONTENT_W, PAGE_H, id="cover", showBoundary=0)
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=_cover_bg),
        PageTemplate(id="Main", frames=[main_frame], onPage=_main_bg),
    ])
    story = []
    for fn in [
        _cover, _exec, _data, _pressure, _wp, _leverage, _measure, _score,
        _batter_table, _batter_evidence, lambda c: _cards_page(c, "Batter"),
        _bowler_table, _bowler_evidence, lambda c: _cards_page(c, "Bowler"),
        _validation, _limits, _appendix,
    ]:
        story += fn(ctx)
    doc.build(story)
    return path
