"""Short, data-grounded player narratives used across the report, deck and dashboard."""
from __future__ import annotations

import math


def _ok(v) -> bool:
    try:
        return v is not None and not (isinstance(v, float) and math.isnan(v))
    except Exception:
        return True


def f(v, d: int = 1, plus: bool = False, dash: str = "—") -> str:
    if not _ok(v):
        return dash
    return f"{v:+.{d}f}" if plus else f"{v:.{d}f}"


def pct(v, d: int = 0) -> str:
    if not _ok(v):
        return "—"
    return f"{v:.{d}f}%"


BAT_ANGLE = {
    "Sai Sudharsan": "The most complete profile in the pool: top-decile output, a large uplift on his own baseline and the best dot-ball control in the top 10.",
    "Shreyas Iyer": "A control-first pressure profile: excellent dot-ball avoidance and a healthy uplift, rather than pure boundary power.",
    "Suryakumar Yadav": "The volume leader: nearly 800 pressure balls across 44 pressure innings, with elite output and a positive impact in most of them.",
    "Jos Buttler": "Fast scoring with unusual consistency: 92% of his qualifying pressure innings finished with positive impact.",
    "Tristan Stubbs": "One of the biggest pressure-over-baseline jumps in the pool, built on boundary hitting rather than dot-ball avoidance.",
    "Naman Dhir": "The highest pressure impact and strike rate in the pool. The ball-striking is real; the sample is shorter than the names around him.",
    "Liam Livingstone": "A high-upside boundary profile with strong output and a positive impact in five of every six pressure innings.",
    "Shashank Singh": "A finisher signal: a big lift over his own baseline and strong boundary output in a mid-sized sample.",
    "David Miller": "A pure finisher signal: the biggest uplift in the pool, with more dot balls and a wider confidence interval.",
    "Shubman Gill": "Elite control and a solid uplift. He keeps the innings moving when others might panic; the boundary ceiling is lower.",
}

BAT_RISK = {
    "Sai Sudharsan": "Pressure batting is still noisy; 362 pressure balls make his exact rank less certain than his place in the top tier.",
    "Shreyas Iyer": "Boundary rate is mid-table; against elite death bowling he may need a partner to carry the tempo.",
    "Suryakumar Yadav": "The only real question is role: much of the sample comes from a free-scoring top-order brief.",
    "Jos Buttler": "A 26% dot rate is the trade-off for his boundary intent; the innings can start slowly.",
    "Tristan Stubbs": "A 26% dot rate can stall an innings. The ranking leans on boundary clusters and a strong uplift.",
    "Naman Dhir": "260 pressure balls is a thin base for a top-six claim. Treat him as a high-upside pick, not a certainty.",
    "Liam Livingstone": "A 33% dot rate is the highest in the top 10; the innings can stall between boundary clusters.",
    "Shashank Singh": "The 90% interval is the widest in the top 10; his rank is more uncertain than the names above him.",
    "David Miller": "A 29% dot rate and a lower pressure impact make him more volatile than the top six.",
    "Shubman Gill": "A 20% boundary rate limits ceiling in a 12-an-over chase; he needs someone else to take down the best bowler.",
}

BOWL_ANGLE = {
    "Sunil Narine": "The benchmark: elite pressure output and control, with a positive impact in 83% of his pressure innings.",
    "Akeal Hosein": "A control monster: 39% dots, a 6.25 pressure economy and a huge uplift on his own baseline.",
    "Mitchell Santner": "The volume-and-control pick: 535 pressure balls, 40% dots and a 6.64 pressure economy.",
    "Sufiyan Muqeem": "The highest pressure impact per 100 balls in the pool, with 56% dots and a 4.81 economy.",
    "Abrar Ahmed": "Wicket-taking and dot-ball pressure in one package; his 5.89 pressure economy is elite.",
    "Rashid Khan": "The safest high-volume profile: 1,089 pressure balls, 38% dots and a long track record.",
    "Varun Chakravarthy": "A high-volume mystery spinner: 905 pressure balls, 42% dots and a wicket threat that survives a higher economy.",
    "Mohammad Nawaz": "A balanced control profile with a strong uplift and a 6.31 pressure economy.",
    "Kuldeep Yadav": "A high-volume wicket threat whose value comes from control and breakthroughs rather than a low economy.",
    "Jasprit Bumrah": "A high-volume death specialist: 39% dots and 42 pressure wickets, with output that holds up in the toughest overs.",
}

BOWL_RISK = {
    "Sunil Narine": "Pressure bowling repeats better than batting, but the exact gap to rank 2 is within model uncertainty.",
    "Akeal Hosein": "A 10% boundary rate is higher than the other top-three bowlers; one bad over can swing a spell.",
    "Mitchell Santner": "Wicket rate is modest; his value is control, so he needs catchers and a good field.",
    "Sufiyan Muqeem": "221 pressure balls is the thinnest sample in the top 10. The upside is clear; the certainty is not.",
    "Abrar Ahmed": "276 pressure balls is a shorter sample than the top three; the confidence interval is wider.",
    "Rashid Khan": "A 13% boundary rate is the highest in the top group, though the volume is unmatched.",
    "Varun Chakravarthy": "A 15% boundary rate and a 7.60 pressure economy make him more volatile than the top six.",
    "Mohammad Nawaz": "214 pressure balls is a thin sample; the ranking leans on economy and dots rather than wickets.",
    "Kuldeep Yadav": "A 7.73 pressure economy is mid-table; the ranking is driven by wickets and volume.",
    "Jasprit Bumrah": "His pressure impact is barely above his own non-pressure baseline; reputation is doing some of the work here.",
}


def batter_narrative(r) -> tuple[str, str]:
    name = str(r.get("player", ""))
    angle = BAT_ANGLE.get(name, "A strong pressure profile with a clear output and control signal.")
    why = (
        f"{angle} {f(r.get('impact_pressure'))} context-adjusted runs per 100 pressure balls "
        f"({f(r.get('uplift'), plus=True)} vs his own non-pressure baseline), "
        f"striking at {f(r.get('sr_pressure'))} with {pct(r.get('dot_pct'))} dots across "
        f"{int(r.get('balls_pressure', 0))} pressure balls."
    )
    risk = BAT_RISK.get(name)
    if not risk:
        bp = r.get("balls_pressure", 0)
        if bp < 300:
            risk = f"Only {int(bp)} pressure balls; the 90% interval is wide."
        elif r.get("dot_pct", 0) > 27:
            risk = f"A {pct(r.get('dot_pct'))} dot rate can stall a chase."
        elif r.get("boundary_pct", 0) < 20:
            risk = f"A {pct(r.get('boundary_pct'))} boundary rate limits the ceiling."
        else:
            risk = "Pressure batting is noisy; treat the exact rank as a band, not a verdict."
    return why, risk


def bowler_narrative(r) -> tuple[str, str]:
    name = str(r.get("player", ""))
    angle = BOWL_ANGLE.get(name, "A strong pressure profile built on control and wicket threat.")
    why = (
        f"{angle} {f(r.get('impact_pressure'))} context-adjusted runs saved per 100 pressure balls "
        f"({f(r.get('uplift'), plus=True)} vs his own baseline), a {f(r.get('economy_pressure'), 2)} "
        f"pressure economy, {pct(r.get('dot_pct'))} dots and {pct(r.get('boundary_pct'))} boundaries "
        f"across {int(r.get('balls_pressure', 0))} pressure balls."
    )
    risk = BOWL_RISK.get(name)
    if not risk:
        bp = r.get("balls_pressure", 0)
        if bp < 300:
            risk = f"Only {int(bp)} pressure balls; the 90% interval is wide."
        elif r.get("boundary_pct", 0) > 14:
            risk = f"A {pct(r.get('boundary_pct'))} boundary rate means one bad over can swing a spell."
        elif r.get("wicket_rate", 0) < 6.5:
            risk = f"A {pct(r.get('wicket_rate'), 1)} wicket rate means the value is control, not breakthroughs."
        else:
            risk = "Pressure bowling repeats better than batting, but the exact order is still uncertain."
    return why, risk
