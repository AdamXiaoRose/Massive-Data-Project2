"""Load raw USCIS H-1B FY2024 data and produce a clean parquet file.

Raw file is UTF-16 LE with BOM. Column names contain spaces from
the encoding; we rename to snake_case and drop rows that carry no
petition outcomes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/h1b_fy2024.csv")
OUT_PATH = Path("data/processed/h1b_clean.parquet")

RENAME = {
    "Line by line": "row_id",
    "Fiscal Year": "fiscal_year",
    "Employer (Petitioner) Name": "employer",
    "Tax ID": "tax_id",
    "Industry (NAICS) Code": "naics",
    "Petitioner City": "city",
    "Petitioner State": "state",
    "Petitioner Zip Code": "zip",
    "Initial Approval": "initial_approval",
    "Initial Denial": "initial_denial",
    "Continuing Approval": "continuing_approval",
    "Continuing Denial": "continuing_denial",
    "Total Approvals": "total_approvals",
    "Total Denials": "total_denials",
    "Approval Rate": "approval_rate",
    "Denial Rate": "denial_rate",
}


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-16", sep=",")
    df.columns = [c.strip() for c in df.columns]
    return df.rename(columns=RENAME)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["fiscal_year"] = df["fiscal_year"].astype("Int64")
    df["employer"] = df["employer"].astype(str).str.strip().str.upper()
    df["state"] = df["state"].astype(str).str.strip().str.upper()
    df["city"] = df["city"].astype(str).str.strip().str.upper()

    # NAICS arrives as "54 - Professional, Scientific, ..." — split code from label.
    naics = df["naics"].astype(str).str.split(" - ", n=1, expand=True)
    df["naics_code"] = naics[0].str.strip()
    df["naics_label"] = naics[1].str.strip() if naics.shape[1] > 1 else ""

    # Zip → 5-digit string, keep first 3 digits as a region proxy.
    df["zip"] = (
        df["zip"].astype(str).str.extract(r"(\d+)")[0].str.zfill(5)
    )
    df["zip3"] = df["zip"].str[:3]

    count_cols = [
        "initial_approval",
        "initial_denial",
        "continuing_approval",
        "continuing_denial",
        "total_approvals",
        "total_denials",
    ]
    for c in count_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["total_petitions"] = df["total_approvals"] + df["total_denials"]

    # Recompute approval rate exactly — the raw column nudges 0 and 1
    # by ~1e-6 for modeling convenience, which distorts averages.
    df["approval_rate"] = df["total_approvals"] / df["total_petitions"].where(
        df["total_petitions"] > 0
    )

    df = df[df["total_petitions"] > 0].copy()
    df = df[df["state"].str.len() == 2]

    known_employer = df["employer"].ne("UNKNOWN")
    df["employer_known"] = known_employer

    return df.reset_index(drop=True)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    clean_df = clean(raw)
    clean_df.to_parquet(OUT_PATH, index=False)
    print(f"wrote {len(clean_df):,} rows → {OUT_PATH}")


if __name__ == "__main__":
    main()
