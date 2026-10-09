#!/usr/bin/env python3
"""
17_q6_wage_means_ttest.py — Question 6.

(a) Mean inflation-adjusted childcare wage by year, with the standard error of
    each mean, laid out so every number can be reproduced by hand.
(b) Two-sample hypothesis test, H0: mu_2019 = mu_2022 (real, 2022 dollars).

Formulas used (all by hand-reproducible):
    mean   m  = sum(x) / n
    sd     s  = sqrt( sum((x - m)^2) / (n - 1) )          [sample sd, ddof = 1]
    se     SE = s / sqrt(n)
    Welch  t  = (m_2022 - m_2019) / sqrt(SE_2022^2 + SE_2019^2)
    Welch df  = (SE_a^2 + SE_b^2)^2 / ( SE_a^4/(n_a-1) + SE_b^4/(n_b-1) )

Writes docs/q6_wage_means_and_ttest.md
"""
import pathlib
import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
p = pd.read_csv(ROOT / "data/processed/county_panel_real_2015_2022.csv",
                dtype={"county_fips": str, "oews_area": str})

VAR = "a_mean_real2022"


def table(df, label):
    rows = []
    for y, grp in df.groupby("year"):
        x = grp[VAR].dropna().values
        n = x.size
        m = x.mean()
        s = x.std(ddof=1)
        rows.append({"year": int(y), "n": n, "mean": m, "sd": s,
                     "se": s / np.sqrt(n)})
    t = pd.DataFrame(rows)
    print(f"\n=== {label} ===")
    print(t.round(4).to_string(index=False))
    return t


# (i) county level — one observation per county-year, as the panel is built
county = table(p, "County level (unit = county-year)")

# (ii) area level — one observation per OEWS area-year. The wage is published per
# AREA and repeats across every county in that area, so county-level observations
# are not independent and the county-level SE is understated. Shown for comparison.
area = table(p.drop_duplicates(["year", "oews_area"]), "OEWS area level (unit = area-year)")


def welch(df, ya, yb, data, label):
    a = data[data.year == ya][VAR].dropna().values
    b = data[data.year == yb][VAR].dropna().values
    na, nb = a.size, b.size
    ma, mb = a.mean(), b.mean()
    sa, sb = a.std(ddof=1), b.std(ddof=1)
    sea, seb = sa / np.sqrt(na), sb / np.sqrt(nb)
    diff = mb - ma
    se_diff = np.sqrt(sea**2 + seb**2)
    t = diff / se_diff
    dfree = (sea**2 + seb**2)**2 / (sea**4 / (na - 1) + seb**4 / (nb - 1))
    pv = 2 * stats.t.sf(abs(t), dfree)
    tc = stats.t.ppf(0.975, dfree)
    ci = (diff - tc * se_diff, diff + tc * se_diff)
    # cross-check with scipy
    t_sp, p_sp = stats.ttest_ind(b, a, equal_var=False)
    # pooled-variance version, for comparison
    sp2 = ((na - 1) * sa**2 + (nb - 1) * sb**2) / (na + nb - 2)
    se_p = np.sqrt(sp2 * (1 / na + 1 / nb))
    t_p = diff / se_p
    p_p = 2 * stats.t.sf(abs(t_p), na + nb - 2)
    print(f"\n=== Welch t-test, H0: mu_{ya} = mu_{yb}  [{label}] ===")
    print(f"  {ya}: n={na}, mean={ma:.4f}, sd={sa:.4f}, SE={sea:.4f}")
    print(f"  {yb}: n={nb}, mean={mb:.4f}, sd={sb:.4f}, SE={seb:.4f}")
    print(f"  diff (mu_{yb} - mu_{ya}) = {diff:.4f}")
    print(f"  SE(diff) = sqrt({sea:.4f}^2 + {seb:.4f}^2) = {se_diff:.4f}")
    print(f"  t = {diff:.4f} / {se_diff:.4f} = {t:.4f}")
    print(f"  Welch df = {dfree:.3f};  t_crit(.975) = {tc:.4f}")
    print(f"  two-tailed p = {pv:.6g}")
    print(f"  95% CI for the difference = [{ci[0]:.4f}, {ci[1]:.4f}]")
    print(f"  scipy cross-check: t={t_sp:.4f}, p={p_sp:.6g}")
    print(f"  pooled-variance alternative: t={t_p:.4f}, df={na+nb-2}, p={p_p:.6g}")
    return dict(na=na, nb=nb, ma=ma, mb=mb, sa=sa, sb=sb, sea=sea, seb=seb,
                diff=diff, se_diff=se_diff, t=t, df=dfree, p=pv, ci=ci,
                t_sp=t_sp, p_sp=p_sp, t_p=t_p, p_p=p_p)


r_cty = welch(p, 2019, 2022, p, "county level")
r_area = welch(p, 2019, 2022, p.drop_duplicates(["year", "oews_area"]), "area level")

# ------------------------------------------------------------------ write-up
L = ["# Question 6 — Mean real childcare wage by year, and a 2019 vs 2022 test", "",
     "All wages are **inflation-adjusted to constant 2022 dollars** using CPI-U",
     "(`real = nominal × CPI_2022 / CPI_t`). Sample: counties in an OEWS",
     "metropolitan area.", "",
     "## (a) Mean and standard error by year — county level", "",
     "`SE = sd / sqrt(n)`, with `sd` the sample standard deviation (divisor n-1).", "",
     "| Year | N | Mean real wage ($2022) | Std. dev. | Std. error of mean |",
     "|---|---:|---:|---:|---:|"]
for r in county.itertuples():
    L.append(f"| {r.year} | {r.n:,} | {r.mean:,.2f} | {r.sd:,.2f} | {r.se:,.4f} |")

L += ["", "## (a2) Same table at the OEWS area level", "",
      "OEWS publishes one wage per **area**; that value repeats across every county in",
      "the area, so county-level observations are not independent and the county-level",
      "standard errors above are too small. This version treats each area-year once.", "",
      "| Year | N areas | Mean real wage ($2022) | Std. dev. | Std. error of mean |",
      "|---|---:|---:|---:|---:|"]
for r in area.itertuples():
    L.append(f"| {r.year} | {r.n:,} | {r.mean:,.2f} | {r.sd:,.2f} | {r.se:,.4f} |")

for lbl, r in (("County level", r_cty), ("OEWS area level", r_area)):
    L += ["", f"## (b) H0: mu_2019 = mu_2022 — {lbl}", "",
          "Welch two-sample t-test (unequal variances), two-tailed, alpha = 0.05.", "",
          "| Quantity | Value |", "|---|---:|",
          f"| n (2019) | {r['na']:,} |",
          f"| mean 2019 ($2022) | {r['ma']:,.4f} |",
          f"| sd 2019 | {r['sa']:,.4f} |",
          f"| SE 2019 | {r['sea']:,.4f} |",
          f"| n (2022) | {r['nb']:,} |",
          f"| mean 2022 ($2022) | {r['mb']:,.4f} |",
          f"| sd 2022 | {r['sb']:,.4f} |",
          f"| SE 2022 | {r['seb']:,.4f} |",
          f"| difference (2022 − 2019) | {r['diff']:,.4f} |",
          f"| SE of difference | {r['se_diff']:,.4f} |",
          f"| **t** | **{r['t']:.4f}** |",
          f"| Welch df | {r['df']:.3f} |",
          f"| **two-tailed p** | **{r['p']:.6g}** |",
          f"| 95% CI for difference | [{r['ci'][0]:,.4f}, {r['ci'][1]:,.4f}] |",
          f"| pooled-variance t (df = {r['na']+r['nb']-2:,}) | {r['t_p']:.4f}, p = {r['p_p']:.6g} |",
          "",
          f"**Decision:** {'reject' if r['p'] < 0.05 else 'fail to reject'} H0 at alpha = 0.05."]

L += ["", "### Worked arithmetic for the county-level test", "",
      "```",
      f"diff      = {r_cty['mb']:.4f} - {r_cty['ma']:.4f} = {r_cty['diff']:.4f}",
      f"SE(diff)  = sqrt({r_cty['seb']:.4f}^2 + {r_cty['sea']:.4f}^2) = {r_cty['se_diff']:.4f}",
      f"t         = {r_cty['diff']:.4f} / {r_cty['se_diff']:.4f} = {r_cty['t']:.4f}",
      f"Welch df  = {r_cty['df']:.3f}",
      f"p         = {r_cty['p']:.6g}",
      "```"]
(ROOT / "docs/q6_wage_means_and_ttest.md").write_text("\n".join(L) + "\n")
print("\nWrote docs/q6_wage_means_and_ttest.md")
