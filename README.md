# H-1B Approval: How Much Can Public Data Explain?

This repo asks, through three successive layers of evidence, whether
**public datasets can explain H-1B approval outcomes** — or whether the
answer lives in case-level material that the U.S. government never
releases.

Short version: even after joining the USCIS employer release with OFLC
LCA wages and Census local-economy indicators, **no model beats a
constant-mean predictor** on city-level approval rate. The unexplained
variance is structural — it comes from inside individual case files.

## Research question

The original coursework tried to *predict* approval rate with OLS,
Random Forest, and XGBoost. All three scored near zero (R² ≤ 0.01).
Rather than keep tuning, this repo reframes the work as a question
about the data itself:

> Is H-1B approval *explainable* from publicly available data — USCIS
> employer counts, OFLC LCA wages, Census population/housing/labor
> indicators — or do approval outcomes depend on case-level signals
> that neither release contains?

A collaborator (Y. Zhang) contributed an LCA-joined city-level file
with wage and local-economy variables. Merging that file is what makes
the *explainability* question testable, because the enrichment columns
are exactly the ones the original USCIS file omits.

## The three-layer story

### Layer 1 — Where does H-1B demand cluster? (LCA + Census)

Wages, density, population, rent, and labor-market indicators *do*
carry signal about **how many** H-1B petitions a city generates.
Bucketing cities into Low / Medium / High petition volume is
classifiable from those economic features (Random Forest + SMOTE,
trilabel classification). That is a legitimate signal — but it is
about *demand*, not *approval*.

### Layer 2 — Who gets approved? (USCIS employer file alone)

Running three model families on the USCIS public release with state,
NAICS industry, and application mix as features:

| Model         | Test R² | MAE    |
|---------------|--------:|-------:|
| OLS           |  +0.006 | 0.060  |
| Random Forest |  +0.008 | 0.059  |
| XGBoost       |  +0.006 | 0.059  |

Between-group variance is tiny:

| Grouping      | Groups | Between-variance share |
|---------------|-------:|-----------------------:|
| State         |     57 |                 0.33 % |
| Census region |      5 |                 0.06 % |
| NAICS code    |     21 |                 0.30 % |
| Size bucket   |      5 |                 0.03 % |

82 % of filings sit at ≥ 99.9 % approval. The target is near-degenerate
at the group level.

### Layer 3 — Does adding wage + local economy move the ceiling?

Aggregating USCIS to the city level and inner-joining Zhang's file
produces 3,968 cities covering 96.7 % of USCIS petition volume. Two
specifications are run on identical rows:

- **Structural**: state, region, n_employers, share_stem,
  share_continuing, log_petitions, log_employers
- **Enriched**: structural + log_wage, log_population, log_density,
  log_rent, employed_pct, unemployed_z, log_lca

| Model         | Structural R² | Enriched R² | Δ R²   |
|---------------|--------------:|------------:|-------:|
| OLS           |        −0.022 |      −0.014 | +0.007 |
| Random Forest |        −0.222 |      −0.055 | +0.167 |
| XGBoost       |        −0.305 |      −0.164 | +0.141 |

Read the numbers carefully. Tree models go **up** when wages and the
local economy are added — but only because without those features they
overfit noise. Even with the full enriched feature set, **no model
achieves R² > 0**. On this data, a constant "every city gets the mean
approval rate" predictor is harder to beat than any combination of
state, industry, wage, population, density, rent, or unemployment.

All specs land at MAE ≈ 0.04 — roughly 4 percentage points of noise
around a mean of 96.6 %. That is the ceiling.

## Interpretation

- USCIS public variables explain *essentially none* of the variance in
  approval rate.
- Adding OFLC LCA wages and Census local-economy indicators does not
  rescue the situation. It partly cures tree overfitting but does not
  reveal hidden signal — the OLS improvement is 0.007 R².
- Approval variance therefore lives **inside individual case files**:
  wage relative to prevailing wage by SOC, job-title specialty, RFE
  history, petition attorney, supporting documentation quality. None
  of those are in any public release.
- The original "our models are bad" reading is wrong. The models are
  as good as they can be on this input. The data is bounded, not the
  method.

## Pipeline

```
data/raw/h1b_fy2024.csv              ┐ USCIS FY2024 employer release
                                     │   (UTF-16, 61,452 rows)
                                     ▼  scripts/cleaning.py
data/processed/h1b_clean.parquet     │
                                     ▼  scripts/feature_engineering.py
data/processed/h1b_features.parquet  │   STEM flag, region, size, etc.
                                     │
                 ┌───────────────────┤
                 │                   │
                 ▼                   ▼
      scripts/modeling.py     scripts/merge_external.py
      (employer-level)        aggregate USCIS → city  ◄──┐
      model_metrics.json      join on STATE+CITY         │  data/raw/
      feature_importance.csv                             │  lca_city_enrichment.csv
      residuals.parquet                                  │  (LCA wage + Census,
                                                         │   9,866 rows, courtesy
                                                         │   of Y. Zhang)
                                                         ▼
                              data/processed/h1b_city_merged.parquet
                                      │  3,968 cities, 96.7 % petition coverage
                                      ▼
                              scripts/modeling_city.py
                              structural vs. enriched specs
                              model_metrics_city.json
                                      │
                                      ▼
                              scripts/analysis.py
                              all figures + descriptive tables
```

Run end-to-end:

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
```

Each stage reads one upstream artifact and writes one downstream, so
any stage can be re-run independently after an edit.

## Repository layout

```
.
├── data/
│   ├── raw/
│   │   ├── h1b_fy2024.csv            # USCIS employer release (UTF-16)
│   │   └── lca_city_enrichment.csv   # LCA wage + Census, Y. Zhang
│   └── processed/                    # parquet outputs, gitignored
├── scripts/
│   ├── cleaning.py
│   ├── feature_engineering.py
│   ├── modeling.py                   # employer-level (Layer 2)
│   ├── merge_external.py             # USCIS × LCA × Census join (pandas)
│   ├── merge_external_spark.py       # same join on PySpark
│   ├── modeling_city.py              # structural vs enriched (Layer 3)
│   ├── analysis.py
│   └── run_pipeline.py
├── outputs/
│   ├── figures/                      # PNGs used in the write-up
│   └── tables/                       # CSV / JSON / parquet artifacts
├── docs/                             # GitHub Pages site
│   ├── _config.yml                   # Jekyll config (minima theme)
│   ├── index.md                      # landing page / pitch
│   ├── findings.md                   # detailed results
│   ├── methodology.md                # pipeline + modeling doc
│   ├── proposal.md                   # Phase 2 grant proposal
│   └── assets/figures/               # PNGs served by Pages
├── requirements.txt
└── README.md
```

## Figures

- `outputs/figures/approval_by_state.png` — 10 lowest + 10 highest
- `outputs/figures/approval_by_industry.png` — NAICS ranking
- `outputs/figures/target_distribution.png` — 82 % of rows ≥ 99.9 %
- `outputs/figures/model_scores.png` — employer-level R² bars
- `outputs/figures/feature_importance.png` — top 15, no dominator
- `outputs/figures/residuals.png` — best-model residuals
- `outputs/figures/enrichment_delta.png` — **Layer 3: structural vs. enriched**
- `outputs/figures/wage_vs_approval.png` — **Layer 3: wages don't separate cities**

## Scalability

The file sizes here fit comfortably in a single process, so the
default path is pandas + sklearn. The pipeline is written so that
scale-up requires minimal surgery — and one stage has already been
ported.

### Distributed-compute variant (PySpark)

`scripts/merge_external_spark.py` reimplements the city-level merge
stage on PySpark 3.5. Outputs verified identical to the pandas path
(3,968 rows, `approval_rate` delta = 0, `avg_wage` delta ≤ 8e-13
from float roundoff):

```bash
pip install "pyspark==3.5.*"      # needs Java 8/11/17 at runtime
python scripts/merge_external_spark.py
```

Runs on `local[*]` unchanged and is structured so the only change for
a managed cluster (Dataproc / EMR / Databricks) is replacing the
final `.toPandas().to_parquet(...)` with `.write.parquet(...)` — a
single-line swap that is only stubbed on Windows because `winutils.exe`
is not installed for the Hadoop filesystem shim.

### The rest of the pipeline

- **Storage.** All intermediate artifacts are parquet (columnar,
  compressed, schema-typed). A full decade of releases — roughly
  600k–1M rows — still fits in memory on a laptop.
- **Compute.** Each stage is a standalone script with a single input
  and a single output. Swapping `pandas` for `dask.dataframe` or
  `polars` is a localized change (read/write + groupby), not a
  pipeline rewrite. Sklearn/XGBoost steps already use `n_jobs=-1`
  and `tree_method="hist"`.
- **Orchestration.** `run_pipeline.py` is a thin shell over stage
  scripts; replacing it with Airflow / Prefect / Dagster changes only
  how stages are triggered, not what they do.
- **Bottleneck.** The bottleneck was never compute; it was the input.
  This repo already takes one step toward the fix (joining OFLC LCA
  and Census). The next step — joining USCIS case-level releases with
  I-129 approval/denial flags and RFE history — is the commit worth
  making, not bigger hardware.

## What's intentionally not here

- **No predictive claim.** The modeling stages exist to bound
  explanatory power, not to ship a predictor.
- **No hyperparameter search.** Three families of models sit at the
  same near-zero ceiling. Search is not what's between us and a good
  model.
- **No causal claim.** State and industry correlate with approval
  rate; they do not *cause* it. Wages correlate with petition volume
  but not with approval. Every correlation reported here is read as
  an upper bound on between-group signal, not as a mechanism.

## Project website

The GitHub Pages site under `docs/` is the grant-pitch surface:

- `docs/index.md` — policy motivation, headline findings, key figures.
- `docs/findings.md` — detailed tables and residual structure.
- `docs/methodology.md` — pipeline, Spark variant, reproducibility.
- `docs/proposal.md` — 12-month Phase 2 grant proposal.

To publish, enable GitHub Pages on the `docs/` folder of the `main`
branch in the repository settings.

## Data sources

- USCIS Employer Data Hub — H-1B Employer Information (FY2024):
  <https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub>

## Authors

- **Xiao Xu** 
- **Cassie Zhang** 
