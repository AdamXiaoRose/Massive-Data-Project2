---
layout: page
title: "Phase 2 · Case-level H-1B explainability"
subtitle: A 12-month follow-on project that turns the Phase 1 ceiling into a funded investigation of what actually drives H-1B approval decisions.
eyebrow: "Path forward"
permalink: /proposal.html
---

<div class="callout">
  <div class="callout-icon">$</div>
  <div>
    <h4>Funding ask</h4>
    12-month grant · one postdoc + one part-time research assistant · cloud compute budget of $15 k on GCP Dataproc or AWS EMR.
  </div>
</div>

## The question this project leaves open

This repo establishes that no combination of <strong>publicly released</strong> employer-level variables explains individual H-1B approval outcomes. It does not — and cannot — tell us which <strong>case-level</strong> variables would close the explanatory gap. That is the Phase 2 question:

> Given sufficient case-level access, how much of the unexplained variance in H-1B approval becomes explainable? Which case-level variables carry the signal, and do they correlate with applicant characteristics in ways that warrant regulatory attention?

## Why it is fundable

1. **Defensible baseline.** We have already bounded what the public data can do (R² ≤ 0.01, MAE ≈ 0.04). Any improvement from case-level data is measurable against a published ceiling.
2. **Policy-relevant audiences.** USCIS Office of Inspector General, Government Accountability Office (GAO), Migration Policy Institute, CATO Institute, and corporate immigration practices are all current consumers of H-1B analytics with no access to the source of truth.
3. **Tractable ask.** The needed data already exists in digital form inside USCIS (I-129 adjudication records, RFE logs, OES wage-tier assignments). Phase 2 is a FOIA / data-use-agreement project, not a new-data-collection project.
4. **Reproducibility-first design.** The Phase 1 pipeline is parquet + pandas + PySpark, already scale-portable. Swapping in a case-level source requires only a new `cleaning_case_level.py` stage.

## Deliverables (12 months)

| Month  | Deliverable                                                                   |
|--------|-------------------------------------------------------------------------------|
| 1–2    | Data-use agreement with USCIS / FOIA batch requests for I-129                 |
| 3–4    | Case-level ingestion stage (`cleaning_case_level.py`) on cluster              |
| 5–6    | Replication of Phase 1 ceiling on case-level N (sanity check)                 |
| 7–8    | Explanatory modeling: which case fields close the R² gap?                     |
| 9–10   | Disparate-impact audit (approval by applicant country, employer size, attorney) |
| 11–12  | White paper + replication kit + convenings with USCIS OIG / GAO               |

## Data we need beyond Phase 1

- **USCIS I-129 case-level records** — petitioner, beneficiary country, SOC code, requested validity period, RFE status, approval/denial, ground of denial.
- **OFLC LCA wage tier (I–IV)** — the prevailing-wage classification is recorded at filing but <em>not</em> included in the public disclosure file at petition grain.
- **Attorney of record** — a strong candidate explanatory variable; already recorded on Form G-28.

## Why the scale story is real even at 60 k rows

The Phase 1 data is ≈ 60 k rows. Phase 2, at case-level, is ≈ 400 k/year × 5–10 years of history = **2–4 M rows with an order of magnitude more columns** (case-level fields, RFE transcripts, attorney identifiers). That is where a PySpark pipeline stops being infrastructure theater and starts paying for itself. Phase 1's `merge_external_spark.py` was written precisely so the Phase 2 scale-up is a configuration change, not an engineering project.

## Risk register

| Risk                                                      | Mitigation                                                          |
|-----------------------------------------------------------|---------------------------------------------------------------------|
| USCIS denies or slow-walks the data-use agreement          | FOIA fallback; begin with already-released OIG reports              |
| Case-level data also fails to explain approval             | Publishable negative result; sharpens the question                   |
| Disparate-impact finding triggers legal scrutiny           | Coordinate early with institutional counsel                          |
| Data volume exceeds single-laptop workflow                 | Already solved; Phase 1 pipeline is cluster-ready                    |

## Expected outcomes

<div class="card-grid" style="margin-top: 1.4em;">
  <div class="card">
    <span class="card-label">Outcome A</span>
    <h3>Case-level variables close the gap</h3>
    <p>We publish the specific variables and their coefficients, with implications for USCIS transparency policy and employer compliance best practices.</p>
  </div>
  <div class="card">
    <span class="card-label">Outcome B</span>
    <h3>Case-level variables also fail</h3>
    <p>We publish that negative result, which reframes H-1B adjudication as <em>irreducibly discretionary</em> and makes a much stronger case for procedural reform — structured rubrics, reviewer training, or algorithmic audit.</p>
  </div>
</div>

Both outcomes are publishable. Both inform policy. The grant's value does not depend on which one lands.
