"""
ControlPlane.ai — Cost Monitor
Tracks token spend, retries, and latency against a *learned baseline per use case* —
because a customer-support bot and a decision-support tool have very different
latency budgets and normal cost profiles (Round 2 brief: "different AI use cases
have very different risk tolerance and latency budgets"). A single global
threshold would either over-flag internal copilots or miss runaway customer-facing
calls, so baselines are learned per use_case rather than globally.
"""

import numpy as np
import pandas as pd

LATENCY_BUDGET_MS = {"customer_support": 800, "internal_copilot": 2500, "decision_support": 4000}


class CostMonitor:
    def __init__(self):
        self.baselines = {}  # use_case -> {"token_mean":..., "token_std":..., "latency_budget":...}
        self.is_fitted = False

    def fit(self, df):
        for uc, group in df.groupby("use_case"):
            self.baselines[uc] = {
                "token_mean": group["token_count"].mean(),
                "token_std": max(group["token_count"].std(), 1e-6),
                "retry_mean": group["retries"].mean(),
                "retry_std": max(group["retries"].std(), 1e-6),
                "latency_budget": LATENCY_BUDGET_MS.get(uc, 2000),
            }
        self.is_fitted = True

    def predict(self, df):
        """Adds cost_risk_score (0-100, higher = burning more compute/rework than expected)."""
        if not self.is_fitted:
            self.fit(df)

        scores = []
        for _, row in df.iterrows():
            uc = row["use_case"]
            base = self.baselines.get(uc, {
                "token_mean": 300, "token_std": 100, "retry_mean": 0.2, "retry_std": 0.5,
                "latency_budget": LATENCY_BUDGET_MS.get(uc, 2000),
            })
            token_z = (row["token_count"] - base["token_mean"]) / base["token_std"]
            retry_z = (row["retries"] - base["retry_mean"]) / base["retry_std"]
            latency_ratio = row["latency_ms"] / base["latency_budget"]

            # Combine: token/retry z-scores capture "burning more than usual",
            # latency_ratio captures "blowing the use-case's own budget"
            raw = 0.4 * max(token_z, 0) + 0.3 * max(retry_z, 0) + 0.3 * max(latency_ratio - 1, 0) * 10
            scores.append(raw)

        scores = np.array(scores)
        # Squash to 0-100 with a soft cap so a handful of extreme spikes don't
        # compress everything else near zero
        risk = 100 * (1 - np.exp(-scores / 4))

        result = df.copy()
        result["cost_risk_score"] = np.round(np.clip(risk, 0, 100), 1)
        result["cost_flag"] = (result["cost_risk_score"] > 55).astype(int)
        return result
