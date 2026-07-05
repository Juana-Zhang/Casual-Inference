# Coupon Incrementality with PSM + Difference-in-Differences

This repository contains a privacy-safe synthetic recreation of a marketplace coupon incrementality project. The case evaluates whether targeted coupon interventions generated true incremental GMV rather than subsidizing users who would have purchased anyway.

Open the local case-study page:

```text
case_study.html
```

## Case Summary

- Business question: Did weekday coupon targeting create incremental GMV among high-value users?
- Measurement issue: Treated users naturally had stronger baseline GMV and purchase frequency.
- Method: Propensity Score Matching (PSM) to build a comparable control group, followed by Difference-in-Differences (DID) to remove natural weekly demand movement.
- Result: The synthetic case reproduces a 6.8% net GMV lift after causal adjustment.

## Why PSM + DID

PSM helps address selection bias by matching coupon-targeted users with similar non-targeted users based on historical GMV, purchase frequency, pre-period GMV slope, weekday share, coupon sensitivity, tenure, and city tier.

DID is then used because matching alone does not remove time-varying shocks. If all high-value users naturally spend more during the campaign week, a post-period comparison would still overstate coupon impact. DID subtracts the matched control group's natural trend from the treatment group's observed lift.

## Key Results

| Metric | Result | Interpretation |
| :--- | ---: | :--- |
| Raw naive post-campaign lift | 24.3% | Inflated readout before causal adjustment |
| Treatment pre-to-post change | 12.1% | Total observed GMV movement among coupon users |
| Matched control natural trend | 5.3% | Baseline weekly movement among similar users |
| PSM + DID net GMV lift | 6.8% | Incremental effect attributable to the coupon |

## Reproduce

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the synthetic panel:

```bash
python src/simulate_coupon_data.py \
  --output data/synthetic_coupon_panel.csv \
  --n-users 12000 \
  --seed 42 \
  --treatment-effect 0.147
```

Run PSM + DID:

```bash
python src/psm_did_analysis.py \
  --input data/synthetic_coupon_panel.csv \
  --output-dir outputs
```

## Repository Structure

```text
.
├── case_study.html
├── data/
│   └── synthetic_coupon_panel.csv        # generated locally
├── outputs/
│   ├── figures/
│   │   ├── covariate_balance.png
│   │   └── matched_gmv_trend.png
│   ├── metrics.json
│   ├── covariate_balance.csv             # generated locally
│   ├── matched_panel.csv                  # generated locally
│   ├── psm_matched_pairs.csv              # generated locally
│   └── user_propensity_scores.csv         # generated locally
├── src/
│   ├── psm_did_analysis.py
│   └── simulate_coupon_data.py
├── Project_Evaluating_Marketing_Impact_via_Propensity_Score_Matching_(PSM).ipynb
└── Project_Incremental_Conversion_Modeling_(Uplift_Analysis).ipynb
```

## Public Data Note

The data in this repository is synthetic. It is calibrated to mirror the mechanics and headline result of a real growth analytics case, but it does not include proprietary user, coupon, transaction, or marketplace data.

## Additional Notebooks

This repository also contains earlier causal marketing analytics notebooks:

- `Project_Evaluating_Marketing_Impact_via_Propensity_Score_Matching_(PSM).ipynb`
- `Project_Incremental_Conversion_Modeling_(Uplift_Analysis).ipynb`
