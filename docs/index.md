---
layout: home
title: Home
---

# H-1B Approval: How Much Can Public Data Explain?

**Xiao Xu & Y. Zhang — PPOL 5204, Georgetown McCourt School (2026)**

A proof-of-concept for a broader policy research program: we ask whether
the datasets the U.S. government releases publicly are sufficient to
explain *who gets approved for an H-1B petition* — or whether the answer
lives in case files that never leave USCIS servers.

Short version: even after joining the USCIS employer release with OFLC
LCA wages and Census local-economy indicators, **no model beats a
constant-mean predictor on city-level approval rate**. The unexplained
variance is structural. It comes from inside individual case files.

## Why this matters (policy pitch)

H-1B is the single largest employment-based temporary visa program in
the United States (~85k new petitions/year capped by Congress, plus
continuing renewals). Public debate treats approval as a semi-random
"lottery-plus-review" process. If approval decisions are in fact
**unexplainable from any public dataset**, then:

- Employers cannot tune compliance to measurable features; they can
  only invest in case documentation quality.
- Watchdog groups cannot audit for disparate treatment using FOIA-able
  data.
- Policy researchers cannot estimate how a proposed rule change will
  affect approval rates without privileged access to case files.
- Applicants cannot make informed decisions about petition timing or
  employer selection.

This repo demonstrates the unexplainability rigorously, and proposes
the specific additional data (USCIS case-level I-129 disclosures with
RFE flags) that a grant could unlock.

## Findings at a glance

### Employer-level models bottom out at R² ≈ 0.008

![Employer model scores]({{ "/assets/figures/model_scores.png" | relative_url }})

Across 61,452 employer filings, three model families (OLS, Random
Forest, XGBoost) converge on the same near-zero R². Feature importance
is diffuse — no single feature dominates.

![Feature importance]({{ "/assets/figures/feature_importance.png" | relative_url }})

### The target is near-degenerate

![Target distribution]({{ "/assets/figures/target_distribution.png" | relative_url }})

82 % of employer filings sit at ≥ 99.9 % approval. There is very little
between-group variation for models to explain.

### Adding wage + local economy does not rescue the ceiling

After joining USCIS with an OFLC LCA + Census city-level file (3,968
cities, 96.7 % of USCIS petition volume), two specifications were run
on identical rows:

![Enrichment delta]({{ "/assets/figures/enrichment_delta.png" | relative_url }})

All six configurations return **negative R²** — none outperforms the
mean predictor. Tree models recover most of their R² (−0.22 → −0.05)
when given wages and economic context, but this is tree *un-overfitting*,
not new signal.

![Wage vs approval]({{ "/assets/figures/wage_vs_approval.png" | relative_url }})

Average wage per city has Pearson correlation ≈ 0 with approval rate.
Higher-paying cities are no more or less likely to see approvals.

## The three-layer narrative

- **Layer 1** — LCA + Census *can* explain **where H-1B demand clusters**
  (petition volume by city).
- **Layer 2** — USCIS public data *cannot* explain **who gets approved**.
  R² ≤ 0.008 across three model families.
- **Layer 3** — Joining Layer 1's data into Layer 2's problem does not
  move the ceiling. Approval variance lives inside case files.

## How to read this site

- [Findings]({{ "/findings.html" | relative_url }}) — detailed results
  and tables.
- [Methodology]({{ "/methodology.html" | relative_url }}) — data
  pipeline, modeling, reproducibility.
- [Phase 2 proposal]({{ "/proposal.html" | relative_url }}) — the
  grant-fundable follow-on this project motivates.
- [Source code on GitHub](https://github.com/) — pipeline, scripts,
  PySpark scale-out variant.
