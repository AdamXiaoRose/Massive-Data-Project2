"""Descriptive analysis and figures that frame the core finding.

Question: Can the USCIS public release explain H-1B approval outcomes?
Answer (from the numbers this script produces): no — the file captures
*where* and *who* files, but the variance that matters lives inside the
case files (wages, job titles, RFE history, attorney). Every figure
below is built to make that visible.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

FEATURES = Path("data/processed/h1b_features.parquet")
MERGED = Path("data/processed/h1b_city_merged.parquet")
RESIDUALS = Path("outputs/tables/residuals.parquet")
CITY_METRICS = Path("outputs/tables/model_metrics_city.json")
TABLES = Path("outputs/tables")
FIGURES = Path("outputs/figures")

plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight", "font.size": 10})


def approval_by_state(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("state").agg(
        petitions=("total_petitions", "sum"),
        approvals=("total_approvals", "sum"),
    )
    g["approval_rate"] = g["approvals"] / g["petitions"]
    return g.sort_values("approval_rate").reset_index()


def approval_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("naics_label").agg(
        petitions=("total_petitions", "sum"),
        approvals=("total_approvals", "sum"),
    )
    g["approval_rate"] = g["approvals"] / g["petitions"]
    g = g[g["petitions"] >= 100]
    return g.sort_values("approval_rate").reset_index()


def plot_state(df_state: pd.DataFrame) -> Path:
    top_bottom = pd.concat([df_state.head(10), df_state.tail(10)])
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top_bottom["state"], top_bottom["approval_rate"], color="#2b7a78")
    ax.axvline(df_state["approval_rate"].mean(), ls="--", c="grey", label="mean")
    ax.set_xlabel("Approval rate")
    ax.set_title("H-1B approval rate by state (10 lowest + 10 highest)")
    ax.legend()
    out = FIGURES / "approval_by_state.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_industry(df_ind: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(9, 6))
    labels = df_ind["naics_label"].str.slice(0, 45)
    ax.barh(labels, df_ind["approval_rate"], color="#3f51b5")
    ax.axvline(df_ind["approval_rate"].mean(), ls="--", c="grey", label="mean")
    ax.set_xlabel("Approval rate")
    ax.set_title("H-1B approval rate by NAICS industry (≥100 petitions)")
    ax.legend()
    out = FIGURES / "approval_by_industry.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_target_distribution(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["approval_rate"], bins=50, color="#c0392b", alpha=0.85)
    ax.set_xlabel("Approval rate")
    ax.set_ylabel("Employer filings")
    share_perfect = (df["approval_rate"] >= 0.999).mean()
    ax.set_title(
        f"Approval rate distribution — {share_perfect:.0%} of rows ≥ 99.9%"
    )
    out = FIGURES / "target_distribution.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_model_scores(metrics_path: Path) -> Path:
    import json
    data = json.loads(metrics_path.read_text())
    df = pd.DataFrame(data["results"])
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(df["model"], df["r2"], color=["#7f8c8d", "#2980b9", "#27ae60"][: len(df)])
    ax.axhline(0, c="black", lw=0.6)
    ax.set_ylabel("Test R²")
    ax.set_title("Model explanatory power on public USCIS data")
    for bar, val in zip(bars, df["r2"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:+.3f}",
                ha="center", va="bottom" if val >= 0 else "top", fontsize=9)
    out = FIGURES / "model_scores.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_feature_importance(path: Path) -> Path:
    imp = pd.read_csv(path).head(15)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(imp["feature"][::-1], imp["importance"][::-1], color="#16a085")
    ax.set_xlabel("Random Forest importance")
    ax.set_title("Top 15 features — none dominate")
    out = FIGURES / "feature_importance.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def variance_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """How much of approval_rate variance lives between vs. within groups?"""
    rows = []
    total_var = df["approval_rate"].var()
    for col in ["state", "region", "naics_code", "size_bucket"]:
        group_means = df.groupby(col)["approval_rate"].mean()
        between = ((df[col].map(group_means) - df["approval_rate"].mean()) ** 2).mean()
        rows.append({
            "grouping": col,
            "between_variance_share": float(between / total_var),
            "n_groups": int(df[col].nunique()),
        })
    return pd.DataFrame(rows)


def plot_enrichment_delta(metrics_path: Path) -> Path:
    import json
    data = json.loads(metrics_path.read_text())
    df = pd.DataFrame(data["results"])
    pivot = df.pivot(index="model", columns="spec", values="r2").reset_index()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = range(len(pivot))
    w = 0.38
    ax.bar([i - w / 2 for i in x], pivot["structural"], width=w,
           label="structural (USCIS only)", color="#95a5a6")
    ax.bar([i + w / 2 for i in x], pivot["enriched"], width=w,
           label="+ wage + local economy", color="#16a085")
    ax.axhline(0, c="black", lw=0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot["model"])
    ax.set_ylabel("Test R² (city-level approval rate)")
    ax.set_title("Adding wage & local economy (LCA + Census) barely lifts the ceiling")
    for i, (s, e) in enumerate(zip(pivot["structural"], pivot["enriched"])):
        ax.text(i - w / 2, s, f"{s:+.3f}", ha="center",
                va="bottom" if s >= 0 else "top", fontsize=8)
        ax.text(i + w / 2, e, f"{e:+.3f}", ha="center",
                va="bottom" if e >= 0 else "top", fontsize=8)
    ax.legend()
    out = FIGURES / "enrichment_delta.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_wage_vs_approval(merged: pd.DataFrame) -> Path:
    df = merged.dropna(subset=["avg_wage", "approval_rate"]).copy()
    df = df[df["total_petitions"] >= 10]  # noisy cities out for readability
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(df["avg_wage"], df["approval_rate"], s=6, alpha=0.35, color="#2980b9")
    ax.set_xscale("log")
    ax.set_xlabel("Average annual wage (log, $)")
    ax.set_ylabel("City-level approval rate")
    corr = df[["avg_wage", "approval_rate"]].corr().iloc[0, 1]
    ax.set_title(
        f"Wages don't separate approved from denied cities "
        f"(Pearson r = {corr:+.3f}, n={len(df):,})"
    )
    out = FIGURES / "wage_vs_approval.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_residual_heterogeneity(res: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(res["residual"], bins=60, color="#8e44ad", alpha=0.85)
    rmse = (res["residual"] ** 2).mean() ** 0.5
    ax.set_title(
        f"Residuals after best model — RMSE={rmse:.3f}, "
        f"{(res['residual'].abs() > 0.05).mean():.0%} off by >5 pts"
    )
    ax.set_xlabel("residual (y_true − y_pred)")
    out = FIGURES / "residuals.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(FEATURES)

    state_tbl = approval_by_state(df)
    industry_tbl = approval_by_industry(df)
    variance_tbl = variance_decomposition(df)

    state_tbl.to_csv(TABLES / "approval_by_state.csv", index=False)
    industry_tbl.to_csv(TABLES / "approval_by_industry.csv", index=False)
    variance_tbl.to_csv(TABLES / "variance_decomposition.csv", index=False)

    plot_state(state_tbl)
    plot_industry(industry_tbl)
    plot_target_distribution(df)

    metrics_path = TABLES / "model_metrics.json"
    if metrics_path.exists():
        plot_model_scores(metrics_path)
    importance_path = TABLES / "feature_importance.csv"
    if importance_path.exists():
        plot_feature_importance(importance_path)
    if RESIDUALS.exists():
        plot_residual_heterogeneity(pd.read_parquet(RESIDUALS))

    if CITY_METRICS.exists():
        plot_enrichment_delta(CITY_METRICS)
    if MERGED.exists():
        plot_wage_vs_approval(pd.read_parquet(MERGED))

    print("variance share captured by each grouping:")
    print(variance_tbl.to_string(index=False))
    print("\nanalysis outputs written under outputs/")


if __name__ == "__main__":
    main()
