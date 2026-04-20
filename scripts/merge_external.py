"""Join USCIS employer data with an LCA + local-economy city-level file.

The external file (data/raw/lca_city_enrichment.csv, contributed by a
collaborator) carries exactly the variables the USCIS public release
omits: average annual wage (from OFLC LCA disclosures), population,
density, rent, and local labor-market indicators. Joining on
STATE + CITY lets us re-run the explainability test with those
variables on the right-hand side and measure whether they move the
ceiling.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

USCIS_FEATURES = Path("data/processed/h1b_features.parquet")
EXTERNAL_RAW = Path("data/raw/lca_city_enrichment.csv")
OUT_PATH = Path("data/processed/h1b_city_merged.parquet")

# Wages above this are data-quality artifacts (hourly / annual unit mixing
# and a handful of clear outliers). ~$500k/yr covers the tail of legitimate
# H-1B wages; anything above is dropped before averaging.
WAGE_HARD_CAP = 500_000


def aggregate_uscis(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["state", "city"], as_index=False).agg(
        total_petitions=("total_petitions", "sum"),
        total_approvals=("total_approvals", "sum"),
        total_denials=("total_denials", "sum"),
        n_employers=("employer", "nunique"),
        share_stem=("is_stem", "mean"),
        share_continuing=("share_continuing", "mean"),
        region=("region", "first"),
    )
    g["approval_rate"] = g["total_approvals"] / g["total_petitions"]
    g["log_petitions"] = np.log1p(g["total_petitions"])
    g["log_employers"] = np.log1p(g["n_employers"])
    return g


def aggregate_external(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["EMPLOYER_STATE"] = df["EMPLOYER_STATE"].astype(str).str.upper().str.strip()
    df["EMPLOYER_CITY"] = df["EMPLOYER_CITY"].astype(str).str.upper().str.strip()

    df.loc[df["AVG_ANNUAL_WAGE"] > WAGE_HARD_CAP, "AVG_ANNUAL_WAGE"] = np.nan

    g = df.groupby(["EMPLOYER_STATE", "EMPLOYER_CITY"], as_index=False).agg(
        avg_wage=("AVG_ANNUAL_WAGE", "mean"),
        lca_applications=("LCA_APPLICATIONS", "sum"),
        population=("POPULATION", "first"),
        density=("DENSITY", "first"),
        avg_rent=("AVG_RENT_2022", "first"),
        employed_pct=("EMPLOYED_PCT", "first"),
        unemployed_z=("UNEMPLOYED_Z", "first"),
    )
    g = g.rename(columns={"EMPLOYER_STATE": "state", "EMPLOYER_CITY": "city"})

    g["log_wage"] = np.log1p(g["avg_wage"])
    g["log_population"] = np.log1p(g["population"])
    g["log_density"] = np.log1p(g["density"])
    g["log_rent"] = np.log1p(g["avg_rent"])
    g["log_lca"] = np.log1p(g["lca_applications"])
    return g


def main() -> None:
    uscis = aggregate_uscis(pd.read_parquet(USCIS_FEATURES))
    external = aggregate_external(pd.read_csv(EXTERNAL_RAW))

    merged = uscis.merge(external, on=["state", "city"], how="inner")

    # Drop cities with missing external features so the same N is compared
    # across structural vs. enriched models (fair ceiling comparison).
    required = ["avg_wage", "population", "density", "avg_rent", "employed_pct"]
    merged = merged.dropna(subset=required).reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_PATH, index=False)

    print(f"USCIS city rows:    {len(uscis):,}")
    print(f"external city rows: {len(external):,}")
    print(f"inner-join rows:    {len(merged):,}")
    print(
        f"merged coverage of USCIS petitions: "
        f"{merged['total_petitions'].sum() / uscis['total_petitions'].sum():.1%}"
    )
    print(f"wrote → {OUT_PATH}")


if __name__ == "__main__":
    main()
