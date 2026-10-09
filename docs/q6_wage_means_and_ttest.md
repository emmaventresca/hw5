# Question 6 — Mean real childcare wage by year, and a 2019 vs 2022 test

All wages are **inflation-adjusted to constant 2022 dollars** using CPI-U
(`real = nominal × CPI_2022 / CPI_t`). Sample: counties in an OEWS
metropolitan area.

## (a) Mean and standard error by year — county level

`SE = sd / sqrt(n)`, with `sd` the sample standard deviation (divisor n-1).

| Year | N | Mean real wage ($2022) | Std. dev. | Std. error of mean |
|---|---:|---:|---:|---:|
| 2015 | 1,222 | 25,851.21 | 3,266.89 | 93.4543 |
| 2016 | 1,219 | 26,169.71 | 3,371.54 | 96.5665 |
| 2017 | 1,224 | 26,392.52 | 3,514.92 | 100.4673 |
| 2018 | 1,228 | 26,505.90 | 3,702.79 | 105.6648 |
| 2019 | 1,229 | 26,888.87 | 3,897.24 | 111.1685 |
| 2020 | 1,215 | 27,641.46 | 4,423.70 | 126.9104 |
| 2021 | 1,222 | 27,646.21 | 4,464.55 | 127.7151 |
| 2022 | 1,215 | 27,373.48 | 4,337.10 | 124.4261 |

## (a2) Same table at the OEWS area level

OEWS publishes one wage per **area**; that value repeats across every county in
the area, so county-level observations are not independent and the county-level
standard errors above are too small. This version treats each area-year once.

| Year | N areas | Mean real wage ($2022) | Std. dev. | Std. error of mean |
|---|---:|---:|---:|---:|
| 2015 | 381 | 25,937.65 | 3,270.72 | 167.5641 |
| 2016 | 381 | 26,278.38 | 3,323.28 | 170.2566 |
| 2017 | 384 | 26,510.27 | 3,475.07 | 177.3366 |
| 2018 | 385 | 26,710.36 | 3,727.65 | 189.9789 |
| 2019 | 385 | 27,189.98 | 4,021.61 | 204.9603 |
| 2020 | 376 | 28,126.27 | 4,579.23 | 236.1560 |
| 2021 | 382 | 28,041.27 | 4,553.03 | 232.9533 |
| 2022 | 377 | 27,716.31 | 4,409.76 | 227.1140 |

## (b) H0: mu_2019 = mu_2022 — County level

Welch two-sample t-test (unequal variances), two-tailed, alpha = 0.05.

| Quantity | Value |
|---|---:|
| n (2019) | 1,229 |
| mean 2019 ($2022) | 26,888.8700 |
| sd 2019 | 3,897.2438 |
| SE 2019 | 111.1685 |
| n (2022) | 1,215 |
| mean 2022 ($2022) | 27,373.4815 |
| sd 2022 | 4,337.1018 |
| SE 2022 | 124.4261 |
| difference (2022 − 2019) | 484.6115 |
| SE of difference | 166.8541 |
| **t** | **2.9044** |
| Welch df | 2408.506 |
| **two-tailed p** | **0.00371305** |
| 95% CI for difference | [157.4191, 811.8039] |
| pooled-variance t (df = 2,442) | 2.9062, p = 0.00369169 |

**Decision:** reject H0 at alpha = 0.05.

## (b) H0: mu_2019 = mu_2022 — OEWS area level

Welch two-sample t-test (unequal variances), two-tailed, alpha = 0.05.

| Quantity | Value |
|---|---:|
| n (2019) | 385 |
| mean 2019 ($2022) | 27,189.9803 |
| sd 2019 | 4,021.6121 |
| SE 2019 | 204.9603 |
| n (2022) | 377 |
| mean 2022 ($2022) | 27,716.3130 |
| sd 2022 | 4,409.7566 |
| SE 2022 | 227.1140 |
| difference (2022 − 2019) | 526.3327 |
| SE of difference | 305.9240 |
| **t** | **1.7205** |
| Welch df | 750.450 |
| **two-tailed p** | **0.0857595** |
| 95% CI for difference | [-74.2360, 1,126.9014] |
| pooled-variance t (df = 760) | 1.7221, p = 0.0854526 |

**Decision:** fail to reject H0 at alpha = 0.05.

### Worked arithmetic for the county-level test

```
diff      = 27373.4815 - 26888.8700 = 484.6115
SE(diff)  = sqrt(124.4261^2 + 111.1685^2) = 166.8541
t         = 484.6115 / 166.8541 = 2.9044
Welch df  = 2408.506
p         = 0.00371305
```

---

## (c) Clarification — the test as specified, and a paired alternative

The test specified is: **are mean inflation-adjusted childcare wages the same in 2022
as in 2019?** — a two-sample difference of means using each year's own standard error,
combined as `SE(diff) = sqrt(SE_2019^2 + SE_2022^2)`. That is exactly the Welch test
reported in section (b) above; no recomputation was needed.

**Sample overlap.** 1,212 of the 1,215 counties with a 2022 wage (99.8%) also have a
2019 wage — the two years are almost entirely the *same* counties, not independent
draws. A paired test uses that structure and is more powerful. Reported alongside, not
instead of, the test as specified:

| Specification | diff (2022 − 2019) | SE | t | df | p | Decision at 0.05 |
|---|---:|---:|---:|---:|---:|---|
| Two-sample, county level | 484.6115 | 166.8541 | 2.9044 | 2,408.5 | 0.003713 | reject |
| Two-sample, OEWS area level | 526.3327 | 305.9240 | 1.7205 | 750.5 | 0.085760 | fail to reject |
| **Paired, county level** | 456.3581 | 53.2066 | 8.5771 | 1,211 | 2.93e-17 | reject |
| **Paired, OEWS area level** | 497.1583 | 111.5536 | 4.4567 | 373 | 1.10e-05 | reject |

Paired SE uses the standard deviation of the within-unit differences:
`SE = sd(x_2022 - x_2019) / sqrt(n)`.

**This resolves the earlier ambiguity.** The single "fail to reject" result came from
treating the two years as independent samples at the area level. Once the pairing is
used, real wages are higher in 2022 than in 2019 under every specification, including
the conservative area-level one.
