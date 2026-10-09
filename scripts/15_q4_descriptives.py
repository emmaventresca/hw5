#!/usr/bin/env python3
"""
15_q4_descriptives.py — Question 4: descriptive table for the predictors, 2022.

Mean, standard deviation (sample, ddof=1) and N for each ACS predictor, over the
Question 3 analysis sample (counties in an OEWS metropolitan area), year 2022.

Writes: output/q4_descriptives_2022.csv  and  docs/q4_descriptives_2022.md
"""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
p = pd.read_csv(ROOT / "data/processed/county_panel_2015_2022.csv",
                dtype={"county_fips": str, "oews_area": str})
d = p[p.year == 2022]

PREDICTORS = [
    ("per_capita_income", "Per capita income ($)"),
    ("total_population", "Total population"),
    ("own_children_under6", "Own children under 6"),
    ("own_children_under6_all_parents_lf", "Own children <6, all resident parents in LF"),
    ("median_gross_rent", "Median gross rent ($/mo)"),
    ("share_women_25plus_bachelors_plus", "Share women 25+ with bachelor's+"),
    ("share_women_16_64_ft_yr", "Share women 16-64 full-time year-round"),
    ("share_kids_under6", "Share of population under 6"),
    ("share_kids_under6_need_care", "Share kids under 6 needing care"),
]

rows = []
for col, label in PREDICTORS:
    s = d[col].dropna()
    rows.append({"variable": col, "label": label, "n": int(s.size),
                 "mean": s.mean(), "sd": s.std(ddof=1)})

# Outcome, shown for reference
w = d["a_mean"].dropna()
out = pd.DataFrame(rows)
out.to_csv(ROOT / "output/q4_descriptives_2022.csv", index=False)

def fmt(v, col):
    if "share" in col:
        return f"{v:,.4f}"
    return f"{v:,.1f}"

lines = ["# Question 4 — Descriptive statistics, 2022",
         "",
         "Sample: counties in an OEWS metropolitan area (`oews_area` begins `00`), "
         "year 2022.",
         "N differs across rows only where ACS suppressed a value.",
         "",
         "| Predictor | Mean | Std. dev. | N |",
         "|---|---:|---:|---:|"]
for r in rows:
    lines.append(f"| {r['label']} | {fmt(r['mean'], r['variable'])} | "
                 f"{fmt(r['sd'], r['variable'])} | {r['n']:,} |")
lines += ["",
          "**Outcome variable, for reference**",
          "",
          "| Variable | Mean | Std. dev. | N |",
          "|---|---:|---:|---:|",
          f"| Childcare worker mean annual wage ($, nominal) | {w.mean():,.1f} | "
          f"{w.std(ddof=1):,.1f} | {w.size:,} |"]
(ROOT / "docs/q4_descriptives_2022.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
