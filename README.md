# Childcare siting — county-level data build and results, 2015–2022

Builds a year × county panel of childcare-worker wages and county demographics for
counties in a BLS OEWS metropolitan area, and reports descriptive statistics, real
(inflation-adjusted) trends, a 2019-vs-2022 wage test, and a 2022 regression.

| Output | What it is |
|---|---|
| `output/Ventresca_writeup.pdf` | Results (Questions 1–7), then the full prompt record |
| `docs/WRITEUP.md` / `.html` | Same content in Markdown / HTML |
| `docs/AI_PROMPT_LOG.md` | Every prompt used, verbatim, with what the AI did |
| `data/processed/county_panel_real_2015_2022.csv` | The analysis panel |

## Sources

| Source | What | Key needed |
|---|---|---|
| ACS 5-year (Census) | county income, population, children under 6, rent, female education and employment shares | yes — your own |
| OEWS (BLS) | mean annual wage, SOC 39-9011 (Childcare Workers), by MSA / nonmetro area | no |
| CPI-U (BLS) | series `CUUR0000SA0`, annual averages, for constant 2022 dollars | no |
| County → OEWS area crosswalk | provided, year-specific | no |

## Reproduce

Requires Python 3.10+ with `pandas`, `numpy`, `scipy`, `matplotlib`, `statsmodels`,
`openpyxl`, `markdown`.

**You need your own free Census API key** — none is included in this repository. Get one
at <https://api.census.gov/data/key_signup.html>, then:

```bash
cp .env.example .env     # paste your key after CENSUS_API_KEY=
```

`.env` is gitignored. No key is needed for the OEWS, CPI-U or crosswalk steps.

Run in order:

| Script | What it does | Network |
|---|---|---|
| `scripts/12_fetch_acs.py` | ACS 5-year county variables, 2015–2022 | yes (Census key) |
| `scripts/13_fetch_oews.py` | OEWS SOC 39-9011 area wages, 2015–2022 (~287 MB) | yes |
| `scripts/14_build_county_panel.py` | Q3 — merge to a year × county metro panel | no |
| `scripts/15_q4_descriptives.py` | Q4 — 2022 descriptive statistics | no |
| `scripts/16_q5_real_trends.py` | Q5 — CPI-U deflation and the figure | yes (BLS CPI) |
| `scripts/17_q6_wage_means_ttest.py` | Q6 — means, standard errors, 2019 vs 2022 | no |
| `scripts/18_q7_regression.py` | Q7 — OLS, 2022 | no |
| `scripts/19_build_writeup.py` | rebuilds the write-up from the processed data | no |

```bash
for s in 12_fetch_acs 13_fetch_oews 14_build_county_panel 15_q4_descriptives \
         16_q5_real_trends 17_q6_wage_means_ttest 18_q7_regression 19_build_writeup; do
  python3 "scripts/$s.py" || break
done
```

`data/raw/` is gitignored; scripts 12 and 13 re-download it, and everything in
`data/processed/` is rebuilt from it, so every published number regenerates from
scratch.

## Data notes

- Join keys are zero-padded strings before any merge: `county_fips` 5 characters,
  `oews_area` 7 characters.
- Analysis sample is counties whose `oews_area` begins `00` (OEWS metropolitan).
- For 2015–2017, OEWS published the eleven largest metros only as metropolitan
  (or NECTA) divisions rather than the combined MSA. Those are aggregated to the parent
  MSA with employment weights; medians are not aggregated, since a pooled median cannot
  be recovered from division medians. Backfilled rows are marked
  `wage_source = "division_aggregate"`.
- Obsolete county FIPS `12025` and `51515` are dropped as duplicates of `12086` and
  `51019`.
- 99 of 9,873 metro county-years (1.00%) have no wage, from BLS non-publication in
  small areas. Connecticut has no ACS values for 2022, where ACS replaced counties with
  nine planning regions.
- Dollar series are deflated to constant 2022 dollars with CPI-U.
