"""
ControlPlane.ai — Policy Engine (Governance Layer)
Combines Performance, Cost, and Responsibility risk into one composite score,
then maps it to a tiered decision — ALLOW / EDIT / FLAG_FOR_REVIEW / BLOCK —
using weights and thresholds that vary by use case and geography, not one
fixed rule for everything (Round 2 brief: "configurable policy layer so
behavior can vary by use case, geography, or risk appetite").

Why tiers, not a single cutoff: over-flagging low-risk responses causes
alert fatigue and teaches humans to ignore warnings; under-flagging creates
real liability. A tiered response lets low-risk cases pass instantly while
still catching genuine edge cases — the tradeoff the brief explicitly asks
teams to tune deliberately rather than solve away.
"""

import numpy as np
import pandas as pd

# Per-use-case dimension weights: a decision-support tool should weight
# Performance (correctness) more heavily; a customer-facing bot should weight
# Responsibility (tone, bias, leaks) more heavily; an internal copilot can
# tolerate more Cost variance since nobody external is waiting on it.
USE_CASE_WEIGHTS = {
    "customer_support":  {"performance": 0.35, "cost": 0.15, "responsibility": 0.50},
    "internal_copilot":  {"performance": 0.40, "cost": 0.35, "responsibility": 0.25},
    "decision_support":  {"performance": 0.55, "cost": 0.10, "responsibility": 0.35},
}

# Geography multiplier on the Responsibility dimension only — stricter
# data-protection regimes (e.g. GDPR in the EU) warrant a lower tolerance
# for the same underlying PII/bias signal.
GEOGRAPHY_RESPONSIBILITY_MULTIPLIER = {"EU": 1.25, "US": 1.0, "IN": 1.05}

# Decision tier thresholds on the final composite score (0-100).
# Exposed as a single "sensitivity" dial in the dashboard so the
# over-flagging vs under-flagging tradeoff is visibly tunable, not hidden.
DEFAULT_THRESHOLDS = {"edit": 35, "flag": 55, "block": 75}


def _thresholds(sensitivity=1.0):
    """sensitivity > 1.0 = stricter (flags more); < 1.0 = looser (flags less)."""
    return {k: v / sensitivity for k, v in DEFAULT_THRESHOLDS.items()}


def compute_policy_decisions(df, sensitivity=1.0):
    result = df.copy()
    thresholds = _thresholds(sensitivity)

    composite = []
    for _, row in result.iterrows():
        weights = USE_CASE_WEIGHTS.get(row["use_case"], USE_CASE_WEIGHTS["internal_copilot"])
        geo_mult = GEOGRAPHY_RESPONSIBILITY_MULTIPLIER.get(row["geography"], 1.0)

        score = (
            weights["performance"] * row["performance_risk_score"]
            + weights["cost"] * row["cost_risk_score"]
            + weights["responsibility"] * row["responsibility_risk_score"] * geo_mult
        )
        composite.append(min(score, 100))

    result["composite_risk_score"] = np.round(composite, 1)

    def decide(score):
        if score >= thresholds["block"]:
            return "BLOCK"
        elif score >= thresholds["flag"]:
            return "FLAG_FOR_REVIEW"
        elif score >= thresholds["edit"]:
            return "AUTO_EDIT"
        return "ALLOW"

    result["decision"] = result["composite_risk_score"].apply(decide)

    # Decision confidence: distance from the nearest tier boundary, normalized.
    # A score of 74 right below BLOCK's 75 is a much less confident ALLOW-adjacent
    # call than a score of 10 — surfacing this lets a human triage borderline cases first.
    boundaries = sorted(thresholds.values())

    def confidence(score):
        dists = [abs(score - b) for b in boundaries]
        return round(100 - min(100, min(dists) * 4), 1)

    result["decision_confidence"] = result["composite_risk_score"].apply(confidence)
    return result


def get_response_action_label(decision):
    return {
        "BLOCK": "Response blocked before reaching the user",
        "FLAG_FOR_REVIEW": "Escalated to a human reviewer",
        "AUTO_EDIT": "Auto-redacted / softened before delivery",
        "ALLOW": "Delivered as-is",
    }.get(decision, "Unknown")
