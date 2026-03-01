# Incremental Conversion Modeling (Uplift Analysis)

### **Business Context**
Traditional A/B testing tells us if a campaign works on average, but it doesn't tell us **who** to target. To optimize marketing efficiency, we categorize users into four segments based on the Uplift framework:
* **Persuadables**: Users who only convert *if* they see an ad. This is the **primary target** for maximizing ROI.
* **Sure Things**: Users who will convert whether they see an ad or not. Targeting them is a waste of budget.
* **Lost Causes**: Users who will not convert even if they see an ad.
* **Sleeping Dogs**: Users who might be discouraged by ads (e.g., unsubscribing). Targeting them is counterproductive.


### **Business Goal (BG)**
The objective is to **maximize Marketing ROI** by identifying the **"Persuadable"** user segment. By predicting the **Incremental Lift (Uplift)** for each individual, we can optimize budget allocation and focus spend only on users whose behavior is genuinely changed by the intervention.



### **Project Impact & Executive Summary**
* **Precision Targeting**: Successfully identified a high-responsiveness segment (Top Decile) exhibiting an incremental lift **7.4 times higher** than the random-targeting baseline.
* **ROI Maximization**: Focusing spend on "Persuadables" captures the majority of incremental conversions while reducing waste on "Sure Things" or "Lost Causes".
* **Risk Mitigation**: The analysis identified segments (e.g., Decile 7) where advertising had a **negative effect**, allowing the business to prevent potential churn among "Sleeping Dogs".
* **Causal Insight**: This framework transforms marketing into a precision revenue-driver by quantifying the true **causal impact** of ads.
