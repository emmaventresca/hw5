#!/usr/bin/env python3
"""
13_fetch_oews.py — BLS OEWS childcare-worker wages, area level, 2015-2022.

Problem 2 of the final project. Downloads the OEWS metropolitan/nonmetropolitan
area files, extracts SOC 39-9011 (Childcare Workers), and builds a tidy panel.

No API key is needed; these are public BLS downloads.

Writes:
  data/raw/oews/oesm<YY>ma.zip            source archives (never edited)
  data/raw/oews/extracted/                unzipped workbooks (never edited)
  data/processed/oews_childcare_2015_2022.csv

Usage:  python3 scripts/13_fetch_oews.py
"""

import pathlib
import sys
import urllib.request
import zipfile

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "oews"
EXTRACT = RAW / "extracted"
PROC = ROOT / "data" / "processed"
YEARS = range(2015, 2023)

SOC = "39-9011"  # Childcare Workers
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36 "
    "(academic research; emma.ventresca@yale.edu)"
)

# OEWS suppression / top-code flags, per BLS field_descriptions.xlsx:
#   *  = estimate not released
#   ** = data not available
#   #  = wage >= $100.00/hour or $208,000/year
SUPPRESSED = {"*", "**", "#", "", "nan", "None"}

WAGE_COLS = [
    "tot_emp", "h_mean", "a_mean", "h_pct10", "h_pct25", "h_median",
    "h_pct75", "h_pct90", "a_pct10", "a_pct25", "a_median", "a_pct75", "a_pct90",
]

# Column-name drift across years -> canonical lowercase names.
RENAME = {
    "area_name": "area_title",
    "loc quotient": "loc_quotient",
    "occ_group": "o_group",
}


def download(year):
    yy = str(year)[2:]
    dest = RAW / f"oesm{yy}ma.zip"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"  {year}: archive already present ({dest.stat().st_size:,} bytes)")
        return dest
    url = f"https://www.bls.gov/oes/special-requests/oesm{yy}ma.zip"
    print(f"  {year}: downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, dest.open("wb") as f:
        f.write(r.read())
    print(f"  {year}: {dest.stat().st_size:,} bytes")
    return dest


def workbooks(year, archive):
    """Extract and return the MSA and BOS workbooks for a year.

    MSA = metropolitan areas, BOS = nonmetropolitan 'balance of state' areas.
    Both are needed: the project crosswalk contains areas of both kinds.
    """
    out = []
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            base = pathlib.Path(name).name
            if base.startswith("~$") or "__MACOSX" in name:
                continue  # Excel lock files
            if not base.lower().endswith((".xlsx", ".xls")):
                continue
            if not (base.startswith(("MSA_M", "BOS_M", "aMSA_M"))):
                continue
            if base.startswith("aMSA_M"):
                continue  # 'a' = alphabetical duplicate of MSA, same rows
            z.extract(name, EXTRACT)
            out.append((base.split("_")[0], EXTRACT / name))
    if not out:
        sys.exit(f"  {year}: no MSA/BOS workbook found inside {archive.name}")
    return out


def clean(v):
    """Return a float, or '' for suppressed/top-coded/missing values."""
    s = str(v).strip().replace(",", "").replace("$", "")
    if s in SUPPRESSED:
        return ""
    try:
        return float(s)
    except ValueError:
        return ""


def flag(v):
    s = str(v).strip()
    return s if s in {"*", "**", "#"} else ""


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    EXTRACT.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    frames = []
    print(f"OEWS childcare workers (SOC {SOC}), {YEARS[0]}-{YEARS[-1]}:")
    for year in YEARS:
        archive = download(year)
        for kind, wb in workbooks(year, archive):
            df = pd.read_excel(wb, dtype=str)
            df.columns = [RENAME.get(c.strip().lower(), c.strip().lower())
                          for c in df.columns]

            df = df[df["occ_code"].astype(str).str.strip() == SOC].copy()
            # Reset the index: `out` below is built with a fresh RangeIndex, and
            # assigning a Series that still carries the source index would align
            # on index and silently produce NaN.
            df = df.reset_index(drop=True)
            if df.empty:
                print(f"  {year} {kind}: WARNING — no {SOC} rows")
                continue

            out = pd.DataFrame()
            out["year"] = [year] * len(df)
            # 7-char zero-padded string, per the project's data rules
            out["oews_area"] = (
                df["area"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
                .str.zfill(7)
            )
            out["area_title"] = df["area_title"].astype(str).str.strip()
            out["area_kind"] = "metro" if kind == "MSA" else "nonmetro"
            out["occ_code"] = SOC
            out["occ_title"] = df["occ_title"].astype(str).str.strip()
            for c in WAGE_COLS:
                out[c] = df[c].map(clean) if c in df.columns else ""
            # Keep the suppression markers for the two headline wage measures
            out["a_mean_flag"] = df["a_mean"].map(flag) if "a_mean" in df else ""
            out["a_median_flag"] = df["a_median"].map(flag) if "a_median" in df else ""

            frames.append(out)
            print(f"  {year} {kind}: {len(out)} areas")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["year", "oews_area"]).reset_index(drop=True)

    dupes = panel.duplicated(["year", "oews_area"]).sum()
    if dupes:
        print(f"  WARNING: {dupes} duplicate (year, oews_area) rows")

    dest = PROC / "oews_childcare_2015_2022.csv"
    panel.to_csv(dest, index=False)
    print(f"\nWrote {dest.relative_to(ROOT)} — {len(panel)} area-year rows")

    # Coverage against the project crosswalk
    xw = pd.read_csv(ROOT / "data" / "crosswalks" / "county_oews_crosswalk.csv",
                     dtype={"oews_area": str, "county_fips": str})
    xw["oews_area"] = xw["oews_area"].str.zfill(7)
    have = set(zip(panel["year"], panel["oews_area"]))
    need = set(zip(xw["year"], xw["oews_area"]))
    missing = need - have
    print(f"Crosswalk area-years: {len(need)}; matched in OEWS: {len(need & have)}; "
          f"missing: {len(missing)}")

    n_sup = (panel["a_mean"] == "").sum()
    print(f"Rows with suppressed/unavailable A_MEAN: {n_sup} of {len(panel)}")


if __name__ == "__main__":
    YEARS = list(YEARS)
    main()
