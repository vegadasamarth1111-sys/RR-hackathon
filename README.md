# SupeRR Selector — Season 2, Round 1

**Pressure performance in T20 cricket.** This repository contains a reproducible, transparent model for ranking batters and bowlers under pressure from the supplied IPL and T20I ball-by-ball data.

The submission answers the official brief with:

- an ordered **top 10 batters** under pressure;
- an ordered **top 10 bowlers** under pressure;
- a methodology report, a presentation deck and a self-contained dashboard.

No raw data is redistributed in the reports or generated artefacts.

---

## Headline results

| # | Batter | PRS | # | Bowler | PRS |
|---:|---|---:|---:|---|---:|
| 1 | Sai Sudharsan | 88.8 | 1 | Sunil Narine | 96.5 |
| 2 | Shreyas Iyer | 87.3 | 2 | Akeal Hosein | 93.0 |
| 3 | Suryakumar Yadav | 84.4 | 3 | Mitchell Santner | 92.8 |
| 4 | Jos Buttler | 83.7 | 4 | Sufiyan Muqeem | 91.6 |
| 5 | Tristan Stubbs | 83.3 | 5 | Abrar Ahmed | 90.3 |
| 6 | Naman Dhir | 83.0 | 6 | Rashid Khan | 89.8 |
| 7 | Liam Livingstone | 78.7 | 7 | Varun Chakravarthy | 85.4 |
| 8 | Shashank Singh | 78.4 | 8 | Mohammad Nawaz | 85.0 |
| 9 | David Miller | 77.9 | 9 | Kuldeep Yadav | 83.8 |
| 10 | Shubman Gill | 76.3 | 10 | Jasprit Bumrah | 83.7 |

PRS is a 0–100 percentile composite. Adjacent ranks should be read as a tier, not a precise order.

---

## Method in one page

### 1. Define pressure from observable match state

A delivery is a pressure ball if any of five rules fires:

1. **Chase pressure:** 2nd innings, after over 4, required run rate ≥ 10, ≤ 5 wickets in hand.
2. **Death pressure:** overs 16–20, within 15 runs of par.
3. **Collapse pressure:** 4+ wickets down and behind the game, or 6+ down in the last five overs.
4. **Knockout pressure:** knockout match, overs 10–20, within 25 runs.
5. **Early collapse:** 3+ wickets down in the powerplay and behind the game.

A ball can satisfy several rules. The flags are kept separately for diagnostics, and the union is used for aggregation.

### 2. Weight pressure balls by leverage

A win-probability model is fitted out-of-fold with `GroupKFold` by match. Leverage is the expected absolute win-probability swing of the next ball. Pressure balls are weighted by:

```text
pressure_weight = (1 + leverage percentile) × competition tier
```

Competition tiers: IPL = 1.00, T20I = 0.90, other T20 = 0.75.

### 3. Measure context-adjusted impact

For batters:

```text
bat_impact = runs − expected runs for phase / bowler type / competition
             − 1.5 × (out − expected out)
```

For bowlers:

```text
bowl_impact = expected runs − runs conceded
              + 2.0 × (wicket − expected wicket)
```

Impact is expressed per 100 pressure balls. Output and uplift are shrunk by `n / (n + 80)` so small samples cannot dominate.

### 4. Build the Pressure Reliability Score

```text
Batters:  PRS = 0.35 Output + 0.20 Uplift + 0.20 Control + 0.15 Consistency + 0.10 Sample
Bowlers:  PRS = 0.40 Output + 0.15 Uplift + 0.20 Control + 0.15 Consistency + 0.10 Sample
```

Every component is a percentile rank inside the eligible pool. Consistency is shrunk toward 50% with a five-innings prior.

Eligibility:

| Criterion | Batter | Bowler |
|---|---:|---:|
| Total balls | ≥ 500 | ≥ 500 |
| Pressure balls | ≥ 80 | ≥ 100 |
| Pressure innings (≥ 6 balls) | ≥ 12 | ≥ 10 |
| Total innings | ≥ 15 | ≥ 12 |

### 5. Test the result

- Split-half reliability: batter ρ = 0.09 (p = 0.57, n = 42); bowler ρ = 0.37 (p = 0.003, n = 66).
- Top-10 overlap across five plausible weightings: 8–10/10 batters and 8–10/10 bowlers.
- 90% innings-bootstrap intervals on impact are reported with the top-10 tables.
- Win-probability validation: innings 1 AUC ≈ 0.69, innings 2 AUC ≈ 0.90.

The honest conclusion: **pressure bowling repeats better than pressure batting.** Treat the batting list as tiers, and the exact order lightly.

---

## Reproduce the result

### Requirements

- Python 3.11+
- The six supplied CSVs in the project root:
  - `6af855c0e8386_ball_by_ball.csv` (refreshed pack; `ball_by_ball.csv` is used as a fallback)
  - `matches.csv`
  - `competitions.csv`
  - `competition_team_player_mapping.csv`
  - `playing_eleven.csv`
  - `teams.csv`

### Run

```bash
python -m pip install -r requirements.txt
python run_all.py
```

The pipeline is deterministic (bootstrap seed 42). It writes every table, chart and report to `outputs/`.

The refreshed ball-by-ball pack stores the actual number of extra runs per delivery (`extras1_runs` / `extras_2_runs`), so the pipeline uses those values directly instead of reconstructing extras. It also corrects the `AHT Donald` name to `Aneurin Donald`. Re-running on the refreshed pack updates the pressure flags, rankings, validation metrics and every generated artefact.

Optional: on Windows with PowerPoint installed, export deck slides to PNG for review:

```bash
python analysis/export_pptx.py
```

---

## Outputs

| File | Contents |
|---|---|
| `outputs/SupeRR_Selector_Report.pdf` | Methodology report (landscape A4) |
| `outputs/SupeRR_Selector_Deck.pptx` | 9-slide presentation deck |
| `outputs/dashboard.html` | Self-contained interactive dashboard |
| `outputs/top10_batters.csv` | Ordered top 10 with metrics and 90% CI |
| `outputs/top10_bowlers.csv` | Ordered top 10 with metrics and 90% CI |
| `outputs/all_batters_scored.csv` | Full eligible batter pool |
| `outputs/all_bowlers_scored.csv` | Full eligible bowler pool |
| `outputs/validation.json` | WP, split-half and sample diagnostics |
| `outputs/figures/` | All report charts (PNG) |

The dashboard embeds only aggregated player metrics and derived charts as base64 images. It does not embed the raw ball-by-ball data.

---

## Repository layout

```text
run_all.py                  end-to-end orchestrator
src/prep.py                 data loading, ball-state construction, pressure rules
src/model.py                win-probability models, leverage, impact, validation
src/metrics.py              aggregation, PRS scoring, eligibility, bootstrap, sensitivity
src/charts.py               report and dashboard charts
src/narrative.py            player “why / risk” narratives
src/report_pdf.py           PDF report builder
src/report_pptx.py          PowerPoint deck builder
src/report_html.py          self-contained dashboard builder
src/report.py               report entry points
outputs/                    final deliverables and figures
analysis/                   QA helpers and review previews (not required to reproduce)
```

---

## Data handling and sharing

The raw CSVs were supplied for this challenge. They are **not** redistributed with this submission and are excluded by `.gitignore`. The PDF, deck and dashboard contain only aggregated player metrics and derived charts.

Do not upload the raw data pack to a public repository or file-sharing service.

---

## Limitations

- No age or date of birth is present, so no youngest-player analysis is possible.
- Pressure is inferred from match state; temperament, heart rate and self-report are not measured.
- There is no ball-tracking, field-placement or catch-difficulty data in the pack.
- Role and team context are only partly observed. An opener and a finisher face different pressure tasks.
- Competition weights are a judgment call.
- This is a historical pressure ranking, not a forecast of the next innings.

The model is strongest when it is used to challenge reputation and structure a shortlist, not to replace scouting.
