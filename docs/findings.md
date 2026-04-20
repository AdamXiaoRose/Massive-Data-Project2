---
layout: page
title: Findings
permalink: /findings/
---

# Findings

## Dataset in one paragraph

The USCIS FY2024 H-1B Employer Information release contains **61,452
employer-level filings** across 57 U.S. states/territories and 21 NAICS
industries, with mean approval rate **96.6 %**. Y. Zhang contributed
a parallel city-level file that joins OFLC LCA disclosures (wages,
LCA application counts) with U.S. Census ACS (population, density,
rent, unemployment rate). Inner-joining on `STATE + CITY` yields
**3,968 cities covering 96.7 % of USCIS petition volume**.

## Layer 2: employer-level model ceiling

| Model         | Test R² | MAE    |
|---------------|--------:|-------:|
| OLS           |  +0.006 | 0.060  |
| Random Forest |  +0.008 | 0.059  |
| XGBoost       |  +0.006 | 0.059  |

Variance share captured by each grouping (between-group / total):

| Grouping      | Groups | Between-variance share |
|---------------|-------:|-----------------------:|
| State         |     57 |                 0.33 % |
| Census region |      5 |                 0.06 % |
| NAICS code    |     21 |                 0.30 % |
| Size bucket   |      5 |                 0.03 % |

### Approval rate by state (10 lowest, 10 highest)

![Approval by state]({{ "/assets/figures/approval_by_state.png" | relative_url }})

State range spans WY (85 %) to HI / WI / ID / RI (~99–100 %). The
lowest-N territories (WY, MP, VI) dominate the low end — not a causal
story, just small samples.

### Approval rate by industry (NAICS, ≥ 100 petitions)

![Approval by industry]({{ "/assets/figures/approval_by_industry.png" | relative_url }})

Tight clustering between 96 % and 99 % across all industries.

### Residual structure

![Residuals]({{ "/assets/figures/residuals.png" | relative_url }})

Residuals from the best employer-level model (Random Forest) are
symmetric around zero with a narrow core and heavy tails at the low
end — the model explains nothing, so residuals look like the target
distribution.

## Layer 3: does LCA + Census raise the ceiling?

Same 3,968 cities, same 80/20 train/test split, two feature sets:

- **Structural**: state, region, n_employers, share_stem,
  share_continuing, log_petitions, log_employers.
- **Enriched**: structural + log_wage, log_population, log_density,
  log_rent, employed_pct, unemployed_z, log_lca.

| Model         | Structural R² | Enriched R² | Δ R²   |
|---------------|--------------:|------------:|-------:|
| OLS           |        −0.022 |      −0.014 | +0.007 |
| Random Forest |        −0.222 |      −0.055 | +0.167 |
| XGBoost       |        −0.305 |      −0.164 | +0.141 |

![Enrichment delta]({{ "/assets/figures/enrichment_delta.png" | relative_url }})

**All six specifications return R² < 0.** No combination of public
features outperforms "predict 96.6 % for every city." Tree models'
large apparent gains (Δ R² ≈ 0.14–0.17) are cured-overfit, not
new signal. The linear Δ — which is immune to tree-specific
overfitting — is 0.007 R², consistent with Layer 2's ceiling.

### Wages don't separate cities

![Wage vs approval]({{ "/assets/figures/wage_vs_approval.png" | relative_url }})

Pearson r between average annual wage (log scale) and city-level
approval rate is near zero.

## What the numbers mean

The missing variables are not "more features of the same kind." They
are case-level facts:

- Whether the offered wage meets the prevailing wage for the specified
  SOC code and worksite level (OES wage tier I–IV).
- Specific job title and whether USCIS deems it a "specialty
  occupation."
- Whether an RFE (Request for Evidence) was issued, and its subject.
- Attorney of record and prior denial history.
- Supporting-document quality (educational evaluation, itinerary,
  client letters for third-party placements).

None of these are in the USCIS Employer Data Hub release, the OFLC
LCA disclosure, or the ACS. They are collected, they exist in digital
form, and they are **not released** at the petition grain.
