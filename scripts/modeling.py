"""Fit OLS, Random Forest, and XGBoost on the engineered features.

The point of the modeling stage is *not* to produce a good predictor —
prior runs established that isn't possible from this file alone. The
point is to quantify the ceiling: how much of the variance in
approval_rate can any of these models pull out of USCIS public data?
Outputs feed into `analysis.py`, which frames the ceiling as evidence
that approval outcomes depend on variables not in the public release.
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
except ImportError:  # xgboost is optional
    HAS_XGB = False

IN_PATH = Path("data/processed/h1b_features.parquet")
METRICS_PATH = Path("outputs/tables/model_metrics.json")
IMPORTANCE_PATH = Path("outputs/tables/feature_importance.csv")
RESIDUAL_PATH = Path("outputs/tables/residuals.parquet")

NUMERIC = ["share_continuing", "log_petitions", "log_employer_total", "is_stem"]
CATEGORICAL = ["state", "naics_code", "region", "size_bucket"]
TARGET = "approval_rate"


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=True),
                CATEGORICAL,
            ),
        ]
    )


def split(df: pd.DataFrame):
    X = df[NUMERIC + CATEGORICAL]
    y = df[TARGET]
    return train_test_split(X, y, test_size=0.2, random_state=42)


def evaluate(name: str, model, X_train, X_test, y_train, y_test) -> dict:
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return {
        "model": name,
        "r2": float(r2_score(y_test, preds)),
        "mae": float(mean_absolute_error(y_test, preds)),
        "mean_target": float(y_test.mean()),
        "std_target": float(y_test.std()),
    }, preds


def run_models(df: pd.DataFrame):
    X_train, X_test, y_train, y_test = split(df)
    pre = build_preprocessor()

    ols = Pipeline([("pre", pre), ("model", LinearRegression())])
    rf = Pipeline([
        ("pre", pre),
        ("model", RandomForestRegressor(
            n_estimators=200, max_depth=12, n_jobs=-1, random_state=42
        )),
    ])

    results = []
    preds_by_model: dict[str, np.ndarray] = {}

    for name, pipe in [("OLS", ols), ("RandomForest", rf)]:
        metrics, preds = evaluate(name, pipe, X_train, X_test, y_train, y_test)
        results.append(metrics)
        preds_by_model[name] = preds
        print(f"{name:15s} R2={metrics['r2']:+.4f}  MAE={metrics['mae']:.4f}")

    if HAS_XGB:
        xgb = Pipeline([
            ("pre", pre),
            ("model", XGBRegressor(
                n_estimators=400, max_depth=6, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9, random_state=42,
                tree_method="hist", n_jobs=-1,
            )),
        ])
        metrics, preds = evaluate("XGBoost", xgb, X_train, X_test, y_train, y_test)
        results.append(metrics)
        preds_by_model["XGBoost"] = preds
        print(f"{'XGBoost':15s} R2={metrics['r2']:+.4f}  MAE={metrics['mae']:.4f}")
    else:
        xgb = None
        print("xgboost not installed — skipping")

    # Feature importance from RandomForest (readable + stable across runs).
    rf_fitted = rf.named_steps["model"]
    feat_names = rf.named_steps["pre"].get_feature_names_out()
    importance = (
        pd.DataFrame({"feature": feat_names, "importance": rf_fitted.feature_importances_})
        .sort_values("importance", ascending=False)
        .head(30)
    )

    # Residuals from the best-performing non-linear model for analysis.py.
    best_name = max(preds_by_model, key=lambda k: r2_score(y_test, preds_by_model[k]))
    residuals = pd.DataFrame({
        "y_true": y_test.values,
        "y_pred": preds_by_model[best_name],
        "state": X_test["state"].values,
        "naics_code": X_test["naics_code"].values,
        "size_bucket": X_test["size_bucket"].values,
    })
    residuals["residual"] = residuals["y_true"] - residuals["y_pred"]

    return results, importance, residuals, best_name


def main() -> None:
    df = pd.read_parquet(IN_PATH)
    results, importance, residuals, best = run_models(df)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w") as f:
        json.dump({"best_model": best, "results": results}, f, indent=2)
    importance.to_csv(IMPORTANCE_PATH, index=False)
    residuals.to_parquet(RESIDUAL_PATH, index=False)
    print(f"wrote metrics → {METRICS_PATH}")


if __name__ == "__main__":
    main()
