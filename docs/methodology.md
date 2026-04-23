---
layout: page
title: Methodology
subtitle: Pipeline architecture, pandas ↔ PySpark parity, modeling choices, data-quality fixes, and full reproducibility.
eyebrow: "How"
permalink: /methodology.html
---

## Pipeline

Every stage reads one upstream artifact and writes one downstream, so any stage can be re-run independently. `scripts/run_pipeline.py` orchestrates the full sequence.

```text
data/raw/h1b_fy2024.csv              ┐ USCIS FY2024 employer release
                                     │   (UTF-16, 61,452 rows)
                                     ▼  scripts/cleaning.py
data/processed/h1b_clean.parquet     │
                                     ▼  scripts/feature_engineering.py
data/processed/h1b_features.parquet  │
                                     │
                 ┌───────────────────┤
                 ▼                   ▼
      scripts/modeling.py     scripts/merge_external.py       ← pandas path
      (employer-level)        scripts/merge_external_spark.py ← Spark path
                                      │
                                      ▼
                              data/processed/h1b_city_merged.parquet
                                      │   3,968 cities
                                      ▼
                              scripts/modeling_city.py
                                      │
                                      ▼
                              scripts/analysis.py → figures + tables
```

## Distributed compute

`scripts/merge_external_spark.py` is a PySpark DataFrame-API reimplementation of the pandas merge stage. Identical aggregation, identical join keys, identical outputs.

<div class="callout">
  <div class="callout-icon">≡</div>
  <div>
    <h4>Layer-3 parity verification</h4>
    3,968 rows match between pandas and Spark outputs. <code>approval_rate</code> delta is 0.0, <code>avg_wage</code> delta is ≤ 8e-13 (float roundoff). The pipelines are operationally identical.
  </div>
</div>

The Spark path is deliberately identical in shape so it can move from `local[*]` to a managed cluster (Dataproc / EMR / Databricks) without code changes. On a cluster the final `.toPandas()` collection should be replaced with `.write.parquet(OUT)` — a one-line swap. It is stubbed out on Windows only because `winutils.exe` is not installed.

## Modeling choices

### Target

- **Employer level** (`modeling.py`): approval rate per (employer × city × year).
- **City level** (`modeling_city.py`): approval rate aggregated over all employers in a (state, city) cell.

### Features

**Structural (public USCIS only):**

- `state`, `region` (Census), `naics_code`, `size_bucket` — categorical, one-hot encoded with `min_frequency=20`.
- `share_continuing`, `share_initial`, `log_petitions`, `log_employer_total`, `is_stem` — numeric.

**Enrichment (LCA + Census, city-level only):**

- `log_wage` — average annual wage, winsorized at $500 k.
- `log_lca` — LCA application count.
- `log_population`, `log_density`, `log_rent`, `employed_pct`, `unemployed_z` — Census ACS-derived.

### Models

| Model                     | Configuration                                                              | Role                                  |
|---------------------------|---------------------------------------------------------------------------|---------------------------------------|
| `LinearRegression`        | No regularization                                                          | Canonical linear baseline             |
| `RandomForestRegressor`   | `n_estimators=200–300`, `max_depth=12`                                     | Non-linear interactions, seed-stable  |
| `XGBRegressor`            | `n_estimators=400–500`, `max_depth=5–6`, `lr=0.05`, `tree_method='hist'`   | Gradient-boosting sanity check        |

### Evaluation

80/20 split with `random_state=42`. Test R² and MAE reported. No hyperparameter tuning on the test set.

## Data quality

- USCIS `Approval Rate` column is nudged by ~10⁻⁶ to avoid 0/1; we recompute rates from the raw count columns to eliminate the nudge.
- LCA `AVG_ANNUAL_WAGE` contains unit-mixing artifacts reaching $238 M. Values above $500 k/yr are dropped before averaging.
- Zip codes are coerced to 5-digit strings; the first three digits form a region proxy used only in Layer 2.
- USCIS employer names are uppercased and trimmed. `"UNKNOWN"` is kept as a distinct category rather than dropped.

## Reproducibility

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
```

Running the Spark variant additionally requires Java 8/11/17:

```bash
pip install "pyspark==3.5.*"
python scripts/merge_external_spark.py
```

All figures and tables in `outputs/` are regenerated deterministically from `data/raw/`.

## Limitations

- **Year alignment.** LCA year may not match USCIS FY2024 perfectly; city-level aggregation partially absorbs this.
- **Aggregation loss.** City-level aggregation loses within-city employer variation that Layer 2's employer-level models do capture — we lose resolution but gain join power.
- **Descriptive, not causal.** Every between-group correlation is read as an upper bound on signal, not as a mechanism.
- **Layer 1 is complementary, not re-validated.** Zhang's original demand-volume classification uses non-matching years and a different outcome variable; it is cited as context, not re-run on the unified dataset.
