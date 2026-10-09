#!/usr/bin/env python3
"""
12_fetch_acs.py — ACS 5-year estimates, county level, 2015-2022.

Pulls the childcare demand/cost explanatory variables for the daycare-siting project.

The API key is read from the CENSUS_API_KEY environment variable, or from the
gitignored .env file in the project root. The key is NEVER printed, NEVER written
to any output file, and NEVER committed. Request URLs are logged with the key
redacted.

Writes:
  data/raw/acs/acs5_county_<year>.json   verbatim API responses (raw, never edited)
  data/processed/acs_county_2015_2022.csv  tidy panel with derived shares

Usage:  python3 scripts/12_fetch_acs.py
"""

import csv
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "acs"
PROC = ROOT / "data" / "processed"
YEARS = range(2015, 2023)  # 2015-2022 inclusive

# ---------------------------------------------------------------- variables
# Verified against api.census.gov/data/2022/acs/acs5/variables/<id>.json
RAW_VARS = {
    # --- demand & cost (the eight requested) ---
    "B19301_001E": "per_capita_income",            # Per capita income, past 12 mo
    "B01003_001E": "total_population",             # Total population
    "B23008_002E": "own_children_under6",          # Own children under 6
    "B23008_004E": "u6_two_parents_both_lf",       # <6, two parents, both in LF
    "B23008_010E": "u6_father_only_lf",            # <6, father only, in LF
    "B23008_013E": "u6_mother_only_lf",            # <6, mother only, in LF
    "B25064_001E": "median_gross_rent",            # Median gross rent (rent+utils)
    "B15002_019E": "women_25plus_total",           # Female 25+, denominator
    "B15002_032E": "women_25plus_bachelors",
    "B15002_033E": "women_25plus_masters",
    "B15002_034E": "women_25plus_professional",
    "B15002_035E": "women_25plus_doctorate",
    "B23022_026E": "women_16_64_total",            # Female 16-64, denominator
    "B23022_029E": "women_16_64_ft_yr",            # Female, 35+ hrs, 50-52 weeks
    # --- young-child counts (for the two shares) ---
    "B09001_003E": "kids_under3",
    "B09001_004E": "kids_3_and_4",
    "B09001_005E": "kids_5",
}

OUT_COLS = [
    "year", "county_fips", "state_fips", "county_code", "name",
    # the eight demand/cost variables
    "per_capita_income", "total_population",
    "own_children_under6", "own_children_under6_all_parents_lf",
    "median_gross_rent",
    "share_women_25plus_bachelors_plus",
    "share_women_16_64_ft_yr",
    # the two young-child shares
    "share_kids_under6", "share_kids_under6_need_care",
    # supporting counts, kept so every share can be re-derived by hand
    "kids_under6", "women_25plus_total", "women_25plus_bachelors_plus",
    "women_16_64_total", "women_16_64_ft_yr",
]


def get_key():
    key = os.environ.get("CENSUS_API_KEY", "").strip()
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("CENSUS_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit(
            "No Census API key found.\n"
            f"Paste your key after CENSUS_API_KEY= in {env}\n"
            "(that file is gitignored), then re-run this script."
        )
    return key


def fetch_year(year, key):
    """Fetch one year. Returns the parsed JSON rows, and saves the raw response."""
    var_list = ",".join(RAW_VARS)
    base = f"https://api.census.gov/data/{year}/acs/acs5"
    query = f"get=NAME,{var_list}&for=county:*&in=state:*"
    url = f"{base}?{query}&key={key}"
    print(f"  {year}: GET {base}?{query}&key=<redacted>")

    req = urllib.request.Request(url, headers={"User-Agent": "stats-final-project"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8")

    if not body.lstrip().startswith("["):
        sys.exit(f"  {year}: expected JSON, got {body[:200]!r} — check the API key.")

    # Save the response verbatim. Raw data is never edited.
    (RAW / f"acs5_county_{year}.json").write_text(body)
    return json.loads(body)


def num(v):
    """ACS uses large negative sentinels (-666666666 etc.) for missing/suppressed."""
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x <= -999999 else x


def share(numer, denom):
    if numer is None or denom is None or denom == 0:
        return ""
    return round(numer / denom, 6)


def main():
    key = get_key()
    RAW.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    rows = []
    print(f"Fetching ACS 5-year county estimates, {YEARS[0]}-{YEARS[-1]}:")
    for year in YEARS:
        for attempt in range(3):
            try:
                payload = fetch_year(year, key)
                break
            except urllib.error.HTTPError as e:
                if attempt == 2:
                    sys.exit(f"  {year}: HTTP {e.code} after 3 attempts — {e.reason}")
                time.sleep(3 * (attempt + 1))
            except urllib.error.URLError as e:
                if attempt == 2:
                    sys.exit(f"  {year}: network error after 3 attempts — {e.reason}")
                time.sleep(3 * (attempt + 1))

        header, body = payload[0], payload[1:]
        idx = {c: i for i, c in enumerate(header)}

        for rec in body:
            g = lambda code: num(rec[idx[code]])  # noqa: E731
            state, county = rec[idx["state"]], rec[idx["county"]]

            u6_all_lf = sum(
                v for v in (g("B23008_004E"), g("B23008_010E"), g("B23008_013E"))
                if v is not None
            ) if any(g(c) is not None for c in
                     ("B23008_004E", "B23008_010E", "B23008_013E")) else None

            w_ba_plus = sum(
                v for v in (g("B15002_032E"), g("B15002_033E"),
                            g("B15002_034E"), g("B15002_035E")) if v is not None
            ) if any(g(c) is not None for c in
                     ("B15002_032E", "B15002_033E",
                      "B15002_034E", "B15002_035E")) else None

            kids_u6 = sum(
                v for v in (g("B09001_003E"), g("B09001_004E"), g("B09001_005E"))
                if v is not None
            ) if any(g(c) is not None for c in
                     ("B09001_003E", "B09001_004E", "B09001_005E")) else None

            own_u6 = g("B23008_002E")
            w25 = g("B15002_019E")
            w1664 = g("B23022_026E")
            w1664_ft = g("B23022_029E")

            rows.append({
                "year": year,
                # 5-char zero-padded string, per the project's data rules
                "county_fips": f"{state}{county}",
                "state_fips": state,
                "county_code": county,
                "name": rec[idx["NAME"]],
                "per_capita_income": g("B19301_001E"),
                "total_population": g("B01003_001E"),
                "own_children_under6": own_u6,
                "own_children_under6_all_parents_lf": u6_all_lf,
                "median_gross_rent": g("B25064_001E"),
                "share_women_25plus_bachelors_plus": share(w_ba_plus, w25),
                "share_women_16_64_ft_yr": share(w1664_ft, w1664),
                "share_kids_under6": share(kids_u6, g("B01003_001E")),
                "share_kids_under6_need_care": share(u6_all_lf, own_u6),
                "kids_under6": kids_u6,
                "women_25plus_total": w25,
                "women_25plus_bachelors_plus": w_ba_plus,
                "women_16_64_total": w1664,
                "women_16_64_ft_yr": w1664_ft,
            })
        print(f"  {year}: {len(body)} counties")

    rows.sort(key=lambda r: (r["year"], r["county_fips"]))
    out = PROC / "acs_county_2015_2022.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in OUT_COLS})

    print(f"\nWrote {out.relative_to(ROOT)} — {len(rows)} county-year rows")
    print(f"Raw responses kept verbatim in {RAW.relative_to(ROOT)}/")


if __name__ == "__main__":
    YEARS = list(YEARS)
    main()
