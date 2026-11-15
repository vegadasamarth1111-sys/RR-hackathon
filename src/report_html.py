"""Self-contained HTML dashboard for the SupeRR submission."""
from __future__ import annotations

import base64
import html
import os

import pandas as pd

from .narrative import f, pct


def _b64(path: str) -> str:
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def _img(path: str, alt: str, caption: str = "") -> str:
    if not os.path.exists(path):
        return ""
    cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return f'<figure><img src="data:image/png;base64,{_b64(path)}" alt="{html.escape(alt)}">{cap}</figure>'


def _csv_link(df: pd.DataFrame, name: str, label: str) -> str:
    data = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("ascii")
    return f'<a class="btn ghost" download="{name}" href="data:text/csv;base64,{data}">{label}</a>'


def _rank_rows(df: pd.DataFrame, role: str) -> str:
    out = []
    for i, (_, r) in enumerate(df.head(10).iterrows(), start=1):
        team = html.escape(str(r.get("team_label", "") or "—"))
        prs = float(r.PRS)
        third = f(r.sr_pressure) if role == "Batter" else f(r.economy_pressure, 2)
        out.append(
            f"<tr><td class='rank'>{i}</td><td><b>{html.escape(str(r.player))}</b>"
            f"<span class='team'>{team}</span></td>"
            f"<td><div class='score'><b>{prs:.1f}</b><span><i style='width:{prs:.1f}%'></i></span></div></td>"
            f"<td class='num'>{f(r.impact_pressure)}</td>"
            f"<td class='num'>{f(r.uplift, plus=True)}</td>"
            f"<td class='num'>{third}</td>"
            f"<td class='num'>{pct(r.dot_pct)}</td></tr>"
        )
    return "\n".join(out)


CSS = """
:root{--navy:#0B1F3A;--navy2:#132A4A;--pink:#E91E8C;--teal:#0E7C86;--gold:#D9A441;--grey:#6B7280;--mid:#8A94A6;--line:#DCE3EC;--light:#F4F6FA;--white:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--navy);font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.55}
a{color:inherit}.wrap{max-width:1180px;margin:0 auto;padding:0 28px}
.top{position:sticky;top:0;z-index:20;background:rgba(11,31,58,.96);backdrop-filter:blur(8px);color:#fff;border-bottom:1px solid rgba(255,255,255,.12)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;height:62px}
.brand{font-weight:800;letter-spacing:.12em;font-size:12px}.brand span{color:var(--pink)}
nav a{color:#C9D6E8;text-decoration:none;font-size:12px;margin-left:22px}nav a:hover{color:#fff}
.hero{background:var(--navy);color:#fff;padding:58px 0 46px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:520px;height:520px;border-radius:50%;right:-160px;top:-230px;background:rgba(233,30,140,.16)}
.hero:after{content:"";position:absolute;width:420px;height:420px;border-radius:50%;left:-220px;bottom:-260px;background:rgba(14,124,134,.16)}
.hero-grid{display:grid;grid-template-columns:1.25fr .75fr;gap:48px;position:relative;z-index:1}
.kicker{color:var(--pink);font-weight:800;letter-spacing:.16em;font-size:11px;margin:0 0 10px}
h1{font-size:52px;line-height:1.02;margin:0 0 16px;letter-spacing:-.03em}h1 em{color:var(--pink);font-style:normal}
.lead{font-size:17px;color:#C9D6E8;max-width:660px;margin:0 0 22px}
.badges{display:flex;gap:10px;flex-wrap:wrap}.badge{border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:7px 12px;font-size:11px;color:#DCE6F3}
.hero-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:22px}
.hero-card h3{margin:0 0 12px;font-size:11px;letter-spacing:.14em;color:var(--pink)}
.hero-list{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.hero-list div{font-size:13px}.hero-list b{display:block;font-size:15px;margin:2px 0 8px}
.hero-list small{color:#AFC0D6}
.section{padding:54px 0;border-bottom:1px solid var(--line);scroll-margin-top:74px}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:30px;margin-bottom:22px}
.section-head>div{flex:1;min-width:0}.section-head h2{font-size:30px;margin:0;letter-spacing:-.02em}.section-head p{margin:0;color:var(--grey);max-width:520px;font-size:14px}
.kicker2{color:var(--pink);font-weight:800;letter-spacing:.14em;font-size:10px;margin:0 0 5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 8px 28px rgba(11,31,58,.04)}
.card h3{margin:0 0 4px;font-size:18px}.card .sub{color:var(--grey);font-size:12px;margin:0 0 12px}
table{width:100%;border-collapse:collapse;font-size:12px}th{text-align:left;color:var(--mid);font-size:9px;letter-spacing:.1em;text-transform:uppercase;padding:7px 6px;border-bottom:1px solid var(--line)}
td{padding:7px 6px;border-bottom:1px solid #EEF2F7;vertical-align:middle}.rank{color:var(--mid);font-weight:700;width:24px}.card th:nth-child(n+3){text-align:right}
.team{display:block;color:var(--grey);font-size:10px;margin-top:1px}.score{display:flex;align-items:center;gap:7px;min-width:86px}.score span{height:4px;background:#EEF2F7;border-radius:4px;flex:1;overflow:hidden}.score i{display:block;height:100%;background:var(--pink);border-radius:4px}
.metric{color:var(--grey);font-size:10px;white-space:nowrap}.num{text-align:right;font-size:11px;white-space:nowrap}
.note{font-size:11px;color:var(--grey);margin:12px 0 0}.note b{color:var(--navy)}
.empty td{text-align:center;color:var(--mid);padding:18px 6px;font-size:11px}
.btn{display:inline-block;background:var(--pink);color:#fff;text-decoration:none;border-radius:999px;padding:9px 14px;font-size:11px;font-weight:700;border:0;cursor:pointer}
.btn.ghost{background:transparent;color:var(--navy);border:1px solid var(--line)}.btn.ghost:hover{border-color:var(--pink);color:var(--pink)}
.toolbar{display:flex;gap:10px;align-items:center;justify-content:flex-end;margin-bottom:10px}
input[type=search]{border:1px solid var(--line);border-radius:999px;padding:9px 14px;font:inherit;font-size:12px;outline:none;min-width:220px}
input[type=search]:focus{border-color:var(--pink)}
.stat{background:var(--light);border-radius:12px;padding:14px 15px;border-left:4px solid var(--pink)}.stat b{display:block;font-size:26px;line-height:1.1}.stat span{font-size:10px;color:var(--grey);text-transform:uppercase;letter-spacing:.1em;font-weight:700}
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.step{background:var(--navy);color:#fff;border-radius:12px;padding:15px;min-height:116px}.step b{display:block;color:var(--pink);font-size:10px;letter-spacing:.1em;margin-bottom:6px}.step span{font-size:12px;color:#DCE6F3}
.rules{display:grid;grid-template-columns:1fr 1fr;gap:12px}.rule{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#fff}.rule b{display:block;font-size:14px;margin-bottom:3px}.rule span{color:var(--grey);font-size:12px}
.gallery{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px}figure img{width:100%;height:auto;display:block;border-radius:8px}figcaption{font-size:10px;color:var(--grey);padding:8px 2px 2px}
.callout{background:var(--light);border-left:4px solid var(--teal);border-radius:0 12px 12px 0;padding:16px 18px;font-size:13px;color:var(--navy)}
.callout.pink{border-left-color:var(--pink)}
.pill{display:inline-block;background:var(--light);border-radius:999px;padding:4px 9px;font-size:10px;color:var(--grey);margin:2px 4px 2px 0}
footer{background:var(--navy);color:#AFC0D6;padding:28px 0;font-size:11px}footer b{color:#fff}
@media(max-width:900px){.hero-grid,.grid2,.grid3,.gallery,.rules{grid-template-columns:1fr}.steps{grid-template-columns:1fr 1fr}h1{font-size:38px}.section-head{display:block}.toolbar{justify-content:flex-start;margin-top:10px}.metric{white-space:normal}}
@media(max-width:640px){.top .wrap{height:auto;min-height:56px;padding:8px 18px 6px;flex-wrap:wrap;gap:3px}.brand{font-size:10px;letter-spacing:.08em}nav{display:flex;width:100%;gap:14px;overflow-x:auto;padding-bottom:2px}nav a{margin-left:0;font-size:11px;white-space:nowrap}.section{scroll-margin-top:100px}.hero{padding:38px 0 34px}h1{font-size:34px}.lead{font-size:15px}.toolbar{flex-wrap:wrap}input[type=search]{flex:1 1 100%;min-width:0}.btn{flex:1 1 45%;text-align:center}table{font-size:11px}th{font-size:8px;padding:6px 3px}td{padding:6px 3px}.rank{width:18px}.score{min-width:70px;gap:4px}.team{font-size:9px}th:last-child,td:last-child{display:none}}
"""


def build_dashboard(ctx):
    s = ctx["summary"]
    tb, tw = ctx["top_bat"], ctx["top_bowl"]
    sb, sw = ctx["split"]["Batter"], ctx["split"]["Bowler"]
    fig = ctx["figdir"]

    def img(name, alt, cap):
        return _img(os.path.join(fig, name), alt, cap)

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SupeRR Selector · Pressure Performance Dashboard</title><style>{CSS}</style></head>
<body>
<header class="top"><div class="wrap"><div class="brand">SUPERR <span>SELECTOR</span> · SEASON 2</div>
<nav><a href="#rankings">Rankings</a><a href="#method">Method</a><a href="#evidence">Evidence</a><a href="#reliability">Reliability</a><a href="#limits">Limits</a></nav></div></header>
<main>
<section class="hero"><div class="wrap hero-grid">
<div><p class="kicker">ROUND 1 · PRESSURE PERFORMANCE</p>
<h1>When the game gets loud,<br><em>who holds up?</em></h1>
<p class="lead">A reproducible pressure-performance model for T20 batting and bowling, built from the supplied IPL and T20I ball-by-ball data. Not a reputation list. Not an overall-impact list. A pressure list.</p>
<div class="badges"><span class="badge">{s['deliveries']:,} deliveries</span><span class="badge">{s['matches']} matches</span><span class="badge">{s['pressure_share']:.1%} pressure</span><span class="badge">{s['eligible_batters']} batters · {s['eligible_bowlers']} bowlers eligible</span></div></div>
<div class="hero-card"><h3>THE TOP 3</h3><div class="hero-list">
<div><small>BATTERS</small><b>1. {html.escape(str(tb.iloc[0].player))}</b><small>{tb.iloc[0].PRS:.1f} PRS</small><br><small>2. {html.escape(str(tb.iloc[1].player))}</small><br><small>3. {html.escape(str(tb.iloc[2].player))}</small></div>
<div><small>BOWLERS</small><b>1. {html.escape(str(tw.iloc[0].player))}</b><small>{tw.iloc[0].PRS:.1f} PRS</small><br><small>2. {html.escape(str(tw.iloc[1].player))}</small><br><small>3. {html.escape(str(tw.iloc[2].player))}</small></div>
</div></div></div></section>

<section class="section" id="rankings"><div class="wrap">
<div class="section-head"><div><p class="kicker2">THE ANSWER</p><h2>Two ordered top 10s</h2></div><p>Ranked by the Pressure Reliability Score (PRS). The top three are shaded. The rest is best read as a tier: adjacent ranks often overlap within model uncertainty.</p></div>
<div class="toolbar"><input id="search" type="search" placeholder="Filter a player…">{_csv_link(tb, 'top10_batters.csv', 'Download batter CSV')} {_csv_link(tw, 'top10_bowlers.csv', 'Download bowler CSV')}</div>
<div class="grid2">
<div class="card"><h3>Top 10 batters</h3><p class="sub">Impact · uplift · SR · dot%</p><table><thead><tr><th>#</th><th>Player</th><th>PRS</th><th>Imp</th><th>Upl</th><th>SR</th><th>Dot</th></tr></thead><tbody>{_rank_rows(tb, 'Batter')}<tr class="empty" hidden><td colspan="7">No batter matches this filter.</td></tr></tbody></table></div>
<div class="card"><h3>Top 10 bowlers</h3><p class="sub">Impact · uplift · economy · dot%</p><table><thead><tr><th>#</th><th>Player</th><th>PRS</th><th>Imp</th><th>Upl</th><th>Econ</th><th>Dot</th></tr></thead><tbody>{_rank_rows(tw, 'Bowler')}<tr class="empty" hidden><td colspan="7">No bowler matches this filter.</td></tr></tbody></table></div>
</div>
<p class="note"><b>PRS</b> is a 0–100 percentile composite. Impact is context-adjusted runs (batters) or runs saved (bowlers) per 100 pressure balls. Uplift is the change from the player's own non-pressure baseline.</p>
</div></section>

<section class="section" id="method"><div class="wrap">
<div class="section-head"><div><p class="kicker2">METHOD</p><h2>Five pressure rules. One score.</h2></div><p>Pressure is a match state, not a reputation and not simply “the death overs”. The rules are observable in real time and auditable ball by ball.</p></div>
<div class="rules">
<div class="rule"><b>1. Chase pressure</b><span>2nd innings, after over 4, RRR ≥ 10, ≤ 5 wickets in hand.</span></div>
<div class="rule"><b>2. Death pressure</b><span>Overs 16–20, within 15 runs of par.</span></div>
<div class="rule"><b>3. Collapse pressure</b><span>4+ down and behind the game, or 6+ down in the last five overs.</span></div>
<div class="rule"><b>4. Knockout pressure</b><span>Knockout match, overs 10–20, within 25 runs.</span></div>
<div class="rule"><b>5. Early collapse</b><span>3+ wickets down in the powerplay and behind the game.</span></div>
<div class="rule" style="background:var(--light)"><b>Leverage weight</b><span>Pressure balls are weighted by the expected win-probability swing of the next ball, then by competition tier.</span></div>
</div>
<div style="height:18px"></div>
<div class="steps">
<div class="step"><b>1. STATE</b><span>Score, wickets, balls, target, RRR, phase, stakes.</span></div>
<div class="step"><b>2. PRESSURE</b><span>Five rules plus leverage from the win-probability model.</span></div>
<div class="step"><b>3. IMPACT</b><span>Runs above par for batters; runs saved for bowlers.</span></div>
<div class="step"><b>4. UPLIFT</b><span>Pressure impact minus the player's own non-pressure baseline.</span></div>
<div class="step"><b>5. PRS</b><span>Output 35/40, uplift 20/15, control 20, consistency 15, sample 10.</span></div>
</div>
<div style="height:18px"></div>
<div class="callout"><b>PRS = 0.35 Output + 0.20 Uplift + 0.20 Control + 0.15 Consistency + 0.10 Sample</b> for batters; bowlers use 0.40 / 0.15 / 0.20 / 0.15 / 0.10. Impact and uplift are shrunk by n/(n+80). Every component is a percentile rank in the eligible pool.</div>
</div></section>

<section class="section" id="evidence"><div class="wrap">
<div class="section-head"><div><p class="kicker2">EVIDENCE</p><h2>What the charts show</h2></div><p>The lists are not just the best overall players. Context changes the answer.</p></div>
<div class="gallery">
{img('pressure_share.png', 'Pressure share by phase', 'Pressure is concentrated in chases and death overs — but the two are not the same.')}
{img('leverage.png', 'Leverage distribution', 'Leverage separates ordinary death overs from genuine nail-biters.')}
{img('bat_baseline.png', 'Batter pressure vs baseline', 'Above the diagonal = better under pressure than in non-pressure balls.')}
{img('bowl_baseline.png', 'Bowler pressure vs baseline', 'Above the diagonal = better under pressure than in non-pressure balls.')}
{img('calibration.png', 'Win probability calibration', 'Out-of-fold calibration, 5-fold GroupKFold by match.')}
{img('split_half.png', 'Split-half reliability', 'Batting pressure is noisy; bowling pressure is moderately repeatable.')}
</div>
</div></section>

<section class="section" id="reliability"><div class="wrap">
<div class="section-head"><div><p class="kicker2">RELIABILITY</p><h2>Does the ranking survive scrutiny?</h2></div><p>We checked repeatability, weight sensitivity, calibration and bootstrap uncertainty.</p></div>
<div class="grid3">
<div class="stat"><b>{sb['rho']:.2f}</b><span>batter split-half rho · p={sb['p']:.2f} · n={sb['n']}</span></div>
<div class="stat" style="border-left-color:var(--teal)"><b>{sw['rho']:.2f}</b><span>bowler split-half rho · p={sw['p']:.3f} · n={sw['n']}</span></div>
<div class="stat" style="border-left-color:var(--gold)"><b>8–10 of 10</b><span>top-10 names retained across weightings</span></div>
</div>
<div style="height:18px"></div>
<div class="grid2">
{img('sensitivity.png', 'Weight sensitivity', 'Membership is stable under plausible weight changes; the exact order is less stable.')}
{img('boot_bat.png', 'Batter impact uncertainty', 'Bootstrap intervals overlap across the middle of the batting list: adjacent ranks are a tier, not a strict order.')}
</div>
<div style="height:18px"></div>
<div class="callout pink"><b>The honest read:</b> pressure bowling repeats better than pressure batting. Batting pressure is noisy, so the batting list should be treated as tiers rather than a precise 1–10 verdict. The 90% bootstrap intervals are in the PDF tables.</div>
</div></section>

<section class="section" id="limits"><div class="wrap">
<div class="section-head"><div><p class="kicker2">LIMITS</p><h2>What this model does not know</h2></div><p>A selector should use the list as a shortlist, not a verdict.</p></div>
<div class="grid2">
<div class="card"><h3>Limitations</h3><p class="sub">Read before using the ranking</p>
<ul>
<li>No age or date of birth in the pack — no youngest-player analysis.</li>
<li>Pressure is observational; we do not measure temperament.</li>
<li>No ball-tracking, field placement or catch difficulty.</li>
<li>Role and team context are only partly observed.</li>
<li>Competition weights are a judgment call (IPL 1.00, T20I 0.90, other T20 0.75).</li>
<li>This is a historical ranking, not a forecast.</li>
</ul></div>
<div class="card"><h3>How to use it</h3><p class="sub">A practical selection memo</p>
<p>Use the top tier as a shortlist. Pair the pressure profile with role fit, availability, recent form and the balance of the XI. The model is strongest when it challenges reputation, not when it replaces scouting.</p>
<p class="pill">IPL 2022–2026</p><p class="pill">T20I 2022–2026</p><p class="pill">Other T20 weighted 0.75</p><p class="pill">Bootstrap seed 42</p>
<p class="note"><b>Data-sharing warning:</b> the raw CSVs are supplied for this challenge and are not redistributed. This dashboard contains only aggregated metrics and derived charts.</p>
</div>
</div>
</div></section>
</main>
<footer><div class="wrap"><b>SupeRR Selector · Season 2 · Round 1</b> — methodology dashboard. Rankings are model estimates, not guarantees. Built from the supplied data pack.</div></footer>
<script>
const q=document.getElementById('search');
if(q){{q.addEventListener('input',()=>{{const v=q.value.trim().toLowerCase();document.querySelectorAll('table').forEach(t=>{{const rows=[...t.querySelectorAll('tbody tr:not(.empty)')];let n=0;rows.forEach(tr=>{{const ok=tr.innerText.toLowerCase().includes(v);tr.style.display=ok?'':'none';if(ok)n++;}});const empty=t.querySelector('tr.empty');if(empty)empty.hidden=n>0;}});}});}}
</script>
</body></html>"""
    path = os.path.join(ctx["out"], "dashboard.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    return path
