#!/usr/bin/env python3
"""
18_q7_regression.py — Question 7.

Regress childcare worker mean annual wage on the share of women 25+ with a
bachelor's degree or higher. 2022 only.

    a_mean_i = b0 + b1 * share_women_25plus_bachelors_plus_i + e_i

2022 is the CPI base year, so real and nominal wages are identical here.

Writes docs/q7_regression_2022.md
"""
import pathlib
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = pathlib.Path(__file__).resolve().parent.parent
p = pd.read_csv(ROOT / "data/processed/county_panel_real_2015_2022.csv",
                dtype={"county_fips": str, "oews_area": str})

Y, X = "a_mean", "share_women_25plus_bachelors_plus"
d = p[(p.year == 2022)][["county_fips", "name", "oews_area", Y, X]].dropna()

mod = sm.OLS(d[Y], sm.add_constant(d[X])).fit()
rob = mod.get_robustcov_results(cov_type="cluster",
                                groups=d.oews_area.astype("category").cat.codes)

b0, b1 = mod.params["const"], mod.params[X]
se0, se1 = mod.bse["const"], mod.bse[X]
ci = mod.conf_int(0.05)
n = int(mod.nobs)

print(mod.summary())
print("\nCluster-robust (by OEWS area) SEs:")
print(f"  b1 = {rob.params[1]:.4f}, SE = {rob.bse[1]:.4f}, "
      f"t = {rob.tvalues[1]:.4f}, p = {rob.pvalues[1]:.6g}, "
      f"clusters = {d.oews_area.nunique()}")

L = ["# Question 7 — Childcare wage on female college share, 2022", "",
     "Model (OLS, 2022 only, counties in an OEWS metropolitan area):", "",
     "```",
     "a_mean_i = b0 + b1 * share_women_25plus_bachelors_plus_i + e_i",
     "```", "",
     "`a_mean` is the OEWS mean annual wage for childcare workers (SOC 39-9011) in the",
     "county's OEWS area, in dollars. The regressor is a proportion on 0-1, so `b1` is",
     "the predicted dollar change in annual wage for a **1.0 (i.e. 0 to 100 percentage",
     "point) increase** in the share; divide by 100 for a 1-percentage-point change.", "",
     "## Coefficients", "",
     "| Term | Coefficient | Std. error | t | P>\\|t\\| | 95% CI |",
     "|---|---:|---:|---:|---:|---|",
     f"| `{X}` (b1) | {b1:,.4f} | {se1:,.4f} | {mod.tvalues[X]:.4f} | "
     f"{mod.pvalues[X]:.6g} | [{ci.loc[X,0]:,.4f}, {ci.loc[X,1]:,.4f}] |",
     f"| Intercept (b0) | {b0:,.4f} | {se0:,.4f} | {mod.tvalues['const']:.4f} | "
     f"{mod.pvalues['const']:.6g} | [{ci.loc['const',0]:,.4f}, {ci.loc['const',1]:,.4f}] |",
     "", "## Fit", "",
     "| Statistic | Value |", "|---|---:|",
     f"| N (counties) | {n:,} |",
     f"| R-squared | {mod.rsquared:.6f} |",
     f"| Adjusted R-squared | {mod.rsquared_adj:.6f} |",
     f"| Root MSE | {np.sqrt(mod.mse_resid):,.4f} |",
     f"| F(1, {int(mod.df_resid)}) | {mod.fvalue:.3f} (p = {mod.f_pvalue:.6g}) |",
     f"| Residual df | {int(mod.df_resid):,} |",
     "",
     "## Note on standard errors",
     "",
     "OEWS publishes one wage per **area**, repeated across every county in that area,",
     f"so the {n:,} counties carry only {d.oews_area.nunique():,} distinct wage values.",
     "Ordinary SEs therefore overstate precision. Clustering by OEWS area:",
     "",
     "| Term | Coefficient | Cluster-robust SE | t | P>\\|t\\| |",
     "|---|---:|---:|---:|---:|",
     f"| `{X}` (b1) | {rob.params[1]:,.4f} | {rob.bse[1]:,.4f} | {rob.tvalues[1]:.4f} | "
     f"{rob.pvalues[1]:.6g} |",
     f"| Intercept (b0) | {rob.params[0]:,.4f} | {rob.bse[0]:,.4f} | {rob.tvalues[0]:.4f} | "
     f"{rob.pvalues[0]:.6g} |",
     "",
     f"Clusters = {d.oews_area.nunique():,} OEWS areas.",
     "",
     "The coefficients are identical either way; only the standard errors change.",
     "Use the ordinary SEs above for a by-hand test; the clustered ones are the",
     "defensible inference."]
(ROOT / "docs/q7_regression_2022.md").write_text("\n".join(L) + "\n")
print("\nWrote docs/q7_regression_2022.md")
