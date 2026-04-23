---
layout: page
title: Findings
subtitle: Detailed results across three analytical layers, with model metrics, variance decomposition, and city-, state-, and industry-level breakdowns.
eyebrow: "Results"
permalink: /findings.html
---

## Dataset in one paragraph

The USCIS FY2024 H-1B Employer Information release contains **61,452 employer-level filings** across 57 U.S. states/territories and 21 NAICS industries, with mean approval rate **96.6 %**. Cassie Zhang contributed a parallel city-level file that joins OFLC LCA disclosures (wages, LCA application counts) with U.S. Census ACS (population, density, rent, unemployment rate). Inner-joining on `STATE + CITY` yields **3,968 cities covering 96.7 % of USCIS petition volume**.

<div class="callout">
  <div class="callout-icon">§</div>
  <div>
    <h4>How to read the metrics below</h4>
    Positive R² means the model explains <em>some</em> share of variance. Negative R² means the model performs <em>worse than a constant-mean predictor</em> — i.e., predicting 96.6% for every observation would have been better. All splits are 80/20 with <code>random_state=42</code>.
  </div>
</div>

## Layer 2 · Employer-level model ceiling {#layer-2}

Three model families trained on USCIS public features alone (state, region, NAICS industry, size bucket, and filing-share variables). All converge on near-zero R².

| Model           | Test R²  | MAE    |
|-----------------|----------|--------|
| OLS             | +0.006   | 0.060  |
| Random Forest   | +0.008   | 0.059  |
| XGBoost         | +0.006   | 0.059  |

**Variance share captured by each grouping** (between-group / total):

| Grouping       | Groups | Between-variance share |
|----------------|--------|------------------------|
| State          | 57     | 0.33 %                 |
| Census region  | 5      | 0.06 %                 |
| NAICS code     | 21     | 0.30 %                 |
| Size bucket    | 5      | 0.03 %                 |

State, industry, and size bucket each explain less than 1% of approval-rate variance. That is the empirical ceiling for any model that uses only these grouping signals.

### Approval rate by state

<figure class="figure">
  <img src="{{ '/assets/figures/approval_by_state.png' | relative_url }}" alt="Approval rate by state, 10 lowest and 10 highest.">
  <figcaption><strong>Fig. 4</strong> State range spans WY (≈ 85 %) to HI / WI / ID / RI (≈ 99–100 %). The lowest-N territories (WY, MP, VI) dominate the low end — not a causal story, just small samples.</figcaption>
</figure>

### Approval rate by industry (NAICS ≥ 100 petitions)

<figure class="figure">
  <img src="{{ '/assets/figures/approval_by_industry.png' | relative_url }}" alt="Approval rate by NAICS industry category.">
  <figcaption><strong>Fig. 5</strong> Tight clustering between 96 % and 99 % across all industries. Industry alone is not a useful discriminator of approval.</figcaption>
</figure>

### Residual structure

<figure class="figure">
  <img src="{{ '/assets/figures/residuals.png' | relative_url }}" alt="Distribution of residuals from the best employer-level model.">
  <figcaption><strong>Fig. 6</strong> Residuals from the best employer-level model (Random Forest) are symmetric around zero with a narrow core and heavy tails at the low end — the model explains almost nothing, so residuals mirror the target distribution.</figcaption>
</figure>

### Feature importance (diffuse, no single driver)

<figure class="figure">
  <img src="{{ '/assets/figures/feature_importance.png' | relative_url }}" alt="Feature importance for Random Forest employer-level model.">
  <figcaption><strong>Fig. 7</strong> Importance is spread across dozens of one-hot state and NAICS dummies with no dominant feature — a pattern consistent with absence of signal rather than with a misspecified feature set.</figcaption>
</figure>

## Layer 3 · Does LCA + Census raise the ceiling? {#layer-3}

Same 3,968 cities, same 80/20 train/test split, two feature sets:

- **Structural** — state, region, `n_employers`, `share_stem`, `share_continuing`, `log_petitions`, `log_employers`.
- **Enriched** — structural + `log_wage`, `log_population`, `log_density`, `log_rent`, `employed_pct`, `unemployed_z`, `log_lca`.

| Model           | Structural R² | Enriched R² | Δ R²    |
|-----------------|---------------|-------------|---------|
| OLS             | −0.022        | −0.014      | +0.007  |
| Random Forest   | −0.222        | −0.055      | +0.167  |
| XGBoost         | −0.305        | −0.164      | +0.141  |

<figure class="figure">
  <img src="{{ '/assets/figures/enrichment_delta.png' | relative_url }}" alt="Structural vs enriched R² for OLS, Random Forest, and XGBoost.">
  <figcaption><strong>Fig. 8</strong> All six specifications return R² &lt; 0. No combination of public features outperforms a constant-mean predictor. Tree models' large apparent gains (ΔR² ≈ 0.14–0.17) reflect un-overfitting, not new signal. The linear Δ — immune to tree-specific overfitting — is 0.007, consistent with Layer 2's ceiling.</figcaption>
</figure>

### Wages don't separate cities

<figure class="figure">
  <img src="{{ '/assets/figures/wage_vs_approval.png' | relative_url }}" alt="City average wage (log) vs approval rate; near-zero correlation.">
  <figcaption><strong>Fig. 9</strong> Pearson r between average annual wage (log scale) and city-level approval rate is near zero. Higher-paying cities are no more or less likely to see approvals.</figcaption>
</figure>

## What the numbers mean

The missing variables are not "more features of the same kind." They are case-level facts:

- Whether the offered wage meets the prevailing wage for the specified SOC code and worksite level (OES wage tier I–IV).
- Specific job title and whether USCIS deems it a "specialty occupation."
- Whether an RFE (Request for Evidence) was issued, and its subject.
- Attorney of record and prior denial history.
- Supporting-document quality (educational evaluation, itinerary, client letters for third-party placements).

None of these are in the USCIS Employer Data Hub release, the OFLC LCA disclosure, or the ACS. They are collected, they exist in digital form, and they are **not released** at the petition grain.

<div class="callout callout-alert">
  <div class="callout-icon">!</div>
  <div>
    <h4>Why this is the right answer, not a failed experiment</h4>
    Finding a near-zero R² after three model families, two feature sets, and two scales of aggregation is not a modeling failure — it is an information-theoretic upper bound. The <a href="{{ '/proposal.html' | relative_url }}">Phase 2 proposal</a> is built on this ceiling.
  </div>
</div>
