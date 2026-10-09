#!/usr/bin/env python3
"""
16_q5_real_trends.py — Question 5: convert dollars to 2022 dollars and plot trends.

CPI-U (series CUUR0000SA0, annual averages) is fetched from the BLS public API and
cached to data/processed/cpi_u_annual.csv. Deflation to constant 2022 dollars:

    real_2022 = nominal_t * (CPI_2022 / CPI_t)

Produces:
  data/processed/county_panel_real_2015_2022.csv   panel + real columns
  output/q5_real_wages_rents.png                   the figure
  docs/q5_real_trends_table.md                     the underlying numbers
"""
import json
import pathlib
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
BASE_YEAR = 2022

# Validated categorical slots 1 and 2 (light surface) from the viz palette.
C_WAGE, C_RENT = "#2a78d6", "#eb6834"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"


def cpi_u():
    cache = PROC / "cpi_u_annual.csv"
    if cache.exists():
        return pd.read_csv(cache).set_index("year")["cpi_u"]
    req = urllib.request.Request(
        "https://api.bls.gov/publicAPI/v1/timeseries/data/",
        data=json.dumps({"seriesid": ["CUUR0000SA0"], "startyear": "2015",
                         "endyear": "2022", "annualaverage": True}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    assert d["status"] == "REQUEST_SUCCEEDED", d.get("message")
    rows = [{"year": int(x["year"]), "cpi_u": float(x["value"])}
            for x in d["Results"]["series"][0]["data"] if x["periodName"] == "Annual"]
    s = pd.DataFrame(rows).sort_values("year")
    s.to_csv(cache, index=False)
    return s.set_index("year")["cpi_u"]


cpi = cpi_u()
defl = cpi[BASE_YEAR] / cpi            # multiply nominal by this
print("CPI-U annual averages and deflators to 2022$:")
print(pd.DataFrame({"cpi_u": cpi, "deflator": defl.round(4)}).to_string())

p = pd.read_csv(PROC / "county_panel_2015_2022.csv",
                dtype={"county_fips": str, "oews_area": str})
p["deflator"] = p.year.map(defl)
p["a_mean_real2022"] = p.a_mean * p.deflator
p["median_gross_rent_real2022"] = p.median_gross_rent * p.deflator
p["per_capita_income_real2022"] = p.per_capita_income * p.deflator
p.to_csv(PROC / "county_panel_real_2015_2022.csv", index=False)

g = p.groupby("year").agg(
    wage_nom=("a_mean", "mean"), wage_real=("a_mean_real2022", "mean"),
    rent_nom=("median_gross_rent", "mean"), rent_real=("median_gross_rent_real2022", "mean"),
    n_wage=("a_mean", "count"), n_rent=("median_gross_rent", "count")).round(1)
print("\nMetro-county means by year:")
print(g.to_string())

# ------------------------------------------------------------------ figure
yrs = g.index.values
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), facecolor=SURFACE)
fig.subplots_adjust(wspace=0.32, top=0.80, bottom=0.17, left=0.065, right=0.985)

def style(ax, title, ylab):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, fontsize=11, color=INK, pad=9, loc="left", fontweight="medium")
    ax.set_ylabel(ylab, fontsize=9, color=MUTED)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.set_xticks(yrs); ax.set_xticklabels(yrs, rotation=45)

# Panel 1 — wages, real vs nominal
ax = axes[0]
ax.plot(yrs, g.wage_nom, lw=2, ls="--", color=MUTED, marker="o", ms=4,
        label="Nominal")
ax.plot(yrs, g.wage_real, lw=2, color=C_WAGE, marker="o", ms=5, label="Real (2022$)")
style(ax, "Childcare worker mean annual wage", "$ per year")
ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc="upper left")

# Panel 2 — rents, real vs nominal
ax = axes[1]
ax.plot(yrs, g.rent_nom, lw=2, ls="--", color=MUTED, marker="o", ms=4, label="Nominal")
ax.plot(yrs, g.rent_real, lw=2, color=C_RENT, marker="o", ms=5, label="Real (2022$)")
style(ax, "Median gross rent (rent + utilities)", "$ per month")
ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc="upper left")

# Panel 3 — both, indexed to a common base (never a dual axis)
ax = axes[2]
wi = g.wage_real / g.wage_real.iloc[0] * 100
ri = g.rent_real / g.rent_real.iloc[0] * 100
ax.axhline(100, color=GRID, lw=1)
ax.plot(yrs, wi, lw=2, color=C_WAGE, marker="o", ms=5, label="Real wage")
ax.plot(yrs, ri, lw=2, color=C_RENT, marker="o", ms=5, label="Real rent")
# The two series land within 0.02 index points of each other in 2022, so the end
# labels are nudged apart vertically and carry one decimal to stay distinguishable.
ax.annotate(f"{wi.iloc[-1]:.1f}", (yrs[-1], wi.iloc[-1]), textcoords="offset points",
            xytext=(7, 7), color=C_WAGE, fontsize=9, va="center", fontweight="medium")
ax.annotate(f"{ri.iloc[-1]:.1f}", (yrs[-1], ri.iloc[-1]), textcoords="offset points",
            xytext=(7, -8), color=C_RENT, fontsize=9, va="center", fontweight="medium")
style(ax, "Both, indexed (2015 = 100, real)", "index, 2015 = 100")
ax.set_xlim(yrs[0] - 0.2, yrs[-1] + 0.8)
ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc="upper left")

fig.suptitle("Childcare worker wages and rents in OEWS metropolitan counties, "
             "2015–2022 (constant 2022 dollars, CPI-U)",
             fontsize=12.5, color=INK, x=0.065, ha="left", y=0.955)
fig.text(0.065, 0.025,
         "Unweighted means across metro counties. Dashed grey = nominal; "
         "colour = inflation-adjusted. Source: BLS OEWS (SOC 39-9011), ACS 5-year, CPI-U.",
         fontsize=8, color=MUTED, ha="left")
out = ROOT / "output/q5_real_wages_rents.png"
fig.savefig(out, dpi=200, facecolor=SURFACE)
print(f"\nWrote {out.relative_to(ROOT)}")

lines = ["# Question 5 — Real wages and rents, 2015–2022 (constant 2022 dollars)", "",
         "CPI-U (CUUR0000SA0, annual average). real = nominal × (CPI_2022 / CPI_t).", "",
         "| Year | CPI-U | Deflator | Wage nominal | Wage real | Rent nominal | Rent real |",
         "|---|---:|---:|---:|---:|---:|---:|"]
for y in yrs:
    lines.append(f"| {y} | {cpi[y]:.3f} | {defl[y]:.4f} | {g.wage_nom[y]:,.0f} | "
                 f"{g.wage_real[y]:,.0f} | {g.rent_nom[y]:,.0f} | {g.rent_real[y]:,.0f} |")
pct = lambda s: (s.iloc[-1] / s.iloc[0] - 1) * 100
lines += ["", f"Real change 2015→2022: wage {pct(g.wage_real):+.1f}%, "
              f"rent {pct(g.rent_real):+.1f}%.",
          f"Nominal change 2015→2022: wage {pct(g.wage_nom):+.1f}%, "
          f"rent {pct(g.rent_nom):+.1f}%."]
(ROOT / "docs/q5_real_trends_table.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[-3:]))
