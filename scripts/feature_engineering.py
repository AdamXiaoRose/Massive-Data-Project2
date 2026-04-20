"""Build the modeling feature table from the cleaned parquet.

The modeling target is `approval_rate`. Features are limited to what the
USCIS public file exposes: industry, state, zip-region, application mix,
and crude employer-size buckets. The downstream story in `analysis.py`
depends on keeping this feature set *honest* about what is missing
(wages, job titles, attorney, RFE history).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

IN_PATH = Path("data/processed/h1b_clean.parquet")
OUT_PATH = Path("data/processed/h1b_features.parquet")

STEM_NAICS_PREFIXES = {"51", "54", "33", "52", "61"}

CENSUS_REGION = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast",
    "NH": "Northeast", "RI": "Northeast", "VT": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest",
    "WI": "Midwest", "IA": "Midwest", "KS": "Midwest", "MN": "Midwest",
    "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    "DE": "South", "FL": "South", "GA": "South", "MD": "South",
    "NC": "South", "SC": "South", "VA": "South", "DC": "South",
    "WV": "South", "AL": "South", "KY": "South", "MS": "South",
    "TN": "South", "AR": "South", "LA": "South", "OK": "South", "TX": "South",
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West", "NV": "West",
    "NM": "West", "UT": "West", "WY": "West", "AK": "West", "CA": "West",
    "HI": "West", "OR": "West", "WA": "West",
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["is_stem"] = df["naics_code"].str[:2].isin(STEM_NAICS_PREFIXES).astype(int)
    df["region"] = df["state"].map(CENSUS_REGION).fillna("Other")

    # Application mix: fraction of continuing vs initial petitions.
    initial = df["initial_approval"] + df["initial_denial"]
    continuing = df["continuing_approval"] + df["continuing_denial"]
    df["share_continuing"] = continuing / df["total_petitions"]
    df["share_initial"] = initial / df["total_petitions"]

    # Employer size proxy — bucketed log volume for this filing.
    df["log_petitions"] = np.log1p(df["total_petitions"])
    df["size_bucket"] = pd.cut(
        df["total_petitions"],
        bins=[0, 1, 5, 25, 100, np.inf],
        labels=["single", "small", "medium", "large", "mega"],
        include_lowest=True,
    ).astype(str)

    # Employer-level volume across the full file (captures repeat filers).
    employer_totals = (
        df.groupby("employer")["total_petitions"].sum().rename("employer_total")
    )
    df = df.join(employer_totals, on="employer")
    df["log_employer_total"] = np.log1p(df["employer_total"])

    df["near_perfect"] = (df["approval_rate"] >= 0.999).astype(int)
    df["any_denial"] = (df["total_denials"] > 0).astype(int)

    return df


def main() -> None:
    df = pd.read_parquet(IN_PATH)
    features = build_features(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(OUT_PATH, index=False)
    print(
        f"wrote {len(features):,} rows with {features.shape[1]} columns → {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
