---
layout: page
title: Phase 2 proposal
permalink: /proposal/
---

# Phase 2: case-level H-1B explainability

**Funding ask.** 12-month grant, one postdoc + one part-time RA,
cloud compute budget (target: $15k on GCP Dataproc or AWS EMR).

## The question this project leaves open

This repo establishes that no combination of **publicly released**
employer-level variables explains individual H-1B approval outcomes.
It does not — and cannot — tell us which **case-level** variables
would close the explanatory gap. That is the Phase 2 question:

> Given sufficient case-level access, how much of the unexplained
> variance in H-1B approval becomes explainable? Which case-level
> variables carry the signal, and do they correlate with applicant
> characteristics in ways that warrant regulatory attention?

## Why it is fundable

1. **Defensible baseline.** We have already bounded what the public
   data can do (R² ≤ 0.01, MAE ≈ 0.04). Any improvement from
   case-level data is measurable against a published ceiling.
2. **Policy-relevant audiences.** USCIS Office of Inspector General,
   Government Accountability Office (GAO), Migration Policy Institute,
   CATO Institute, and corporate immigration practices are all
   current consumers of H-1B analytics with no access to the source
   of truth.
3. **Tractable ask.** The needed data already exists in digital form
   inside USCIS (I-129 adjudication records, RFE logs, OES wage tier
   assignments). Phase 2 is a FOIA / data-use-agreement project,
   not a new-data-collection project.
4. **Reproducibility-first design.** The Phase 1 pipeline is parquet
   + pandas + PySpark, already scale-portable. Swapping in a case-
   level source requires only a new `cleaning_case_level.py` stage.

## Deliverables (12 months)

| Month  | Deliverable                                                    |
|-------:|----------------------------------------------------------------|
|   1–2  | Data-use agreement with USCIS / FOIA batch requests for I-129 |
|   3–4  | Case-level ingestion stage (`cleaning_case_level.py`) on cluster |
|   5–6  | Replication of Phase 1 ceiling on case-level N (sanity check) |
|   7–8  | Explanatory modeling: which case fields close the R² gap?     |
|   9–10 | Disparate-impact audit (approval by applicant country, employer size, attorney) |
|  11–12 | White paper + replication kit + convenings with USCIS OIG/GAO |

## Data we need beyond Phase 1

- **USCIS I-129 case-level records** (petitioner, beneficiary country,
  SOC code, requested validity period, RFE status, approval/denial,
  ground of denial).
- **OFLC LCA wage tier (I–IV)** — the prevailing-wage classification
  is recorded at filing but *not* included in the public disclosure
  file at petition grain.
- **Attorney of record** — a strong candidate explanatory variable;
  already recorded on Form G-28.

## Why the scale story is real even at 60k rows

The Phase 1 data is ~60k rows. Phase 2, at case-level, is ~400k/year
× 5–10 years of history = 2–4M rows with an order of magnitude more
columns (case-level fields, RFE transcripts, attorney identifiers).
That is where a PySpark pipeline stops being infrastructure theater
and starts paying for itself. Phase 1's `merge_external_spark.py`
was written precisely so the Phase 2 scale-up is a configuration
change, not an engineering project.

## Risk register

| Risk                                                 | Mitigation                                            |
|------------------------------------------------------|--------------------------------------------------------|
| USCIS denies / slow-walks the data-use agreement     | FOIA fallback; begin with already-released OIG reports |
| Case-level data also fails to explain approval       | Publishable negative result; sharpens the question     |
| Disparate-impact finding triggers legal scrutiny     | Coordinate early with institutional counsel            |
| Data volume exceeds single-laptop workflow           | Already solved; Phase 1 pipeline is cluster-ready      |

## Expected outcomes

Either:

- **A** — Case-level variables close the gap. We publish the specific
  variables and their coefficients, with implications for USCIS
  transparency policy and employer compliance best practices.
- **B** — Case-level variables also fail to close the gap. We publish
  that negative result, which reframes H-1B adjudication as
  **irreducibly discretionary** and makes a much stronger case for
  procedural reform (structured rubrics, reviewer training, or
  algorithmic audit).

Both outcomes are publishable. Both inform policy. The grant's value
does not depend on which one lands.
