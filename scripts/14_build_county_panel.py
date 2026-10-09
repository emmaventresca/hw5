#!/usr/bin/env python3
"""
14_build_county_panel.py — Question 3: merge OEWS wages to counties, attach ACS.

Pipeline:
  crosswalk (county_fips x year -> oews_area)
    |  join on [year, oews_area]
  OEWS childcare wages (area level)
    |  join on [year, county_fips]
  ACS county explanatory variables
    |  keep only counties in an OEWS *metropolitan* area (oews_area starts "00")
  -> data/processed/county_panel_2015_2022.csv   (one row per year x county)

Both key fields are forced to zero-padded strings before any join:
  county_fips -> 5 characters,  oews_area -> 7 characters.

Metropolitan-division backfill (2015-2017)
------------------------------------------
In 2015-2017 OEWS published the 11 largest metros ONLY as metropolitan divisions
(NECTA divisions for Boston), not as the combined MSA the crosswalk uses. Left alone
this drops ~10% of metro county-years in those years. For those area-years only, the
divisions are aggregated up to the parent MSA:

    tot_emp = sum over divisions
    a_mean / h_mean = employment-weighted mean over divisions

Percentiles and medians are NOT aggregated -- a pooled median cannot be recovered from
division medians -- so they are left blank on backfilled rows. Every backfilled row is
marked `wage_source = "division_aggregate"`; published rows are `"published"`.

Usage:  python3 scripts/14_build_county_panel.py
"""

import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
DOCS = ROOT / "docs"

# parent MSA (as used by the crosswalk) -> its OEWS division codes.
# Derived from the area titles in the 2015-2017 OEWS files; printed for audit at run time.
DIVISIONS = {
    "0031080": ["0031084", "0011244"],                                  # Los Angeles
    "0016980": ["0016974", "0020994", "0029404", "0023844"],            # Chicago
    "0019100": ["0019124", "0023104"],                                  # Dallas-Fort Worth
    "0019820": ["0019804", "0047664"],                                  # Detroit
    "0033100": ["0033124", "0022744", "0048424"],                       # Miami
    "0035620": ["0035614", "0035004", "0020524", "0035084"],            # New York
    "0037980": ["0037964", "0015804", "0033874", "0048864"],            # Philadelphia
    "0041860": ["0041884", "0036084", "0042034"],                       # San Francisco
    "0042660": ["0042644", "0045104"],                                  # Seattle
    "0047900": ["0047894", "0043524"],                                  # Washington DC
    "0071650": ["0071654", "0072104", "0073104", "0073604", "0074204",  # Boston NECTA
                "0074804", "0074854", "0075404", "0076524", "0078254"],
}

ACS_VARS = [
    "per_capita_income", "total_population", "own_children_under6",
    "own_children_under6_all_parents_lf", "median_gross_rent",
    "share_women_25plus_bachelors_plus", "share_women_16_64_ft_yr",
    "share_kids_under6", "share_kids_under6_need_care",
]


def wmean(values, weights):
    v, w = np.asarray(values, float), np.asarray(weights, float)
    ok = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    return np.nan if not ok.any() else float((v[ok] * w[ok]).sum() / w[ok].sum())


def backfill_divisions(oews):
    """Add MSA-level rows built from divisions, for area-years OEWS didn't publish."""
    have = set(zip(oews.year, oews.oews_area))
    by_area = {(r.year, r.oews_area): r for r in oews.itertuples()}
    new, audit = [], []

    for year in sorted(oews.year.unique()):
        for msa, divs in DIVISIONS.items():
            if (year, msa) in have:
                continue  # OEWS published the MSA itself; never override it
            parts = [by_area[(year, d)] for d in divs if (year, d) in by_area]
            if not parts:
                continue
            emp = [p.tot_emp for p in parts]
            tot = float(np.nansum(emp))
            row = {
                "year": year, "oews_area": msa,
                "area_title": f"[aggregated from {len(parts)} divisions]",
                "area_kind": "metro", "occ_code": "39-9011",
                "occ_title": "Childcare Workers",
                "tot_emp": tot,
                "h_mean": wmean([p.h_mean for p in parts], emp),
                "a_mean": wmean([p.a_mean for p in parts], emp),
                "wage_source": "division_aggregate",
            }
            new.append(row)
            audit.append({"year": year, "msa": msa, "n_divisions": len(parts),
                          "tot_emp": tot, "a_mean": round(row["a_mean"], 1)})

    if not new:
        return oews, pd.DataFrame(audit)
    return pd.concat([oews, pd.DataFrame(new)], ignore_index=True), pd.DataFrame(audit)


def main():
    # ---------------------------------------------------------------- load + zero-pad
    xw = pd.read_csv(ROOT / "data/crosswalks/county_oews_crosswalk.csv",
                     dtype={"county_fips": str, "oews_area": str})
    xw["county_fips"] = xw.county_fips.str.strip().str.zfill(5)
    xw["oews_area"] = xw.oews_area.str.strip().str.zfill(7)

    oews = pd.read_csv(PROC / "oews_childcare_2015_2022.csv", dtype={"oews_area": str})
    oews["oews_area"] = oews.oews_area.str.strip().str.zfill(7)
    oews["wage_source"] = "published"

    acs = pd.read_csv(PROC / "acs_county_2015_2022.csv", dtype={"county_fips": str})
    acs["county_fips"] = acs.county_fips.str.strip().str.zfill(5)

    for name, df, col, width in (("crosswalk", xw, "county_fips", 5),
                                 ("crosswalk", xw, "oews_area", 7),
                                 ("OEWS", oews, "oews_area", 7),
                                 ("ACS", acs, "county_fips", 5)):
        bad = set(df[col].str.len()) - {width}
        if bad:
            sys.exit(f"{name}.{col}: unexpected widths {bad}")
    print("Zero-padding verified: county_fips = 5 chars, oews_area = 7 chars "
          "in crosswalk, OEWS and ACS.")

    # Obsolete county FIPS carried in the crosswalk. Each is a legacy duplicate whose
    # modern replacement is ALSO in the crosswalk for every year, so dropping them
    # removes double-counting rather than losing a county:
    #   12025 Dade County FL      -> renamed 12086 Miami-Dade in 1997
    #   51515 Bedford city VA     -> merged into 51019 Bedford County in 2013
    # ACS publishes only the modern codes, so these rows could never match.
    OBSOLETE = {"12025": "12086", "51515": "51019"}
    for old_fips, new_fips in OBSOLETE.items():
        same = set(xw.loc[xw.county_fips == old_fips, "year"]) <= set(
            xw.loc[xw.county_fips == new_fips, "year"])
        assert same, f"{old_fips} present in years {new_fips} is not — cannot drop"
    n0 = len(xw)
    xw = xw[~xw.county_fips.isin(OBSOLETE)].copy()
    print(f"Dropped {n0 - len(xw)} crosswalk rows with obsolete county FIPS "
          f"{sorted(OBSOLETE)} (modern equivalents already present).")

    # ---------------------------------------------------------------- backfill
    oews, audit = backfill_divisions(oews)
    if not audit.empty:
        audit.to_csv(DOCS / "oews_division_backfill.csv", index=False)
        print(f"\nBackfilled {len(audit)} MSA-year wage cells from metropolitan "
              f"divisions (2015-2017); audit -> docs/oews_division_backfill.csv")

    # ---------------------------------------------------------------- merge
    wage_cols = ["tot_emp", "h_mean", "a_mean", "h_median", "a_median",
                 "a_pct10", "a_pct25", "a_pct75", "a_pct90", "wage_source"]
    wage_cols = [c for c in wage_cols if c in oews.columns]

    panel = xw.merge(oews[["year", "oews_area"] + wage_cols],
                     on=["year", "oews_area"], how="left", validate="m:1")
    before = len(panel)
    panel = panel.merge(acs[["year", "county_fips", "name"] + ACS_VARS],
                        on=["year", "county_fips"], how="left", validate="1:1")
    assert len(panel) == before, "ACS join changed row count"

    # ---------------------------------------------------------------- metro filter
    panel = panel[panel.oews_area.str.startswith("00")].copy()
    panel = panel.sort_values(["year", "county_fips"]).reset_index(drop=True)

    # ---------------------------------------------------------------- diagnostics
    n = len(panel)
    miss = int(panel.a_mean.isna().sum())
    print(f"\nMetro county-year rows: {n:,}")
    print(f"Counties per year: "
          f"{panel.groupby('year').county_fips.nunique().to_dict()}")
    print(f"Duplicate (year, county_fips): "
          f"{int(panel.duplicated(['year','county_fips']).sum())}")
    print(f"\nSANITY CHECK — rows missing a_mean: {miss} of {n} "
          f"({miss/n*100:.2f}%)  [target: < 1%]")
    g = panel.groupby("year").a_mean.agg(n="size", missing=lambda s: int(s.isna().sum()))
    g["pct"] = (g.missing / g.n * 100).round(2)
    print(g.to_string())

    print(f"\nWage source: "
          f"{panel.wage_source.value_counts(dropna=False).to_dict()}")
    print("ACS coverage — rows missing each predictor:")
    print(panel[ACS_VARS].isna().sum().to_string())

    if miss / n >= 0.01:
        print("\nWARNING: missing wages exceed the 1% tolerance.")

    unmatched = panel[panel.a_mean.isna()][
        ["year", "county_fips", "name", "oews_area", "area_title"]]
    unmatched.to_csv(DOCS / "q3_counties_missing_wages.csv", index=False)

    dest = PROC / "county_panel_2015_2022.csv"
    panel.to_csv(dest, index=False)
    print(f"\nWrote {dest.relative_to(ROOT)} — {n:,} rows x {panel.shape[1]} cols")


if __name__ == "__main__":
    main()
