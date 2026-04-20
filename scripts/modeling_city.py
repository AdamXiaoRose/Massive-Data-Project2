"""City-level ceiling test: structural features vs. structural + wage/local-economy.

Uses the merged USCIS × LCA × Census file produced by `merge_external.py`.
Runs the same three model families as `modeling.py`, but twice per family:
once on structural features only, once with wage + local-economy
variables added. The Δ R² between the two is the punchline — it
measures how much of the previously-unexplained variance in
approval_rate becomes explainable once the variables missing from
USCIS are supplied by OFLC LCA and Census.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

IN_PATH = Path("data/processed/h1b_city_merged.parquet")
METRICS_PATH = Path("outputs/tables/model_metrics_city.json")
IMPORTANCE_PATH = Path("outputs/tables/feature_importance_city.csv")

STRUCTURAL_NUM = ["share_stem", "share_continuing", "log_petitions", "log_employers"]
STRUCTURAL_CAT = ["state", "region"]
ENRICHMENT = ["log_wage", "log_population", "log_density", "log_rent",
              "employed_pct", "unemployed_z", "log_lca"]

TARGET = "approval_rate"


def build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", "passthrough", numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10,
                              sparse_output=True), categorical),
    ])


def build_models(pre: ColumnTransformer) -> dict[str, Pipeline]:
    models = {
        "OLS": Pipeline([("pre", pre), ("m", LinearRegression())]),
        "RandomForest": Pipeline([("pre", pre), ("m", RandomForestRegressor(
            n_estimators=300, max_depth=12, n_jobs=-1, random_state=42
        ))]),
    }
    if HAS_XGB:
        models["XGBoost"] = Pipeline([("pre", pre), ("m", XGBRegressor(
            n_estimators=500, max_depth=5, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, tree_method="hist",
            n_jobs=-1, random_state=42,
        ))])
    return models


def run_spec(name: str, df: pd.DataFrame, numeric: list[str],
             categorical: list[str]) -> tuple[list[dict], pd.DataFrame]:
    X = df[numeric + categorical]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pre = build_preprocessor(numeric, categorical)
    rows = []
    rf_importance = None

    for model_name, pipe in build_models(pre).items():
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        r2 = float(r2_score(y_test, pred))
        mae = float(mean_absolute_error(y_test, pred))
        rows.append({
            "spec": name, "model": model_name,
            "r2": r2, "mae": mae, "n_train": len(X_train), "n_test": len(X_test),
        })
        print(f"[{name:11s}] {model_name:13s} R2={r2:+.4f}  MAE={mae:.4f}")

        if model_name == "RandomForest":
            feats = pipe.named_steps["pre"].get_feature_names_out()
            rf_importance = (
                pd.DataFrame({
                    "spec": name, "feature": feats,
                    "importance": pipe.named_steps["m"].feature_importances_,
                })
                .sort_values("importance", ascending=False)
                .head(20)
            )

    return rows, rf_importance


def main() -> None:
    df = pd.read_parquet(IN_PATH)
    print(f"loaded {len(df):,} merged city rows")

    all_rows = []
    all_imp = []

    print("\n--- Spec A: structural only (USCIS fields) ---")
    rows, imp = run_spec("structural", df, STRUCTURAL_NUM, STRUCTURAL_CAT)
    all_rows.extend(rows)
    all_imp.append(imp)

    print("\n--- Spec B: structural + wage + local economy ---")
    rows, imp = run_spec("enriched", df,
                         STRUCTURAL_NUM + ENRICHMENT, STRUCTURAL_CAT)
    all_rows.extend(rows)
    all_imp.append(imp)

    results = pd.DataFrame(all_rows)
    delta = (
        results.pivot(index="model", columns="spec", values="r2")
        .assign(delta=lambda x: x["enriched"] - x["structural"])
        .reset_index()
    )
    print("\nΔ R² (enriched − structural):")
    print(delta.to_string(index=False))

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w") as f:
        json.dump({
            "n_cities": len(df),
            "results": all_rows,
            "delta_r2": delta.to_dict(orient="records"),
        }, f, indent=2)
    pd.concat(all_imp, ignore_index=True).to_csv(IMPORTANCE_PATH, index=False)
    print(f"\nwrote → {METRICS_PATH}")


if __name__ == "__main__":
    main()
