# Question 7 — Childcare wage on female college share, 2022

Model (OLS, 2022 only, counties in an OEWS metropolitan area):

```
a_mean_i = b0 + b1 * share_women_25plus_bachelors_plus_i + e_i
```

`a_mean` is the OEWS mean annual wage for childcare workers (SOC 39-9011) in the
county's OEWS area, in dollars. The regressor is a proportion on 0-1, so `b1` is
the predicted dollar change in annual wage for a **1.0 (i.e. 0 to 100 percentage
point) increase** in the share; divide by 100 for a 1-percentage-point change.

## Coefficients

| Term | Coefficient | Std. error | t | P>\|t\| | 95% CI |
|---|---:|---:|---:|---:|---|
| `share_women_25plus_bachelors_plus` (b1) | 16,499.9862 | 1,058.1894 | 15.5927 | 4.48293e-50 | [14,423.8894, 18,576.0829] |
| Intercept (b0) | 22,359.1942 | 339.1614 | 65.9249 | 0 | [21,693.7823, 23,024.6060] |

## Fit

| Statistic | Value |
|---|---:|
| N (counties) | 1,208 |
| R-squared | 0.167777 |
| Adjusted R-squared | 0.167087 |
| Root MSE | 3,949.9201 |
| F(1, 1206) | 243.131 (p = 4.48293e-50) |
| Residual df | 1,206 |

## Note on standard errors

OEWS publishes one wage per **area**, repeated across every county in that area,
so the 1,208 counties carry only 373 distinct wage values.
Ordinary SEs therefore overstate precision. Clustering by OEWS area:

| Term | Coefficient | Cluster-robust SE | t | P>\|t\| |
|---|---:|---:|---:|---:|
| `share_women_25plus_bachelors_plus` (b1) | 16,499.9862 | 2,217.3295 | 7.4414 | 6.97122e-13 |
| Intercept (b0) | 22,359.1942 | 606.3146 | 36.8772 | 2.64822e-126 |

Clusters = 373 OEWS areas.

The coefficients are identical either way; only the standard errors change.
Use the ordinary SEs above for a by-hand test; the clustered ones are the
defensible inference.
