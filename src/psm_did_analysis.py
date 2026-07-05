"""Estimate coupon incrementality using PSM plus Difference-in-Differences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


COVARIATES = [
    "historical_gmv_4w",
    "historical_purchase_freq_4w",
    "pre_gmv_slope",
    "weekday_share",
    "coupon_sensitivity",
    "tenure_months",
    "city_tier",
]


def user_level_features(panel: pd.DataFrame) -> pd.DataFrame:
    pre = panel[panel["period"].eq("pre")].copy()
    return pre[["user_id", "treated", *COVARIATES, "pre_weekday_gmv"]].drop_duplicates("user_id")


def estimate_propensity(users: pd.DataFrame) -> pd.DataFrame:
    users = users.copy()
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(users[COVARIATES])
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(x_scaled, users["treated"])
    users["propensity_score"] = model.predict_proba(x_scaled)[:, 1]
    return users


def match_nearest_neighbor(users: pd.DataFrame, caliper: float = 0.035) -> pd.DataFrame:
    treated = users[users["treated"].eq(1)].copy()
    control = users[users["treated"].eq(0)].copy()

    nn = NearestNeighbors(n_neighbors=1)
    nn.fit(control[["propensity_score"]])
    distances, indices = nn.kneighbors(treated[["propensity_score"]])

    matches = treated[["user_id", "propensity_score"]].rename(
        columns={"user_id": "treated_user_id", "propensity_score": "treated_ps"}
    )
    matched_control = control.iloc[indices.flatten()][["user_id", "propensity_score"]].reset_index(drop=True)
    matches = matches.reset_index(drop=True)
    matches["control_user_id"] = matched_control["user_id"]
    matches["control_ps"] = matched_control["propensity_score"]
    matches["ps_distance"] = distances.flatten()
    matches = matches[matches["ps_distance"].le(caliper)].copy()
    matches["pair_id"] = np.arange(1, len(matches) + 1)
    return matches


def standardized_mean_differences(users: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    treated_matched = matches[["pair_id", "treated_user_id"]].merge(
        users,
        left_on="treated_user_id",
        right_on="user_id",
        how="left",
    )
    control_matched = matches[["pair_id", "control_user_id"]].merge(
        users,
        left_on="control_user_id",
        right_on="user_id",
        how="left",
    )
    matched = pd.concat([treated_matched, control_matched], ignore_index=True)

    rows = []
    for cov in COVARIATES:
        for sample_name, sample in [("Before matching", users), ("After matching", matched)]:
            t = sample[sample["treated"].eq(1)][cov]
            c = sample[sample["treated"].eq(0)][cov]
            pooled_std = np.sqrt((t.var() + c.var()) / 2)
            smd = 0 if pooled_std == 0 else (t.mean() - c.mean()) / pooled_std
            rows.append({"covariate": cov, "sample": sample_name, "smd": smd, "abs_smd": abs(smd)})
    return pd.DataFrame(rows)


def did_estimates(panel: pd.DataFrame, matches: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    raw_pre = panel[panel["period"].eq("pre")]
    raw_post = panel[panel["period"].eq("post")]
    raw_pre_gap = (
        raw_pre[raw_pre["treated"].eq(1)]["weekday_gmv"].mean()
        / raw_pre[raw_pre["treated"].eq(0)]["weekday_gmv"].mean()
        - 1
    )
    raw_post_lift = (
        raw_post[raw_post["treated"].eq(1)]["weekday_gmv"].mean()
        / raw_post[raw_post["treated"].eq(0)]["weekday_gmv"].mean()
        - 1
    )

    treated_panel = matches[["pair_id", "treated_user_id"]].merge(
        panel,
        left_on="treated_user_id",
        right_on="user_id",
        how="left",
    )
    treated_panel["matched_group"] = "Treatment"

    control_panel = matches[["pair_id", "control_user_id"]].merge(
        panel,
        left_on="control_user_id",
        right_on="user_id",
        how="left",
    )
    control_panel["matched_group"] = "Matched control"

    matched_panel = pd.concat([treated_panel, control_panel], ignore_index=True)

    summary = (
        matched_panel.groupby(["matched_group", "period"])["weekday_gmv"]
        .mean()
        .reset_index()
        .pivot(index="matched_group", columns="period", values="weekday_gmv")
    )
    summary["absolute_change"] = summary["post"] - summary["pre"]
    summary["relative_change"] = summary["absolute_change"] / summary["pre"]

    treatment_change = summary.loc["Treatment", "relative_change"]
    control_change = summary.loc["Matched control", "relative_change"]
    did_relative_lift = treatment_change - control_change

    post = matched_panel[matched_panel["period"].eq("post")]
    psm_post_only_lift = (
        post[post["matched_group"].eq("Treatment")]["weekday_gmv"].mean()
        / post[post["matched_group"].eq("Matched control")]["weekday_gmv"].mean()
        - 1
    )

    pre = matched_panel[matched_panel["period"].eq("pre")]
    baseline_gap = (
        pre[pre["matched_group"].eq("Treatment")]["weekday_gmv"].mean()
        / pre[pre["matched_group"].eq("Matched control")]["weekday_gmv"].mean()
        - 1
    )

    metrics = {
        "matched_pairs": float(matches["pair_id"].nunique()),
        "treatment_pre_gmv": float(summary.loc["Treatment", "pre"]),
        "treatment_post_gmv": float(summary.loc["Treatment", "post"]),
        "control_pre_gmv": float(summary.loc["Matched control", "pre"]),
        "control_post_gmv": float(summary.loc["Matched control", "post"]),
        "treatment_relative_change": float(treatment_change),
        "control_relative_change": float(control_change),
        "did_relative_lift": float(did_relative_lift),
        "raw_pre_baseline_gap": float(raw_pre_gap),
        "raw_naive_post_lift": float(raw_post_lift),
        "psm_post_only_lift": float(psm_post_only_lift),
        "baseline_gap_after_matching": float(baseline_gap),
    }
    return matched_panel, metrics


def write_charts(matched_panel: pd.DataFrame, smd: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    trend = (
        matched_panel.groupby(["matched_group", "period"])["weekday_gmv"]
        .mean()
        .reset_index()
    )
    trend["period_order"] = trend["period"].map({"pre": 0, "post": 1})
    trend = trend.sort_values(["matched_group", "period_order"])

    plt.figure(figsize=(8.8, 5.2))
    for group, frame in trend.groupby("matched_group"):
        plt.plot(frame["period"], frame["weekday_gmv"], marker="o", linewidth=3, label=group)
    plt.title("Matched GMV Trend: Pre vs Post Campaign")
    plt.ylabel("Average weekday GMV per user")
    plt.xlabel("")
    plt.grid(axis="y", alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(fig_dir / "matched_gmv_trend.png", dpi=180)
    plt.close()

    smd_pivot = smd.pivot(index="covariate", columns="sample", values="abs_smd").sort_values(
        "Before matching",
        ascending=True,
    )
    ax = smd_pivot.plot(kind="barh", figsize=(9, 5.8), color=["#c65d4b", "#167d7f"])
    ax.axvline(0.1, color="#333333", linestyle="--", linewidth=1)
    ax.set_title("Covariate Balance Before and After PSM")
    ax.set_xlabel("Absolute standardized mean difference")
    ax.set_ylabel("")
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(fig_dir / "covariate_balance.png", dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/synthetic_coupon_panel.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    panel = pd.read_csv(args.input)
    users = estimate_propensity(user_level_features(panel))
    matches = match_nearest_neighbor(users)
    smd = standardized_mean_differences(users, matches)
    matched_panel, metrics = did_estimates(panel, matches)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    users.to_csv(args.output_dir / "user_propensity_scores.csv", index=False)
    matches.to_csv(args.output_dir / "psm_matched_pairs.csv", index=False)
    smd.to_csv(args.output_dir / "covariate_balance.csv", index=False)
    matched_panel.to_csv(args.output_dir / "matched_panel.csv", index=False)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    write_charts(matched_panel, smd, args.output_dir)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
