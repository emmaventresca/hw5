#!/usr/bin/env python3
"""
19_build_writeup.py — assemble the write-up: tables, numbers and figures only.

Every value is recomputed from the processed data files at build time, so the
document cannot drift from the data. Produces:
    docs/WRITEUP.md
    docs/WRITEUP.html   (self-contained; figure embedded as base64)
"""
import base64
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
V = "a_mean_real2022"

p = pd.read_csv(PROC / "county_panel_real_2015_2022.csv",
                dtype={"county_fips": str, "oews_area": str})
acs = pd.read_csv(PROC / "acs_county_2015_2022.csv", dtype={"county_fips": str})
oews = pd.read_csv(PROC / "oews_childcare_2015_2022.csv", dtype={"oews_area": str})
cpi = pd.read_csv(PROC / "cpi_u_annual.csv").set_index("year")["cpi_u"]
defl = cpi[2022] / cpi

L = []
A = L.append

A("# Childcare siting — results")
A("")
A("Emma Ventresca · 2026-10-08")
A("")

# ---------------------------------------------------------------- Q1
A("## Question 1 — ACS 5-year explanatory variables, county level, 2015–2022")
A("")
A("Process completed. See AI output notes below.")
A("")

A("## Question 2 — OEWS childcare-worker wages, SOC 39-9011, area level, 2015–2022")
A("")
A("Process completed. See AI output notes below.")
A("")

# ---------------------------------------------------------------- Q3
A("## Question 3 — Merge and cleaning")
A("")
A("Process completed. See AI output notes below.")
A("")
g = p.groupby("year").agg(rows=("a_mean", "size"),
                          missing=("a_mean", lambda s: int(s.isna().sum())))
g["pct"] = (g.missing / g.rows * 100).round(2)
A("| Year | Rows | Missing wage | % missing |")
A("|---|---:|---:|---:|")
for y, r in g.iterrows():
    A(f"| {y} | {int(r.rows):,} | {int(r.missing)} | {r.pct:.2f} |")
A(f"| **Total** | **{len(p):,}** | **{int(p.a_mean.isna().sum())}** | "
  f"**{p.a_mean.isna().sum()/len(p)*100:.2f}** |")
A("")

# ---------------------------------------------------------------- Q4
A("## Question 4 — Descriptive statistics, 2022")
A("")
A("| Predictor | Mean | Std. dev. | N |")
A("|---|---:|---:|---:|")
d22 = p[p.year == 2022]
for col, lab in [
    ("per_capita_income", "Per capita income ($)"),
    ("total_population", "Total population"),
    ("own_children_under6", "Own children under 6"),
    ("own_children_under6_all_parents_lf", "Own children <6, all parents in LF"),
    ("median_gross_rent", "Median gross rent ($/mo)"),
    ("share_women_25plus_bachelors_plus", "Share women 25+ bachelor's+"),
    ("share_women_16_64_ft_yr", "Share women 16–64 FT year-round"),
    ("share_kids_under6", "Share of population under 6"),
    ("share_kids_under6_need_care", "Share kids under 6 needing care"),
]:
    s = d22[col].dropna()
    f = "{:,.4f}" if "share" in col else "{:,.1f}"
    A(f"| {lab} | {f.format(s.mean())} | {f.format(s.std(ddof=1))} | {s.size:,} |")
w = d22.a_mean.dropna()
A(f"| Childcare worker mean annual wage ($) | {w.mean():,.1f} | "
  f"{w.std(ddof=1):,.1f} | {w.size:,} |")
A("")

# ---------------------------------------------------------------- Q5
A("## Question 5 — Constant 2022 dollars (CPI-U)")
A("")
A("`real_2022 = nominal_t × (CPI_2022 / CPI_t)`; CPI-U series `CUUR0000SA0`.")
A("")
gy = p.groupby("year").agg(wn=("a_mean", "mean"), wr=(V, "mean"),
                           rn=("median_gross_rent", "mean"),
                           rr=("median_gross_rent_real2022", "mean"))
A("| Year | CPI-U | Deflator | Wage nominal ($/yr) | Wage real ($/yr) | "
  "Rent nominal ($/mo) | Rent real ($/mo) |")
A("|---|---:|---:|---:|---:|---:|---:|")
for y, r in gy.iterrows():
    A(f"| {y} | {cpi[y]:.3f} | {defl[y]:.4f} | {r.wn:,.0f} | {r.wr:,.0f} | "
      f"{r.rn:,.0f} | {r.rr:,.0f} |")
A("")
pc = lambda s: (s.iloc[-1] / s.iloc[0] - 1) * 100
A("| Change 2015→2022 | Nominal | Real |")
A("|---|---:|---:|")
A(f"| Childcare wage | {pc(gy.wn):+.2f}% | {pc(gy.wr):+.2f}% |")
A(f"| Median gross rent | {pc(gy.rn):+.2f}% | {pc(gy.rr):+.2f}% |")
A("")
A("![Real and nominal childcare wages and rents, 2015–2022]"
  "(../output/q5_real_wages_rents.png)")
A("")

# ---------------------------------------------------------------- Q6
A("## Question 6 — Mean real wage by year, and 2019 vs 2022")
A("")
A("`SE = sd / sqrt(n)`; `sd` is the sample standard deviation (divisor n−1).")
A("")


def yearly(df, lab, unit):
    A(f"**{lab}**")
    A("")
    A(f"| Year | {unit} | Mean real wage ($2022) | Std. dev. | Std. error |")
    A("|---|---:|---:|---:|---:|")
    rows = {}
    for y, grp in df.groupby("year"):
        x = grp[V].dropna().values
        m, s, n = x.mean(), x.std(ddof=1), x.size
        rows[y] = (n, m, s, s / np.sqrt(n))
        A(f"| {y} | {n:,} | {m:,.2f} | {s:,.2f} | {s/np.sqrt(n):,.4f} |")
    A("")
    return rows


cty = yearly(p, "County level", "N counties")
ar = yearly(p.drop_duplicates(["year", "oews_area"]), "OEWS area level", "N areas")

A("**H₀: mean real wage 2019 = mean real wage 2022** (two-tailed)")
A("")
A("| Specification | diff (2022−2019) | SE(diff) | t | df | p | 95% CI |")
A("|---|---:|---:|---:|---:|---:|---|")


def two_sample(rows, lab):
    n1, m1, s1, se1 = rows[2019]
    n2, m2, s2, se2 = rows[2022]
    diff = m2 - m1
    se = np.hypot(se1, se2)
    t = diff / se
    df = (se1**2 + se2**2)**2 / (se1**4 / (n1 - 1) + se2**4 / (n2 - 1))
    pv = 2 * stats.t.sf(abs(t), df)
    tc = stats.t.ppf(0.975, df)
    A(f"| {lab} | {diff:,.4f} | {se:,.4f} | {t:.4f} | {df:,.1f} | {pv:.6g} | "
      f"[{diff-tc*se:,.4f}, {diff+tc*se:,.4f}] |")


two_sample(cty, "Two-sample, county level")
two_sample(ar, "Two-sample, OEWS area level")


def paired(df, key, lab):
    a = df[df.year == 2019][[key, V]].dropna().drop_duplicates(key)
    b = df[df.year == 2022][[key, V]].dropna().drop_duplicates(key)
    m = a.merge(b, on=key, suffixes=("_19", "_22"))
    d = m[V + "_22"] - m[V + "_19"]
    n = len(d)
    se = d.std(ddof=1) / np.sqrt(n)
    t = d.mean() / se
    pv = 2 * stats.t.sf(abs(t), n - 1)
    tc = stats.t.ppf(0.975, n - 1)
    A(f"| {lab} (n = {n:,}) | {d.mean():,.4f} | {se:,.4f} | {t:.4f} | {n-1:,} | "
      f"{pv:.6g} | [{d.mean()-tc*se:,.4f}, {d.mean()+tc*se:,.4f}] |")


paired(p, "county_fips", "Paired, county level")
paired(p.drop_duplicates(["year", "oews_area"]), "oews_area", "Paired, OEWS area level")
A("")
A("Paired SE = `sd(x₂₀₂₂ − x₂₀₁₉) / sqrt(n)`.")
A("")

# ---------------------------------------------------------------- Q7
A("## Question 7 — Childcare wage on female college share, 2022")
A("")
A("`a_mean_i = b0 + b1 · share_women_25plus_bachelors_plus_i + e_i`  (OLS, 2022)")
A("")
X = "share_women_25plus_bachelors_plus"
dd = p[p.year == 2022][["oews_area", "a_mean", X]].dropna()
mod = sm.OLS(dd.a_mean, sm.add_constant(dd[X])).fit()
ci = mod.conf_int(0.05)
A("| Term | Coefficient | Std. error | t | P>\\|t\\| | 95% CI |")
A("|---|---:|---:|---:|---:|---|")
A(f"| `{X}` (b1) | {mod.params[X]:,.4f} | {mod.bse[X]:,.4f} | {mod.tvalues[X]:.4f} | "
  f"{mod.pvalues[X]:.6g} | [{ci.loc[X,0]:,.4f}, {ci.loc[X,1]:,.4f}] |")
A(f"| Intercept (b0) | {mod.params['const']:,.4f} | {mod.bse['const']:,.4f} | "
  f"{mod.tvalues['const']:.4f} | {mod.pvalues['const']:.3g} | "
  f"[{ci.loc['const',0]:,.4f}, {ci.loc['const',1]:,.4f}] |")
A("")
A("| Statistic | Value |")
A("|---|---:|")
A(f"| N | {int(mod.nobs):,} |")
A(f"| R² | {mod.rsquared:.6f} |")
A(f"| Adjusted R² | {mod.rsquared_adj:.6f} |")
A(f"| Root MSE | {np.sqrt(mod.mse_resid):,.4f} |")
A(f"| F(1, {int(mod.df_resid):,}) | {mod.fvalue:.3f} |")
A(f"| p(F) | {mod.f_pvalue:.6g} |")
A(f"| Residual df | {int(mod.df_resid):,} |")
A("")
rob = mod.get_robustcov_results(cov_type="cluster",
                                groups=dd.oews_area.astype("category").cat.codes)
A(f"Standard errors clustered by OEWS area ({dd.oews_area.nunique():,} clusters):")
A("")
A("| Term | Coefficient | Cluster-robust SE | t | P>\\|t\\| |")
A("|---|---:|---:|---:|---:|")
A(f"| `{X}` (b1) | {rob.params[1]:,.4f} | {rob.bse[1]:,.4f} | {rob.tvalues[1]:.4f} | "
  f"{rob.pvalues[1]:.6g} |")
A(f"| Intercept (b0) | {rob.params[0]:,.4f} | {rob.bse[0]:,.4f} | {rob.tvalues[0]:.4f} | "
  f"{rob.pvalues[0]:.3g} |")
A("")

A("")
A("---")
A("")
A("# AI output notes")
A("")
_log = (ROOT / "docs/AI_PROMPT_LOG.md").read_text().splitlines()
for _ln in _log:
    A(("##" + _ln) if _ln.startswith("#") else _ln)

md = "\n".join(L) + "\n"
(ROOT / "docs/WRITEUP.md").write_text(md)

# ---------------------------------------------------------------- HTML
import markdown as md_mod
png = base64.b64encode((ROOT / "output/q5_real_wages_rents.png").read_bytes()).decode()
body = md_mod.markdown(md.replace("../output/q5_real_wages_rents.png",
                                  f"data:image/png;base64,{png}"),
                       extensions=["tables"])
(ROOT / "docs/WRITEUP.html").write_text(
    "<!doctype html><meta charset='utf-8'><title>Childcare siting — write-up</title>"
    "<style>body{font:14px/1.5 -apple-system,Segoe UI,sans-serif;max-width:900px;"
    "margin:40px auto;padding:0 24px;color:#111}"
    "h1{font-size:23px}h2{font-size:17px;margin-top:34px;border-bottom:1px solid #ddd;"
    "padding-bottom:5px}table{border-collapse:collapse;margin:12px 0;font-size:12.5px}"
    "th,td{border:1px solid #ccc;padding:5px 9px}th{background:#f4f4f2;text-align:left}"
    "td:not(:first-child){text-align:right}img{max-width:100%;margin:14px 0}"
    "code{background:#f4f4f2;padding:1px 4px;border-radius:3px;font-size:12px}"
    "@media print{body{margin:0}h2{page-break-after:avoid}table{page-break-inside:avoid}}"
    f"</style>{body}")
print("Wrote docs/WRITEUP.md and docs/WRITEUP.html")
