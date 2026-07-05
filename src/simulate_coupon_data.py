"""Generate a synthetic coupon-campaign dataset for causal inference."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-values))


def generate_users(n_users: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    user_id = np.arange(1, n_users + 1)

    city_tier = rng.choice([1, 2, 3], size=n_users, p=[0.34, 0.46, 0.20])
    tenure_months = rng.integers(3, 49, size=n_users)
    weekday_share = rng.beta(4.2, 3.8, size=n_users)
    coupon_sensitivity = rng.beta(3.0, 4.2, size=n_users)
    historical_freq = rng.poisson(5.2 + 1.15 * (city_tier == 1) + 1.4 * weekday_share)
    historical_freq = np.clip(historical_freq, 1, None)
    pre_gmv_slope = rng.normal(0.012 + 0.006 * (city_tier == 1), 0.035, size=n_users)
    avg_order_value = rng.lognormal(mean=3.65 + 0.08 * (city_tier == 1), sigma=0.28, size=n_users)
    historical_gmv = historical_freq * avg_order_value * rng.normal(4.0, 0.26, size=n_users)

    logit = (
        -1.15
        + 0.55 * np.log1p(historical_gmv / 100)
        + 0.48 * weekday_share
        + 0.42 * coupon_sensitivity
        + 0.28 * (city_tier == 1)
        + 0.18 * pre_gmv_slope * 10
    )
    propensity = sigmoid(logit)
    treated = rng.binomial(1, propensity)

    natural_growth = (
        0.034
        + 0.018 * (city_tier == 1)
        + 0.014 * weekday_share
        + 0.22 * pre_gmv_slope
        + rng.normal(0, 0.025, size=n_users)
    )
    pre_weekday_gmv = historical_gmv * rng.normal(0.245, 0.025, size=n_users)

    return pd.DataFrame(
        {
            "user_id": user_id,
            "treated": treated,
            "propensity_true": propensity,
            "city_tier": city_tier,
            "tenure_months": tenure_months,
            "historical_gmv_4w": historical_gmv,
            "historical_purchase_freq_4w": historical_freq,
            "pre_gmv_slope": pre_gmv_slope,
            "weekday_share": weekday_share,
            "coupon_sensitivity": coupon_sensitivity,
            "pre_weekday_gmv": pre_weekday_gmv,
            "natural_growth": natural_growth,
        }
    )


def expand_periods(users: pd.DataFrame, treatment_effect: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 101)
    rows: list[pd.DataFrame] = []

    for period, is_post in [("pre", 0), ("post", 1)]:
        frame = users.copy()
        frame["period"] = period
        frame["post"] = is_post
        if is_post:
            noise = rng.normal(0, 0.035, size=len(frame))
            effect = frame["treated"] * treatment_effect * frame["coupon_sensitivity"].clip(0.35, 1.0)
            frame["weekday_gmv"] = frame["pre_weekday_gmv"] * (1 + frame["natural_growth"] + effect + noise)
            frame["orders"] = np.maximum(
                1,
                np.round(frame["historical_purchase_freq_4w"] * (0.28 + frame["natural_growth"] + effect / 2)),
            )
        else:
            frame["weekday_gmv"] = frame["pre_weekday_gmv"]
            frame["orders"] = np.maximum(1, np.round(frame["historical_purchase_freq_4w"] * 0.28))
        rows.append(frame)

    panel = pd.concat(rows, ignore_index=True)
    panel["weekday_gmv"] = panel["weekday_gmv"].clip(lower=1)
    panel["orders"] = panel["orders"].astype(int)
    return panel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_coupon_panel.csv"))
    parser.add_argument("--n-users", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--treatment-effect", type=float, default=0.147)
    args = parser.parse_args()

    users = generate_users(args.n_users, args.seed)
    panel = expand_periods(users, args.treatment_effect, args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False)
    print(f"Saved synthetic coupon panel: {args.output}")
    print(f"Rows: {len(panel):,}; users: {panel['user_id'].nunique():,}")
    print(f"Treatment share: {users['treated'].mean():.1%}")


if __name__ == "__main__":
    main()
