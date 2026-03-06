
# Incremental Conversion Modeling (Uplift Analysis)
https://github.com/Juana-Zhang/Casual-Inference/blob/main/Project_Incremental_Conversion_Modeling_(Uplift_Analysis).ipynb

### **Business Context**
Traditional A/B testing tells us if a campaign works on average, but it doesn't tell us **who** to target. To optimize marketing efficiency, we categorize users into four segments based on the Uplift framework:
* **Persuadables**: Users who only convert *if* they see an ad. This is the **primary target** for maximizing ROI.
* **Sure Things**: Users who will convert whether they see an ad or not. Targeting them is a waste of budget.
* **Lost Causes**: Users who will not convert even if they see an ad.
* **Sleeping Dogs**: Users who might be discouraged by ads (e.g., unsubscribing). Targeting them is counterproductive.


### **Business Goal (BG)**
The objective is to **maximize Marketing ROI** by identifying the **"Persuadable"** user segment. By predicting the **Incremental Lift (Uplift)** for each individual, we can optimize budget allocation and focus spend only on users whose behavior is genuinely changed by the intervention.

# Propensity Score Match Project - Coupon
https://github.com/Juana-Zhang/Casual-Inference/blob/main/Project_Evaluating_Marketing_Impact_via_Propensity_Score_Matching_(PSM).ipynb
### **Project Impact & Executive Summary**
* **Precision Targeting**: Successfully identified a high-responsiveness segment (Top Decile) exhibiting an incremental lift **7.4 times higher** than the random-targeting baseline.
* **ROI Maximization**: Focusing spend on "Persuadables" captures the majority of incremental conversions while reducing waste on "Sure Things" or "Lost Causes".
* **Risk Mitigation**: The analysis identified segments (e.g., Decile 7) where advertising had a **negative effect**, allowing the business to prevent potential churn among "Sleeping Dogs".
* **Causal Insight**: This framework transforms marketing into a precision revenue-driver by quantifying the true **causal impact** of ads.

# Causal Inference: Uplift Attribution via Propensity Score Matching (PSM)

## 1. Executive Summary
This project addresses a critical challenge in marketing analytics: **How do we measure the true incremental lift of a promotion when voucher distribution is non-random?** By simulating a dataset with known ground truth and intentional **Selection Bias**, I implemented a **Propensity Score Matching (PSM)** pipeline to isolate the treatment effect from user-level confounders.

---

## 2. Problem Statement: The Selection Bias Trap
In many tech scenarios, vouchers are targeted toward high-value or active users. A naive comparison of GMV between treated and untreated groups leads to an overestimation of the campaign's success. 

In this simulation:
* **Confounders ($X$)**: App frequency, historical GMV, and membership status.
* **Naive Lift**: **43.24 units** (inflated by user activity bias).
* **True Causal Lift**: **30.00 units** (ground truth).



---

## 3. Methodology & Technical Workflow

### * I. Data Simulation (Ground Truth Construction)
To validate the model, I generated 2,000 synthetic records where the treatment assignment ($T$) follows a **Logistic Function** based on user features.
* $P(T=1|X) = \sigma(-5 + 0.3 \cdot \text{freq} + 0.002 \cdot \text{gmv} + 1.5 \cdot \text{member})$.

### * II. Propensity Score Estimation
I trained a **Logistic Regression** model using the full dataset to estimate the likelihood of each user receiving a treatment. 
* **Note**: No Train/Test split was performed to ensure a maximum **Matching Pool**, as the objective is internal validity (inference) rather than external prediction.



### * III. Nearest Neighbor Matching with Bias Adjustment
Every treated unit was matched with a control "twin" using the `causalinference` library.
* **Matching with Replacement**: High-quality control units can be reused to minimize distance between pairs.
* **Bias Adjustment (`bias_adj=True`)**: Implemented a secondary **Linear Regression Adjustment** on matched sets to remove residual bias from continuous variables like historical spend.

---

## 4. Evaluation & Balance Verification

### * Covariate Balance Check
A critical step in PSM is ensuring the groups are comparable. I verified the quality by calculating the **Standardized Mean Difference (Nor-diff)**.

| Feature | Pre-Match Nor-diff | Post-Match Nor-diff | Status |
| :--- | :--- | :--- | :--- |
| **App Freq** | **0.758** | **< 0.1** | **Balanced** |
| **Hist GMV** | 0.179 | < 0.1 | Balanced |
| **Member** | 0.553 | < 0.1 | Balanced |



### * Causal Effect Results
The model successfully corrected for selection bias, effectively recovering the simulated ground truth.

| Metric | Result | Interpretation |
| :--- | :--- | :--- |
| **Simulated True Lift** | 30.00 | Ground Truth |
| **PSM Estimated ATE** | **29.x ~ 30.x** | Consistent with true effect |
| **P-Value** | < 0.05 | Statistically Significant |

---

## 5. Business Implications
By stripping away the **13.07 units of bias**, this analysis prevents the business from over-allocating budget to users who would have spent anyway. This framework allows for a clean **Incremental ROI (iROI)** calculation, ensuring marketing efficiency is driven by incremental growth rather than pre-existing behavior.
